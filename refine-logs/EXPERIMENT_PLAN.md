# EXPERIMENT PLAN — SPECTRA

All runs: ngspice-42, SKY130 (tt/ff/ss/sf/fs), 4 CPU workers; LLM via `claude -p` (default sampling). Logs:
`results/raw/<exp>/<method>/<task>/<seed>.json`, LLM usage `results/llm_usage.jsonl`.

## Benchmark — SPECTRA-Bench
- 12 families; tasks derived from expert-template exploration archives (`data/explore/*.jsonl`): pick diverse sane
  reference designs; specs = reference metrics relaxed by tier margin (T1 loose, T2 standard, T3 tight); robust tier:
  specs derived from the reference's worst-case over 17 PVT conditions (reference re-verified at PVT).
- Infeasible controls: ~6 tasks with specs beyond every reference by a large margin (e.g. 120 dB gain single stage
  at 10 µW), labelled infeasible.
- Also: functional AnalogCoder-style tasks are subsumed by T1 tasks of the same circuits.

## Methods (equal budgets per task-run: ≤ 12 LLM calls, ≤ 400 testbench simulations nominal-equivalent; PVT
evaluations count each condition)
1. SPECTRA (full)
2. AnalogCoder-style: LLM writes sized netlist directly; iterative feedback of spec table + errors (AnalogCoder prompts
   adapted to SKY130 interface), up to 12 calls.
3. AnalogCoder-Pro-style: LLM proposes topology + parameterised netlist; TPE (Optuna) over raw W/L/R/C with the
   remaining simulation budget; up to 3 regeneration rounds.
4. Expert-topology oracle + CMA-ES / TPE / random (reference only — uses benchmark templates).
Ablations of SPECTRA: −intent (raw W/L program), −diagnosis (spec table only), −refinement (LLM-only repair),
−knowledge cards, −memory, −PVT-aware (robust tasks: nominal design then verify / verify-all-corners each iteration).

## Experiments
- E1 main: all tasks × {1,2,3} × 3–5 seeds; metrics: success@TT, success@PVT (robust tasks), pass@k, sims, tokens, USD, time.
- E2 ablations: stratified subset (≈36 tasks, 3/family) × 3 seeds.
- E3 robustness: robust tier tasks; compare PVT strategies; cost (sims) vs robust success.
- E4 diagnosis accuracy: fault injection on reference designs (≥ 100 faults: device to triode, under-biased branch,
  missing compensation, wrong mirror ratio, swapped polarity...), top-1/top-3 root-cause localisation, vs raw-output LLM.
- E5 backbones: Opus 5.5 / Sonnet 5.5 / Haiku 5.5 on the E2 subset for SPECTRA and AnalogCoder-style.
- E6 infeasible controls: false-success rate, infeasibility declaration precision/recall.
- E7 efficiency curves: success vs. simulation budget and vs. LLM calls (anytime curves).

## Statistics
95% bootstrap CIs over tasks×seeds; paired comparisons via McNemar / Wilcoxon signed-rank with Holm correction.
