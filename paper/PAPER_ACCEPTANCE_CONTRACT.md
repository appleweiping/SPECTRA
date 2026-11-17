# PAPER ACCEPTANCE CONTRACT — SPECTRA (ICCAD)

status: frozen after 3 negotiation rounds (reviews: paper/.contract_r1.md, .contract_r2.md, .contract_r3.md). Round 3 ended
`CONTRACT_ACCEPTED: no` with three demands; all three were adopted verbatim below (A3/A9 E4 pool equality, A9 claim rule,
A7 sign rule), so no item is disputed. The reviewer did not re-confirm (round limit reached); the Phase-6 gate grades
this version.
Inputs: NARRATIVE_REPORT.md, paper/ (draft), results/, EXPERIMENT_LOG.md.
Each assertion is checked against the compiled `paper/main.pdf`, its sources and the named files.

## Venue / form
A1. `acmart` sigconf with `review,anonymous`; body (text, figures, tables) ends on or before page 8, references occupy at
    most one further page; no author names, affiliations, acknowledgements or non-anonymous URLs.
A2. `paper/main.log` has no undefined references/citations/font shapes and no overfull hbox wider than 5 pt.

## Traceability and freshness
A3. Every result number in every section (abstract, intro, bench, method, experiments, conclusion) is a macro from
    `paper/numbers.tex` or a cell of a generated table; the abstract's main claim is the generated macro `\AbsMainClaim`.
    Hand-typed numbers are allowed only for constants fixed by construction (45 PVT conditions, budgets, LUT grid, CMA-ES
    settings, family count). Freshness: running, in this order, the commands below at check time reproduces exactly the
    listed committed files (no diff):
    - `python -m scripts.analyze --exp E1` → `results/E1_summary.json`
    - `python -m scripts.comparisons` → `results/comparisons.json`
    - `python -m scripts.pvt_failures` → `results/pvt_failure_conditions.json`
    - `python -m scripts.failure_analysis E1` → `results/E1_failures.json`
    - `python -m scripts.prediction_accuracy E1 spectra` → `results/E1_spectra_prediction_accuracy.json`
    - `python -m scripts.e4_tests` → `results/E4_tests.json`
    - `python -m scripts.make_tables` → `paper/tables/{main,fault,ablation,pvt,scaling}.tex`
    - `python -m scripts.bench_stats` → `paper/tables/bench_stats.tex`
    - `python -m scripts.make_figures` → `paper/figs/E1_{tiers,anytime,anytime2,families}.pdf` (content, not bytes)
    - `python -m scripts.paper_numbers` → `paper/numbers.tex`
    Files produced by long-running experiments (E4 summaries, `results/mc_yield.json`, raw runs) are inputs, not checked
    for freshness.
A4. Generators as listed in A3; `families.tex` is hand-written (benchmark description, no results). Tier groups are
    defined once (`TIER_GROUPS` in `scripts/analyze.py`: Robust = every robust task incl. designer-written robust ones;
    T1/T2/T3/Designer = nominal tasks) and used by the summary, the main table and the tier figure. All E1 statistics,
    tables, figures, the failure analysis and the prediction-accuracy analysis use the common task set of the four main
    methods (`load_common`); prediction accuracy uses SPECTRA's runs within it.
A5. Fig. 2 is a verbatim, abridged excerpt (elisions marked `...`) of the *final* program of
    `results/raw/E1/spectra/opamp-09/s0.json`; the caption names the tier, experiment and that it is the run's final program.

## Headline claims and scope
A6. The primary endpoint (T3 ∪ robust) is described as fixed at an interim review (after about a third of the E1 runs),
    never as "pre-registered". The headline reports it with 95% cluster-bootstrap CIs and Holm-corrected paired tests and
    states the number of common primary tasks out of the 61 primary tasks and the families covered out of 12.
A7. Every comparative claim ("SPECTRA beats/outperforms/is more reliable than X") anywhere — abstract, intro,
    experiments, conclusion — is backed by Holm-corrected p < 0.05 on the primary endpoint; otherwise it is a point
    estimate with CI and per-task wins/losses, without "significant", "reliable", "outperforms". `\AbsMainClaim` is
    emitted by `scripts/paper_numbers.py`, which chooses the wording per baseline: "significant gain" requires Holm-corrected
    p < 0.05 and a positive mean per-task difference for SPECTRA; a significant negative difference is reported as a loss
    with the same statistics.
