"""Expert parametric reference templates (topology fixed, sizes free).

Each template: VARS (list[Var]) and build(x) -> canonical netlist text.
Used to (a) certify feasibility of benchmark specs, (b) the expert-topology
optimizer baseline. Units: W, L in um; R in ohm; C in F; ratios dimensionless.
"""
from __future__ import annotations

from ..opt.sizing import Var

T = {}


def reg(name, family, vars_, doc=""):
    def deco(fn):
        T[name] = {"family": family, "vars": vars_, "build": fn, "doc": doc}
        return fn
    return deco


def _w(x, k):
    return max(0.42, x[k])


# ------------------------------------------------------------ op-amps
@reg("ota5t", "opamp", [Var("W1", 0.5, 100), Var("L1", 0.15, 4), Var("W3", 0.5, 100), Var("L3", 0.15, 4),
                        Var("W5", 0.5, 100), Var("L5", 0.15, 4), Var("k5", 0.5, 20)],
     "5-transistor OTA (NMOS input pair, PMOS mirror load), NMOS tail mirrored from ibias")
def ota5t(x):
    w6 = x["W5"] / x["k5"]
    return f""".subckt dut vinp vinn vout vdd vss ibias
M1 a vinn t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 vout vinp t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M3 a a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M4 vout a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M5 t ibias vss vss nfet W={x['W5']:.3f} L={x['L5']:.3f}
M6 ibias ibias vss vss nfet W={max(0.42, w6):.3f} L={x['L5']:.3f}
.ends"""


@reg("miller2", "opamp", [Var("W1", 0.5, 100), Var("L1", 0.15, 4), Var("W3", 0.5, 100), Var("L3", 0.15, 4),
                          Var("W5", 0.5, 100), Var("L5", 0.15, 4), Var("k5", 0.5, 20), Var("W7", 1, 400),
                          Var("L7", 0.15, 2), Var("k8", 0.5, 80), Var("Cc", 0.05e-12, 10e-12), Var("Rz", 10, 50e3)],
     "two-stage Miller op-amp, NMOS input, PMOS CS second stage, nulling resistor")
def miller2(x):
    w6 = x["W5"] / x["k5"]
    return f""".subckt dut vinp vinn vout vdd vss ibias
M1 a vinn t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 b vinp t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M3 a a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M4 b a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M5 t ibias vss vss nfet W={x['W5']:.3f} L={x['L5']:.3f}
M6 ibias ibias vss vss nfet W={max(0.42, w6):.3f} L={x['L5']:.3f}
M7 vout b vdd vdd pfet W={x['W7']:.3f} L={x['L7']:.3f}
M8 vout ibias vss vss nfet W={max(0.42, w6 * x['k8']):.3f} L={x['L5']:.3f}
Rz b z {x['Rz']:.1f}
Cc z vout {x['Cc']:.4g}
.ends"""


@reg("fcasc", "opamp", [Var("W1", 1, 200), Var("L1", 0.15, 2), Var("Wp", 1, 300), Var("Lp", 0.15, 2),
                        Var("Wc", 1, 200), Var("Lc", 0.15, 2), Var("Wn", 1, 200), Var("Ln", 0.15, 3),
                        Var("kt", 1, 40), Var("kp", 1, 80), Var("Rb", 1e3, 200e3)],
     "folded-cascode OTA: NMOS input pair, PMOS current sources, PMOS/NMOS cascodes, wide-swing cascode mirror; cascode biases from resistor-shifted diode stacks")
