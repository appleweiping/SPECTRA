# EXPERIMENT PLAN — SPECTRA (revised after Gate-1 review, pilot and calibration)

Common: ngspice-42, SKY130 (5 corners, 3 temps, 3 supplies = 45-condition PVT grid; per-instance mismatch MC),
LLM = Claude Opus 5.5 via `claude -p` (default sampling) for all LLM methods; identical task text, interface,
PDK sheet and topology knowledge cards for all LLM methods; opaque task ids; independent final verification.
Budgets per run: ≤12 LLM calls; ≤300 (nominal) / ≤2000 (robust) condition-evaluations, hard-capped.

## Benchmark — SPECTRA-Bench
- Certified tier: 92 slots over 12 families (T1/T2/T3 + 19 robust); T3/robust references frontier-refined;
  T3 margins 1 dB / 2° / 0.95× / 0.97×; robust specs from the 45-condition worst case with T3 margins.
- Designer tier: 25 hand-written tasks (5 robust), feasibility certified post hoc.
- Oracle-unmet controls: tightened certified tasks that an extended template oracle (2×600 CMA-ES evals) cannot meet.

## Experiments
- E1 main: all tasks × 3 seeds × {SPECTRA, SPECTRA-min, AnalogCoder-style, Gen+TPE}; Oracle(CMA-ES) on template tasks.
- E2 ablations (stratified subset, 2 hardest nominal + 1 robust per family): w/o diagnosis, w/o intent (raw W/L),
  w/o refinement, Gen+CMA-ES; 3 seeds.
- E3 PVT strategy (robust tasks): adaptive (SPECTRA) vs all-corners-every-step vs nominal-only; + MC yield of
  robust-tier final designs (100 samples).
- E4 diagnosis by fault injection: 7 fault classes on certified references; rule-only vs LLM+raw vs LLM+SPECTRA diagnosis.
- E5 backbone scaling: Sonnet 5.5 / Haiku 5.5 on the subset for SPECTRA and AnalogCoder-style (2 seeds).
- Efficiency: anytime success vs simulations and vs LLM calls; tokens/$ per success.
## Statistics
Cluster bootstrap over tasks (95% CI); paired Wilcoxon on per-task success with Holm correction.
