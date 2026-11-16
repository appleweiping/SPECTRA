"""Derive SPECTRA-Bench tasks from expert-template exploration archives.

For every task slot: pick a reference design near the Pareto front of its template archive (random weighted
utility over the family profile), derive specs from the reference's (re-)simulated metrics with a tier margin,
round conservatively, render the natural-language spec, and RE-VERIFY that the reference meets the specs
(at TT, or at all 17 PVT conditions for robust tasks). Output: data/bench/tasks.jsonl
"""
import json, math, sys
from pathlib import Path
import numpy as np
from spectra.paths import ROOT
from spectra.bench.templates import T
from spectra.bench.profiles import PROFILES
from spectra.bench.nl import render
from spectra.sim.evaluate import evaluate, PVT, NOMINAL

EXP = ROOT / "data" / "explore"
OUT = ROOT / "data" / "bench"
OUT.mkdir(parents=True, exist_ok=True)

DB = {"gain_db", "cmrr_db", "psrr_db", "zt_dbohm", "psrr_1k", "atten_db"}
DB_MINUS = {"peaking_db"}
LOG_PLUS = {"ugbw", "f3db", "gbw", "slew", "rout", "f_mid", "fmin", "fmax", "tuning_ratio", "kvco", "bw"}
LOG_MINUS = {"power", "settle", "noise_1k", "in_noise_1m", "load_reg", "line_reg", "iq", "undershoot", "overshoot",
             "tc_ppm", "tpd", "delay", "energy", "power_avg", "ripple_settled", "offset_abs"}
LIN_PLUS = {"swing", "hysteresis"}
LIN_MINUS = {"v_compliance"}
PCT = {"iout_err_pct", "vout_err_pct"}
TARGET = {"fc": "rel", "f0": "rel", "vref": "rel", "f_unity": "rel", "a1": "rel", "a2": "rel"}

MARGIN = {  # tier -> (dB, deg, log factor, lin factor, pct)
    1: (10.0, 15.0, 0.5, 0.7, 5.0), 2: (5.0, 8.0, 0.75, 0.85, 3.0), 3: (1.0, 2.0, 0.95, 0.97, 1.0)}
REL_TOL = {1: 0.2, 2: 0.1, 3: 0.03}
N_SPECS = {1: 4, 2: 6, 3: 99}
FRONTIER = True


def nice_floor(v, digits=2):
    if v <= 0:
        return v
    e = math.floor(math.log10(v)) - digits + 1
    return math.floor(v / 10 ** e) * 10 ** e


def nice_ceil(v, digits=2):
    if v <= 0:
        return v
    e = math.floor(math.log10(v)) - digits + 1
    return math.ceil(v / 10 ** e) * 10 ** e


def derive_spec(metric, val, tier):
    dB, deg, lf, lin, pct = MARGIN[tier]
    if val is None or not np.isfinite(val):
        return None
    if metric in DB:
        return {"metric": metric, "op": ">=", "value": math.floor(val - dB)}
    if metric in DB_MINUS:
        return {"metric": metric, "op": "<=", "value": round(max(val, 0) + dB / 5, 1)}
    if metric == "pm":
        return {"metric": metric, "op": ">=", "value": max(45, min(70, math.floor(val - deg)))}
    if metric in LOG_PLUS:
        return {"metric": metric, "op": ">=", "value": nice_floor(val * lf)}
    if metric in LOG_MINUS:
        return {"metric": metric, "op": "<=", "value": nice_ceil(abs(val) / lf)}
    if metric in LIN_PLUS:
        return {"metric": metric, "op": ">=", "value": math.floor(val * lin * 100) / 100}
    if metric in LIN_MINUS:
        return {"metric": metric, "op": "<=", "value": math.ceil(val / lin * 100) / 100}
    if metric in PCT:
        return {"metric": metric, "op": "<=", "value": round(max(pct, val + 0.5), 1)}
    if metric in TARGET:
        tol = REL_TOL[tier]
        tgt = float(f"{val:.2g}")
        if abs(tgt / val - 1) > tol / 2:
            tgt = val
        lo, hi = sorted((tgt * (1 - tol), tgt * (1 + tol)))
        return {"metric": metric, "op": "range", "value": [float(f"{lo:.4g}"), float(f"{hi:.4g}")]}
    return None


def worst_case(evP, metric, sense):
    vals = [m.get(metric) for m in evP.per_cond.values()]
    if any(v is None for v in vals):
        return None
    return min(vals) if sense == "+" else max(vals)


