"""Post-hoc mismatch Monte Carlo of the final designs of PVT-robust runs.

Scope: seed-0 runs of E1 (SPECTRA, SPECTRA-min, AnalogCoder-style, Gen+TPE) and E3 (TT-only design, Gen+TPE-full) on
robust tasks whose final design passed all 45 PVT conditions. Each design is simulated at TT/27 C with N per-instance
mismatch samples (agauss on the PDK's Pelgrom slopes, `.option seed=k`); yield = fraction of samples meeting every
specification. Writes results/mc_yield.json: {"n_samples": N, "yield": {method: {"task/s0": y}},
"max_rel_spread": {method: {"task/s0": largest (max-min)/|mean| over metrics}}} (> 0 shows that samples differ).

python -m scripts.mc_yield [N]
"""
import argparse
import json, sys
import os
from concurrent.futures import ThreadPoolExecutor
from spectra.paths import ROOT
from spectra.sim.evaluate import evaluate, MC

SCOPE = {"E1": ("spectra", "spectra_min", "direct", "genbo"), "E3": ("spectra_pvt_nominal", "genbo_full")}


def method_dirs(exp, method):
    """Yield raw-run directories for a base method in legacy or GPT runs."""
    root = ROOT / "results" / "raw" / exp
    for p in sorted(root.glob(f"{method}*")):
        if p.is_dir() and p.name.split("@", 1)[0] == method:
            yield p


def main(n=100, e1="E1", e3="E3"):
    n = int(n)
    scope = {e1: SCOPE["E1"], e3: SCOPE["E3"]}
    tasks = {json.loads(l)["id"]: json.loads(l) for f in ["tasks.jsonl", "designer_tasks.jsonl"]
             for l in open(ROOT / "data" / "bench" / f)}
    outp = ROOT / "results" / "mc_yield.json"
    manifest = {"e1": e1, "e3": e3}
    out = json.loads(outp.read_text()) if outp.exists() else {}
    # The method names are shared by legacy E1/E3 and GPT E1g/E3g.  Reset the
    # post-hoc file when its source experiments differ, otherwise a previous
    # model's yields would silently suppress the new jobs as already complete.
    if out.get("n_samples") != n or out.get("experiments") != manifest:
        out = {"n_samples": n, "experiments": manifest, "yield": {}}
    out.setdefault("yield", {})
    jobs = []
    for exp, methods in scope.items():
        for m in methods:
            for mdir in method_dirs(exp, m):
                for f in sorted(mdir.glob("*/s0.json")):
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
        # sanity check that mismatch samples differ: largest relative spread (max-min)/|mean| over the metrics
        spread = 0.0
        for k in (next(iter(ev.checks.values())) if ev.checks else {}):
            vals = [chk[k][0] for chk in ev.checks.values() if k in chk and isinstance(chk[k][0], (int, float))]
            if len(vals) > 1 and abs(sum(vals) / len(vals)) > 0:
                spread = max(spread, (max(vals) - min(vals)) / abs(sum(vals) / len(vals)))
        return m, t["id"], sum(ok) / n, len(ok), spread   # unsimulatable samples count as failures

    with ThreadPoolExecutor(2) as ex:
        for m, tid, y, k, sp in ex.map(one, jobs):
            out["yield"].setdefault(m, {})[f"{tid}/s0"] = y
            out.setdefault("max_rel_spread", {}).setdefault(m, {})[f"{tid}/s0"] = sp
            outp.write_text(json.dumps(out, indent=1))
            print(m, tid, f"yield={y:.2f} ({k} samples, max rel. spread {sp:.3f})", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=100)
    ap.add_argument("--e1", default=os.environ.get("SPECTRA_MAIN_EXP", "E1"))
    ap.add_argument("--e3", default=os.environ.get("SPECTRA_E3_EXP", "E3"))
    a = ap.parse_args()
    main(a.n, a.e1, a.e3)
