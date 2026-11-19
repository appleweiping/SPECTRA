#!/usr/bin/env python3
"""Gate a public cross-domain result table before ranking.

The validator is deliberately conservative.  It rejects duplicate task-method
seed cells, non-exact simulation/call budgets, incomplete PVT grids, missing
violations and unavailable PVT results.  It produces a receipt even when the
table is rejected, which keeps negative evidence auditable.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from spectra.bench.cross_domain import load_manifest, validate_budget, write_receipt


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError("result payload must be a list or an object containing rows")


def validate(rows: list[dict[str, Any]], *, budget: dict[str, int], pvt_conditions: int) -> dict[str, Any]:
    errors: list[str] = []
    keys: set[tuple[Any, ...]] = set()
    eligible_rows = 0
    for index, row in enumerate(rows):
        prefix = f"row[{index}]"
        row_errors: list[str] = []
        key = (row.get("task"), row.get("method"), row.get("seed"), row.get("pdk"), row.get("simulator"))
        if key in keys:
            row_errors.append(f"{prefix}: duplicate cell {key!r}")
        keys.add(key)
        row_errors.extend(f"{prefix}: {error}" for error in validate_budget(row, budget["simulations"], budget["llm_calls"]))
        pvt = row.get("pvt") or row.get("pvt_summary")
        if not isinstance(pvt, dict):
            row_errors.append(f"{prefix}: missing pvt summary")
            errors.extend(row_errors)
            continue
        if pvt.get("conditions_observed") != pvt_conditions:
            row_errors.append(f"{prefix}: observed {pvt.get('conditions_observed')!r} PVT conditions, expected {pvt_conditions}")
        if not isinstance(pvt.get("pvt_success"), bool):
            row_errors.append(f"{prefix}: pvt_success is unavailable")
        for metric in ("mean_normalized_violation", "median_normalized_violation"):
            if not isinstance(pvt.get(metric), (int, float)) or not math.isfinite(float(pvt.get(metric))):
                row_errors.append(f"{prefix}: missing {metric}")
        errors.extend(row_errors)
        if not row_errors:
            eligible_rows += 1
    return {
        "cells_observed": len(rows),
        "unique_cells": len(keys),
        "eligible_rows": eligible_rows,
        "errors": errors,
        "ranking_eligible": bool(rows) and not errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--pvt-conditions", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    track = next((item for item in manifest["tracks"] if item["id"] == args.track_id), None)
    if track is None:
        raise SystemExit(f"unknown track: {args.track_id}")
    payload = json.loads(args.rows.read_text(encoding="utf-8"))
    receipt = validate(_rows(payload), budget=track["budget"], pvt_conditions=args.pvt_conditions)
    receipt.update({"schema": "spectra-cross-domain-validation/v1", "track_id": args.track_id,
                    "manifest": str(args.manifest), "rows": str(args.rows)})
    write_receipt(args.output, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
