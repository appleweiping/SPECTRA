# AUTO_REVIEW (ARIS W2) — SPECTRA

Reviewer: Fable 5.1 via fresh `claude -p` (read-only tools), executor Opus 5.5 → review_independence = same-family,
acceptance_status = provisional. Traces: `.aris/traces/auto-review-loop/`.

## Round 1 (interim; E1 ≈35% complete) — score 5/10, verdict not-ready
Full text: `review-stage/ROUND1_REVIEW.md`.

| # | Reviewer finding | Action | Status |
|---|---|---|---|
| W1 | Headline not significant; robust number from 3 tasks; one SPECTRA "failure" was a harness crash (div-by-zero in `diagnose.py`); methods compared on different task sets | Fixed the bug and re-ran the run (cached LLM calls); analysis restricted to the common task set; pre-registered primary endpoint = T3 ∪ robust with exact sign / paired-permutation tests (Holm); E1 queue reordered to finish T3/robust tasks first; robust-only number removed from intro | done; E1 running |
| W2 | Oracle-unmet controls broken (2 physically impossible, 2 solved by all) | Control tier v0 withdrawn from benchmark and paper (runs moved to `results/raw/E1_controls_v0`) | done |
| W3 | E4 shows diagnosis does not help localisation; E4 evidence ≠ agent's diagnosis | Text rewritten as an explicit null result with the caveat; C2's end-to-end value deferred to E2 "w/o diagnosis" (3 seeds, run first in E2) | text done; E2 queued |
| W4 | Gen+TPE capped at 3 calls and fixed corners | Setup text states the design (AnalogCoder-Pro's ≤3 regenerations; direct is call-bound); added `genbo_full` (≤12 regenerations + adaptive PVT corners) run on all robust tasks in E3 | variant implemented; queued |
| W5 | Saturation of T1/T2/D; knowledge cards mirror templates; frontier refinement moved 31/58 | T3 ∪ robust primary endpoint; no-card arms `spectra_noknow`/`direct_noknow` on subset T3 tasks queued; 31/58 stated in paper; knowledge.py header corrected | done / queued |
| W6 | Unsupported numbers (157.7 kHz, "3–5×", 68.7 dB program attributed to the agent) | Validation recorded in `results/pilot/testbench_validation.json`; "3–5×" replaced by measured 10 intent vs 18 raw variables; the hand-written pilot program claim replaced by aggregate prediction accuracy over 78 agent-written programs (`results/E1_spectra_prediction_accuracy.json`) | done |
| W7 | Discarded seed-2 runs | All completed seeds now used (per-task means) | done |
| W8 | Statistics | exact sign + permutation tests, per-task W/L, cluster bootstrap | done |
| W9 | Writing/template | ACM header set to ICCAD '27, "independent" → "outside the agent's budget", PANDA claim softened, fonts fixed | done |
