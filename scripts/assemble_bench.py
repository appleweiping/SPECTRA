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
        t["nl_spec"] = render(t)
        net = T[t["ref"]["template"]]["build"](t["ref"]["x"])
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