def fcasc(x):
    wb = 2.0
    return f""".subckt dut vinp vinn vout vdd vss ibias
* input pair and tail
M1 f1 vinn t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 f2 vinp t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M5 t ibias vss vss nfet W={wb * x['kt']:.3f} L=1
M0 ibias ibias vss vss nfet W={wb:.3f} L=1
* PMOS current sources (top)
M3 f1 pb vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
M4 f2 pb vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
* PMOS cascodes
M6 c1 pc f1 vdd pfet W={x['Wc']:.3f} L={x['Lc']:.3f}
M7 vout pc f2 vdd pfet W={x['Wc']:.3f} L={x['Lc']:.3f}
* NMOS cascode mirror (wide swing)
M8 c1 nc s1 vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
M9 vout nc s2 vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
M10 s1 c1 vss vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
M11 s2 c1 vss vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
* bias: pb from mirrored current through diode pfet; pc = pb - Ib*Rb ; nc = diode + Rb
Mb1 pbd ibias vss vss nfet W={wb * x['kp']:.3f} L=1
Mb2 pbd pb vdd vdd pfet W={x['Wp'] * 0.25:.3f} L={x['Lp']:.3f}
Rpb pb pbd 1
Mb3 pc ibias vss vss nfet W={wb:.3f} L=1
Mb4 pcx pcx vdd vdd pfet W={x['Wp'] * 0.1:.3f} L={x['Lp']:.3f}
Rpc pcx pc {x['Rb']:.1f}
Mb5 ncd ncd vss vss nfet W={x['Wn'] * 0.2:.3f} L={x['Ln']:.3f}
Rnc nc ncd {x['Rb']:.1f}
Mb6 nc pb vdd vdd pfet W={x['Wp'] * 0.05:.3f} L={x['Lp']:.3f}
.ends"""


# ------------------------------------------------------------ fixed op-amp core used inside op-amp applications
OPAMP_CORE = """M1 oa_a {n} oa_t vss nfet W=21.3 L=0.52
M2 oa_b {p} oa_t vss nfet W=21.3 L=0.52
M3 oa_a oa_a vdd vdd pfet W=26.3 L=0.32
M4 oa_b oa_a vdd vdd pfet W=26.3 L=0.32
M5 oa_t ibias vss vss nfet W=2.02 L=2.34
M6 ibias ibias vss vss nfet W=0.49 L=2.34
M7 {o} oa_b vdd vdd pfet W={w7:.2f} L=0.43
M8 {o} ibias vss vss nfet W={w8:.2f} L=2.34
Rz oa_b oa_z 930
Cc oa_z {o} {cc:.4g}"""


def opamp_core(n, p, o, x):
    return OPAMP_CORE.format(n=n, p=p, o=o, w7=65.7 * x.get("ko", 1.0), w8=5.4 * x.get("ko", 1.0), cc=x.get("Cc", 0.5e-12))


# ------------------------------------------------------------ amplifiers
@reg("cs_pload", "amp", [Var("W1", 0.5, 100), Var("L1", 0.15, 4), Var("W2", 0.5, 100), Var("L2", 0.15, 4),
                         Var("kb", 0.2, 20)],
     "NMOS common-source with PMOS current-source load biased by a mirror from ibias")
def cs_pload(x):
    return f""".subckt dut vin vout vdd vss ibias
M1 vout vin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 vout pb vdd vdd pfet W={x['W2']:.3f} L={x['L2']:.3f}
M3 pb pb vdd vdd pfet W={max(0.42, x['W2'] / x['kb']):.3f} L={x['L2']:.3f}
M4 pb ibias vss vss nfet W=2 L=1
M5 ibias ibias vss vss nfet W=2 L=1
.ends"""


@reg("cs_diode", "amp", [Var("W1", 0.5, 100), Var("L1", 0.15, 4), Var("W2", 0.5, 100), Var("L2", 0.15, 4)],
     "NMOS common-source with diode-connected PMOS load")
def cs_diode(x):
    return f""".subckt dut vin vout vdd vss ibias
M1 vout vin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 vout vout vdd vdd pfet W={x['W2']:.3f} L={x['L2']:.3f}
.ends"""


@reg("casc_amp", "amp", [Var("W1", 0.5, 100), Var("L1", 0.15, 4), Var("W2", 0.5, 100), Var("L2", 0.15, 4),
                         Var("Wc", 0.5, 100), Var("Lc", 0.15, 2), Var("kb", 0.2, 20), Var("Rn", 1e3, 300e3),
                         Var("Rp", 1e3, 300e3)],
     "telescopic cascode CS amplifier: NMOS input + NMOS cascode, PMOS cascode current-source load")
