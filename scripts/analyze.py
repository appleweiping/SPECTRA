"""Aggregate benchmark runs: success rates with cluster-bootstrap CIs, efficiency, paired tests.

python -m scripts.analyze --exp E1 [--methods a,b,c] [--baseline spectra]
Success := independent verification passes (TT for nominal tasks; all 45 PVT conditions for robust tasks).
"""
import sys
import argparse, json, math, random
from collections import defaultdict
from pathlib import Path

import numpy as np

from spectra.paths import ROOT

RAW = ROOT / "results" / "raw"


# E1 protocol: SPECTRA and AnalogCoder-style use seeds 0-2; the simulation-heavy Gen+TPE and SPECTRA-min use 0-1
SEED_FILTER = {}   # all completed seeds are used (per-task means)
ROBUST_CAP = 600   # condition-evaluations per robust run (final protocol)


def load(exp, methods=None):
    runs = []
    sf = SEED_FILTER.get(exp, {})
    for mdir in sorted((RAW / exp).glob("*")):
        if methods and mdir.name not in methods:
            continue
        for f in mdir.glob("*/s*.json"):
            if mdir.name in sf and f.stem not in sf[mdir.name]:
                continue
            r = json.loads(f.read_text())
            meta = r.get("task_meta", {})
            v = r.get("verify", {})
            succ = bool(v.get("pvt_pass")) if meta.get("robust") else bool(v.get("tt_pass"))
            bs, bc = r.get("budget_sims"), r.get("budget_calls")
            if meta.get("robust") and bs is not None and bs > ROBUST_CAP:
                # 1200-cap runs were archived and re-run natively at 600 (EXPERIMENT_LOG 2026-11-17 04:40)
                print(f"WARNING: {f} ran under a {bs} cap; excluded", file=sys.stderr)
                continue
            over = (bs is not None and (r.get("sims") or 0) > bs) or (bc is not None and (r.get("calls") or 0) > bc)
            if over:
                succ = False
            runs.append({"method": mdir.name, "task": f.parent.name, "seed": f.stem, "success": succ,
                         "tt_pass": bool(v.get("tt_pass")), "robust": meta.get("robust", False), "tier": meta.get("tier"),
                         "family": meta.get("family"), "sims": r.get("sims") or 0, "calls": r.get("calls") or 0,
                         "cost": r.get("cost_usd") or 0.0, "wall": r.get("wall_seconds") or 0.0,
                         "tokens": (r.get("tokens_in") or 0) + (r.get("tokens_out") or 0), "status": r.get("status"),
                         "first_pass_sims": r.get("first_pass_sims"), "declared_infeasible": r.get("status") == "declared_infeasible",
                         "over_budget": over, "infeasible": meta.get("infeasible", False)})
    return runs


