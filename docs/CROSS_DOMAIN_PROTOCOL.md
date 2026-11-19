# Cross-domain evaluation protocol

This protocol extends the fixed-topology SKY130 study to public circuit sources while keeping the comparison auditable. It is frozen before the next server run. A track is included in the primary cross-domain table only when the task source, topology digest, PDK, simulator version, corner set, verifier, model, seeds and budget are recorded for every cell.

## Acceptance table

| ID | Requirement | Passing evidence | Current status |
|---|---|---|---|
| XPDK-1 | At least three public PDK/model groups | SKY130, GF180MCU and PTM45/PTM180 or PTM90/PTM130/PTM180, with immutable model receipts | Planned. The current repository executes SKY130 only |
| XTOPO-1 | Cross-topology public coverage | AnalogGym/AnalogGym-Opt, AMPICBench, opensource-analog-circuits, Analog Design Bench and ATLAS task manifests with non-template topology digests | Planned. The existing 92 tasks are fixed SPECTRA templates |
| XSIM-1 | Cross-simulator validation | At least two independently versioned simulators with the same netlist, models, corners and metric parser. Spectre/HSPICE rows require a reproducible licensed environment | Partial. Server now has official ngspice-44.2 and Xyce 7.10 serial builds. The Xyce translator passes an AnalogGym BSIM4 AC smoke, while the full matched 300-evaluation, 45-condition, three-seed matrix remains in progress |
| XSEED-1 | Multi-seed protocol | Three or more seeds per task-method cell, with seed listed in raw evidence | Pass on existing SIZ7g/SIZ11g tracks |
| XMET-1 | Metric parity | TT success, all-corner PVT success, mean and median normalized violation, simulations-to-first-pass, calls, wall time, token/cost and crash rate | Partial. Existing tracks have the first four core metrics and efficiency fields, but cross-domain parsers are not yet unified |
| XSTAT-1 | Statistical testing | Task-cluster bootstrap confidence intervals, paired sign/Wilcoxon tests and Holm correction across external rows | Pass on existing external track. Must be rerun for each cross-domain family |
| XANA-1 | AnaFlow comparability | AnaFlow clean-room adapter runs on the same public task, PDK, simulator, budget, seed and verifier | Not met outside the current fixed-topology adapter |
| XSOTA-1 | Domain-level claim | Every preregistered main endpoint beats AnaFlow on every declared PDK/topology/simulator stratum, with confidence intervals and no hidden exclusions | Not met. Current evidence supports benchmark-scoped SOTA only |

## Frozen matrix

The next primary matrix has four public tracks.

1. `analoggym_amp_ldo` uses the open SKY130/ngspice AMP and LDO subset from AnalogGym-Opt. It keeps the source testbenches and design-variable bounds, and reports TT plus the source 21-corner robust subset.
2. `opensource_31` uses the 31-circuit suite without copying its unlicensed harness. The adapter records source files and PDK/model provenance, and separates PTM45, PTM180, SKY130 and BJT strata rather than pooling incompatible metrics.
3. `atlas_dual_pdk` uses the public ATLAS benchmark circuits under SKY130 and GF180MCU where the repository provides both model paths. The budget is 500 simulator evaluations, 10 seeds and the ATLAS baseline family. The 500/10 setting is an external reference protocol and is kept separate from the existing 300/3 SIZ7g protocol.
4. `analog_design_bench` uses the public 50-task verifier split. Its task-level success and normalized violation are reported separately from transistor-sizing PVT rows when the task does not expose a common PVT grid.

The primary cross-domain comparison uses the intersection of tasks with identical electrical metrics. Rows with missing PDK or simulator support remain capability-audit entries and do not enter the ranking. Crashes and budget exhaustion remain in denominators.

The first server capability receipt is archived at
`results/cross_domain_capability_receipt.json`. It found the public source
trees for `opensource_31` and `atlas_dual_pdk`, the bundled ngspice-42 binary,
and no Xyce, Spectre or HSPICE executable. Its `ranking_eligible` field is
false because no matched SPECTRA/AnaFlow performance cells are implied by a
capability scan.

