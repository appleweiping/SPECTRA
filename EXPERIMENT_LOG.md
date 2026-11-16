# EXPERIMENT LOG (ARIS W1.5)

## 2026-11-16 Pilot (results/raw/pilot, results/pilot/pilot_run.log)
- 8 tasks (op-amp T2/T3/robust, amplifier T2/T3, TIA T3, current mirror T3) × {spectra, spectra_min, direct, genbo}, seed 0.
- Outcome: **every completed run succeeded** (29/29 before the pilot was stopped), including the AnalogCoder-style
  `direct` baseline in 1–4 LLM calls and the robust op-amp in 3 calls.
- Interpretation: with Opus 5.5 the template-archive-derived T2/T3 margins are not tight; the benchmark saturates.
  The Gate-1 reviewer predicted this ("tiers relative to a 480-evaluation archive, not to physical limits").
- Decisions: (1) T3 margins tightened (1 dB / 2° / 0.95× / 0.97×), robust tasks derive specs with T3 margins from the
  reference's 45-condition worst case; (2) **frontier refinement** of T3/robust references (CMA-ES maximising the minimum
  normalised improvement of all chosen metrics over the archive reference, worst case over hard PVT conditions for
  robust tasks) before spec derivation; (3) slot allocation shifted toward T3/robust; (4) efficiency (calls, tokens,
  sims) and weaker backbones become first-class outcomes since nominal success saturates.

## 2026-11-16 Code review R1 (refine-logs/CODE_REVIEW_R1.md, Fable 5.1)
All MUST-FIX items addressed (commit "Code review R1 fixes"): opaque task ids and no ids in prompts (topology/tier leak),
ota5t polarity + polarity spec/sanity, hard budget cap with lock, CMA incumbent + budget-sized populations, robust
refine on the active corner set, oracle PVT loop, temperature LUTs (queued), sandbox import/I-O restrictions,
settling relative to final value. Archives of ota5t/fcasc/sf/cm_psrc are regenerated.

## 2026-11-16 Difficulty calibration (results/raw/calib, results/pilot/calib_run.log)
Hardened tasks (frontier-refined T3 references, T3 margins; robust tasks from 45-condition worst case):
| task | direct (AnalogCoder-style) | SPECTRA (pre-fix parser) |
|---|---|---|
| op-amp T3, 10 specs (frontier-refined) | 0/2 (12 calls each, $2.8–4.0) | 1/2 (9 calls, 228 sims; failed run within 0.4% of UGBW and 0.1% of settling) |
| op-amp T3 robust (45 PVT) | 0/2 (TT pass, PVT fail; 12 calls) | 1/1 so far (3 calls, 132 sims, $0.35) |
| cascode amplifier T3 (not frontier-refined) | 2/2* | 2/2* |
Finding: the hardened tiers discriminate. A parser bug dropped split-JSON `refine` actions in 3 of 11 SPECTRA
iterations of the failed run (fixed before E1). Cost per failing direct run on hard op-amps is $2.8–4.0 (very long
outputs), relevant for the cost analysis.

*Correction: when assembling `data/bench/calib_tasks.jsonl` I appended `polarity_ok>=1` to every calibration task,
including the amplifier task whose family has no such metric (an inverting CS/cascode stage), which made that task
unsatisfiable; the logged `budget_exhausted` outcomes for it are artefacts. Re-checking the returned netlists against the
task's real specs (scripts in this log entry) gives 2/2 for both methods. The production builder adds `polarity_ok`
only to the op-amp family (EXTRA_SPECS), so SPECTRA-Bench is unaffected.

## 2026-11-16 20:05 Harness fix during E1 (designer tier)
A SPECTRA run (D03 seed 1) spent all 12 calls without a single simulation: the iteration prompt did not repeat the
design-program API (stateless calls), so after a broken first program the model lost track of `lut.size`; the sandbox
also lacked common exception builtins and the forbidden-construct regex rejected `__init__`. Fixes: API doc in the
iteration and fix prompts, API reminder appended to program errors, exception builtins and class definitions allowed,
forbidden list narrowed to real escape vectors, scalar PARAMS accepted as fixed values. All E1 results of SPECTRA and
SPECTRA-min obtained before the fix were deleted and re-run so that E1 uses a single method version; baseline results
(direct, genbo) were unaffected by the change and kept.

## 2026-11-16 23:05 E1 throughput and protocol
E1 was CPU-bound (4 cores; load average up to 27 with five concurrent experiment processes). Secondary jobs (E5,
E4 extension, control-task runs) were paused (SIGSTOP) and E1 restarted with (i) a machine-wide limit of 5 concurrent
ngspice processes (flock slots) and (ii) the seed protocol: SPECTRA and the AnalogCoder-style agent 3 seeds, the
simulation-heavy Gen+TPE and SPECTRA-min 2 seeds (analysis uses seeds 0-1 for these two even where a third seed
had completed). Restarting loses no LLM work: responses are cached per (run tag, call index).
