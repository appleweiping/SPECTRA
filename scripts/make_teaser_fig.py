#!/usr/bin/env python3
"""Upgrade paper/figs/spectra_teaser.{png,pdf}: replace the AI T-block cluster and speech-bubble
V-wedge in Panel (a) Card 2 with an authentic IEEE CMOS differential-pair schematic (M1 != M2 + Rz/Cc)
and a closed dashed callout box + crisp arrow."""
from __future__ import annotations

import math
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "paper" / "figs"


def build(src_png: Path, out_png: Path, out_pdf: Path) -> None:
    im = Image.open(src_png).convert("RGB")
    orig = np.array(im, dtype=np.uint8)
    arr = orig.copy()
    h, w, _ = arr.shape

    bg_rgb = tuple(int(v) for v in np.median(orig[192:202, 272:295].reshape(-1, 3), axis=0))

    # Wipe entire interior of Panel (a) Card 2 below subtitle (y=191..468, x=264..518),
    # preserving incoming arrow tip on the left (x<=269, y=270..296) and outer card border (x=256, 524, y=474)
    arr[191:268, 264:518] = bg_rgb
    arr[268:298, 271:518] = bg_rgb
    arr[298:476, 264:518] = bg_rgb

    dpi = 200
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.imshow(arr, extent=(0, w, h, 0), interpolation="lanczos")

    NAVY = "#2B3A4E"
    TEAL = "#48758C"
    RED = "#C04B43"
    DARK_DASH = "#1E293B"
    TEXT_BLACK = "#111827"

    def sharp_arrow(x0, y0, x1, y1, color=DARK_DASH, lw=1.55, ls="solid", hl=8.0, hw=6.0):
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        bx, by = x1 - ux * (hl * 0.8), y1 - uy * (hl * 0.8)
        if dist > hl * 0.85:
            ax.plot([x0, bx], [y0, by], color=color, lw=lw, linestyle=ls, zorder=6)
        hx_b, hy_b = x1 - ux * hl, y1 - uy * hl
        ax.add_patch(Polygon([
            (x1, y1),
            (hx_b + px * hw * 0.5, hy_b + py * hw * 0.5),
            (hx_b - px * hw * 0.5, hy_b - py * hw * 0.5),
        ], closed=True, facecolor=color, edgecolor="none", zorder=7))

    # --- IEEE Analog IC Differential Pair + Broken Mirror/Rz Schematic (spacious, non-overlapping) ---
    # Note: at dpi=200, 1pt = 2.78px -> fontsize=5.2pt = 14.5px, fontsize=6.8pt = 19px!
    x_c, x_L, x_R = 384.0, 336.0, 432.0

    # VDD supply bar at y=206
    ax.plot([314, 454], [206, 206], color=NAVY, lw=2.0, solid_capstyle="round", zorder=6)
    ax.text(x_c, 203, r"$\mathbf{V_{DD}}$", fontsize=5.2, color=NAVY, ha="center", va="bottom", zorder=7)

    # Drain loads (mismatched mirror/load elements) y=206..244
    ax.plot([x_L, x_L], [206, 214], color=NAVY, lw=1.7, zorder=6)
    ax.add_patch(FancyBboxPatch((x_L - 5.5, 214), 11, 18, boxstyle="round,pad=0,rounding_size=1.5",
                                facecolor="#FFFFFF", edgecolor=NAVY, lw=1.5, zorder=6))
    ax.plot([x_L, x_L], [232, 248], color=NAVY, lw=1.7, zorder=6)

    ax.plot([x_R, x_R], [206, 214], color=NAVY, lw=1.7, zorder=6)
    ax.add_patch(FancyBboxPatch((x_R - 5.5, 214), 11, 18, boxstyle="round,pad=0,rounding_size=1.5",
                                facecolor="#FFF5F5", edgecolor=RED, lw=1.5, zorder=6))
    ax.plot([x_R, x_R], [232, 248], color=NAVY, lw=1.7, zorder=6)

    # Uncoupled Miller Rz - Cc branch at y=224 extending right from right drain (432 -> 504), well ABOVE M2!
    ax.plot([x_R + 5.5, 456], [223, 223], color=TEAL, lw=1.4, linestyle=(0, (3, 2)), zorder=6)
    ax.add_patch(FancyBboxPatch((456, 218.5), 15, 9, boxstyle="round,pad=0,rounding_size=1",
                                facecolor="#FFFFFF", edgecolor=TEAL, lw=1.35, zorder=6))
    ax.plot([471, 481], [223, 223], color=TEAL, lw=1.4, zorder=6)
    ax.plot([481, 481], [216.5, 229.5], color=TEAL, lw=1.7, zorder=6)
    ax.plot([486, 486], [216.5, 229.5], color=TEAL, lw=1.7, zorder=6)
    ax.plot([486, 496], [223, 223], color=TEAL, lw=1.4, zorder=6)
    ax.text(476, 213, r"$R_z, C_c$", fontsize=4.8, fontweight="bold", color=TEAL, ha="center", va="bottom", zorder=7)

    # Left NMOS M1 (y=244..284)
    ax.plot([306, 318], [264, 264], color=NAVY, lw=1.7, zorder=6)
    ax.plot([318, 318], [248, 280], color=NAVY, lw=1.8, zorder=6)
    ax.plot([324, 324], [244, 284], color=TEAL, lw=2.6, zorder=6)
    ax.plot([324, x_L], [248, 248], color=NAVY, lw=1.7, zorder=6)
    ax.plot([324, x_L], [279, 279], color=NAVY, lw=1.7, zorder=6)
    sharp_arrow(325, 279, 335, 279, color=NAVY, lw=1.5, hl=5.8, hw=4.8)
    ax.text(303, 263, "M1\n17.4u", fontsize=4.9, fontweight="bold", color=NAVY, ha="right", va="center", linespacing=1.1, zorder=7)

    # Right NMOS M2 (mismatched raw width highlighted in terracotta RED, y=240..288)
    ax.plot([450, 462], [264, 264], color=RED, lw=1.7, zorder=6)
    ax.plot([450, 450], [246, 282], color=RED, lw=1.8, zorder=6)
    ax.plot([444, 444], [240, 288], color=RED, lw=3.8, zorder=6)
    ax.plot([x_R, 444], [248, 248], color=RED, lw=1.7, zorder=6)
    ax.plot([x_R, 444], [279, 279], color=RED, lw=1.7, zorder=6)
    sharp_arrow(443, 279, 433, 279, color=RED, lw=1.5, hl=5.8, hw=4.8)
    ax.text(465, 263, "M2\n11.2u", fontsize=4.9, fontweight="bold", color=RED, ha="left", va="center", linespacing=1.1, zorder=7)

    # Center symmetry-broken pill badge between M1 & M2 (fits cleanly with generous padding!)
    ax.add_patch(FancyBboxPatch((347, 253), 74, 22, boxstyle="round,pad=0,rounding_size=6",
                                facecolor="#FFF5F5", edgecolor=RED, lw=1.3, zorder=7))
    ax.text(x_c, 264.5, r"$\mathbf{W_1 \neq W_2}$", fontsize=5.3, color=RED, ha="center", va="center", zorder=8)

    # Tail connection & IEEE current sink to ground
    ax.plot([x_L, x_L, x_R, x_R], [279, 295, 295, 279], color=NAVY, lw=1.7, zorder=6)
    ax.plot([x_c, x_c], [295, 304], color=NAVY, lw=1.7, zorder=6)
    ax.add_patch(Circle((x_c, 316), 11.5, facecolor="#FFFFFF", edgecolor=NAVY, lw=1.6, zorder=6))
    sharp_arrow(x_c, 308.5, x_c, 323.5, color=NAVY, lw=1.45, hl=5.5, hw=4.5)
    ax.plot([x_c, x_c], [327.5, 335], color=NAVY, lw=1.7, zorder=6)
    ax.plot([x_c - 10, x_c + 10], [335, 335], color=NAVY, lw=1.7, zorder=6)
    ax.plot([x_c - 6.5, x_c + 6.5], [339, 339], color=NAVY, lw=1.5, zorder=6)
    ax.plot([x_c - 3, x_c + 3], [343, 343], color=NAVY, lw=1.4, zorder=6)

    # --- Clean closed dark-slate dashed callout box + crisp vector text + straight upward dashed arrow ---
    ax.add_patch(FancyBboxPatch(
        (271, 369), 240, 94,
        boxstyle="round,pad=0,rounding_size=12",
        facecolor="#FFFFFF",
        edgecolor=DARK_DASH,
        linewidth=1.5,
        linestyle=(0, (5.0, 3.2)),
        zorder=6,
    ))
    ax.text(
        391, 416,
        "Breaks differential\nsymmetry & mirror\nratios",
        fontsize=6.9,
        fontfamily="sans-serif",
        color=TEXT_BLACK,
        ha="center",
        va="center",
        linespacing=1.18,
        zorder=7,
    )
    sharp_arrow(x_c, 369, x_c, 348, color=DARK_DASH, lw=1.5, ls=(0, (4.2, 2.8)), hl=7.2, hw=5.6)

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
    ap.add_argument("--src", type=Path, default=FIGS / "spectra_teaser.png")
    args = ap.parse_args()
    build(args.src, FIGS / "spectra_teaser.png", FIGS / "spectra_teaser.pdf")
    print("Wrote paper/figs/spectra_teaser.{png,pdf}")
