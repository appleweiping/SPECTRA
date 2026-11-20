# SPECTRA — Spec-to-Robust Analog Circuit Synthesis with LLM Agents

End-to-end agentic analog circuit generation: natural-language specification → topology → device sizing →
PVT-robust (45 conditions) + mismatch-verified SPICE netlist on the open SkyWater SKY130 PDK. The checked-in
server receipts use ngspice-44.2 and Xyce-7.10 where the corresponding track supports both simulators.

* **SPECTRA agent** (`spectra/agent`): the LLM writes *design-intent programs* that size devices from
  (gm/Id, L, Id) via PDK lookup tables and predict their own performance; a deterministic layer executes, checks
  (ERC), simulates and returns a device-level diagnosis; the LLM picks Refine / Edit / Declare-infeasible;
  refinement runs CMA-ES in the program's intent space with adaptive worst-corner PVT closure.
* **SPECTRA-Bench** (`data/bench`, `spectra/sim`, `spectra/bench`): 12 circuit families (op-amp, amplifier, TIA,
  current mirror, LDO, bandgap reference, CT comparator, StrongARM latch, VCO, filters, Schmitt trigger, op-amp
  applications) with testbenches, certified tiers (feasibility certificates from expert templates), a designer tier,
  45-condition PVT grid and per-instance mismatch Monte Carlo (an early infeasible-control tier was withdrawn).
* **Baselines** (`spectra/baselines`): the repository keeps legacy controls and oracle implementations for audit
  reproducibility. They are excluded from the primary claim. The primary comparison is the native SPECTRA framework
  against seven paper-backed external sizing frameworks in `results/external_primary_sota.md`.
* **Strict paper sizing track** (`data/bench/paper_sizing_tasks.jsonl`): SPECTRA plus AnalogCoder, ADO-LLM, AnaFlow,
  Artisan, AutoSizer, ATLAS and GLOVA use one frozen-topology protocol. The seven external rows are clean-room
  adapters with paper and venue metadata in `data/bench/paper_sizing_manifest.json`. SPECTRA uses the native
  diagnosis, knowledge and bounded-refinement loop through a fixed-topology adapter. All eight rows receive the same
  bounds, 300 simulation-unit budget and 12-call LLM cap. The previous EXT7g framework-and-control matrix remains
  a separate diagnostic appendix.
  The final matched extension contains 864 cells, eight rows across 36 tasks and three seeds. In the primary
  eight-row aggregate SPECTRA reaches 0.806 TT and 0.194 PVT, while AnaFlow reaches 0.870 TT and 0.306 PVT.
  The independently reported post-fix SPECTRA-PVT-staged variant reaches 0.815 TT, 0.222 PVT and 0.5009 mean PVT violation.
  These are track-scoped measurements and do not establish universal analog-sizing SOTA.
  The primary-row contract, metric definitions, statistical scope and exclusions are fixed in
  `docs/MAIN_COMPARISON_PROTOCOL.md`.
  A 92-task, 12-family external-only expansion is documented in `results/EXTERNAL_EXPANSION_AUDIT.md`; the complete
  external matrix contains 2,208/2,208 cells. The family-policy and union-top-k4 SPECTRA candidates each contain
  276/276 cells with three seeds. These results are benchmark-scoped and do not establish universal analog-sizing SOTA.
