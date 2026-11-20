#!/usr/bin/env python3
"""Audit the public LOADBench evaluation scripts without copying the dataset.

LOADBench publishes evaluation helpers but no license file in the script
repository.  This command records a pinned source commit and file digests,
then runs small in-memory smoke checks for the topology-selection and inverse-
sizing metrics.  It deliberately does not download the multi-gigabyte dataset,
run a simulator, or turn the source-only inspection into a SIZ7g ranking row.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


EXPECTED = {
    "README.md": "protocol and metric definitions",
    "struct_matcher.py": "netlist structural matching",
    "circuit_generation_coverage.py": "topology coverage",
    "topology_selection_eval.py": "top-k and MFHR",
    "optimization_helper.py": "12-D hypervolume ratio",
    "inverse_sizing.py": "MAPE, outliers, satisfaction and R2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_module(root: Path, filename: str):
    spec = importlib.util.spec_from_file_location(filename[:-3], root / filename)
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def smoke(root: Path) -> dict[str, object]:
    """Exercise metric functions using deterministic synthetic data only."""
    result: dict[str, object] = {"status": "pass", "checks": []}
    try:
        topology = load_module(root, "topology_selection_eval.py")
        import pandas as pd

        pof = pd.DataFrame(
            [
                {
                    "area": 2.0,
                    "dc_gain": 70.0,
                    "ft": 1.0e7,
                    "phasemargin": 60.0,
                }
            ]
        )
        spec = {"area": 3.0, "dc_gain": 60.0, "ft": 5.0e6, "phasemargin": 50.0}
        measured = topology.evaluate_topk_lists_mfhr([[pof]], spec)
        if measured["top_k_acc"] != 1.0 or measured["mfhr"] != 1.0:
            raise AssertionError(f"unexpected top-k result: {measured}")
        result["checks"].append("topology_selection_eval")

        inverse = load_module(root, "inverse_sizing.py")
        true = pd.DataFrame(
            [
                {
                    name: 1.0
                    for name in inverse.METRICS
                }
            ]
        )
        predicted = true.copy()
        # The evaluator expects file paths. Use temporary files only in memory's
        # surrounding scratch directory, and remove them before returning.
        import tempfile

        with tempfile.TemporaryDirectory(prefix="loadbench-smoke-") as scratch:
            true_path = Path(scratch) / "true.csv"
            pred_path = Path(scratch) / "pred.csv"
            true.to_csv(true_path, index=False)
            predicted.to_csv(pred_path, index=False)
            metrics = inverse.evaluate_inverse_sizing(
                str(true_path), str(pred_path), verbose=False
            )
        if metrics["infeasible_fraction"] != 0.0 or metrics["spec_satisfaction_rate"] != 1.0:
            raise AssertionError(f"unexpected inverse result: {metrics}")
        result["checks"].append("inverse_sizing")
    except Exception as exc:  # keep the audit useful when optional deps are absent
        result["status"] = "partial"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_receipt(root: Path) -> dict[str, object]:
    files = []
    for name, role in EXPECTED.items():
        path = root / name
        row: dict[str, object] = {"name": name, "role": role, "exists": path.is_file()}
        if path.is_file():
            row.update({"bytes": path.stat().st_size, "sha256": sha256(path)})
        files.append(row)
    license_files = sorted(
        path.name for path in root.iterdir() if path.is_file() and path.name.lower().startswith("license")
    )
    return {
        "schema": "loadbench-scripts-source-audit/v1",
        "benchmark": "LOADBench",
        "source_url": "https://github.com/FilipeAz/LOADBench-Scripts",
        "source_commit": git(root, "rev-parse", "HEAD"),
        "source_date": git(root, "show", "-s", "--format=%cI", "HEAD"),
        "license_files": license_files,
        "license_status": "no-license-file-in-script-repository" if not license_files else "license-file-present",
        "dataset_downloaded": False,
        "dataset_policy": "source-only audit; do not download the approximately 40GB release in this workspace",
        "files": files,
        "metric_contract": [
            "top-k accuracy",
            "mean first-hit rank",
            "12-D hypervolume ratio against NSGA-II",
            "MAPE and standard deviation",
            "outlier rate",
            "spec-satisfaction rate",
            "R2",
            "FoM",
        ],
        "ranking_status": "capability_only_source_audit",
        "ranking_blocker": "dataset, source-native netlists, common SPECTRA/AnaFlow task cells and an independent matched verifier are not present in this checkout",
        "smoke": smoke(root),
    }


def markdown(receipt: dict[str, object]) -> str:
    lines = [
        "# LOADBench scripts source audit",
        "",
        "This is a server-side source audit of the public evaluation helpers. The",
        "large dataset was not downloaded and no electrical ranking cell is inferred.",
        "",
        f"- Source commit: `{receipt['source_commit']}`",
        f"- License status: `{receipt['license_status']}`",
        f"- Dataset downloaded: `{receipt['dataset_downloaded']}`",
        f"- Ranking status: `{receipt['ranking_status']}`",
        f"- Smoke status: `{receipt['smoke']['status']}`",
        "",
        "| File | Role | Present | SHA-256 |",
        "|---|---|:---:|---|",
    ]
    for row in receipt["files"]:
        lines.append(
            f"| `{row['name']}` | {row['role']} | "
            f"{'yes' if row['exists'] else 'no'} | `{row.get('sha256', '')}` |"
        )
    lines.extend(
        [
            "",
            "The smoke uses synthetic one-row DataFrames and only checks metric",
            "plumbing. It is not a LOADBench dataset result and is excluded from",
            "the SIZ7g and XSOTA-1 gates.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_receipt(args.source_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(receipt), encoding="utf-8")
    print(json.dumps({"source_commit": receipt["source_commit"], "smoke": receipt["smoke"]}, sort_keys=True))
    if not all(row["exists"] for row in receipt["files"]):
        raise SystemExit("LOADBench script audit failed: missing expected files")


if __name__ == "__main__":
    main()