def casc_amp(x):
    return f""".subckt dut vin vout vdd vss ibias
M1 s1 vin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 vout nc s1 vss nfet W={x['Wc']:.3f} L={x['Lc']:.3f}
M3 vout pc s3 vdd pfet W={x['Wc'] * 2:.3f} L={x['Lc']:.3f}
M4 s3 pb vdd vdd pfet W={x['W2']:.3f} L={x['L2']:.3f}
M5 pbx pb vdd vdd pfet W={max(0.42, x['W2'] / x['kb']):.3f} L={x['L2']:.3f}
Rp pbx pb 1
Rpc pc pcd {x['Rp']:.1f}
M6 pbx ibias vss vss nfet W=2 L=1
M7 pcd ibias vss vss nfet W=2 L=1
M8 pcd2 pcd2 vdd vdd pfet W=1 L=1
Rpc2 pcd2 pc 1
M9 ibias ibias vss vss nfet W=2 L=1
M10 nc nc nd vss nfet W=2 L=0.5
Rn nd vss {x['Rn']:.1f}
M11 nc pb vdd vdd pfet W={max(0.42, x['W2'] / x['kb']):.3f} L={x['L2']:.3f}
.ends"""


@reg("sf", "amp", [Var("W1", 0.5, 200), Var("L1", 0.15, 2), Var("Wb", 0.5, 100), Var("Lb", 0.15, 4), Var("kb", 0.2, 50)],
     "NMOS source follower with NMOS current-sink bias mirrored from ibias")
def sf(x):
    return f""".subckt dut vin vout vdd vss ibias
M1 vdd vin vout vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 vout ibias vss vss nfet W={x['Wb']:.3f} L={x['Lb']:.3f}
M3 ibias ibias vss vss nfet W={max(0.42, x['Wb'] / x['kb']):.3f} L={x['Lb']:.3f}
.ends"""


# ------------------------------------------------------------ TIA
@reg("tia_sfb", "tia", [Var("W1", 0.5, 100), Var("L1", 0.15, 2), Var("W2", 0.5, 100), Var("L2", 0.15, 2),
                        Var("kb", 0.2, 20), Var("Wsf", 0.5, 100), Var("ksf", 0.2, 20), Var("Rf", 500, 500e3)],
     "shunt-feedback TIA: CS gain stage (PMOS current-source load) + NMOS source follower, feedback resistor Rf")
def tia_sfb(x):
    return f""".subckt dut iin vout vdd vss ibias
M1 a iin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 a pb vdd vdd pfet W={x['W2']:.3f} L={x['L2']:.3f}
M3 pb pb vdd vdd pfet W={max(0.42, x['W2'] / x['kb']):.3f} L={x['L2']:.3f}
M4 pb ibias vss vss nfet W=2 L=1
M5 vdd a vout vss nfet W={x['Wsf']:.3f} L=0.15
M6 vout ibias vss vss nfet W={2 * x['ksf']:.3f} L=1
M7 ibias ibias vss vss nfet W=2 L=1
Rf iin vout {x['Rf']:.1f}
.ends"""


# ------------------------------------------------------------ current mirrors
@reg("cm_simple", "cmirror", [Var("W1", 0.5, 100), Var("L1", 0.15, 8), Var("k", 0.1, 20)],
     "simple NMOS current mirror, ratio k")
def cm_simple(x):
    return f""".subckt dut iin iout vdd vss
M1 iin iin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 iout iin vss vss nfet W={max(0.42, x['W1'] * x['k']):.3f} L={x['L1']:.3f}
.ends"""


@reg("cm_casc", "cmirror", [Var("W1", 0.5, 100), Var("L1", 0.15, 8), Var("W3", 0.5, 100), Var("L3", 0.15, 4),
                            Var("k", 0.1, 20)],
     "stacked (diode-diode) NMOS cascode current mirror")
