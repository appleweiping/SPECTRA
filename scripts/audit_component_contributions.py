"""Audit component contributions on the frozen matched mechanism track.

The audit distinguishes a component's mechanism endpoint from binary success.
This prevents a mixed endpoint from being turned into a claim of universal
essentiality while still checking that each enabled mechanism has measurable
paired evidence.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    matrix = json.loads((ROOT / "results/component_mechanism_matrix.json").read_text())
    rows = {row["method"]: row for row in matrix["rows"]}
    pairs = matrix["paired"]
    definitions = {
        "diagnosis": ("spectra_nodiag", "lower matched violation score"),
        "intent-program abstraction": ("spectra_nointent", "lower matched violation score"),
        "PVT-aware refinement": ("spectra_norefine", "higher TT/PVT success"),
        "knowledge cards": ("spectra_noknow", "higher TT/PVT success"),
    }
    full = rows["spectra"]
    out_rows = []
    for component, (arm, criterion) in definitions.items():
        ablated = rows[arm]
        pair = pairs[arm]
        violation_delta = ablated["mean_violation_score"] - full["mean_violation_score"]
        tt_delta = full["tt_success"] - ablated["tt_success"]
        pvt_delta = full["pvt_success"] - ablated["pvt_success"]
        if component in {"diagnosis", "intent-program abstraction"}:
            supported = violation_delta > 0
            evidence = "violation_reduction"
        else:
            supported = tt_delta > 0 and pvt_delta > 0
            evidence = "endpoint_success"
        out_rows.append({
            "component": component,
            "ablation": arm,
            "criterion": criterion,
            "matched_runs": pair["n"],
            "full_mean_violation": full["mean_violation_score"],
            "ablated_mean_violation": ablated["mean_violation_score"],
            "ablated_minus_full_violation": violation_delta,
            "full_tt_success": full["tt_success"],
            "ablated_tt_success": ablated["tt_success"],
            "full_pvt_success": full["pvt_success"],
            "ablated_pvt_success": ablated["pvt_success"],
            "tt_delta_full_minus_ablated": tt_delta,
            "pvt_delta_full_minus_ablated": pvt_delta,
            "tt_wins": pair["tt_wins"],
            "tt_losses": pair["tt_losses"],
            "mechanism_evidence": evidence,
            "contribution_supported": supported,
        })
    payload = {
        "schema": "spectra-component-contribution-audit/v1",
        "track": matrix["exp"],
        "model": matrix["model"],
        "rows": out_rows,
        "interpretation": "Every enabled mechanism has a prespecified measurable contribution axis. Binary endpoint effects remain separate and mixed effects are retained.",
    }
    (ROOT / "results/component_contribution_audit.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# Component contribution audit",
        "",
        "The matched mechanism track has 18 tasks, three seeds and 54 runs per arm. A component is supported when its prespecified mechanism axis improves with the full arm. This is not an essentiality claim on every endpoint.",
        "",
        "| Component | Ablation | Evidence axis | Full | Ablated | Delta | Paired TT W/L | Supported |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in out_rows:
        if row["mechanism_evidence"] == "violation_reduction":
            full, ablated, delta = row["full_mean_violation"], row["ablated_mean_violation"], row["ablated_minus_full_violation"]
        else:
            full = row["full_tt_success"]
            ablated = row["ablated_tt_success"]
            delta = row["tt_delta_full_minus_ablated"]
        lines.append(f"| {row['component']} | {row['ablation']} | {row['mechanism_evidence']} | {full:.4f} | {ablated:.4f} | {delta:+.4f} | {row['tt_wins']}/{row['tt_losses']} | {'PASS' if row['contribution_supported'] else 'MIXED'} |")
    lines += ["", "The raw endpoint and event-level tables remain in `results/component_mechanism_matrix.json`; no arm or task is removed from this audit.", ""]
    (ROOT / "results/component_contribution_audit.md").write_text("\n".join(lines))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
