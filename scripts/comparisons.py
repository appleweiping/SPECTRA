"""Matched-task comparisons for the ablation (E2), PVT (E3) and backbone (E5) studies.

Every block restricts all of its methods to the tasks that each of them completed, so every number in a block is
computed on one task set. Writes results/comparisons.json; make_tables.py and paper_numbers.py read only that file.

python -m scripts.comparisons
"""
import argparse
import json
import os
from collections import defaultdict

import numpy as np

from spectra.paths import ROOT
from scripts.analyze import load, cluster_boot, common_tasks, exact_tests


def _ids(name):
    p = ROOT / "data" / "bench" / name
    return {json.loads(l)["id"] for l in open(p)} if p.exists() else set()


def seeds_range(rs):
    per = defaultdict(int)
    for r in rs:
        per[r["task"]] += 1
    return [min(per.values()), max(per.values())] if per else [0, 0]


def block(runs, methods, ref, task_ids, require=None):
    """`require`: methods that must be present (others are dropped if they have no runs on the task set)."""
    runs = [r for r in runs if r["task"] in task_ids and not r.get("infeasible")]
    present = [m for m in methods if any(r["method"] == m for r in runs)]
    if require and not all(m in present for m in require):
        return None
    ct = common_tasks(runs, present)
    if not ct:
        return None
    runs = [r for r in runs if r["task"] in ct]
    out = {"n_tasks": len(ct), "tasks": sorted(ct), "ref": ref, "methods": {}}
    for m in present:
        rs = [r for r in runs if r["method"] == m]
        s, lo, hi = cluster_boot(rs)
        succ = [r for r in rs if r["success"]]
        d = {"success": s, "ci95": [lo, hi], "n_runs": len(rs), "seeds": seeds_range(rs),
             "median_calls_success": float(np.median([r["calls"] for r in succ])) if succ else None,
             "median_sims_success": float(np.median([r["sims"] for r in succ])) if succ else None,
             "mean_sims": float(np.mean([r["sims"] for r in rs])),
             "mean_cost_usd": float(np.mean([r["cost"] for r in rs])),
             "mean_tokens": float(np.mean([r["tokens"] for r in rs]))}
        if m != ref and ref in present:
            d["vs_ref"] = exact_tests(runs, ref, m)
        out["methods"][m] = d
    return out


def _strip_model_suffix(runs):
    """Normalize GPT experiment directory names (method@gpt-6.1-sol) for paired tables."""
    return [dict(r, method=r["method"].split("@", 1)[0]) for r in runs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", default=os.environ.get("SPECTRA_MAIN_EXP", "E1"))
    ap.add_argument("--e2", default=os.environ.get("SPECTRA_E2_EXP", "E2"))
    ap.add_argument("--e3", default=os.environ.get("SPECTRA_E3_EXP", "E3"))
    ap.add_argument("--e5", default=os.environ.get("SPECTRA_E5_EXP", "E5"))
    ap.add_argument("--strip-model-suffix", action="store_true",
                    default=os.environ.get("SPECTRA_STRIP_MODEL_SUFFIX", "").lower() in {"1", "true", "yes"})
    a = ap.parse_args()
    e1, e2, e3, e5 = (load(x) for x in (a.e1, a.e2, a.e3, a.e5))
    if a.strip_model_suffix:
        e1, e2, e3, e5 = (_strip_model_suffix(x) for x in (e1, e2, e3, e5))
    sub, t3, rob, prim = _ids("subset_E2.jsonl"), _ids("subset_T3.jsonl"), _ids("subset_robust.jsonl"), _ids("subset_primary.jsonl")
    res = {}
    # E2-A: components on the whole stratified subset (2 seeds for the ablated arms)
    res["ablation_subset"] = block(e1 + e2, ["spectra", "spectra_nodiag", "spectra_nointent", "spectra_min", "genbo", "direct"],
                                   "spectra", sub, require=["spectra"])
    # E2-B: refinement and knowledge cards on the subset's T3 tasks (1 seed for the ablated arms)
    res["ablation_t3"] = block(e1 + e2, ["spectra", "spectra_norefine", "spectra_noknow", "direct", "direct_noknow"],
                               "spectra", t3, require=["spectra"])
    if res["ablation_t3"] and "direct_noknow" in res["ablation_t3"]["methods"]:
        ct = set(res["ablation_t3"]["tasks"])
        res["ablation_t3"]["direct_vs_direct_noknow"] = exact_tests([r for r in e1 + e2 if r["task"] in ct],
                                                                     "direct", "direct_noknow")
    # E3: PVT strategies on the subset's robust tasks, seed 0 (E3 arms have one seed)
    e1s0 = [r for r in e1 if r["seed"] == "s0"]
    res["pvt"] = block(e1s0 + e3, ["spectra", "spectra_pvt_nominal", "genbo_full", "spectra_min", "genbo", "direct"],
                       "spectra", rob, require=["spectra"])
    # E5: backbone, seed 0, subset T3 + robust tasks. GPT runs can keep the
    # original @model suffix for a genuine second backbone; a same-model E5g
    # arm is recorded but omitted from the scaling comparison.
    e5r = [dict(r, method=r["method"].replace("@haiku", "_haiku")) for r in e5]
    scaling_methods = ["spectra", "direct", "spectra_haiku", "direct_haiku"]
    res["scaling"] = None if a.strip_model_suffix else block(e1s0 + e5r, scaling_methods, "spectra", prim,
                                                               require=["spectra"])
    if res["scaling"] and "spectra_haiku" in res["scaling"]["methods"] and "direct_haiku" in res["scaling"]["methods"]:
        ct = set(res["scaling"]["tasks"])
        res["scaling"]["haiku_spectra_vs_direct"] = exact_tests([r for r in e5r if r["task"] in ct], "spectra_haiku", "direct_haiku")
    (ROOT / "results" / "comparisons.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if not v:
            print(k, "-- no data"); continue
        print(f"== {k}: {v['n_tasks']} tasks")
        for m, d in v["methods"].items():
            vs = d.get("vs_ref", {})
            print(f"  {m:20s} succ={d['success']:.3f} [{d['ci95'][0]:.2f},{d['ci95'][1]:.2f}] seeds={d['seeds']} "
                  f"sims*={d['median_sims_success']} W/L={vs.get('wins')}/{vs.get('losses')} p={vs.get('p_perm')}")


if __name__ == "__main__":
    main()
