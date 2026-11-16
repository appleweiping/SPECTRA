"""Unified evaluation: parse -> ERC -> compile -> simulate (per PVT condition) -> measure -> spec check."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from . import ngspice as ng
from . import tb_opamp
from .families import REGISTRY
from .netlist import NetlistError, compile_sky130, erc, parse

FAMILIES = dict(REGISTRY)


class _OpampFam:
    PORTS = tb_opamp.PORTS
    build = staticmethod(tb_opamp.build)
    measure = staticmethod(tb_opamp.measure)


FAMILIES["opamp"] = _OpampFam

NOMINAL = {"corner": "tt", "temp": 27, "vdd": 1.8}
PVT = ([{"corner": c, "temp": t, "vdd": 1.8} for c in ["tt", "ff", "ss", "sf", "fs"] for t in (-40, 27, 125)]
       + [{"corner": "tt", "temp": 27, "vdd": v} for v in (1.62, 1.98)])
# metrics where log-ratio violations make more sense
LOG_METRICS = {"ugbw", "f3db", "gbw", "rout", "fmin", "fmax", "f_mid", "f_lo", "f_hi", "fc", "f0", "slew",
               "tuning_ratio", "kvco", "bw", "f_unity", "power", "power_avg", "energy", "tpd", "delay",
               "settle", "iq", "noise_1k", "in_noise_1m", "tc_ppm", "load_reg", "line_reg", "ripple_settled",
               "undershoot", "overshoot"}


def cond_name(c):
    return f"{c['corner']}_{c['temp']}C_{c['vdd']}V"


@dataclass
class EvalResult:
    status: str                      # ok | parse_error | erc_error | sim_error
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    per_cond: dict = field(default_factory=dict)    # cond_name -> metrics
    checks: dict = field(default_factory=dict)      # cond_name -> {spec_key: (value, pass, violation)}
    score: float = float("inf")      # sum of normalized violations, worst over conditions (0 = all pass)
    passed: bool = False
    ops: dict = field(default_factory=dict)          # nominal device op points
    n_sims: int = 0
    seconds: float = 0.0
    ckt: object = None

    def summary(self):
        return {"status": self.status, "passed": self.passed, "score": self.score, "n_sims": self.n_sims,
                "errors": self.errors[:10], "warnings": self.warnings[:10],
                "per_cond": {k: {m: v for m, v in d.items() if not m.startswith("_")} for k, d in self.per_cond.items()}}


def spec_key(s):
    return f"{s['metric']}{s['op']}{s['value']}"


def violation(spec, val):
    """Normalized violation >= 0 (0 means satisfied)."""
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return 2.0
    op, tgt, met = spec["op"], spec["value"], spec["metric"]
    if op == "range":
        lo, hi = tgt
        if lo <= val <= hi:
            return 0.0
        span = max(hi - lo, 1e-12)
        return min(2.0, (lo - val) / span if val < lo else (val - hi) / span)
    use_log = met in LOG_METRICS and tgt > 0
    if use_log:
        v = max(val, 1e-30)
        r = math.log10(tgt / v) if op == ">=" else math.log10(v / tgt)
        return min(2.0, max(0.0, r))
    scale = abs(tgt) if abs(tgt) > 1e-12 else 1.0
    r = (tgt - val) / scale if op == ">=" else (val - tgt) / scale
    return min(2.0, max(0.0, r))


def check(specs, metrics):
    out, total = {}, 0.0
    for s in specs:
        v = metrics.get(s["metric"])
        vio = violation(s, v)
        out[spec_key(s)] = (v, vio == 0.0, vio)
        total += vio
    return out, total


def evaluate(task: dict, netlist_text: str, conds=None, keep_ops=True, timeout=120.0) -> EvalResult:
    t0 = time.time()
    fam = FAMILIES[task["family"]]
    ports = task.get("ports", fam.PORTS)
    try:
        ckt = parse(netlist_text, ports)
    except NetlistError as e:
        return EvalResult("parse_error", errors=[str(e)], seconds=time.time() - t0)
    errs, warns = erc(ckt, ground="vss" if "vss" in ports else "0",
                      supplies=tuple(p for p in ports if p in ("vdd", "vin")))
    if errs:
        return EvalResult("erc_error", errors=errs, warnings=warns, seconds=time.time() - t0, ckt=ckt)
    dut = compile_sky130(ckt, "dut")
    conds = conds or [NOMINAL]
    jobs, idx = [], []
    for ci, c in enumerate(conds):
        for net, files in fam.build(dut, ckt, c, task.get("tb", {})):
            jobs.append((net, files)); idx.append(ci)
    results = ng.run_many([j[0] for j in jobs], wrdata_files=tuple(sorted({f for _, fs in jobs for f in fs})),
                          timeout=timeout)
    res = EvalResult("ok", warnings=warns, n_sims=len(jobs), ckt=ckt)
    worst = 0.0
    all_pass = True
    for ci, c in enumerate(conds):
        rs = [r for r, i in zip(results, idx) if i == ci]
        name = cond_name(c)
        if not all(r.ok for r in rs) and not any(r.vectors or r.scalars for r in rs):
            res.per_cond[name] = {}
            res.errors.append(f"{name}: simulation failed: " + "; ".join(r.error[:300] for r in rs if r.error))
            chk, tot = check(task["specs"], {})
        else:
            try:
                m = fam.measure(rs, c, task.get("tb", {}))
            except Exception as e:  # measurement crash -> treat as failure with message
                m = {"_ops": {}}
                res.errors.append(f"{name}: measurement error: {type(e).__name__}: {e}")
            if ci == 0 and keep_ops:
                res.ops = m.get("_ops", {})
            res.per_cond[name] = {k: v for k, v in m.items() if k != "_ops"}
            chk, tot = check(task["specs"], m)
            for r in rs:
                if r.error:
                    res.warnings.append(f"{name}: {r.error[:200]}")
        res.checks[name] = chk
        worst = max(worst, tot)
        all_pass = all_pass and all(p for _, p, _ in chk.values())
    if not res.per_cond or all(not v for v in res.per_cond.values()):
        res.status = "sim_error"
    res.score = worst
    res.passed = all_pass and res.status == "ok"
    res.seconds = time.time() - t0
    return res


def region_report(ops: dict, margin=0.05):
    """Classify each MOSFET's operating region from op-point data."""
    rep = {}
    for dn, o in ops.items():
        vds, vgs, vth, vdsat, idv = (abs(o.get(k) or 0.0) for k in ("vds", "vgs", "vth", "vdsat", "id"))
        gm = abs(o.get("gm") or 0.0)
        if idv < 1e-9:
            reg = "off"
        elif vgs < vth - 0.05:
            reg = "subthreshold" + ("" if vds > 0.1 else "/triode")
        elif vds < vdsat + margin:
            reg = "triode" if vds < vdsat else "edge-of-saturation"
        else:
            reg = "saturation"
        rep[dn] = {"region": reg, "id_uA": round(idv * 1e6, 3), "gm_id": round(gm / max(idv, 1e-15), 2),
                   "vgs": round(vgs, 3), "vds": round(vds, 3), "vth": round(vth, 3), "vdsat": round(vdsat, 3),
                   "vds_margin": round(vds - vdsat, 3),
                   "gm_gds": round(gm / max(abs(o.get('gds') or 1e-15), 1e-15), 1)}
    return rep
