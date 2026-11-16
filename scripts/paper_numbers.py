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
        out["NCommon"] = str(full.get("common_tasks", "--")); out["NPrimaryTasks"] = str(full.get("primary_n_tasks", "--"))
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
        out["FaultHaikuSentence"] = (f"With the smaller Haiku~5.5 model the diagnosis changes top-1 accuracy from "
                                     f"{pct(d['raw']['top1'])} (raw) to {pct(d['spectra']['top1'])}.")
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
