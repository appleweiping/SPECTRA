#!/usr/bin/env python3
"""Create a provenance-only receipt for Analog Design Bench v2.

The public repository contains the frozen task manifest and task instructions. It
does not contain the isolated evaluator or the submitted circuit artifacts, so
this command deliberately audits source coverage and metric declarations without
inventing pass rates or converting the benchmark into the SIZ7g ranking track.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


METRIC_PATTERNS = {
    "pvt": r"\bpvt\b|process,?\s*voltage,?\s*and\s*temperature",
    "mismatch": r"mismatch|monte[- ]?carlo|local variation",
    "dc": r"\bdc\b|operating point|dropout|quiescent",
    "ac": r"\bac\b|gain|bandwidth|phase margin|psrr|cmrr|loop gain",
    "transient": r"transient|settling|slew|startup|load[- ]step|line[- ]step",
    "noise": r"noise|\bnef\b",
    "spectral": r"spectral|spur|snr|sndr|sfdr|iip3|compression",
    "frequency": r"\bghz\b|\bmhz\b|frequency",
    "power": r"power|current consumption|efficiency",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def metric_flags(text: str, task_id: str = "") -> list[str]:
    lowered = f"{task_id} {text}".lower()
    return sorted(
        name for name, pattern in METRIC_PATTERNS.items() if re.search(pattern, lowered)
    )


def inspect_task(root: Path, task_id: str) -> dict[str, object]:
    task_dir = root / "tasks" / task_id
    task_toml = task_dir / "task.toml"
    instruction = task_dir / "instruction.md"
    task_data = tomllib.loads(task_toml.read_text(encoding="utf-8"))
    instruction_text = instruction.read_text(encoding="utf-8")
    task_meta = task_data.get("task", {})
    metadata = task_data.get("metadata", {})
    return {
        "task_id": task_id,
        "task_schema_version": task_data.get("schema_version"),
        "instruction_sha256": sha256_file(instruction),
        "task_toml_sha256": sha256_file(task_toml),
        "instruction_bytes": instruction.stat().st_size,
        "artifact_paths": task_data.get("artifacts", []),
        "name": task_meta.get("name"),
        "description": task_meta.get("description"),
        "authors": task_meta.get("authors", []),
        "keywords": task_meta.get("keywords", []),
        "declared_task_id": metadata.get("task_id"),
        "metric_flags": metric_flags(instruction_text, task_id),
        "has_verifier_block": "verifier" in task_data,
        "has_pvt": bool(re.search(r"\bpvt\b|process,?\s*voltage,?\s*and\s*temperature", f"{task_id} {instruction_text}", re.I)),
        "has_mismatch": bool(re.search(r"mismatch|monte[- ]?carlo|local variation", f"{task_id} {instruction_text}", re.I)),
    }


def markdown(receipt: dict[str, object]) -> str:
    tasks = receipt["tasks"]
    rows = []
    for task in tasks:
        flags = ", ".join(task["metric_flags"])
        rows.append(
            f"| `{task['task_id']}` | {flags or 'none'} | "
            f"{'yes' if task['has_pvt'] else 'no'} | {'yes' if task['has_mismatch'] else 'no'} |"
        )
    header = """# Analog Design Bench v2 source audit

This receipt audits the public frozen task manifest and instruction files on the
server. The repository does not ship the isolated evaluator or submitted circuit
artifacts. No electrical score, pass rate, or SIZ7g ranking cell is inferred from
this source-only audit.

"""
    summary = receipt["summary"]
    body = (
        f"- Release: `{receipt['release_id']}`\n"
        f"- Source commit: `{receipt['source_commit']}`\n"
        f"- Tasks: {summary['task_count']} manifest slots, "
        f"{summary['task_files']} complete task directories\n"
        f"- PVT-declared tasks: {summary['pvt_tasks']}\n"
        f"- Mismatch-declared tasks: {summary['mismatch_tasks']}\n"
        f"- Ranking status: `{receipt['ranking_status']}`\n"
        f"- Blocking evidence: {receipt['ranking_blocker']}\n\n"
        "## Task metric declarations\n\n"
        "| Task | Text-derived metric flags | PVT | Mismatch |\n"
        "|---|---|:---:|:---:|\n"
        + "\n".join(rows)
        + "\n"
    )
    return header + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    manifest_path = root / "tasks" / "benchmark.toml"
    defaults_path = root / "tasks" / "defaults.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    defaults = tomllib.loads(defaults_path.read_text(encoding="utf-8"))
    task_ids = [entry["id"] for entry in manifest.get("tasks", [])]
    tasks = [inspect_task(root, task_id) for task_id in task_ids]
    complete = [task for task in tasks if task["artifact_paths"] and (root / "tasks" / task["task_id"] / "instruction.md").is_file()]
    receipt = {
        "schema": "analog-design-bench-source-audit/v1",
        "release_id": manifest.get("release_id"),
        "source_commit": git_value(root, "rev-parse", "HEAD"),
        "source_url": "https://github.com/Arcadia-1/analog-design-bench",
        "manifest_sha256": sha256_file(manifest_path),
        "defaults_sha256": sha256_file(defaults_path),
        "defaults": defaults,
        "ranking_status": "capability_only_source_audit",
        "ranking_blocker": "isolated verifier and submitted circuit artifacts are external to this git source; no matched SPECTRA/AnaFlow cells were run",
        "declared_protocol": {
            "source_native": True,
            "common_siz7g": False,
            "pvt_and_mismatch": "task-defined",
            "independent_verifier": "required but not present in cloned source",
        },
        "summary": {
            "manifest_slots": len(task_ids),
            "task_count": len(task_ids),
            "task_files": len(complete),
            "pvt_tasks": sum(bool(task["has_pvt"]) for task in tasks),
            "mismatch_tasks": sum(bool(task["has_mismatch"]) for task in tasks),
        },
        "tasks": tasks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(receipt), encoding="utf-8")
    print(json.dumps(receipt["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
