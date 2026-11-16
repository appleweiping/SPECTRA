"""C1 evidence from E1: (a) accuracy of the agent's own design-intent-program predictions vs re-simulation of the
final design; (b) size of the intent space vs the raw sizing space of the generated netlist."""
import json, glob, math, statistics as st, sys
from collections import defaultdict
from spectra.paths import ROOT
from spectra.agent.sandbox import run_program
from spectra.sim.netlist import parse

DBM = {"gain_db", "cmrr_db", "psrr_db", "zt_dbohm", "psrr_1k", "atten_db", "pm"}

def main(exp="E1", method="spectra"):
    tasks = {json.loads(l)["id"]: json.loads(l) for f in ["tasks.jsonl", "designer_tasks.jsonl"]
             for l in open(ROOT / "data/bench" / f)}
    err = defaultdict(list); ratios = []; n_int, n_raw = [], []
    for f in sorted(glob.glob(str(ROOT / f"results/raw/{exp}/{method}/*/s*.json"))):
        r = json.load(open(f)); t = tasks.get(f.split("/")[-2])
        if not t or not r.get("program") or not r.get("verify", {}).get("tt_metrics"):
            continue
        out = run_program(r["program"], [r.get("params") or {}], spec=t.get("tb", {}))
        if not out.get("ok") or not out["results"][0]["ok"]:
            continue
        pred = out["results"][0]["pred"]; sim = r["verify"]["tt_metrics"]
        for k, pv in pred.items():
            sv = sim.get(k)
            if pv is None or sv is None:
                continue
            if k in DBM:
                err[k].append(abs(pv - sv))
            elif pv > 0 and sv > 0:
                err[k].append(abs(math.log10(pv / sv)))
        try:
            ckt = parse(out["results"][0]["netlist"])
            raw = sum(2 if d.kind in ("nfet", "pfet") else 1 for d in ckt.devices if d.kind != "pnp")
            nfree = sum(1 for v in (out.get("PARAMS") or {}).values() if v[2] > v[1])
            if nfree:
                n_int.append(nfree); n_raw.append(raw); ratios.append(raw / nfree)
        except Exception:
            pass
    summ = {"n_programs": len(n_int), "intent_vars_median": st.median(n_int) if n_int else None,
            "raw_vars_median": st.median(n_raw) if n_raw else None, "raw_over_intent_median": st.median(ratios) if ratios else None,
            "metrics": {}}
    for k, v in sorted(err.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 5:
            continue
        if k in DBM:
            summ["metrics"][k] = {"n": len(v), "median_abs_err": st.median(v), "unit": "dB" if k != "pm" else "deg"}
        else:
            summ["metrics"][k] = {"n": len(v), "median_ratio_err_pct": 100 * (10 ** st.median(v) - 1),
                                  "within_25pct": sum(x <= math.log10(1.25) for x in v) / len(v)}
    (ROOT / "results" / f"{exp}_{method}_prediction_accuracy.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
