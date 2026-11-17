I have what I need. Everything the executor claimed is in the code, and I confirmed each item directly. One defect remains that the contract itself lets through, plus two wording gaps.

## Verified as fine

- **A7 / `\AbsMainClaim`.** The macro is emitted by paper_numbers.py and picks the wording per baseline from the Holm-corrected permutation p on the primary endpoint. The hand-written `\providecommand` in main.tex is only a fallback for a missing numbers file.
- **A3 freshness list.** Every listed command exists, accepts the stated arguments, and writes the named file. The order is right: paper_numbers runs last and reads everything upstream. All bootstrap and permutation draws use fixed seeds, so "no diff" is achievable. failure_analysis and prediction_accuracy both restrict to `load_common` of the four main methods and state the pool in their docstrings.
- **A12.** No E1 robust run has a seed above 0. The loader drops any robust run above the 600 cap. The runner defaults robust tasks to 600. Setup text states seed-0-only for E1 and E5, seeds 0 to 1 for E2, discarded higher seeds, and the harness fix with selective re-run. `load_common` intersects tasks across methods, so an incomplete robust task leaves the set automatically.
- **A13.** mc_yield.py writes the schema the contract names and records `max_rel_spread` per design. The sentence and table read `results/mc_yield.json`. E3 has no runs yet; the A11 fallback covers it.
- **A6, A8, A11.** The primary list file has 61 entries. Setup says "interim review, after about a third of the main-experiment runs", discloses the LUT asymmetry and caching. pvt_failures pools only the four E1 methods, guards the cap, and records the run list.
- **A1, A2, A5, A10, A14 to A20** are checkable as written.

## Defect the contract lets through

**E4 is reported from two different case pools, and A3 exempts the one that is stale.** The Haiku summary is frozen at 120 cases, while the raw directory and the regenerated E4_tests.json hold 156. The fault table puts Haiku columns beside Opus columns under a single n column, and the Haiku sentence takes its accuracies and case count from the summary but its discordant counts and p from E4_tests.

| source | Haiku n | raw top-1 | diag top-1 |
|---|---|---|---|
| results/E4_haiku_summary.json | 120 | 59.2% | 50.8% |
| results/E4_tests.json | 156 | 60.9% | 55.1% |
| Opus summary, same table | 166 | | |

Because A3 declares E4 summaries "inputs, not checked for freshness", the check passes while the sentence prints a 120-case point estimate with a 156-case p-value. Re-running fault_injection at check time is not an option, since it would call the LLM for any missing case. The fix is a checkable equality, not machinery.

## Wording gaps

- **A9** forbids the word "degrades" unless p < 0.05. The current text says "a long structured report can distract a smaller model" at p = 0.21. The rule must cover the claim, not the word.
- **A7** chooses wording from p alone. A significant negative difference would be printed as a "gain". The rule should also require the sign.

## Notes that need no contract change

- A4 says `TIER_GROUPS` is used by the summary and main table. Today `summarize()` has its own inline tier lambdas and the main table reads those fields. They coincide, but the assertion as written fails until `summarize()` uses `TIER_GROUPS`. Satisfiable in a few lines.
- A3's "content, not bytes" for figures is honest but can only be checked by eye. Passing `metadata={"CreationDate": None}` to savefig would make a byte diff work. Optional.
- The conclusion's "reliable where it matters" is a comparative claim that A7 already governs. With the current p against the AnalogCoder-style baseline it would have to change, which is the intended effect.

CONTRACT_ACCEPTED: no

1. Amend A3 and A9(i): the Haiku and Opus fault-localisation numbers in the table and in `\FaultHaikuSentence` come from one case pool per model. Require `results/E4_tests.json[model].n` to equal `n_cases` in the corresponding E4 summary for both models at check time, and require the Haiku sentence's accuracies, n and p all to be read from E4_tests.json. If the two models' case sets differ, the fault table states n per model.
2. Rewrite A9(i)'s clause as: no statement that the diagnosis hurts, distracts or degrades the smaller model unless the exact McNemar p < 0.05; otherwise the sentence is the point estimate with n and p only.
3. Amend A7: "significant gain" wording requires Holm-corrected p < 0.05 and a positive mean per-task difference for SPECTRA; a significant negative difference is reported as a loss with the same statistics.