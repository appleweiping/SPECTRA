# External evaluation alignment

This note records why the expanded SPECTRA evaluation uses its current task, baseline and metric targets. The numeric targets for this project come from the project acceptance rules. The papers below provide the empirical patterns that we reproduce where the evaluator permits a fair comparison.

| Reference | Benchmark scale | External comparisons | Reported metrics or protocol | SPECTRA consequence |
|---|---:|---|---|---|
| AnalogCoder, AAAI 2025 | 24 tasks, split into basic and composite circuits | CodeLlama-70B, WizardCoder-33B, DeepSeek-V2, Llama-3-70B, GPT-3.5, GPT-4o without the tool, and AnalogCoder | Pass@1, Pass@5, solved-task count, component ablations, 15 or 30 independent trials | Keep the per-task success endpoint, add a seven-framework comparison matrix and retain matched ablations with seeds and confidence intervals |
| AnalogGym, ICCAD 2024 | 30 topologies in five categories | The suite reports comparisons among sizing methods under a common evaluator | Category coverage, simulator/PDK identity, circuit-specific performance and reproducibility details | Use at least six SPECTRA circuit domains, explicit PDK and simulator identity, and per-domain metrics |
| AnalogGenie, ICLR 2025 | Multi-family topology corpus with more than 3,000 unique training sequences and augmented samples | CktGNN, LaMAGIC and AnalogCoder | Valid-circuit rate, topology scale, novelty and circuit-family FoM | Retain validity and novelty-style structural checks separately from electrical success and report a multi-metric table |
| AnalogScout, arXiv 2026 | Three SKY130 OTAs, with a GF180 test track | CMA-ES, Bayesian optimization, LAS-style and AnalogCoder-Pro-style flows | Equal simulation budget, PVT feasibility, TT power, sample standard deviation, mismatch yield with 500 samples and phase ablations | Use one fixed simulation accounting unit, add optimizer baselines, report PVT and mismatch separately, and test each component under matched budgets |

The current SPECTRA-Bench contains 11 circuit families, 92 certified or designer tasks and 25 additional designer tasks. Its evaluator exposes gain, bandwidth, phase margin, power, swing, noise, PSRR, CMRR, slew, settling, ripple, line regulation and delay where the circuit family defines them. All methods receive the same task text, simulator, PDK, seed and simulation budget. Robust tasks use the 45-corner PVT grid, and mismatch is reported as a separate post-hoc verification stage.

The seven-framework target is implemented as an empirical matrix. The fair external methods are AnalogCoder-style direct generation, AnalogCoder-Pro-style generation plus TPE, SPECTRA-min, generation plus CMA-ES and the three template-oracle optimizers used as privileged upper bounds. The oracle rows are labeled as privileged and are excluded from claims about fair LLM superiority. SPECTRA is the eighth row. All eight rows use the same 36-task six-domain extension. The four existing arms reuse their 16 matching E1g records and are rerun on the 20 topconf6 tasks absent from that chain before aggregation. The matrix records success rate with confidence intervals, per-task wins/losses, simulator evaluations to success, LLM calls, cost fields, PVT feasibility and mismatch yield.

The ablation rule follows the component studies in AnalogCoder and AnalogScout. A component is retained in the final claim only when the paired comparison supports a directional contribution. If an ablation wins on a subset, the result remains in the tables and the paper reports the negative or mixed finding rather than changing the endpoint or deleting the task.

References

- AnalogCoder, AAAI 2025. <https://ojs.aaai.org/index.php/AAAI/article/download/32016/34171>
- AnalogGym, ICCAD 2024. <https://arxiv.org/abs/2409.08534>
- AnalogGenie, ICLR 2025. <https://proceedings.iclr.cc/paper_files/paper/2025/file/f0552f14388d95b19740dee809f5cad1-Paper-Conference.pdf>
- AnalogScout, arXiv 2026. <https://arxiv.org/abs/2610.37319>
