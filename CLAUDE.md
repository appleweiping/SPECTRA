# Project: SPECTRA — end-to-end agentic analog circuit synthesis (ICCAD submission)

## Pipeline Status

```yaml
stage: handoff   # idle | idea-discovery | implementation | training | review | paper | handoff
idea: "Spec-to-robust-netlist analog agent with design-intent (gm/Id) programs, causal diagnosis, PVT-aware refinement"
contract: "refine-logs/FINAL_PROPOSAL.md; paper/PAPER_ACCEPTANCE_CONTRACT.md (frozen after 3 rounds)"
current_branch: "main"
baseline: "AnalogCoder-style codegen agent; AnalogCoder-Pro-style Gen+TPE (+Gen+TPE-full); SPECTRA-min"
training_status: "GPT-6.1-sol is the active experiment backend; historical Claude results remain supplemental and isolated."
language: en
active_tasks: []
next: "Read HANDOFF.md. Executor, experiment LLM and ARIS reviewer switch to GPT-family models (HANDOFF section 0.5)."
last_updated: "2026-11-17"
```

## Project Constraints
- ARIS workflow (https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep): W1 idea-discovery ->
  W1.5 experiment-bridge -> W2 auto-review-loop -> W3 paper-writing; artifacts in canonical locations.
- Executor, experiment LLM, and reviewer use the GPT family after the handoff (current default: `gpt-6.1-sol`).
  `tools/aris_review.py` uses the OpenAI Python client and a bounded read-only artifact bundle. Claude is disabled;
  same-family review remains provisional.
- Venue: ICCAD (2026 CFP: ACM proceedings template `acmart` sigconf, <=8 pages incl. figures/tables + 1 page references, double blind, anonymous code via anonymous.4open.science). Keep LaTeX portable to IEEEtran.
- All numbers in the paper must come from files in results/; no fabricated results.

## Non-Goals
- Layout, extraction, fine-tuning.

## Compute Budget
- 4 CPU cores, ngspice-42, GPT calls via the OpenAI Python client (track tokens / USD in results/llm_usage.jsonl).
