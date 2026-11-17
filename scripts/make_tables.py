"""LaTeX tables from results/*_summary.json (numbers only from files)."""
import json, sys
import os
from pathlib import Path
from spectra.paths import ROOT

TAB = ROOT / "paper" / "tables"
LABEL = {"spectra": "SPECTRA", "spectra_min": "SPECTRA-min (1 call + intent CMA-ES)",
         "direct": "AnalogCoder-style~\\cite{lai2025analogcoder}", "genbo": "Gen+TPE (AnalogCoder-Pro-style)~\\cite{lai2026analogcoderpro}",
         "genbo_cmaes": "Gen+CMA-ES", "oracle_cmaes": "\\textit{Oracle topology + CMA-ES}",
         "spectra_nodiag": "\\quad w/o diagnosis", "spectra_nointent": "\\quad w/o intent (raw $W/L$)",
         "spectra_norefine": "\\quad w/o refinement", "spectra_pvt_all": "\\quad PVT: all corners each step",
         "spectra_pvt_nominal": "\\quad w/o PVT-aware refinement"}


def f(x, pct=True):
    if x is None:
        return "--"
    return f"{100 * x:.0f}" if pct else (f"{x:.0f}" if x >= 10 else f"{x:.1f}")


SHORT = {"spectra": "SPECTRA", "spectra_min": "SPECTRA-min", "direct": "AnalogCoder-style", "genbo": "Gen+TPE",
         "spectra_nodiag": "w/o diagnosis", "spectra_nointent": "w/o intent", "spectra_norefine": "w/o refinement",
         "spectra_noknow": "w/o cards", "direct_noknow": "AnalogCoder-style w/o cards", "genbo_full": "Gen+TPE-full",
         "spectra_pvt_nominal": "w/o PVT refinement"}


def base_method(name):
    return str(name).split("@", 1)[0]


def env_bool(name):
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


def seeds_text(d):
    """{method: [lo, hi]} -> 'SPECTRA 1--2, ...' (seeds per task, computed from the runs)."""
    def rg(v):
        return f"{v[0]}" if v[0] == v[1] else f"{v[0]}--{v[1]}"
    return ", ".join(f"{SHORT.get(m, m)} {rg(v)}" for m, v in d.items())


def main_table(exp=None, out="main.tex"):
    exp = exp or os.environ.get("SPECTRA_MAIN_EXP", "E1g")
    summ = json.loads((ROOT / "results" / f"{exp}_summary.json").read_text())
    # `analyze --strip-model-suffix` emits base method names.  Normalize here
    # too so this table remains valid when a summary was generated without the
    # optional flag from a method@gpt-6.1-sol raw directory.
    s = {base_method(m): d for m, d in summ["summary"].items()}
    methods = [m for m in ("spectra", "spectra_min", "direct", "genbo") if m in s]
    from scripts.analyze import load, common_tasks
    runs = [dict(r, method=base_method(r["method"])) for r in load(exp)]
    ct = common_tasks([r for r in runs if not r.get("infeasible")], methods)
    runs = [r for r in runs if not r.get("infeasible") and r["task"] in ct]
    from scripts.comparisons import seeds_range
    seeds = {m: seeds_range([r for r in runs if r["method"] == m]) for m in methods}
    rows = []
    best = max((s[m].get("success", float("-inf")) for m in methods), default=float("-inf"))
    unique_best = sum(abs(s[m].get("success", float("-inf")) - best) < 1e-12 for m in methods) == 1
    for m in methods:
        d = s[m]
        name = LABEL.get(m, m)
        if unique_best and abs(d.get("success", float("-inf")) - best) < 1e-12:
            name = f"\\textbf{{{name}}}"
        rows.append(f"{name} & {f(d['success'])} [{f(d['ci95'][0])},{f(d['ci95'][1])}] & {f(d.get('tier1'))} & "
                    f"{f(d.get('tier2'))} & {f(d.get('tier3'))} & {f(d.get('robust'))} & {f(d.get('tierD'))} & "
                    f"{f(d.get('median_calls_success'), False)} & {f(d.get('median_sims_success'), False)} & "
                    f"{d['mean_tokens'] / 1e3:.0f} & {d['mean_cost_usd']:.2f} \\\\")
    cap = (f"Main results on the {summ['common_tasks']} tasks completed by every method (success = re-simulation outside "
           "the agent at TT, or on all 45 PVT conditions for robust tasks; per-task means over seeds, seeds per task: "
           + seeds_text(seeds) + "). Calls/Sims: medians over successful runs; kTok: mean LLM tokens "
           "(thousands); Cost$^\\dagger$: retained cost field (the configured gateway has no published tariff).")
    tex = ("\\begin{table*}[t]\n\\centering\n\\caption{" + cap + "}\n\\label{tab:main}\n\\small\n"
           "\\begin{tabular}{@{}lcccccccccc@{}}\n\\toprule\n"
           "Method & Success (\\%) [95\\% CI] & T1 & T2 & T3 & Robust & Designer & Calls$^\\star$ & Sims$^\\star$ & kTok & Cost$^\\dagger$ \\\\\n\\midrule\n"
           + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table*}\n")
    (TAB / out).write_text(tex)


