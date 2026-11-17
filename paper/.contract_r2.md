**Verdict: close, but not yet. The round-1 demands are substantively met in code and text; the contract itself still has six places where it names the wrong artifact, understates what was done, or leaves a loophole that the check cannot catch.**

## What I verified as fine

- **Truncation is gone.** No file under results/raw has a 1200 cap; the 79 archived runs match the log's per-method counts. analyze, comparisons, pvt_failures and mc_yield all guard on the cap. The LLM cache key includes the prompt text, so re-runs only replay calls whose prompt is unchanged. The iteration prompt does show the remaining budget, so native re-runs were the right call.
- **A4, A10, A11.** TIER_GROUPS exists and the tier figure uses it; the summary's tier selectors are written separately but coincide with it. Captions compute seed ranges from the runs. pvt_failures pools the four E1 methods, records the run list, and the sentence is macro-generated. E3 fallback is present.
- **A6, A8, A14, A16.** The 61 primary tasks check out as 39 T3 plus 22 robust. Budgets of 12 calls and 300/600 are the runner's defaults. Setup discloses the LUT asymmetry, caching, interim endpoint, cap change and harness fix. The metrics paragraph now matches the main table's columns, with wall-clock struck. The Declare-Infeasible count is a macro in the method section.
- **A1, A2, A5, A15, A17 to A20** are checkable as written.

## Defects in the contract

1. **A13 names a file nothing writes.** mc_yield.py, make_tables.py and paper_numbers.py now all use results/mc_yield.json with a top-level "yield" key. The contract says E1_mc_yield.json. Also, the table's yield column is restricted to the matched subset tasks while the generated MC sentence pools every PVT-verified seed-0 design of E1 and E3. The assertion must name the real file and require the text to state its pool. Since the mismatch model relies on per-instance re-evaluation of agauss inside the subcircuit, A13 should also require a logged check that samples actually differ, or the yield column is meaningless.

2. **A12 says archived runs are "re-run". Only some are.** The log states archived seed-1 robust runs are not re-run, and results/raw/E1 now contains zero robust runs with seed above 0. The archive holds about 25 such E1 files across all four methods. The resulting protocol is consistent, but the contract and the setup sentence "were discarded and re-run at 600" must say: robust tasks use seed 0 only in E1 and E5, seeds 0 to 1 in E2, and archived higher seeds were dropped. Pending work is substantial and the contract should state the automatic fallback: a robust task whose seed-0 run is incomplete at check time leaves the common set, and the paper reports the resulting n.

| robust seed-0 cells (4 methods × 22 tasks) | count |
|---|---|
| present at 600 | 53 |
| archived, to re-run | 23 |
| never run | 12 |

3. **A3's freshness list has a loophole.** failure_analysis.py produces E1_failures.json, which feeds the two failure-mode macros, yet it is not among the commands run at check time. A stale file would pass "no diff" because nothing regenerates it. "results/*.json" also sweeps in E4 summaries, the pilot summary and the citation check, which the listed commands never touch. Name each command and the exact files it must reproduce, and add failure_analysis.

4. **A4's "all E1 statistics use the common task set" is false for two generators.** failure_analysis pools every run of every method, includes control tasks, and has no cap guard. prediction_accuracy pools all SPECTRA runs. Either both use load_common on the four methods, or A4 exempts them and the text states the pool for "of 8 failed runs" and for the intent-variable medians.

5. **A7's abstract macro is unowned.** AbsMainClaim is a hand-written placeholder in main.tex, outside numbers.tex, so A3 cannot reach it. Require paper_numbers.py to emit it with wording chosen by the Holm-corrected p rule, as it already does for the PVT sentence.

6. **A9 applies a lower standard to a negative claim.** "Degrades it for Haiku" rests on 59.2 versus 50.8 percent over 120 cases with no test. Under A7's own rule this is a point estimate with n unless a paired test supports it.

Draft issues I noticed but which are not contract matters: NPrimaryFamilies renders as "--" from a stale summary, the conclusion says one or two seeds while captions say 1 to 3, and the PVT sentence prints "median --" for a method with no successes.

CONTRACT_ACCEPTED: no

1. Fix A13: name results/mc_yield.json and its schema, require the text to state the pooled design set, and require a logged check that mismatch samples differ.
2. Rewrite A12 to state what is re-run and what is dropped: robust tasks seed 0 only in E1 and E5, seeds 0 to 1 in E2; archived higher seeds discarded; setup text to match; incomplete robust tasks leave the common set at check time and the n is reported.
3. Make A3 enumerate each regenerating command with the exact files it must reproduce, add scripts.failure_analysis, and drop the blanket "results/*.json".
4. Amend A4 so failure_analysis and prediction_accuracy either use load_common on the four main methods or are exempted with their pool stated in the text.
5. Amend A7 to require AbsMainClaim be emitted by paper_numbers.py with wording set by the Holm p rule.
6. Amend A9 so the Haiku localisation statement is a point estimate with n, or is backed by a paired test.