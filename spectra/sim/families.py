"""Testbenches for all circuit families except the op-amp (see tb_opamp.py).

Every family exposes: PORTS (default), build(dut, ckt, cond, p) -> [(netlist, files)],
measure(results, cond, p) -> dict of metrics (+ '_ops' device operating points).
"""
from __future__ import annotations

import math
import numpy as np

from . import ngspice as ng
from .measure import ac_metrics, mag_at, slew_settle, swing_from_dc, _cross
from .netlist import device_op_saves


def _head(cond, title):
    seed = f".option seed={cond['seed']}\n" if "seed" in cond else ""
    return (f"* {title}\n{ng.lib_line(cond.get('corner', 'tt'))}\n.temp {cond.get('temp', 27)}\n"
            ".option gmin=1e-15 reltol=1e-4\n" + seed)


def _op_block(ckt, inst):
    saves = device_op_saves(ckt, inst)
    save_line = " ".join(s for _, _, s in saves)
    echo = "\n".join(f'echo "@@ op:{dn}:{k} $&{s}"' for dn, k, s in saves)
    return save_line, echo


def _ops(sc):
    ops = {}
    for k, v in sc.items():
        if k.startswith("op:"):
            _, dn, q = k.split(":")
            ops.setdefault(dn, {})[q] = v
    return ops


def _arr(r, f, cols=2):
    a = r.vectors.get(f)
    if a is None or a.ndim != 2 or a.shape[1] < cols or len(a) < 3:
        return None
    return a


