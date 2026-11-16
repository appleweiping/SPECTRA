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
