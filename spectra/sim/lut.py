"""gm/Id lookup-table API for SKY130 1.8 V devices.

The design-intent abstraction used by the agent: a transistor is described by
(type, gm/Id, L, Id, VDS, VSB) and the LUT returns width and small-signal
parameters. All values are positive-magnitude (|VGS|, |Id| ...).
"""
from __future__ import annotations

import functools
import math
from dataclasses import dataclass

import numpy as np

from ..paths import LUT_DIR

W_MIN, W_MAX_FINGER, L_MIN = 0.42, 5.0, 0.15


@functools.lru_cache(maxsize=16)
def _load(dev: str, corner: str = "tt", temp: int = 27):
    z = np.load(LUT_DIR / f"sky130_{dev}fet_{corner}_{temp}.npz")
    return {k: z[k] for k in z.files}


def _interp_axis(grid, x):
    grid = np.asarray(grid)
    x = float(np.clip(x, grid[0], grid[-1]))
    i = int(np.clip(np.searchsorted(grid, x) - 1, 0, len(grid) - 2))
    t = (x - grid[i]) / (grid[i + 1] - grid[i])
    return i, t


def _slice(dev, L, vds, vsb, corner="tt", temp=27):
    """Return dict of 1-D arrays over VGS, trilinearly interpolated in (L, VDS, VSB)."""
    d = _load(dev, corner, temp)
    # interpolate in log(L) for smoother behaviour
    li, lt = _interp_axis(np.log(d["L"]), math.log(max(L, L_MIN)))
    vi, vt = _interp_axis(d["VDS"], vds)
    si, st = _interp_axis(d["VSB"], vsb)
    out = {}
    for k in ["id", "gm", "gds", "gmbs", "vth", "vdsat", "cgg", "cgs", "cgd", "cdd"]:
        a = d[k]
        acc = 0.0
        for a_i, wa in ((li, 1 - lt), (li + 1, lt)):
            for b_i, wb in ((vi, 1 - vt), (vi + 1, vt)):
                for c_i, wc in ((si, 1 - st), (si + 1, st)):
                    w = wa * wb * wc
                    if w:
                        acc = acc + w * a[a_i, b_i, c_i, :]
        out[k] = acc
    out["vgs"] = d["VGS"]
    out["W_REF"] = float(d["W_REF"])
    return out


@dataclass
class DevOP:
    dev: str
    L: float
    W: float
    Id: float
    gm_id: float
    vgs: float
    vth: float
    vdsat: float
    gm: float
    gds: float
    gmbs: float
    cgg: float
    cgd: float
    cdd: float
    ft: float
    intrinsic_gain: float

    def as_dict(self):
        return {k: (float(f"{v:.4g}") if isinstance(v, float) else v) for k, v in self.__dict__.items()}


def size(dev: str, gm_id: float, L: float, Id: float, vds: float = 0.6, vsb: float = 0.0,
         corner="tt", temp=27) -> DevOP:
    """Size a transistor from design intent (gm/Id, L, Id) -> W and small-signal params."""
    s = _slice(dev, L, vds, vsb, corner, temp)
    idw = s["id"] / s["W_REF"]
    with np.errstate(divide="ignore", invalid="ignore"):
        gmid = s["gm"] / s["id"]
    # only consider the monotonic (above ~zero current) region
    valid = np.where((idw > 1e-9) & np.isfinite(gmid))[0]
    vgs_axis = s["vgs"][valid]
    g = gmid[valid]
    # gm/Id decreases with VGS; find VGS where gm/Id == target (search from strong inversion side)
    target = float(np.clip(gm_id, np.nanmin(g) + 1e-6, np.nanmax(g) - 1e-6))
    # use the branch after the peak (weak->strong inversion)
    pk = int(np.nanargmax(g))
    gb, vb = g[pk:], vgs_axis[pk:]
    j = int(np.clip(np.searchsorted(-gb, -target), 1, len(gb) - 1))
    t = (target - gb[j - 1]) / (gb[j] - gb[j - 1]) if gb[j] != gb[j - 1] else 0.0
    vgs = float(vb[j - 1] + t * (vb[j] - vb[j - 1]))

    def at(arr):
        return float(np.interp(vgs, s["vgs"], arr))

    idw_v = at(idw)
    W = Id / max(idw_v, 1e-15)
    scale = W / s["W_REF"]
    gm = at(s["gm"]) * scale
    gds = at(s["gds"]) * scale
    cgg = at(s["cgg"]) * scale
    return DevOP(dev=dev, L=L, W=W, Id=Id, gm_id=target, vgs=vgs, vth=at(s["vth"]),
                 vdsat=at(s["vdsat"]), gm=gm, gds=gds, gmbs=at(s["gmbs"]) * scale,
                 cgg=cgg, cgd=at(s["cgd"]) * scale, cdd=at(s["cdd"]) * scale,
                 ft=gm / (2 * math.pi * max(cgg, 1e-30)), intrinsic_gain=gm / max(gds, 1e-30))


def op_at(dev: str, W: float, L: float, vgs: float, vds: float, vsb: float = 0.0, corner="tt", temp=27):
    """Small-signal parameters of a device of width W at a given bias (forward model)."""
    s = _slice(dev, L, vds, vsb, corner, temp)
    scale = W / s["W_REF"]
    at = lambda arr: float(np.interp(vgs, s["vgs"], arr))
    Id = at(s["id"]) * scale
    gm = at(s["gm"]) * scale
    return {"Id": Id, "gm": gm, "gds": at(s["gds"]) * scale, "vth": at(s["vth"]),
            "vdsat": at(s["vdsat"]), "gm_id": gm / max(Id, 1e-30), "cgg": at(s["cgg"]) * scale}


def table(dev: str, L: float, vds: float = 0.6, vsb: float = 0.0, gm_ids=(5, 8, 10, 12, 15, 18, 20)):
    """Human/LLM readable characterization table for a device at length L."""
    rows = []
    for g in gm_ids:
        o = size(dev, g, L, 1e-6 * 10, vds, vsb)
        rows.append({"gm_id": round(o.gm_id, 2), "Id_per_W[uA/um]": round(o.Id / o.W * 1e6, 3),
                     "VGS": round(o.vgs, 3), "Vdsat": round(o.vdsat, 3), "gm/gds": round(o.intrinsic_gain, 1),
                     "fT[GHz]": round(o.ft / 1e9, 2)})
    return rows
