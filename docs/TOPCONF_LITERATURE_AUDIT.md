# Top-conference literature audit for SPECTRA

Audit date: 2026-11-20. This document records the public primary sources used to set the
benchmark and experiment contract. Counts below are taken from the papers or official project
pages. A preprint is labelled as a preprint until a proceedings page or DOI is available.

## Sources and what they establish

| Source | Evidence read | Design implication for SPECTRA |
|---|---|---|
| [AnalogGym, arXiv:2409.08534](https://arxiv.org/abs/2409.08534) and [code](https://github.com/CODA-Team/AnalogGym) | An open suite with 30 topologies in five categories, multiple technology nodes and simulator support. | A serious sizing paper needs public, source-native circuits, fixed testbenches, PDK/simulator receipts and an independent verifier. One topology is not enough. |
| [AutoSizer, ICML 2026](https://proceedings.mlr.press/v306/yu26aw.html) | Introduces AMS-SizingBench with 24 diverse AMS circuits in SKY130 and evaluates a reflective two-loop optimizer. | A current ML venue expects a named benchmark, adaptive-search analysis and comparisons against both classical and LLM methods. |
| [AnalogAgent, arXiv:2603.23910](https://arxiv.org/abs/2603.23910) and [artifact](https://github.com/artifact-repro/analogagent-artifact) | Reuses 30 AnalogCoder functional tasks and reports Pass@1/5, cumulative success, time-to-first-success, tokens/runtime and five-trial variability. | Keep functional topology-generation results separate from quantitative PVT sizing, and report both per-task success and resource-to-success curves. |
| [NEMESIS2.0, arXiv:2611.18995](https://arxiv.org/abs/2611.18995) and [code](https://github.com/UMN-EDA/NEMESIS) | Uses seven test circuits and 700 specification-set sizing tasks with SPICE-checked surrogate equations, reporting surrogate accuracy, final SPICE pass, runtime, samples and iterations. | Add surrogate-calibration error and simulator-confirmed pass as separate endpoints when a learned equation model is used. |
| [AgenticSizing, arXiv:2609.25873](https://arxiv.org/abs/2609.25873) | Reports eight circuits, including an LDO with up to 55 transistors and 60 sizing variables. The method uses topology decomposition, knowledge reuse and role-specialized agents. | Topology understanding, reusable design knowledge and specialization are separable components and require matched ablations. |
| [Long-Horizon Analog Design Bench, arXiv:2609.33356](https://arxiv.org/abs/2609.33356) | Uses 50 tasks from 17 designers, 15 agent configurations, three rollouts and 2,250 two-hour attempts. Reports full-specification pass rate, reliability, coverage, runtime, model iterations, tool calls, wait time, recovered candidates, tokens and cost. | A benchmark must preserve task-level outcomes and resource accounting. Pass rate alone is insufficient. |
| [PVTSizing 2.0, arXiv:2611.22328](https://arxiv.org/abs/2611.22328) | Evaluates four circuit benchmarks and 40 runs, reporting runtime/sample-count trade-offs and a knowledge-injection study. | PVT-aware sizing needs corner closure, sample efficiency and runtime, with a separate knowledge intervention. |
| [AnalogScout, arXiv:2610.37319](https://arxiv.org/abs/2610.37319) | Targets simulation-efficient PVT-aware sizing and identifies all-corner simulation as the dominant cost. | SPECTRA must report corner allocation, independent PVT verification and simulation savings. |
| [AMPICBench, 2026 repository](https://github.com/AMPICLab/AMPICBench) | Provides source-native Sky130 ngspice netlists with per-corner operating-region data for sizing, simulation and layout tools. | Add source-native topology receipts and separate sizing, simulation and layout evaluation layers. |
| [SGAnalog, 2026 repository](https://github.com/Li-Yueting/SGAnalog) | Uses commit-pinned open-source silicon tapeouts, graph-deduplicated circuits and runnable ngspice testbenches. | Add provenance-pinned held-out designs and leakage-aware post-cutoff splits when the task is topology generation or sizing from real tapeouts. |
| [AnalogGym-Opt, IEEE TCAD 2026 code](https://github.com/Computing-Intelligent-Decision-Team/AnalogGym-Opt) | Provides a GRPO/R-GNN multi-objective sizing infrastructure on AnalogGym with optional PVT verification and Pareto tracking. | Include learned optimizer and Pareto-front baselines, with identical simulator and budget caps. |
| [Open-source Analog Circuit Sizing Benchmark](https://github.com/jialinlu/opensource-analog-circuits) | Provides 31 circuits, ngspice wrappers, 12 PVT corners and a separate 200/500-sample mismatch-yield protocol. | Keep PVT and mismatch as distinct axes and use an independent validation seed for yield. |
| [PARADIGM-Analog-EDA](https://github.com/Kevin-Pal/PARADIGM-Analog-EDA) | Reuses topology-specific Pareto databases to warm-start topology selection and sizing. | Add database reuse and cold-start transfer controls to distinguish retrieval from optimizer skill. |
| [BAIcO](https://github.com/nunocclourenco/BAIcO) and [ACOB](https://github.com/Quizas605/ACOB-Analog-Circuit-Optimization-Benchmark) | Open optimization frameworks expose simulator wrappers, task configs and reproducible black-box baselines. | Preserve classical GA/BO/RL controls and simulator-failure denominators in the same manifest. |
| [ATLAS, ICCAD 2026 code and paper metadata](https://github.com/youngmin0oh/atlas) | Public topology-aware Bayesian optimization with Mapper/TDA, ngspice, GF180MCU and SKY130. The repository exposes fixed optimizer defaults and documents reproducibility defects corrected after the paper experiments. | Cross-PDK receipts and versioned optimizer configuration are required. A result must distinguish paper reproduction from a clean-room adapter. |
| [AnaFlow, arXiv:2511.03697](https://arxiv.org/abs/2511.03697) | Agentic, explainable, sample-efficient sizing demonstrated on two circuits, with adaptive simulation and reasoning history. | AnaFlow is a meaningful matched comparator, but an adapter must not be called an official reproduction when source code is unavailable. |
| [Analog Canvas](https://github.com/cascode-ai/analog-canvas) | 2,500+ commits, deterministic SPICE/Spectre import/export, typed Agent transaction model, ERC, simulator service and auditable acceptance artifacts. | Framework quality includes deterministic artifacts, typed interfaces, reproducible simulator runs and provenance, beyond an optimizer loop. |
| [Virtuoso Bridge Lite](https://github.com/Arcadia-1/virtuoso-bridge-lite) | Release documentation emphasizes scoped Spectre execution, PDK/CDF callback provenance, isolated work directories, explicit recovery boundaries and offline tests. | A production-facing framework must isolate runs, record simulator/PDK identity and avoid claiming GUI/electrical equivalence without matching netlists, models and solver options. |

The 2026 arXiv entries above are time-stamped snapshots found on 2026-11-19. They are
included as emerging references and are not silently upgraded to peer-reviewed status.

The new repository snapshots were checked out under `work/reference_sources/` on E: for
source inspection only. They were not added as vendored project dependencies and no local
simulator or model run was started. The audit focuses on benchmark manifests, evaluation
scripts, simulator wrappers, provenance rules and ablation contracts rather than treating
repository size as evidence of scientific quality.

## Derived SPECTRA quality contract

The following is the minimum contract adopted for the top-conference version of SPECTRA. It is
an evidence-based synthesis of the sources above, not a claim that a venue mandates a fixed
number.

### Benchmarks

Use at least six circuit domains and at least 36 fixed-topology tasks for the primary matched
comparison. Add a larger repository-wide expansion with at least 12 families and 92 tasks. Add
public source-native tracks with AnalogGym, ATLAS/GF180, at least one additional PDK/model group,
two simulators, and PVT corner files where the source exposes them. Every cell records the task,
PDK, topology, simulator version, seed, budget, nominal result and independent corner result.

### External frameworks

Use seven paper-backed external rows beside the native SPECTRA row. The current rows are
AnalogCoder, ADO-LLM, AnaFlow, Artisan, AutoSizer, ATLAS and GLOVA. Each row must use the same
task text, simulation cap, LLM-call cap, seeds, verifier, parser and failure denominator. A
clean-room adapter carries its source venue and implementation status in the manifest.

### Components

The framework has four coupled mechanisms that can be independently removed or replaced:

1. topology and fault diagnosis,
2. intent-program abstraction,
3. PVT-aware refinement and worst-corner closure,
4. versioned design-knowledge cards.

The mechanism audit must report endpoint success, normalized violation, sample count, first-pass
budget, tool calls, and structured events. A component can be supported by a prespecified
mechanism axis when binary endpoint effects are mixed. Mixed results remain in the appendix.

### Metrics

The primary table reports TT success, PVT success, mean and median normalized violation, per-task
win/loss/tie, 95% cluster-bootstrap intervals, simulator evaluations, LLM calls, wall time, token
usage/cost when available, and crash counts. Robustness reports corner-wise violation, worst-corner
violation, mismatch/yield when the task supports it, and cross-seed variance. Efficiency reports
time-to-first-feasible and simulation-normalized success. A result is ranking-eligible only when
all required cells and verifier conditions are finite and present.

### Required experiments beyond the main comparison and ablation

The paper contract includes the following additional studies.

* Cross-seed variance with at least three seeds and paired statistical tests.
* Cross-PDK, cross-topology and cross-simulator transfer or matched reruns.
* PVT sensitivity with nominal-only, staged-corner and full-verifier policies.
* Budget curves and stability curves over simulation and call caps.
* Failure taxonomy with convergence, parser, simulator, legality and electrical-closure errors.
* Cost and wall-time accounting, including simulator parallelism and token usage.
* Mismatch or Monte-Carlo yield when the public testbench supports it.
* Knowledge and prompt provenance, leakage checks, and held-out task evaluation.
* Reproducibility audit with source commit, binary hash, PDK identity, raw shards and a strict
  merger that rejects missing, duplicate or non-finite cells.

### Universal-coverage extension

“All analog circuits, all PDKs and all simulators” is an open-ended population, so it cannot
be established by a finite benchmark as a literal theorem. The reproducible extension contract
therefore uses a coverage matrix with explicit strata rather than silently extrapolating one
PDK or simulator. A universal-style claim requires, at minimum, source-native tasks from
AnalogGym/AMPICBench, the 31-circuit open-source suite, SGAnalog tapeout-derived circuits,
ATLAS GF180/SKY130 tasks, and Analog Design Bench; at least three PDK/model groups; ngspice,
Xyce and one licensed Spectre/Virtuoso path when a licensed server is available; three seeds;
nominal plus all source-defined PVT corners; independent mismatch validation; and matched
classical, learned, LLM-agent and database-reuse baselines. Every unsupported stratum must be
reported as unmeasured, with no universal SOTA extrapolation.

## SPECTRA implementation mapping

The repository currently materializes the contract through the 36-task/92-task external
matrices, the 18-task component mechanism audit, AnalogGym HoiLee and Leung topology tracks,
ngspice-44.2 and Xyce-7.10 receipts, and the ATLAS GF180 matched adapter. The primary result and
the exploratory union/family policies remain separately labelled. This preserves the negative
and mixed findings required by the sources while keeping the main method focused on one SPECTRA
framework.

