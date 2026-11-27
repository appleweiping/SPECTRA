"""Draw paper/figs/diagnostics_analysis.pdf from committed result JSON.

(a) share of synthesized intent programs whose analytical self-prediction lies
    within +-25% of SPICE, per metric (first-order vs second-order metrics);
(b) corner failures of TT-passing designs over the 5-corner x 3-temperature x
    3-supply PVT grid, summed over designs.

Usage: python scripts/make_diagnostics_fig.py [output.pdf]
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.size": 6.3,
    "axes.edgecolor": "#475569",
    "axes.linewidth": 0.6,
})

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "paper/figs/diagnostics_analysis.pdf"

pred = json.load(open(ROOT / "results/E1g_spectra_prediction_accuracy.json"))["metrics"]
pvt = json.load(open(ROOT / "results/pvt_failure_conditions.json"))

FIRST = [
    ("vref", r"$V_{\mathrm{ref}}$"),
    ("iq", r"$I_Q$"),
    ("gbw", "GBW"),
    ("swing", "Swing"),
    ("power", "Power"),
    ("ugbw", "UGBW"),
]
SECOND = [
    ("slew", "Slew"),
    ("noise_1k", "Noise"),
    ("settle", "Settle"),
    ("line_reg", "LineReg"),
    ("rout", r"$R_{\mathrm{out}}$"),
]
C1, C2 = "#1e4e8c", "#c84b31"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(3.48, 2.18), gridspec_kw={"width_ratios": [1.0, 1.32], "wspace": 0.34}
)

rows = [(n, 100 * pred[k]["within_25pct"], C1) for k, n in FIRST] + [
    (n, 100 * pred[k]["within_25pct"], C2) for k, n in SECOND
]
y = np.arange(len(rows))[::-1]
ax1.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.70, edgecolor="none")
ax1.axhline(len(SECOND) - 0.5, color="#94a3b8", lw=0.6, ls="--")
ax1.set_yticks(y)
ax1.set_yticklabels([r[0] for r in rows], fontsize=5.8)
ax1.set_xlim(0, 106)
ax1.set_xticks([0, 50, 100])
ax1.set_xlabel(r"Within $\pm 25\%$ of SPICE (%)", fontsize=6.0)
ax1.set_title("(a) Self-prediction calibration", fontsize=6.6, fontweight="bold", pad=5)
ax1.spines[["top", "right"]].set_visible(False)
ax1.grid(axis="x", color="#e2e8f0", lw=0.5)
ax1.set_axisbelow(True)
ax1.legend(
    handles=[plt.Rectangle((0, 0), 1, 1, color=C1), plt.Rectangle((0, 0), 1, 1, color=C2)],
    labels=["1st-order", "2nd-order"],
    loc="lower right",
    fontsize=5.4,
    frameon=True,
    facecolor="white",
    edgecolor="none",
    framealpha=0.88,
    handlelength=0.9,
    borderpad=0.2,
)

corners = ["tt", "ff", "ss", "sf", "fs"]
temps = ["-40C", "27C", "125C"]
temp_labels = ["-40", "27", "125"]
vdds = ["1.62V", "1.8V", "1.98V"]
grid = np.zeros((len(corners), 9))
for key, n in pvt["fail_counts"].items():
    c, t, v = key.split("_")
    grid[corners.index(c), vdds.index(v) * 3 + temps.index(t)] += n

ax2.imshow(grid, cmap="OrRd", aspect="auto", vmin=0, vmax=max(18, grid.max()))
ax2.set_xticks(range(9))
ax2.set_xticklabels(temp_labels * 3, fontsize=5.0, rotation=40, ha="right", rotation_mode="anchor")
ax2.tick_params(axis="x", pad=1, length=2)
ax2.set_yticks(range(5))
ax2.set_yticklabels([c.upper() for c in corners], fontsize=5.8)
ax2.tick_params(axis="y", length=2)

for i in range(5):
    for j in range(9):
        n = int(grid[i, j])
        ax2.text(
            j, i, str(n) if n else "-",
            ha="center", va="center", fontsize=5.5,
            color="white" if n > 0.52 * grid.max() else "#1e293b",
        )

for x in (2.5, 5.5):
    ax2.axvline(x, color="#1e293b", lw=0.8)

tot = sum(pvt["by_vdd"].values())
vdd_Disp = ["1.62 V", "1.80 V", "1.98 V"]
for k, v in enumerate(vdds):
    pct_str = f" ({100 * pvt['by_vdd'][v] / tot:.0f}%)" if k == 0 else ""
    ax2.text(
        k * 3 + 1, -0.62, vdd_Disp[k] + pct_str,
        ha="center", va="bottom", fontsize=5.4, fontweight="bold" if k == 0 else "normal",
        color="#991b1b" if k == 0 else "#334155",
    )

ax2.set_xlabel(r"Temperature [$^\circ\mathrm{C}$]", fontsize=6.0, labelpad=2)
ax2.set_title(f"(b) 45-corner failures ($n={pvt['n_designs']}$)", fontsize=6.6, fontweight="bold", pad=13)

fig.subplots_adjust(left=0.14, right=0.99, bottom=0.22, top=0.84, wspace=0.34)
fig.savefig(OUT, metadata={"CreationDate": None, "Producer": "pdfTeX", "Creator": "LaTeX"})
print("wrote", OUT)
