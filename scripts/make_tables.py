"""LaTeX tables from results/*_summary.json (numbers only from files)."""
import json, sys
from pathlib import Path
from spectra.paths import ROOT

TAB = ROOT / "paper" / "tables"
LABEL = {"spectra": "\\textbf{SPECTRA}", "spectra_min": "SPECTRA-min (1 call + intent CMA-ES)",
         "direct": "AnalogCoder-style~\\cite{lai2025analogcoder}", "genbo": "Gen+TPE (AnalogCoder-Pro-style)~\\cite{lai2026analogcoderpro}",
         "genbo_cmaes": "Gen+CMA-ES", "oracle_cmaes": "\\textit{Oracle topology + CMA-ES}",
         "spectra_nodiag": "\\quad w/o diagnosis", "spectra_nointent": "\\quad w/o intent (raw $W/L$)",
         "spectra_norefine": "\\quad w/o refinement", "spectra_pvt_all": "\\quad PVT: all corners each step",
         "spectra_pvt_nominal": "\\quad PVT: nominal-only design"}


def f(x, pct=True):
    if x is None:
        return "--"
    return f"{100 * x:.0f}" if pct else (f"{x:.0f}" if x >= 10 else f"{x:.1f}")


def main_table(exp="E1", methods=None, out="main.tex", caption="", label="tab:main"):
    s = json.loads((ROOT / "results" / f"{exp}_summary.json").read_text())["summary"]
    methods = methods or [m for m in LABEL if m in s]
    rows = []
    for m in methods:
        d = s.get(m)
        if not d:
            continue
        rows.append(f"{LABEL.get(m, m)} & {f(d['success'])} [{f(d['ci95'][0])},{f(d['ci95'][1])}] & {f(d.get('tier1'))} & "
                    f"{f(d.get('tier2'))} & {f(d.get('tier3'))} & {f(d.get('robust'))} & {f(d.get('tierD'))} & "
                    f"{f(d.get('median_calls_success'), False)} & {f(d.get('median_sims_success'), False)} & {d['mean_cost_usd']:.2f} \\\\")
    tex = ("\\begin{table*}[t]\n\\centering\n\\caption{" + caption + "}\n\\label{" + label + "}\n\\small\n"
           "\\begin{tabular}{@{}lccccccccc@{}}\n\\toprule\n"
           "Method & Success (\\%) [95\\% CI] & T1 & T2 & T3 & Robust & Designer & Calls$^\\star$ & Sims$^\\star$ & \\$/run \\\\\n\\midrule\n"
           + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table*}\n")
    (TAB / out).write_text(tex)
    print(tex)


if __name__ == "__main__":
    main_table(*(sys.argv[1:2] or ["E1"]))


def ablation_table(exp_main="E1", exp_abl="E2", out="ablation.tex"):
    """Ablations on the E2 subset: SPECTRA/SPECTRA-min/baselines restricted to subset tasks + E2 variants."""
    from scripts.analyze import load, cluster_boot
    import numpy as np
    sub = {json.loads(l)["id"] for l in open(ROOT / "data/bench/subset_E2.jsonl")}
    runs = [r for r in load(exp_main) + load(exp_abl) if r["task"] in sub]
    order = ["spectra", "spectra_nodiag", "spectra_nointent", "spectra_norefine", "spectra_min", "genbo", "genbo_cmaes", "direct"]
    rows = []
    for m in order:
        rs = [r for r in runs if r["method"] == m]
        if not rs:
            continue
        s, lo, hi = cluster_boot(rs)
        nom = cluster_boot([r for r in rs if not r["robust"]])[0]
        rob = cluster_boot([r for r in rs if r["robust"]])[0]
        succ = [r for r in rs if r["success"]]
        calls = np.median([r["calls"] for r in succ]) if succ else None
        sims = np.median([r["sims"] for r in succ]) if succ else None
        cost = np.mean([r["cost"] for r in rs])
        rows.append(f"{LABEL.get(m, m)} & {f(s)} [{f(lo)},{f(hi)}] & {f(nom)} & {f(rob)} & {f(calls, False)} & {f(sims, False)} & {cost:.2f} \\\\")
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{Ablations on the stratified subset (" + str(len(sub)) +
           " tasks, 3 seeds). Calls/sims: medians over successful runs.}\n\\label{tab:ablation}\n\\scriptsize\n"
           "\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{@{}lcccccc@{}}\n\\toprule\n"
           "Variant & Succ.\\,(\\%) [CI] & Nom. & Rob. & Calls & Sims & \\$/run \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (TAB / out).write_text(tex)
    print(tex)


def fault_table(out="fault.tex"):
    s = json.loads((ROOT / "results/E4_summary.json").read_text())
    hp = ROOT / "results/E4_haiku_summary.json"
    h = json.loads(hp.read_text()) if hp.exists() else None
    classes = [c for c in s["rule"] if c not in ("top1", "top3")]
    nice = {"undersize_W": "Undersized $W$", "short_L": "Short $L$", "mirror_ratio": "Mirror ratio", "comp_cap": "Comp.\\ cap",
            "bias_starve": "Bias starved", "miswire_gate": "Miswired gate", "resistor_value": "Resistor value"}
    def cell(d, a, c=None):
        x = d[a] if c is None else d[a].get(c)
        return "--" if not x else f"{f(x['top1'])}/{f(x['top3'])}"
    arms = [(s, "rule"), (s, "raw"), (s, "spectra")] + ([(h, "raw"), (h, "spectra")] if h else [])
    rows = []
    for c in classes:
        rows.append(f"{nice.get(c, c)} & {s['rule'][c]['n']} & " + " & ".join(cell(d, a, c) for d, a in arms) + " \\\\")
    rows.append("\\midrule")
    rows.append("All & " + str(sum(s['rule'][c]['n'] for c in classes)) + " & " + " & ".join(cell(d, a) for d, a in arms) + " \\\\")
    head = "Fault class & $n$ & Rules & Opus+raw & Opus+diag." + (" & Haiku+raw & Haiku+diag." if h else "")
    cols = "lc" + "c" * len(arms)
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{Fault localisation accuracy (top-1/top-3, \\%) by injected fault class: "
           "rule-only diagnoser vs.\\ LLM given the netlist and spec table (raw) or the SPECTRA diagnosis.}\n"
           "\\label{tab:fault}\n\\scriptsize\n\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{@{}" + cols + "@{}}\n\\toprule\n"
           + head + " \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (TAB / out).write_text(tex)
    print(tex)
