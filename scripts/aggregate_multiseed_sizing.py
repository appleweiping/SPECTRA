"""Aggregate matched multi-seed strict sizing evidence.

The seed-0 strict run lives under ``SIZ7g``.  Additional pre-registered
seeds live under ``SIZ7g_MS``.  This script keeps every task/seed cell,
reports Wilson intervals over cells, and uses task-clustered bootstrap
intervals so repeated seeds do not masquerade as independent tasks.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median

import numpy as np

from spectra.paths import ROOT
from spectra.baselines.paper_sizing import PAPER_META, RUNNERS

METHODS = tuple(RUNNERS)


def _load_tasks(path: Path):
    return {json.loads(line)["id"]: json.loads(line) for line in path.read_text().splitlines() if line.strip()}


def _wilson(values):
    n = len(values)
    if not n:
        return None
    z = 1.959963984540054
    p = sum(values) / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - r), 4), round(min(1.0, c + r), 4)]


def _load_record(root: Path, exp: str, method: str, task_id: str, seed: int):
    for directory in sorted((root / "results" / "raw" / exp).glob(f"{method}*")):
        if directory.name.split("@", 1)[0] != method:
            continue
        path = directory / task_id / f"s{seed}.json"
        if path.exists():
            return json.loads(path.read_text())
    return None


def _cluster_bootstrap(groups, reps=4000, seed=0):
    """95% task-clustered bootstrap for a scalar mean.

    Each group is one task and contains all available seed-level values.
    Sampling groups preserves the dependence induced by repeated seeds.
    """
    if not groups:
        return None
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(g, dtype=float) for g in groups if len(g)]
    if not arrays:
        return None
    values = np.asarray([float(a.mean()) for a in arrays])
    draws = rng.integers(0, len(values), size=(reps, len(values)))
    boot = values[draws].mean(axis=1)
    return [round(float(np.quantile(boot, 0.025)), 4), round(float(np.quantile(boot, 0.975)), 4)]


def _record_metrics(rec):
    verify = rec.get("verify", {}) if rec else {}
    return {
        "tt": bool(verify.get("tt_pass")) if rec else None,
        "pvt": bool(verify.get("pvt_pass")) if rec and "pvt_pass" in verify else None,
        "violation": float(verify["tt_score"]) if rec and isinstance(verify.get("tt_score"), (int, float)) else None,
        "sims": float(rec.get("sims", 0) or 0) if rec else None,
        "calls": float(rec.get("calls", 0) or 0) if rec else None,
        "crash": bool(rec and rec.get("status") == "crash"),
    }


def _pair_sign_p(wins, losses):
    n = wins + losses
    if not n:
        return None
    tail = sum(math.comb(n, k) for k in range(0, min(wins, losses) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def main(subset="data/bench/paper_sizing_tasks.jsonl", seeds=(0, 1, 2), exps=("SIZ7g", "SIZ7g_MS"), reps=4000):
    tasks = _load_tasks(ROOT / subset)
    root = ROOT
    cells = {m: {} for m in METHODS}
    for method in METHODS:
        for task_id, task in tasks.items():
            cells[method][task_id] = []
            for seed in seeds:
                exp = exps[0] if seed == 0 else exps[1]
                rec = _load_record(root, exp, method, task_id, seed)
                if rec is not None:
                    cells[method][task_id].append({"seed": seed, **_record_metrics(rec)})

    rows = []
    for method in METHODS:
        all_cells = [r for values in cells[method].values() for r in values]
        tt = [r["tt"] for r in all_cells]
        pvt = [r["pvt"] for tid, values in cells[method].items() for r in values
               if tasks[tid].get("robust") and r["pvt"] is not None]
        violation = [r["violation"] for r in all_cells if r["violation"] is not None]
        task_tt_groups = [[r["tt"] for r in cells[method][tid]] for tid in tasks]
        task_pvt_groups = [[r["pvt"] for r in cells[method][tid] if tasks[tid].get("robust") and r["pvt"] is not None]
                           for tid in tasks]
        task_violation_groups = [[r["violation"] for r in cells[method][tid] if r["violation"] is not None]
                                 for tid in tasks]
        rows.append({
            "method": method,
            **PAPER_META[method],
            "cells_observed": len(all_cells),
            "cells_expected": len(tasks) * len(seeds),
            "tasks_observed": sum(bool(v) for v in cells[method].values()),
            "tt_success": sum(tt) / len(tt) if tt else None,
            "tt_wilson95": _wilson(tt),
            "tt_task_cluster_bootstrap95": _cluster_bootstrap(task_tt_groups, reps, 17),
            "pvt_cells_observed": len(pvt),
            "pvt_success": sum(pvt) / len(pvt) if pvt else None,
            "pvt_wilson95": _wilson(pvt),
            "pvt_task_cluster_bootstrap95": _cluster_bootstrap(task_pvt_groups, reps, 19),
            "mean_violation_score": sum(violation) / len(violation) if violation else None,
            "violation_task_cluster_bootstrap95": _cluster_bootstrap(task_violation_groups, reps, 23),
            "mean_sims": sum(r["sims"] for r in all_cells if r["sims"] is not None) / len(all_cells) if all_cells else None,
            "mean_calls": sum(r["calls"] for r in all_cells if r["calls"] is not None) / len(all_cells) if all_cells else None,
            "crashes": sum(r["crash"] for r in all_cells),
        })

    pairwise = {}
    for method in METHODS:
        if method == "spectra":
            continue
        pairs = []
        for tid in tasks:
            other_by_seed = {r["seed"]: r for r in cells[method][tid]}
            for a in cells["spectra"][tid]:
                b = other_by_seed.get(a["seed"])
                if b is not None:
                    pairs.append((a, b))
        wins = sum(a["tt"] and not b["tt"] for a, b in pairs)
        losses = sum(b["tt"] and not a["tt"] for a, b in pairs)
        # Task-clustered paired bootstrap of the TT difference.
        groups = []
        for tid in tasks:
            other_by_seed = {r["seed"]: r for r in cells[method][tid]}
            by_seed = {a["seed"]: (int(a["tt"]) - int(other_by_seed[a["seed"]]["tt"]))
                       for a in cells["spectra"][tid] if a["seed"] in other_by_seed}
            if by_seed:
                groups.append(list(by_seed.values()))
        diff_ci = _cluster_bootstrap(groups, reps, 29)
        pairwise[method] = {
            "common_cells": len(pairs), "tt_wins": wins, "tt_losses": losses,
            "tt_ties": len(pairs) - wins - losses,
            "exact_sign_p_cells": _pair_sign_p(wins, losses),
            "task_cluster_bootstrap_diff95": diff_ci,
        }

    domain_rows = []
    for method in METHODS:
        for family in sorted({task["family"] for task in tasks.values()}):
            tids = [tid for tid, task in tasks.items() if task["family"] == family]
            tt = [r["tt"] for tid in tids for r in cells[method][tid]]
            pvt = [r["pvt"] for tid in tids for r in cells[method][tid]
                   if tasks[tid].get("robust") and r["pvt"] is not None]
            domain_rows.append({"method": method, "family": family, "cells_observed": len(tt),
                                "tt_success": sum(tt) / len(tt) if tt else None,
                                "pvt_success": sum(pvt) / len(pvt) if pvt else None})

    result = {
        "schema": "spectra-paper-sizing/multiseed-v1",
        "model": "gpt-6.1-sol", "subset": subset, "experiments": list(exps), "seeds": list(seeds),
        "n_tasks": len(tasks), "n_frameworks": len(METHODS),
        "budget": {"simulation_units": 300, "llm_calls": 12}, "search_corners": 3, "verifier_corners": 45,
        "inference_scope": "three_seed_task_clustered_snapshot",
        "bootstrap_replicates": reps,
        "rows": rows, "pairwise_vs_spectra": pairwise, "domain_rows": domain_rows,
    }
    out_json = root / "results/paper_sizing_multiseed.json"
    out_md = root / "results/paper_sizing_multiseed.md"
    out_json.write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Three-seed strict sizing track", "", "Seed 0 is from SIZ7g and seeds 1/2 are from SIZ7g_MS. All methods use the frozen 36-task, 300-simulation-unit, 12-call protocol. Bootstrap intervals resample task IDs, preserving seed dependence.", "", "| Framework | Cells | TT success | Task-cluster TT 95% | PVT success | Task-cluster PVT 95% | Mean violation | Crashes |", "|---|---:|---:|---|---:|---|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['method']} | {row['cells_observed']}/{row['cells_expected']} | {row['tt_success']:.3f} [{row['tt_wilson95'][0]:.3f},{row['tt_wilson95'][1]:.3f}] | {row['tt_task_cluster_bootstrap95']} | {row['pvt_success']:.3f} [{row['pvt_wilson95'][0]:.3f},{row['pvt_wilson95'][1]:.3f}] | {row['pvt_task_cluster_bootstrap95']} | {row['mean_violation_score']:.4f} | {row['crashes']} |")
    lines += ["", "## Paired SPECTRA comparisons", "", "| Framework | Common cells | SPECTRA wins | losses | ties | Exact sign p | Cluster bootstrap diff 95% |", "|---|---:|---:|---:|---:|---:|---|"]
    for method, p in pairwise.items():
        lines.append(f"| {method} | {p['common_cells']} | {p['tt_wins']} | {p['tt_losses']} | {p['tt_ties']} | {p['exact_sign_p_cells']:.4g} | {p['task_cluster_bootstrap_diff95']} |")
    lines += ["", "## Per-domain rates", "", "| Method | Family | Cells | TT | PVT |", "|---|---|---:|---:|---:|"]
    for row in domain_rows:
        lines.append(f"| {row['method']} | {row['family']} | {row['cells_observed']} | {row['tt_success']:.3f} | {row['pvt_success']:.3f} |")
    out_md.write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", default="data/bench/paper_sizing_tasks.jsonl")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--exps", default="SIZ7g,SIZ7g_MS")
    ap.add_argument("--reps", type=int, default=4000)
    args = ap.parse_args()
    main(args.subset, tuple(int(x) for x in args.seeds.split(",")), tuple(args.exps.split(",")), args.reps)
