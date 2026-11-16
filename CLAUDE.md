# Project: SPECTRA — end-to-end agentic analog circuit synthesis (ICCAD submission)

## Pipeline Status

```yaml
stage: idea-discovery   # idle | idea-discovery | implementation | training | review | paper
idea: "Spec-to-robust-netlist analog agent with design-intent (gm/Id) programs, causal diagnosis, PVT-aware refinement"
contract: "refine-logs/FINAL_PROPOSAL.md"
current_branch: "main"
baseline: "AnalogCoder-style codegen agent; netlist ReAct agent; BO/CMA-ES sizing on raw W/L"
training_status: idle
language: en
active_tasks: [literature-survey, repo-analysis, sim-substrate]
next: "finish LUTs + testbenches; write IDEA_REPORT; reviewer gate"
last_updated: "2026-11-16"
```

## Project Constraints
- ARIS workflow (https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep): W1 idea-discovery ->
  W1.5 experiment-bridge -> W2 auto-review-loop -> W3 paper-writing; artifacts in canonical locations.
- Executor: Claude Code (Opus 5.5). Reviewer: fresh `claude -p` sessions (Fable 5.1 primary, Opus 5.5
  secondary) via tools/aris_review.py; traces in .aris/traces/. Same-family => provisional acceptance.
- Venue: ICCAD — IEEEtran conference, 8 pages content (+ references as allowed by CFP), double blind.
- All numbers in the paper must come from files in results/; no fabricated results.

## Non-Goals
- Layout, extraction, fine-tuning.

## Compute Budget
- 4 CPU cores, ngspice-42, LLM via `claude -p` (track tokens / USD in results/llm_usage.jsonl).
