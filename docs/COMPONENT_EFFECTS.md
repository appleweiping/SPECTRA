# Component evidence policy

SPECTRA has four coupled components with separate removal arms in the frozen GPT-6.1-sol evaluation.
The project reports binary success, paired wins/losses, simulator work and mechanism evidence together. A mixed or null endpoint result is retained as a result and is not rewritten as an essentiality claim.

The generated table is [results/component_effects.md](../results/component_effects.md), with machine-readable values in [results/component_effects.json](../results/component_effects.json).

| Component | Concrete implementation | Primary evidence | Interpretation |
|---|---|---|---|
| Device-level diagnosis | Operating-region checks, failing-margin tables, finite-difference intent sensitivities and worst-condition reports in `spectra/agent/diagnose.py` | 34-task mean simulations 77.8 with diagnosis vs 103.2 without. Fault top-1 is 76.5% with diagnosis vs 80.7% for raw LLM evidence | Lower simulation work and richer causal feedback, mixed fault-localisation endpoint |
| Design-intent program | `lut.size`, bounded intent parameters and executable first-order predictions in `spectra/agent/dsl.py` and `spectra/agent/spectra_agent.py` | Median 10 intent variables vs 25 raw sizing variables, 2.29x compression. Prediction accuracy is metric-dependent | Search-space and auditability contribution, mixed success endpoint |
| PVT-aware refinement | Worst-condition selection followed by bounded CMA-ES over intent variables in `Spectra.robust_stage` | 89.9% vs 69.6% without refinement on the matched T3 block, 7/3 task W/L, paired p=0.05194 | Directional endpoint contribution, below the contract's threshold for an essentiality claim |
| Knowledge cards | Family-specific topology, headroom, bias and stability cards in `spectra/agent/knowledge.py` | 89.9% vs 87.0% without cards, 47.5 vs 53.1 mean simulations, 3/6 task W/L, paired p=0.85903 | Small mixed effect retained without a necessity claim |

This separation follows the acceptance contract. The paper therefore preserves the negative diagnosis localisation result, the intent predictor's second-order errors and the non-significant knowledge-card comparison.