* **Cross-domain public benchmark track** (`docs/CROSS_DOMAIN_PROTOCOL.md`, `data/bench/cross_domain_manifest.json`):
  the frozen extension targets AnalogGym, AMPICBench, the 31-circuit public suite, SGAnalog tapeout-derived tasks,
  ATLAS dual-PDK tasks, Analog Design Bench, LOADBench and AnalogPortBench. Server receipts and a three-PDK TT-only adapter run are archived in
  `results/cross_domain_capability_receipt_v6.json` and `results/public_suite_3pdk_tt_v2.md`. AnalogGym and GF180
  now have matched ngspice-44.2/Xyce-7.10 and strict PVT receipts. The server-only public-source expansion adds
  32/32 opensource configs, 9 AMPICBench decks across source corners, a 3-seed PTM180/BJT TT adapter, a matched
  Xyce BJT receipt, and 3-seed 45-condition ASAP7 LDO, SKY130 LP-opamp and SKY130 LDO receipts. The measured-scope
  table is `results/public_scope_sota_summary.md`. The universal-coverage contract and unmeasured strata are
  recorded in `docs/TOPCONF_LITERATURE_AUDIT.md`. The complete pre-registered
  `spectra_staged` sensitivity now covers both AnalogGym amplifier topologies,
  three seeds, 300 units and 45 verifier conditions. It reaches TT/PVT
  `1.000/1.000` on HoiLee and `1.000/0.667` on Leung, compared with the
  matched clean-room AnaFlow rows at `1.000/0.667` and `1.000/0.333`.
  The two topology receipts and endpoint comparisons are
  `results/analoggym_pvt_staged_comparison.{json,md}` and
  `results/analoggym_leung_pvt_staged_comparison.{json,md}`. This is a
  benchmark-scoped sensitivity arm with TT ties, so it remains outside the
  frozen primary row and the literal XSOTA-1 gate.
* **Component mechanism track** (`data/bench/component_mech_manifest.json`): six circuit domains, five matched
  SPECTRA arms and three seeds record structured diagnosis attribution, intent provenance, active-set refinement
  traces and versioned knowledge-card retrieval alongside TT/PVT success and efficiency metrics.
* **Top-conference literature contract** (`docs/TOPCONF_LITERATURE_AUDIT.md`): a source-linked audit of AnalogGym,
  AnalogAgent, AutoSizer, NEMESIS2.0, AgenticSizing, Long-Horizon Analog Design Bench, PVTSizing 2.0,
  AnalogScout, ATLAS, AnaFlow, Analog Canvas and Virtuoso Bridge Lite. It fixes the benchmark, baseline, component, metric, robustness,
  efficiency and provenance requirements used by the handoff. The 2026 read-level ledger in
  `docs/refs/READ_STATUS_2026.md` distinguishes full-paper/code inspection from abstract-only leads. The
  companion `docs/refs/LIT_SURVEY_2026_ADDENDUM.md` records the latest AutoSizer, AgenticSizing, AnalogScout,
  PVTSizing 2.0, CRAFT, GFlow-SAEA, AnalogGym-Opt, NEMESIS2.0, AnalogAgent and Long-Horizon benchmark evidence.

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

## Extended reproducibility contract

The public expansion follows one strict cell schema. A cell is identified by source task, topology digest, PDK/model profile, simulator version, method, seed, and budget. Its receipt contains the prepared deck digest, corner list, per-corner measurements, normalized violations, first-pass simulation count, LLM call count, wall time, token usage when available, crash state, and failure taxonomy. The merger refuses duplicate cells, missing seeds, wrong budgets, non-finite violations, or incomplete declared corner grids.

The common matched budget is 300 simulator evaluations, 12 LLM calls, and seeds 0, 1, and 2. The nominal result is called TT. A PVT result is ranking-eligible only when the source exposes a compatible multi-condition contract and the independent verifier evaluates every declared condition. Source decks that provide one operating point remain useful capability evidence and are explicitly excluded from PVT ranking.

### Public matrix

