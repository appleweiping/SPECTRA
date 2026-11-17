"""Paper figures from results/ (matplotlib, PDF). Palette: validated categorical order (dataviz reference)."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from spectra.paths import ROOT
from scripts.analyze import load, cluster_boot, load_common, TIER_GROUPS

FIG = ROOT / "paper" / "figs"
PAL = {"spectra": "#2a78d6", "spectra_min": "#eb6834", "direct": "#1baf7a", "genbo": "#eda100",
       "genbo_cmaes": "#e87ba4", "oracle_cmaes": "#008300", "spectra_nodiag": "#6250d6", "spectra_nointent": "#e34948",
       "spectra_norefine": "#52514e"}
LABEL = {"spectra": "SPECTRA", "spectra_min": "SPECTRA-min", "direct": "AnalogCoder-style", "genbo": "Gen+TPE",
         "genbo_cmaes": "Gen+CMA-ES", "oracle_cmaes": "Oracle topology+CMA-ES", "spectra_nodiag": "w/o diagnosis",
         "spectra_nointent": "w/o intent (raw W/L)", "spectra_norefine": "w/o refinement"}
plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.edgecolor": "#52514e",
                     "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "pdf.fonttype": 42, "ps.fonttype": 42})


def tier_bars(exp, methods, out):
    runs = load_common(exp, methods)
    groups = TIER_GROUPS
    groups = [(g, f) for g, f in groups if any(f(r) for r in runs)]
    fig, ax = plt.subplots(figsize=(3.4, 1.7))
    w = 0.8 / len(methods)
    for i, m in enumerate(methods):
        vals, los, his = [], [], []
        for g, f in groups:
            s, lo, hi = cluster_boot([r for r in runs if r["method"] == m and f(r)])
            vals.append(s); los.append(s - lo); his.append(hi - s)
        x = np.arange(len(groups)) + (i - (len(methods) - 1) / 2) * w
        ax.bar(x, vals, w * 0.9, color=PAL[m], label=LABEL[m], yerr=[los, his], error_kw={"lw": 0.5, "capsize": 1, "ecolor": "#52514e"})
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([g for g, _ in groups])
    ax.set_ylabel("Success rate"); ax.set_ylim(0, 1.05)
    ax.grid(axis="y", color="#e5e4e0", lw=0.5); ax.set_axisbelow(True)
    ax.legend(ncol=3, fontsize=5.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.32))
    fig.tight_layout(); fig.savefig(FIG / out, metadata={"CreationDate": None}); plt.close(fig)


def anytime(exp, methods, out, key="sims", xmax=300):
    runs = load_common(exp, methods)
    fig, ax = plt.subplots(figsize=(3.3, 1.6))
    for m in methods:
        rs = [r for r in runs if r["method"] == m and not r["robust"]]
        if not rs:
            continue
        xs = np.unique(np.concatenate([[1], np.logspace(0, np.log10(xmax), 60)]))
        ys = [np.mean([r["success"] and r[key] <= x for r in rs]) for x in xs]
        ax.plot(xs, ys, color=PAL[m], lw=1.4, label=LABEL[m])
    ax.set_xscale("log"); ax.set_xlabel("Simulations used (condition-evaluations)" if key == "sims" else "LLM calls")
    ax.set_ylabel("Solved fraction"); ax.set_ylim(0, 1.02)
    ax.grid(color="#e5e4e0", lw=0.5); ax.legend(fontsize=5.5, frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / out, metadata={"CreationDate": None}); plt.close(fig)


def family_heatmap(exp, methods, out):
    """Per-family success (rows: methods, cols: families); sequential single-hue blue, values annotated."""
    runs = load_common(exp, methods)
    fams = ["opamp", "amp", "tia", "cmirror", "ldo", "ref", "comparator", "latch", "vco", "filter", "schmitt", "opamp_app"]
    short = ["OpAmp", "Amp", "TIA", "Mirror", "LDO", "Ref", "Comp", "Latch", "VCO", "Filter", "Schmitt", "App"]
    M = np.full((len(methods), len(fams)), np.nan)
    for i, m in enumerate(methods):
        for j, fa in enumerate(fams):
            rs = [r for r in runs if r["method"] == m and r["family"] == fa]
            if rs:
                M[i, j] = cluster_boot(rs)[0]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seqblue", ["#f2f6fc", "#9cc0ee", "#2a78d6", "#123f75"])
    fig, ax = plt.subplots(figsize=(3.4, 0.35 + 0.22 * len(methods)))
    ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(methods)):
        for j in range(len(fams)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{100 * M[i, j]:.0f}", ha="center", va="center", fontsize=5,
                        color="#0b0b0b" if M[i, j] < 0.6 else "#ffffff")
    ax.set_xticks(range(len(fams))); ax.set_xticklabels(short, rotation=45, ha="right", fontsize=5.5)
    ax.set_yticks(range(len(methods))); ax.set_yticklabels([LABEL[m] for m in methods], fontsize=5.5)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout(); fig.savefig(FIG / out, metadata={"CreationDate": None}); plt.close(fig)


def anytime2(exp, methods, out, xmax_sims=300, xmax_calls=12):
    """Two panels: solved fraction (nominal tasks) vs simulations and vs LLM calls."""
    runs = [r for r in load_common(exp, methods) if not r["robust"]]
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.55), sharey=True)
    for m in methods:
        rs = [r for r in runs if r["method"] == m]
        if not rs:
            continue
        xs = np.unique(np.concatenate([[1], np.logspace(0, np.log10(xmax_sims), 60)]))
        axes[0].plot(xs, [np.mean([r["success"] and r["sims"] <= x for r in rs]) for x in xs], color=PAL[m], lw=1.3, label=LABEL[m])
        cs = np.arange(1, xmax_calls + 1)
        axes[1].step(cs, [np.mean([r["success"] and r["calls"] <= c for r in rs]) for c in cs], where="post", color=PAL[m], lw=1.3)
    axes[0].set_xscale("log"); axes[0].set_xlabel("Simulations"); axes[1].set_xlabel("LLM calls")
    axes[0].set_ylabel("Solved fraction"); axes[0].set_ylim(0, 1.02)
    for ax in axes:
        ax.grid(color="#e5e4e0", lw=0.5)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=5.5, frameon=False, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02),
               handlelength=1.2, columnspacing=0.8)
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(FIG / out, metadata={"CreationDate": None}); plt.close(fig)


if __name__ == "__main__":
    exp = sys.argv[1] if len(sys.argv) > 1 else "E1g"
    ms = sys.argv[2].split(",") if len(sys.argv) > 2 else ["spectra", "spectra_min", "direct", "genbo"]
    tier_bars(exp, ms, f"{exp}_tiers.pdf"); anytime(exp, ms, f"{exp}_anytime.pdf")
    anytime2(exp, ms, f"{exp}_anytime2.pdf"); family_heatmap(exp, ms, f"{exp}_families.pdf")
    print("ok")
