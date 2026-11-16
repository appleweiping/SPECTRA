"""Helper API available inside SPECTRA design-intent programs.

A design program defines:
    PARAMS = {"name": (init, lo, hi), ...}      # intent variables (gm/Id, L, currents, C, R, ratios ...)
    def design(p, lut, spec): -> (Netlist, predicted_metrics_dict)
Inside design(), size transistors from intent with lut.size(...) and add elements to a Netlist.
"""
from __future__ import annotations

import math

from ..sim import lut as _lut


class Netlist:
    def __init__(self, ports: str | list):
        self.ports = ports.split() if isinstance(ports, str) else list(ports)
        self.lines = []
        self.devices = {}

    def M(self, name, d, g, s, b, kind, W, L, m=1):
        kind = {"n": "nfet", "p": "pfet", "nmos": "nfet", "pmos": "pfet"}.get(kind, kind)
        W = max(0.42, float(W)); L = max(0.15, float(L))
        self.lines.append(f"{name} {d} {g} {s} {b} {kind} W={W:.4g} L={L:.4g} m={int(m)}")
        self.devices[name] = (kind, W, L, int(m))
        return self

    def dev(self, name, d, g, s, b, op, m=1):
        """Add a transistor sized by a DevOP returned from lut.size()."""
        return self.M(name, d, g, s, b, "nfet" if op.dev == "n" else "pfet", op.W / m, op.L, m)

    def Q(self, name, c, b, e, m=1):
        self.lines.append(f"{name} {c} {b} {e} pnp m={int(m)}"); return self

    def R(self, name, a, b, val):
        self.lines.append(f"{name} {a} {b} {float(val):.6g}"); return self

    def C(self, name, a, b, val):
        self.lines.append(f"{name} {a} {b} {float(val):.6g}"); return self

    def text(self):
        return ".subckt dut " + " ".join(self.ports) + "\n" + "\n".join(self.lines) + "\n.ends"


class LUT:
    """Thin facade exposed to programs as `lut`."""

    def __init__(self, corner="tt", temp=27):
        self.corner, self.temp = corner, temp

    def size(self, dev, gm_id, L, Id, vds=0.6, vsb=0.0):
        """dev 'n'|'p'; returns DevOP with W [um], vgs, vth, vdsat, gm, gds, cgg, cgd, cdd, ft, intrinsic_gain."""
        return _lut.size(dev, gm_id, L, Id, vds, vsb, self.corner, self.temp)

    def op(self, dev, W, L, vgs, vds, vsb=0.0):
        return _lut.op_at(dev, W, L, vgs, vds, vsb, self.corner, self.temp)

    def table(self, dev, L, vds=0.6, vsb=0.0):
        return _lut.table(dev, L, vds, vsb)


def par(*rs):
    return 1.0 / sum(1.0 / r for r in rs)


def db(x):
    return 20 * math.log10(max(abs(x), 1e-30))


PI = math.pi
UT = 0.02585
