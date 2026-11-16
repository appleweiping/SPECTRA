# IDEA_REPORT — SPECTRA (W1 /idea-discovery output)

Direction: end-to-end LLM-agent analog circuit generation (NL spec → topology → sizing → verification), ICCAD.
Inputs: `RESEARCH_BRIEF.md`, `docs/refs/LIT_SURVEY.md` (≈60 papers, 2023–2026, verified), `docs/refs/REPO_ANALYSIS.md`
(AnalogGym/-Opt, AnalogCoder(-Pro), AnalogGenie, EEsizer, ...), pilot code in `spectra/`.

## Landscape (condensed from LIT_SURVEY §0, §4, §5)
- Topology-generation agents (AnalogCoder 24 tasks, AnalogAgent 30, MenTeR) are evaluated with Level-1 square-law
  MOSFETs and functional pass/fail checks.
- Spec-driven topology+sizing systems (AnalogCoder-Pro: single scalar FoM with BPTM-45; AnalogSAGE: 10 op-amp tasks;
  AaLLM: 24 op-amp spec targets; SAFTAC: fine-tuned 8B model) verify at the **nominal TT corner only** (Table G1).
- PVT/MC-aware LLM work (AnalogScout, OPERA, SABLE) only **sizes a given topology**, on 2–6 circuits.
- Long-Horizon Analog Design Bench: frontier agents fail mostly on *electrical closure* (8–78% full-spec pass).
- No work attributes spec violations to devices/poles and maps them to design-intent changes (Gap 4); budgets are
  accounted inconsistently (Gap 3).

## Candidate ideas (generated → filtered)

### Idea 1 (SELECTED): SPECTRA — design-intent programs + causal diagnosis + PVT-aware refinement, with a multi-family robust benchmark
- **Core claim.** LLMs are good at *qualitative* analog reasoning (topology choice, inversion level, current budgeting,
  compensation strategy) but bad at numeric W/L and at reading raw simulator output. SPECTRA makes the LLM write a
  **design-intent program**: a short Python procedure that chooses a topology and expresses every device as
  (gm/Id, L, Id) through a PDK-characterised gm/Id lookup-table API, exposes a handful of intent variables, and predicts
  its own performance. A deterministic layer compiles the program to SKY130 netlists, runs ERC, simulates, and produces a
  **causal diagnosis** (spec table + prediction/simulation discrepancy + device operating-region margins + finite-difference
  sensitivities of failing specs to intent variables). The LLM chooses among hierarchical repair actions (re-bias /
  re-size / numerical refinement in intent space / topology change). **PVT-aware refinement** adaptively selects the worst
  corners and optimises worst-case violation in the low-dimensional intent space, then verifies on 17 PVT conditions.
- **Benchmark (SPECTRA-Bench).** ≈100 spec-driven tasks over 12 circuit families (op-amp, amplifier, TIA, current mirror,
  LDO, bandgap reference, CT comparator, StrongARM latch, VCO, filters, Schmitt trigger, op-amp applications) on the open
  SKY130 PDK with ngspice-42; three difficulty tiers, a PVT-robust tier, and infeasible-spec controls. Every feasible task
  carries a **feasibility certificate**: an expert reference design found by template optimisation that meets the spec.
- **Novelty vs closest work.** AaLLM/AnalogSAGE/SAFTAC: TT only, op-amp-centric, sizing by LLM critique or BO over raw
  W/L. AnalogScout/OPERA: PVT-aware but fixed topology. AnalogCoder(-Pro): Level-1/BPTM, functional or single FoM.
  None uses gm/Id intent programs whose predictions are checked against simulation, nor device-level causal diagnosis
  evaluated by fault injection.
- **Pilot (done).** Simulation substrate validated (12 testbenches; e.g. integrator f_unity 157.7 kHz vs 159 kHz ideal;
  gm/Id LUTs for 5 corners); expert-template CMA-ES on a two-stage op-amp meets 5 specs after 83 evaluations
  (≈1 min) → refinement in a small intent space is cheap enough for the loop.
- **Risk.** (a) Intent-program generation may fail on unusual families (VCO/latch where gm/Id is less natural) →
  programs may fall back to W/L for digital-like devices. (b) LLM cost: ~10–15 calls/task/run.

### Idea 2: Corner-aware surrogate sizing for LLM-proposed topologies (GNN/GP surrogate across PVT)
- Learn a cross-task surrogate to cut simulations under PVT. Novelty moderate (ML-sizing literature is crowded:
  AutoSizer, AnalogScout, ATLAS); needs large training data; weaker LLM-agent story. **Rejected as main idea**; the
  adaptive-corner selection part is folded into Idea 1.

### Idea 3: Infeasibility-aware agent (detect and certify infeasible specs)
- Agents tend to "keep trying" or hallucinate success. Novel and useful but too thin for a full ICCAD paper alone.
  **Folded into Idea 1** as infeasible-spec control tasks + a "declare infeasible" action evaluated for precision/recall.

### Idea 4: Fine-tuned small model for analog design (SFT+RL with simulation reward)
- Infeasible on 4 CPU cores, and covered by SAFTAC/AnalogSeeker/EasySize. **Rejected.**

## Ranking
| Idea | Novelty | Feasibility (4 CPU, ngspice, claude -p) | Expected impact | Decision |
|---|---|---|---|---|
| 1 SPECTRA | high (fills Gaps 1,2,3,4) | high (pilot done) | high | **selected** |
| 2 surrogate | medium | medium | medium | merged (adaptive corners) |
| 3 infeasibility | medium-high | high | medium | merged (controls) |
| 4 fine-tune | low | infeasible | — | rejected |

AUTO_PROCEED: selected Idea 1 → `refine-logs/FINAL_PROPOSAL.md`, `refine-logs/EXPERIMENT_PLAN.md`.
