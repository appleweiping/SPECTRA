#!/usr/bin/env python3
"""Audit the literal XSOTA-1 gate from merged public receipts.

The audit is intentionally conservative.  It only compares rows that have a
complete merged receipt, a matched ``anaflow_cleanroom`` reference and a
``spectra`` row with finite TT/PVT success and violation aggregates.  A tie is
not a strict lead.  Missing or capability-only strata are reported as
uncovered rather than silently removed from the denominator.

This is an evidence checker, not an experiment launcher.  Run it on the
server checkout after merging receipts, then copy the validated receipt to the
local E: checkout.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


REQUIRED_METHODS = ("anaflow_cleanroom", "spectra")
REQUIRED_ENDPOINTS = (
    "tt_success",
    "pvt_success",
    "mean_tt_violation",
    "mean_pvt_violation",
)


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def compare(anflow: dict[str, Any], spectra: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "tt_success": float(spectra["tt_success"]) > float(anflow["tt_success"]),
        "pvt_success": float(spectra["pvt_success"]) > float(anflow["pvt_success"]),
        "mean_tt_violation": float(spectra["mean_tt_violation"]) < float(anflow["mean_tt_violation"]),
        "mean_pvt_violation": float(spectra["mean_pvt_violation"]) < float(anflow["mean_pvt_violation"]),
    }
    return {
        "anaflow": {key: anflow[key] for key in REQUIRED_ENDPOINTS},
        "spectra": {key: spectra[key] for key in REQUIRED_ENDPOINTS},
        "strict_endpoint_leads": checks,
        "strict_all_endpoints": all(checks.values()),
    }


def audit(root: Path) -> dict[str, Any]:
    strata: list[dict[str, Any]] = []
    uncovered: list[str] = []
    for path in sorted(root.glob("*_merged.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        record: dict[str, Any] = {
            "receipt": path.name,
            "complete": bool(payload.get("complete")),
            "ranking_eligible": bool(payload.get("ranking_eligible")),
            "pvt_conditions": payload.get("pvt_conditions"),
            "errors": list(payload.get("errors", [])),
        }
        aggregate = payload.get("aggregate")
        if not record["complete"] or not record["ranking_eligible"]:
            record["tier"] = "uncovered"
            record["reason"] = "receipt is incomplete or ranking-ineligible"
            uncovered.append(path.name)
            strata.append(record)
            continue
        if not isinstance(aggregate, dict) or any(method not in aggregate for method in REQUIRED_METHODS):
            record["tier"] = "uncovered"
            record["reason"] = "matched AnaFlow and SPECTRA aggregates are unavailable"
            uncovered.append(path.name)
            strata.append(record)
            continue
        anaflow = aggregate["anaflow_cleanroom"]
        spectra = aggregate["spectra"]
        missing = [
            f"{method}.{endpoint}"
            for method, values in (("anaflow_cleanroom", anaflow), ("spectra", spectra))
            for endpoint in REQUIRED_ENDPOINTS
            if not isinstance(values, dict) or not finite(values.get(endpoint))
        ]
        if missing:
            record["tier"] = "uncovered"
            record["reason"] = "missing or non-finite endpoint aggregates"
            record["missing"] = missing
            uncovered.append(path.name)
            strata.append(record)
            continue
        record["tier"] = "strict-pvt-comparison"
        record["comparison"] = compare(anaflow, spectra)
        strata.append(record)

    comparable = [item for item in strata if item["tier"] == "strict-pvt-comparison"]
    strict_pass = bool(comparable) and not uncovered and all(item["comparison"]["strict_all_endpoints"] for item in comparable)
    return {
        "schema": "spectra-xsota-gate-audit/v1",
        "gate": "XSOTA-1",
        "strict_definition": "SPECTRA must strictly beat matched AnaFlow on TT success, PVT success, mean TT violation, and mean PVT violation in every declared public stratum",
        "root": str(root),
        "receipts_observed": len(strata),
        "comparable_strata": len(comparable),
        "uncovered_strata": len(uncovered),
        "uncovered_receipts": uncovered,
        "strict_gate_pass": strict_pass,
        "strata": strata,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("results"))
    parser.add_argument("--json-output", type=Path, default=Path("results/xsota_gate_audit.json"))
    parser.add_argument("--md-output", type=Path, default=Path("results/xsota_gate_audit.md"))
    args = parser.parse_args()
    receipt = audit(args.root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# XSOTA-1 gate audit",
        "",
        receipt["strict_definition"],
        "",
        f"Strict gate: **{'PASS' if receipt['strict_gate_pass'] else 'NOT MET'}**",
        f"Comparable strata: {receipt['comparable_strata']}; uncovered receipts: {receipt['uncovered_strata']}.",
        "",
        "| Receipt | Tier | TT lead | PVT lead | TT violation lead | PVT violation lead | All endpoints |",
        "|---|---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for item in receipt["strata"]:
        comparison = item.get("comparison", {})
        leads = comparison.get("strict_endpoint_leads", {})
        fmt = lambda key: "yes" if leads.get(key, False) else "no"
        lines.append(
            f"| `{item['receipt']}` | {item['tier']} | {fmt('tt_success')} | {fmt('pvt_success')} | {fmt('mean_tt_violation')} | {fmt('mean_pvt_violation')} | {'yes' if comparison.get('strict_all_endpoints', False) else 'no'} |"
        )
    lines += [
        "",
        "Uncovered or capability-only receipts remain in this audit and count against the literal gate. A benchmark-scoped lead does not change the gate result.",
    ]
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("receipts_observed", "comparable_strata", "uncovered_strata", "strict_gate_pass")}, sort_keys=True))


if __name__ == "__main__":
    main()
