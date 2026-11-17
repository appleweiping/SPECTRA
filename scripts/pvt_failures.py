"""Which PVT conditions break designs that pass at TT but fail the 45-condition grid.

Pools the final designs of the four main methods on robust tasks and records
exactly which runs were pooled.  The experiment defaults to ``E1g`` and can be
overridden by a positional argument or ``SPECTRA_MAIN_EXP``.  This keeps the
analysis on the GPT namespace while retaining compatibility with legacy E1
directories.  Writes ``results/pvt_failure_conditions.json``.
"""
import json, collections, os
from spectra.paths import ROOT

METHODS = ("spectra", "spectra_min", "direct", "genbo")


def base_method(name):
    return str(name).split("@", 1)[0]


def run_files(exp):
    """Yield ``(base_method, path)`` for legacy and method@model run trees."""
    root = ROOT / "results" / "raw" / exp
    if not root.exists():
        return
    for method_dir in sorted(root.iterdir()):
        if not method_dir.is_dir():
            continue
        method = base_method(method_dir.name)
        if method not in METHODS:
            continue
        for task_dir in sorted(method_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            yield from ((method, path) for path in sorted(task_dir.glob("s*.json")))


def main(exp=None):
    exp = exp or os.environ.get("SPECTRA_MAIN_EXP", "E1g")
    c = collections.Counter(); runs = []
    per_design = collections.Counter()
    for method, f in run_files(exp):
        with f.open() as fh:
            r = json.load(fh)
        v = r.get("verify", {})
        budget = r.get("budget_sims")
        if budget is not None and budget > 600:
            continue
        if r.get("task_meta", {}).get("robust") and v.get("tt_pass") and not v.get("pvt_pass"):
            conds = v.get("pvt_fail_conds", [])
            runs.append(f"{method}/{f.parent.name}/{f.stem}")
            for cn in conds:
                c[cn] += 1
            parts = [cn.split("_")[:3] for cn in conds]
            per_design["any_1.62V"] += any(p[2] == "1.62V" for p in parts)
            per_design["only_1.62V"] += bool(parts) and all(p[2] == "1.62V" for p in parts)
    bc, bt, bv = collections.Counter(), collections.Counter(), collections.Counter()
    for k, v in c.items():
        a, b, d = k.split("_")[:3]; bc[a] += v; bt[b] += v; bv[d] += v
    out = {"experiment": exp,
           "pooled": f"{exp} final designs of " + ", ".join(METHODS) + " on robust tasks that pass TT and fail PVT",
           "n_designs": len(runs), "runs": runs, "n_fail_conditions": sum(c.values()), "fail_counts": dict(c),
           "by_corner": dict(bc.most_common()), "by_temp": dict(bt.most_common()), "by_vdd": dict(bv.most_common()),
           "designs_failing_at_1.62V": per_design["any_1.62V"], "designs_failing_only_at_1.62V": per_design["only_1.62V"]}
    (ROOT / "results/pvt_failure_conditions.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("runs", "fail_counts")}, indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("exp", nargs="?", default=None)
    main(ap.parse_args().exp)