| Track | PDK/model | Simulator | Task evidence | Conditions | Tier |
|---|---|---|---|---:|---|
| AnalogGym HoiLee | SKY130 | ngspice-44.2 | public amplifier topology | 45 | matched PVT |
| AnalogGym Leung | SKY130 | ngspice-44.2 | public LDO/topology | 45 | matched PVT |
| AnalogGym HoiLee/Leung | SKY130 | Xyce-7.10 | translated public decks | 45 where parser-equivalent | matched PVT |
| open-source LP opamp | SKY130 | Xyce-7.10 | full Xyce AC/45-condition receipt; translator validated separately | 45 | matched PVT |
| ATLAS | GF180MCU | ngspice-44.2 | public ATLAS task digest | 17 source conditions | matched PVT |
| open-source LP and LDO | SKY130 | ngspice-44.2 | source-native configurations | 45 | matched PVT |
| open-source ASAP7 LDO | ASAP7 | ngspice-44.2 | source-native configuration | 45 | matched PVT |
| open-source PTM180 | PTM180 | ngspice-44.2 | op-amp configuration | 1 | TT capability |
| open-source BPTM45 | PTM45 BSIM4 | ngspice-44.2 | gh_autockt_opamp | 1 | TT capability |
| open-source BJT | public BJT model | ngspice-44.2 and Xyce-7.10 | CE amplifier | 1 | TT capability |
| AMPICBench | SKY130A | ngspice-44.2 | nine source decks, 135 source-corner runs | 15 per deck | capability |
| SGAnalog | SKY130A | native ngspice-44.2 harness; pinned ngspice-45.2 source protocol | 17 tapeout-derived sizing tasks | source-defined | tapeout sizing |
| Analog Design Bench v2 | SKY130 | source manifest audit; isolated verifier is external to the source repository | 50 designer-contributed tasks | task-defined PVT/mismatch | capability audit |
| LOADBench | SKY130 | public evaluation scripts audited at pinned commit; dataset and netlists not downloaded | >100 op-amp topologies, six ML tasks | source-defined | capability audit |
| AnalogPortBench | GF180→SKY130 transfer | source code audited; no SPECTRA transfer run | 54 porting tasks over 10 circuits, including infeasible specifications | five-corner source reference | capability audit |
| IHP SG13G2 Open PDK | SG13G2 130 nm BiCMOS | ngspice-44.2 with server-built OpenVAF OSDI models | 7,267 observed PDK files (7,290 tracked entries), MOS/HBT/passive model inventory, native OP smoke | no common sizing task | capability audit |

The PTM45 receipt is results/public_v7_ptm45_merged.json and its readable audit is results/public_v7_ptm45_merged.md. The full Xyce SKY130 LP runner receipt is results/opensource_xyce_sky130_lp_sizing.json and the strict merged receipt is results/public_v8_sky130_lp_xyce_merged.json. Together they contain six method-seed rows with 45 parsed conditions. The source deck has no matched process-corner library, so TT success and TT violation are reported while PVT success remains inapplicable. The receipt predates automatic sibling-deck translation, while direct translated SKY130 and PTM180 decks have independent Xyce artifacts and parser checks. The corrected adapter preserves the SPICE title line before inserting temperature control, and the raw failed pre-fix shards remain archived.

### Framework components

SPECTRA has four independently testable scientific mechanisms.

1. Diagnosis converts simulator evidence into device-level causes and suggested actions.
2. Intent programs provide a typed intermediate representation between language output and transistor dimensions.
3. Adaptive refinement promotes worst corners and sensitive variables into bounded CMA-ES search.
4. Knowledge cards provide versioned, source-linked topology and PDK facts.

The component audit uses matched tasks, seeds, budgets, and verifier. It reports TT/PVT success, mean and median normalized violation, first-pass simulations, calls, wall time, structured events, active-variable traces, and paired confidence intervals. A component is credited only when its predeclared mechanism axis improves the recorded metric. Mixed endpoint effects remain visible.

### External baselines

The main external table has seven paper-backed rows beside SPECTRA: AnalogCoder, ADO-LLM, AnaFlow, Artisan, AutoSizer, ATLAS, and GLOVA. Each row has a paper or official-project citation, implementation-status label, fixed task text, identical parameter bounds, 300/12/3 resource contract, common simulator, common parser, and independent verifier. Clean-room adapters are labelled as such. Internal controls and oracle search are appendix diagnostics and are never counted as external frameworks.

### Metrics

The primary electrical endpoints are TT success, all-corner PVT success, mean normalized violation, median normalized violation, and worst-corner violation. Efficiency and reliability metrics are simulations to first feasible candidate, total simulator evaluations, LLM calls, wall time, tokens and cost when exposed, crash rate, timeout rate, parser failures, convergence failures, legality failures, cross-seed variance, task-cluster bootstrap intervals, paired win/loss/tie counts, and Holm-corrected tests. Mismatch yield is reported separately when a source benchmark provides a train/validation Monte Carlo contract.

### Server-only execution

All simulator and model runs use the remote server. The local E: checkout is reserved for source review, report generation, and synchronization.
The westc host is the active experiment server. The user-provided westb host was checked read-only and
contains no detected simulator or PDK installation, so no experiment is assigned there. Its capability
boundary is recorded in `results/westb_capability_receipt.json`.

