# External evaluation alignment

This note records why the expanded SPECTRA evaluation uses its current task, baseline and metric targets. The numeric targets for this project come from the project acceptance rules. The papers below provide the empirical patterns that we reproduce where the evaluator permits a fair comparison.

| Reference | Benchmark scale | External comparisons | Reported metrics or protocol | SPECTRA consequence |
|---|---:|---|---|---|
| AnalogCoder, AAAI 2025 | 24 tasks, split into basic and composite circuits | CodeLlama-70B, WizardCoder-33B, DeepSeek-V2, Llama-3-70B, GPT-3.5, GPT-4o without the tool, and AnalogCoder | Pass@1, Pass@5, solved-task count, component ablations, 15 or 30 independent trials | Keep the per-task success endpoint, add a seven-row comparison matrix and retain matched ablations with seeds and confidence intervals |
| AnalogGym, ICCAD 2024 | 30 topologies in five categories | The suite reports comparisons among sizing methods under a common evaluator | Category coverage, simulator/PDK identity, circuit-specific performance and reproducibility details | Use at least six SPECTRA circuit domains, explicit PDK and simulator identity, and per-domain metrics |
| AnalogGenie, ICLR 2025 | Multi-family topology corpus with more than 3,000 unique training sequences and augmented samples | CktGNN, LaMAGIC and AnalogCoder | Valid-circuit rate, topology scale, novelty and circuit-family FoM | Retain validity and novelty-style structural checks separately from electrical success and report a multi-metric table |
| AnalogScout, arXiv 2026 | Three SKY130 OTAs, with a GF180 test track | CMA-ES, Bayesian optimization, LAS-style and AnalogCoder-Pro-style flows | Equal simulation budget, PVT feasibility, TT power, sample standard deviation, mismatch yield with 500 samples and phase ablations | Use one fixed simulation accounting unit, add optimizer baselines, report PVT and mismatch separately, and test each component under matched budgets |

The current SPECTRA-Bench contains 11 circuit families, 92 certified or designer tasks and 25 additional designer tasks. Its evaluator exposes gain, bandwidth, phase margin, power, swing, noise, PSRR, CMRR, slew, settling, ripple, line regulation and delay where the circuit family defines them. All methods receive the same task text, simulator, PDK, seed and simulation budget. Robust tasks use the 45-corner PVT grid, and mismatch is reported as a separate post-hoc verification stage.

The completed matrix has eight rows and should be read as a protocol matrix rather than seven top-conference framework implementations. Direct generation has AnalogCoder AAAI 2025 lineage. Generate plus TPE is an AnalogCoder-Pro IEEE TCAD adaptation. SPECTRA-min is an internal control, generate plus CMA-ES is an optimizer replacement control, and the three oracle rows are privileged template-optimization upper bounds. AnalogGenie, AnalogGym and AnalogScout informed the benchmark protocol but were not executed as drop-in sizing agents. All eight rows use the same 36-task six-domain extension. The four existing arms reuse their 16 matching E1g records and are rerun on the 20 topconf6 tasks absent from that chain before aggregation. The matrix records success rate with confidence intervals, per-task wins/losses, simulator evaluations to success, LLM calls, cost fields, PVT feasibility and mismatch yield.

The ablation rule follows the component studies in AnalogCoder and AnalogScout. A component is retained in the final claim only when the paired comparison supports a directional contribution. If an ablation wins on a subset, the result remains in the tables and the paper reports the negative or mixed finding rather than changing the endpoint or deleting the task.

The mechanism track follows that rule in `results/component_mechanism_matrix.json`. Refinement and knowledge removal reduce
paired TT success on the matched six-domain set. Diagnosis and intent produce auditable attribution and parameterization
signals, but their TT/PVT removal arms are mixed or numerically better on this run. The project therefore does not make
an all-components performance claim.

The strict sizing track now uses `data/bench/paper_sizing_tasks.jsonl`. It contains 36 public fixed-topology tasks
across opamp, amp, cmirror, filter, ldo and vco, including a robust subset with PVT-enabled verification. Its seven
external paper-backed rows are AnalogCoder AAAI-25, ADO-LLM ICCAD-24, AnaFlow ICCAD-25, Artisan DAC-24, AutoSizer
ICML-26, ATLAS ICCAD-26 and GLOVA DAC-25. SPECTRA is the eighth row and uses the native diagnosis, knowledge and
bounded-refinement loop through a fixed-topology adapter. The external rows are explicitly labelled clean-room
adapters. The same topology digest, variable bounds, task text, simulator, 300 simulation-unit budget and 12-call
LLM cap are used across rows. The earlier EXT7g rows remain a diagnostic framework-and-control matrix and are
excluded from the strict external count.

The seven external strict rows are paper-backed framework identities, while their implementations in this
repository are clean-room adapters that expose each paper's sizing loop through the frozen fixed-topology interface.
SPECTRA is evaluated through its native diagnosis, knowledge and bounded-refinement logic with the same frozen
topology interface. Official code is used only where the paper repository supports the required interface. Paper-only
rows record the unsupported features and the adaptation in `data/bench/paper_sizing_manifest.json`, so a clean-room
adapter is not presented as an official reproduction.

The completed eight-row SIZ7g snapshot gives SPECTRA the highest observed nominal TT success, 31/36 or 0.861,
with a 95% Wilson interval of [0.713, 0.939]. Its independent 45-corner PVT success is 2/12 or 0.167, while
AnaFlow reaches 4/12 or 0.333. The result supports a strict-track nominal sizing lead under the frozen protocol.
It does not support a universal analog-sizing SOTA statement because the track is fixed-topology, self-constructed,
single-seed and mismatch data are unavailable for all rows.

References

- AnalogCoder, AAAI 2025. <https://ojs.aaai.org/index.php/AAAI/article/download/32016/34171>
- AnalogGym, ICCAD 2024. <https://arxiv.org/abs/2409.08534>
- AnalogGenie, ICLR 2025. <https://proceedings.iclr.cc/paper_files/paper/2025/file/f0552f14388d95b19740dee809f5cad1-Paper-Conference.pdf>
- AnalogScout, arXiv 2026. <https://arxiv.org/abs/2610.37319>
- ADO-LLM, ICCAD 2024. <https://doi.org/10.1145/3676536.3676816>
- AnaFlow, ICCAD 2025. <https://doi.org/10.1109/ICCAD66269.2025.11240818>
- Artisan, DAC 2024. <https://doi.org/10.1145/3649329.3655903>
- AutoSizer, ICML 2026. <https://proceedings.mlr.press/v306/yu26aw.html>
- ATLAS, ICCAD 2026. <https://doi.org/10.1145/3831252.3834039>
- GLOVA, DAC 2025. <https://doi.org/10.1109/DAC63849.2025.11132461>
