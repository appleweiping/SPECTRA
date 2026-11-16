ARIS /experiment-bridge step 3: cross-model CODE REVIEW before full deployment (no GPU here; the expensive
resources are LLM calls and ngspice time). Repository root is your cwd. Read the code yourself:
- spectra/sim/ngspice.py, netlist.py, measure.py, tb_opamp.py, families.py, evaluate.py, lut.py
- spectra/agent/spectra_agent.py, common.py, diagnose.py, sandbox.py, sandbox_worker.py, dsl.py, prompts.py, knowledge.py, llm.py
- spectra/baselines/direct.py, genbo.py, oracle.py
- spectra/opt/sizing.py, spectra/bench/templates.py
- scripts/run_bench.py, scripts/build_bench.py, scripts/analyze.py, scripts/fault_injection.py, scripts/build_controls.py
- idea-stage/GATE1_RESPONSE.md and refine-logs/EXPERIMENT_PLAN.md for intent.

Find concrete BUGS and FAIRNESS problems, ranked by severity, each with file:line and a minimal fix. In particular:
1. Measurement correctness: PM/UGBW/gain extraction, CMRR/PSRR, slew/settling, swing, LDO/ref/VCO/latch/comparator/
   filter metrics; sign conventions; wrdata column layouts (wr_singlescale); unit errors.
2. Spec checking / violation normalisation (evaluate.py) and the robust (45-condition PVT) logic.
3. Budget accounting: is every simulation a method performs charged to it (sensitivities, refinement, PVT verifies)?
   Are budgets equal across SPECTRA, SPECTRA-min, direct, genbo (TPE/CMA-ES), oracle? Any method that can exceed it?
4. Independent verification in run_bench.py: could a method be credited success without its returned netlist passing?
5. Leakage: does any method see information others don't (beyond the documented design differences)?
6. Benchmark derivation: are feasibility certificates valid (reference re-verified against the final spec set)?
7. Concurrency/race issues (threads, temp dirs, caches keyed by run_tag), anything that could silently corrupt results.
Be concrete and terse. End with a list "MUST FIX before E1" vs "should fix".
