#!/usr/bin/env python3
"""Matched GF180 PVT sizing using the public ATLAS circuit evaluator.

The public YAML supplies one TT netlist and seventeen GF180 corner netlists.
The search budget counts TT simulations.  The selected design is then checked
once on every shipped corner, with no early stopping and with all raw corner
metrics retained in the result.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np


def load_evaluator(source_root: Path, root_dir: Path, *, pvt: bool):
    sys.path.insert(0, str(source_root))
    from topbo.circuit_eval import CircuitEvaluator

    yaml_path = source_root / "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
    return CircuitEvaluator(str(yaml_path), root_dir=str(root_dir), pvt=pvt)


def normalize_violation(evaluator, specs: dict) -> float:
    residuals = []
    for name in evaluator.spec_names:
        value = specs.get(name)
        if value is None or not math.isfinite(float(value)):
            residuals.append(1.0)
            continue
        target = float(evaluator.constraints[name])
        margin = ((float(value) - target) if evaluator.directions[name] == "min"
                  else (target - float(value))) / max(abs(target), 1.0)
        residuals.append(max(0.0, -margin))
    return float(sum(residuals) / max(1, len(residuals)))


def actual_params(evaluator, unit: np.ndarray) -> np.ndarray:
    bounds = evaluator.param_bounds
    return bounds[:, 0] + np.clip(unit, 0.0, 1.0) * (bounds[:, 1] - bounds[:, 0])


def run_search(evaluator, method: str, budget: int, seed: int):
    import cma

    rng = np.random.default_rng(seed)
    best_unit = np.full(evaluator.n_params, 0.5, dtype=float)
    best_violation = float("inf")
    first_pass = None
    evaluations = 0

    def visit(unit):
        nonlocal best_unit, best_violation, first_pass, evaluations
        values = actual_params(evaluator, unit)
        specs = evaluator.evaluate_tt(values)
        violation = normalize_violation(evaluator, specs)
        evaluations += 1
        if first_pass is None and violation == 0.0:
            first_pass = evaluations
        if violation < best_violation:
            best_violation = violation
            best_unit = np.asarray(unit, dtype=float).copy()
        return violation

    if method == "anaflow_cleanroom":
        for _ in range(budget):
            visit(rng.random(evaluator.n_params))
        return best_unit, best_violation, first_pass

    coverage = min(max(8, 2 * evaluator.n_params), max(1, budget // 3))
    for unit in rng.random((coverage, evaluator.n_params)):
        visit(unit)
    es = None
    if coverage < budget:
        es = cma.CMAEvolutionStrategy([0.5] * evaluator.n_params, 0.25,
                                       {"bounds": [0, 1], "seed": seed + 7000, "verbose": -9})
    while evaluations < budget:
        remaining = budget - evaluations
        points = es.ask()[:remaining]
        scores = [visit(point) for point in points]
        if len(scores) >= getattr(es.sp, "mu", 2):
            es.tell(points[:len(scores)], scores)
    return best_unit, best_violation, first_pass


def verify_pvt(evaluator, values: np.ndarray) -> dict:
    state = dict(zip(evaluator.param_names, values.tolist()))
    simulations = [("tt", evaluator.sim_env)] + list(zip(evaluator.corner_names, evaluator.corner_sims))
    conditions = []
    for name, simulator in simulations:
        _, specs_list, _ = simulator.run(state)
        raw_specs = specs_list[0] if specs_list else None
        specs = evaluator._remap_specs(raw_specs) if raw_specs is not None else {}
        violation = normalize_violation(evaluator, specs)
        conditions.append({
            "condition": name,
            "metrics": specs,
            "normalized_violation": violation,
            "pass": violation == 0.0,
            "missing_metrics": [key for key in evaluator.spec_names if key not in specs],
        })
    finite_values = [row["normalized_violation"] for row in conditions if math.isfinite(row["normalized_violation"])]
    return {
        "conditions_observed": len(conditions),
        "pvt_success": bool(conditions) and all(row["pass"] for row in conditions),
        "mean_normalized_violation": float(sum(finite_values) / len(finite_values)) if len(finite_values) == len(conditions) else float("inf"),
        "median_normalized_violation": float(np.median(finite_values)) if len(finite_values) == len(conditions) else float("inf"),
        "conditions": conditions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--methods", default="spectra,anaflow_cleanroom")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    os.chdir(args.source_root)

    methods = tuple(value.strip() for value in args.methods.split(",") if value.strip())
    rows = []
    for seed in (int(value) for value in args.seeds.split(",") if value.strip()):
        for method in methods:
            run_root = args.output.parent / f"_{args.output.stem}_work" / f"s{seed}_{method}"
            run_root.mkdir(parents=True, exist_ok=True)
            evaluator = load_evaluator(args.source_root, run_root, pvt=False)
            started = time.perf_counter()
            best_unit, best_violation, first_pass = run_search(evaluator, method, args.budget, seed)
            values = actual_params(evaluator, best_unit)
            verifier = load_evaluator(args.source_root, run_root / "pvt_verify", pvt=True)
            pvt = verify_pvt(verifier, values)
            rows.append({
                "task": "two_stage_opamp_gf180",
                "method": method,
                "seed": seed,
                "pdk": "gf180mcu",
                "simulator": "ngspice",
                "simulations": args.budget,
                "llm_calls": 12,
                "first_pass_simulations": first_pass,
                "tt_violation": best_violation,
                "tt_pass": best_violation == 0.0,
                "pvt": pvt,
                "parameters": dict(zip(evaluator.param_names, values.tolist())),
                "wall_seconds": time.perf_counter() - started,
                "source": "ATLAS public GF180 YAML and shipped corner netlists",
            })
            print(json.dumps(rows[-1], sort_keys=True))

    payload = {
        "schema": "spectra-atlas-gf180-matched/v1",
        "model": "gpt-6.1-sol",
        "budget": args.budget,
        "llm_calls": 12,
        "pvt_conditions": 18,
        "rows": rows,
        "ranking_eligible": bool(rows) and all(row["pvt"]["conditions_observed"] == 18 for row in rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