def _cmp():
    p = ROOT / "results" / "comparisons.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _wl(d):
    v = d.get("vs_ref")
    return "--" if not v else f"{v['wins']}/{v['losses']}"


def _row(name, d, extra=""):
    return (f"{name} & {f(d['success'])} [{f(d['ci95'][0])},{f(d['ci95'][1])}] & {_wl(d)} & "
            f"{f(d['median_calls_success'], False)} & {f(d['median_sims_success'], False)} & {d['mean_cost_usd']:.2f}{extra} \\\\")


def ablation_table(out="ablation.tex"):
    c = _cmp()
    A, B = c.get("ablation_subset"), c.get("ablation_t3")
    if not A or len(A["methods"]) < 3:
        return
    lab = {"spectra": "SPECTRA", "spectra_nodiag": "\\quad w/o diagnosis", "spectra_nointent": "\\quad w/o intent (raw $W/L$)",
           "spectra_min": "\\quad SPECTRA-min", "genbo": "Gen+TPE", "direct": "AnalogCoder-style",
           "spectra_norefine": "\\quad w/o refinement", "spectra_noknow": "\\quad w/o knowledge cards",
           "direct_noknow": "AnalogCoder-style w/o cards"}
    rows = [f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{(a) stratified subset, {A['n_tasks']} tasks}}}} \\\\"]
    best_a = max((d.get("success", float("-inf")) for d in A["methods"].values()), default=float("-inf"))
    unique_a = sum(abs(d.get("success", float("-inf")) - best_a) < 1e-12 for d in A["methods"].values()) == 1
    rows += [_row((f"\\textbf{{{lab[m]}}}" if unique_a and abs(d.get("success", float("-inf")) - best_a) < 1e-12 else lab[m]), d)
             for m, d in A["methods"].items()]
    seeds = {m: d["seeds"] for m, d in A["methods"].items()}
    if B and len(B["methods"]) >= 3:
        rows.append("\\midrule")
        rows.append(f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{(b) T3 tasks of the subset, {B['n_tasks']} tasks}}}} \\\\")
        best_b = max((d.get("success", float("-inf")) for d in B["methods"].values()), default=float("-inf"))
        unique_b = sum(abs(d.get("success", float("-inf")) - best_b) < 1e-12 for d in B["methods"].values()) == 1
        rows += [_row((f"\\textbf{{{lab[m]}}}" if unique_b and abs(d.get("success", float("-inf")) - best_b) < 1e-12 else lab[m]), d)
                 for m, d in B["methods"].items()]
        seeds.update({m: d["seeds"] for m, d in B["methods"].items() if m not in seeds})
    cap = ("Ablations on matched tasks. W/L: tasks on which SPECTRA has a higher/lower success rate than the variant. "
           "Calls/sims: medians over successful runs. Seeds per task: " + seeds_text(seeds) + ".")
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{" + cap + "}\n\\label{tab:ablation}\n\\scriptsize\n"
           "\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{@{}lccccc@{}}\n\\toprule\n"
           "Variant & Succ.\\,(\\%) [CI] & W/L & Calls & Sims & Cost$^\\dagger$ \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (TAB / out).write_text(tex)


