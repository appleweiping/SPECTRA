#!/usr/bin/env python3
"""Create a provenance and completeness receipt for a SGAnalog checkout.

This audit deliberately does not run a simulator or score a model.  It checks
the source-native sizing task manifest before ``run_sganalog_native.py`` is
scheduled, resolves the published deck paths, and records the task and class
inventory.  The resulting receipt is a capability gate and cannot be used as
a SIZ7g ranking result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_TASK_FIELDS = ("task_id", "repo", "dut", "klass", "tb_cir", "reference", "n_devices")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_deck(root: Path, task: dict[str, Any]) -> Path:
    rel = Path(str(task["tb_cir"]))
    marker = "out/sim_ui/netlists/"
    if marker in rel.as_posix():
        rel = Path(rel.as_posix().replace(marker, "circuits/", 1))
    return (root / rel).resolve()


def git_commit(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def audit(root: Path) -> dict[str, Any]:
    task_file = root / "eval" / "sizing" / "tasks.jsonl"
    if not task_file.is_file():
        raise FileNotFoundError(task_file)
    tasks: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, raw in enumerate(task_file.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            task = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
            continue
        missing = [name for name in REQUIRED_TASK_FIELDS if name not in task]
        if missing:
            errors.append(f"{task.get('task_id', f'line-{line_number}')}: missing {','.join(missing)}")
        tasks.append(task)

    ids = [str(task.get("task_id", "")) for task in tasks]
    duplicate_ids = sorted(task_id for task_id, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate task ids: {duplicate_ids}")

    manifests: list[dict[str, Any]] = []
    for task in tasks:
        deck = resolve_deck(root, task)
        reference = task.get("reference")
        device_count = len(reference) if isinstance(reference, dict) else 0
        deck_exists = deck.is_file()
        if not deck_exists:
            errors.append(f"{task.get('task_id')}: missing deck {deck}")
        if int(task.get("n_devices", -1)) != device_count:
            errors.append(
                f"{task.get('task_id')}: n_devices={task.get('n_devices')} reference={device_count}"
            )
        manifests.append(
            {
                "task_id": task.get("task_id"),
                "repo": task.get("repo"),
                "dut": task.get("dut"),
                "klass": task.get("klass"),
                "n_devices": task.get("n_devices"),
                "reference_devices": device_count,
                "deck_relpath": str(deck.relative_to(root)) if deck.is_relative_to(root) else str(deck),
                "deck_exists": deck_exists,
                "deck_sha256": sha256(deck) if deck_exists else None,
            }
        )

    class_counts = Counter(str(task.get("klass", "unknown")) for task in tasks)
    return {
        "schema": "sganalog-source-audit/v1",
        "benchmark": "SGAnalog",
        "source_commit": git_commit(root),
        "task_file": str(task_file),
        "task_file_sha256": sha256(task_file),
        "task_count": len(tasks),
        "expected_task_count": 17,
        "task_count_matches_expected": len(tasks) == 17,
        "class_counts": dict(sorted(class_counts.items())),
        "deck_count": sum(bool(item["deck_exists"]) for item in manifests),
        "tasks": manifests,
        "errors": errors,
        "complete": not errors and len(tasks) == 17,
        "ranking_eligible": False,
        "boundary": "source audit only; native Task 2 rows require run_sganalog_native.py and are not SIZ7g cells",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sg-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit(args.sg_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("task_count", "deck_count", "complete", "ranking_eligible")}, sort_keys=True))
    if not receipt["complete"]:
        raise SystemExit("SGAnalog source audit failed: " + "; ".join(receipt["errors"][:8]))


if __name__ == "__main__":
    main()
