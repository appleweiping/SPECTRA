#!/usr/bin/env python3
"""Audit AnalogPortBench coverage and optional server-side golden evidence.

The public AnalogPortBench repository contains 54 prompts, source circuits,
50 feasible golden SKY130 designs and four deliberately infeasible task
families.  This command records the pinned source tree and checks that the
task/golden inventory is complete.  An optional golden result JSON can be
attached when the source evaluator was actually run on the server.

The command never treats a golden design audit as a SPECTRA/AnaFlow ranking
cell.  A matched transfer result requires model answers, the source evaluator,
the target PDK, the same resource accounting, and an independent receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


TASK_RE = re.compile(r"^(T[1-4])__[^/]+\.txt$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def task_inventory(root: Path) -> dict[str, Any]:
    prompt_dir = root / "prompts"
    task_files = sorted(
        path for path in prompt_dir.glob("*.txt") if TASK_RE.match(path.name)
    )
    tiers = Counter(TASK_RE.match(path.name).group(1) for path in task_files)
    circuit_dir = root / "benchmark" / "circuits"
    circuits = sorted(path.name for path in circuit_dir.iterdir() if path.is_dir())
    source_count = sum(1 for path in circuit_dir.glob("*/source_180n.sp"))
    golden_files = sorted((root / "benchmark" / "golden").glob("*.sp"))
    return {
        "prompt_files": len(task_files),
        "task_ids": [path.stem for path in task_files],
        "tier_counts": dict(sorted(tiers.items())),
        "circuit_count": len(circuits),
        "circuits": circuits,
        "source_180n_count": source_count,
        "golden_netlist_count": len(golden_files),
        "golden_netlist_sha256": {
            path.stem: sha256(path) for path in golden_files
        },
        "missing_source_180n": sorted(
            name for name in circuits if not (circuit_dir / name / "source_180n.sp").is_file()
        ),
    }


def golden_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "attached": False,
            "status": "not_run",
            "ranking_eligible": False,
        }
    if not path.is_file():
        return {
            "attached": False,
            "status": "missing",
            "path": str(path),
            "ranking_eligible": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "attached": True,
            "status": "invalid",
            "path": str(path),
            "error": f"{type(exc).__name__}: {exc}",
            "ranking_eligible": False,
        }
    rows = payload.values() if isinstance(payload, dict) else []
    rows = list(rows)
    complete_corner_rows = [
        row for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("corners_pass"), dict)
        and len(row["corners_pass"]) == 5
    ]
    all_corner_pass = [
        row for row in complete_corner_rows
        if all(bool(value) for value in row["corners_pass"].values())
    ]
    issue_counts: Counter[str] = Counter()
    for row in rows:
        if isinstance(row, dict):
            issue_counts.update(str(issue) for issue in row.get("issues", []))
    return {
        "attached": True,
        "status": "complete" if rows else "empty",
        "path": str(path),
        "sha256": sha256(path),
        "golden_rows": len(rows),
        "golden_pass_rows": sum(bool(row.get("pass")) for row in rows if isinstance(row, dict)),
        "golden_all_corner_pass_rows": len(all_corner_pass),
        "golden_complete_corner_rows": len(complete_corner_rows),
        "golden_issue_counts": dict(issue_counts),
        "ranking_eligible": False,
        "boundary": "golden source audit only; no SPECTRA or AnaFlow answer cells",
    }


def build_receipt(root: Path, golden_path: Path | None) -> dict[str, Any]:
    inventory = task_inventory(root)
    license_path = root / "LICENSE"
    expected = {
        "source_commit": git(root, "rev-parse", "HEAD"),
        "source_url": "https://github.com/saeidrajabii/AnalogPortBench",
        "paper_url": "https://arxiv.org/abs/2610.33088",
        "license": {
            "path": str(license_path),
            "present": license_path.is_file(),
            "sha256": sha256(license_path) if license_path.is_file() else None,
        },
        "inventory": inventory,
        "golden_audit": golden_summary(golden_path),
        "protocol": {
            "task_total": 54,
            "feasible_tiers": ["T1", "T2", "T3"],
            "infeasible_tier": "T4",
            "source_process": "0.18um",
            "target_process": "SKY130",
            "source_corners": 5,
            "simulator": "ngspice",
            "simulation_feedback_attempts": 3,
            "common_siz7g": False,
        },
        "ranking_eligible": False,
        "ranking_blocker": "source benchmark audit and golden references do not provide matched SPECTRA/AnaFlow transfer answer cells under the common SIZ7g budget",
    }
    expected["complete_manifest"] = (
        inventory["prompt_files"] == 54
        and inventory["tier_counts"] == {"T1": 10, "T2": 12, "T3": 28, "T4": 4}
        and inventory["source_180n_count"] == inventory["circuit_count"]
        and not inventory["missing_source_180n"]
        and inventory["golden_netlist_count"] == 50
    )
    return expected


def markdown(receipt: dict[str, Any]) -> str:
    inv = receipt["inventory"]
    gold = receipt["golden_audit"]
    lines = [
        "# AnalogPortBench source and golden audit",
        "",
        "This server receipt checks the public benchmark inventory and attaches",
        "a source evaluator golden audit when available. It is not a matched",
        "SPECTRA/AnaFlow transfer ranking result.",
        "",
        f"- Source commit: `{receipt['source_commit']}`",
        f"- Manifest complete: `{receipt['complete_manifest']}`",
        f"- Tasks: {inv['prompt_files']} ({inv['tier_counts']})",
        f"- Circuits with 0.18um sources: {inv['source_180n_count']}/{inv['circuit_count']}",
        f"- Golden netlists: {inv['golden_netlist_count']}",
        f"- Golden audit: `{gold['status']}` ({gold.get('golden_rows', 0)} rows)",
        f"- Ranking eligible: `{receipt['ranking_eligible']}`",
        "",
        "The source tree defines 54 tasks, including four infeasible T4 tasks.",
        "The source evaluator and golden references validate benchmark integrity",
        "under ngspice/SKY130. They do not evaluate SPECTRA or AnaFlow answers.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--golden-json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_receipt(args.source_root.resolve(), args.golden_json.resolve() if args.golden_json else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(receipt), encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("source_commit", "complete_manifest", "ranking_eligible")}, sort_keys=True))
    if not receipt["complete_manifest"]:
        raise SystemExit("AnalogPortBench manifest audit failed")


if __name__ == "__main__":
    main()
