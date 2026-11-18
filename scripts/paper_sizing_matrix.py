"""Aggregate the strict seven-framework fixed-topology sizing track."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

from spectra.paths import ROOT
from spectra.baselines.paper_sizing import PAPER_META, RUNNERS

METHODS = tuple(RUNNERS)


def _wilson(values):
    n = len(values)
    if not n:
        return None
    z = 1.959963984540054
    p = sum(values) / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0, c - r), 4), round(min(1, c + r), 4)]


def _load(path):
    return {json.loads(line)["id"]: json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()}


def _record(exp, method, task_id):
    root = ROOT / "results" / "raw" / exp
    for directory in sorted(root.glob(f"{method}*")):
        if directory.name.split("@", 1)[0] != method:
            continue
        path = directory / task_id / "s0.json"
        if path.exists():
            return json.loads(path.read_text())
    return None


def main(subset="data/bench/paper_sizing_tasks.jsonl", exp="SIZ7g"):
    tasks = _load(ROOT / subset)
    rows, records = [], {}
    for method in METHODS:
        pairs = [(tid, task, _record(exp, method, tid)) for tid, task in tasks.items()]
        observed = [(tid, task, rec) for tid, task, rec in pairs if rec is not None]
        records[method] = {tid: rec for tid, _, rec in observed}
        verifies = [rec.get("verify", {}) for _, _, rec in observed]
        tt = [bool(v.get("tt_pass")) for v in verifies]
        sims = [rec.get("sims", 0) or 0 for _, _, rec in observed]
        calls = [rec.get("calls", 0) or 0 for _, _, rec in observed]
        rows.append({
            "method": method,
            **PAPER_META[method],
            "implementation": "paper-faithful-clean-room",
            "task_scope": "fixed_topology_sizing",
            "observed": len(observed), "missing": len(tasks) - len(observed), "task_count": len(tasks),
            "family_count": len({task["family"] for _, task, _ in observed}),
            "tt_success": sum(tt) / len(tt) if tt else None, "tt_ci95": _wilson(tt),
            "mean_sims": sum(sims) / len(sims) if sims else None, "median_sims": median(sims) if sims else None,
            "mean_calls": sum(calls) / len(calls) if calls else None, "median_calls": median(calls) if calls else None,
            "crashes": sum(rec.get("status") == "crash" for _, _, rec in observed),
            "families": sorted({task["family"] for _, task, _ in observed}),
        })
    base = records.get("analogcoder", {})
    for row in rows:
        if row["method"] == "analogcoder":
            row["wins_vs_analogcoder"] = None; row["losses_vs_analogcoder"] = None
            continue
        common = set(base) & set(records[row["method"]])
        row["wins_vs_analogcoder"] = sum(bool(records[row["method"]][t].get("verify", {}).get("tt_pass")) and not bool(base[t].get("verify", {}).get("tt_pass")) for t in common)
        row["losses_vs_analogcoder"] = sum(bool(base[t].get("verify", {}).get("tt_pass")) and not bool(records[row["method"]][t].get("verify", {}).get("tt_pass")) for t in common)
    result = {"schema": "spectra-paper-sizing/v1", "model": "gpt-6.1-sol", "subset": subset,
              "exp": exp, "n_tasks": len(tasks), "n_frameworks": len(METHODS), "frameworks": list(METHODS), "rows": rows}
    (ROOT / "results/paper_sizing_matrix.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Strict seven-framework fixed-topology sizing track", "",
             "All rows receive the same frozen topology, variable bounds, task text, SKY130/ngspice-42 and 300 simulation-unit budget. LLM adapters share a 12-call cap. Results are reimplementations or adapters and do not reuse paper-reported numbers.", "",
             "| Framework | Venue | Observed/36 | TT success (95% Wilson CI) | Mean sims | Mean calls | W/L vs AnalogCoder | Crashes |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        ci = row["tt_ci95"]
        rate = "--" if row["tt_success"] is None else f"{row['tt_success']:.3f} [{ci[0]:.3f},{ci[1]:.3f}]"
        sims = "--" if row["mean_sims"] is None else f"{row['mean_sims']:.1f}"
        calls = "--" if row["mean_calls"] is None else f"{row['mean_calls']:.1f}"
        wl = "--" if row["wins_vs_analogcoder"] is None else f"{row['wins_vs_analogcoder']}/{row['losses_vs_analogcoder']}"
        lines.append(f"| {row['paper']} | {row['venue']} | {row['observed']}/{row['task_count']} | {rate} | {sims} | {calls} | {wl} | {row['crashes']} |")
    (ROOT / "results/paper_sizing_matrix.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--subset", default="data/bench/paper_sizing_tasks.jsonl"); ap.add_argument("--exp", default="SIZ7g")
    args = ap.parse_args(); main(args.subset, args.exp)
