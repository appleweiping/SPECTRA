"""Causal diagnosis: turn raw simulation results into device-level, actionable evidence.

Components
  1. spec table (target / simulated / predicted / violation) per condition
  2. operating-region table with Vds-Vdsat margins, gm/Id, current; flags (triode, edge, off, subthreshold)
  3. prediction-vs-simulation discrepancies (model mismatch of the design program)
  4. finite-difference sensitivities of failing metrics to intent variables (top knobs, direction, magnitude)
  5. rule-based root-cause hypotheses linking failing specs to devices / nodes
"""
from __future__ import annotations

import math

from ..sim.evaluate import region_report, spec_key, violation

UNITS = {"ugbw": "Hz", "f3db": "Hz", "gbw": "Hz", "power": "W", "power_avg": "W", "slew": "V/s", "settle": "s",
         "noise_1k": "V/rtHz", "in_noise_1m": "A/rtHz", "pm": "deg", "gain_db": "dB", "cmrr_db": "dB",
         "psrr_db": "dB", "swing": "V", "vos": "V", "rout": "ohm", "v_compliance": "V", "iout": "A",
         "iq": "A", "load_reg": "V/A", "line_reg": "V/V", "tc_ppm": "ppm/C", "vref": "V", "tpd": "s",
         "delay": "s", "energy": "J", "fc": "Hz", "f0": "Hz", "fmin": "Hz", "fmax": "Hz", "f_mid": "Hz",
         "hysteresis": "V", "zt_dbohm": "dBohm", "bw": "Hz", "f_unity": "Hz", "undershoot": "V", "overshoot": "V"}


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, (tuple, list)):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e4 or a < 1e-2:
        return f"{v:.3e}"
    return f"{v:.4g}"


def spec_table(task, ev, pred=None, cond=None):
    cond = cond or next(iter(ev.checks), None)
    if cond is None:
        return "(no simulation results)"
    m = ev.per_cond.get(cond, {})
    lines = [f"Spec check @ {cond}:", "| metric | target | simulated | predicted | status |", "|---|---|---|---|---|"]
    for s in task["specs"]:
        k = spec_key(s)
        v, ok, vio = ev.checks[cond].get(k, (None, False, 2.0))
        tgt = f"{s['op']} {fmt(s['value'])}" if s["op"] != "range" else f"in {fmt(s['value'])}"
        pv = (pred or {}).get(s["metric"])
        lines.append(f"| {s['metric']} [{UNITS.get(s['metric'], '')}] | {tgt} | {fmt(v)} | {fmt(pv)} | "
                     f"{'PASS' if ok else f'FAIL (viol {vio:.2f})'} |")
    extra = {k: v for k, v in m.items() if k not in {s['metric'] for s in task['specs']} and not k.startswith("_")}
    if extra:
        lines.append("Other measured: " + ", ".join(f"{k}={fmt(v)}" for k, v in list(extra.items())[:14]))
    return "\n".join(lines)


