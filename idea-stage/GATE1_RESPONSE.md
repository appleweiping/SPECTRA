# Response to Gate-1 review (Fable 5.1, trace .aris/traces/idea-discovery/2026-11-16_run01)

Verdict received: PROCEED-WITH-CHANGES (novelty 6, significance 7, soundness 5, feasibility 4→7 if descoped,
acceptance 5→6). Acceptance status: provisional (same-family reviewer). Changes adopted:

| Reviewer point | Change | Status |
|---|---|---|
| Benchmark circularity; knowledge only for SPECTRA | Topology knowledge cards given to ALL LLM methods (cards ablation dropped); designer-specified tier of tasks written independently of templates; oracle pass rate under the same budget reported; "infeasible" controls replaced by **oracle-unmet** near-frontier controls (≥20) | in progress |
| PVT grid lacks cross terms (SS/125C/1.62V) | Final verification on the full 45-condition grid (5 corners × 3 temps × 3 supplies) | done (`spectra/sim/evaluate.py: PVT`) |
| No mismatch | Per-instance SKY130 mismatch MC (PDK Pelgrom slopes, agauss per instance, `.option seed`), 100 samples on robust-tier final designs → yield | done (`scripts/make_mc_models.py`, `MC`) |
| Ideal resistors in BGR/LDO | All resistors compiled as SKY130 high-po poly first-order model (PDK TC1=5.14e-4, TC2=1.22e-6, tnom 30 C) | done (`spectra_rpoly`) |
| LUTs only at 27 C | LUTs for 5 corners × {−40, 27, 125} C; exposed to programs via `lut.at(corner, temp)` | in progress |
| Budget accounting on robust tier | Per-tier budgets (nominal 300, robust 3000 condition-evaluations); sensitivity sims charged; anytime curves as primary efficiency result | in progress |
| Missing decisive ablation | New baseline **SPECTRA-min**: one LLM call (topology + intent program) + intent-space CMA-ES with the whole budget, no diagnosis/repair | in progress |
| Optimizer confound in Gen+BO | AnalogCoder-Pro-style baseline run with TPE **and** CMA-ES over raw W/L | in progress |
| AnalogSAGE baseline | Public code depends on Gemini-2.5-Flash, OpenAI embeddings and an ISSCC RAG corpus not available here; we document this and instead cover its mechanism (topology selection + BO sizing) by the Gen+BO baselines | documented |
| Scope | Contributions narrowed to: (C1) intent programs with prediction–simulation discrepancy feedback; (C2) device-level diagnosis validated by stratified fault injection incl. a rule-only (no-LLM) diagnoser baseline; (C3) PVT/MC-verified multi-family benchmark with fair budget accounting. "Causal" wording dropped; backbone study reframed as model-size scaling within the Claude family; memory module dropped | adopted |
| Statistics | Cluster bootstrap over tasks; detectable-effect statement; 3 seeds E1 | adopted |
| Pilot numbers without files | Pilot results written to `results/pilot/` | done |
| Swing testbench loading | Documented in the paper (inverting ×10 with 1 MΩ feedback measures the loaded linear output range) | adopted |
