"""Single-ended-output operational amplifier / OTA testbench.

DUT ports: vinp vinn vout vdd vss ibias.  An ideal reference current IREF flows
from VDD into `ibias` (the DUT must sink it, e.g. with a diode-connected nfet).
Three DUT instances are simulated in ONE ngspice run:
  X1: open loop with a DC servo (1 GOhm / 1 F) -> AC DM gain, CM gain, PSRR, noise, op-point
  X2: unity-gain buffer, large-signal step -> slew rate, settling
  X3: inverting gain of -10 around VCM, DC sweep -> output swing
"""
from __future__ import annotations

import numpy as np

from . import ngspice as ng
from .measure import ac_metrics, mag_at, slew_settle, swing_from_dc
from .netlist import device_op_saves

PORTS = ["vinp", "vinn", "vout", "vdd", "vss", "ibias"]


def build(dut_sky130: str, ckt, cond: dict, p: dict) -> list:
    vdd, vcm, iref, cl = cond.get("vdd", 1.8), p.get("vcm", 0.9), p.get("iref", 10e-6), p.get("cl", 1e-12)
    a = p.get("step", 0.4) / 2
    saves = device_op_saves(ckt, "xd1")
    save_line = " ".join(s for _, _, s in saves)
    echo_ops = "\n".join(f'echo "@@ op:{dn}:{k} $&{s}"' for dn, k, s in saves)
    sw = 0.9 * min(vcm, vdd - vcm) / 10.0
    net_a = f"""* opamp testbench
{ng.lib_line(cond.get('corner', 'tt'))}
.temp {cond.get('temp', 27)}
.option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7
{dut_sky130}
* --- X1: open loop + DC servo
Vdd1 vdd1 0 DC {vdd} AC 0
Iref1 vdd1 ib1 DC {iref}
Vcm1 cm1 0 DC {vcm}
Vin1 vinp1 cm1 DC 0 AC 1
Xd1 vinp1 vinn1 vout1 vdd1 0 ib1 dut
Rfb1 vout1 vinn1 1e9
Cfb1 vinn1 acg1 1
Vacg1 acg1 0 DC 0 AC 0
CL1 vout1 0 {cl}
* --- X3: inverting gain -10 for output swing
Vdd3 vdd3 0 DC {vdd}
Iref3 vdd3 ib3 DC {iref}
Vref3 ref3 0 DC {vcm}
Vs3 vs3 0 DC {vcm}
Rin3 vs3 vneg3 100k
Rf3 vneg3 vout3 1Meg
Xd3 ref3 vneg3 vout3 vdd3 0 ib3 dut
CL3 vout3 0 {cl}
.control
set wr_singlescale
save all {save_line}
op
echo "@@ idd $&i(vdd1)"
echo "@@ vout_dc $&v(vout1)"
let vos = v(vout1) - v(vinp1)
echo "@@ vos $&vos"
{echo_ops}
ac dec 20 0.01 1e10
wrdata ac_dm.txt v(vout1)
noise v(vout1) vin1 dec 10 1 1e8
setplot noise1
wrdata noise.txt inoise_spectrum
setplot ac1
alter @vacg1[acmag]=1
ac dec 5 0.01 10
wrdata ac_cm.txt v(vout1)
alter @vacg1[acmag]=0
alter @vin1[acmag]=0
alter @vdd1[acmag]=1
ac dec 5 0.01 10
wrdata ac_ps.txt v(vout1)
dc vs3 {vcm - sw:.4f} {vcm + sw:.4f} {sw / 60:.5f}
wrdata dc.txt v(vout3)
.endc
.end
"""
    net_b = f"""* opamp testbench (transient)
{ng.lib_line(cond.get('corner', 'tt'))}
.temp {cond.get('temp', 27)}
{dut_sky130}
Vdd2 vdd2 0 DC {vdd}
Iref2 vdd2 ib2 DC {iref}
Vin2 vinp2 0 PULSE({vcm - a} {vcm + a} 1u 1n 1n 4u 10u)
Xd2 vinp2 vout2 vout2 vdd2 0 ib2 dut
CL2 vout2 0 {cl}
.control
tran 4n 9u
wrdata tran.txt v(vout2)
.endc
.end
"""
    return [(net_a, FILES_A), (net_b, FILES_B)]


