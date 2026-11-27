#!/usr/bin/env python3
"""Generate paper/figs/spectra_framework.{png,pdf} with:
1. 100% pure #FFFFFF background unmixing,
2. Connected-component + dilation removal of ALL old raster borders & arrows (zero residual hair-lines),
3. Closed SLATE-Rec template borders and crisp phase-locked bold vector arrows,
4. No green checkmark next to the Static ERC MOSFET symbol."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "paper" / "figs"


def build(src_png: Path, out_png: Path, out_pdf: Path) -> np.ndarray:
    im = Image.open(src_png).convert("RGB")
    orig = np.array(im, dtype=np.uint8)
    arr = orig.copy()
    h, w, _ = arr.shape

    # 1. Pure #FFFFFF background unmixing FIRST on untouched original image
    protected_color = np.zeros((h, w), dtype=bool)
    protected_color[105:189, 139:199] = True    # NL Spec doc icon interior
    protected_color[112:178, 926:1036] = True   # Gauge arc
    protected_color[113:179, 1187:1298] = True  # Top bar chart (tallest bar starts at y=115; old border was y<=108)
    protected_color[533:642, 1111:1204] = True  # 5x9 PVT heatmap cells (all 5 rows TT..FS through y=641)

    rf = arr[:, :, 0].astype(np.float32)
    gf = arr[:, :, 1].astype(np.float32)
    bf = arr[:, :, 2].astype(np.float32)
    sat = np.maximum(np.maximum(rf, gf), bf) - np.minimum(np.minimum(rf, gf), bf)
    lum = 0.299 * rf + 0.587 * gf + 0.114 * bf

    neutral = (~protected_color) & (sat <= 28.0)
    arr[neutral & (lum >= 192.0)] = 255

    aa_mask = neutral & (lum >= 25.0) & (lum < 192.0)
    mapped = np.clip(np.round(15.0 + (lum[aa_mask] - 25.0) * (240.0 / (192.0 - 25.0))), 0, 255).astype(np.uint8)
    arr[aa_mask] = mapped[:, None]

    arr[(~protected_color) & (sat > 28.0) & (sat <= 42.0) & (lum >= 198.0)] = 255

    # Remove green checkmark next to MOSFET in Card 1 & re-center clean MOSFET under "Static ERC"
    mosfet_patch = arr[521:590, 380:425].copy()
    arr[519:594, 378:466] = 255
    arr[522:591, 390:435] = mosfet_patch

    # 2. Protect graphics that physically touched an old border/arrow in `orig` before connected-component deletion:
    #    - Bode plot in Card 2 (x=834..897, y=405..467; bottom axis is at y=465)
    #    - Router diamond in Card 2 (x=754..805, y=600..651)
    #    - Letter "V" of "1.62 V" in Callout 3 (x=1326..1340, y=248..270)
    keep_content = protected_color.copy()
    keep_content[405:467, 834:897] = True
    keep_content[600:651, 754:805] = True
    keep_content[248:270, 1326:1340] = True

    # Label all non-white foreground strokes (< 253) outside `keep_content`
    nonwhite = (~keep_content) & (arr.min(axis=2) < 253)
    lbl, _ = ndimage.label(nonwhite, structure=np.ones((3, 3), dtype=int))

    seed = np.zeros((h, w), dtype=bool)

    def seed_rrect(x0: float, y0: float, x1: float, y1: float, r: float = 15.0, tol: float = 2.5) -> None:
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        hx, hy = max(1.0, 0.5 * (x1 - x0) - r), max(1.0, 0.5 * (y1 - y0) - r)
        qx, qy = np.abs(xx - cx) - hx, np.abs(yy - cy) - hy
        sdf = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0)) + np.minimum(np.maximum(qx, qy), 0.0) - r
        seed[np.abs(sdf) <= tol] = True

    def seed_box(x0: int, y0: int, x1: int, y1: int) -> None:
        seed[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = True

    # Seed ALL old raster borders & ALL old raster arrows
    # Outer macro-containers + old Edit top return line
    seed_rrect(27.0, 64.5, 1351.0, 316.0, r=18.0, tol=2.8)
    seed_box(22, 355, 1356, 365)
    seed_box(474, 350, 496, 368)
    seed_box(22, 752, 1356, 760)
    seed_box(23, 355, 31, 760)
    seed_box(1348, 355, 1356, 760)
    seed_box(911, 355, 924, 548)

    # Top 4 black stage boxes + horizontal arrows
    seed_rrect(335.5, 107.0, 531.5, 186.0, r=16.0, tol=2.8)
    seed_rrect(646.0, 107.0, 777.5, 185.0, r=16.0, tol=2.8)
    seed_rrect(914.0, 107.0, 1047.5, 185.0, r=16.0, tol=2.8)
    seed_rrect(1177.5, 107.0, 1306.5, 186.0, r=16.0, tol=2.8)
    seed_box(208, 139, 336, 149)
    seed_box(531, 139, 646, 149)
    seed_box(777, 139, 914, 149)
    seed_box(1047, 139, 1178, 149)

    # Top 3 callout borders (including bottom y=300..303!) + V-wedge pointers
    seed_rrect(56.5, 214.5, 478.5, 300.5, r=15.0, tol=3.0)
    seed_box(275, 188, 415, 216)
    seed_rrect(502.5, 214.5, 891.5, 300.5, r=15.0, tol=3.0)
    seed_box(730, 189, 830, 216)
    seed_box(795, 155, 911, 216)
    seed_rrect(914.5, 214.5, 1339.5, 300.5, r=15.0, tol=3.0)
    seed_box(1140, 188, 1265, 216)
    seed_box(50, 298, 1344, 305)

    # Bottom 3 gray card outer borders
    seed_rrect(39.0, 371.5, 483.5, 742.5, r=16.0, tol=2.5)
    seed_rrect(507.5, 371.5, 905.0, 742.5, r=16.0, tol=2.5)
    seed_rrect(928.5, 371.5, 1340.5, 742.5, r=16.0, tol=2.5)

    # Inner dashed borders in Card 1 & Card 2
    seed_rrect(50.0, 439.5, 150.0, 732.5, r=12.0, tol=2.5)
    seed_rrect(50.0, 439.5, 157.5, 732.5, r=12.0, tol=2.5)
    seed_box(148, 439, 161, 733)
    seed_rrect(165.5, 439.5, 475.5, 732.5, r=12.0, tol=2.5)

    # Card 2 broken inner dashed border + hook arrow
    seed_box(514, 468, 903, 476)
    seed_box(514, 468, 520, 736)
    seed_box(514, 731, 812, 736)
    seed_box(895, 468, 905, 539)
    seed_box(746, 530, 905, 539)

    # Bottom old raster arrows
    seed_box(338, 649, 360, 660)    # LUT -> Netlist
    seed_box(483, 549, 507, 561)    # Card 1 -> Card 2
    seed_box(905, 549, 929, 561)    # Card 2 -> Card 3
    seed_box(1206, 576, 1232, 592)  # Active Set -> IC Netlist
    seed_box(815, 550, 863, 556)    # Card 2 Refine -> Edit horizontal
    seed_box(856, 553, 863, 598)    # Card 2 Refine -> Edit vertical
    seed_box(806, 621, 824, 629)    # Card 2 diamond right stub
    seed_box(846, 672, 874, 692)    # Card 2 Refine -> Declare-Infeasible
    seed_box(748, 698, 783, 703)    # Card 2 Channel 4 -> diamond horizontal
    seed_box(778, 653, 783, 703)    # Card 2 Channel 4 -> diamond vertical

    hit_cids = set(np.unique(lbl[seed & (~keep_content)])) - {0}
    del_mask = np.isin(lbl, list(hit_cids))
    # Dilate by 2px (outside keep_content) so even faint 253..254 anti-aliasing fringe pixels vanish 100%!
    del_mask = ndimage.binary_dilation(del_mask, structure=np.ones((3, 3), dtype=bool), iterations=2) & (~keep_content)
    arr[del_mask] = 255
    # Also ensure absolute pure white on any >=248 gray speck outside protected color blocks
    arr[(~protected_color) & (arr.min(axis=2) >= 246)] = 255

    # 3. Clean micro-adjustments for spacious layout:
    # 3a. Shift all 3 top callout interiors down by 4px (y=221..293 -> y=225..297) and Callout 3 left by 14px
    #     so diagonal dashed arrows have extra vertical room AND "1.62 V" has 17px right padding!
    c1_patch = arr[220:295, 62:475].copy()
    c2_patch = arr[220:295, 508:888].copy()
    c3_patch = arr[220:295, 924:1341].copy()
    arr[218:302, 55:1345] = 255
    arr[224:299, 62:475] = c1_patch
    arr[224:299, 506:886] = c2_patch
    arr[224:299, 910:1327] = c3_patch

    # 3b. Shift "Inputs" interior left by 4px (x=54..144 -> x=50..140) so Inputs->SelfPred arrow corridor is 28px wide!
    inp_patch = arr[443:728, 54:144].copy()
    arr[442:730, 48:146] = 255
    arr[443:728, 50:140] = inp_patch

    # 3c. Ensure pure white behind "9 (T, Vdd) Pairs" label above heatmap (y=499..531 had ~179 gray strip)
    lbl_sub = arr[499:531, 1105:1210]
    lbl_sub[lbl_sub.mean(axis=2) >= 145] = 255

    # 3d. Position "Proposed Framework: SPECTRA" cleanly centered at y=318..346
    title_patch = arr[324:352, 510:890].copy()
    arr[322:354, 508:892] = 255
    arr[318:346, 510:890] = title_patch

    # 4. Render crisp SLATE-Rec borders and bold, crystal-clear vector arrows
    dpi = 200
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.imshow(arr, extent=(0, w, h, 0), interpolation="lanczos")

    OUTER_GRAY = "#A3ABB6"
    CARD_GRAY = "#98A0AB"
    DARK_DASH = "#1E293B"
    BLACK = "#0B0F17"
    DASH_OUTER = (0, (5.5, 3.8))
    DASH_INNER = (0, (5.0, 3.2))

    def rbox(x0: float, y0: float, x1: float, y1: float, ec=BLACK, lw=1.7, r=14, ls="solid") -> None:
        ax.add_patch(FancyBboxPatch(
            (x0, y0), x1 - x0, y1 - y0,
            boxstyle=f"round,pad=0,rounding_size={r}",
            facecolor="none", edgecolor=ec, linewidth=lw, linestyle=ls, zorder=5,
        ))

    def solid_arrow(x0: float, y0: float, x1: float, y1: float, color=BLACK, lw=2.0, hl=10.5, hw=8.4) -> None:
        """Crisp solid vector arrow with stopped shaft and sharp unstroked triangular head."""
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        bx, by = x1 - ux * (hl * 0.78), y1 - uy * (hl * 0.78)
        if dist > hl * 0.82:
            ax.plot([x0, bx], [y0, by], color=color, linewidth=lw, solid_capstyle="butt", zorder=6)
        hx_b, hy_b = x1 - ux * hl, y1 - uy * hl
        ax.add_patch(Polygon([
            (x1, y1),
            (hx_b + px * (hw * 0.5), hy_b + py * (hw * 0.5)),
            (hx_b - px * (hw * 0.5), hy_b - py * (hw * 0.5)),
        ], closed=True, facecolor=color, edgecolor="none", zorder=7))

    def phase_dashed_line(x0: float, y0: float, x1: float, y1: float, color=BLACK, lw=1.95, target_dash=9.5, ratio=0.62) -> None:
        """Draw evenly spaced dashes where BOTH endpoints (x0,y0) and (x1,y1) start/end with a full dash (zero floating gaps!)."""
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return
        ux, uy = dx / dist, dy / dist
        # L = N * d + (N - 1) * g, where g = ratio * d  =>  d = L / (N + (N - 1) * ratio)
        n_dashes = max(2, int(round((dist + target_dash * ratio) / (target_dash * (1.0 + ratio)))))
        d_len = dist / (n_dashes + (n_dashes - 1) * ratio)
        g_len = d_len * ratio
        for i in range(n_dashes):
            s = i * (d_len + g_len)
            e = min(dist, s + d_len)
            ax.plot(
                [x0 + ux * s, x0 + ux * e],
                [y0 + uy * s, y0 + uy * e],
                color=color, linewidth=lw, solid_capstyle="butt", zorder=6,
            )

    def dashed_arrow(x0: float, y0: float, x1: float, y1: float, color=BLACK, lw=1.95, hl=10.8, hw=8.6, target_dash=9.5) -> None:
        """SLATE-Rec style diagonal dashed arrow: phase-locked dashes fused directly into a crisp triangular head."""
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        # Last dash joins cleanly into the base of the arrowhead!
        bx, by = x1 - ux * (hl * 0.85), y1 - uy * (hl * 0.85)
        phase_dashed_line(x0, y0, bx, by, color=color, lw=lw, target_dash=target_dash, ratio=0.58)
        hx_b, hy_b = x1 - ux * hl, y1 - uy * hl
        ax.add_patch(Polygon([
            (x1, y1),
            (hx_b + px * (hw * 0.5), hy_b + py * (hw * 0.5)),
            (hx_b - px * (hw * 0.5), hy_b - py * (hw * 0.5)),
        ], closed=True, facecolor=color, edgecolor="none", zorder=7))

    # 4a. Two outer macro-containers
    rbox(26, 64, 1354, 314, ec=OUTER_GRAY, lw=1.35, r=18, ls=DASH_OUTER)
    rbox(26, 349, 1354, 754, ec=OUTER_GRAY, lw=1.35, r=18, ls=DASH_OUTER)

    # 4b. Top-row 4 solid black stage boxes (pure white interior, zero inner hair-lines!)
    rbox(333, 104, 534, 187, ec=BLACK, lw=1.85, r=14)
    rbox(644, 104, 780, 187, ec=BLACK, lw=1.85, r=14)
    rbox(912, 104, 1050, 187, ec=BLACK, lw=1.85, r=14)
    rbox(1175, 104, 1309, 187, ec=BLACK, lw=1.85, r=14)

    # 4c. Top-row 4 horizontal pipeline arrows (at y=138 so diagonal callout arrows below have clean breathing room, matching SLATE-Rec!)
    solid_arrow(210, 138, 327, 138, color=BLACK, lw=2.05, hl=11.0, hw=8.8)
    solid_arrow(540, 138, 638, 138, color=BLACK, lw=2.05, hl=11.0, hw=8.8)
    solid_arrow(786, 138, 906, 138, color=BLACK, lw=2.05, hl=11.0, hw=8.8)
    solid_arrow(1056, 138, 1169, 138, color=BLACK, lw=2.05, hl=11.0, hw=8.8)

    # 4d. Top-row 3 CLOSED unbroken dark-slate dashed callout boxes (y=219..304)
    rbox(55, 219, 480, 304, ec=DARK_DASH, lw=1.55, r=14, ls=DASH_INNER)
    rbox(499, 219, 888, 304, ec=DARK_DASH, lw=1.55, r=14, ls=DASH_INNER)
    rbox(904, 219, 1342, 304, ec=DARK_DASH, lw=1.55, r=14, ls=DASH_INNER)

    # 3 parallel SLATE-Rec diagonal dashed arrows (dx=+114, dy=-64 -> 131px long, 6 crisp phase-locked dashes fused to head!)
    dashed_arrow(204, 219, 318, 155, color=BLACK, lw=1.95, hl=10.8, hw=8.6, target_dash=11.0)
    dashed_arrow(782, 219, 896, 155, color=BLACK, lw=1.95, hl=10.8, hw=8.6, target_dash=11.0)
    dashed_arrow(1047, 219, 1161, 155, color=BLACK, lw=1.95, hl=10.8, hw=8.6, target_dash=11.0)

    # 4e. Bottom-row 3 solid medium-gray module cards (24px–26px inter-card corridors for bold arrows!)
    rbox(38, 375, 482, 743, ec=CARD_GRAY, lw=1.55, r=16)
    rbox(508, 375, 904, 743, ec=CARD_GRAY, lw=1.55, r=16)
    rbox(928, 375, 1342, 743, ec=CARD_GRAY, lw=1.55, r=16)

    # 4f. Inner closed dark-slate dashed sub-containers (27px corridor between Inputs & Self-Predicting!)
    rbox(47, 439, 143, 733, ec=DARK_DASH, lw=1.45, r=12, ls=DASH_INNER)
    rbox(170, 439, 474, 733, ec=DARK_DASH, lw=1.45, r=12, ls=DASH_INNER)
    rbox(517, 470, 896, 734, ec=DARK_DASH, lw=1.45, r=12, ls=DASH_INNER)

    # 4g. Bottom-row bold, crystal-clear geometric arrows (modeled on SLATE-Rec ref_bot_arrows.png)
    # Card 1: Inputs -> Self-Predicting Python Module (three crisp parallel horizontal arrows just like SLATE-Rec TEF!)
    solid_arrow(146, 505, 167, 505, color=BLACK, lw=1.85, hl=8.5, hw=7.2)
    solid_arrow(146, 580, 167, 580, color=BLACK, lw=1.85, hl=8.5, hw=7.2)
    solid_arrow(146, 655, 167, 655, color=BLACK, lw=1.85, hl=8.5, hw=7.2)

    # Card 1: BSIM4 LUT -> Canonical .subckt Netlist
    solid_arrow(333, 654, 361, 654, color=BLACK, lw=1.9, hl=9.5, hw=7.8)

    # Inter-card pipeline arrows: Card 1 -> Card 2, and Card 2 -> Card 3 (bold, clear shaft + crisp head)
    solid_arrow(484, 558, 506, 558, color=BLACK, lw=2.1, hl=9.8, hw=8.4)
    solid_arrow(906, 558, 926, 558, color=BLACK, lw=2.1, hl=9.6, hw=8.2)

    # Card 3: Active Set -> PVT-Verified SKY130 Netlist
    solid_arrow(1205, 583, 1232, 583, color=BLACK, lw=2.0, hl=9.6, hw=8.0)

    # Card 2 internal causal router arrows (bold orthogonal CAD lines, zero ambiguity)
    # Channel 4 -> bottom of router diamond (780, 651)
    ax.plot([746, 780], [700, 700], color=BLACK, lw=1.85, solid_capstyle="projecting", zorder=6)
    solid_arrow(780, 700, 780, 653, color=BLACK, lw=1.85, hl=9.0, hw=7.5)
    # Router diamond right (806, 625) -> Refine
    solid_arrow(806, 625, 829, 625, color=BLACK, lw=1.85, hl=8.6, hw=7.2)
    # Refine / Router -> Edit (clean L-arrow at x=861 up to y=550, left to 814)
    ax.plot([861, 861], [599, 550], color=BLACK, lw=1.85, solid_capstyle="projecting", zorder=6)
    solid_arrow(861, 550, 814, 550, color=BLACK, lw=1.85, hl=9.0, hw=7.5)
    # Refine -> Declare-Infeasible
    solid_arrow(856, 670, 856, 694, color=BLACK, lw=1.85, hl=8.6, hw=7.2)

    # Card-to-card Edit feedback loop above Cards 1 & 2 (phase-locked dashes + 16px clear downward arrow into Card 1!)
    phase_dashed_line(707, 375, 707, 359, color=BLACK, lw=1.8, target_dash=6.5, ratio=0.55)
    phase_dashed_line(707, 359, 260, 359, color=BLACK, lw=1.8, target_dash=10.5, ratio=0.58)
    solid_arrow(260, 359, 260, 374, color=BLACK, lw=1.85, hl=8.2, hw=7.0)

    fig.savefig(out_png, dpi=dpi, facecolor="#FFFFFF")
    fig.savefig(
        out_pdf,
        dpi=300,
        facecolor="#FFFFFF",
        metadata={"Creator": "", "Producer": "", "Author": "", "Title": ""},
    )
    plt.close(fig)
    return arr


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=FIGS / "spectra_framework.png")
    args = ap.parse_args()
    build(args.src, FIGS / "spectra_framework.png", FIGS / "spectra_framework.pdf")
    print("Wrote paper/figs/spectra_framework.{png,pdf}")
