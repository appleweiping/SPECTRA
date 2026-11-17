# PAPER ACCEPTANCE CONTRACT — SPECTRA (ICCAD)

status: proposed (round 1 revision; round-1 review: paper/.contract_r1.md)
Inputs: NARRATIVE_REPORT.md, paper/ (draft), results/, EXPERIMENT_LOG.md.
Each assertion is checked against the compiled `paper/main.pdf`, its sources and the named files.

## Venue / form
A1. `acmart` sigconf with `review,anonymous`; body (text, figures, tables) ends on or before page 8, references occupy at
    most one further page; no author names, affiliations, acknowledgements or non-anonymous URLs.
A2. `paper/main.log` has no undefined references/citations/font shapes and no overfull hbox wider than 5 pt.

## Traceability and freshness
A3. Every result number in every section (abstract, intro, bench, method, experiments, conclusion) is a macro from
    `paper/numbers.tex` or a cell of a generated table. Hand-typed numbers are allowed only for constants fixed by
    construction (45 PVT conditions, budgets, LUT grid, CMA-ES settings, family count). Freshness: running
    `analyze --exp E1`, `scripts.comparisons`, `scripts.pvt_failures`, `scripts.prediction_accuracy`, `scripts.make_tables`,
    `scripts.make_figures`, `scripts.paper_numbers` at check time reproduces the committed `paper/numbers.tex`,
    `paper/tables/*.tex` (except the hand-written `families.tex`) and `results/*.json` with no diff.
A4. Generators: `main/fault/ablation/pvt/scaling.tex` ← `scripts/make_tables.py` (ablation/pvt/scaling via
    `results/comparisons.json` from `scripts/comparisons.py`); `bench_stats.tex` ← `scripts/bench_stats.py`;
    `families.tex` hand-written (benchmark description, no results); data figures ← `scripts/make_figures.py`. Tier groups
    are defined once (`TIER_GROUPS` in `scripts/analyze.py`: Robust = every robust task incl. designer-written robust ones;
    T1/T2/T3/Designer = nominal tasks) and used by the summary, the main table and the tier figure; all E1 statistics,
    tables and figures use the common task set (`load_common`).
A5. Fig. 2 is a verbatim, abridged excerpt (elisions marked `...`) of the *final* program of
    `results/raw/E1/spectra/opamp-09/s0.json`; the caption names the tier, experiment and that it is the run's final program.

## Headline claims and scope
A6. The primary endpoint (T3 ∪ robust) is described as fixed at an interim review (after about a third of the E1 runs),
    never as "pre-registered". The headline reports it with 95% cluster-bootstrap CIs and Holm-corrected paired tests and
    states the number of common primary tasks out of the 61 primary tasks and the families covered out of 12.
A7. Every comparative claim ("SPECTRA beats/outperforms/is more reliable than X") anywhere — abstract main-claim macro,
    intro, experiments, conclusion — is backed by Holm-corrected p < 0.05 on the primary endpoint; otherwise it is a point
    estimate with CI and per-task wins/losses, without "significant", "reliable", "outperforms".
A8. Setup states: same LLM (Opus 5.5 via the Claude Code CLI, default sampling), same task text, PDK sheet and knowledge
    cards, identical budgets (12 calls; 300 / 600 condition-evaluations); only SPECTRA (and its ablations) gets the
    gm/Id LUT API; responses are cached per (prompt, run tag).
A9. Negative results appear in the intro and experiments: (i) diagnosis does not improve fault localisation in isolation
    (E4) and degrades it for Haiku; (ii) intent programs mispredict second-order metrics; (iii) per-task losses of SPECTRA
    against each baseline (W/L macros), including the designer-tier low-noise op-amp if SPECTRA still loses it.
A10. Ablation text names the matched task count and the seeds per task (computed, from the table caption); a component
    is called "necessary"/"essential" only with a paired-test-supported difference; otherwise "contributes" (point
    estimate and W/L) or "no measurable effect".
A11. PVT section: SPECTRA vs TT-only design vs Gen+TPE-full (and E1 methods) on the same robust subset tasks (seed 0),
    with simulation cost; failing-condition statements come only from the generated `\PVTFailSentence` over the file's
    recorded run list (E1 final designs of the four main methods). Fallback: if E3 is incomplete at submission, the
    abstract makes no PVT-strategy claim and the section reports only completed arms.
A12. Robust runs: no run is scored by truncation — every robust run in `results/raw/E{1,2,3,5}` has `budget_sims == 600`
    (1200-cap runs archived in `results/raw_cap1200_archive/` and re-run); the setup text says so.
A13. Mismatch: either `results/E1_mc_yield.json` exists and feeds the yield column of the PVT table and the text, or the
    mismatch claims are removed from abstract, intro and bench section (and the sample count matches the file).
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
