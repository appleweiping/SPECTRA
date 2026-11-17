# Project: SPECTRA — end-to-end agentic analog circuit synthesis (ICCAD submission)

## Pipeline Status

```yaml
stage: handoff   # idle | idea-discovery | implementation | training | review | paper | handoff
idea: "Spec-to-robust-netlist analog agent with design-intent (gm/Id) programs, causal diagnosis, PVT-aware refinement"
contract: "refine-logs/FINAL_PROPOSAL.md; paper/PAPER_ACCEPTANCE_CONTRACT.md (frozen after 3 rounds)"
current_branch: "main"
baseline: "AnalogCoder-style codegen agent; AnalogCoder-Pro-style Gen+TPE (+Gen+TPE-full); SPECTRA-min"
training_status: "ALL EXPERIMENTS STOPPED 2026-11-17 05:00 UTC by user request (handoff). Claude quota exhausted."
language: en
active_tasks: []
next: "Read HANDOFF.md. Executor, experiment LLM and ARIS reviewer switch to GPT-family models (HANDOFF section 0.5)."
last_updated: "2026-11-17"
```

## Project Constraints
- ARIS workflow (https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep): W1 idea-discovery ->
  W1.5 experiment-bridge -> W2 auto-review-loop -> W3 paper-writing; artifacts in canonical locations.
- Executor until 2026-11-17: Claude Code (Opus 5.5); reviewer: fresh `claude -p` sessions (Fable 5.1) via
  tools/aris_review.py. FROM THE HANDOFF ON: executor, experiment LLM and reviewer are GPT-family models
  (Claude quota exhausted) -- see HANDOFF.md section 0.5. Same-family review => provisional acceptance.
- Venue: ICCAD (2026 CFP: ACM proceedings template `acmart` sigconf, <=8 pages incl. figures/tables + 1 page references, double blind, anonymous code via anonymous.4open.science). Keep LaTeX portable to IEEEtran.
- All numbers in the paper must come from files in results/; no fabricated results.

## Non-Goals
- Layout, extraction, fine-tuning.

## Compute Budget
- 4 CPU cores, ngspice-42, LLM via `claude -p` (track tokens / USD in results/llm_usage.jsonl).