def cluster_boot(runs, key="success", B=2000, seed=0):
    by_task = defaultdict(list)
    for r in runs:
        by_task[r["task"]].append(float(r[key]))
    tasks = list(by_task)
    if not tasks:
        return (float("nan"),) * 3
    means = np.array([np.mean(by_task[t]) for t in tasks])
    rng = np.random.default_rng(seed)
    bs = [means[rng.integers(0, len(tasks), len(tasks))].mean() for _ in range(B)]
    return float(means.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def pass_at_k(runs, k):
    by_task = defaultdict(list)
    for r in runs:
        by_task[r["task"]].append(r["success"])
    vals = []
    for t, xs in by_task.items():
        n, c = len(xs), sum(xs)
        if n < k:
            continue
        vals.append(1.0 - (math.comb(n - c, k) / math.comb(n, k) if n - c >= k else 0.0))
    return float(np.mean(vals)) if vals else float("nan")


def summarize(runs, methods):
    out = {}
    for m in methods:
        rs_all = [r for r in runs if r["method"] == m]
        rs = [r for r in rs_all if not r.get("infeasible")]
        ctl = [r for r in rs_all if r.get("infeasible")]
        if not rs:
            continue
        s, lo, hi = cluster_boot(rs)
        succ = [r for r in rs if r["success"]]
        d = {"n_runs": len(rs), "n_tasks": len({r["task"] for r in rs}), "success": s, "ci95": [lo, hi],
             "pass@1": pass_at_k(rs, 1), "pass@3": pass_at_k(rs, 3),
             "median_sims_success": float(np.median([r["sims"] for r in succ])) if succ else None,
             "median_calls_success": float(np.median([r["calls"] for r in succ])) if succ else None,
             "mean_cost_usd": float(np.mean([r["cost"] for r in rs])), "mean_tokens": float(np.mean([r["tokens"] for r in rs])),
             "mean_wall_s": float(np.mean([r["wall"] for r in rs])), "mean_sims": float(np.mean([r["sims"] for r in rs])),
             "declared_infeasible": sum(r["declared_infeasible"] for r in rs),
             "controls_n": len(ctl), "controls_success": (sum(r["success"] for r in ctl) / len(ctl)) if ctl else None,
             "controls_declared": sum(r["declared_infeasible"] for r in ctl),
             "controls_mean_cost": (sum(r["cost"] for r in ctl) / len(ctl)) if ctl else None}
        key = {"T1": "tier1", "T2": "tier2", "T3": "tier3", "Robust": "robust", "Designer": "tierD"}
        for name, sel in [("nominal", lambda r: not r["robust"])] + [(key[g], fn) for g, fn in TIER_GROUPS]:
            sub = [r for r in rs if sel(r)]
            if sub:
                d[name] = cluster_boot(sub)[0]
                d[name + "_n"] = len({r["task"] for r in sub})
        fams = sorted({r["family"] for r in rs})
        d["by_family"] = {f: cluster_boot([r for r in rs if r["family"] == f])[0] for f in fams}
        out[m] = d
    return out


def paired(runs, a, b):
    from scipy.stats import wilcoxon
    ta = defaultdict(list); tb = defaultdict(list)
    runs = [r for r in runs if not r.get("infeasible")]
    for r in runs:
        if r["method"] == a: ta[r["task"]].append(r["success"])
        if r["method"] == b: tb[r["task"]].append(r["success"])
    common = sorted(set(ta) & set(tb))
    x = np.array([np.mean(ta[t]) for t in common]); y = np.array([np.mean(tb[t]) for t in common])
    diff = x - y
    if np.all(diff == 0):
        return {"n": len(common), "mean_diff": 0.0, "p": 1.0}
    st = wilcoxon(x, y, zero_method="zsplit")
    return {"n": len(common), "mean_diff": float(diff.mean()), "p": float(st.pvalue), "wins": int((diff > 0).sum()),
            "losses": int((diff < 0).sum())}


def anytime(runs, methods, budgets=(1, 5, 10, 20, 50, 100, 200, 300)):
    curves = {}
    for m in methods:
        rs = [r for r in runs if r["method"] == m and not r["robust"] and not r.get("infeasible")]
        if not rs:
            continue
        curves[m] = {b: float(np.mean([r["success"] and r["sims"] <= b for r in rs])) for b in budgets}
    return curves


# One tier-group definition shared by analyze, make_tables and make_figures: every PVT-robust task (certified or
# designer-written) counts as Robust; T1/T2/T3/Designer contain nominal tasks only.
TIER_GROUPS = [("T1", lambda r: str(r["tier"]) == "1" and not r["robust"]),
               ("T2", lambda r: str(r["tier"]) == "2" and not r["robust"]),
               ("T3", lambda r: str(r["tier"]) == "3" and not r["robust"]),
               ("Robust", lambda r: r["robust"]),
               ("Designer", lambda r: str(r["tier"]) == "D" and not r["robust"])]


def load_common(exp, methods):
    """Runs of `methods` restricted to the tasks every method completed (the set used for all E1 statistics)."""
    runs = [r for r in load(exp, methods) if not r.get("infeasible")]
    ct = common_tasks(runs, methods)
    return [r for r in runs if r["task"] in ct]


def common_tasks(runs, methods):
    sets = [{r["task"] for r in runs if r["method"] == m} for m in methods]
    sets = [x for x in sets if x]
    return set.intersection(*sets) if sets else set()


def primary(r):
    """Primary endpoint (fixed at interim review round 1): near-frontier tasks (certified T3) and every PVT-robust task."""
    return r["robust"] or str(r["tier"]) == "3"


def exact_tests(runs, a, b):
    """Per-task paired comparison: exact two-sided sign test on tasks with different success rates, and a paired
    permutation test (10^5 sign flips) on the mean per-task difference."""
    from scipy.stats import binomtest
    ta, tb = defaultdict(list), defaultdict(list)
    for r in runs:
        if r["method"] == a: ta[r["task"]].append(r["success"])
        if r["method"] == b: tb[r["task"]].append(r["success"])
    common = sorted(set(ta) & set(tb))
    d = np.array([np.mean(ta[t]) - np.mean(tb[t]) for t in common])
    wins, losses = int((d > 0).sum()), int((d < 0).sum())
    p_sign = binomtest(wins, wins + losses, 0.5).pvalue if wins + losses else 1.0
    rng = np.random.default_rng(0)
    obs = d.mean() if len(d) else 0.0
    flips = rng.choice([-1, 1], size=(100000, len(d))) if len(d) else np.zeros((1, 0))
    perm = (flips * d).mean(1) if len(d) else np.zeros(1)
    p_perm = float((np.abs(perm) >= abs(obs) - 1e-12).mean())
    return {"n_tasks": len(common), "mean_diff": float(obs), "wins": wins, "losses": losses,
            "p_sign": float(p_sign), "p_perm": p_perm}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--methods", default="")
    ap.add_argument("--baseline", default="spectra")
    a = ap.parse_args()
    methods = a.methods.split(",") if a.methods else None
    runs = load(a.exp, methods)
    methods = methods or sorted({r["method"] for r in runs})
    feas = [r for r in runs if not r.get("infeasible")]
    ct = common_tasks(feas, methods)
    runs_c = [r for r in feas if r["task"] in ct]
    summ = summarize(runs_c, methods)
    prim = [r for r in runs_c if primary(r)]
    summ_primary = summarize(prim, methods)
    tests = {}
    for m in methods:
        if m != a.baseline and a.baseline in methods:
            tests[f"{a.baseline}_vs_{m}"] = paired(runs_c, a.baseline, m)
    # Holm correction
    ps = sorted(((v["p"], k) for k, v in tests.items()))
    for i, (p, k) in enumerate(ps):
        tests[k]["p_holm"] = min(1.0, p * (len(ps) - i))
    exact = {}
    for m in methods:
        if m != a.baseline and a.baseline in methods:
            exact[f"{a.baseline}_vs_{m}"] = {"all": exact_tests(runs_c, a.baseline, m),
                                             "primary": exact_tests(prim, a.baseline, m)}
    ps = sorted(((v["primary"]["p_perm"], k) for k, v in exact.items()))
    for i, (p, k) in enumerate(ps):
        exact[k]["primary"]["p_perm_holm"] = min(1.0, p * (len(ps) - i))
    res = {"common_tasks": len(ct), "summary": summ, "primary": summ_primary, "primary_n_tasks": len({r["task"] for r in prim}),
           "primary_families": len({r["family"] for r in prim}), "common_families": len({r["family"] for r in runs_c}),
           "primary_tasks": sorted({r["task"] for r in prim}),
           "tests": tests, "exact": exact, "anytime": anytime(runs_c, methods)}
    (ROOT / "results" / f"{a.exp}_summary.json").write_text(json.dumps(res, indent=1))
    print(f"{'method':22s} {'n':>4s} {'succ':>6s} {'95%CI':>15s} {'nom':>6s} {'rob':>6s} {'T1':>5s} {'T2':>5s} {'T3':>5s} {'D':>5s} {'sims*':>6s} {'calls*':>6s} {'$':>6s}")
    for m, d in summ.items():
        f = lambda k: f"{d[k]:.2f}" if d.get(k) is not None else "  - "
        print(f"{m:22s} {d['n_runs']:4d} {d['success']:6.3f} [{d['ci95'][0]:.2f},{d['ci95'][1]:.2f}] {f('nominal'):>6s} "
              f"{f('robust'):>6s} {f('tier1'):>5s} {f('tier2'):>5s} {f('tier3'):>5s} {f('tierD'):>5s} "
              f"{str(d['median_sims_success']):>6s} {str(d['median_calls_success']):>6s} {d['mean_cost_usd']:6.2f}")
    print("common tasks:", len(ct), " primary (T3 + robust) tasks:", res["primary_n_tasks"])
    for m, d in summ_primary.items():
        print(f"  PRIMARY {m:20s} succ={d['success']:.3f} CI=[{d['ci95'][0]:.2f},{d['ci95'][1]:.2f}] n_runs={d['n_runs']}")
    for k, v in exact.items():
        print(k, "primary:", v["primary"], " all:", v["all"])


if __name__ == "__main__":
    main()
