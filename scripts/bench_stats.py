"""Benchmark statistics table (paper/tables/bench_stats.tex) from data/bench/*.jsonl."""
import json
from collections import defaultdict
from spectra.paths import ROOT

NAMES = {"opamp": "Op-amp/OTA", "amp": "Amplifier", "tia": "TIA", "cmirror": "Current mirror", "ldo": "LDO",
         "ref": "Reference", "comparator": "CT comparator", "latch": "Clocked comp.", "vco": "VCO", "filter": "Filter",
         "schmitt": "Schmitt", "opamp_app": "Op-amp appl."}

def main():
    load = lambda f: [json.loads(l) for l in open(ROOT / "data/bench" / f)] if (ROOT / "data/bench" / f).exists() else []
    cert, des, ctl = load("tasks.jsonl"), load("designer_tasks.jsonl"), load("control_tasks.jsonl")
    rows = defaultdict(lambda: defaultdict(int)); nspec = defaultdict(list)
    for t in cert:
        k = "R" if t.get("robust") else f"T{t['tier']}"
        rows[t["family"]][k] += 1; nspec[t["family"]].append(len(t["specs"]))
    for t in des:
        rows[t["family"]]["D"] += 1; nspec[t["family"]].append(len(t["specs"]))
    for t in ctl:
        rows[t["family"]]["C"] += 1
    lines = []
    tot = defaultdict(int)
    for fam in NAMES:
        r = rows[fam]
        for k in ("T1", "T2", "T3", "R", "D", "C"):
            tot[k] += r[k]
        ns = nspec[fam]
        lines.append(f"{NAMES[fam]} & {r['T1']} & {r['T2']} & {r['T3']} & {r['R']} & {r['D']} & {r['C']} & "
                     f"{sum(r.values())} & {sum(ns) / max(len(ns), 1):.1f} \\\\")
    allns = [n for v in nspec.values() for n in v]
    lines.append("\\midrule")
    lines.append(f"Total & {tot['T1']} & {tot['T2']} & {tot['T3']} & {tot['R']} & {tot['D']} & {tot['C']} & "
                 f"{sum(tot.values())} & {sum(allns) / max(len(allns), 1):.1f} \\\\")
    tex = ("\\begin{table}[t]\n\\centering\n\\caption{SPECTRA-Bench composition: certified tiers T1--T3, robust (R, 45-condition"
           " PVT), designer tier (D) and oracle-unmet controls (C); \\#spec = mean specifications per task.}\n"
           "\\label{tab:bench}\n\\scriptsize\n\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{@{}lcccccccc@{}}\n\\toprule\n"
           "Family & T1 & T2 & T3 & R & D & C & Total & \\#spec \\\\\n\\midrule\n" + "\n".join(lines) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (ROOT / "paper/tables/bench_stats.tex").write_text(tex)
    print(tex)

if __name__ == "__main__":
    main()
