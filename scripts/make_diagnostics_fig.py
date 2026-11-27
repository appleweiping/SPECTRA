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

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["font.size"] = 6.5

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "paper/figs/diagnostics_analysis.pdf"

pred = json.load(open(ROOT / "results/E1g_spectra_prediction_accuracy.json"))["metrics"]
pvt = json.load(open(ROOT / "results/pvt_failure_conditions.json"))

FIRST = [("vref", "Vref"), ("iq", "Iq"), ("gbw", "GBW"), ("swing", "Swing"), ("power", "Power"), ("ugbw", "UGBW")]
SECOND = [("slew", "Slew"), ("noise_1k", "Noise"), ("settle", "Settle"), ("line_reg", "LineReg"), ("rout", "Rout")]
C1, C2 = "#2f6fdd", "#d6403a"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(3.45, 2.3), gridspec_kw={"width_ratios": [1, 1.25]})

rows = [(n, 100 * pred[k]["within_25pct"], C1) for k, n in FIRST] + \
       [(n, 100 * pred[k]["within_25pct"], C2) for k, n in SECOND]
y = np.arange(len(rows))[::-1]
ax1.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.72)
ax1.set_yticks(y)
ax1.set_yticklabels([r[0] for r in rows])
ax1.set_xlim(0, 105)
ax1.set_xlabel(r"Pred. within $\pm$25% (%)")
ax1.set_title("(a) Prediction fidelity", fontsize=7, fontweight="bold")
ax1.spines[["top", "right"]].set_visible(False)
ax1.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C1), plt.Rectangle((0, 0), 1, 1, color=C2)],
           labels=["1st-order", "2nd-order"], loc="lower right", fontsize=6, frameon=False)

corners = ["tt", "ff", "ss", "sf", "fs"]
temps = ["-40C", "27C", "125C"]
vdds = ["1.62V", "1.8V", "1.98V"]
grid = np.zeros((len(corners), 9))
for key, n in pvt["fail_counts"].items():
    c, t, v = key.split("_")
    grid[corners.index(c), vdds.index(v) * 3 + temps.index(t)] += n
ax2.imshow(grid, cmap="Oranges", aspect="auto")
ax2.set_xticks(range(9))
ax2.set_xticklabels([t[:-1] for _ in vdds for t in temps], fontsize=6)
ax2.set_yticks(range(5))
ax2.set_yticklabels([c.upper() for c in corners])
for i in range(5):
    for j in range(9):
        n = int(grid[i, j])
        ax2.text(j, i, n if n else "-", ha="center", va="center", fontsize=6,
                 color="white" if n > 0.6 * grid.max() else "black")
for x in (2.5, 5.5):
    ax2.axvline(x, color="black", lw=0.8)
tot = sum(pvt["by_vdd"].values())
for k, v in enumerate(vdds):
    ax2.text(k * 3 + 1, 5.15, v.replace("V", " V") + (f"\n({100 * pvt['by_vdd'][v] / tot:.0f}%)" if k == 0 else ""),
             ha="center", va="top", fontsize=6.5)
ax2.set_xlabel(r"Temperature [$\degree$C]", fontsize=6.5, labelpad=24)
ax2.set_title(f"(b) PVT failures (n={pvt['n_designs']})", fontsize=7, fontweight="bold")

fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
