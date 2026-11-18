# SPECTRA — Spec-to-Robust Analog Circuit Synthesis with LLM Agents

End-to-end agentic analog circuit generation: natural-language specification → topology → device sizing →
PVT-robust (45 conditions) + mismatch-verified SPICE netlist on the open SkyWater SKY130 PDK (ngspice-42).

* **SPECTRA agent** (`spectra/agent`): the LLM writes *design-intent programs* that size devices from
  (gm/Id, L, Id) via PDK lookup tables and predict their own performance; a deterministic layer executes, checks
  (ERC), simulates and returns a device-level diagnosis; the LLM picks Refine / Edit / Declare-infeasible;
  refinement runs CMA-ES in the program's intent space with adaptive worst-corner PVT closure.
* **SPECTRA-Bench** (`data/bench`, `spectra/sim`, `spectra/bench`): 12 circuit families (op-amp, amplifier, TIA,
  current mirror, LDO, bandgap reference, CT comparator, StrongARM latch, VCO, filters, Schmitt trigger, op-amp
  applications) with testbenches, certified tiers (feasibility certificates from expert templates), a designer tier,
  45-condition PVT grid and per-instance mismatch Monte Carlo (an early infeasible-control tier was withdrawn).
* **Baselines** (`spectra/baselines`): an AnalogCoder-style direct netlist agent, an AnalogCoder-Pro-style
  generate+TPE adaptation, a generate+CMA-ES optimizer control and three explicitly labelled template-oracle
  controls. The six-domain extension evaluates eight rows under one budget. Only the first two rows have direct
  literature lineage. SPECTRA-min is an internal control, and oracle rows are privileged upper bounds. Ablations are
  in `scripts/run_bench.py`.
* **Strict paper sizing track** (`data/bench/paper_sizing_tasks.jsonl`): SPECTRA plus AnalogCoder, ADO-LLM, AnaFlow,
  Artisan, AutoSizer, ATLAS and GLOVA use one frozen-topology protocol. The seven external rows are clean-room
  adapters with paper and venue metadata in `data/bench/paper_sizing_manifest.json`. SPECTRA uses the native
  diagnosis, knowledge and bounded-refinement loop through a fixed-topology adapter. All eight rows receive the same
  bounds, 300 simulation-unit budget and 12-call LLM cap. The previous EXT7g framework-and-control matrix remains
  a separate diagnostic appendix.
  The final matched extension contains 864 cells, eight rows across 36 tasks and three seeds. In the primary
  eight-row aggregate SPECTRA reaches 0.806 TT and 0.194 PVT, while AnaFlow reaches 0.870 TT and 0.306 PVT.
  The independently reported SPECTRA-PVT-staged variant reaches 0.833 TT, 0.222 PVT and 0.5063 mean PVT violation.
  These are track-scoped measurements and do not establish universal analog-sizing SOTA.
* **Component mechanism track** (`data/bench/component_mech_manifest.json`): six circuit domains, five matched
  SPECTRA arms and three seeds record structured diagnosis attribution, intent provenance, active-set refinement
  traces and versioned knowledge-card retrieval alongside TT/PVT success and efficiency metrics.

Research process follows ARIS (Auto-claude-code-research-in-sleep): `RESEARCH_BRIEF.md` → `idea-stage/` →
`refine-logs/` → `EXPERIMENT_LOG.md` → `review-stage/` → `paper/`; reviewer traces in `.aris/traces/`.

## Quick start
```bash
pip install numpy scipy cma optuna matplotlib openai # + ngspice >= 42 on PATH, OPENAI_API_KEY for GPT calls
python -m scripts.gen_lut tt ff ss sf fs T=-40 T=27 T=125      # gm/Id lookup tables
python -m scripts.run_bench --exp E1g --model gpt-6.1-sol --methods spectra,direct,genbo --seeds 0,1,2
python -m scripts.run_bench --exp EXT7g --model gpt-6.1-sol --methods genbo_cmaes,oracle_random,oracle_cmaes,oracle_tpe --seeds 0 --tasks data/bench/topconf6.jsonl
python -m scripts.analyze --exp E1
bash scripts/finalize_paper.sh        # regenerate every analysis, table, figure and paper macro, then compile
```
Experiment protocol and every deviation: `EXPERIMENT_LOG.md`; acceptance contract: `paper/PAPER_ACCEPTANCE_CONTRACT.md`.

## Layout
- `spectra/sim` — ngspice runner, canonical netlist + ERC + SKY130 compiler, testbenches/measurements, LUT API, evaluation
- `spectra/agent` — SPECTRA (prompts, DSL, sandbox, diagnosis, main loop), LLM wrapper
- `spectra/baselines`, `spectra/opt` — baselines and optimisers
- `spectra/bench` — expert templates, family profiles, NL rendering; `scripts/build_bench.py` derives tasks
- `pdk/sky130` — minimal SKY130 1.8 V FET + PNP models (Apache-2.0, google/skywater-pdk-libs-sky130_fd_pr), mismatch variants
- `results/` — raw runs, summaries; `paper/` — LaTeX (ACM sigconf, anonymous)
