#!/usr/bin/env python3
"""Generate paper/figs/spectra_framework.{png,pdf} with 100% pure #FFFFFF background,
SLATE-Rec closed borders & crisp vector arrows, and no green checkmark."""
from __future__ import annotations

import math
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "paper" / "figs"


def erase_rect(arr: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> None:
    arr[max(0, y0):min(arr.shape[0], y1), max(0, x0):min(arr.shape[1], x1)] = 255


def erase_rrect_stroke(
    arr: np.ndarray, x0: float, y0: float, x1: float, y1: float, r: float = 14.0, tol: float = 4.0
) -> None:
    """Erase ONLY pixels within `tol` of the exact rounded-rectangle perimeter curve."""
    h, w, _ = arr.shape
    ix0 = max(0, int(math.floor(x0 - tol - 2)))
    iy0 = max(0, int(math.floor(y0 - tol - 2)))
    ix1 = min(w, int(math.ceil(x1 + tol + 3)))
    iy1 = min(h, int(math.ceil(y1 + tol + 3)))
    yy, xx = np.mgrid[iy0:iy1, ix0:ix1]
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    hx = max(1.0, 0.5 * (x1 - x0) - r)
    hy = max(1.0, 0.5 * (y1 - y0) - r)
    qx, qy = np.abs(xx - cx) - hx, np.abs(yy - cy) - hy
    sdf = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0)) + np.minimum(np.maximum(qx, qy), 0.0) - r
    sub = arr[iy0:iy1, ix0:ix1]
    sub[np.abs(sdf) <= tol] = 255