~~~bash
ssh -p 39737 root@connect.westc.seetacloud.com
cd /root/autodl-tmp/spectra-analog-agent
source /root/miniconda3/etc/profile.d/conda.sh
conda activate spectra

python scripts/summarize_public_scope.py
python scripts/summarize_public_v2.py
python scripts/validate_cross_domain_cells.py
python scripts/smoke_contracts.py
python scripts/audit_xsota_gate.py
python scripts/cross_domain_capability_audit.py \
  --manifest data/bench/cross_domain_manifest.json \
  --source-root analoggym_amp_ldo=/root/autodl-tmp/bench_sources/AnalogGym \
  --source-root opensource_31=/root/autodl-tmp/bench_sources/opensource-analog-circuits \
  --source-root ampicbench_public=/root/autodl-tmp/bench_sources/AMPICBench \
  --source-root sganalog_tapeout=/root/autodl-tmp/bench_sources/SGAnalog \
  --source-root atlas_dual_pdk=/root/autodl-tmp/bench_sources/atlas \
  --source-root analog_design_bench=/root/autodl-tmp/bench_sources/analog-design-bench \
  --source-root loadbench_ml=/root/autodl-tmp/bench_sources/LOADBench-Scripts \
  --source-root analog_port_bench=/root/autodl-tmp/bench_sources/AnalogPortBench \
  --simulator ngspice=/root/autodl-tmp/sim-build/ngspice-44.2-install/bin/ngspice \
  --simulator xyce=/root/autodl-tmp/sim-build/xyce-7.10-serial-install/bin/Xyce \
  --output results/cross_domain_capability_receipt_v6.json
python scripts/audit_analog_design_bench.py \
  --source-root /root/autodl-tmp/bench_sources/analog-design-bench \
  --output results/analog_design_bench_v2_source_audit.json
python scripts/audit_sganalog_source.py \
  --sg-root /root/autodl-tmp/bench_sources/SGAnalog \
  --output results/sganalog_source_audit.json
python scripts/audit_loadbench_scripts.py \
  --source-root /root/autodl-tmp/bench_sources/LOADBench-Scripts \
  --output results/loadbench_scripts_source_audit.json
python scripts/audit_analog_port_bench.py \
  --source-root /root/autodl-tmp/bench_sources/AnalogPortBench \
  --golden-json /root/autodl-tmp/bench_sources/AnalogPortBench/benchmark/results/golden_audit.json \
  --golden-status partial_timeout --completed-jobs 243 --total-jobs 250 \
  --timeout-seconds 900 \
  --build-root /root/autodl-tmp/bench_sources/AnalogPortBench/build \
  --output results/analog_port_bench_source_audit.json
python scripts/run_analog_port_bench_smoke.py \
  --source-root /root/autodl-tmp/bench_sources/AnalogPortBench \
  --pdk-root /root/autodl-tmp/analogport_pdk \
  --ngspice /root/autodl-tmp/sim-build/ngspice-44.2-install/bin/ngspice \
  --python /root/miniconda3/bin/python3.12 \
  --circuit ota_tele --golden-name ota_tele_1v8 --tech sky130_lvt \
  --vdd 1.8 --corner tt --output results/analog_port_bench_source_smoke.json
python scripts/test_xyce_ac_translator.py
~~~

For a public source cell, run both methods with the same seed, simulator, and budget, then merge only after all six seed-method cells are present.

~~~bash
python scripts/run_public_config_pvt.py --source-root /root/autodl-tmp/bench_sources/SOURCE_REPO --config /root/autodl-tmp/bench_sources/SOURCE_REPO/circuits/CONFIG/config.json --simulator /root/autodl-tmp/sim-build/ngspice-44.2-install/bin/ngspice --track-id TRACK --pdk PDK --budget 300 --seeds 0,1,2 --methods spectra,anaflow_cleanroom --output results/TRACK_merged.json --pvt-mode canonical
python scripts/merge_public_config_shards.py --input results/TRACK_s*_spectra.json results/TRACK_s*_anaflow_cleanroom.json --output results/TRACK_merged.json
~~~

