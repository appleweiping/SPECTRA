# SPECTRA delivery acceptance checklist

This checklist turns the project handoff and the ICCAD contract into checks that can be rerun. A check is marked **PASS** only when its evidence is present in the GPT-backed run; a code change or a successful PDF build alone is not sufficient.

| ID | Check | Evidence required | Status |
|---|---|---|---|
| ENV-1 | No local C/D experiments | Worktree and caches under `E:\CodexProjects`; no simulator/LLM run on the workstation | PASS (layout); pending run audit |
| ENV-2 | Server storage and simulator | westc `/root/autodl-tmp/spectra-analog-agent`, `ngspice -v` = 42, GPU/CPU inventory recorded | PASS (see `docs/REMOTE_ENV.md`) |
| SYNC-1 | Three-way synchronization | Same commit hash on local E:, server, and GitHub; clean worktrees | PASS for current commit |
| CODE-1 | GPT-only experiment backend | `spectra/agent/llm.py` uses OpenAI client, rejects Claude aliases, preserves cache/usage schema | PASS (offline fake-client smoke; GPT-6.1-sol server smoke pending) |
| CODE-2 | GPT ARIS reviewer | `tools/aris_review.py` uses fresh GPT call and read-only context manifest; no `claude -p` invocation | PASS (compile/help smoke; paid review pending) |
| EXP-1 | Main comparison | GPT-6.1-sol E1g with SPECTRA, direct, Gen+TPE, SPECTRA-min; common primary endpoint | NOT RUN |
| EXP-2 | Coupled component ablations | E2g diagnosis, intent, refinement, knowledge ablations with matched tasks/seeds and paired tests | NOT RUN |
| EXP-3 | PVT strategy | E3g nominal-only and Gen+TPE-full against adaptive SPECTRA, all robust runs capped at 600 | NOT RUN |
| EXP-4 | Fault diagnosis | E4g rule/raw/SPECTRA arms with identical case pool and GPT-6.1-sol | NOT RUN |
| EXP-5 | Mismatch | 100-sample MC over PVT-verified seed-0 designs; nonzero sample spread | NOT RUN |
| PAPER-1 | Traceable numbers | Generators reproduce `results/` summaries, tables, figures, and `paper/numbers.tex` with no diff | NOT RUN |
| PAPER-2 | ICCAD layout | Anonymous `acmart` sigconf; body ≤8 pages, references ≤1 page; rendered page-by-page inspection | NOT RUN |
| PAPER-3 | Statistical claims | 95% cluster bootstrap CIs, Holm-corrected paired tests, negative results and per-task W/L retained | NOT RUN |
| REPRO-1 | Reproduction materials | Model ID, prices, prompts/cache policy, PDK/ngspice versions, budgets, seeds, raw results and SHA manifest | PARTIAL |

The frozen A1–A20 contract in `paper/PAPER_ACCEPTANCE_CONTRACT.md` remains authoritative for paper-specific checks. This file is updated with evidence after each experiment block and before any final push.