def cm_casc(x):
    return f""".subckt dut iin iout vdd vss
M3 iin iin m vss nfet W={x['W3']:.3f} L={x['L3']:.3f}
M1 m m vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M4 iout iin o vss nfet W={max(0.42, x['W3'] * x['k']):.3f} L={x['L3']:.3f}
M2 o m vss vss nfet W={max(0.42, x['W1'] * x['k']):.3f} L={x['L1']:.3f}
.ends"""


@reg("cm_wide", "cmirror", [Var("W1", 0.5, 100), Var("L1", 0.15, 8), Var("W3", 0.5, 100), Var("L3", 0.15, 4),
                            Var("k", 0.1, 20), Var("R", 1e3, 200e3)],
     "self-biased wide-swing (low-voltage) NMOS cascode mirror with series resistor")
def cm_wide(x):
    return f""".subckt dut iin iout vdd vss
R1 iin b {x['R']:.1f}
M3 b iin m vss nfet W={x['W3']:.3f} L={x['L3']:.3f}
M1 m b vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M4 iout iin o vss nfet W={max(0.42, x['W3'] * x['k']):.3f} L={x['L3']:.3f}
M2 o b vss vss nfet W={max(0.42, x['W1'] * x['k']):.3f} L={x['L1']:.3f}
.ends"""


@reg("cm_psrc", "cmirror", [Var("W1", 0.5, 100), Var("L1", 0.15, 8), Var("Wp", 0.5, 200), Var("Lp", 0.15, 8),
                            Var("k", 0.1, 20)],
     "current source: NMOS input diode, NMOS mirror into a PMOS diode, PMOS output mirror (ratio k)")
def cm_psrc(x):
    return f""".subckt dut iin iout vdd vss
M1 iin iin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 pd iin vss vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M3 pd pd vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
M4 iout pd vdd vdd pfet W={max(0.42, x['Wp'] * x['k']):.3f} L={x['Lp']:.3f}
.ends"""


# ------------------------------------------------------------ LDO
@reg("ldo_pmos", "ldo", [Var("W1", 0.5, 50), Var("L1", 0.15, 2), Var("W3", 0.5, 50), Var("L3", 0.15, 2),
                         Var("kt", 0.5, 20), Var("Wpass", 50, 4000), Var("Lpass", 0.15, 0.5),
                         Var("Rtot", 20e3, 2e6), Var("Cc", 0.05e-12, 20e-12)],
     "PMOS-pass LDO: 5T OTA error amplifier, resistive feedback divider, Miller compensation gate->vout")
def ldo_pmos(x, vout_target=1.2, vref=0.6):
    r2 = x["Rtot"] * vref / vout_target
    r1 = x["Rtot"] - r2
    return f""".subckt dut vin vout vref vss ibias
M1 a fb t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 g vref t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M3 a a vin vin pfet W={x['W3']:.3f} L={x['L3']:.3f}
M4 g a vin vin pfet W={x['W3']:.3f} L={x['L3']:.3f}
M5 t ibias vss vss nfet W={2 * x['kt']:.3f} L=1
M6 ibias ibias vss vss nfet W=2 L=1
Mp vout g vin vin pfet W={x['Wpass']:.2f} L={x['Lpass']:.3f}
R1 vout fb {r1:.1f}
R2 fb vss {r2:.1f}
Cc g vout {x['Cc']:.4g}
.ends"""


# ------------------------------------------------------------ bandgap
@reg("bgr", "ref", [Var("Wp", 0.5, 50), Var("Lp", 0.5, 8), Var("Wn", 0.5, 50), Var("Ln", 0.5, 8),
                    Var("N", 2, 24, log=False, integer=True), Var("R1", 1e3, 500e3), Var("R2", 1e3, 2e6)],
     "op-amp-less CMOS bandgap: PTAT current dVeb/R1 from PNP pair (1:N) with NMOS level-matching and PMOS mirror; output Veb + I*R2; startup")