A8. Setup states: same LLM (Opus 5.5 via the Claude Code CLI, default sampling), same task text, PDK sheet and knowledge
    cards, identical budgets (12 calls; 300 / 600 condition-evaluations); only SPECTRA (and its ablations) gets the
    gm/Id LUT API; responses are cached per (prompt, run tag).
A9. Negative results appear in the intro and experiments: (i) diagnosis does not improve fault localisation in isolation
    (E4). The Haiku accuracies, n and p in `\FaultHaikuSentence` are all read from `results/E4_tests.json`, and
    `E4_tests.json[model].n` equals `n_cases` of the corresponding E4 summary for both models at check time (else the
    fault table states n per model). No statement that the diagnosis hurts, distracts or degrades the smaller model
    unless the exact McNemar p < 0.05 (and the sign is negative); otherwise only the point estimate with n and p; (ii) intent programs mispredict second-order metrics; (iii) per-task losses of SPECTRA
    against each baseline (W/L macros), including the designer-tier low-noise op-amp if SPECTRA still loses it.
A10. Ablation text names the matched task count and the seeds per task (computed, from the table caption); a component
    is called "necessary"/"essential" only with a paired-test-supported difference; otherwise "contributes" (point
    estimate and W/L) or "no measurable effect".
A11. PVT section: SPECTRA vs TT-only design vs Gen+TPE-full (and E1 methods) on the same robust subset tasks (seed 0),
    with simulation cost; failing-condition statements come only from the generated `\PVTFailSentence` over the file's
    recorded run list (E1 final designs of the four main methods). Fallback: if E3 is incomplete at submission, the
    abstract makes no PVT-strategy claim and the section reports only completed arms.
A12. Robust runs: no run is scored by truncation — every robust run in `results/raw/E{1,2,3,5}` has `budget_sims == 600`
    (`analyze.py` excludes others). Robust tasks use seed 0 in E1, E3 and E5 and seeds 0–1 in E2; 1200-cap runs were
    archived in `results/raw_cap1200_archive/`, seed-0 (E1/E5) and seed-0/1 (E2) runs re-run, archived higher E1/E5 seeds
    dropped; the setup text says so. A robust task whose seed-0 runs are incomplete at check time leaves the common set
    automatically and the reported n (`\NCommon`, `\NPrimaryTasks`, block sizes) reflects it.
A13. Mismatch: `results/mc_yield.json` (schema `{"n_samples", "yield": {method: {"task/s0": y}}, "max_rel_spread": {...}}`,
    written by `scripts/mc_yield.py`) exists, feeds the yield column of the PVT table and `\MCSentence`; the text states
    its pool (PVT-verified seed-0 designs of E1's four methods and E3's two arms) and the sample count matches the file;
    every analysed design has `max_rel_spread > 0` (samples differ). Otherwise the mismatch claims are removed from the
    intro, bench section and PVT section. The abstract makes no mismatch claim.
A14. Every quantity promised in the metrics paragraph (success with CIs, sims and calls to success, tokens, cost) appears
    in a table; wall-clock is explicitly not reported.

## Honesty / limitations / dropped hypotheses
A15. Limitations name: schematic level only; template-derived certified tier; 1–3 seeds per task (tiered); dropped arms
    (Gen+CMA-ES, all-corner strategy, template oracle, third backbone, infeasible-spec controls); mid-E1 harness fix with
    re-run of SPECTRA/SPECTRA-min only; same-family executor and reviewer.
A16. Scope of dropped hypotheses: no claim that adaptive worst-condition selection is cheaper than all-corner refinement
    (only vs TT-only design and Gen+TPE-full); no claim that gains hold across backbones (only Haiku vs Opus, one seed);
    no infeasibility-detection claim, and the number of SPECTRA runs ending in Declare-Infeasible is reported.
A17. Baselines are called "AnalogCoder-style" / "AnalogCoder-Pro-style" re-implementations, never the original systems,
    and their shared resources with SPECTRA are listed.
A18. Benchmark description gives task counts per family and tier consistent with `data/bench/*.jsonl`, and how
    feasibility certificates are produced and re-verified.

## Completeness
A19. Related work positions against AnalogCoder, AnalogCoder-Pro, ≥1 PVT-aware LLM sizing method, ≥1 gm/Id automation
    method and ≥1 analog-LLM benchmark; `paper/CITATION_AUDIT.md` is PASS for the final bib.
A20. Reproducibility: PDK, simulator version, LUT grid, CMA-ES settings, budgets, LLM access path and caching are
    stated; code and benchmark release promised via an anonymous link.
