# Top-conference evidence map

This map is the handoff contract for the SPECTRA repository. It separates the
quality expected for a paper from the evidence currently materialized in the
checkout. A row marked `capability` or `sensitivity` cannot be promoted to the
frozen primary ranking or to a universal SOTA claim.

## Target paper contract

The current manuscript template is ICCAD-style (`paper/main.tex`). The evidence
contract follows the literature audit in [`docs/TOPCONF_LITERATURE_AUDIT.md`](TOPCONF_LITERATURE_AUDIT.md)
and the frozen comparison protocol in [`docs/MAIN_COMPARISON_PROTOCOL.md`](MAIN_COMPARISON_PROTOCOL.md).

| Requirement | Target scale | Current evidence |
|---|---|---|
| Primary matched benchmark | At least six circuit domains and a fixed task text | 36 fixed-topology SKY130 tasks across six families, with 24 nominal and 12 robust tasks |
| Repository-wide expansion | At least twelve families and a larger held-out matrix | 92 tasks across 12 families, 2,208/2,208 external-primary cells |
| Public source-native tracks | Multiple topology sources, PDKs and simulators | AnalogGym, AMPICBench, opensource-analog-circuits, SGAnalog, ATLAS, Analog Design Bench, LOADBench and AnalogPortBench are registered in `data/bench/cross_domain_manifest.json` |
| External frameworks | Seven paper-backed rows beside SPECTRA | AnalogCoder, ADO-LLM, AnaFlow, Artisan, AutoSizer, ATLAS and GLOVA in `data/bench/paper_sizing_manifest.json` |
| Coupled components | At least three independently removable mechanisms | Diagnosis, intent programs, PVT-aware refinement and versioned knowledge cards, with mechanism-level matched ablations |
| Seeds and budget | At least three seeds and one common resource cap | Seeds 0/1/2, 300 simulation units and 12 LLM calls per matched cell |
| Robustness | Independent all-corner verification | 45-condition verifier for eligible SKY130 tracks, source-defined corner contracts elsewhere |

## Metrics required for each matched row

Electrical endpoints are TT success, all-corner PVT success, mean and median
normalized violation, and worst-corner violation. The report also retains
per-task win/loss/tie, 95% task-cluster bootstrap intervals, exact paired tests
with Holm correction, simulations to first feasible design, total simulations,
LLM calls, wall time, token counts, cost when a tariff is available, crash and
timeout rates, parser/convergence/legality failure counts, and cross-seed
variance. Mismatch yield is a separate endpoint when the source benchmark
provides an independent Monte-Carlo contract. Capability-only rows report their
available source metrics without inventing missing PVT or mismatch values.

## Components and required studies

| Mechanism | Full method role | Required evidence |
|---|---|---|
| Device-level diagnosis | Converts simulator failures into structured causes and actions | Remove diagnosis and report endpoint plus mechanism-axis attribution |
| Typed intent program | Constrains LLM output to a PDK-aware sizing representation | Replace with raw device dimensions under the same parser and budget |
| Adaptive PVT refinement | Promotes worst corners and sensitive variables into bounded search | Nominal-only, staged-corner and full-verifier arms |
| Versioned knowledge cards | Supplies topology, PDK and provenance facts | Remove retrieval or replace with an unversioned card under matched prompts |

The mechanism track retains mixed binary endpoint effects. A component is
credited only on its predeclared mechanism axis, and a null or negative endpoint
remains visible in the appendix and acceptance records.

## Experiments beyond performance and ablation

1. Cross-seed variance and paired statistical tests.
2. Cross-PDK, cross-topology and cross-simulator matched reruns where the source exposes a common metric contract.
3. PVT policy sensitivity with an independent 45-condition verifier.
4. Budget and stability curves over simulation and call caps.
5. Failure taxonomy covering convergence, parser, simulator, legality and electrical closure.
6. Wall-time, token and cost accounting, including simulator parallelism.
7. Mismatch or Monte-Carlo yield with an independent validation seed.
8. Knowledge provenance, prompt leakage and held-out-task checks.
9. Reproduction audit with source commits, binary hashes, PDK identity, raw shards and strict duplicate/missing-cell rejection.
10. Cross-domain capability audits for public suites whose source artifacts do not yet define a matched sizing transfer protocol.

## Current measured results and boundaries

The pre-registered `spectra_staged` sensitivity is complete for both AnalogGym
amplifier topologies. HoiLee reaches TT/PVT `1.000/1.000` against AnaFlow
`1.000/0.667`; Leung reaches `1.000/0.667` against `1.000/0.333`. Mean PVT
violation is lower in both cases. TT success is tied, and mean wall time is
higher for the staged arm, so these are electrical sensitivity leads rather than
an efficiency lead. The receipts are
`results/analoggym_pvt_staged_comparison.{json,md}` and
`results/analoggym_leung_pvt_staged_comparison.{json,md}`. They are excluded
from the frozen eight-row primary matrix.

AnalogPortBench has a complete source inventory and a real source-native smoke
receipt. Its initial 250-job golden replay completed 243 jobs before eight high-cost
corners hit the upstream 900-second timeout. The eight jobs were rerun with the
same evaluator and fixed corners, completing 250/250 with 8/8 recovered corners
passing. The initial timeout and complete recovery receipts are retained in
`results/golden_attempt_timeout_receipt.json` and
`results/analogport_golden_recovery_receipt.{json,md}`. The smoke passes 9/9 source
checks but uses a bundled golden reference, so it is capability evidence rather
than a SPECTRA/AnaFlow ranking cell.

The literal gate remains `XSOTA-1: NOT MET`. The latest audit is
`results/xsota_gate_audit.json` with 19 receipts, 9 comparable PVT strata and
10 uncovered or capability-only strata. The audit requires strict SPECTRA leads
on TT success, PVT success, mean TT violation and mean PVT violation in every
declared public stratum. No finite subset is extrapolated to all analog circuits,
all PDKs or all simulators.

## Synchronization and reproducibility

The tracked source is synchronized across local `E:/CodexProjects/spectra-analog-agent`,
`/root/autodl-tmp/spectra-analog-agent` on westc, and GitHub
`appleweiping/SPECTRA`. Current synchronized commit and raw-evidence hashes are
checked before handoff. Simulator and model experiments are executed on the
server. Local E: is used for source review and evidence synchronization, with no
C: or D: experiment workspace.