def bgr(x):
    return f""".subckt dut vdd vref vss
M4 a g vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
M3 g g vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
M5 vref g vdd vdd pfet W={x['Wp']:.3f} L={x['Lp']:.3f}
M1 a a e1 vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
M2 g a r vss nfet W={x['Wn']:.3f} L={x['Ln']:.3f}
R1 r e2 {x['R1']:.1f}
Q1 vss vss e1 pnp m=1
Q2 vss vss e2 pnp m={int(x['N'])}
R2 vref e3 {x['R2']:.1f}
Q3 vss vss e3 pnp m=1
Mst1 st vss vdd vdd pfet W=0.5 L=8
Mst2 st vref vss vss nfet W=2 L=0.5
Mst3 g st vss vss nfet W=0.5 L=1
.ends"""


# ------------------------------------------------------------ comparators
@reg("comp2", "comparator", [Var("W1", 0.5, 50), Var("L1", 0.15, 1), Var("W3", 0.5, 50), Var("L3", 0.15, 1),
                             Var("kt", 0.5, 20), Var("W7", 0.5, 100), Var("k8", 0.5, 40), Var("Wi", 0.42, 20)],
     "continuous-time comparator: 5T OTA preamp + PMOS CS gain stage + output inverter")
def comp2(x):
    return f""".subckt dut vinp vinn vout vdd vss ibias
M1 a vinp t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M2 b vinn t vss nfet W={x['W1']:.3f} L={x['L1']:.3f}
M3 a a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M4 b a vdd vdd pfet W={x['W3']:.3f} L={x['L3']:.3f}
M5 t ibias vss vss nfet W={x['kt'] * 1:.3f} L=0.5
M6 ibias ibias vss vss nfet W=1 L=0.5
M7 c b vdd vdd pfet W={x['W7']:.3f} L=0.15
M8 c ibias vss vss nfet W={max(0.42, x['k8']):.3f} L=0.5
M9 vout c vdd vdd pfet W={2 * x['Wi']:.3f} L=0.15
M10 vout c vss vss nfet W={x['Wi']:.3f} L=0.15
.ends"""


@reg("strongarm", "latch", [Var("Wt", 0.5, 40), Var("W1", 0.5, 40), Var("Wn", 0.42, 20), Var("Wp", 0.42, 20),
                            Var("Wr", 0.42, 10), Var("Wi", 0.42, 10)],
     "StrongARM latch with reset PMOS and output inverters")
def strongarm(x):
    return f""".subckt dut vinp vinn clk outp outn vdd vss
Mt t clk vss vss nfet W={x['Wt']:.3f} L=0.15
M1 xn vinp t vss nfet W={x['W1']:.3f} L=0.15
M2 xp vinn t vss nfet W={x['W1']:.3f} L=0.15
M3 on op xn vss nfet W={x['Wn']:.3f} L=0.15
M4 op on xp vss nfet W={x['Wn']:.3f} L=0.15
M5 on op vdd vdd pfet W={x['Wp']:.3f} L=0.15
M6 op on vdd vdd pfet W={x['Wp']:.3f} L=0.15
M7 on clk vdd vdd pfet W={x['Wr']:.3f} L=0.15
M8 op clk vdd vdd pfet W={x['Wr']:.3f} L=0.15
M9 xn clk vdd vdd pfet W={x['Wr']:.3f} L=0.15
M10 xp clk vdd vdd pfet W={x['Wr']:.3f} L=0.15
Mi1 outp on vdd vdd pfet W={2 * x['Wi']:.3f} L=0.15
Mi2 outp on vss vss nfet W={x['Wi']:.3f} L=0.15
Mi3 outn op vdd vdd pfet W={2 * x['Wi']:.3f} L=0.15
Mi4 outn op vss vss nfet W={x['Wi']:.3f} L=0.15
.ends"""