def build(src_png: Path, out_png: Path, out_pdf: Path) -> None:
    im = Image.open(src_png).convert("RGB")
    orig = np.array(im, dtype=np.uint8)
    arr = orig.copy()
    h, w, _ = arr.shape

    c3_patch = orig[221:294, 924:1339].copy()
    c3_patch[0:18, -8:] = 255
    c3_patch[-16:, -8:] = 255

    mosfet_patch = orig[521:590, 380:425].copy()
    title_patch = orig[324:353, 510:890].copy()

    # 1. Erase ALL old raster borders & arrows
    erase_rrect_stroke(arr, 27.0, 64.5, 1351.0, 316.0, r=18.0, tol=4.4)
    erase_rect(arr, 20, 353, 1358, 366)
    erase_rect(arr, 472, 348, 496, 369)
    erase_rect(arr, 20, 751, 1358, 762)
    erase_rect(arr, 20, 353, 33, 762)
    erase_rect(arr, 1339, 353, 1360, 762)
    erase_rect(arr, 910, 353, 925, 550)

    erase_rrect_stroke(arr, 333.5, 107.0, 533.5, 187.5, r=13.0, tol=4.0)
    erase_rrect_stroke(arr, 644.0, 107.0, 779.5, 185.5, r=13.0, tol=4.0)
    erase_rrect_stroke(arr, 912.0, 107.0, 1049.5, 185.5, r=13.0, tol=4.0)
    erase_rrect_stroke(arr, 1175.5, 107.0, 1307.5, 187.5, r=13.0, tol=4.0)

    erase_rect(arr, 206, 134, 336, 155)
    erase_rect(arr, 533, 134, 646, 155)
    erase_rect(arr, 779, 134, 914, 155)
    erase_rect(arr, 1049, 134, 1178, 155)

    erase_rrect_stroke(arr, 55.5, 214.0, 479.5, 300.0, r=14.0, tol=4.4)
    erase_rect(arr, 270, 189, 420, 219)

    erase_rrect_stroke(arr, 501.5, 214.0, 892.5, 300.0, r=14.0, tol=4.4)
    erase_rect(arr, 725, 189, 830, 219)
    erase_rect(arr, 790, 154, 911, 219)

    erase_rect(arr, 908, 188, 1348, 306)
    arr[221:294, 910:1325] = c3_patch

    erase_rect(arr, 508, 323, 892, 355)
    arr[318:347, 510:890] = title_patch

    erase_rect(arr, 378, 519, 466, 594)
    arr[522:591, 390:435] = mosfet_patch

    erase_rrect_stroke(arr, 38.5, 371.0, 483.5, 742.5, r=16.0, tol=4.2)
    erase_rrect_stroke(arr, 507.0, 371.0, 905.5, 742.5, r=16.0, tol=4.2)
    erase_rrect_stroke(arr, 928.0, 371.0, 1341.0, 742.5, r=16.0, tol=4.2)

    erase_rrect_stroke(arr, 49.5, 439.0, 150.5, 732.5, r=12.0, tol=4.0)
    erase_rrect_stroke(arr, 49.5, 439.0, 157.5, 732.5, r=12.0, tol=4.0)
    erase_rect(arr, 147, 436, 162, 736)
    erase_rrect_stroke(arr, 165.0, 439.0, 476.0, 732.5, r=12.0, tol=4.0)

    erase_rect(arr, 512, 463, 907, 478)
    erase_rect(arr, 886, 463, 907, 540)  # wipe full top-right corner arc of old Card 2 inner border
    erase_rect(arr, 512, 463, 524, 484)  # wipe full top-left corner arc of old Card 2 inner border
    erase_rect(arr, 512, 463, 522, 737)
    erase_rect(arr, 512, 730, 815, 737)
    erase_rect(arr, 743, 528, 907, 540)

    erase_rect(arr, 336, 645, 362, 664)
    erase_rect(arr, 481, 544, 510, 566)
    erase_rect(arr, 903, 544, 931, 566)
    erase_rect(arr, 1205, 573, 1235, 594)

    erase_rect(arr, 813, 549, 864, 557)
    erase_rect(arr, 856, 553, 864, 600)
    erase_rect(arr, 805, 620, 826, 630)
    erase_rect(arr, 844, 670, 875, 695)
    erase_rect(arr, 746, 697, 785, 704)
    erase_rect(arr, 777, 652, 785, 704)

    # 2. Pure #FFFFFF background unmixing
    protected = np.zeros((h, w), dtype=bool)
    protected[105:189, 139:199] = True
    protected[110:178, 926:1036] = True
    protected[108:179, 1187:1298] = True
    protected[531:634, 1112:1203] = True

    rf = arr[:, :, 0].astype(np.float32)
    gf = arr[:, :, 1].astype(np.float32)
    bf = arr[:, :, 2].astype(np.float32)
    sat = np.maximum(np.maximum(rf, gf), bf) - np.minimum(np.minimum(rf, gf), bf)
    lum = 0.299 * rf + 0.587 * gf + 0.114 * bf

    neutral = (~protected) & (sat <= 24.0)
    arr[neutral & (lum >= 194.0)] = 255

    aa_mask = neutral & (lum >= 25.0) & (lum < 194.0)
    mapped = 15.0 + (lum[aa_mask] - 25.0) * (240.0 / (194.0 - 25.0))
    mapped_u8 = np.clip(np.round(mapped), 0, 255).astype(np.uint8)
    arr[aa_mask, 0] = mapped_u8
    arr[aa_mask, 1] = mapped_u8
    arr[aa_mask, 2] = mapped_u8

    arr[(~protected) & (sat > 24.0) & (sat <= 38.0) & (lum >= 202.0)] = 255

    # 3. Vector borders & Illustrator-style arrows
    dpi = 200
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.imshow(arr, extent=(0, w, h, 0), interpolation="lanczos")

    def rbox(x0, y0, x1, y1, ec="#111827", lw=1.6, r=14, ls="solid"):
        ax.add_patch(FancyBboxPatch(
            (x0, y0), x1 - x0, y1 - y0,
            boxstyle=f"round,pad=0,rounding_size={r}",
            facecolor="none", edgecolor=ec, linewidth=lw, linestyle=ls, zorder=5,
        ))

    def sharp_arrow(x0, y0, x1, y1, color="#111827", lw=1.55, ls="solid", hl=9.5, hw=7.0):
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        bx, by = x1 - ux * (hl * 0.82), y1 - uy * (hl * 0.82)
        if dist > hl * 0.88:
            ax.plot([x0, bx], [y0, by], color=color, linewidth=lw, linestyle=ls,
                    solid_capstyle="butt", dash_capstyle="butt", zorder=6)
        hx_base, hy_base = x1 - ux * hl, y1 - uy * hl
        ax.add_patch(Polygon([
            (x1, y1),
            (hx_base + px * (hw * 0.5), hy_base + py * (hw * 0.5)),
            (hx_base - px * (hw * 0.5), hy_base - py * (hw * 0.5)),
        ], closed=True, facecolor=color, edgecolor="none", zorder=7))

    OUTER_GRAY = "#A3ABB6"
    CARD_GRAY = "#98A0AB"
    DARK_DASH = "#1E293B"
    BLACK = "#111827"
    DASH_OUTER = (0, (5.5, 3.8))
    DASH_INNER = (0, (5.0, 3.2))
    DASH_ARROW = (0, (4.8, 3.0))

    rbox(26, 64, 1354, 313, ec=OUTER_GRAY, lw=1.35, r=18, ls=DASH_OUTER)
    rbox(26, 351, 1354, 754, ec=OUTER_GRAY, lw=1.35, r=18, ls=DASH_OUTER)

    rbox(333, 105, 534, 188, ec=BLACK, lw=1.75, r=14)
    rbox(644, 105, 780, 188, ec=BLACK, lw=1.75, r=14)
    rbox(912, 105, 1050, 188, ec=BLACK, lw=1.75, r=14)
    rbox(1175, 105, 1309, 188, ec=BLACK, lw=1.75, r=14)

    sharp_arrow(210, 146, 329, 146, color=BLACK, lw=1.65, hl=10.0, hw=7.2)
    sharp_arrow(538, 146, 640, 146, color=BLACK, lw=1.65, hl=10.0, hw=7.2)
    sharp_arrow(784, 146, 908, 146, color=BLACK, lw=1.65, hl=10.0, hw=7.2)
    sharp_arrow(1054, 146, 1171, 146, color=BLACK, lw=1.65, hl=10.0, hw=7.2)

    rbox(55, 214, 480, 300, ec=DARK_DASH, lw=1.5, r=14, ls=DASH_INNER)
    rbox(499, 214, 888, 300, ec=DARK_DASH, lw=1.5, r=14, ls=DASH_INNER)
    rbox(904, 214, 1342, 300, ec=DARK_DASH, lw=1.5, r=14, ls=DASH_INNER)

    sharp_arrow(232, 214, 324, 156, color=BLACK, lw=1.55, ls=DASH_ARROW, hl=9.5, hw=6.8)
    sharp_arrow(808, 214, 900, 156, color=BLACK, lw=1.55, ls=DASH_ARROW, hl=9.5, hw=6.8)
    sharp_arrow(1072, 214, 1164, 156, color=BLACK, lw=1.55, ls=DASH_ARROW, hl=9.5, hw=6.8)

    rbox(38, 371, 484, 743, ec=CARD_GRAY, lw=1.55, r=16)
    rbox(505, 371, 909, 743, ec=CARD_GRAY, lw=1.55, r=16)
    rbox(930, 371, 1342, 743, ec=CARD_GRAY, lw=1.55, r=16)

    rbox(49, 439, 148, 733, ec=DARK_DASH, lw=1.4, r=12, ls=DASH_INNER)
    rbox(165, 439, 475, 733, ec=DARK_DASH, lw=1.4, r=12, ls=DASH_INNER)
    rbox(515, 470, 900, 734, ec=DARK_DASH, lw=1.4, r=12, ls=DASH_INNER)

    sharp_arrow(149, 515, 164, 515, color=BLACK, lw=1.4, hl=6.6, hw=5.2)
    sharp_arrow(149, 650, 164, 650, color=BLACK, lw=1.4, hl=6.6, hw=5.2)
    sharp_arrow(336, 654, 360, 654, color=BLACK, lw=1.45, hl=7.5, hw=5.8)

    sharp_arrow(485, 556, 504, 556, color=BLACK, lw=1.6, hl=8.0, hw=6.2)
    sharp_arrow(910, 556, 929, 556, color=BLACK, lw=1.6, hl=8.0, hw=6.2)
    sharp_arrow(1206, 583, 1232, 583, color=BLACK, lw=1.55, hl=8.2, hw=6.2)

    ax.plot([746, 780], [700, 700], color=BLACK, lw=1.4, solid_capstyle="projecting", zorder=6)
    sharp_arrow(780, 700, 780, 652, color=BLACK, lw=1.4, hl=7.5, hw=5.8)
    sharp_arrow(805, 625, 827, 625, color=BLACK, lw=1.4, hl=7.2, hw=5.6)
    ax.plot([860, 860], [600, 551], color=BLACK, lw=1.4, solid_capstyle="projecting", zorder=6)
    sharp_arrow(860, 551, 815, 551, color=BLACK, lw=1.4, hl=7.5, hw=5.8)
    sharp_arrow(856, 671, 856, 693, color=BLACK, lw=1.4, hl=7.2, hw=5.6)

    ax.plot([707, 707, 261], [371, 361, 361], color=BLACK, lw=1.45, linestyle=DASH_ARROW, zorder=6)
    sharp_arrow(261, 361, 261, 371, color=BLACK, lw=1.45, hl=6.5, hw=5.4)

    fig.savefig(out_png, dpi=dpi, facecolor="#FFFFFF")
    fig.savefig(
        out_pdf,
        dpi=300,
        facecolor="#FFFFFF",
        metadata={"Creator": "", "Producer": "", "Author": "", "Title": ""},
    )
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=FIGS / "spectra_framework.png")
    args = ap.parse_args()
    build(args.src, FIGS / "spectra_framework.png", FIGS / "spectra_framework.pdf")
    print("Wrote paper/figs/spectra_framework.{png,pdf}")
