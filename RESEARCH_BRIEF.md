# Research Brief

## Problem Statement
LLM agents for analog circuit design (AnalogCoder AAAI'25, AnalogCoder-Pro, AnalogXpert, Artisan DAC'24,
AmpAgent, ADO-LLM, AnaFlow, ...) have shown that LLMs can emit plausible topologies and, separately,
assist sizing. However, the end-to-end problem a designer faces — *natural-language spec → topology →
device sizing → verification that quantitative specs hold under process/voltage/temperature (PVT)
variation in a real PDK* — remains largely unsolved. Typical evaluation uses level-1 square-law models,
5 V supplies, and functional pass/fail checks (e.g., "differential gain > 1e-5"), which hides the real
difficulty: LLMs are weak at numeric sizing, raw simulator output is a poor feedback signal, and nominal
designs routinely break at corners.

## Background
- Field: EDA / analog design automation; LLM agents.
- Sub-area: spec-driven, simulation-in-the-loop analog synthesis (topology + sizing).
- Key papers: AnalogCoder, AnalogCoder-Pro, AnalogGenie (ICLR'25), Artisan, AmpAgent, ADO-LLM, AnaFlow,
  AnalogGym, LaMAGIC, CktGNN (see /home/user/refs/LIT_SURVEY.md when available).

## Constraints
- Compute: 4 CPU cores, 15 GB RAM, no GPU. Simulator: ngspice-42. PDK: SkyWater SKY130 (open, BSIM4,
  5 process corners). LLM access: `claude -p` (Opus 5.5 / Sonnet 5.5 / Haiku 5.5 / Fable 5.1).
- Target venue: ICCAD (IEEE double-column conference format).
- Training-free (no fine-tuning possible on this hardware).

## What I'm Looking For
- [x] New research direction / system: end-to-end agentic analog synthesis with quantitative,
      PVT-robust spec satisfaction on a real open PDK, plus a benchmark that is larger and harder than
      prior LLM-analog benchmarks.

## Domain Knowledge
- gm/Id methodology turns sizing into choosing inversion level (gm/Id), L, and branch currents; the
  mapping to W is deterministic given LUTs. LLMs know these heuristics qualitatively.
- Designers debug with operating-point regions, Vds–Vdsat margins, pole/zero locations and sensitivities,
  not with raw waveforms.
- Robustness: worst case usually at SS/hot or FF/cold; designing with margin at TT is insufficient.

## Non-Goals
- Layout generation / parasitic extraction (mentioned as future work).
- Fine-tuning LLMs.