The config-driven runner also accepts `--search-profile spectra_staged` for a
pre-registered sensitivity arm. Under the 300-unit cap it uses 50 nominal
warm-start evaluations and 50 candidates evaluated on five fixed screening
corners. Keep this output in a separate sensitivity receipt and compare it to
the matched AnaFlow row without replacing the frozen primary result.

For the AnalogGym sensitivity audit, `scripts/run_analog_gym_pvt.py` accepts
`--search-profile spectra_staged`. This is a fixed 50-nominal/50-five-corner
screening schedule under the same 300-unit cap, with the five corners and the
independent 45-condition verifier recorded in each receipt. It is a sensitivity
arm until the complete matched multi-seed rerun is finished.

The same profile was exercised against the public-config runner on the
source-native `hoilee_affc` SKY130 configuration. The six-unit server smoke
completed its search phase and prepared 44/45 verifier decks before the
`fs_125C_1.62V` ngspice process exceeded the operator timeout at 519 seconds.
`results/public_config_staged_smoke_timeout.{json,md}` records the timeout,
source and runner commits, screening corners, and ranking exclusion. It has no
AnaFlow counterpart and is excluded from the public ranking and XSOTA audit.

SGAnalog uses the pinned upstream task file eval/sizing/tasks.jsonl and preserves the author testbench. Its complete GPT-6.1-sol receipt is results/sganalog_native_gpt61_multiseed.json with 51 rows, 48 converged and 3 failed retained in the denominator. The three failures are the sz016 std-cell include path on the analog-only PDK, and are preserved rather than scored as successes. Xyce runs retain mt0, prn, translated control, and parser receipts. AMPICBench capability evidence retains source-corner artifacts but is not promoted to sizing ranking until a common objective and verifier exist.

Analog Design Bench v2 is handled by `scripts/audit_analog_design_bench.py`. The server-side
source audit records the frozen 50-task manifest, instruction hashes, task-declared metrics,
PVT/mismatch flags, and the pinned source commit. Its isolated verifier and submitted circuit
artifacts are external to the cloned repository, so the resulting receipt is capability-only.
It is not converted into a 300/12 SIZ7g score and does not supply a fabricated pass rate.

LOADBench is handled by `scripts/audit_loadbench_scripts.py`. The server-side audit pins the
five public evaluation modules and their hashes, records the missing script-repository license,
and runs synthetic checks for top-k/MFHR and inverse-sizing metrics. The roughly 40 GB public
dataset is intentionally not downloaded, and no LOADBench result is promoted to a SIZ7g or
XSOTA-1 row without source-native netlists, a license decision, and the same independent
electrical verifier.

AnalogPortBench is registered as a separate cross-PDK transfer capability track. Its 54 tasks
cover ten source circuits, five source corners, feasible transfers, and deliberately infeasible
specifications. The pinned source inspection is documented in `docs/refs/REPO_ANALYSIS.md`.
Because the public transfer evaluator and task artifacts are not part of the SPECTRA checkout,
this track remains outside the matched SIZ7g and XSOTA-1 aggregates until a server-side adapter
and independent verifier receipt exist. The source evaluator's five-corner golden replay is
attached only as benchmark-integrity evidence. The current server attempt completed 243 of 250
jobs before the upstream 900-second per-job timeout classified eight high-cost corners as unresolved.
That timeout receipt is retained explicitly and is not treated as a complete golden pass. It is not
a SPECTRA or AnaFlow answer result. A reproducible one-task source-native
smoke harness is available as `scripts/run_analog_port_bench_smoke.py` and
was run on the server for `ota_tele_1v8` under SKY130/ngspice-44.2. Its
receipt is `results/analog_port_bench_source_smoke.json` with a readable
summary in `results/analog_port_bench_source_smoke.md`. The smoke passes the
source evaluator checks while remaining explicitly ranking-ineligible because
it uses a bundled golden reference and has no matched transfer verifier.

