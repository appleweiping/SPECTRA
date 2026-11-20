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
    non_inferior_checks = {
        "tt_success": float(spectra["tt_success"]) >= float(anflow["tt_success"]),
        "pvt_success": float(spectra["pvt_success"]) >= float(anflow["pvt_success"]),
        "mean_tt_violation": float(spectra["mean_tt_violation"]) <= float(anflow["mean_tt_violation"]),
        "mean_pvt_violation": float(spectra["mean_pvt_violation"]) <= float(anflow["mean_pvt_violation"]),
    }
    zero_floor_ties = {}
    for endpoint in REQUIRED_ENDPOINTS:
        left = float(anflow[endpoint])
        right = float(spectra[endpoint])
        ideal = 1.0 if endpoint.endswith("_success") else 0.0
        zero_floor_ties[endpoint] = (
            math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(right, ideal, rel_tol=0.0, abs_tol=1e-12)
        )
    strict_positive_leads = [endpoint for endpoint, lead in checks.items() if lead]
    return {
        "anaflow": {key: anflow[key] for key in REQUIRED_ENDPOINTS},
        "spectra": {key: spectra[key] for key in REQUIRED_ENDPOINTS},
        "strict_endpoint_leads": checks,
        "strict_positive_leads": strict_positive_leads,
        "strict_positive_lead_count": len(strict_positive_leads),
        "non_inferior_endpoint_checks": non_inferior_checks,
        "non_inferior_all_endpoints": all(non_inferior_checks.values()),
        "zero_floor_ties": zero_floor_ties,
        "zero_floor_tie_count": sum(zero_floor_ties.values()),
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
    comparable_non_inferior = sum(
        item["comparison"]["non_inferior_all_endpoints"] for item in comparable
    )
    strict_positive_all = sum(
        item["comparison"]["strict_all_endpoints"] for item in comparable
    )
    zero_floor_tie_strata = sum(
        item["comparison"]["zero_floor_tie_count"] > 0 for item in comparable
    )
    zero_floor_tie_endpoints = sum(
        item["comparison"]["zero_floor_tie_count"] for item in comparable
    )
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
        "diagnostic_summary": {
            "comparable_non_inferior_all_endpoints": comparable_non_inferior,
            "comparable_strict_positive_all_endpoints": strict_positive_all,
            "strata_with_zero_floor_ties": zero_floor_tie_strata,
            "zero_floor_tie_endpoints": zero_floor_tie_endpoints,
        },
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
    args.json_output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# XSOTA-1 gate audit",
        "",
        receipt["strict_definition"],
        "",
        f"Strict gate: **{'PASS' if receipt['strict_gate_pass'] else 'NOT MET'}**",
        f"Comparable strata: {receipt['comparable_strata']}; uncovered receipts: {receipt['uncovered_strata']}.",
        "",
        "| Receipt | Tier | TT lead | PVT lead | TT violation lead | PVT violation lead | Non-inferior | Zero-floor ties | All endpoints |",
        "|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for item in receipt["strata"]:
        comparison = item.get("comparison", {})
        leads = comparison.get("strict_endpoint_leads", {})
        fmt = lambda key: "yes" if leads.get(key, False) else "no"
        zero_floor_ties = comparison.get("zero_floor_ties", {})
        zero_floor_labels = ", ".join(key for key, value in zero_floor_ties.items() if value) or "none"
        lines.append(
            f"| `{item['receipt']}` | {item['tier']} | {fmt('tt_success')} | {fmt('pvt_success')} | {fmt('mean_tt_violation')} | {fmt('mean_pvt_violation')} | {'yes' if comparison.get('non_inferior_all_endpoints', False) else 'no'} | {zero_floor_labels} | {'yes' if comparison.get('strict_all_endpoints', False) else 'no'} |"
        )
    lines += [
        "",
        f"Diagnostics: {receipt['diagnostic_summary']['comparable_non_inferior_all_endpoints']} comparable strata are non-inferior on every endpoint; {receipt['diagnostic_summary']['comparable_strict_positive_all_endpoints']} have strict positive leads on every endpoint; {receipt['diagnostic_summary']['strata_with_zero_floor_ties']} contain zero-floor ties.",
        "Zero-floor ties mean equal ideal endpoints such as TT success 1.0 or mean violation 0.0. They are explanatory diagnostics only and do not relax XSOTA-1.",
        "Uncovered or capability-only receipts remain in this audit and count against the literal gate. A benchmark-scoped lead does not change the gate result.",
    ]
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: receipt[key] for key in ("receipts_observed", "comparable_strata", "uncovered_strata", "strict_gate_pass")}, sort_keys=True))


if __name__ == "__main__":
    main()