FRONTIER_CONDS = [NOMINAL, {"corner": "ss", "temp": 125, "vdd": 1.62}, {"corner": "ff", "temp": -40, "vdd": 1.98},
                  {"corner": "sf", "temp": 125, "vdd": 1.62}, {"corner": "fs", "temp": -40, "vdd": 1.62}]


def frontier_refine(fam, tname, x0, tb, metrics, robust, budget=160, seed=0):
    """Push a reference toward the template's Pareto front: maximise the minimum normalised improvement of the chosen
    metrics over the reference (worst case over a few hard PVT conditions for robust tasks), subject to sanity."""
    from spectra.opt.sizing import run_cmaes
    tpl = T[tname]
    prof = {n: s for n, s, _ in PROFILES[fam]["metrics"]}
    conds = FRONTIER_CONDS if robust else [NOMINAL]
    task0 = {"family": fam, "tb": tb, "specs": [{"metric": m, "op": ">=", "value": -1e30} for m in metrics]}
    ev0 = evaluate(task0, tpl["build"](x0), conds=conds)
    if ev0.status != "ok":
        return x0
    def agg(ev, m, sense):
        vals = [d.get(m) for d in ev.per_cond.values()]
        if any(v is None for v in vals):
            return None
        return min(vals) if sense == "+" else max(vals)
    ref = {m: agg(ev0, m, prof.get(m, "+")) for m in metrics}
    def unit(m, a, b):  # improvement of b over a in "spec units"
        sense = prof.get(m, "+")
        if a is None or b is None:
            return -5.0
        if m in DB or m.endswith("_db"):
            d = (b - a) / 3.0
        elif m == "pm":
            d = (b - a) / 5.0
        else:
            d = math.log(max(abs(b), 1e-30) / max(abs(a), 1e-30)) / math.log(1.25)
        return d if sense == "+" else -d
    def score(ev):
        if ev.status != "ok":
            return 50.0
        from spectra.sim.evaluate import check
        san = 0.0
        for c in ev.per_cond.values():
            _, v = check(PROFILES[fam]["sanity"], c); san = max(san, v)
        imp = min(unit(m, ref[m], agg(ev, m, prof.get(m, "+"))) for m in metrics)
        return 10 * san - min(imp, 2.0)
    task = {"family": fam, "tb": tb, "specs": task0["specs"]}
    r = run_cmaes(task, tpl["build"], tpl["vars"], budget=budget, conds=conds, seed=seed, x0=x0, sigma0=0.12,
                  score_fn=score)
    return r.best_x if (r.best_x and r.best_score < score(ev0)) else x0


def utility(rows, fam, w):
    prof = PROFILES[fam]["metrics"]
    M = []
    for name, sense, ref in prof:
        col = np.array([r["m"].get(name) if r["m"].get(name) is not None else np.nan for r in rows], dtype=float)
        if np.all(np.isnan(col)):
            M.append(np.zeros(len(rows))); continue
        order = np.argsort(np.argsort(np.where(np.isnan(col), -np.inf if sense == "+" else np.inf, col)))
        pr = order / max(len(rows) - 1, 1)
        M.append(pr if sense == "+" else 1 - pr)
    M = np.array(M)
    return (w[:, None] * M).sum(0)