The IHP SG13G2 audit is capability-only. The server checkout pins the
IHP Open PDK at commit `e73adb4045731ddec21634146d536380057f6a26` and finds
the MOS/HBT/passive model sources. We compiled PSP103, PSP103-NQS, R3-CMC,
MOSVAR, CMOMI and CMOMF with the OpenVAF 0.3-compatible binary and loaded the
six OSDI artifacts into ngspice-44.2 through a reproducible temporary
`.spiceinit`. The native one-netlist operating-point smoke returned code `0`
with finite output voltage and supply current. Model artifact hashes and the
raw output are retained in `results/ihp_sg13g2_capability_receipt.{json,md}`
and `results/ihp_sg13g2_native_smoke.stdout`. This is runtime capability
evidence, not a sizing result. A matched Xyce-7.10 probe is also retained and
returns `pdk_deck_unsupported` because the ngspice source deck does not expose
a Xyce-compatible `SG13_LV_NMOS` definition. No SIZ7g or XSOTA-1 score is inferred because
the PDK source has no common sizing task, independent verifier, or matched
AnaFlow cell.

The server-side capability audit can be reproduced without writing experiment
artifacts to the local machine. From the pinned IHP checkout, compile the
Verilog-A models with the OpenVAF 0.3-compatible binary, then pass the generated
OSDI directory to the audit. The audit excludes generated `osdi/` binaries from
the source-tree digest, writes its temporary `.spiceinit` under the server work
directory, and records every OSDI SHA-256 in the receipt.

~~~bash
cd /root/autodl-tmp/bench_sources/IHP-Open-PDK/ihp-sg13g2/libs.tech/verilog-a
PATH=/root/autodl-tmp/tools/openvaf-osdi03:$PATH ./openvaf-compile-va.sh --compile-model-generic
cd /root/autodl-tmp/spectra-analog-agent
/root/miniconda3/bin/python scripts/audit_ihp_sg13g2.py \
  --pdk-root /root/autodl-tmp/bench_sources/IHP-Open-PDK \
  --simulator /root/autodl-tmp/sim-build/ngspice-44.2-install/bin/ngspice \
  --xyce /root/autodl-tmp/sim-build/xyce-7.10-serial-install/bin/Xyce \
  --osdi-dir /root/autodl-tmp/bench_sources/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/osdi \
  --work-root results/_ihp_sg13g2_smoke_repro_osdi \
  --output results/ihp_sg13g2_capability_receipt.json
~~~

The Xyce AC translator is deterministic and does not alter the source deck in place. It removes ngspice-only control blocks, normalizes `dc=value` and `ac=value` source syntax, braces bare `.param` references required by Xyce, and writes a sibling `.xyce.cir` deck. The parser reads Xyce `.FD.prn` frequency tables and `.ma0` measurements. When a simulator measure reports `FAILED`, it derives the 0 dB crossing by interpolation in log frequency and records the phase convention used for phase margin. A direct audit can be reproduced on the server with the following commands.

~~~bash
python scripts/xyce_ac_translator.py /root/autodl-tmp/bench_sources/opensource-analog-circuits/circuits/sky130_lp_opamp/circuit.cir \
  --translated /tmp/sky130_lp_opamp.xyce.cir
/root/autodl-tmp/sim-build/xyce-7.10-serial-install/bin/Xyce \
  -b /tmp/sky130_lp_opamp.xyce.cir
python scripts/xyce_ac_translator.py /tmp/sky130_lp_opamp.xyce.cir --parse
~~~

The parser reports missing UGF or phase margin when the measured response never crosses 0 dB. Those missing values remain violations in the receipt and are never replaced by an oracle value.

`scripts/audit_xsota_gate.py` is the literal XSOTA-1 checker. It scans every
`*_merged.json` receipt, retains incomplete and capability-only strata in the
denominator, and requires strict SPECTRA leads over the matched AnaFlow row on
TT success, PVT success, mean TT violation, and mean PVT violation. The
generated `results/xsota_gate_audit.{json,md}` is an auditable gate report,
not a claim generator. A benchmark-scoped lead cannot turn an uncovered
stratum or a tie into a domain-level pass.

### Acceptance snapshot

The repository records acceptance as evidence-backed states so a checkout can
be audited without relying on prose. The current snapshot is as follows.

