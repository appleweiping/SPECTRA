# Project: SPECTRA — end-to-end agentic analog circuit synthesis (ICCAD submission)

## Pipeline Status

```yaml
stage: paper   # idle | idea-discovery | implementation | training | review | paper
idea: "Spec-to-robust-netlist analog agent with design-intent (gm/Id) programs, causal diagnosis, PVT-aware refinement"
contract: "refine-logs/FINAL_PROPOSAL.md; paper/PAPER_ACCEPTANCE_CONTRACT.md (frozen after 3 rounds)"
current_branch: "main"
baseline: "AnalogCoder-style codegen agent; AnalogCoder-Pro-style Gen+TPE (+Gen+TPE-full); SPECTRA-min"
training_status: "final experiments running (E1 seed0 primary + 600-cap re-runs, E1 seed1 T3, E2, E3, E5, MC yield)"
language: en
active_tasks: [E1-finish, E2-E3-E5, rerun-600, mc-yield, W2-round2, claim-audit, kill-argument]
next: "bash scripts/finalize_paper.sh when all *_DONE flags exist; write ablation/PVT/scaling interpretation; W2 r2; audits"
last_updated: "2026-11-17"
```

## Project Constraints
- ARIS workflow (https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep): W1 idea-discovery ->
  W1.5 experiment-bridge -> W2 auto-review-loop -> W3 paper-writing; artifacts in canonical locations.
- Executor: Claude Code (Opus 5.5). Reviewer: fresh `claude -p` sessions (Fable 5.1 primary, Opus 5.5
  secondary) via tools/aris_review.py; traces in .aris/traces/. Same-family => provisional acceptance.
- Venue: ICCAD (2026 CFP: ACM proceedings template `acmart` sigconf, <=8 pages incl. figures/tables + 1 page references, double blind, anonymous code via anonymous.4open.science). Keep LaTeX portable to IEEEtran.
- All numbers in the paper must come from files in results/; no fabricated results.

## Non-Goals
- Layout, extraction, fine-tuning.

## Compute Budget
- 4 CPU cores, ngspice-42, LLM via `claude -p` (track tokens / USD in results/llm_usage.jsonl).
