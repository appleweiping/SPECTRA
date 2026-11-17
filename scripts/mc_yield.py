"""Post-hoc mismatch Monte Carlo of the final designs of PVT-robust runs.

Scope: seed-0 runs of E1 (SPECTRA, SPECTRA-min, AnalogCoder-style, Gen+TPE) and E3 (TT-only design, Gen+TPE-full) on
robust tasks whose final design passed all 45 PVT conditions. Each design is simulated at TT/27 C with N per-instance
mismatch samples (agauss on the PDK's Pelgrom slopes, `.option seed=k`); yield = fraction of samples meeting every
specification. Writes results/mc_yield.json: {"n_samples": N, "yield": {method: {"task/s0": y}}}.

python -m scripts.mc_yield [N]
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from spectra.paths import ROOT
from spectra.sim.evaluate import evaluate, MC

SCOPE = {"E1": ("spectra", "spectra_min", "direct", "genbo"), "E3": ("spectra_pvt_nominal", "genbo_full")}


def main(n=100):
    n = int(n)
    tasks = {json.loads(l)["id"]: json.loads(l) for f in ["tasks.jsonl", "designer_tasks.jsonl"]
             for l in open(ROOT / "data" / "bench" / f)}
    outp = ROOT / "results" / "mc_yield.json"
    out = json.loads(outp.read_text()) if outp.exists() else {"n_samples": n, "yield": {}}
    if out.get("n_samples") != n:
        out = {"n_samples": n, "yield": {}}
    jobs = []
    for exp, methods in SCOPE.items():
        for m in methods:
            for f in sorted((ROOT / "results" / "raw" / exp / m).glob("*/s0.json")):
                r = json.loads(f.read_text()); t = tasks.get(f.parent.name)
                if not t or not t.get("robust") or not r.get("verify", {}).get("pvt_pass") or r.get("budget_sims") != 600:
                    continue
                if f"{t['id']}/s0" in out["yield"].get(m, {}):
                    continue
                jobs.append((m, t, r["final_netlist"]))
    print(len(jobs), "designs to analyse", flush=True)

    def one(j):
        m, t, net = j
        ev = evaluate(t, net, conds=MC[:n])
        ok = [all(v[1] for v in chk.values()) for chk in ev.checks.values()]
        return m, t["id"], sum(ok) / n, len(ok)        # unsimulatable samples count as failures

    with ThreadPoolExecutor(2) as ex:
        for m, tid, y, k in ex.map(one, jobs):
            out["yield"].setdefault(m, {})[f"{tid}/s0"] = y
            outp.write_text(json.dumps(out, indent=1))
            print(m, tid, f"yield={y:.2f} ({k} samples)", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:2])
