"""Aggregate the six-domain seven-framework evaluation matrix.

The matrix reuses the frozen GPT-6.1-sol E1g runs for the four existing arms and
reads the additional optimizer arms from EXT7g.  It never fills missing runs
with zeros.  Missing or crashed runs remain visible in the output counts.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from spectra.paths import ROOT


FAIR = ("direct", "genbo", "spectra_min", "genbo_cmaes")
ORACLE = ("oracle_random", "oracle_cmaes", "oracle_tpe")
METHODS = ("spectra",) + FAIR + ORACLE


def _load_tasks(path: Path) -> dict[str, dict]:
    return {json.loads(line)["id"]: json.loads(line) for line in path.read_text().splitlines() if line.strip()}


def _files(exp: str, method: str):
    root = ROOT / "results" / "raw" / exp
    for directory in sorted(root.glob(f"{method}*")):
        if directory.name.split("@", 1)[0] != method:
            continue
        yield from sorted(directory.glob("*/s0.json"))


def _record(exp: str, method: str, task_id: str):
    for path in _files(exp, method):
        if path.parent.name == task_id:
            return json.loads(path.read_text())
    return None


def _rate(values):
    return sum(bool(x) for x in values) / len(values) if values else None


def _wilson(values):
    """Return the two-sided 95% Wilson interval for boolean observations."""
    n = len(values)
    if not n:
        return None
    z = 1.959963984540054
    successes = sum(bool(x) for x in values)
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denominator
    radius = z * ((p * (1.0 - p) / n + z * z / (4.0 * n * n)) ** 0.5) / denominator
    return [round(max(0.0, centre - radius), 4), round(min(1.0, centre + radius), 4)]


def _mismatch_yield(record):
    for key in ("mismatch_yield", "yield", "mc_yield"):
        value = record.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            for nested in ("yield", "mean_yield", "fraction"):
                if isinstance(value.get(nested), (int, float)):
                    return float(value[nested])
    return None


def main(subset: str = "data/bench/topconf6.jsonl", output: str = "results/extended_baselines.json"):
    tasks = _load_tasks(ROOT / subset)
    rows = []
    records_by_method = {}
    for method in METHODS:
        records = []
        for task_id, task in tasks.items():
            record = _record("EXT7g", method, task_id)
            # The first 16 topconf6 tasks are already present in the frozen
            # E1g chain.  They use the same model, task text and budget, so
            # they are valid matched records for the extension.  The missing
            # 20 tasks are rerun into EXT7g before this aggregation.
            if record is None and method in {"spectra", "direct", "genbo", "spectra_min"}:
                record = _record("E1g", method, task_id)
            records.append((task_id, task, record))
        observed = [(task_id, task, record) for task_id, task, record in records if record is not None]
        records_by_method[method] = {task_id: record for task_id, _, record in observed}
        verified = [record.get("verify", {}) for _, _, record in observed]
        tt_values = [v.get("tt_pass", False) for v in verified]
        pvt_values = [
            v.get("pvt_pass")
            for (_, task, _), v in zip(observed, verified)
            if task.get("robust") and "pvt_pass" in v
        ]
        mismatch_values = [value for _, _, record in observed if (value := _mismatch_yield(record)) is not None]
        numeric_calls = [record.get("calls", 0) or 0 for _, _, record in observed]
        numeric_sims = [record.get("sims", 0) or 0 for _, _, record in observed]
        rows.append({
            "method": method,
            "family_count": len({task["family"] for _, task, _ in observed}),
            "task_count": len(tasks),
            "observed": len(observed),
            "missing": len(tasks) - len(observed),
            "tt_success": _rate(tt_values),
            "tt_ci95": _wilson(tt_values),
            "pvt_success": _rate(pvt_values),
            "pvt_ci95": _wilson(pvt_values),
            "mean_calls": sum(numeric_calls) / len(numeric_calls) if numeric_calls else None,
            "median_calls": median(numeric_calls) if numeric_calls else None,
            "mean_sims": sum(numeric_sims) / len(numeric_sims) if numeric_sims else None,
            "median_sims": median(numeric_sims) if numeric_sims else None,
            "mean_mismatch_yield": sum(mismatch_values) / len(mismatch_values) if mismatch_values else None,
            "mismatch_observed": len(mismatch_values),
            "crashes": sum(record.get("status") == "crash" for _, _, record in observed),
            "privileged_upper_bound": method in ORACLE,
            "families": sorted({task["family"] for _, task, _ in observed}),
        })
    spectra_records = records_by_method["spectra"]
    for row in rows:
        if row["method"] == "spectra":
            row["wins_vs_spectra"] = None
            row["losses_vs_spectra"] = None
            continue
        common = set(spectra_records) & set(records_by_method[row["method"]])
        method_wins = sum(
            bool(records_by_method[row["method"]][task_id].get("verify", {}).get("tt_pass"))
            and not bool(spectra_records[task_id].get("verify", {}).get("tt_pass"))
            for task_id in common
        )
        spectra_wins = sum(
            bool(spectra_records[task_id].get("verify", {}).get("tt_pass"))
            and not bool(records_by_method[row["method"]][task_id].get("verify", {}).get("tt_pass"))
            for task_id in common
        )
        row["wins_vs_spectra"] = method_wins
        row["losses_vs_spectra"] = spectra_wins
    result = {
        "schema": "spectra-extended-baselines/v1",
        "model": "gpt-6.1-sol",
        "subset": str(subset),
        "families": sorted({task["family"] for task in tasks.values()}),
        "n_tasks": len(tasks),
        "n_frameworks": len(METHODS),
        "frameworks": list(METHODS),
        "fair_frameworks": list(FAIR),
        "privileged_frameworks": list(ORACLE),
        "rows": rows,
    }
    destination = ROOT / output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    markdown = [
        "# Six-domain external-framework matrix",
        "",
        "All rows use the frozen GPT-6.1-sol task text, SKY130/ngspice-42 and the same budget. Oracle rows are privileged upper bounds and are not fair LLM comparisons.",
        "",
        "| Framework | Observed/36 | TT success (95% Wilson CI) | PVT success | Mean sims | Mean calls | Mismatch n | W/L vs SPECTRA | Crashes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        ci = row["tt_ci95"]
        ci_text = "--" if ci is None else f"{row['tt_success']:.3f} [{ci[0]:.3f},{ci[1]:.3f}]"
        pvt = "--" if row["pvt_success"] is None else f"{row['pvt_success']:.3f}"
        wl = "--" if row["wins_vs_spectra"] is None else f"{row['wins_vs_spectra']}/{row['losses_vs_spectra']}"
        label = row["method"] + ("*" if row["privileged_upper_bound"] else "")
        mean_sims = "--" if row["mean_sims"] is None else f"{row['mean_sims']:.1f}"
        mean_calls = "--" if row["mean_calls"] is None else f"{row['mean_calls']:.1f}"
        markdown.append(
            f"| {label} | {row['observed']}/{row['task_count']} | {ci_text} | {pvt} | "
            f"{mean_sims} | {mean_calls} | {row['mismatch_observed']} | {wl} | {row['crashes']} |"
        )
    markdown.extend(["", "*Privileged template-oracle upper bound.", ""])
    (ROOT / "results" / "extended_baselines.md").write_text("\n".join(markdown))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", default="data/bench/topconf6.jsonl")
    parser.add_argument("--output", default="results/extended_baselines.json")
    args = parser.parse_args()
    main(args.subset, args.output)