| Gate | Current state | Evidence and interpretation |
|---|---|---|
| `XSOTA-MEASURED-1` | PASS for measured scope | `results/public_scope_sota_summary.md` compares every complete merged receipt under its declared contract. |
| `XCAP-2` | PASS for capability inventory | `results/cross_domain_capability_receipt_v6.json` pins eight public source roots and the isolated ngspice-44.2/Xyce-7.10 binaries. |
| `XPORT-1` | PASS for source inventory, PARTIAL for golden replay | `results/analog_port_bench_source_audit.json` records the complete 54-task inventory. The server replay attempted all 250 golden corner jobs, completed 243, and records eight high-cost timeout jobs in `results/golden_attempt_timeout_receipt.json`. It is not a SPECTRA ranking row. |
| `XSOTA-1` | NOT MET | `results/xsota_gate_audit.json` retains ties, uncovered strata, TT-only rows, and capability-only rows. The latest diagnostics show 9/9 comparable strata non-inferior, only 1/9 strict on all endpoints, and 7 strata with 14 zero-floor ties. A universal claim requires the missing matched electrical cells and strict endpoint leads. |

This table is deliberately generated from receipts rather than optimistic
framework names. Updating a gate requires a new immutable server receipt,
schema validation, and synchronized source on E:, the server, and GitHub.

### Audit and claim policy

The source-linked literature contract is docs/TOPCONF_LITERATURE_AUDIT.md. The implementation-level audit of Analog Canvas and Virtuoso Bridge Lite is docs/REFERENCE_CODE_AUDIT.md. The cross-domain protocol and current statuses are docs/CROSS_DOMAIN_PROTOCOL.md and docs/ACCEPTANCE_CHECKLIST.md.

A successful script exit is not acceptance. PASS requires complete immutable evidence. PARTIAL records a useful but narrower result. NOT MET remains explicit when a universal or domain-level claim is unsupported. Capability scans, one-condition TT rows, parser diagnostics, and clean-room adapters are never silently upgraded to universal SOTA.

The finite matrix supports measured-scope conclusions over the listed source, PDK, topology, simulator, metric, and budget strata. A literal claim over every analog circuit, every PDK, and every simulator would require additional source-native tasks and matching metrics. The repository keeps that boundary visible while continuing to expand the measured matrix.

### Repository map

~~~text
spectra/agent        intent DSL, sandbox, diagnosis, knowledge, agent loop
spectra/sim          netlist compiler, simulator adapters, PVT verifier
spectra/bench        task schemas and cross-domain contracts
spectra/opt          CMA-ES, TPE, Bayesian, and classical search
scripts              runners, strict mergers, validators, reports
data/bench           frozen tasks, source manifests, metric schemas
results              raw shards, merged receipts, summaries, audit logs
paper                anonymous ACM/ICCAD manuscript and figures
docs                  protocols, literature, acceptance, remote environment
pdk/sky130            redistributable model and mismatch profiles
work/reference_sources source-only inspections of requested projects
~~~

### Three-way synchronization

The maintained copies are E:/CodexProjects/spectra-analog-agent, /root/autodl-tmp/spectra-analog-agent on the server, and GitHub appleweiping/SPECTRA. Release checks compare tracked commit hashes across all three copies. Raw evidence is retained on the server and copied into results/ only after schema validation and SHA-256 recording. The synchronization procedure does not use C: or D: for experiment data.

### SGAnalog native harness

~~~bash
source /root/autodl-tmp/spectra-gpt.env
python scripts/run_sganalog_native.py \
  --sg-root /root/autodl-tmp/bench_sources/SGAnalog \
  --generate-model gpt-6.1-sol --model-seeds 0,1,2 \
  --output results/sganalog_native_gpt61_multiseed.json
~~~

The command is intended for the server. It uses the pinned SGAnalog task list, native ngspice, isolated task/seed work directories, retryable GPT requests, response digests, and raw simulator logs. The output is a direct SGAnalog Task 2 audit rather than a SPECTRA optimization result and therefore remains a separate capability tier.
Each direct task-seed cell uses one GPT request plus two native deck executions. The declared 300-simulation and 12-call SIZ7g budget is recorded as a reference contract, not claimed for this direct Task 2 receipt, so these 51 rows are excluded from the SIZ7g ranking aggregate.
