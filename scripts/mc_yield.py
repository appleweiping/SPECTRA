"""Post-hoc mismatch Monte-Carlo (100 per-instance samples, TT/27C) of final designs of robust-tier runs.
Yield = fraction of samples meeting every spec. Writes results/<exp>_mc_yield.json."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from spectra.paths import ROOT
from spectra.sim.evaluate import evaluate, MC

def main(exp="E1", n=100):
    raw = ROOT / "results" / "raw" / exp
    tasks = {json.loads(l)["id"]: json.loads(l) for f in ["tasks.jsonl", "designer_tasks.jsonl"]
             for l in open(ROOT / "data" / "bench" / f) if (ROOT / "data" / "bench" / f).exists()}
    out = {}
    jobs = []
    for f in raw.glob("*/*/s*.json"):
        r = json.loads(f.read_text())
        t = tasks.get(f.parent.name)
        if not t or not t.get("robust") or not r.get("verify", {}).get("pvt_pass"):
            continue
        jobs.append((f.parent.parent.name, t, f.stem, r["final_netlist"]))
    def one(j):
        m, t, s, net = j
        ev = evaluate(t, net, conds=MC[:n])
        ok = [all(v[1] for v in chk.values()) for chk in ev.checks.values()]
        return m, t["id"], s, sum(ok) / max(len(ok), 1)
    with ThreadPoolExecutor(2) as ex:
        for m, tid, s, y in ex.map(one, jobs):
            out.setdefault(m, {})[f"{tid}/{s}"] = y
            print(m, tid, s, f"yield={y:.2f}", flush=True)
    (ROOT / "results" / f"{exp}_mc_yield.json").write_text(json.dumps(out, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:2])
