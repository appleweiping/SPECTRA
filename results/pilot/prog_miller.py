PARAMS = {
    "gmid1": (14.0, 6, 20), "L1": (0.5, 0.15, 2), "Itail": (30e-6, 4e-6, 300e-6),
    "gmid3": (9.0, 5, 15), "L3": (0.5, 0.15, 2), "gmid7": (10.0, 5, 16), "L7": (0.4, 0.15, 2),
    "I7": (80e-6, 5e-6, 800e-6), "Cc": (1e-12, 0.1e-12, 10e-12), "Lb": (1.0, 0.3, 4),
}
def design(p, lut, spec):
    VDD = 1.8
    m1 = lut.size("n", p["gmid1"], p["L1"], p["Itail"] / 2, vds=0.5, vsb=0.25)
    m3 = lut.size("p", p["gmid3"], p["L3"], p["Itail"] / 2, vds=1.0)
    m5 = lut.size("n", 8, p["Lb"], p["Itail"], vds=0.25)
    m6 = lut.size("n", 8, p["Lb"], spec.get("iref", 10e-6), vds=0.6)
    m7 = lut.size("p", p["gmid7"], p["L7"], p["I7"], vds=0.9)
    m8 = lut.size("n", 8, p["Lb"], p["I7"], vds=0.9)
    n = Netlist("vinp vinn vout vdd vss ibias")
    n.dev("M1", "a", "vinn", "t", "vss", m1); n.dev("M2", "b", "vinp", "t", "vss", m1)
    n.dev("M3", "a", "a", "vdd", "vdd", m3); n.dev("M4", "b", "a", "vdd", "vdd", m3)
    n.dev("M5", "t", "ibias", "vss", "vss", m5); n.dev("M6", "ibias", "ibias", "vss", "vss", m6)
    n.dev("M7", "vout", "b", "vdd", "vdd", m7); n.dev("M8", "vout", "ibias", "vss", "vss", m8)
    Rz = 1.2 / m7.gm
    n.R("Rz", "b", "z", Rz); n.C("Cc", "z", "vout", p["Cc"])
    a1 = m1.gm / (m1.gds + m3.gds); a2 = m7.gm / (m7.gds + m8.gds)
    CL = spec.get("cl", 2e-12)
    gbw = m1.gm / (2 * PI * p["Cc"]); p2 = m7.gm / (2 * PI * (CL + m7.cgg * 0.2))
    pm = 90 - math.degrees(math.atan(gbw / p2))
    return n, {"gain_db": db(a1 * a2), "ugbw": gbw, "pm": pm, "power": VDD * (p["Itail"] + p["I7"] + spec.get("iref", 10e-6))}
