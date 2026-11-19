"""Aggregate one completed sizing experiment directory.

This helper is intentionally independent of the primary-track aggregator. It
supports candidate strategy experiments where all seeds are stored under one
experiment name, while preserving the same cell-level metrics and robust-task
filter used by the main sizing reports.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _tasks(path: Path):
    return {json.loads(line)["id"]: json.loads(line) for line in path.read_text().splitlines() if line.strip()}


def _records(root: Path, exp: str):
    out = []
    for path in (root / "results" / "raw" / exp).glob("*/*/s*.json"):
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        record["_path"] = str(path)
        out.append(record)
    return out


def _metric(record, name):
    verify = record.get("verify", {})
    if name == "tt":
        return bool(verify.get("tt_pass"))
    if name == "pvt":
        value = verify.get("pvt_pass")
        return bool(value) if value is not None else None
    if name == "tt_violation":
        value = verify.get("tt_score")
    else:
        value = verify.get("pvt_score")
    return float(value) if isinstance(value, (int, float)) else None


def aggregate(exp: str, subset: str, root: Path):
    tasks = _tasks(root / subset)
    records = [r for r in _records(root, exp) if r.get("task") in tasks]
    groups = defaultdict(list)
    for record in records:
        groups[record.get("task")].append(record)
    rows = []
    for task_id in tasks:
        task_records = groups.get(task_id, [])
        robust = bool(tasks[task_id].get("robust"))
        rows.append({
            "task": task_id,
            "family": tasks[task_id].get("family"),
            "robust": robust,
            "cells": len(task_records),
            "tt_success": sum(_metric(r, "tt") for r in task_records),
            "pvt_success": sum(_metric(r, "pvt") is True for r in task_records),
            "tt_violation": [v for r in task_records if (v := _metric(r, "tt_violation")) is not None],
            "pvt_violation": [v for r in task_records if (v := _metric(r, "pvt_violation")) is not None],
            "crashes": sum(r.get("status") == "crash" for r in task_records),
        })
    all_records = records
    robust_records = [r for r in all_records if tasks.get(r.get("task"), {}).get("robust")]
    result = {
        "experiment": exp,
        "subset": subset,
        "cells_observed": len(all_records),
        "cells_expected": len(tasks) * 3,
        "task_count": len(tasks),
        "family_count": len({t.get("family") for t in tasks.values()}),
        "tt_success": sum(_metric(r, "tt") for r in all_records) / len(all_records) if all_records else 0.0,
        "pvt_success": sum(_metric(r, "pvt") is True for r in robust_records) / len(robust_records) if robust_records else 0.0,
        "mean_tt_violation": sum(_metric(r, "tt_violation") or 0.0 for r in all_records) / len(all_records) if all_records else 0.0,
        "mean_pvt_violation": sum(_metric(r, "pvt_violation") or 0.0 for r in robust_records) / len(robust_records) if robust_records else 0.0,
        "crashes": sum(r.get("status") == "crash" for r in all_records),
        "rows": rows,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", required=True)
    parser.add_argument("--subset", default="data/bench/paper_sizing_tasks.jsonl")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = aggregate(args.exp, args.subset, Path(args.root).resolve())
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
