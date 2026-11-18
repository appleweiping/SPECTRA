"""Aggregate the strict eight-framework fixed-topology sizing track."""
from __future__ import annotations

import argparse
import json
import math
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


def _mismatch_yield(record):
    """Read an optional post-hoc mismatch-yield field without inventing values."""
    for key in ("mismatch_yield", "yield", "mc_yield"):
        value = record.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            for nested in ("yield", "mean_yield", "fraction"):
                if isinstance(value.get(nested), (int, float)):
                    return float(value[nested])
    return None


def _mean(values):
    return sum(values) / len(values) if values else None


def _median(values):
    return median(values) if values else None


def _exact_sign_p(wins, losses):
    n = wins + losses
    if n == 0:
        return None
    tail = sum(math.comb(n, k) for k in range(0, min(wins, losses) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def _failure_taxonomy(record):
    """Return an observed failure label without inferring missing outcomes."""
    verify = record.get("verify", {})
    if verify.get("status") not in (None, "ok"):
        return str(verify.get("status"))
    status = str(record.get("status", ""))
    if status and status not in ("success", "ok"):
        return status
    if verify.get("tt_pass") is False:
        return "tt_fail"
    if verify.get("pvt_pass") is False:
        return "pvt_fail"
    return "pass"


def main(subset="data/bench/paper_sizing_tasks.jsonl", exp="SIZ7g"):
    tasks = _load(ROOT / subset)
    rows, records = [], {}
    for method in METHODS:
        pairs = [(tid, task, _record(exp, method, tid)) for tid, task in tasks.items()]
        observed = [(tid, task, rec) for tid, task, rec in pairs if rec is not None]
        records[method] = {tid: rec for tid, _, rec in observed}
        verifies = [rec.get("verify", {}) for _, _, rec in observed]
        tt = [bool(v.get("tt_pass")) for v in verifies]
        pvt = [bool(v.get("pvt_pass")) for (_, task, rec), v in zip(observed, verifies)
               if task.get("robust") and "pvt_pass" in v]
        mismatch = [value for _, _, rec in observed if (value := _mismatch_yield(rec)) is not None]
        sims = [rec.get("sims", 0) or 0 for _, _, rec in observed]
        calls = [rec.get("calls", 0) or 0 for _, _, rec in observed]
        wall = [float(rec.get("wall_seconds", 0) or 0) for _, _, rec in observed]
        tokens_in = [int(rec.get("tokens_in", 0) or 0) for _, _, rec in observed]
        tokens_out = [int(rec.get("tokens_out", 0) or 0) for _, _, rec in observed]
        costs = [float(rec.get("cost_usd", 0) or 0) for _, _, rec in observed]
        violation_scores = [float(rec.get("verify", {}).get("tt_score"))
                            for _, _, rec in observed
                            if isinstance(rec.get("verify", {}).get("tt_score"), (int, float))]
        charged_sims = [int(rec.get("sims", rec.get("verify", {}).get("n_sims", 0)) or 0)
                        for _, _, rec in observed]
        failure_taxonomy = {}
        for _, _, rec in observed:
            label = _failure_taxonomy(rec)
            failure_taxonomy[label] = failure_taxonomy.get(label, 0) + 1
        first_pass_sims = [int(rec["first_pass_sims"]) for _, _, rec in observed
                           if rec.get("first_pass_sims") is not None]
        first_pass_calls = [int(rec["first_pass_calls"]) for _, _, rec in observed
                            if rec.get("first_pass_calls") is not None]
        rows.append({
            "method": method,
            **PAPER_META[method],
            "implementation": ("native-SPECTRA-fixed-topology-adapter" if method == "spectra"
                               else "paper-aligned-clean-room-reimplementation"),
            "task_scope": "fixed_topology_sizing",
            "observed": len(observed), "missing": len(tasks) - len(observed), "task_count": len(tasks),
            "family_count": len({task["family"] for _, task, _ in observed}),
            "robust_tasks": sum(bool(task.get("robust")) for task in tasks.values()),
            "robust_observed": sum(bool(task.get("robust")) for _, task, _ in observed),
            "tt_success": sum(tt) / len(tt) if tt else None, "tt_ci95": _wilson(tt),
            "pvt_success": sum(pvt) / len(pvt) if pvt else None, "pvt_ci95": _wilson(pvt),
            "mismatch_yield": _mean(mismatch), "mismatch_observed": len(mismatch),
            "mean_sims": _mean(sims), "median_sims": median(sims) if sims else None,
            "mean_calls": _mean(calls), "median_calls": median(calls) if calls else None,
            "mean_wall_seconds": _mean(wall), "median_wall_seconds": median(wall) if wall else None,
            "mean_tokens_in": _mean(tokens_in), "mean_tokens_out": _mean(tokens_out),
            "mean_cost_usd": _mean(costs),
            "mean_first_pass_sims": _mean(first_pass_sims),
            "mean_first_pass_calls": _mean(first_pass_calls),
            "first_pass_observed": len(first_pass_sims),
            "mean_violation_score": _mean(violation_scores),
            "median_violation_score": _median(violation_scores),
            "violation_observed": len(violation_scores),
            "mean_simulation_units": _mean(charged_sims),
            "failure_taxonomy": failure_taxonomy,
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
    pairwise = {}
    for method in METHODS:
        if method == "spectra":
            continue
        common = sorted(set(records["spectra"]) & set(records[method]))
        wins = sum(bool(records["spectra"][t].get("verify", {}).get("tt_pass")) and
                   not bool(records[method][t].get("verify", {}).get("tt_pass")) for t in common)
        losses = sum(bool(records[method][t].get("verify", {}).get("tt_pass")) and
                     not bool(records["spectra"][t].get("verify", {}).get("tt_pass")) for t in common)
        pairwise[method] = {"common": len(common), "tt_wins": wins, "tt_losses": losses,
                            "tt_ties": len(common) - wins - losses,
                            "exact_sign_p_single_seed": _exact_sign_p(wins, losses)}

    domain_rows = []
    for method in METHODS:
        for family in sorted({task["family"] for task in tasks.values()}):
            observed = [(tid, task, records[method].get(tid)) for tid, task in tasks.items()
                        if task["family"] == family and records[method].get(tid) is not None]
            verifies = [rec.get("verify", {}) for _, _, rec in observed]
            robust_verifies = [v for (_, task, _), v in zip(observed, verifies) if task.get("robust") and "pvt_pass" in v]
            domain_rows.append({"method": method, "family": family, "observed": len(observed),
                                "tt_success": _mean([bool(v.get("tt_pass")) for v in verifies]),
                                "pvt_success": _mean([bool(v.get("pvt_pass")) for v in robust_verifies])})

    result = {"schema": "spectra-paper-sizing/v4", "model": "gpt-6.1-sol", "subset": subset,
              "exp": exp, "n_tasks": len(tasks), "n_frameworks": len(METHODS), "frameworks": list(METHODS),
              "budget": {"simulation_units": 300, "llm_calls": 12},
              "search_corners": 3, "verifier_corners": 45,
              "primary_endpoint": "tt_success",
              "inference_scope": "single_seed_paired_snapshot",
              "metrics": ["tt_success", "pvt_success", "mismatch_yield", "violation_score",
                          "simulation_units", "llm_calls", "wall_seconds", "tokens", "cost_usd",
                          "first_pass_sims", "first_pass_calls", "failure_taxonomy"],
              "rows": rows, "pairwise_vs_spectra": pairwise, "domain_rows": domain_rows}
    (ROOT / "results/paper_sizing_matrix.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Strict eight-framework fixed-topology sizing track", "",
             "All rows receive the same frozen topology, variable bounds, task text, SKY130/ngspice-42 and 300 simulation-unit budget. LLM adapters share a 12-call cap. Results are reimplementations or adapters and do not reuse paper-reported numbers.", "",
             "Search uses 3 corners during adaptation. An independent 45-corner verifier reports PVT pass. Missing fields remain missing and are never imputed.", "",
             "| Framework | Venue | Observed/36 | Robust n | TT success (95% Wilson CI) | PVT success (95% Wilson CI) | Mismatch n | Mean sims | Mean calls | Mean wall s | Mean cost | W/L vs AnalogCoder | Crashes |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        ci = row["tt_ci95"]
        rate = "--" if row["tt_success"] is None else f"{row['tt_success']:.3f} [{ci[0]:.3f},{ci[1]:.3f}]"
        pvt_ci = row["pvt_ci95"]
        pvt = "--" if row["pvt_success"] is None else f"{row['pvt_success']:.3f} [{pvt_ci[0]:.3f},{pvt_ci[1]:.3f}]"
        sims = "--" if row["mean_sims"] is None else f"{row['mean_sims']:.1f}"
        calls = "--" if row["mean_calls"] is None else f"{row['mean_calls']:.1f}"
        wall = "--" if row["mean_wall_seconds"] is None else f"{row['mean_wall_seconds']:.1f}"
        cost = "--" if row["mean_cost_usd"] is None else f"${row['mean_cost_usd']:.3f}"
        wl = "--" if row["wins_vs_analogcoder"] is None else f"{row['wins_vs_analogcoder']}/{row['losses_vs_analogcoder']}"
        robust_n = f"{row['robust_observed']}/{row['robust_tasks']}"
        lines.append(f"| {row['paper']} | {row['venue']} | {row['observed']}/{row['task_count']} | {robust_n} | {rate} | {pvt} | {row['mismatch_observed']} | {sims} | {calls} | {wall} | {cost} | {wl} | {row['crashes']} |")
    lines += ["", "## Per-domain TT success", "", "| Method | opamp | amp | cmirror | filter | ldo | vco |", "|---|---:|---:|---:|---:|---:|---:|"]
    by_method = {m: {r["family"]: r for r in domain_rows if r["method"] == m} for m in METHODS}
    for method in METHODS:
        values = [by_method[method][family]["tt_success"] for family in ("opamp", "amp", "cmirror", "filter", "ldo", "vco")]
        lines.append("| " + method + " | " + " | ".join("--" if v is None else f"{v:.3f}" for v in values) + " |")
    lines += ["", "## Paired TT snapshot against SPECTRA", "", "| Method | Common | SPECTRA wins | SPECTRA losses | Ties | Exact sign p |", "|---|---:|---:|---:|---:|---:|"]
    for method, p in pairwise.items():
        lines.append(f"| {method} | {p['common']} | {p['tt_wins']} | {p['tt_losses']} | {p['tt_ties']} | {p['exact_sign_p_single_seed']:.4g} |")
    (ROOT / "results/paper_sizing_matrix.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--subset", default="data/bench/paper_sizing_tasks.jsonl"); ap.add_argument("--exp", default="SIZ7g")
    args = ap.parse_args(); main(args.subset, args.exp)