def pvt_table(out="pvt.tex"):
    c = _cmp().get("pvt")
    if not c or len(c["methods"]) < 3:
        return
    lab = {"spectra": "SPECTRA (adaptive worst conditions)", "spectra_pvt_nominal": "\\quad w/o PVT-aware refinement",
           "spectra_min": "SPECTRA-min", "direct": "AnalogCoder-style", "genbo": "Gen+TPE (3 fixed corners)",
           "genbo_full": "Gen+TPE-full (12 regen., adaptive)"}
    yp = ROOT / "results" / "mc_yield.json"
    my = json.loads(yp.read_text())["yield"] if yp.exists() else {}
    rows = []
    best = max((d.get("success", float("-inf")) for d in c["methods"].values()), default=float("-inf"))
    unique_best = sum(abs(d.get("success", float("-inf")) - best) < 1e-12 for d in c["methods"].values()) == 1
    for m, d in c["methods"].items():
        name = lab[m]
        if unique_best and abs(d.get("success", float("-inf")) - best) < 1e-12:
            name = f"\\textbf{{{name}}}"
        ys = [v for k, v in my.get(m, {}).items() if k.split("/")[0] in set(c["tasks"]) and k.endswith("s0")]
        y = f" & {100 * sum(ys) / len(ys):.0f}" if ys else (" & --" if my else "")
        rows.append(f"{name} & {f(d['success'])} [{f(d['ci95'][0])},{f(d['ci95'][1])}] & {_wl(d)} & "
                    f"{f(d['median_sims_success'], False)} & {f(d['mean_sims'], False)}{y} \\\\")
    ycol = " & Yield" if my else ""
    cap = (f"PVT-robust tasks of the subset ({c['n_tasks']} tasks, seed 0; success on all 45 conditions). Sims: "
           "condition-evaluations, median over successful runs and mean over all runs"
           + ("; yield: mean mismatch Monte-Carlo yield (\\%) at TT of the successful designs" if my else "") + ".")
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{" + cap + "}\n\\label{tab:pvt}\n\\scriptsize\n"
           "\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{@{}lcccc" + ("c" if my else "") + "@{}}\n\\toprule\n"
           "Method & Success (\\%) [CI] & W/L & Sims$^\\star$ & Sims" + ycol + " \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (TAB / out).write_text(tex)


def scaling_table(out="scaling.tex"):
    c = _cmp().get("scaling")
    path = TAB / out
    if not c or not any(m.endswith("_haiku") for m in c["methods"]):
        # E5g reuses GPT-6.1-sol as a same-backbone replication arm.  It is
        # not a cross-backbone study; remove historical tables instead of
        # carrying stale model labels into the GPT paper.
        if path.exists():
            path.unlink()
        return
    rows = []
    for m, d in c["methods"].items():
        llm = "Haiku 5.5" if m.endswith("_haiku") else "Opus 5.5"
        meth = "SPECTRA" if m.startswith("spectra") else "AnalogCoder-style"
        rows.append(f"{llm} & {meth} & {f(d['success'])} [{f(d['ci95'][0])},{f(d['ci95'][1])}] & "
                    f"{f(d['median_calls_success'], False)} & {d['mean_cost_usd']:.2f} \\\\")
    cap = f"Backbone study on the subset's T3 and robust tasks ({c['n_tasks']} tasks, seed 0)."
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{" + cap + "}\n\\label{tab:scaling}\n\\scriptsize\n"
           "\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{@{}llccc@{}}\n\\toprule\n"
           "LLM & Method & Success (\\%) [CI] & Calls$^\\star$ & Cost$^\\dagger$ \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    path.write_text(tex)


def fault_table(out="fault.tex"):
    main_exp = os.environ.get("SPECTRA_E4_EXP", "E4g")
    alt_exp = os.environ.get("SPECTRA_E4_ALT_EXP", "")
    s = json.loads((ROOT / f"results/{main_exp}_summary.json").read_text())
    hp = ROOT / f"results/{alt_exp}_summary.json"
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
    default_main_label = "GPT-6.1-sol"
    main_label = os.environ.get("SPECTRA_E4_MAIN_LABEL", default_main_label)
    alt_label = os.environ.get("SPECTRA_E4_ALT_LABEL", "alternate")
    head = f"Fault class & $n$ & Rules & {main_label}+raw & {main_label}+diag." + (f" & {alt_label}+raw & {alt_label}+diag." if h else "")
    cols = "lc" + "c" * len(arms)
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{Fault localisation accuracy (top-1/top-3, \\%) by injected fault class: "
           "rule-only diagnoser vs.\\ LLM given the netlist and spec table (raw) or the SPECTRA diagnosis.}\n"
           "\\label{tab:fault}\n\\scriptsize\n\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{@{}" + cols + "@{}}\n\\toprule\n"
           + head + " \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (TAB / out).write_text(tex)
    print(tex)




if __name__ == "__main__":
    main_table(os.environ.get("SPECTRA_MAIN_EXP", "E1g"))
    fault_table()
    ablation_table()
    pvt_table()
    scaling_table()
    print("tables:", sorted(p.name for p in TAB.glob("*.tex")))
