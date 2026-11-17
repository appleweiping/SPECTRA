**Verdict first: the contract is not acceptable as written.** The evidence inventory is in better shape than most at this stage, and several assertions are fine as they stand. But four things are wrong with the contract itself: a headline framing that the inventory contradicts, a scoring protocol whose validity no assertion checks, traceability assertions with gaps that the current draft already falls through, and claims in the draft that no results file can back.

## Assertions that are fine

- **A1, A2** are checkable and sensible. The current log shows 7 pages, no overfull boxes, one font warning.
- **A5** holds today. All five distinctive lines of the Fig. 2 listing appear in the stored opamp-09 seed-0 run, whose metadata is tier 3, nominal, matching the caption. Keep it. Add one word: the caption must also state that the listing is the run's final program, since the caption interprets it as containing corrections from earlier diagnoses.
- **A13, A14, A15, A16** are fine. A16 should additionally require the LLM access path to be stated, since the setup text says Claude Code CLI with default sampling and responses are cached per run tag and call index. That affects reproducibility more than the CMA-ES settings do.
- **A9** is fine but incomplete. The narrative itself lists a third negative that must appear: the D06 low-noise op-amp, where SPECTRA loses 2/3 to 3/3. Add per-task losses to each baseline, which the existing WL macros already carry.

## Assertions that need a checkable rewrite

**A6 and the word "pre-registered".** The draft uses "pre-registered primary endpoint" in the intro, setup and results. The repository shows where it came from: review round 1, held when E1 was about 35 percent complete and the reviewer's first finding was "headline not significant." The endpoint was fixed in response to that, after interim results. The FINAL_PROPOSAL contains no primary endpoint and states H1 "across 12 families." Today the primary comparison rests on 16 of 61 primary tasks and 4 of 12 families. A6 must require either a dated record predating any E1 analysis, which does not exist, or the wording "pre-specified at interim review round 1, before the remaining E1 runs," plus the coverage: common primary tasks out of 61, and families covered out of 12. The 61 also needs stating, because the endpoint's robust set includes 3 designer-tier robust tasks on top of the 19 certified ones.

**A3 is too narrow and has no freshness check.** It covers abstract, intro and experiments text, but result numbers also sit in the method section (prediction accuracy, intent-variable counts) and bench section (frontier-refinement count). The current experiments text contains a hand-typed result number, "classes with at most 29 cases," while the fault table shows classes of 41 and 44. And the committed numbers file is stale against the committed summary right now:

| quantity | numbers.tex | E1_summary.json |
|---|---|---|
| common tasks | 24 | 31 |
| primary tasks | 9 | 16 |
| SPECTRA primary | 100.0% | 92.7% |

A3 must cover every section and require that re-running analyze, paper_numbers, make_tables and make_figures at check time reproduces the committed files with no diff.

**A4 misnames generators and misses a definition clash.** The bench composition table comes from bench_stats.py, and the families table is hand-written. More importantly, "Robust" means different things in the table generator and the figure generator: the table counts designer-robust tasks under Robust, the figure counts them under Designer. A4 must name each table's generator and require one shared tier-group definition across analyze, tables and figures.

**A10 and the table captions.** The main-table caption hard-codes "3 seeds for SPECTRA/AnalogCoder-style, 2–3 for the others," and the ablation caption hard-codes "3 seeds." The executed protocol is 2 seeds on T3, 1 to 2 on robust, 1 elsewhere. A10 must require that seed counts in every caption are computed from the runs, as a per-method range, not typed.

**A11 and the PVT failure file.** The script that produces it pools every experiment and method under results/raw, including ablation arms and Haiku runs. The draft says "across the 19 returned designs" with no method named. The draft also makes three qualitative claims with no macro: SF and SS most frequent, cold fails as often as hot, low supply dominates. The file gives corner counts of 67, 62, 60, 51, 47 and temperature counts of 106 cold versus 92 hot. SS versus FS is a two-count margin and cold fails more than hot, not "as often." A11 must require the file to record which runs it pooled, the text to name them, and these three statements to be macro-generated or removed.

