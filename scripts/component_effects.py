"""Render an auditable component-effect table from the frozen GPT run summaries.

The endpoint and mechanism columns are deliberately separate.  A component can
reduce the search space or simulation cost without improving the binary success
endpoint, and the report keeps that mixed result instead of converting it into a
claim of necessity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from spectra.paths import ROOT


def _load(name: str):
    return json.loads((ROOT / "results" / name).read_text())


def _method(block, name):
    return block["methods"].get(name, {})


def main(output: str = "results/component_effects.json"):
    comparisons = _load("comparisons.json")
    prediction = _load("E1g_spectra_prediction_accuracy.json")
    fault = _load("E4g_tests.json")
    subset = comparisons["ablation_subset"]
    t3 = comparisons["ablation_t3"]
    ref = _method(subset, "spectra")
    rows = []

    def add(name, variant, block, mechanism, status):
        base = _method(block, "spectra")
        ablated = _method(block, variant)
        rows.append({
            "component": name,
            "variant": variant,
            "matched_tasks": block["n_tasks"],
            "seeds": ablated.get("seeds", []),
            "success_with": base.get("success"),
            "success_without": ablated.get("success"),
            "delta_success_pp": 100 * (base.get("success", 0) - ablated.get("success", 0)),
            "with_mean_sims": base.get("mean_sims"),
            "without_mean_sims": ablated.get("mean_sims"),
            "wins": ablated.get("vs_ref", {}).get("wins"),
            "losses": ablated.get("vs_ref", {}).get("losses"),
            "paired_p": ablated.get("vs_ref", {}).get("p_perm"),
            "mechanism": mechanism,
            "status": status,
        })

    add(
        "diagnosis", "spectra_nodiag", subset,
        "The failure-feedback path lowers mean simulations on the matched set and provides causal device/sensitivity evidence. E4 fault top-1 is raw 80.7% versus diagnosis 76.5%, so localization is a negative or mixed standalone result.",
        "mixed",
    )
    add(
        "intent-program abstraction", "spectra_nointent", subset,
        f"Median intent variables {prediction['intent_vars_median']} versus {prediction['raw_vars_median']} raw sizing variables ({prediction['raw_over_intent_median']:.2f}x compression). First-order predictions are accurate for some metrics and poor for second-order metrics.",
        "mixed",
    )
    add(
        "PVT-aware refinement", "spectra_norefine", t3,
        "Worst-condition CMA-ES refinement is the strongest endpoint contribution in the matched T3 block.",
        "directional",
    )
    add(
        "knowledge cards", "spectra_noknow", t3,
        "Cards encode topology, headroom, bias and stability constraints. The observed endpoint difference is small and the W/L test is non-significant, so the mechanism is retained without an essentiality claim.",
        "mixed",
    )
    result = {
        "schema": "spectra-component-effects/v1",
        "model": "gpt-6.1-sol",
        "rows": rows,
        "diagnosis_fault_test": fault["main"],
        "interpretation": "Endpoint success, mechanism evidence and paired significance are reported separately. Mixed or null effects are retained.",
    }
    path = ROOT / output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Component effects",
        "",
        "This table uses the frozen GPT-6.1-sol runs. Endpoint success and mechanism evidence are separate, and mixed or null effects remain visible.",
        "",
        "| Component | Matched tasks | Success with | Success without | Delta (pp) | Mean sims with/without | W/L | Paired p | Evidence status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        wl = f"{row['wins']}/{row['losses']}"
        lines.append(
            f"| {row['component']} | {row['matched_tasks']} | {row['success_with']:.3f} | {row['success_without']:.3f} | "
            f"{row['delta_success_pp']:+.1f} | {row['with_mean_sims']:.1f}/{row['without_mean_sims']:.1f} | {wl} | "
            f"{row['paired_p']:.5f} | {row['status']} |"
        )
    lines.extend(["", "Mechanism notes", ""])
    for row in rows:
        lines.append(f"- **{row['component']}**. {row['mechanism']}")
    lines.extend(["", f"Fault localization test. raw top-1={fault['main']['top1_raw']:.3f}, diagnosis top-1={fault['main']['top1_diag']:.3f}, exact McNemar p={fault['main']['p_mcnemar_exact']:.5f}.", ""])
    (ROOT / "results" / "component_effects.md").write_text("\n".join(lines))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/component_effects.json")
    args = parser.parse_args()
    main(args.output)