# ---------------------------------------------------------------- amp
class Amp:
    """Single-ended voltage amplifier. vin is DC-biased at p['vin_dc'] by the testbench."""
    PORTS = ["vin", "vout", "vdd", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, vin_dc, iref, cl = cond.get("vdd", 1.8), p.get("vin_dc", 0.9), p.get("iref", 10e-6), p.get("cl", 1e-12)
        rl = p.get("rl")
        sl, echo = _op_block(ckt, "xd1")
        net = f"""{_head(cond, 'amp tb')}{dut}
Vdd vdd 0 DC {vdd} AC 0
Iref vdd ib DC {iref}
Vin vin 0 DC {vin_dc} AC 1
Xd1 vin vout vdd 0 ib dut
CL vout 0 {cl}
{f'RL vout 0 {rl}' if rl else ''}
.control
set wr_singlescale
save all {sl}
op
echo "@@ idd $&i(vdd)"
echo "@@ vout_dc $&v(vout)"
{echo}
ac dec 20 1 1e11
wrdata ac.txt v(vout)
dc vin {vin_dc - 0.3:.4f} {vin_dc + 0.3:.4f} 0.002
wrdata dc.txt v(vout)
.endc
.end
"""
        return [(net, ("ac.txt", "dc.txt"))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; sc = r.scalars; vdd = cond.get("vdd", 1.8); m = {}
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd
        m["vout_dc"] = sc.get("vout_dc")
        a = _arr(r, "ac.txt", 3)
        if a is not None:
            am = ac_metrics(a[:, 0], a[:, 1], a[:, 2])
            m["gain_db"], m["f3db"], m["ugbw"] = am["gain_db"], am["f3db"], am["ugbw"]
            m["inverting"] = 1.0 if am["inverting"] else 0.0
            if am["f3db"] is not None:
                m["gbw"] = 10 ** (am["gain_db"] / 20) * am["f3db"]
        d = _arr(r, "dc.txt")
        if d is not None:
            # swing: output range where |dVout/dVin| >= 50% of its value at the bias point
            vin, vo = d[:, 0], d[:, 1]
            g = np.abs(np.gradient(vo, vin)); c = len(g) // 2
            if g[c] > 0:
                ok = g >= 0.5 * g[c]; lo = hi = c
                while lo > 0 and ok[lo - 1]: lo -= 1
                while hi < len(g) - 1 and ok[hi + 1]: hi += 1
                m["swing"] = float(abs(vo[hi] - vo[lo]))
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- tia
class TIA:
    """Transimpedance amplifier: AC current into `iin` with photodiode capacitance."""
    PORTS = ["iin", "vout", "vdd", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, iref, cl, cpd = cond.get("vdd", 1.8), p.get("iref", 10e-6), p.get("cl", 0.2e-12), p.get("cpd", 0.5e-12)
        sl, echo = _op_block(ckt, "xd1")
        net = f"""{_head(cond, 'tia tb')}{dut}
Vdd vdd 0 DC {vdd}
Iref vdd ib DC {iref}
Iin 0 iin DC 0 AC 1
Cpd iin 0 {cpd}
Xd1 iin vout vdd 0 ib dut
CL vout 0 {cl}
.control
set wr_singlescale
save all {sl}
op
echo "@@ idd $&i(vdd)"
echo "@@ vout_dc $&v(vout)"
echo "@@ vin_dc $&v(iin)"
{echo}
ac dec 20 1 1e11
wrdata ac.txt v(vout)
noise v(vout) Iin dec 10 1e3 1e10
setplot noise1
wrdata noise.txt inoise_spectrum
.endc
.end
"""
        return [(net, ("ac.txt", "noise.txt"))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; sc = r.scalars; vdd = cond.get("vdd", 1.8); m = {}
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd
        m["vout_dc"], m["vin_dc"] = sc.get("vout_dc"), sc.get("vin_dc")
        a = _arr(r, "ac.txt", 3)
        if a is not None:
            am = ac_metrics(a[:, 0], a[:, 1], a[:, 2])
            m["zt_dbohm"], m["f3db"] = am["gain_db"], am["f3db"]
        n = _arr(r, "noise.txt")
        if n is not None:
            m["in_noise_1m"] = float(10 ** np.interp(6.0, np.log10(n[:, 0]), np.log10(np.maximum(n[:, 1], 1e-40))))
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- current mirror
class CMirror:
    """Current mirror / sink. Ideal Iin flows from vdd into `iin`; `iout` is held by a
    voltage source Vo. direction='sink' -> current flows INTO iout from Vo."""
    PORTS = ["iin", "iout", "vdd", "vss"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, iin, vnom = cond.get("vdd", 1.8), p.get("iin", 10e-6), p.get("vout_nom", 0.9)
        sink = p.get("direction", "sink") == "sink"
        sl, echo = _op_block(ckt, "xd1")
        iin_line = f"Iin vdd iin DC {iin}" if sink else f"Iin iin 0 DC {iin}"
        net = f"""{_head(cond, 'current mirror tb')}{dut}
Vdd vdd 0 DC {vdd}
{iin_line}
Vo vo 0 DC {vnom}
Vm vo iout DC 0
Xd1 iin iout vdd 0 dut
.control
set wr_singlescale
save all {sl}
op
echo "@@ iout $&i(vm)"
echo "@@ idd $&i(vdd)"
echo "@@ vin_node $&v(iin)"
{echo}
dc vo 0 {vdd} 0.01
wrdata dc.txt i(vm)
.endc
.end
"""
        return [(net, ("dc.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; sc = r.scalars; vdd = cond.get("vdd", 1.8); m = {}
        sink = p.get("direction", "sink") == "sink"
        sgn = 1.0 if sink else -1.0
        vnom = p.get("vout_nom", 0.9)
        if sc.get("iout") is not None:
            m["iout"] = sgn * sc["iout"]
            tgt = p.get("iout_target")
            if tgt:
                m["iout_err_pct"] = abs(m["iout"] / tgt - 1) * 100
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd + (0 if sink else 0)
        m["vin_node"] = sc.get("vin_node")
        d = _arr(r, "dc.txt")
        if d is not None and m.get("iout"):
            v, i = d[:, 0], sgn * d[:, 1]
            k = int(np.argmin(np.abs(v - vnom)))
            k0, k1 = max(k - 5, 0), min(k + 5, len(v) - 1)
            di = (i[k1] - i[k0]) / (v[k1] - v[k0])
            m["rout"] = float(1 / max(abs(di), 1e-15))
            inom = i[k]
            if sink:   # compliance: lowest Vo with I >= 0.95*I(vnom), scanning down from vnom
                j = k
                while j > 0 and i[j - 1] >= 0.95 * inom: j -= 1
                m["v_compliance"] = float(v[j])
            else:      # source: highest Vo with I >= 0.95*I(vnom); report headroom vdd - v
                j = k
                while j < len(v) - 1 and i[j + 1] >= 0.95 * inom: j += 1
                m["v_compliance"] = float(vdd - v[j])
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- LDO
class LDO:
    """LDO: input supply vin, ideal reference vref, load current sink at vout."""
    PORTS = ["vin", "vout", "vref", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vin = cond.get("vdd", 1.8); vref = p.get("vref", 0.6); iref = p.get("iref", 10e-6)
        imax, imin, cl = p.get("iload_max", 5e-3), p.get("iload_min", 50e-6), p.get("cl", 100e-12)
        esr = p.get("esr", 0)
        sl, echo = _op_block(ckt, "xd1")
        cl_line = f"CL vout 0 {cl}" if not esr else f"CL vout cesr {cl}\nResr cesr 0 {esr}"
        net_a = f"""{_head(cond, 'ldo tb dc/ac')}{dut}
Vin vin 0 DC {vin} AC 1
Vref vref 0 DC {vref}
Iref vin ib DC {iref}
Il vout 0 DC {imax}
Xd1 vin vout vref 0 ib dut
{cl_line}
.control
set wr_singlescale
save all {sl}
op
echo "@@ vout_imax $&v(vout)"
echo "@@ iin_imax $&i(vin)"
{echo}
ac dec 10 10 1e9
wrdata ac.txt v(vout)
dc il {imin} {imax} {(imax - imin) / 20}
wrdata load.txt v(vout)
dc vin {vin - 0.1:.4f} {vin + 0.1:.4f} 0.01
wrdata line.txt v(vout)
alter il dc={imin}
op
echo "@@ vout_imin $&v(vout)"
echo "@@ iin_imin $&i(vin)"
.endc
.end
"""
        net_b = f"""{_head(cond, 'ldo tb tran')}{dut}
Vin vin 0 DC {vin}
Vref vref 0 DC {vref}
Iref vin ib DC {iref}
Il vout 0 PULSE({imin} {imax} 5u 100n 100n 10u 30u)
Xd1 vin vout vref 0 ib dut
{cl_line}
.control
set wr_singlescale
tran 10n 25u
wrdata tran.txt v(vout)
.endc
.end
"""
        return [(net_a, ("ac.txt", "load.txt", "line.txt")), (net_b, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r, rt = rs; sc = r.scalars; m = {}
        imax, imin = p.get("iload_max", 5e-3), p.get("iload_min", 50e-6)
        vin = cond.get("vdd", 1.8)
        m["vout"] = sc.get("vout_imax")
        if sc.get("vout_imin") is not None and sc.get("vout_imax") is not None:
            m["load_reg"] = abs(sc["vout_imin"] - sc["vout_imax"]) / (imax - imin)   # V/A = mV/mA
        if sc.get("iin_imin") is not None:
            m["iq"] = -sc["iin_imin"] - imin
        tgt = p.get("vout_target")
        if tgt and m.get("vout") is not None:
            m["vout_err_pct"] = abs(m["vout"] / tgt - 1) * 100
        a = _arr(r, "ac.txt", 3)
        if a is not None:
            for f0, nm in ((1e3, "psrr_1k"), (1e6, "psrr_1m")):
                g = mag_at(a[:, 0], a[:, 1], a[:, 2], f0)
                m[nm] = float(-20 * np.log10(max(g, 1e-30)))
        ln = _arr(r, "line.txt")
        if ln is not None:
            m["line_reg"] = float(abs(ln[-1, 1] - ln[0, 1]) / (ln[-1, 0] - ln[0, 0]))  # V/V
        t = _arr(rt, "tran.txt")
        if t is not None:
            tt, v = t[:, 0], t[:, 1]
            pre = v[(tt > 4e-6) & (tt < 5e-6)]
            on = v[(tt > 5e-6) & (tt < 15e-6)]
            post = v[(tt > 15e-6) & (tt < 25e-6)]
            if len(pre) and len(on) and len(post):
                v0 = pre.mean()
                m["undershoot"] = float(max(0.0, v0 - on.min()))
                m["overshoot"] = float(max(0.0, post.max() - v0))
                # ringing / stability proxy: settled within 1% of final value by 5us after edge
                tail_on = v[(tt > 12e-6) & (tt < 15e-6)]
                tail_post = v[(tt > 22e-6) & (tt < 25e-6)]
                m["ripple_settled"] = float(max(np.ptp(tail_on), np.ptp(tail_post)))
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- voltage reference
class Ref:
    """Self-biased voltage reference (bandgap or MOS-only). Ports: vdd vref vss."""
    PORTS = ["vdd", "vref", "vss"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd = cond.get("vdd", 1.8)
        sl, echo = _op_block(ckt, "xd1")
        temps = p.get("temps", (-40, 125))
        net_a = f"""{_head(cond, 'ref tb')}{dut}
Vdd vdd 0 DC {vdd} AC 1
Xd1 vdd vref 0 dut
Cl vref 0 1p
.control
set wr_singlescale
save all {sl}
op
echo "@@ vref $&v(vref)"
echo "@@ idd $&i(vdd)"
{echo}
dc temp {temps[0]} {temps[1]} 5
wrdata temp.txt v(vref)
.endc
.end
"""
        net_b = f"""{_head(cond, 'ref tb line/psrr')}{dut}
Vdd vdd 0 DC {vdd} AC 1
Xd1 vdd vref 0 dut
Cl vref 0 1p
.control
set wr_singlescale
ac dec 10 10 1e8
wrdata ac.txt v(vref)
dc vdd {vdd - 0.2:.3f} {vdd + 0.2:.3f} 0.02
wrdata line.txt v(vref)
.endc
.end
"""
        net_c = f"""{_head(cond, 'ref tb startup')}{dut}
Vdd vdd 0 PWL(0 0 10u {vdd})
Xd1 vdd vref 0 dut
Cl vref 0 1p
.control
set wr_singlescale
tran 20n 60u
wrdata tran.txt v(vref)
.endc
.end
"""
        return [(net_a, ("temp.txt",)), (net_b, ("ac.txt", "line.txt")), (net_c, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        ra, rb, rc = rs; sc = ra.scalars; vdd = cond.get("vdd", 1.8); m = {}
        m["vref"] = sc.get("vref")
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd
        t = _arr(ra, "temp.txt")
        if t is not None and m["vref"]:
            v = t[:, 1]
            m["tc_ppm"] = float((v.max() - v.min()) / (abs(v.mean()) * (t[-1, 0] - t[0, 0])) * 1e6)
        ln = _arr(rb, "line.txt")
        if ln is not None:
            m["line_reg"] = float(abs(ln[-1, 1] - ln[0, 1]) / (ln[-1, 0] - ln[0, 0]))
        a = _arr(rb, "ac.txt", 3)
        if a is not None:
            m["psrr_1k"] = float(-20 * np.log10(max(mag_at(a[:, 0], a[:, 1], a[:, 2], 1e3), 1e-30)))
        tr = _arr(rc, "tran.txt")
        if tr is not None and m.get("vref"):
            fin = tr[tr[:, 0] > 50e-6, 1]
            m["startup_ok"] = 1.0 if (len(fin) and abs(fin.mean() - m["vref"]) < 0.01 * abs(m["vref"]) + 1e-3) else 0.0
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- continuous-time comparator
class Comparator:
    PORTS = ["vinp", "vinn", "vout", "vdd", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, vcm, iref, cl, vod = cond.get("vdd", 1.8), p.get("vcm", 0.9), p.get("iref", 10e-6), p.get("cl", 50e-15), p.get("vod", 10e-3)
        sl, echo = _op_block(ckt, "xd1")
        net_a = f"""{_head(cond, 'comparator tb dc')}{dut}
Vdd vdd 0 DC {vdd}
Iref vdd ib DC {iref}
Vn vinn 0 DC {vcm}
Vp vinp 0 DC {vcm - 0.05}
Xd1 vinp vinn vout vdd 0 ib dut
CL vout 0 {cl}
.control
set wr_singlescale
save all {sl}
op
echo "@@ idd_low $&i(vdd)"
echo "@@ vout_low $&v(vout)"
{echo}
dc vp {vcm - 0.05} {vcm + 0.05} 0.0005
wrdata dc.txt v(vout)
.endc
.end
"""
        tper = p.get("tper", 200e-9)
        net_b = f"""{_head(cond, 'comparator tb tran')}{dut}
Vdd vdd 0 DC {vdd}
Iref vdd ib DC {iref}
Vn vinn 0 DC {vcm}
Vp vinp 0 PULSE({vcm - vod} {vcm + vod} {tper / 4} 10p 10p {tper / 2} {tper})
Xd1 vinp vinn vout vdd 0 ib dut
CL vout 0 {cl}
.control
set wr_singlescale
tran {tper / 2000} {tper * 1.25 + tper / 4}
wrdata tran.txt v(vout) i(vdd)
.endc
.end
"""
        return [(net_a, ("dc.txt",)), (net_b, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        ra, rb = rs; sc = ra.scalars; vdd = cond.get("vdd", 1.8); vcm = p.get("vcm", 0.9); m = {}
        tper = p.get("tper", 200e-9)
        d = _arr(ra, "dc.txt")
        if d is not None:
            vin, vo = d[:, 0], d[:, 1]
            m["vout_min"], m["vout_max"] = float(vo.min()), float(vo.max())
            hi = np.where(vo > vdd / 2)[0]
            if len(hi) and 0 < hi[0]:
                m["offset"] = float(vin[hi[0]] - vcm)
        if sc.get("idd_low") is not None:
            m["power"] = -sc["idd_low"] * vdd
        t = _arr(rb, "tran.txt", 3)
        if t is not None:
            tt, vo, idd = t[:, 0], t[:, 1], t[:, 2]
            t_r, t_f = tper / 4, tper / 4 + tper / 2
            pre = vo[(tt > t_r * 0.5) & (tt < t_r)]
            if len(pre) and pre.mean() > vdd / 2:
                m["polarity_ok"] = 0.0
            else:
                m["polarity_ok"] = 1.0
            seg_r = tt >= t_r
            x = _cross(tt[seg_r], vo[seg_r], vdd / 2)
            m["tpd_rise"] = (x - t_r) if (x is not None and x < t_f and m["polarity_ok"]) else None
            seg_f = tt >= t_f
            x2 = _cross(tt[seg_f], vdd - vo[seg_f], vdd / 2)
            m["tpd_fall"] = (x2 - t_f) if (x2 is not None and m["polarity_ok"]) else None
            if m["tpd_rise"] is not None and m["tpd_fall"] is not None:
                m["tpd"] = max(m["tpd_rise"], m["tpd_fall"])
            m["power_avg"] = float(-np.trapezoid(idd, tt) / (tt[-1] - tt[0]) * vdd)
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- clocked (latched) comparator
class Latch:
    PORTS = ["vinp", "vinn", "clk", "outp", "outn", "vdd", "vss"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, vcm, dv, fclk, cl = cond.get("vdd", 1.8), p.get("vcm", 0.9), p.get("dv", 1e-3), p.get("fclk", 500e6), p.get("cl", 20e-15)
        T = 1 / fclk
        # cycle1: +dv, cycle2: -dv ; clk high = evaluate
        net = f"""{_head(cond, 'latch tb')}{dut}
Vdd vdd 0 DC {vdd}
Vclk clk 0 PULSE(0 {vdd} {T / 2} {T / 50} {T / 50} {T / 2 - T / 50} {T})
Vn vinn 0 DC {vcm}
Vp vinp 0 PWL(0 {vcm + dv / 2} {1.4 * T} {vcm + dv / 2} {1.45 * T} {vcm - dv / 2} {3 * T} {vcm - dv / 2})
Vnn vinn2 0 DC 0
Xd1 vinp vinn clk outp outn vdd 0 dut
C1 outp 0 {cl}
C2 outn 0 {cl}
.control
set wr_singlescale
tran {T / 400} {2.5 * T}
wrdata tran.txt v(outp) v(outn) i(vdd)
.endc
.end
"""
        return [(net, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; vdd = cond.get("vdd", 1.8); m = {}
        T = 1 / p.get("fclk", 500e6)
        t = _arr(r, "tran.txt", 4)
        if t is None:
            m["_ops"] = {}
            return m
        tt, op, on, idd = t[:, 0], t[:, 1], t[:, 2], t[:, 3]
        ok, delays = 1.0, []
        for k, sign in ((0, +1), (1, -1)):
            t_ev = T / 2 + k * T + T / 100        # clk rising 50%
            t_end = T + k * T - T / 50            # just before clk falls
            i_end = np.searchsorted(tt, t_end)
            vp, vn = op[i_end], on[i_end]
            good = (vp > 0.9 * vdd and vn < 0.1 * vdd) if sign > 0 else (vn > 0.9 * vdd and vp < 0.1 * vdd)
            ok = ok if good else 0.0
            seg = (tt >= t_ev) & (tt <= t_end)
            diff = sign * (op[seg] - on[seg])
            x = _cross(tt[seg], diff, vdd / 2)
            delays.append((x - t_ev) if x is not None else None)
            # reset check: during clk low, outputs should be in a common reset state (|outp - outn| small)
            t_rst = T + k * T + T / 2 - T / 50 if k == 0 else None
            if t_rst is not None:
                j = np.searchsorted(tt, t_rst)
                if abs(op[j] - on[j]) > 0.2 * vdd:
                    ok = 0.0
        m["correct"] = ok
        m["delay"] = max(delays) if all(d is not None for d in delays) else None
        sel = (tt >= T / 2) & (tt <= 2.5 * T)
        m["energy"] = float(-np.trapezoid(idd[sel], tt[sel]) * vdd / 2.0)   # per comparison
        m["_ops"] = {}
        return m


# ---------------------------------------------------------------- VCO
class VCO:
    PORTS = ["vctrl", "vout", "vdd", "vss"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, cl = cond.get("vdd", 1.8), p.get("cl", 10e-15)
        vlo, vhi = p.get("vctrl_range", (0.6, 1.2))
        vmid = (vlo + vhi) / 2
        tstop = p.get("tstop", 200e-9)
        lines = []
        for i, vc in enumerate((vlo, vmid, vhi)):
            lines.append(f"Vdd{i} vdd{i} 0 DC {vdd}\nVc{i} vc{i} 0 DC {vc}\nXd{i} vc{i} vo{i} vdd{i} 0 dut\n"
                         f"CL{i} vo{i} 0 {cl}\nIk{i} 0 vo{i} PULSE(0 50u 0 10p 10p 0.5n 1)")
        net = f"""{_head(cond, 'vco tb')}{dut}
{chr(10).join(lines)}
.control
set wr_singlescale
tran {tstop / 20000} {tstop}
wrdata tran.txt v(vo0) v(vo1) v(vo2) i(vdd1)
.endc
.end
"""
        return [(net, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; vdd = cond.get("vdd", 1.8); m = {}
        t = _arr(r, "tran.txt", 5)
        if t is None:
            m["_ops"] = {}
            return m
        tt = t[:, 0]; half = tt > tt[-1] * 0.4
        freqs, swings = [], []
        for col in (1, 2, 3):
            v = t[:, col][half]; ts = tt[half]
            s = np.sign(v - vdd / 2)
            idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
            if len(idx) >= 3:
                tc = ts[idx] + (vdd / 2 - v[idx]) * (ts[idx + 1] - ts[idx]) / np.maximum(v[idx + 1] - v[idx], 1e-12)
                freqs.append(float(1 / np.mean(np.diff(tc))))
            else:
                freqs.append(None)
            swings.append(float(np.ptp(v)) if len(v) else 0.0)
        m["f_lo"], m["f_mid"], m["f_hi"] = freqs
        if all(f is not None for f in freqs):
            m["fmin"], m["fmax"] = min(freqs), max(freqs)
            m["tuning_ratio"] = max(freqs) / max(min(freqs), 1.0)
            vlo, vhi = p.get("vctrl_range", (0.6, 1.2))
            m["kvco"] = abs(freqs[2] - freqs[0]) / (vhi - vlo)
        m["swing"] = min(swings)
        idd = t[:, 4][half]
        m["power"] = float(-np.mean(idd) * vdd)
        m["_ops"] = {}
        return m


# ---------------------------------------------------------------- filter
class Filter:
    PORTS = ["vin", "vout", "vdd", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, vcm, iref, cl = cond.get("vdd", 1.8), p.get("vcm", 0.9), p.get("iref", 10e-6), p.get("cl", 1e-12)
        sl, echo = _op_block(ckt, "xd1")
        net = f"""{_head(cond, 'filter tb')}{dut}
Vdd vdd 0 DC {vdd}
Iref vdd ib DC {iref}
Vin vin 0 DC {vcm} AC 1
Xd1 vin vout vdd 0 ib dut
CL vout 0 {cl}
.control
set wr_singlescale
save all {sl}
op
echo "@@ idd $&i(vdd)"
echo "@@ vout_dc $&v(vout)"
{echo}
ac dec 40 10 1e10
wrdata ac.txt v(vout)
.endc
.end
"""
        return [(net, ("ac.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; sc = r.scalars; vdd = cond.get("vdd", 1.8); m = {}
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd
        m["vout_dc"] = sc.get("vout_dc")
        a = _arr(r, "ac.txt", 3)
        if a is not None:
            f, h = a[:, 0], np.abs(a[:, 1] + 1j * a[:, 2])
            hdb = 20 * np.log10(np.maximum(h, 1e-30))
            kind = p.get("kind", "lowpass")
            if kind == "lowpass":
                g0 = hdb[0]; m["gain_db"] = float(g0)
                idx = np.where(hdb < g0 - 3)[0]
                m["fc"] = float(f[idx[0]]) if len(idx) else None
                m["peaking_db"] = float(hdb.max() - g0)
                if m["fc"]:
                    fs = p.get("stop_ratio", 10) * m["fc"]
                    m["atten_db"] = float(g0 - np.interp(np.log10(fs), np.log10(f), hdb))
            else:  # bandpass
                k = int(np.argmax(hdb)); m["gain_db"] = float(hdb[k]); m["f0"] = float(f[k])
                lo = np.where(hdb[:k] < hdb[k] - 3)[0]; hi = np.where(hdb[k:] < hdb[k] - 3)[0]
                if len(lo) and len(hi):
                    bw = f[k + hi[0]] - f[lo[-1]]
                    m["q"] = float(f[k] / bw)
        m["_ops"] = _ops(sc)
        return m


# ---------------------------------------------------------------- Schmitt trigger
class Schmitt:
    PORTS = ["vin", "vout", "vdd", "vss"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd = cond.get("vdd", 1.8)
        net = f"""{_head(cond, 'schmitt tb')}{dut}
Vdd vdd 0 DC {vdd}
Vin vin 0 PWL(0 0 10u {vdd} 20u 0)
Xd1 vin vout vdd 0 dut
CL vout 0 10f
.control
set wr_singlescale
tran 5n 20u
wrdata tran.txt v(vin) v(vout) i(vdd)
.endc
.end
"""
        return [(net, ("tran.txt",))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; vdd = cond.get("vdd", 1.8); m = {}
        t = _arr(r, "tran.txt", 4)
        if t is None:
            m["_ops"] = {}
            return m
        tt, vi, vo, idd = t[:, 0], t[:, 1], t[:, 2], t[:, 3]
        inv = p.get("inverting", False)
        y = (vdd - vo) if inv else vo
        up = tt <= 10e-6; dn = tt > 10e-6
        iu = np.where(y[up] > vdd / 2)[0]
        idn = np.where(y[dn] < vdd / 2)[0]
        m["vth_hi"] = float(vi[up][iu[0]]) if len(iu) else None
        m["vth_lo"] = float(vi[dn][idn[0]]) if len(idn) else None
        if m["vth_hi"] is not None and m["vth_lo"] is not None:
            m["hysteresis"] = m["vth_hi"] - m["vth_lo"]
        m["vout_min"], m["vout_max"] = float(vo.min()), float(vo.max())
        m["power_avg"] = float(-np.trapezoid(idd, tt) / tt[-1] * vdd)
        m["_ops"] = {}
        return m


# ---------------------------------------------------------------- op-amp based closed-loop circuits
class OpampApp:
    """Closed-loop op-amp circuits around an ideal common-mode reference `vcm`.
    p['func'] in {'inv', 'noninv', 'sum', 'diff', 'integ'}; inputs vin1, vin2."""
    PORTS = ["vin1", "vin2", "vout", "vcm", "vdd", "vss", "ibias"]

    @staticmethod
    def build(dut, ckt, cond, p):
        vdd, vcm, iref, cl = cond.get("vdd", 1.8), p.get("vcm", 0.9), p.get("iref", 10e-6), p.get("cl", 1e-12)
        sl, echo = _op_block(ckt, "xd1")
        net = f"""{_head(cond, 'opamp-app tb')}{dut}
Vdd vdd 0 DC {vdd}
Iref vdd ib DC {iref}
Vcm vcm 0 DC {vcm}
V1 vin1 0 DC {vcm} AC 1
V2 vin2 0 DC {vcm} AC 0
Xd1 vin1 vin2 vout vcm vdd 0 ib dut
CL vout 0 {cl}
.control
set wr_singlescale
save all {sl}
op
echo "@@ idd $&i(vdd)"
echo "@@ vout_dc $&v(vout)"
{echo}
ac dec 20 1 1e10
wrdata ac1.txt v(vout)
alter @v1[acmag]=0
alter @v2[acmag]=1
ac dec 20 1 1e10
wrdata ac2.txt v(vout)
dc v1 {vcm - 0.05} {vcm + 0.05} 0.005
wrdata dc1.txt v(vout)
.endc
.end
"""
        return [(net, ("ac1.txt", "ac2.txt", "dc1.txt"))]

    @staticmethod
    def measure(rs, cond, p):
        r = rs[0]; sc = r.scalars; vdd = cond.get("vdd", 1.8); vcm = p.get("vcm", 0.9); m = {}
        if sc.get("idd") is not None:
            m["power"] = -sc["idd"] * vdd
        if sc.get("vout_dc") is not None:
            m["vout_offset"] = sc["vout_dc"] - vcm
        func = p.get("func", "inv")
        for k in ("1", "2"):
            a = _arr(r, f"ac{k}.txt", 3)
            if a is None:
                continue
            f, h = a[:, 0], a[:, 1] + 1j * a[:, 2]
            if func == "integ" and k == "1":
                mag = np.abs(h)
                idx = np.where(mag < 1.0)[0]
                if len(idx) and idx[0] > 0:
                    i = idx[0]
                    x0, x1 = np.log10(f[i - 1]), np.log10(f[i])
                    y0, y1 = np.log10(mag[i - 1]), np.log10(mag[i])
                    m["f_unity"] = float(10 ** (x0 + (0 - y0) * (x1 - x0) / (y1 - y0)))
                    # integrator slope between f_unity/100 and f_unity/10 (ideal -20 dB/dec)
                    fa, fb = m["f_unity"] / 100, m["f_unity"] / 10
                    ga = np.interp(np.log10(fa), np.log10(f), 20 * np.log10(np.maximum(mag, 1e-30)))
                    gb = np.interp(np.log10(fb), np.log10(f), 20 * np.log10(np.maximum(mag, 1e-30)))
                    m["slope_db_dec"] = float(gb - ga)
                m["gain_dc_db"] = float(20 * np.log10(max(mag[0], 1e-30)))
            else:
                g = h[min(np.searchsorted(f, 100), len(h) - 1)]
                m[f"a{k}"] = float(np.real(g))     # signed low-frequency gain
                mag = np.abs(h); g0 = mag[0]
                idx = np.where(mag < g0 / math.sqrt(2))[0]
                if len(idx):
                    m[f"bw{k}"] = float(f[idx[0]])
        if "bw1" in m and "bw2" in m:
            m["bw"] = min(m["bw1"], m["bw2"])
        elif "bw1" in m:
            m["bw"] = m["bw1"]
        m["_ops"] = _ops(sc)
        return m


REGISTRY = {"amp": Amp, "tia": TIA, "cmirror": CMirror, "ldo": LDO, "ref": Ref,
            "comparator": Comparator, "latch": Latch, "vco": VCO, "filter": Filter,
            "schmitt": Schmitt, "opamp_app": OpampApp}
