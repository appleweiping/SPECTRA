"""Generate gm/Id lookup tables for sky130 1.8V nfet/pfet with ngspice.

Arrays are indexed [L, VDS, VSB, VGS] at a reference finger width W_REF.
All quantities are reported with positive sign conventions (|VGS|, |VDS|, |Id|).
"""
import itertools, sys, time
import numpy as np
from spectra.sim import ngspice as ng
from spectra.paths import NMOS, PMOS, LUT_DIR

W_REF = 5.0
LS = [0.15, 0.18, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
VDS = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.9, 1.2, 1.5, 1.8]
VSB = [0.0, 0.2, 0.4, 0.6, 0.8]
VGS_STEP = 0.01
PARAMS = ["id", "gm", "gds", "gmbs", "vth", "vdsat", "cgg", "cgs", "cgd", "cdd"]


def netlist(dev, L, vds, vsb, corner="tt", temp=27):
    name = NMOS if dev == "n" else PMOS
    p = f"@m.xm1.m{name}"
    saves = " ".join(f"{p}[{k}]" for k in PARAMS)
    if dev == "n":
        body = f"""XM1 d g s b {name} W={W_REF} L={L} nf=1
Vd d 0 {vds+vsb}
Vg g 0 0
Vs s 0 {vsb}
Vb b 0 0
"""
        sweep = f"dc Vg {vsb} {vsb+1.8+1e-9} {VGS_STEP}"
    else:
        # pmos: source at 1.8+vsb rail referenced, sweep gate downward
        vs = 2.6
        body = f"""XM1 d g s b {name} W={W_REF} L={L} nf=1
Vs s 0 {vs}
Vb b 0 {vs+vsb}
Vd d 0 {vs-vds}
Vg g 0 {vs}
"""
        sweep = f"dc Vg {vs} {vs-1.8-1e-9} {-VGS_STEP}"
    return f"""* lut
{ng.lib_line(corner)}
.temp {temp}
{body}
.control
save {saves}
{sweep}
wrdata out.txt {saves}
.endc
.end
"""


def gen(dev, corner="tt", temp=27):
    jobs = list(itertools.product(range(len(LS)), range(len(VDS)), range(len(VSB))))
    nets = [netlist(dev, LS[i], VDS[j], VSB[k], corner, temp) for i, j, k in jobs]
    t0 = time.time()
    res = ng.run_many(nets, wrdata_files=("out.txt",), timeout=120)
    nvgs = int(round(1.8 / VGS_STEP)) + 1
    data = {k: np.full((len(LS), len(VDS), len(VSB), nvgs), np.nan) for k in PARAMS}
    for (i, j, k), r in zip(jobs, res):
        arr = r.vectors.get("out.txt")
        if arr is None:
            print("FAIL", dev, LS[i], VDS[j], VSB[k], r.error[:300]); continue
        # wrdata writes pairs (sweep, value) for each vector
        for pi, pname in enumerate(PARAMS):
            col = arr[:, 2 * pi + 1][:nvgs]
            data[pname][i, j, k, :len(col)] = np.abs(col)
    vgs = np.arange(nvgs) * VGS_STEP
    out = LUT_DIR / f"sky130_{dev}fet_{corner}_{temp}.npz"
    np.savez_compressed(out, L=np.array(LS), VDS=np.array(VDS), VSB=np.array(VSB), VGS=vgs,
                        W_REF=W_REF, **data)
    print(f"{dev} {corner} {temp}C: {len(jobs)} sweeps in {time.time()-t0:.1f}s -> {out}")


if __name__ == "__main__":
    corners = sys.argv[1:] or ["tt"]
    for c in corners:
        for dev in ["n", "p"]:
            gen(dev, c)