# ------------------------------------------------------------ VCO
def _csring(x, n):
    lines = []
    nodes = [f"n{i}" for i in range(n - 1)] + ["vout"]
    for i in range(n):
        inp = nodes[i - 1] if i > 0 else "vout"
        out = nodes[i]
        lines.append(f"Mp{i} {out} {inp} sp{i} vdd pfet W={x['Wp']:.3f} L={x['L']:.3f}")
        lines.append(f"Mq{i} sp{i} pc vdd vdd pfet W={x['Wcp']:.3f} L=0.15")
        lines.append(f"Mn{i} {out} {inp} sn{i} vss nfet W={x['Wn']:.3f} L={x['L']:.3f}")
        lines.append(f"Mc{i} sn{i} vctrl vss vss nfet W={x['Wc']:.3f} L=0.15")
    lines.append(f"Mb1 pc vctrl vss vss nfet W={x['Wc']:.3f} L=0.15")
    lines.append(f"Mb2 pc pc vdd vdd pfet W={x['Wcp']:.3f} L=0.15")
    return ".subckt dut vctrl vout vdd vss\n" + "\n".join(lines) + "\n.ends"


for _n in (3, 5, 7):
    reg(f"csring{_n}", "vco", [Var("Wp", 0.42, 20), Var("Wn", 0.42, 20), Var("Wc", 0.42, 40), Var("Wcp", 0.42, 80),
                               Var("L", 0.15, 1)],
        f"{_n}-stage current-starved ring VCO, NMOS starving + mirrored PMOS starving")(lambda x, n=_n: _csring(x, n))