**A7** is fine as a rule but must explicitly cover the conclusion and the abstract's main-claim macro. "Makes end-to-end analog synthesis reliable where it matters" is a comparative claim, and the current paired permutation p against the AnalogCoder-style baseline on the primary endpoint is 0.13.

**A8** should also require stating what SPECTRA alone receives: the gm/Id LUT API. Baselines get the PDK sheet and cards, not the LUT.

## Missing assertions

**Robust-budget truncation is not a re-scoring, and nothing checks it.** The iteration prompt tells the LLM its remaining simulation budget. A run started under the 1200 cap therefore showed the model budget numbers a 600-cap run never shows, so "success iff succeeded within 600" is not equivalent to having run at 600. In E1 today, 46 robust run files carry the 1200 cap and 29 carry 600. A12 only asks that the change be named. Add an assertion: the paper reports, per method, how many robust runs ran under each cap, states the prompt difference, and gives the primary-endpoint result restricted to native 600-cap runs alongside the pooled one, or the truncated runs are re-run.

**Mismatch Monte Carlo has no results file.** The abstract claims verification "plus mismatch," the bench section describes a 100-sample MC, and the PVT table generator reads a yield file that does not exist. Add: either the yield file exists and feeds the table, or the mismatch claim leaves the abstract and bench section.

**Wall-clock and tokens.** The bench section says the paper reports tokens, cost and wall-clock time. No table does. Add: every quantity the metrics paragraph promises appears in a table, or is struck from the paragraph.

**Dropped hypotheses need scope assertions, not just a limitations list.** H4 compared adaptive corner selection against refining on all corners each step; that arm is dropped, so the paper may not claim adaptive selection is cheaper than all-corner refinement, only cheaper than TT-only design and Gen+TPE-full. H5 claimed gains across backbones; only Haiku remains, single seed, on a subset, so no "gains hold across backbones" claim. H6 claimed infeasibility declaration; controls were withdrawn, and declared-infeasible counts are zero in E1, so the Declare-Infeasible action may be described but no honesty claim made, and the zero count reported.

**Mid-E1 method revision.** SPECTRA and SPECTRA-min results before the harness fix were deleted and re-run after a failure on D03 was inspected; baselines were kept. A12 must name this, since it is method development on the evaluation set, however benign.

**E3 has not started.** No E3 raw runs exist. A11 needs a fallback: if E3 is incomplete at submission, C4 leaves the abstract and the PVT section reports only what exists.

One deviation from FINAL_PROPOSAL needs no assertion: 17 PVT conditions became 45, which is a strengthening and is what the paper describes.

CONTRACT_ACCEPTED: no

1. Rewrite A6: replace "pre-registered" with "pre-specified at interim review round 1, before the remaining E1 runs," and require the headline to state common primary tasks out of 61 and families covered out of 12.
2. Extend A3 to all sections and add a freshness check: regenerating numbers, tables and figures at check time produces no diff against the committed files.
3. Rewrite A4 to name the true generator of each table, exempt the hand-written families table, and require one shared tier-group definition across analyze, make_tables and make_figures.
4. Amend A10 so every caption's seed count is computed from the runs as a per-method range.
5. Amend A11: the PVT failure file records the runs it pooled, the text names them, and the corner, temperature and supply statements are macro-generated or removed; add the E3-incomplete fallback.
6. Add an assertion on robust-budget truncation: per-method counts of 1200-cap versus 600-cap runs, disclosure of the budget shown in the prompt, and the primary result on native 600-cap runs alongside the pooled result, or re-runs.
7. Add an assertion that the mismatch MC claim is backed by a yield results file feeding the PVT table, or is removed from abstract and bench section.
8. Add an assertion that every quantity promised in the metrics paragraph appears in a table.
9. Add scope assertions for H4, H5 and H6: no all-corner cost comparison, no cross-backbone generality claim, no infeasibility-detection claim, and the declared-infeasible count reported.
10. Extend A12 with the mid-E1 harness fix and selective re-run of SPECTRA arms.
11. Extend A7 to the conclusion and the abstract macro; extend A8 to state that only SPECTRA receives the LUT API; extend A9 with per-task losses including D06.