# FINAL PROPOSAL (research contract) — SPECTRA

## Problem
Given a natural-language analog specification (function, interface, load/bias conditions, quantitative targets, and
optionally a PVT-robustness requirement), produce a sized transistor-level netlist in a real PDK (SKY130) that meets
**all** targets in simulation — at TT, and for robust tasks across 17 PVT conditions (5 process corners × {−40, 27,
125 °C} at 1.8 V, plus TT at 1.62/1.98 V).

## Hypotheses (each mapped to an experiment)
- H1 (end-to-end): SPECTRA achieves a substantially higher all-spec success rate than LLM-only iterative design
  (AnalogCoder-style) and LLM-topology + black-box sizing (AnalogCoder-Pro-style) under equal LLM-call and simulation
  budgets, across 12 families. → E1
- H2 (intent abstraction): expressing sizing as gm/Id intent programs reduces both LLM iterations and simulations
  to first feasible design vs. raw W/L programs. → E2 ablation (−intent)
- H3 (diagnosis): causal diagnosis (regions, margins, sensitivities, prediction discrepancy) improves repair success over
  raw spec tables; diagnosis localises injected faults with high top-1/top-3 accuracy. → E2 ablation (−diag), E4 fault injection
- H4 (robustness): PVT-aware refinement with adaptive worst-corner selection raises robust (17-PVT) success at lower
  simulation cost than verifying all corners every iteration or nominal-only design. → E3
- H5 (generality): gains hold across LLM backbones (Opus 5.5, Sonnet 5.5, Haiku 5.5). → E5
- H6 (honesty): on infeasible-spec controls, SPECTRA declares infeasibility rather than claiming success. → E6

## Method summary (modules)
M1 spec formalizer (NL → typed targets) · M2 topology knowledge cards + experience memory · M3 design-intent program
synthesis (gm/Id LUT API, intent variables, self-predicted performance) · M4 static checks (sandbox exec, parse, ERC) ·
M5 simulation + causal diagnosis · M6 hierarchical repair policy (LLM) · M7 intent-space numerical refinement (CMA-ES,
warm start) · M8 PVT-aware refinement (adaptive worst-corner set) + full-PVT verification · M9 infeasibility declaration.

## Success criteria for the paper
- Benchmark ≥ 100 tasks, ≥ 12 families, feasibility certificates; ≥ 3 seeds (5 for main comparison where budget allows).
- Report pass@1 / pass@k (TT and PVT), sims-to-first-feasible, LLM tokens/USD, wall-clock, with 95% CIs.
- Claims only from `results/` files; ARIS audits (experiment, claim, citation) before submission.

## Non-goals
Layout/extraction, fine-tuning, novel-topology discovery (we compose from known archetypes).
