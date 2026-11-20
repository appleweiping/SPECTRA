#!/usr/bin/env python3
"""Render the SGAnalog Xyce AC probe receipt as a concise audit table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.receipt.read_text(encoding="utf-8"))
    lines = [
        "# SGAnalog Xyce AC translator probe",
        "",
        f"- Source commit: `{data['source_commit']}`",
        f"- Tasks probed: **{data['task_count']}**",
        f"- Status counts: `{json.dumps(data['status_counts'], sort_keys=True)}`",
        f"- Xyce: `{data['xyce']}`",
        "- Ranking eligibility: **false**",
        "",
        "The probe translates each pinned SGAnalog task deck into a sibling Xyce AC deck, executes Xyce with a bounded timeout, and records the source/translated hashes, return code, log digest, and parser output. The source decks depend on the SGAnalog SKY130 model environment. In this run all 17 probes returned an Xyce parser failure from the included mismatch-function expression, so no AC metric is promoted to a sizing result.",
        "",
        "| Task | Status | Return code | Parsed AC keys |",
        "|---|---|---:|---|",
    ]
    for row in data["tasks"]:
        probe = row["probe"]
        lines.append(
            f"| `{row['task_id']}` | `{probe['status']}` | "
            f"{probe.get('returncode', '')} | "
            f"{', '.join(sorted(probe.get('metrics', {}).keys())) or '—'} |"
        )
    lines.extend([
        "",
        "This is simulator compatibility evidence for the public AC translator. It is not a SIZ7g cell, does not compare SPECTRA with AnaFlow, and cannot support an all-simulator SOTA claim.",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
