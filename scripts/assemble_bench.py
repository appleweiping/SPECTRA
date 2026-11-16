"""Merge per-family build outputs into data/bench/tasks.jsonl (stable order), harmonise output-level specs to
VDD-relative form, and re-verify every reference against its final spec set (feasibility certificates)."""
import json, glob, re
from spectra.paths import ROOT
from spectra.bench.templates import T
from spectra.bench.nl import render
from spectra.sim.evaluate import evaluate, PVT, NOMINAL
from scripts.build_bench import SLOTS

B = ROOT / "data" / "bench"
REL = {("comparator", "vout_max"): ("vout_max_rel", 1.8), ("comparator", "vout_min"): ("vout_min_rel", 1.8),
       ("schmitt", "vout_max"): ("vout_max_rel", 1.8), ("schmitt", "vout_min"): ("vout_min_rel", 1.8)}

REL_TOL = {1: 0.2, 2: 0.1, 3: 0.03}


def augment_app(t, net):
    """Integrators need f_unity/slope specs; summing/difference amplifiers need the second gain a2."""
    func = t["tb"].get("func")
    have = {s["metric"] for s in t["specs"]}
    conds = PVT if t.get("robust") else [NOMINAL]
    ev = evaluate({"family": t["family"], "tb": t["tb"], "specs": [], "full_analyses": True}, net, conds=conds)
    tol = REL_TOL.get(int(t["tier"]) if str(t["tier"]).isdigit() else 2, 0.1)
    def rng(metric):
        vals = [m.get(metric) for m in ev.per_cond.values() if m.get(metric) is not None]
        if not vals:
            return None
        lo, hi = min(vals), max(vals)
        span = tol * max(abs(lo), abs(hi))
        return [float(f"{lo - span:.4g}"), float(f"{hi + span:.4g}")]
    if func == "integ":
        t["specs"] = [s for s in t["specs"] if s["metric"] != "a1"]
        if "f_unity" not in have and rng("f_unity"):
            t["specs"].append({"metric": "f_unity", "op": "range", "value": rng("f_unity")})
        if "slope_db_dec" not in have:
            vals = [m.get("slope_db_dec") for m in ev.per_cond.values() if m.get("slope_db_dec") is not None]
            if vals:
                t["specs"].append({"metric": "slope_db_dec", "op": "range",
                                   "value": [round(min(vals) - 1.5, 2), round(max(vals) + 1.5, 2)]})
    if func in ("sum", "diff") and "a2" not in have and rng("a2"):
        t["specs"].append({"metric": "a2", "op": "range", "value": rng("a2")})


def main():
    tasks = {}
    files = sorted(glob.glob(str(B / "tasks_*.jsonl")))
    files = [f for f in files if not f.endswith(".partial.jsonl")]
    for f in files:                      # later files (e.g. tasks_rebuild) override earlier ones
        for l in open(f):
            t = json.loads(l); tasks[t["id"]] = t
    order = {fam: i for i, fam in enumerate(SLOTS)}
    out, bad = [], []
    for tid in sorted(tasks, key=lambda k: (order[tasks[k]["family"]], int(k.split("-")[-1]))):
        t = tasks[tid]
        for s in t["specs"]:
            key = (t["family"], s["metric"])
            if key in REL:
                nm, vdd = REL[key]
                s["metric"] = nm; s["value"] = round(s["value"] / vdd, 3)
        net = T[t["ref"]["template"]]["build"](t["ref"]["x"])
        if t["family"] == "opamp_app":
            augment_app(t, net)
        t["nl_spec"] = render(t)
        ev = evaluate(t, net, conds=PVT if t.get("robust") else [NOMINAL])
        if not ev.passed:
            bad.append(tid); print("CERTIFICATE FAILED", tid, [k for c in ev.checks.values() for k, v in c.items() if not v[1]][:4]); continue
        t["ref"]["certificate"] = True
        out.append(t)
    with open(B / "tasks.jsonl", "w") as f:
        for t in out:
            f.write(json.dumps(t, default=float) + "\n")
    print(len(out), "certified tasks;", sum(t.get("robust", False) for t in out), "robust; dropped", bad)

if __name__ == "__main__":
    main()
