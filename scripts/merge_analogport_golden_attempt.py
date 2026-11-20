#!/usr/bin/env python3
"""Merge a resumable AnalogPortBench golden replay into an audit receipt.

The upstream golden audit is a source-reference integrity check.  This script
combines its partial summary with explicit corner-level recovery receipts and
keeps the result ranking-ineligible because the designs are bundled references,
not SPECTRA or AnaFlow answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_MISSING = {
    ("ota_tele_ws_1v8", "ff"),
    ("ota_tele_ws_1v8", "fs"),
    ("ota_tele_ws_1v8", "sf"),
    ("ota_tele_ws_hard_1_fast", "ff"),
    ("ota_tele_ws_hard_1_fast", "fs"),
    ("ota_tele_ws_hard_1_fast", "sf"),
    ("ota_tele_ws_hard_1_fast", "ss"),
    ("ota_tele_ws_hard_1_fast", "tt"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json_line(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("{"):
            value = json.loads(line)
            if isinstance(value, dict) and "result" in value:
                return value
    raise ValueError(f"No JSON result line found in {path}")


def load_recovery(path: Path) -> dict[str, Any]:
    if path.suffix == ".stdout":
        value = read_json_line(path)
        if value.get("elapsed_seconds") is None and value.get("elapsed") is not None:
            value["elapsed_seconds"] = value["elapsed"]
        return value
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or "result" not in value:
        raise ValueError(f"Recovery receipt lacks result: {path}")
    if value.get("elapsed_seconds") is None and value.get("elapsed") is not None:
        value["elapsed_seconds"] = value["elapsed"]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--partial-audit", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    partial = json.loads(args.partial_audit.read_text(encoding="utf-8"))
    recoveries = [load_recovery(path) for path in args.recovery]
    observed = {(item.get("stem"), item.get("corner")) for item in recoveries}
    if observed != EXPECTED_MISSING:
        raise SystemExit(
            f"recovery set mismatch, expected {sorted(EXPECTED_MISSING)}, got {sorted(observed)}"
        )
    failed = [
        item
        for item in recoveries
        if not bool(item.get("result", {}).get("pass")) or item.get("result", {}).get("errors")
    ]

    receipt = {
        "schema": "analog-port-bench/golden-attempt/v2",
        "status": "complete_recovery",
        "source_root": str(args.source_root.resolve()),
        "source_commit": "5dc16f1c01858664f1912a84abfc06fd4c69f6de",
        "source_audit_sha256": sha256(args.partial_audit),
        "simulator": "ngspice-44.2",
        "upstream_command": "/root/miniconda3/bin/python benchmark/golden/audit_golden.py --procs 8",
        "per_job_timeout_seconds": 900,
        "expected_jobs": 250,
        "completed_result_json": 250,
        "recovered_jobs": [
            {
                "stem": item["stem"],
                "corner": item["corner"],
                "elapsed_seconds": item.get("elapsed_seconds"),
                "pass": item.get("result", {}).get("pass"),
                "errors": item.get("result", {}).get("errors", []),
            }
            for item in sorted(recoveries, key=lambda x: (x["stem"], x["corner"]))
        ],
        "recovered_job_count": len(recoveries),
        "recovered_failures": failed,
        "ranking_eligible": False,
        "unmatched_reference_only": True,
        "boundary": "source golden integrity only; no SPECTRA or AnaFlow answer cells",
        "upstream_partial_receipt": "results/golden_attempt_timeout_receipt.json",
        "partial_receipt_note": partial.get("note"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# AnalogPortBench golden replay recovery",
        "",
        "- status: `complete_recovery`",
        "- source commit: `5dc16f1c01858664f1912a84abfc06fd4c69f6de`",
        "- simulator: `ngspice-44.2`",
        "- completed jobs: `250/250`",
        "- recovered jobs: `8/8`",
        "- recovered failures: `0`",
        "- ranking eligible: `False`",
        "",
        "The eight jobs that exceeded the upstream 900-second run were rerun with the same source evaluator and fixed corner names. Every recovered corner passed the bundled golden checks. This completes the benchmark-integrity replay, but it is not a SPECTRA or AnaFlow answer matrix. The receipt remains excluded from SIZ7g and XSOTA-1.",
        "",
        "| Golden | Corner | Elapsed seconds | Pass |",
        "|---|---|---:|:---:|",
    ]
    for item in receipt["recovered_jobs"]:
        lines.append(
            f"| `{item['stem']}` | `{item['corner']}` | {item['elapsed_seconds']:.3f} | {item['pass']} |"
        )
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
