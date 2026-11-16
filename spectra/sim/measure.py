"""Post-processing helpers for AC / DC / transient vectors."""
from __future__ import annotations

import math
import numpy as np


def ac_metrics(f, re, im):
    """Gain/UGBW/PM/GM from a complex transfer H(f) (non-inverting convention)."""
    h = re + 1j * im
    mag = np.abs(h)
    mag_db = 20 * np.log10(np.maximum(mag, 1e-30))
    ph = np.degrees(np.unwrap(np.angle(h)))
    # normalise so that low-frequency phase is near 0 (non-inverting) or 180 (inverting)
    ph0 = ph[0]
    k = round(ph0 / 360.0)
    ph = ph - 360.0 * k
    out = {"gain_db": float(mag_db[0]), "ugbw": None, "pm": None, "gm_db": None, "f3db": None,
           "inverting": bool(abs(ph[0]) > 90)}
    # -3 dB bandwidth
    idx = np.where(mag_db < mag_db[0] - 3.0)[0]
    if len(idx):
        i = idx[0]
        if i > 0:
            out["f3db"] = float(_interp_log(f, mag_db, i, mag_db[0] - 3.0))
    if mag_db[0] > 0:
        idx = np.where(mag_db < 0)[0]
        if len(idx) and idx[0] > 0:
            i = idx[0]
            fu = _interp_log(f, mag_db, i, 0.0)
            out["ugbw"] = float(fu)
            phu = float(np.interp(math.log10(fu), np.log10(f[i - 1:i + 1]), ph[i - 1:i + 1]))
            ref = 180.0 if out["inverting"] else 0.0
            # phase margin = 180 - (phase lag relative to low-frequency phase)
            lag = (ph[0] - phu) if not out["inverting"] else (ph[0] - phu)
            out["pm"] = float(180.0 - lag)
        # gain margin: magnitude where lag reaches 180
        lag_arr = ph[0] - ph
        j = np.where(lag_arr >= 180.0)[0]
        if len(j) and j[0] > 0:
            g180 = float(np.interp(180.0, lag_arr[j[0] - 1:j[0] + 1], mag_db[j[0] - 1:j[0] + 1]))
            out["gm_db"] = float(-g180)
        else:
            out["gm_db"] = 99.0
    return out


def _interp_log(f, y, i, target):
    x0, x1 = math.log10(f[i - 1]), math.log10(f[i])
    y0, y1 = y[i - 1], y[i]
    if y1 == y0:
        return 10 ** x1
    return 10 ** (x0 + (target - y0) * (x1 - x0) / (y1 - y0))


def mag_at(f, re, im, f0):
    h = np.abs(re + 1j * im)
    return float(10 ** np.interp(math.log10(f0), np.log10(f), np.log10(np.maximum(h, 1e-30))))


def slew_settle(t, v, vlo, vhi, t_edge, tol=0.01, rising=True):
    """Slew rate (V/s, 10-90%) and settling time (s) to `tol` of step after t_edge."""
    sel = t >= t_edge
    tt, vv = t[sel], v[sel]
    if len(tt) < 5:
        return None, None
    step = vhi - vlo
    if not rising:
        vv = vlo + vhi - vv   # mirror so it looks rising
    a, b = vlo + 0.1 * step, vlo + 0.9 * step
    ta, tb = _cross(tt, vv, a), _cross(tt, vv, b)
    sr = (0.8 * step) / max(tb - ta, 1e-15) if (ta is not None and tb is not None) else None
    final = float(np.mean(vv[int(len(vv) * 0.9):]))      # settle to the actual final value
    err = np.abs(vv - final) > tol * abs(step)
    if err[-1]:
        ts = None
    else:
        last = np.where(err)[0]
        ts = float(tt[last[-1] + 1] - t_edge) if len(last) else 0.0
    return (float(sr) if sr is not None else None), ts


def _cross(t, v, level):
    idx = np.where(v >= level)[0]
    if not len(idx):
        return None
    i = idx[0]
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (level - v[i - 1]) * (t[i] - t[i - 1]) / max(v[i] - v[i - 1], 1e-18))


def swing_from_dc(vin, vout, frac=0.9):
    """Output range where incremental gain stays >= frac * centre gain."""
    g = np.gradient(vout, vin)
    c = len(g) // 2
    gc = abs(g[c])
    if gc <= 0:
        return None, None
    ok = np.abs(g) >= frac * gc
    # contiguous region around centre
    lo = c
    while lo > 0 and ok[lo - 1]:
        lo -= 1
    hi = c
    while hi < len(g) - 1 and ok[hi + 1]:
        hi += 1
    return float(min(vout[lo], vout[hi])), float(max(vout[lo], vout[hi]))
