"""Failure modes of SPECTRA's failed E1 runs (common task set of the four main methods).

For each failed run: robust or nominal, LLM calls and simulations used, the simulations spent inside the PVT loop
(refinement on the active condition set + full 45-condition verifications), the number of full verifications, and
whether the worst-case PVT violation stalled (no decrease between consecutive verifications). Also lists, per
baseline, the primary-endpoint tasks on which SPECTRA's per-task success rate is lower. Writes
results/E1_spectra_failure_modes.json.

python -m scripts.spectra_failures
"""
import json, os, sys
from collections import defaultdict
from statistics import median

from spectra.paths import ROOT
from scripts.analyze import load_common, primary

METHODS = ["spectra", "spectra_min", "direct", "genbo"]


def base_method(name):
    return str(name).split("@", 1)[0]


def main(exp=None):
    exp = exp or os.environ.get("SPECTRA_MAIN_EXP", "E1g")
    runs = load_common(exp, METHODS)
    fails = []
    for r in runs:
        if r["method"] != "spectra" or r["success"]:
            continue
        method_dir = next((p for p in (ROOT / "results/raw" / exp).glob("spectra*")
                           if p.is_dir() and base_method(p.name) == "spectra"), None)
        if method_dir is None:
            continue
        d = json.loads((method_dir / r["task"] / f"{r['seed']}.json").read_text())
        ev = d.get("events", [])
        ver = [e for e in ev if e.get("kind") == "pvt_verify"]
        pvt_sims, prev = 0, 0
        in_pvt = False
        for e in ev:
            if e.get("kind") in ("refine", "pvt_verify"):
                if e.get("kind") == "pvt_verify" or in_pvt:
                    pvt_sims += e["sims"] - prev
                in_pvt = in_pvt or e.get("kind") == "pvt_verify"
            elif e.get("kind") == "llm":
                in_pvt = False
            prev = e.get("sims", prev)
        scores = [e.get("score") for e in ver if e.get("score") is not None]
        stalled = any(b >= a for a, b in zip(scores, scores[1:]))
        fails.append({"task": r["task"], "seed": r["seed"], "family": r["family"], "robust": r["robust"],
                      "calls": d["calls"], "sims": d["sims"], "status": d["status"], "n_pvt_verify": len(ver),
                      "pvt_sims": pvt_sims, "pvt_scores": scores, "pvt_stalled": stalled})
    rob = [f for f in fails if f["robust"]]
    per_task = defaultdict(lambda: defaultdict(list))
    for r in runs:
        if primary(r):
            per_task[r["task"]][r["method"]].append(r["success"])
    losses = {}
    for b in ("direct", "genbo", "spectra_min"):
        losses[b] = sorted(t for t, d in per_task.items()
                           if d.get(b) and sum(d["spectra"]) / len(d["spectra"]) < sum(d[b]) / len(d[b]))
    fam = {r["task"]: r["family"] for r in runs}
    out = {"n_failed_runs": len(fails), "n_failed_robust": len(rob), "n_failed_nominal": len(fails) - len(rob),
           "robust_stalled": sum(f["pvt_stalled"] for f in rob),
           "robust_median_pvt_sims": median([f["pvt_sims"] for f in rob]) if rob else None,
           "robust_median_calls": median([f["calls"] for f in rob]) if rob else None,
           "nominal_median_calls": median([f["calls"] for f in fails if not f["robust"]]) if len(fails) > len(rob) else None,
           "primary_losses": losses, "primary_loss_families": {b: sorted({fam[t] for t in v}) for b, v in losses.items()},
           "runs": fails}
    (ROOT / "results" / f"{exp}_spectra_failure_modes.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("exp", nargs="?", default=None)
    main(ap.parse_args().exp)
