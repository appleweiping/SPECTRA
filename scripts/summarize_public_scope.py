#!/usr/bin/env python3
"""Build a measured-scope public cross-domain receipt table.

The report intentionally consumes only merged JSON receipts. Missing future
strata are omitted until their strict merge exists, while every completed
stratum retains its stored ranking flag, success, violation, first-pass and
wall-time values.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


TRACKS = [
    ("analoggym_pvt_merged.json", "AnalogGym / HoiLee", "SKY130", "ngspice-44.2"),
    ("analoggym_xyce_merged.json", "AnalogGym / HoiLee", "SKY130", "Xyce-7.10"),
    ("analoggym_leung_pvt_merged.json", "AnalogGym / Leung", "SKY130", "ngspice-44.2"),
    ("analoggym_leung_xyce_merged.json", "AnalogGym / Leung", "SKY130", "Xyce-7.10"),
    ("atlas_gf180_matched_merged.json", "ATLAS public task", "GF180MCU", "ngspice-44.2"),
    ("public_v6_sky130_lp_merged.json", "opensource / SKY130 LP opamp tuned", "SKY130", "ngspice-44.2"),
    ("public_v8_sky130_lp_xyce_merged.json", "opensource / SKY130 LP opamp", "SKY130", "Xyce-7.10"),
    ("public_v3_asap7_ldo_merged.json", "opensource / ASAP7 LDO", "ASAP7", "ngspice-44.2"),
    ("public_v4_ldo_simple_merged.json", "opensource / SKY130 LDO", "SKY130", "ngspice-44.2"),
    ("public_v5_ptm180_merged.json", "opensource / PTM180 opamp", "PTM180", "ngspice-44.2"),
    ("public_v7_ptm45_merged.json", "opensource / PTM45 gh_autockt opamp", "PTM45", "ngspice-44.2"),
    ("public_v5_bjt_merged.json", "opensource / BJT CE amplifier", "BJT", "ngspice-44.2"),
    ("public_x1_v3_bjt_merged.json", "opensource / BJT CE amplifier", "BJT", "Xyce-7.10"),
]


def finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def aggregate(rows: list[dict]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("method", "unknown")), []).append(row)
    result: dict[str, dict[str, float | int]] = {}
    for method, method_rows in sorted(grouped.items()):
        count = max(1, len(method_rows))
        pvt = [row.get("pvt", {}).get("mean_normalized_violation") for row in method_rows]
        first = [row.get("first_pass_simulations") for row in method_rows]
        walls = [row.get("wall_seconds") for row in method_rows]
        result[method] = {
            "cells": len(method_rows),
            "tt_success": sum(bool(row.get("tt_pass")) for row in method_rows) / count,
            "pvt_success": sum(bool(row.get("pvt", {}).get("pvt_success")) for row in method_rows) / count,
            "mean_tt_violation": sum(float(row.get("tt_violation", float("nan"))) for row in method_rows) / count,
            "mean_pvt_violation": sum(float(value) for value in pvt if finite(value)) / max(1, sum(finite(value) for value in pvt)),
            "mean_first_pass": sum(float(value) for value in first if finite(value)) / max(1, sum(finite(value) for value in first)),
            "mean_wall_seconds": sum(float(value) for value in walls if finite(value)) / max(1, sum(finite(value) for value in walls)),
        }
    return result


def fmt(value: object, digits: int = 4) -> str:
    return "NA" if not finite(value) else f"{float(value):.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/public_scope_sota_summary.md"))
    parser.add_argument("--json-output", type=Path, default=Path("results/public_scope_sota_summary.json"))
    args = parser.parse_args()

    records: list[dict] = []
    for filename, track, pdk, simulator in TRACKS:
        path = args.root / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
        computed = aggregate(rows)
        values = json.loads(json.dumps(payload.get("aggregate") or computed))
        for method, computed_values in computed.items():
            values.setdefault(method, {}).update({
                key: value for key, value in computed_values.items()
                if key not in values.get(method, {})
            })
        records.append({
            "receipt": filename,
            "track": track,
            "pdk": pdk,
            "simulator": simulator,
            "budget": payload.get("budget"),
            "llm_calls": payload.get("llm_calls"),
            "pvt_conditions": payload.get("pvt_conditions"),
            # Older public-config receipts predate the explicit `complete`
            # field.  Their strict merger already records the same contract
            # as `ranking_eligible`, so use that field as a compatibility
            # fallback while retaining one-condition receipts as incomplete.
            "complete": bool(payload.get("complete", payload.get("ranking_eligible"))),
            "stored_ranking_eligible": bool(payload.get("ranking_eligible")),
            "protocol_eligible": bool(payload.get("complete", payload.get("ranking_eligible"))) and not payload.get("errors") and (payload.get("pvt_conditions") or 0) > 1,
            "errors": list(payload.get("errors", [])),
            "aggregate": values,
        })

    lines = [
        "# Public cross-domain measured-scope summary",
        "",
        "This file is generated by `scripts/summarize_public_scope.py` from strict merged receipts. Every listed cell uses the recorded 300-simulation and 12-call budget with seeds 0/1/2. A one-condition source receipt is retained as TT-only capability evidence and excluded from PVT ranking.",
        "",
        "## Receipt coverage",
        "",
        "| Receipt | Track | PDK | Simulator | PVT conditions | Complete | Stored ranking flag | Protocol-eligible | Errors |",
        "|---|---|---|---|---:|:---:|:---:|:---:|---:|",
    ]
    for record in records:
        lines.append(f"| `{record['receipt']}` | {record['track']} | {record['pdk']} | {record['simulator']} | {record['pvt_conditions']} | {'yes' if record['complete'] else 'no'} | {'yes' if record['stored_ranking_eligible'] else 'no'} | {'yes' if record['protocol_eligible'] else 'no'} | {len(record['errors'])} |")

    lines += [
        "",
        "## Method metrics",
        "",
        "| Track | PDK | Simulator | Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean first-pass simulations | Mean wall seconds | Tier |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    exported: list[dict] = []
    for record in records:
        tier = "PVT ranking" if record["protocol_eligible"] else ("TT-only capability" if record["pvt_conditions"] == 1 else "complete but flag-ineligible")
        for method, values in sorted(record["aggregate"].items()):
            row = {"receipt": record["receipt"], "track": record["track"], "pdk": record["pdk"], "simulator": record["simulator"], "method": method, "tier": tier, **values}
            exported.append(row)
            lines.append(f"| {record['track']} | {record['pdk']} | {record['simulator']} | `{method}` | {values.get('cells', 'NA')} | {fmt(values.get('tt_success'))} | {fmt(values.get('pvt_success'))} | {fmt(values.get('mean_tt_violation'))} | {fmt(values.get('mean_pvt_violation'))} | {fmt(values.get('mean_simulations_to_first_pass', values.get('mean_first_pass')), 2)} | {fmt(values.get('mean_wall_seconds'), 2)} | {tier} |")

    lines += [
        "",
        "## Claim scope",
        "",
        "The table supports a measured-scope comparison over the listed public strata. It preserves ties, violation leads, endpoint failures, and efficiency trade-offs. It does not support a literal all-circuit, all-PDK, all-simulator SOTA claim because unlisted source suites and simulator translators remain outside the strict ranking matrix.",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps({"schema": "spectra-public-scope-summary/v1", "records": records, "rows": exported}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipts": len(records), "rows": len(exported), "protocol_pvt_receipts": sum(record["protocol_eligible"] for record in records)}))


if __name__ == "__main__":
    main()