# family -> list of slots: (archive tag, template, tier, robust, extra tb)
SLOTS = {
    "opamp": [("ota5t", 1, 0), ("ota5t", 2, 0), ("ota5t", 3, 0), ("miller2", 1, 0), ("miller2", 2, 0), ("miller2", 2, 0),
              ("miller2", 3, 0), ("miller2", 3, 0), ("miller2", 3, 0), ("fcasc", 1, 0), ("fcasc", 2, 0), ("fcasc", 3, 0),
              ("fcasc", 3, 0), ("miller2", 2, 1), ("miller2", 2, 1), ("ota5t", 2, 1), ("fcasc", 2, 1), ("miller2", 3, 1)],
    "amp": [("cs_pload", 1, 0), ("cs_pload", 2, 0), ("cs_diode", 1, 0), ("cs_diode", 3, 0), ("casc_amp", 2, 0),
            ("casc_amp", 3, 0), ("sf", 2, 0), ("cs_diode", 2, 1)],
    "tia": [("tia_sfb", 1, 0), ("tia_sfb", 2, 0), ("tia_sfb", 3, 0), ("tia_sfb", 3, 0), ("tia_sfb", 2, 1), ("tia_sfb", 2, 0)],
    "cmirror": [("cm_simple@20u", 1, 0), ("cm_casc@80u", 2, 0), ("cm_wide@20u", 3, 0), ("cm_psrc@5u", 2, 0),
                ("cm_wide@80u", 2, 0), ("cm_casc@5u", 3, 0), ("cm_simple@80u", 2, 1), ("cm_wide@20u", 2, 1), ("cm_casc@20u", 1, 0)],
    "ldo": [("ldo_pmos", 1, 0), ("ldo_pmos", 2, 0), ("ldo_pmos", 2, 0), ("ldo_pmos", 3, 0), ("ldo_pmos", 3, 0),
            ("ldo_pmos", 1, 0), ("ldo_pmos", 2, 1), ("ldo_pmos", 2, 1)],
    "ref": [("bgr", 1, 0), ("bgr", 2, 0), ("bgr", 3, 0), ("bgr", 2, 0), ("bgr", 2, 1), ("bgr", 1, 1)],
    "comparator": [("comp2", 1, 0), ("comp2", 2, 0), ("comp2", 3, 0), ("comp2", 2, 0), ("comp2", 3, 0), ("comp2", 2, 1)],
    "latch": [("strongarm", 1, 0), ("strongarm", 2, 0), ("strongarm", 3, 0), ("strongarm", 2, 0), ("strongarm", 3, 0), ("strongarm", 2, 1)],
    "vco": [("csring3", 1, 0), ("csring3", 2, 0), ("csring5", 2, 0), ("csring5", 3, 0), ("csring7", 2, 0), ("csring7", 3, 0),
            ("csring3", 3, 0), ("csring5", 2, 1)],
    "filter": [("sk_lpf2", 1, 0), ("sk_lpf2", 2, 0), ("sk_lpf2", 3, 0), ("sk_lpf3", 2, 0), ("sk_lpf3", 3, 0), ("mfb_bpf", 1, 0),
               ("mfb_bpf", 2, 0), ("sk_lpf2", 2, 1)],
    "schmitt": [("st6", 1, 0), ("st6", 2, 0), ("st6", 3, 0), ("st6", 2, 1)],
    "opamp_app": [("app_inv", 1, 0), ("app_inv", 3, 0), ("app_noninv", 2, 0), ("app_sum", 2, 0), ("app_sum", 3, 0),
                  ("app_diff", 2, 0), ("app_diff", 3, 0), ("app_integ", 2, 0), ("app_integ", 3, 0), ("app_inv", 2, 1)],
}
EXTRA_SPECS = {  # always-on functional specs (from sanity) per family
    "opamp": [{"metric": "polarity_ok", "op": ">=", "value": 1}],
    "amp": [{"metric": "vout_dc", "op": "range", "value": [0.45, 1.35]}],
    "tia": [{"metric": "vout_dc", "op": "range", "value": [0.3, 1.5]}],
    "ref": [{"metric": "startup_ok", "op": ">=", "value": 1}],
    "comparator": [{"metric": "polarity_ok", "op": ">=", "value": 1}, {"metric": "vout_max", "op": ">=", "value": 1.62},
                   {"metric": "vout_min", "op": "<=", "value": 0.18}],
    "latch": [{"metric": "correct", "op": ">=", "value": 1}],
    "filter": [], "schmitt": [{"metric": "vout_max", "op": ">=", "value": 1.7}, {"metric": "vout_min", "op": "<=", "value": 0.1}],
    "opamp_app": [{"metric": "vout_offset", "op": "range", "value": [-0.05, 0.05]}],
    "ldo": [{"metric": "ripple_settled", "op": "<=", "value": 0.01}],
}
FAMILY_EXTRA_METRICS = {"opamp": ["gain_db", "ugbw", "pm"], "amp": ["gain_db", "f3db"], "tia": ["zt_dbohm", "f3db"],
                        "ref": ["vref", "tc_ppm"], "filter": ["fc"], "opamp_app": ["a1"], "cmirror": ["iout_err_pct"],
                        "ldo": ["vout_err_pct"], "vco": ["f_mid"], "comparator": ["tpd"], "latch": ["delay"],
                        "schmitt": ["hysteresis"]}


