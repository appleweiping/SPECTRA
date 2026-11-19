#!/usr/bin/env python3
"""Run a matched, source-native public sizing smoke/matrix.

This runner deliberately keeps public-suite metric semantics separate from the
SIZ7g verifier.  It can produce TT and normalized-violation evidence for the
open-source JSON configs.  PVT is reported as unavailable unless the source
declares a corner-aware evaluator, so a single-netlist result cannot enter the
PVT ranking by accident.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


def _load_benchmark(source_root: Path, config: str):
    sys.path.insert(0, str(source_root))
    from benchmark.ngspice_benchmark import NgspiceBenchmark
    return NgspiceBenchmark.from_config(str(source_root / config))


def _violation(bench, metrics: dict[str, Any]) -> float:
    total = 0.0
    for name, spec in bench.specs.items():
        value = metrics.get(name)
        if value is None or not math.isfinite(float(value)):
            total += 1.0
            continue
        op, target = spec
        scale = max(abs(float(target)), 1.0)
        if op == ">":
            total += max(0.0, (float(target) - float(value)) / scale)
        else:
            total += max(0.0, (float(value) - float(target)) / scale)
    return total / max(1, len(bench.specs))


def _objective(bench, x: np.ndarray) -> tuple[float, dict[str, Any], float]:
    metrics = bench.evaluate(x)
    vio = _violation(bench, metrics)
    return vio, metrics, time.perf_counter()


def _random(bench, seed: int, budget: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    best = None
    first = None
    started = time.perf_counter()
    for index in range(budget):
        x = rng.random(bench.dim)
        vio, metrics, _ = _objective(bench, x)
        if first is None and bench.meets_specs(metrics):
            first = index + 1
        if best is None or vio < best["violation"]:
            best = {"x": x.tolist(), "metrics": metrics, "violation": vio, "tt_pass": bool(bench.meets_specs(metrics))}
    return {"method": "anaflow_cleanroom", "seed": seed, "budget": budget, "best": best, "first_pass": first,
            "simulations": budget, "wall_seconds": time.perf_counter() - started}


def _spectra(bench, seed: int, budget: int) -> dict[str, Any]:
    import cma

    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    best = None
    first = None
    evaluations = 0

    def record(x, vio, metrics):
        nonlocal best, first, evaluations
        evaluations += 1
        passed = bool(bench.meets_specs(metrics))
        if first is None and passed:
            first = evaluations
        if best is None or vio < best["violation"]:
            best = {"x": np.asarray(x).tolist(), "metrics": metrics, "violation": vio, "tt_pass": passed}

    # A small deterministic coverage phase prevents CMA-ES from inheriting a
    # lucky center point on low-dimensional public circuits.
    coverage = min(max(8, 2 * bench.dim), budget // 3)
    for x in rng.random((coverage, bench.dim)):
        vio, metrics, _ = _objective(bench, x)
        record(x, vio, metrics)

    remaining = budget - evaluations
    es = cma.CMAEvolutionStrategy([0.5] * bench.dim, 0.25,
                                   {"bounds": [0, 1], "seed": seed + 1001,
                                    "popsize": max(6, min(16, 4 + int(3 * math.log(max(2, bench.dim)))),
                                    "verbose": -9})
    while evaluations < budget and not es.stop():
        points = es.ask()
        points = [np.clip(point, 0.0, 1.0) for point in points[:remaining]]
        scores = []
        for x in points:
            vio, metrics, _ = _objective(bench, x)
            scores.append(vio)
            record(x, vio, metrics)
            if evaluations >= budget:
                break
        if scores:
            es.tell(points[:len(scores)], scores)
        remaining = budget - evaluations
    return {"method": "spectra_public_adapter", "seed": seed, "budget": budget, "best": best,
            "first_pass": first, "simulations": evaluations, "wall_seconds": time.perf_counter() - started}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    rows = []
    for config in args.config:
        bench = _load_benchmark(args.source_root, config)
        for seed in seeds:
            for runner in (_spectra, _random):
                result = runner(bench, seed, args.budget)
                result.update({"config": config, "task": bench.name, "pdk": config.split("/")[1],
                               "simulator": os.environ.get("SPECTRA_PUBLIC_SIMULATOR", "ngspice"),
                               "pvt_status": "unavailable_source_has_no_corner_evaluator",
                               "pvt_pass": None})
                rows.append(result)
                print(json.dumps(result, sort_keys=True))
    payload = {
        "schema": "spectra-public-suite/v1",
        "model": "gpt-6.1-sol",
        "budget": args.budget,
        "seeds": seeds,
        "rows": rows,
        "ranking_eligible": False,
        "ranking_reason": "TT-only public config results. PVT is unavailable for these source configs and no AnaFlow paper row is implied.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