def region_table(ev, roles=None):
    rep = region_report(ev.ops)
    if not rep:
        return "(no device operating-point data)", []
    lines = ["Device operating points (TT):", "| dev | region | Id[uA] | gm/Id | Vgs | Vth | Vds | Vdsat | Vds-Vdsat | gm/gds |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    flags = []
    for d, r in rep.items():
        lines.append(f"| {d} | {r['region']} | {r['id_uA']} | {r['gm_id']} | {r['vgs']} | {r['vth']} | {r['vds']} | "
                     f"{r['vdsat']} | {r['vds_margin']} | {r['gm_gds']} |")
        if r["region"] != "saturation":
            flags.append((d, r))
    return "\n".join(lines), flags


def discrepancy(task, ev, pred, cond=None, tol=0.25):
    if not pred:
        return ""
    cond = cond or next(iter(ev.per_cond), None)
    m = ev.per_cond.get(cond, {})
    out = []
    for k, pv in pred.items():
        sv = m.get(k)
        if pv is None or sv is None:
            continue
        if k.endswith("_db") or k in ("pm",):
            if abs(pv - sv) > (6 if k != "pm" else 10):
                out.append(f"- {k}: predicted {fmt(pv)} vs simulated {fmt(sv)} (diff {sv - pv:+.1f})")
        elif pv == 0 or sv == 0:
            if pv != sv:
                out.append(f"- {k}: predicted {fmt(pv)} vs simulated {fmt(sv)}")
        elif abs(pv / sv - 1) > tol:
            out.append(f"- {k}: predicted {fmt(pv)} vs simulated {fmt(sv)} (ratio sim/pred {sv / pv:.2f})")
    if not out:
        return "Program predictions agree with simulation (within tolerance)."
    return "Model-vs-simulation discrepancies (your analytic model of the circuit is wrong here):\n" + "\n".join(out)


def sensitivity_text(sens, failing):
    """sens: {param: {metric: d_metric per +10% param (dB/deg/abs or relative %)}}"""
    if not sens:
        return ""
    lines = ["Sensitivities of failing specs to intent variables (effect of +10% change of the variable):"]
    for met in failing:
        items = []
        for p, d in sens.items():
            if p.startswith("_") or not isinstance(d, dict):
                continue
            if met in d and d[met] is not None:
                items.append((abs(d[met]), p, d[met]))
        items.sort(reverse=True)
        if items:
            unit = "dB" if met.endswith("_db") else ("deg" if met == "pm" else "%")
            lines.append(f"- {met}: " + ", ".join(f"{p} {v:+.3g}{unit}" for _, p, v in items[:4]))
    return "\n".join(lines) if len(lines) > 1 else ""


def root_causes(task, ev, flags, cond=None):
    fam = task["family"]
    cond = cond or next(iter(ev.per_cond), None)
    m = ev.per_cond.get(cond, {})
    fails = [s for s in task["specs"] if not ev.checks.get(cond, {}).get(spec_key(s), (0, True, 0))[1]]
    fm = {s["metric"] for s in fails}
    hyp = []
    for d, r in flags:
        if r["region"].startswith("triode"):
            hyp.append(f"{d} is in TRIODE (Vds={r['vds']} V < Vdsat={r['vdsat']} V): its branch current/node voltage is "
                       f"inconsistent with the intended bias -> gain/swing/CMRR collapse; fix the DC level of its drain node "
                       f"or reduce its Vdsat (higher gm/Id) / headroom of the devices stacked with it.")
        elif r["region"] == "edge-of-saturation":
            hyp.append(f"{d} has only {r['vds_margin']} V of Vds-Vdsat margin: corners/temperature will push it into "
                       f"triode; raise its Vds or lower its Vdsat.")
        elif r["region"] == "off":
            hyp.append(f"{d} carries no current (OFF): its branch is not biased (wrong mirror connection, gate voltage "
                       f"below threshold, or missing current path).")
        elif r["region"].startswith("subthreshold"):
            hyp.append(f"{d} operates in weak inversion (Vgs<Vth): slow, current-starved; acceptable only if intended.")
    if fam in ("opamp", "opamp_app", "filter"):
        vo = m.get("vout_dc")
        if vo is not None and (vo < 0.25 or vo > 1.55):
            hyp.append(f"Output DC level {vo:.3f} V is near a rail: the output stage current sources are unbalanced "
                       f"(e.g. 2nd-stage NMOS sink vs PMOS driver currents) or the loop is not closing -> high-gain node saturated.")
        if "pm" in fm and m.get("ugbw"):
            hyp.append("Phase margin low: the non-dominant pole (output or mirror node) is too close to UGBW. Options: "
                       "increase Cc (lowers UGBW), increase gm of the 2nd stage (I7 or gm/Id7), set Rz >= 1/gm7, reduce "
                       "parasitic capacitance at the mirror node (smaller/shorter PMOS load).")
        if "gain_db" in fm:
            hyp.append("DC gain low: increase output resistance at the high-impedance nodes (longer L of the devices with "
                       "lowest gm/gds at those nodes, cascoding) or raise gm/Id of the gain devices.")
        if "ugbw" in fm or "f3db" in fm or "bw" in fm:
            hyp.append("Bandwidth low: raise gm of the input device (more current / higher gm/Id) or reduce the "
                       "compensation/load capacitance; check non-dominant poles.")
        if "swing" in fm:
            hyp.append("Swing low: the output devices need smaller Vdsat (higher gm/Id, wider) and fewer stacked devices at the output.")
        if "slew" in fm:
            hyp.append("Slew low: increase tail current (Itail/Cc) and output-stage current (I/(CL+Cc)).")
        if "cmrr_db" in fm:
            hyp.append("CMRR low: tail current source output resistance too low (longer L, more Vds margin) or mirror mismatch.")
    if fam == "ldo":
        if m.get("ripple_settled") is not None and m["ripple_settled"] > 5e-3:
            hyp.append(f"LDO output still rings ({m['ripple_settled']:.3g} V p-p) after load steps: loop is (nearly) unstable; "
                       "move the dominant pole (Miller Cc at the pass gate or larger CL), reduce error-amp output resistance, "
                       "or add a zero (series R with Cc).")
        if "load_reg" in fm:
            hyp.append("Load regulation poor: loop gain too low -> increase error-amp gain (longer L) and pass-device gm.")
    if fam == "ref":
        if m.get("startup_ok") == 0:
            hyp.append("Start-up FAILS: the self-biased core stays in its zero-current state during the VDD ramp; add/strengthen "
                       "a start-up branch that injects current when vref is low and turns off afterwards.")
        if "tc_ppm" in fm:
            hyp.append("TC too high: rebalance PTAT and CTAT terms (R2/R1*ln(N)); check that the PTAT generator devices "
                       "stay in saturation over temperature.")
    if fam == "comparator" and m.get("polarity_ok") == 0:
        hyp.append("Output POLARITY is inverted: vout must be HIGH when vinp > vinn (swap the input pair connections or add an inversion).")
    if fam == "latch" and m.get("correct") == 0:
        hyp.append("Wrong/incomplete decision: check output polarity, reset of internal nodes, and that the latch fully "
                   "regenerates within half a clock period (stronger latch/tail devices).")
    return hyp


def analyze(task, ev, pred=None, sens=None, cond=None, max_items=8):
    """Return a structured, deterministic diagnosis for one evaluation.

    The previous API exposed only prose.  This record keeps the same evidence
    but makes attribution and downstream ablation metrics auditable.  The
    ``sens`` mapping remains backward compatible with ``sensitivity_text`` and
    may additionally contain a private ``_violation`` mapping produced by the
    agent's finite-difference probe.
    """
    cond = cond or next(iter(ev.checks), None)
    if ev.status != "ok":
        return {"schema": "spectra-diagnosis/v2", "status": ev.status, "condition": cond,
                "failing": [], "regions": {}, "flags": [], "attribution": [],
                "hypotheses": list(ev.errors[:max_items])}
    metrics = ev.per_cond.get(cond, {}) if cond else {}
    checks = ev.checks.get(cond, {}) if cond else {}
    specs = {s["metric"]: s for s in task.get("specs", [])}
    failing = []
    for s in task.get("specs", []):
        v, ok, vio = checks.get(spec_key(s), (metrics.get(s["metric"]), False, 2.0))
        if not ok:
            failing.append({"metric": s["metric"], "value": v, "target": s["value"],
                            "op": s["op"], "violation": float(vio)})
    regions = region_report(ev.ops)
    flags = [{"device": d, **r} for d, r in regions.items() if r["region"] != "saturation"]
    attribution = []
    for param, details in (sens or {}).items():
        if not isinstance(details, dict) or param.startswith("_"):
            continue
        vd = details.get("_violation", {})
        for fail in failing:
            metric = fail["metric"]
            raw = details.get(metric)
            if raw is None and metric not in vd:
                continue
            delta = vd.get(metric)
            if delta is None:
                # Legacy callers provide only a raw one-sided delta.  Keep the
                # direction explicit and mark the normalized value unavailable.
                delta = None
            attribution.append({"param": param, "metric": metric,
                                "delta": raw, "d_violation": delta,
                                "direction": ("improves" if delta is not None and delta < 0 else
                                               "worsens" if delta is not None and delta > 0 else "unknown")})
    attribution.sort(key=lambda x: (x["d_violation"] is None, x["d_violation"] if x["d_violation"] is not None else 0.0))
    flags_for_hyp = [(x["device"], x) for x in flags]
    hypotheses = root_causes(task, ev, flags_for_hyp, cond)
    dis = discrepancy(task, ev, pred, cond)
    return {"schema": "spectra-diagnosis/v2", "status": ev.status, "condition": cond,
            "score": float(ev.score), "failing": failing, "regions": regions, "flags": flags,
            "attribution": attribution[:max_items], "hypotheses": hypotheses[:max_items],
            "discrepancy": dis}


def failure_summary(task, ev, cond=None):
    """Expose only observed failed margins for the diagnosis ablation arm.

    Knowledge retrieval may still use the failed metric names, while operating
    regions, hypotheses and parameter attribution remain unavailable.  This
    keeps the no-diagnosis arm from receiving the component it is meant to
    remove.
    """
    cond = cond or next(iter(ev.checks), None)
    checks = ev.checks.get(cond, {}) if cond else {}
    metrics = ev.per_cond.get(cond, {}) if cond else {}
    failing = []
    for spec in task.get("specs", []):
        value, ok, vio = checks.get(spec_key(spec), (metrics.get(spec["metric"]), False, 2.0))
        if not ok:
            failing.append({"metric": spec["metric"], "value": value, "target": spec["value"],
                            "op": spec["op"], "violation": float(vio)})
    return {"schema": "spectra-diagnosis/disabled", "status": ev.status, "condition": cond,
            "failing": failing, "flags": [], "attribution": [], "hypotheses": []}


def render_analysis(analysis):
    """Render :func:`analyze` output into the compact feedback text expected by LLMs."""
    if not analysis:
        return "(no diagnosis)"
    if analysis.get("status") != "ok":
        lines = [f"Evaluation status: {analysis.get('status', 'unknown')}"]
        lines.extend(f"- {e}" for e in analysis.get("hypotheses", [])[:8])
        return "\n".join(lines)
    lines = ["Causal diagnosis (structured evidence):"]
    fails = analysis.get("failing", [])
    if fails:
        lines.append("Failing margins: " + "; ".join(
            f"{x['metric']} {x['op']} {fmt(x['target'])}, value={fmt(x['value'])}, violation={x['violation']:.3f}"
            for x in fails))
    else:
        lines.append("No failing specs in this condition.")
    attrs = analysis.get("attribution", [])
    if attrs:
        lines.append("Parameter attribution: " + "; ".join(
            f"{x['param']}→{x['metric']} ({x['direction']}, d_vio={fmt(x['d_violation'])})" for x in attrs[:8]))
    flags = analysis.get("flags", [])
    if flags:
        lines.append("Operating-region flags: " + "; ".join(
            f"{x['device']}={x['region']} (Vds-Vdsat={fmt(x['vds_margin'])})" for x in flags[:8]))
    hyps = analysis.get("hypotheses", [])
    if hyps:
        lines.append("Root-cause hypotheses:\n" + "\n".join(f"- {h}" for h in hyps[:8]))
    dis = analysis.get("discrepancy")
    if dis:
        lines.append(dis)
    return "\n".join(lines)


def report(task, ev, pred=None, sens=None, cond=None, max_hyp=8):
    if ev.status != "ok":
        return f"Evaluation status: {ev.status}\nErrors:\n" + "\n".join(f"- {e}" for e in ev.errors[:10]) + \
               ("\nWarnings:\n" + "\n".join(f"- {w}" for w in ev.warnings[:5]) if ev.warnings else "")
    parts = [spec_table(task, ev, pred, cond)]
    rt, flags = region_table(ev)
    parts.append(rt)
    dis = discrepancy(task, ev, pred, cond)
    if dis:
        parts.append(dis)
    cond_ = cond or next(iter(ev.checks), None)
    failing = [s["metric"] for s in task["specs"] if not ev.checks.get(cond_, {}).get(spec_key(s), (0, True, 0))[1]]
    st = sensitivity_text(sens, failing)
    if st:
        parts.append(st)
    hyp = root_causes(task, ev, flags, cond_)
    if hyp:
        parts.append("Root-cause hypotheses:\n" + "\n".join(f"- {h}" for h in hyp[:max_hyp]))
    if ev.warnings:
        parts.append("Warnings: " + "; ".join(ev.warnings[:4]))
    return "\n\n".join(parts)
