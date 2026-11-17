# NARRATIVE REPORT — SPECTRA (ARIS W3 input)

Status: experiments in progress (final scope v3, see EXPERIMENT_LOG.md). Numbers below marked *interim* are read from
`results/` at the time of writing and are regenerated into `paper/numbers.tex` by `scripts/paper_numbers.py`; the paper
never hard-codes a result.

## One-sentence story
Asking an LLM for transistor widths wastes its strength. If it instead writes executable gm/Id **design-intent
programs** that predict their own performance, and a deterministic layer turns simulation into device-level evidence and
does all numerical search (including worst-PVT-condition refinement) in the program's low-dimensional intent space,
end-to-end spec-to-netlist synthesis becomes reliable on the tasks that existing agents fail: near-frontier,
many-specification and PVT-robust ones.

## Problem and gap (Sec. 1–2)
- Published LLM analog agents (AnalogCoder, AnalogCoder-Pro, AnalogAgent, AnalogSAGE, AALLM, ...) are evaluated on
  square-law models / functional checks / op-amps at TT; PVT-aware LLM methods size a *given* topology
  (AnalogScout, OPERA). An agent benchmark (ADBench long-horizon) finds frontier models fail at electrical closure.
- Pilot (EXPERIMENT_LOG 2026-11-16): on specs relaxed from archive designs every method succeeds (29/29) — the
  benchmark must be built near the frontier and across PVT to discriminate. Calibration after frontier refinement:
  direct 0/2 vs SPECTRA 1/2 on a 10-spec T3 op-amp; 0/2 vs 1/1 on the robust op-amp.

## Contributions and the evidence each needs
| # | Claim | Evidence (file) | Status |
|---|---|---|---|
| C1 | SPECTRA solves more tasks than AnalogCoder-style and AnalogCoder-Pro-style (Gen+TPE) agents under identical LLM (Opus 5.5), call (12) and simulation (300 nominal / 600 robust condition-evaluations) budgets; the advantage concentrates on the pre-registered primary endpoint (T3 ∪ robust). | results/E1_summary.json (`analyze --exp E1`), tables/main.tex, figs/E1_tiers.pdf | interim (16 common primary tasks): SPECTRA 92.7% [84,100], direct 75.0% [54,94], Gen+TPE 47.9% [27,71], SPECTRA-min 74.0% [56,89]; vs Gen+TPE Holm p=0.006, vs direct p=0.13 |
| C2 | The full agent loop matters beyond the intent representation: SPECTRA-min (one plan + intent CMA-ES, no diagnosis/repair) is weaker. | same as C1 | interim 92.7 vs 74.0 primary, 10 wins / 1 loss on all common tasks |
| C3 | Ablations: w/o diagnosis, w/o intent (raw W/L programs), w/o refinement, w/o knowledge cards (and AnalogCoder-style w/o cards). | results/E2_summary.json, tables/ablation.tex | running |
| C4 | PVT: designing at TT only and verifying afterwards (SPECTRA-TT) fails more robust tasks than adaptive worst-condition refinement; Gen+TPE with 12 regenerations + adaptive corners (genbo_full) does not close the gap. Failing conditions concentrate at low supply. | results/E3_summary.json, results/pvt_failure_conditions.json, tables/pvt.tex | running |
| C5 | Diagnosis does not improve fault localisation in isolation (negative result): Opus 77.1 vs 77.1 top-1; Haiku 59.2 → 50.8. | results/E4_summary.json, results/E4_haiku_summary.json, tables/fault.tex | final |
| C6 | Backbone: with Haiku 5.5 the gap between SPECTRA and the AnalogCoder-style agent on the subset. | results/E5_summary.json, tables/scaling.tex | running |
| C7 | Intent programs predict first-order metrics well and second-order (noise, PSRR/CMRR) poorly. | results/E1_spectra_prediction_accuracy.json | final for completed runs; regenerate |
| C8 | SPECTRA-Bench: 117 tasks (92 certified + 25 designer), 12 families, 45-condition PVT + mismatch MC, certificates re-verified. | data/bench/*.jsonl, tables/bench_stats.tex | final |
| C9 | Cost: $/run, calls, sims to success. | E1 summary | interim |

## Honest negatives / limits that must appear
- E4 null result (C5); D06 low-noise op-amp: SPECTRA 2/3 vs direct 3/3 (flicker noise mispredicted).
- Tiered seeds (compute-bound, 4 cores): 2 seeds SPECTRA/direct on T3, 1 seed elsewhere; robust: seed 0.
- Robust budget changed 1200 → 600 mid-run; scored by truncation for all methods.
- Dropped for compute: Gen+CMA-ES arm, all-corners PVT strategy, template oracle, Sonnet backbone, infeasible-spec
  controls (withdrawn after review: built incorrectly).
- Same-family reviewer (Fable 5.1 / Opus 5.5) ⇒ provisional acceptance.
- Schematic-level only (no layout parasitics), first-order poly-resistor model, ideal capacitors.

## Figures / tables
1. Fig. 1 overview (TikZ). 2. Fig. 2 intent program — verbatim abridged agent output from E1 opamp-09 s0.
3. Tab. families, Tab. bench_stats. 4. Tab. main + Fig. tiers. 5. Tab. ablation. 6. Tab. pvt. 7. Tab. fault.
8. Tab./text scaling + Fig. anytime.
