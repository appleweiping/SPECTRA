"""Failure-mode analysis: for failed runs, final normalised violation and which metrics fail most often."""
import json, glob, collections, sys
from spectra.paths import ROOT
from spectra.sim.evaluate import check

def main(exp="E1"):
    tasks = {}
    for f in ["tasks.jsonl", "designer_tasks.jsonl", "control_tasks.jsonl"]:
        p = ROOT / "data/bench" / f
        if p.exists():
            for l in open(p):
                t = json.loads(l); tasks[t["id"]] = t
    out = {}
    for mdir in sorted((ROOT / "results/raw" / exp).glob("*")):
        m = mdir.name
        viol, metr, near = [], collections.Counter(), 0
        nfail = 0
        for f in mdir.glob("*/s*.json"):
            r = json.loads(f.read_text()); t = tasks.get(f.parent.name)
            if t is None:
                continue
            v = r.get("verify", {})
            ok = v.get("pvt_pass") if t.get("robust") else v.get("tt_pass")
            if ok:
                continue
            nfail += 1
            tm = v.get("tt_metrics") or {}
            chk, tot = check(t["specs"], tm)
            viol.append(tot)
            if not t.get("robust") and 0 < tot < 0.05:
                near += 1
            for k, (val, p, _) in chk.items():
                if not p:
                    metr[k.split(">")[0].split("<")[0].split("range")[0]] += 1
            if t.get("robust") and v.get("tt_pass"):
                metr["(PVT only)"] += 1
        out[m] = {"n_fail": nfail, "near_miss_<5%": near, "median_violation": sorted(viol)[len(viol) // 2] if viol else None,
                  "top_failing_metrics": metr.most_common(8)}
    (ROOT / "results" / f"{exp}_failures.json").write_text(json.dumps(out, indent=1))
    for m, d in out.items():
        print(m, d)

if __name__ == "__main__":
    main(*sys.argv[1:2])