# ------------------------------------------------------------ filters (op-amp based)
@reg("sk_lpf2", "filter", [Var("R1", 1e3, 1e6), Var("R2", 1e3, 1e6), Var("C1", 0.1e-12, 100e-12),
                           Var("C2", 0.1e-12, 100e-12), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
     "2nd-order unity-gain Sallen-Key low-pass using a two-stage op-amp buffer")
def sk_lpf2(x):
    return (".subckt dut vin vout vdd vss ibias\n" + f"R1 vin a {x['R1']:.1f}\nR2 a b {x['R2']:.1f}\n"
            f"C1 a vout {x['C1']:.4g}\nC2 b vss {x['C2']:.4g}\n" + opamp_core("vout", "b", "vout", x) + "\n.ends")


@reg("sk_lpf3", "filter", [Var("R0", 1e3, 1e6), Var("C0", 0.1e-12, 100e-12), Var("R1", 1e3, 1e6), Var("R2", 1e3, 1e6),
                           Var("C1", 0.1e-12, 100e-12), Var("C2", 0.1e-12, 100e-12), Var("Cc", 0.1e-12, 5e-12)],
     "3rd-order low-pass: passive RC pole followed by unity-gain Sallen-Key stage")
def sk_lpf3(x):
    return (".subckt dut vin vout vdd vss ibias\n" + f"R0 vin p {x['R0']:.1f}\nC0 p vss {x['C0']:.4g}\n"
            f"R1 p a {x['R1']:.1f}\nR2 a b {x['R2']:.1f}\nC1 a vout {x['C1']:.4g}\nC2 b vss {x['C2']:.4g}\n"
            + opamp_core("vout", "b", "vout", x) + "\n.ends")


@reg("mfb_bpf", "filter", [Var("R1", 1e3, 1e6), Var("R2", 100, 1e6), Var("R3", 1e3, 5e6), Var("C1", 0.1e-12, 100e-12),
                           Var("C2", 0.1e-12, 100e-12), Var("Cc", 0.1e-12, 5e-12)],
     "multiple-feedback band-pass filter around a two-stage op-amp referenced to an internal VDD/2 divider")
def mfb_bpf(x):
    return (".subckt dut vin vout vdd vss ibias\n" + "Rd1 vdd vm 200k\nRd2 vm vss 200k\nCd vm vss 20p\n"
            f"R1 vin a {x['R1']:.1f}\nR2 a vm {x['R2']:.1f}\nC1 a vout {x['C1']:.4g}\nC2 a n {x['C2']:.4g}\n"
            f"R3 n vout {x['R3']:.1f}\n" + opamp_core("n", "vm", "vout", x) + "\n.ends")


# ------------------------------------------------------------ Schmitt
@reg("st6", "schmitt", [Var("Wn", 0.42, 20), Var("Wnf", 0.42, 20), Var("Wp", 0.42, 40), Var("Wpf", 0.42, 40),
                        Var("Wi", 0.42, 10)],
     "6-transistor CMOS Schmitt trigger with output inverter (non-inverting overall)")
def st6(x):
    return f""".subckt dut vin vout vdd vss
M1 a vin vss vss nfet W={x['Wn']:.3f} L=0.15
M2 x vin a vss nfet W={x['Wn']:.3f} L=0.15
M3 vdd x a vss nfet W={x['Wnf']:.3f} L=0.15
M4 b vin vdd vdd pfet W={x['Wp']:.3f} L=0.15
M5 x vin b vdd pfet W={x['Wp']:.3f} L=0.15
M6 vss x b vdd pfet W={x['Wpf']:.3f} L=0.15
M7 vout x vdd vdd pfet W={2 * x['Wi']:.3f} L=0.15
M8 vout x vss vss nfet W={x['Wi']:.3f} L=0.15
.ends"""


# ------------------------------------------------------------ op-amp applications
def _app(body, x):
    return ".subckt dut vin1 vin2 vout vcm vdd vss ibias\n" + body + "\n" + opamp_core("n", "vcm", "vout", x) + "\n.ends"


reg("app_inv", "opamp_app", [Var("R1", 1e3, 1e6), Var("Rf", 1e3, 1e7), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
    "inverting amplifier: vout-vcm = -(Rf/R1)(vin1-vcm); vin2 unused")(
    lambda x: _app(f"R1 vin1 n {x['R1']:.1f}\nRf n vout {x['Rf']:.1f}\nRx vin2 vcm 1meg", x))
reg("app_sum", "opamp_app", [Var("R1", 1e3, 1e6), Var("R2", 1e3, 1e6), Var("Rf", 1e3, 1e7), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
    "inverting summing amplifier")(
    lambda x: _app(f"R1 vin1 n {x['R1']:.1f}\nR2 vin2 n {x['R2']:.1f}\nRf n vout {x['Rf']:.1f}", x))
reg("app_integ", "opamp_app", [Var("R1", 1e3, 1e6), Var("Cf", 0.1e-12, 100e-12), Var("Rl", 1e5, 1e9), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
    "lossy inverting integrator with DC-stabilizing resistor")(
    lambda x: _app(f"R1 vin1 n {x['R1']:.1f}\nCf n vout {x['Cf']:.4g}\nRl n vout {x['Rl']:.1f}\nRx vin2 vcm 1meg", x))


def _diff(x):
    body = (f"R1 vin1 n {x['R1']:.1f}\nRf n vout {x['Rf']:.1f}\nR3 vin2 p {x['R1']:.1f}\nR4 p vcm {x['Rf']:.1f}")
    return ".subckt dut vin1 vin2 vout vcm vdd vss ibias\n" + body + "\n" + opamp_core("n", "p", "vout", x) + "\n.ends"


reg("app_diff", "opamp_app", [Var("R1", 1e3, 1e6), Var("Rf", 1e3, 1e7), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
    "difference amplifier: vout-vcm = (Rf/R1)(vin2-vin1)")(_diff)


def _noninv(x):
    body = f"Rg n vcm {x['Rg']:.1f}\nRf n vout {x['Rf']:.1f}\nRx vin2 vcm 1meg"
    return ".subckt dut vin1 vin2 vout vcm vdd vss ibias\n" + body + "\n" + opamp_core("n", "vin1", "vout", x) + "\n.ends"


reg("app_noninv", "opamp_app", [Var("Rg", 1e3, 1e6), Var("Rf", 1e3, 1e7), Var("Cc", 0.1e-12, 5e-12), Var("ko", 0.3, 3)],
    "non-inverting amplifier referenced to vcm")(_noninv)
