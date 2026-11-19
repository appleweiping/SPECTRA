#!/usr/bin/env python3
"""Strictly merge matched ATLAS/GF180 public PVT shards.

The adapter emits one row per seed/method.  This merger checks the exact
simulation budget, GPT call budget, shipped-condition count, and finite
violations before producing a ranking receipt.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
from collections import defaultdict
from pathlib import Path


def finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--calls", type=int, default=12)
    parser.add_argument("--pvt-conditions", type=int, default=17)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--methods", default="spectra,anaflow_cleanroom")
    args = parser.parse_args()

    paths: list[Path] = []
    for pattern in args.input:
        matches = [Path(item) for item in glob.glob(pattern)]
        paths.extend(matches or [Path(pattern)])
    expected_seeds = {int(item) for item in args.seeds.split(",") if item.strip()}
    expected_methods = {item.strip() for item in args.methods.split(",") if item.strip()}
    errors: list[str] = []
    rows: list[dict] = []
    seen: set[tuple[int, str]] = set()
    for path in sorted(set(paths)):
        if not path.exists():
            errors.append(f"missing shard: {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid shard {path}: {type(exc).__name__}")
            continue
        if payload.get("budget") != args.budget:
            errors.append(f"{path}: payload budget={payload.get('budget')} expected {args.budget}")
        if payload.get("pvt_conditions") != args.pvt_conditions:
            errors.append(f"{path}: payload PVT={payload.get('pvt_conditions')} expected {args.pvt_conditions}")
        for row in payload.get("rows", []):
            key = (int(row.get("seed", -1)), str(row.get("method")))
            if key in seen:
                errors.append(f"duplicate cell seed={key[0]} method={key[1]}")
            seen.add(key)
            rows.append(row)
            if row.get("simulations") != args.budget:
                errors.append(f"{path}: simulations={row.get('simulations')} expected {args.budget}")
            if row.get("llm_calls") != args.calls:
                errors.append(f"{path}: llm_calls={row.get('llm_calls')} expected {args.calls}")
            pvt = row.get("pvt", {})
            if pvt.get("conditions_observed") != args.pvt_conditions:
                errors.append(f"{path}: PVT conditions={pvt.get('conditions_observed')} expected {args.pvt_conditions}")
            for name in ("tt_violation",):
                if not finite(row.get(name)):
                    errors.append(f"{path}: non-finite {name}")
            for name in ("mean_normalized_violation", "median_normalized_violation"):
                if not finite(pvt.get(name)):
                    errors.append(f"{path}: non-finite pvt.{name}")
            for condition in pvt.get("conditions", []):
                if not finite(condition.get("normalized_violation")):
                    errors.append(f"{path}: non-finite condition violation {condition.get('condition')}")

    expected = {(seed, method) for seed in expected_seeds for method in expected_methods}
    missing = sorted(expected.difference(seen))
    extra = sorted(seen.difference(expected))
    if missing:
        errors.append(f"missing cells: {missing}")
    if extra:
        errors.append(f"unexpected cells: {extra}")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("method"))].append(row)
    aggregate = {}
    for method, method_rows in sorted(grouped.items()):
        n = len(method_rows)
        aggregate[method] = {
            "cells": n,
            "tt_success": sum(bool(row.get("tt_pass")) for row in method_rows) / max(1, n),
            "pvt_success": sum(bool(row.get("pvt", {}).get("pvt_success")) for row in method_rows) / max(1, n),
            "mean_tt_violation": sum(float(row["tt_violation"]) for row in method_rows) / max(1, n),
            "mean_pvt_violation": sum(float(row["pvt"]["mean_normalized_violation"]) for row in method_rows) / max(1, n),
            "mean_wall_seconds": sum(float(row.get("wall_seconds", 0.0)) for row in method_rows) / max(1, n),
        }

    result = {
        "schema": "spectra-atlas-gf180-shards/v1",
        "source": "ATLAS public two_stage_opamp GF180 corner netlists",
        "budget": args.budget,
        "llm_calls": args.calls,
        "pvt_conditions": args.pvt_conditions,
        "expected_seeds": sorted(expected_seeds),
        "expected_methods": sorted(expected_methods),
        "rows": rows,
        "aggregate": aggregate,
        "complete": not errors,
        "ranking_eligible": not errors and all(row.get("ranking_eligible", False) for row in rows),
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("GF180 shard audit failed: " + "; ".join(errors[:8]))


if __name__ == "__main__":
    main()
