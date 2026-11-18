"""Aggregate matched component-mechanism ablations without imputing missing runs."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from statistics import median
from spectra.paths import ROOT

METHODS = ("spectra", "spectra_nodiag", "spectra_nointent", "spectra_norefine", "spectra_noknow")

def load_tasks(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def record(exp, method, task_id, seed):
    root = ROOT / "results" / "raw" / exp
    for d in sorted(root.glob(f"{method}*")):
        if d.name.split("@", 1)[0] != method:
            continue
        p = d / task_id / f"s{seed}.json"
        if p.exists():
            return json.loads(p.read_text())
    return None

def mean(values):
    return sum(values) / len(values) if values else None

def ci(values):
    if not values:
        return None
    n, p = len(values), sum(values) / len(values)
    z, den = 1.959963984540054, 1 + 1.959963984540054**2 / n
    rad = z * (p*(1-p)/n + z*z/(4*n*n))**0.5 / den
    ctr = (p + z*z/(2*n)) / den
    return [round(max(0, ctr-rad), 4), round(min(1, ctr+rad), 4)]

def main(exp="E2g_mech", subset="data/bench/component_mech_tasks.jsonl", seeds=(0,1,2)):
    tasks = load_tasks(ROOT / subset)
    expected = len(tasks) * len(seeds)
    rows, all_records = [], {}
    for method in METHODS:
        obs = []
        for task in tasks:
            for seed in seeds:
                rec = record(exp, method, task["id"], seed)
                if rec is not None:
                    obs.append((task, seed, rec))
        all_records[method] = {(t["id"], s): r for t, s, r in obs}
        verifies = [r.get("verify", {}) for _, _, r in obs]
        tt = [bool(v.get("tt_pass")) for v in verifies]
        robust = [(t, r) for t, _, r in obs if t.get("robust")]
        pvt = [bool(r.get("verify", {}).get("pvt_pass")) for _, r in robust if "pvt_pass" in r.get("verify", {})]
        scores = [float(v["tt_score"]) for v in verifies if isinstance(v.get("tt_score"), (int,float))]
        sims = [float(r.get("sims", 0) or 0) for _, _, r in obs]
        calls = [float(r.get("calls", 0) or 0) for _, _, r in obs]
        walls = [float(r.get("wall_seconds", 0) or 0) for _, _, r in obs]
        stats = [r.get("program_stats", {}) for _, _, r in obs if r.get("program_stats")]
        events = [e for _, _, r in obs for e in r.get("events", [])]
        traces = [e for e in events if e.get("kind") == "refine_trace"]
        cards = [c for e in events if e.get("kind") == "diagnosis" for c in e.get("cards", [])]
        card_counts = Counter(cards)
        rows.append({
            "method": method, "observed": len(obs), "expected": expected, "missing": expected-len(obs),
            "tt_success": mean(tt), "tt_ci95": ci(tt), "pvt_observed": len(pvt), "pvt_success": mean(pvt), "pvt_ci95": ci(pvt),
            "mean_violation_score": mean(scores), "median_violation_score": median(scores) if scores else None,
            "mean_simulation_units": mean(sims), "mean_llm_calls": mean(calls), "mean_wall_seconds": mean(walls),
            "intent_fraction_mean": mean([float(s.get("intent_fraction")) for s in stats if isinstance(s.get("intent_fraction"),(int,float))]),
            "intent_compliant_rate": mean([bool(s.get("intent_compliant")) for s in stats]) if stats else None,
            "diagnosis_events": sum(e.get("kind") == "diagnosis" for e in events),
            "refine_trace_events": len(traces), "refine_active_param_mean": mean([len(e.get("active_params", [])) for e in traces]),
            "card_events": len(cards), "card_top": card_counts.most_common(5),
            "failure_taxonomy": dict(Counter(str(r.get("status", "unknown")) for _, _, r in obs)),
        })
    base = all_records["spectra"]
    paired = {}
    for method in METHODS[1:]:
        common = sorted(set(base) & set(all_records[method]))
        deltas = []
        for key in common:
            a, b = base[key].get("verify", {}), all_records[method][key].get("verify", {})
            if isinstance(a.get("tt_score"), (int,float)) and isinstance(b.get("tt_score"), (int,float)):
                deltas.append(float(a["tt_score"]) - float(b["tt_score"]))
        paired[method] = {"n": len(common), "mean_delta_score_with_minus_without": mean(deltas),
                          "tt_wins": sum(bool(base[k].get("verify", {}).get("tt_pass")) and not bool(all_records[method][k].get("verify", {}).get("tt_pass")) for k in common),
                          "tt_losses": sum(not bool(base[k].get("verify", {}).get("tt_pass")) and bool(all_records[method][k].get("verify", {}).get("tt_pass")) for k in common)}
    out = {"schema":"spectra-component-mechanism/v1", "exp":exp, "subset":subset, "model":"gpt-6.1-sol",
           "tasks":len(tasks), "seeds":list(seeds), "methods":list(METHODS), "rows":rows, "paired":paired,
           "interpretation":"Rows keep missing runs and mixed effects visible. Mechanism fields are observed event logs, not post-hoc labels."}
    (ROOT / "results/component_mechanism_matrix.json").write_text(json.dumps(out, indent=2) + "\n")
    lines=["# Component mechanism ablation", "", f"Experiment `{exp}` uses {len(tasks)} tasks across six domains, three seeds and a common GPT-6.1-sol budget.", "", "| Arm | Observed/expected | TT success | PVT success | Mean violation | Mean sims | Mean calls | Intent fraction | Refine traces | Card events |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        tt = "--" if r["tt_success"] is None else f"{r['tt_success']:.3f}"
        pvt = "--" if r["pvt_success"] is None else f"{r['pvt_success']:.3f}"
        fmt = lambda x: "--" if x is None else f"{x:.2f}"
        lines.append(f"| {r['method']} | {r['observed']}/{r['expected']} | {tt} | {pvt} | {fmt(r['mean_violation_score'])} | {fmt(r['mean_simulation_units'])} | {fmt(r['mean_llm_calls'])} | {fmt(r['intent_fraction_mean'])} | {r['refine_trace_events']} | {r['card_events']} |")
    lines += ["", "Paired comparisons", "", "| Ablation arm | Common runs | TT wins by full arm | TT losses by full arm | Mean score delta |", "|---|---:|---:|---:|---:|"]
    for m, p in paired.items():
        lines.append(f"| {m} | {p['n']} | {p['tt_wins']} | {p['tt_losses']} | {p['mean_delta_score_with_minus_without'] if p['mean_delta_score_with_minus_without'] is not None else '--'} |")
    (ROOT / "results/component_mechanism_matrix.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--exp",default="E2g_mech"); ap.add_argument("--subset",default="data/bench/component_mech_tasks.jsonl"); ap.add_argument("--seeds",default="0,1,2"); a=ap.parse_args(); main(a.exp,a.subset,tuple(int(x) for x in a.seeds.split(",")))
