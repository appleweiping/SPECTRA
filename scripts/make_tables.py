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
