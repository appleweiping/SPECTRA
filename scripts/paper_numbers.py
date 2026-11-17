"""Generate paper/numbers.tex (LaTeX macros) from results/ and data/ files so every number in the paper is traceable."""
import json
from pathlib import Path
from spectra.paths import ROOT

def pct(x):
    return f"{100 * x:.1f}\\%" if x is not None else "--"

def main():
    out = {}
    bench = [json.loads(l) for l in open(ROOT / "data/bench/tasks.jsonl")] if (ROOT / "data/bench/tasks.jsonl").exists() else []
    des = [json.loads(l) for l in open(ROOT / "data/bench/designer_tasks.jsonl")] if (ROOT / "data/bench/designer_tasks.jsonl").exists() else []
    ctl = [json.loads(l) for l in open(ROOT / "data/bench/control_tasks.jsonl")] if (ROOT / "data/bench/control_tasks.jsonl").exists() else []
    out["NCertified"] = str(len(bench))
    out["NRobust"] = str(sum(t.get("robust", False) for t in bench))
    out["NDesigner"] = str(len(des))
    out["NControls"] = str(len(ctl))
    out["NTasksTotal"] = str(len(bench) + len(des))      # controls (v0) withdrawn after review round 1
    from spectra.bench.templates import T
    out["NTemplates"] = str(len(T))
    n = 0
    for f in (ROOT / "data/explore").glob("*.jsonl"):
        n += sum(1 for _ in open(f))
    out["NExploreEvals"] = f"{n:,}".replace(",", "{,}")
    e1 = ROOT / "results/E1_summary.json"
    if e1.exists():
        s = json.loads(e1.read_text())["summary"]
        for m, key in [("spectra", "Spectra"), ("direct", "Direct"), ("genbo", "Genbo"), ("genbo_cmaes", "GenboC"),
                       ("spectra_min", "SpectraMin")]:
            if m in s:
                d = s[m]
                out[key + "Succ"] = pct(d["success"])
                out[key + "Robust"] = pct(d.get("robust"))
                for tk, nm in (("tier1", "One"), ("tier2", "Two"), ("tier3", "Three"), ("tierD", "Des")):
                    out[key + "T" + nm] = pct(d.get(tk))
                out[key + "Cost"] = f"\\${d['mean_cost_usd']:.2f}"
                out[key + "Calls"] = f"{d['median_calls_success']:.0f}" if d.get("median_calls_success") is not None else "--"
                out[key + "Sims"] = f"{d['median_sims_success']:.0f}" if d.get("median_sims_success") is not None else "--"
                out[key + "Nruns"] = str(d["n_runs"])
        full = json.loads(e1.read_text())
        out["NDeclaredSpectra"] = str(full["summary"].get("spectra", {}).get("declared_infeasible", 0))
        out["NCommon"] = str(full.get("common_tasks", "--")); out["NPrimaryTasks"] = str(full.get("primary_n_tasks", "--"))
        out["NPrimaryFamilies"] = str(full.get("primary_families", "--")); out["NCommonFamilies"] = str(full.get("common_families", "--"))
        pt = ROOT / "data/bench/E1_primary.jsonl"
        out["NPrimaryAll"] = str(sum(1 for _ in open(pt))) if pt.exists() else "--"
        for m, key in [("spectra", "Spectra"), ("direct", "Direct"), ("genbo", "Genbo"), ("spectra_min", "SpectraMin")]:
            if m in full.get("primary", {}):
                pd = full["primary"][m]
                out[key + "Prim"] = pct(pd["success"])
                out[key + "PrimCI"] = f"[{100 * pd['ci95'][0]:.0f},{100 * pd['ci95'][1]:.0f}]"
        for k, v in full.get("exact", {}).items():
            nm = "".join(w.capitalize() for w in k.replace("spectra_vs_", "").split("_"))
            pr = v["primary"]
            out["Prim" + nm + "P"] = f"{pr.get('p_perm_holm', pr['p_perm']):.2g}"
            out["Prim" + nm + "WL"] = f"{pr['wins']}/{pr['losses']}"
        # abstract main claim: wording chosen by the Holm-corrected paired permutation p on the primary endpoint
        ex = full.get("exact", {}); P = full.get("primary", {})
        if all(m in P for m in ("spectra", "direct", "genbo")):
            names = {"direct": "an AnalogCoder-style agent", "genbo": "an AnalogCoder-Pro-style generate-then-optimise agent"}
            sig = [m for m in ("direct", "genbo") if ex.get(f"spectra_vs_{m}", {}).get("primary", {}).get("p_perm_holm", 1) < 0.05]
            ns = [m for m in ("direct", "genbo") if m not in sig]
            claim = (f"solves {pct(P['spectra']['success'])} of the near-frontier and PVT-robust tasks (our primary endpoint; "
                     f"{full['primary_n_tasks']} tasks) versus {pct(P['direct']['success'])} for {names['direct']} and "
                     f"{pct(P['genbo']['success'])} for {names['genbo']}.")
            if sig:
                claim += (" The gain over " + " and over ".join(names[m].replace("an ", "the ", 1) for m in sig)
                          + " is significant in a paired, Holm-corrected test")
                claim += ("; the gain over " + names[ns[0]].replace("an ", "the ", 1) + " is not (p = "
                          + f"{ex[f'spectra_vs_{ns[0]}']['primary']['p_perm_holm']:.2g})." if ns else ".")
            else:
                claim += " At this sample size neither difference is significant in a paired, Holm-corrected test."
            out["AbsMainClaim"] = claim
        t = full["tests"]
        for k, v in t.items():
            nm = "Test" + "".join(w.capitalize() for w in k.replace("spectra_vs_", "").split("_"))
            out[nm + "P"] = f"{v.get('p_holm', v['p']):.3g}"
            out[nm + "Diff"] = f"{100 * v['mean_diff']:+.1f}"
    e4 = ROOT / "results/E4_summary.json"
    if e4.exists():
        d = json.loads(e4.read_text())
        out["FaultN"] = str(d.get("n_cases", sum(v["n"] for k, v in d["rule"].items() if isinstance(v, dict))))
        out["FaultRuleTopOne"] = pct(d["rule"]["top1"]).replace(".0\\%", "\\%")
        out["FaultRawTopOne"] = pct(d["raw"]["top1"])
        out["FaultDiagTopOne"] = pct(d["spectra"]["top1"])
        out["FaultDiagTopThree"] = pct(d["spectra"]["top3"])
    e4h = ROOT / "results/E4_haiku_summary.json"
    if e4h.exists():
        d = json.loads(e4h.read_text())
        tp = ROOT / "results/E4_tests.json"
        tt = json.loads(tp.read_text())["haiku"] if tp.exists() else None
        out["FaultHaikuSentence"] = (f"With the smaller Haiku~5.5 model top-1 accuracy is {pct(d['raw']['top1'])} with the raw "
                                     f"evidence and {pct(d['spectra']['top1'])} with the diagnosis ({d['n_cases']} cases"
                                     + (f"; {tt['only_raw_correct']} cases are solved only with the raw evidence and "
                                        f"{tt['only_diag_correct']} only with the diagnosis, exact McNemar $p={tt['p_mcnemar_exact']:.2f}$"
                                        if tt else "") + ").")
    else:
        out["FaultHaikuSentence"] = ""
    pa = ROOT / "results/E1_spectra_prediction_accuracy.json"
    if pa.exists():
        d = json.loads(pa.read_text()); mm = d["metrics"]
        out["NPrograms"] = str(d["n_programs"])
        out["IntentVars"] = f"{d['intent_vars_median']:.0f}"; out["RawVars"] = f"{d['raw_vars_median']:.0f}"
        out["RawOverIntent"] = f"{d['raw_over_intent_median']:.1f}"
        g = lambda k, f: (f(mm[k]) if k in mm else "--")
        out["PredPower"] = g("power", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
        out["PredUGBW"] = g("ugbw", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
        out["PredUGBWwithin"] = g("ugbw", lambda v: f"{100 * v['within_25pct']:.0f}\\%")
        out["PredGain"] = g("gain_db", lambda v: f"{v['median_abs_err']:.1f}\\,dB")
        out["PredPM"] = g("pm", lambda v: f"{v['median_abs_err']:.1f}$^\\circ$")
        out["PredSwing"] = g("swing", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
        out["PredCMRR"] = g("cmrr_db", lambda v: f"{v['median_abs_err']:.1f}\\,dB")
        out["PredPSRR"] = g("psrr_db", lambda v: f"{v['median_abs_err']:.1f}\\,dB")
        out["PredSlew"] = g("slew", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
        out["PredSettle"] = g("settle", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
        out["PredNoise"] = g("noise_1k", lambda v: f"{v['median_ratio_err_pct']:.0f}\\%")
    tv = ROOT / "results/pilot/testbench_validation.json"
    if tv.exists():
        d = json.loads(tv.read_text())["integrator"]
        out["TBIntegSim"] = f"{d['f_unity_sim'] / 1e3:.1f}\\,kHz"; out["TBIntegIdeal"] = f"{d['f_unity_ideal'] / 1e3:.1f}\\,kHz"
    hard = [t for t in bench if t.get("robust") or str(t.get("tier")) == "3"]
    out["NHard"] = str(len(hard)); out["NFrontier"] = str(sum(1 for t in hard if t["ref"].get("frontier_refined")))
    out["NTOne"] = str(sum(1 for t in bench if str(t.get("tier")) == "1" and not t.get("robust")))
    out["NTTwo"] = str(sum(1 for t in bench if str(t.get("tier")) == "2" and not t.get("robust")))
    out["NTThree"] = str(sum(1 for t in bench if str(t.get("tier")) == "3" and not t.get("robust")))
    fa = ROOT / "results/E1_failures.json"
    if fa.exists():
        d = json.loads(fa.read_text())
        nm = {"cmrr_db": "CMRR", "psrr_db": "PSRR", "power": "power", "noise_1k": "noise", "gain_db": "gain", "ugbw": "UGBW",
              "pm": "phase margin", "slew": "slew rate", "settle": "settling", "swing": "swing", "(PVT only)": "PVT corners",
              "polarity_ok": "polarity", "in_noise_1m": "input noise current", "f3db": "bandwidth", "vout_dc": "output DC level", "zt_dbohm": "transimpedance"}
        for m, key in (("direct", "FailDirectTop"), ("genbo", "FailGenboTop")):
            if m in d:
                tops = d[m]["top_failing_metrics"][:3]
                out[key] = ", ".join(f"{nm.get(k, k.replace('_', ' '))} ({v})" for k, v in tops) + f" of {d[m]['n_fail']} failed runs"
    sub = ROOT / "data/bench/subset_E2.jsonl"
    out["NSubset"] = str(sum(1 for _ in open(sub))) if sub.exists() else "--"
    # ---- E2 ablations (subset), E3 PVT strategies, E5 backbones: neutral, number-only sentences
    import subprocess
    def summ(exp, methods):
        f = ROOT / "results" / f"{exp}_summary.json"
        return json.loads(f.read_text()) if f.exists() else None
    pf = ROOT / "results/pvt_failure_conditions.json"
    if pf.exists():
        d = json.loads(pf.read_text()); tot = d["n_fail_conditions"] or 1
        out["PVTFailDesigns"] = str(d["n_designs"])
        out["PVTFailLowVdd"] = f"{100 * d['by_vdd'].get('1.62V', 0) / tot:.0f}\\%"
        cn = {"tt": "TT", "ss": "SS", "ff": "FF", "sf": "SF", "fs": "FS"}
        tn = {"125C": "125\\,$^\\circ$C", "-40C": "$-40\\,^\\circ$C", "27C": "27\\,$^\\circ$C"}
        out["PVTFailSentence"] = (
            f"Across the {d['n_designs']} designs returned by the four main methods that pass at TT but fail the grid, "
            f"{100 * d['by_vdd'].get('1.62V', 0) / tot:.0f}\\% of the {d['n_fail_conditions']} failing conditions are at the "
            f"low supply (1.62\\,V) and {d['designs_failing_at_1.62V']} of the {d['n_designs']} designs fail at least one "
            f"low-supply condition; failing conditions by corner are "
            + ", ".join(f"{cn.get(k, k)} {v}" for k, v in d["by_corner"].items())
            + " and by temperature " + ", ".join(f"{tn.get(k, k)} {v}" for k, v in d["by_temp"].items()) + ".")
    mp = ROOT / "results/mc_yield.json"
    if mp.exists():
        d = json.loads(mp.read_text()); Y = d["yield"]
        labm = {"spectra": "SPECTRA", "spectra_min": "SPECTRA-min", "direct": "the AnalogCoder-style agent", "genbo": "Gen+TPE",
                "spectra_pvt_nominal": "TT-only design", "genbo_full": "Gen+TPE-full"}
        parts = [f"{labm.get(m, m)} {100 * sum(v.values()) / len(v):.0f}\\% ({len(v)} designs, "
                 f"{sum(1 for x in v.values() if x >= 0.9)} with yield $\\geq$90\\%)" for m, v in Y.items() if v]
        out["MCN"] = str(d["n_samples"])
        out["MCSentence"] = (f"Under {d['n_samples']}-sample mismatch Monte Carlo at TT, the mean yield of the PVT-verified "
                             "seed-0 designs is " + "; ".join(parts) + ".") if parts else ""
    else:
        out["MCSentence"] = ""
    cp = ROOT / "results/comparisons.json"
    cmp = json.loads(cp.read_text()) if cp.exists() else {}
    def wl(d):
        v = d.get("vs_ref")
        return f" ({v['wins']}/{v['losses']} per-task wins/losses for SPECTRA)" if v else ""
    def sr(d):
        return f"{pct(d['success'])}"
    A, B = cmp.get("ablation_subset"), cmp.get("ablation_t3")
    lab = {"spectra_nodiag": "without diagnosis", "spectra_nointent": "without intent (raw $W/L$ programs)",
           "spectra_min": "SPECTRA-min", "genbo": "Gen+TPE", "direct": "the AnalogCoder-style agent",
           "spectra_norefine": "without refinement", "spectra_noknow": "without knowledge cards",
           "direct_noknow": "the AnalogCoder-style agent without cards"}
    txt = []
    if A and len(A["methods"]) >= 3 and "spectra" in A["methods"]:
        ms = [m for m in ("spectra_nodiag", "spectra_nointent", "spectra_min") if m in A["methods"]]
        txt.append(f"On the {A['n_tasks']} matched tasks of the stratified subset SPECTRA reaches {sr(A['methods']['spectra'])}; "
                   + "; ".join(f"{lab[m]} {sr(A['methods'][m])}{wl(A['methods'][m])}" for m in ms) + ".")
        out["AblSpectra"] = sr(A["methods"]["spectra"])
        for m, key in (("spectra_nodiag", "AblNoDiag"), ("spectra_nointent", "AblNoIntent"), ("spectra_min", "AblMin")):
            if m in A["methods"]:
                out[key] = sr(A["methods"][m]); v = A["methods"][m]["vs_ref"]
                out[key + "WL"] = f"{v['wins']}/{v['losses']}"; out[key + "P"] = f"{v['p_perm']:.2g}"
    if B and len(B["methods"]) >= 3 and "spectra" in B["methods"]:
        ms = [m for m in ("spectra_norefine", "spectra_noknow", "direct", "direct_noknow") if m in B["methods"]]
        txt.append(f"On its {B['n_tasks']} T3 tasks SPECTRA reaches {sr(B['methods']['spectra'])}; "
                   + "; ".join(f"{lab[m]} {sr(B['methods'][m])}{wl(B['methods'][m])}" for m in ms) + ".")
        for m, key in (("spectra_norefine", "AblNoRefine"), ("spectra_noknow", "AblNoKnow"), ("direct", "AblDirectTThree"),
                       ("direct_noknow", "AblDirectNoKnow")):
            if m in B["methods"]:
                out[key] = sr(B["methods"][m])
        out["AblTThreeN"] = str(B["n_tasks"]); out["AblSpectraTThree"] = sr(B["methods"]["spectra"])
    out["AblationText"] = " ".join(txt)
    P = cmp.get("pvt")
    if P and len(P["methods"]) >= 3:
        lab3 = {"spectra": "SPECTRA", "spectra_pvt_nominal": "designing at TT only and verifying at the end",
                "genbo_full": "Gen+TPE-full", "spectra_min": "SPECTRA-min", "genbo": "Gen+TPE", "direct": "the AnalogCoder-style agent"}
        def sims(d):
            return f"{d['median_sims_success']:.0f}" if d.get("median_sims_success") is not None else "--"
        out["PVTText"] = (f"On the {P['n_tasks']} robust tasks of the subset (seed 0), "
                          + "; ".join(f"{lab3[m]} reaches {sr(d)}" + (f" (median {sims(d)} condition-evaluations when successful)"
                                                                       if d.get("median_sims_success") is not None else "")
                                      for m, d in P["methods"].items()) + ".")
        out["PVTN"] = str(P["n_tasks"])
        for m, key in (("spectra", "PVTSpectra"), ("spectra_pvt_nominal", "PVTNominal"), ("genbo_full", "PVTGenboFull")):
            if m in P["methods"]:
                out[key] = sr(P["methods"][m]); out[key + "Sims"] = sims(P["methods"][m])
    S = cmp.get("scaling")
    if S and "spectra_haiku" in S["methods"] and "direct_haiku" in S["methods"]:
        h = S.get("haiku_spectra_vs_direct", {})
        out["ScalingText"] = (f"On the subset's {S['n_tasks']} T3 and robust tasks (seed 0), SPECTRA reaches "
                              f"{sr(S['methods']['spectra'])} with Opus~5.5 and {sr(S['methods']['spectra_haiku'])} with Haiku~5.5; "
                              f"the AnalogCoder-style agent reaches {sr(S['methods']['direct'])} and "
                              f"{sr(S['methods']['direct_haiku'])}" + (f" (Haiku: {h['wins']}/{h['losses']} per-task wins/losses for SPECTRA)" if h else "") + ".")
        out["ScaleN"] = str(S["n_tasks"])
        for m, key in (("spectra", "ScaleSpectraOpus"), ("direct", "ScaleDirectOpus"), ("spectra_haiku", "ScaleSpectraHaiku"),
                       ("direct_haiku", "ScaleDirectHaiku")):
            out[key] = sr(S["methods"][m])
    for k in ("AblationText", "PVTText", "ScalingText"):
        out.setdefault(k, "")
    lines = ["% auto-generated by scripts/paper_numbers.py -- do not edit"]
    for k, v in out.items():
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    for k in ["SpectraSucc", "DirectSucc", "GenboSucc", "SpectraRobust"]:
        if k not in out:
            lines.append(f"\\newcommand{{\\{k}}}{{\\textbf{{[TBD]}}}}")
    (ROOT / "paper/numbers.tex").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