The follow-up receipt `results/cross_domain_capability_receipt_v2.json` adds
the AnalogGym checkout and records its immutable source commit. A three-PDK
TT-only adapter run is archived in
`results/public_suite_3pdk_tt_v2.md` and
`results/public_suite_3pdk_tt_v2.json`. It uses 300 simulations per cell and
seeds 0, 1 and 2 for SPECTRA and the clean-room AnaFlow adapter. The run is
not ranking-eligible because the public configs do not expose a common PVT
evaluator and the clean-room adapter is not the published AnaFlow code.

`results/analoggym_amp_tt_smoke.md` records a separate AnalogGym SKY130
testbench smoke with immutable source, PDK and simulator hashes. It verifies
the public netlist can execute under ngspice-42, while explicitly excluding
sizing, PVT and ranking claims.

The ATLAS GF180 capability check is archived in
`results/atlas_gf180_ngspice42_capability.md`. The public GF180 model tree was
prepared on the server, but the ATLAS netlist emitted an undefined
`par_vth=$`/`var_vth` model expression under ngspice-42. ATLAS specifies
ngspice 44.2, so this failed cell is excluded from the ranking.

The cross-simulator capability receipt is archived in
`results/cross_simulator_capability_receipt.json`. It records the official
ngspice-44.2 binary and Xyce 7.10 serial binary hashes, their source-build
provenance, and the one-cell Xyce AnalogGym smoke. The smoke is deliberately
not ranking-eligible because it does not satisfy the frozen budget, PVT-grid,
and multi-seed requirements.

## Capability audit before a run

Run the receipt generator on the server before scheduling a matrix. It records
the manifest digest, source-tree digests, repository commits and detected
simulator versions. A receipt is not a result table and its
`ranking_eligible` field is always false.

```bash
python3 scripts/cross_domain_capability_audit.py \
  --manifest data/bench/cross_domain_manifest.json \
  --source-root opensource_31=/root/autodl-tmp/bench_sources/opensource-analog-circuits \
  --source-root atlas_dual_pdk=/root/autodl-tmp/bench_sources/atlas \
  --output results/cross_domain_capability_receipt.json
python3 -m py_compile spectra/bench/cross_domain.py scripts/cross_domain_capability_audit.py
```

## Common metrics and budgets

Every comparable cell records `task_id`, `source_commit`, `topology_digest`, `pdk_id`, `simulator_id`, `simulator_version`, `seed`, `llm_calls`, `simulations`, `first_pass_simulations`, `wall_seconds`, `tokens_in`, `tokens_out`, `cost_usd`, `tt_pass`, `pvt_pass`, `tt_violation_mean`, `tt_violation_median`, `pvt_violation_mean`, `pvt_violation_median`, `crash` and `failure_taxonomy`. Normalized violation is the mean positive spec residual after each metric is divided by its task-specific tolerance. PVT success means every declared corner passes.

The shared contract is implemented in `spectra/bench/cross_domain.py`. It
creates the canonical 45-condition PVT grid, aggregates per-corner metrics and
rejects missing values as infinite violation. Before ranking a result table,
run `scripts/validate_cross_domain_cells.py`. The validator requires exact
simulation and call budgets, unique task-method-seed cells, a complete PVT
grid and finite mean/median violation fields.

The sharded AnalogGym jobs are merged only by
`scripts/merge_analoggym_shards.py`. The merger requires all six cells in the
three-seed by two-method matrix and refuses duplicate cells, wrong budgets,
missing corners, or non-finite violations.

```bash
python scripts/merge_analoggym_shards.py \
  --input results/analoggym_pvt_s*_spectra.json \
          results/analoggym_pvt_s*_anaflow_cleanroom.json \
  --output results/analoggym_pvt_merged.json
```

AnaFlow is a clean-room adapter in this repository. Its paper reports two PTM45/ngspice op-amp demonstrations and sample-efficiency fields, not a cross-domain TT/PVT table. A domain-level claim therefore requires a matched AnaFlow adapter run on every public stratum.

## Public sources

- AnalogGym, ICCAD 2024, https://arxiv.org/abs/2409.08534 and https://github.com/CODA-Team/AnalogGym
- AMPICBench, https://github.com/AMPICLab/AMPICBench
- Open-Source Analog Circuit Sizing Benchmark Suite, https://github.com/jialinlu/opensource-analog-circuits
- ATLAS, https://github.com/youngmin0oh/atlas
- Analog Design Bench, https://huggingface.co/datasets/Arcadia-2026/analog-design-bench
- AnaFlow, ICCAD 2025, https://arxiv.org/abs/2511.03697
