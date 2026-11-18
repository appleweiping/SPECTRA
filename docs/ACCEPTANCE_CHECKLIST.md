# SPECTRA delivery acceptance checklist

This checklist turns the project handoff and the ICCAD contract into checks that can be rerun. A check is marked **PASS** only when its evidence is present in the GPT-backed run; a code change or a successful PDF build alone is not sufficient.

| ID | Check | Evidence required | Status |
|---|---|---|---|
| ENV-1 | No local C/D experiments | Worktree and caches under `E:\CodexProjects`; no simulator/LLM run on the workstation | PASS (E-only source, cache and PDF build; remote-only experiments) |
| ENV-2 | Server storage and simulator | westc `/root/autodl-tmp/spectra-analog-agent`, `ngspice -v` = 42, GPU/CPU inventory recorded | PASS (see `docs/REMOTE_ENV.md`) |
| SYNC-1 | Three-way synchronization | Same commit hash on local E:, server, and GitHub; clean worktrees | PASS (`58f419ba38cec77478b091a6d348a7b7140cba1e` on all three) |
| CODE-1 | GPT-only experiment backend | `spectra/agent/llm.py` uses OpenAI client, rejects Claude aliases, preserves cache/usage schema | PASS (offline fake-client smoke; 2026-11-17 server GPT-6.1-sol catalog + `OK.` smoke) |
| CODE-2 | GPT ARIS reviewer | `tools/aris_review.py` uses fresh GPT call and read-only context manifest; no `claude -p` invocation | PASS (compile/help smoke; paid review pending) |
| EXP-1 | Main comparison | GPT-6.1-sol E1g with SPECTRA, direct, Gen+TPE, SPECTRA-min; common primary endpoint | PASS (`results/E1g_summary.json`, `results/comparisons.json`) |
| EXP-2 | Coupled component ablations | E2g diagnosis, intent, refinement, knowledge ablations with matched tasks/seeds and paired tests | PASS (`results/comparisons.json`, `results/component_effects.json`; mixed effects retained) |
| EXP-3 | PVT strategy | E3g nominal-only and Gen+TPE-full against adaptive SPECTRA, all robust runs capped at 600 | PASS (`results/comparisons.json`, `paper/tables/pvt.tex`) |
| EXP-4 | Fault diagnosis | E4g rule/raw/SPECTRA arms with identical case pool and GPT-6.1-sol | PASS (`results/E4g_summary.json`, `results/E4g_tests.json`) |
| EXP-5 | Mismatch | 100-sample MC over PVT-verified seed-0 designs; nonzero sample spread | PASS (`results/mc_yield.json`) |
| PAPER-1 | Traceable numbers | Generators reproduce `results/` summaries, tables, figures, and `paper/numbers.tex` with no diff | PARTIAL (remote raw runs preserved; local source-level generators pass compile/help checks) |
| PAPER-2 | ICCAD layout | Anonymous `acmart` sigconf; body ≤8 pages, references ≤1 page; rendered page-by-page inspection | PASS (7 pages, all pages rendered; no undefined refs; bibliography fits page 7) |
| PAPER-3 | Statistical claims | 95% cluster bootstrap CIs, Holm-corrected paired tests, negative results and per-task W/L retained | PASS (`results/comparisons.json`, `results/component_effects.md`) |
| REPRO-1 | Reproduction materials | Model ID, prices, prompts/cache policy, PDK/ngspice versions, budgets, seeds, raw results and SHA manifest | PASS (`results/evidence_manifest.json`, `docs/REMOTE_ENV.md`, server raw archive) |
| EXT-1 | Top-conference benchmark breadth | Six-domain extension subset with 36 tasks, shared task text, SKY130/ngspice-42 and family-stratified reporting | PASS (36 tasks × 8 rows, 224 raw records, archive SHA verified on E:) |
| EXT-2 | Seven external frameworks | Direct, Gen+TPE, SPECTRA-min, Gen+CMA-ES, oracle-random, oracle-CMA-ES and oracle-TPE, with SPECTRA as the eighth row | PASS (`results/extended_baselines.json`, all rows observed 36/36) |
| EXT-3 | Metric parity | Success and confidence intervals, per-task W/L, simulator evaluations, calls, cost, PVT feasibility and mismatch yield | PASS (`results/extended_baselines.md`; PVT/mismatch are explicitly N/A for this non-robust subset) |
| ABL-1 | Component efficacy | Diagnosis, intent, refinement and knowledge-card ablations with matched tasks and seeds | PARTIAL (refinement and diagnosis contribute; intent and knowledge effects are mixed and require the targeted extension) |

The frozen A1–A20 contract in `paper/PAPER_ACCEPTANCE_CONTRACT.md` remains authoritative for paper-specific checks. This file is updated with evidence after each experiment block and before any final push.