FILES_A = ("ac_dm.txt", "ac_cm.txt", "ac_ps.txt", "dc.txt", "noise.txt")
FILES_B = ("tran.txt",)


def measure(rs: list, cond: dict, p: dict) -> dict:
    vdd, vcm = cond.get("vdd", 1.8), p.get("vcm", 0.9)
    m = {}
    r = rs[0]
    r.vectors.update(rs[1].vectors)
    sc = r.scalars
    if sc.get("idd") is not None:
        m["power"] = -sc["idd"] * vdd
    if sc.get("vos") is not None:
        m["vos"] = sc["vos"]
    m["vout_dc"] = sc.get("vout_dc")
    dm = r.vectors.get("ac_dm.txt")
    if dm is not None and dm.ndim == 2 and dm.shape[1] >= 3 and len(dm) > 10:
        f, re_, im_ = dm[:, 0], dm[:, 1], dm[:, 2]
        acm = ac_metrics(f, re_, im_)
        m["gain_db"], m["ugbw"], m["pm"], m["gm_db"], m["f3db"] = (acm["gain_db"], acm["ugbw"], acm["pm"],
                                                                    acm["gm_db"], acm["f3db"])
        m["_inverting"] = acm["inverting"]
        adm = mag_at(f, re_, im_, 1.0)
        cm = r.vectors.get("ac_cm.txt")
        if cm is not None and cm.ndim == 2 and len(cm) > 2:
            acmv = mag_at(cm[:, 0], cm[:, 1], cm[:, 2], 1.0)
            m["cmrr_db"] = float(20 * np.log10(adm / max(acmv, 1e-30)))
        ps = r.vectors.get("ac_ps.txt")
        if ps is not None and ps.ndim == 2 and len(ps) > 2:
            apsv = mag_at(ps[:, 0], ps[:, 1], ps[:, 2], 1.0)
            m["psrr_db"] = float(20 * np.log10(adm / max(apsv, 1e-30)))
    nz = r.vectors.get("noise.txt")
    if nz is not None and nz.ndim == 2 and len(nz) > 3:
        m["noise_1k"] = float(10 ** np.interp(3.0, np.log10(nz[:, 0]), np.log10(np.maximum(nz[:, 1], 1e-30))))
    tr = r.vectors.get("tran.txt")
    if tr is not None and tr.ndim == 2 and len(tr) > 20:
        t, v = tr[:, 0], tr[:, 1]
        a = p.get("step", 0.4) / 2
        sel1 = t < 5e-6
        sr_r, ts_r = slew_settle(t[sel1], v[sel1], vcm - a, vcm + a, 1e-6)
        # falling edge mirrored about vcm so it looks like a rising step
        sr_f, ts_f = slew_settle(t, (2 * vcm) - v, vcm - a, vcm + a, 5e-6)
        m["slew"] = min(sr_r, sr_f) if (sr_r is not None and sr_f is not None) else None
        tss = [ts_r, ts_f]
        m["settle"] = max(tss) if all(x is not None for x in tss) else None
    dc = r.vectors.get("dc.txt")
    if dc is not None and dc.ndim == 2 and len(dc) > 10:
        lo, hi = swing_from_dc(dc[:, 0], dc[:, 1])
        if lo is not None:
            m["swing_lo"], m["swing_hi"] = lo, hi
            m["swing"] = hi - lo
    # device op points
    ops = {}
    for k, v in sc.items():
        if k.startswith("op:"):
            _, dn, q = k.split(":")
            ops.setdefault(dn, {})[q] = v
    m["_ops"] = ops
    return m