def main(families=None, seed=0):
    rng = np.random.default_rng(seed)
    tasks, used = [], set()
    for fam, slots in SLOTS.items():
        if families and fam not in families:
            continue
        for si, (tag, tier, robust) in enumerate(slots):
            path = EXP / f"{tag}.jsonl"
            if not path.exists():
                print("missing archive", tag); continue
            tname = tag.split("@")[0]
            rows = []
            for l in open(path):
                r = json.loads(l)
                if r["sanity_ok"]:
                    r["m"] = r["metrics"]["tt_27C_1.8V"]; rows.append(r)
            if not rows:
                print("no sane rows", tag); continue
            prof = PROFILES[fam]["metrics"]
            for attempt in range(12):
                w = rng.dirichlet(np.ones(len(prof)) * 0.7)
                u = utility(rows, fam, w)
                order = np.argsort(-u)
                pick = next((i for i in order[:max(5, len(order) // 4)] if (tag, i) not in used), order[0])
                ref = rows[pick]
                tb = ref["tb"]
                if fam == "filter" and tname == "mfb_bpf":
                    tb = dict(tb, kind="bandpass")
                xref = ref["x"]
                if (tier == 3 or robust) and FRONTIER:
                    pm_names = [n for n, _, _ in prof if ref["m"].get(n) is not None and n not in TARGET][:6]
                    xref = frontier_refine(fam, tname, ref["x"], tb, pm_names, robust, seed=si)
                net = T[tname]["build"](xref)
                task = {"family": fam, "tb": tb, "specs": []}
                conds = PVT if robust else [NOMINAL]
                ev = evaluate(task, net, conds=conds)
                if ev.status != "ok":
                    continue
                m0 = ev.per_cond["tt_27C_1.8V"]
                # choose metrics
                names = [n for n, _, _ in prof if m0.get(n) is not None]
                if fam == "filter" and tb.get("kind") == "bandpass":
                    names = ["f0", "q", "gain_db", "power"]
                order_m = list(rng.permutation(names))
                core = [c for c in FAMILY_EXTRA_METRICS.get(fam, []) if c in names or c in ("vref", "fc", "a1", "f0")]
                if any(m0.get(c) is None for c in core if c not in ("vref", "fc", "a1", "f0")):
                    print("  core metric missing; retry", tag); continue
                chosen = core + [n for n in order_m if n not in core][: max(0, N_SPECS[tier] - len(core))]
                specs = []
                for n in chosen:
                    sense = next((s for nm, s, _ in prof if nm == n), "+")
                    v = worst_case(ev, n, sense) if robust else m0.get(n)
                    if n == "q":
                        sp = {"metric": "q", "op": "range", "value": [round(v * (1 - REL_TOL[tier]), 3), round(v * (1 + REL_TOL[tier]), 3)]} if v else None
                    elif n == "gain_db" and fam == "filter":
                        sp = {"metric": "gain_db", "op": "range", "value": [-1.0, 1.0]} if tb.get("kind") == "lowpass" else {"metric": "gain_db", "op": ">=", "value": math.floor(v - MARGIN[tier][0])}
                    elif robust and n in TARGET:
                        vals = [m.get(n) for m in ev.per_cond.values()]
                        lo, hi = min(vals), max(vals)
                        span = max(abs(hi), abs(lo)) * REL_TOL[2]
                        sp = {"metric": n, "op": "range", "value": [float(f"{lo - span:.4g}"), float(f"{hi + span:.4g}")]}
                    else:
                        sp = derive_spec(n, v, 3 if robust else tier)
                    if sp:
                        specs.append(sp)
                specs += EXTRA_SPECS.get(fam, [])
                task["specs"] = specs
                ev2 = evaluate(task, net, conds=conds)
                if not ev2.passed:
                    print("  reference fails derived specs; retry", tag, [k for c in ev2.checks.values() for k, v in c.items() if not v[1]][:4])
                    continue
                used.add((tag, pick))
                tid = f"{fam}-{si:02d}"
                task.update({"id": tid, "tier": tier, "robust": bool(robust), "ref": {"template": tname, "x": xref, "archive": tag,
                             "frontier_refined": xref is not ref["x"]},
                             "ref_metrics": {k: v for k, v in m0.items()}})
                task["nl_spec"] = render(task)
                tasks.append(task)
                print(f"{tid:34s} specs={len(specs)}", flush=True)
                break
            else:
                print("FAILED slot", fam, tag, tier, robust)
    with open(OUT / ("tasks.jsonl" if not families else f"tasks_{'_'.join(families)}.jsonl"), "w") as f:
        for t in tasks:
            f.write(json.dumps(t, default=float) + "\n")
    print("total", len(tasks))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
