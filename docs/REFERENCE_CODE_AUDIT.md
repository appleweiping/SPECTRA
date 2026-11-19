# Reference code audit for SPECTRA

This audit records the source review of the two requested reference projects and
the current SPECTRA implementation. The reference checkouts were cloned into
`work/reference_sources/` on the E: drive for source inspection only. No local
simulator or model run was started.

## Audit scope

| Source | Revision inspected | Main implementation areas |
|---|---|---|
| `cascode-ai/analog-canvas` | shallow checkout of the public `main` head | `packages/model`, `project-protocol`, `edit-engine`, `derived`, `netlist`, `simulation-service`, `agent-adapter`, `worker`, `apps/editor`, `eda` |
| `Arcadia-1/virtuoso-bridge-lite` | shallow checkout of the public `main` head | `src/virtuoso_bridge`, `mcp_server.py`, `tools`, `tests`, `examples`, `skills` |
| SPECTRA | current E: checkout | `spectra/agent`, `spectra/sim`, `spectra/bench`, `scripts`, `results`, `docs` |

The Analog Canvas checkout contains 3,826 tracked files and Virtuoso Bridge
Lite contains 485 tracked files. The review focused on executable contracts and
the modules that carry topology, simulation, remote execution, diagnostics and
artifact identity. Generated assets and duplicated test fixtures were not
treated as independent framework components.

## Analog Canvas implementation findings

Analog Canvas is a local-first schematic system. Its persisted circuit model is
separate from projections used for connectivity, geometry and diagnostics.
`packages/model` defines stable IDs, cells, instances, pins, routes, nets,
annotations and simulation folders. `packages/project-protocol` provides
versioned project files and migrations. `packages/edit-engine` applies atomic
transactions, repairs routes and preserves undoable edit boundaries.
`packages/derived` computes logical connectivity and presentation geometry from
the persisted document instead of storing competing copies of those facts.

The simulation service is contract-driven. `packages/simulation-service/src/contract.ts`
uses strict Zod schemas for environments, prepared inputs, operations, runs,
artifacts, batches, sweeps, outputs and capabilities. The schemas represent
corner, temperature, variable and parameter axes explicitly. `executor.ts`
checks simulator identity, input revision, profile identity, entry evidence and
collection completeness. Invalid results are rejected without silently starting
a second run. `execution-receipt.ts` binds the streamed result to a run token,
byte length, SHA-256 digests, metadata and the executed-file set.

The Agent layer exposes a typed snapshot and transaction interface through MCP,
HTTP and an OpenAPI description. `agent-adapter/src/snapshot.ts` builds a
canonical snapshot, computes topology-derived context on demand and returns
stable geometry and diagnostic records. `request-contract.ts` turns schema
failures into one redacted, versioned error envelope. The adapter keeps the
browser/editor model and the Agent model on one operation contract rather than
letting a language model mutate raw JSON.

The netlist and simulation packages add deterministic SPICE/Spectre conversion,
device facts, signal semantics, prepared input files and result catalogs. The
Worker and hosted executor add managed-run state, bounded artifacts and
capability discovery. The repository also includes a large contract-test corpus
for migrations, transactions, netlist import, run identity, artifact digest,
transport parity and simulation result parsing.

### Reusable ideas for SPECTRA

1. Add a versioned `SizingTaskSnapshot` with stable task, topology, PDK,
   simulator, metric and budget identity. Store the canonical JSON and its
   digest beside every raw result.
2. Make the simulator adapter return a strict result envelope containing the
   prepared netlist, executed files, PVT axis, measurements, violations,
   timeout state and simulator identity. The existing shard mergers should
   validate this envelope before aggregation.
3. Represent topology and connectivity as a derived graph with a stable hash.
   This prevents a sizing result from being attributed to a changed netlist or
   a different pin ordering.
4. Port the transaction/error boundary to intent edits. A refine step should
   be an admitted operation with a request ID, previous snapshot revision,
   changed intent variables and a deterministic replay record.
5. Keep artifact digests and run-local paths in the evidence manifest. A PVT
   result should be independently replayable from the recorded prepared deck,
   corner definitions and parser version.

## Virtuoso Bridge Lite implementation findings

Virtuoso Bridge Lite is a Python transport and automation framework for
Cadence Virtuoso and Spectre. `src/virtuoso_bridge/transport` supports local
execution, SSH tunnels, Paramiko backends, remote roles, transfer plans and
path resolution. `daemon_setup.py`, `daemon_guard.py` and `daemon_auth.py`
provide ownership, token and lifecycle checks. `env.py`, `profile.py` and
`profile_inventory.py` make installation and PDK selection explicit.

The bridge exposes a CLI, Python API and an optional stdio MCP adapter. The MCP
server has protocol negotiation, pagination, bounded text/structured output,
per-tool rate limits and stderr-only logging. Its safe-root policy rejects
paths outside the checkout, working area, PDK roots and explicitly configured
Cadence directories. It redacts token material before returning diagnostics.

The Virtuoso modules are layered. `virtuoso/basic` handles SKILL deployment and
daemon requests. `virtuoso/schematic` has typed instance, pin, parameter,
manifest, netlist, reader and planner objects. `schematic/planner.py` models
hard and soft placement constraints, differential pairs and conflict
diagnostics. `virtuoso/symbol` and `virtuoso/layout` operate on symbols,
geometry, groups and stream-out. `virtuoso/maestro` handles test jobs,
waveforms, histories and Monte Carlo records. `spectre/runner.py` builds
bounded command lines, supports named Spectre modes, captures PSF output and
parses diagnostics. `spectre/parsers.py` and `parsers_fast.py` preserve scalar
and waveform semantics.

`unified_search.py` builds an SQLite FTS5 index over SKILL entries, Cadence
documentation, topic maps, libraries, cells and project files. This prevents
agents from repeatedly scanning large PDK trees. The test suite covers remote
paths, SSH lifecycle, daemon ownership, parsers, schematic semantics, layout,
Maestro, MCP contracts and recovery behavior.

### Reusable ideas for SPECTRA

1. Replace simulator-specific shell calls with a `SimulatorAdapter` contract
   covering capability discovery, prepare, run, cancel, collect and parse.
   ngspice-44.2 and Xyce-7.10 can implement this contract first. A future
   Spectre/Virtuoso adapter can use the same receipt schema when a licensed
   environment is available.
2. Carry a per-run session ID, request ID and ownership token through remote
   execution. Recovery must read an admitted run and never silently submit a
   second simulation after an unknown transport failure.
3. Use safe path roots and explicit PDK profiles in the remote runner. Include
   the resolved simulator binary, PDK root, netlist digest and parser version
   in every receipt.
4. Adopt the bridge's structured diagnostic vocabulary for simulator errors,
   timeout, missing metrics, non-finite values and parser mismatch. This makes
   failure rates comparable across PVT and simulator strata.
5. Add an indexed knowledge/search layer for PDK facts, topology cards,
   previous failure signatures and public benchmark metadata. The index should
   carry source URLs, versions and digests so retrieval is auditable.

## SPECTRA implementation findings

SPECTRA already has a coherent sizing loop. `spectra/agent/dsl.py` gives the
model a bounded design-intent program and a `gm/Id, L, Id` lookup-table API.
`sandbox.py` and `sandbox_worker.py` execute programs with normalized parameter
bounds and report intent usage. `diagnose.py` converts simulation margins,
operating regions, prediction discrepancies and finite-difference sensitivities
into structured causal evidence. `knowledge.py` retrieves topology and failure
cards. `spectra_agent.py` combines design, diagnosis, refinement and
infeasibility decisions. `spectra/sim/evaluate.py` defines the 45-condition
PVT grid, measurements and normalized violations. The benchmark and merge
scripts enforce exact simulation/call budgets and finite PVT evidence.

The current framework has three strong research components. The intent program
is an interpretable representation between the LLM and transistor dimensions.
Causal diagnosis exposes actionable device-level causes. PVT-aware refinement
uses bounded numerical search after the LLM has selected a topology and program.
Knowledge cards make topology and PDK facts explicit and versionable. The
component mechanism audit already tests these axes over six domains and three
seeds, retaining mixed endpoint effects.

## Differences and quality gaps to close

The reference projects provide production-grade typed state, transport and
artifact contracts. SPECTRA's research code is deterministic and auditable at
the benchmark level, but its raw sizing records do not yet form one universal
run envelope with prepared-deck digests, topology hashes, cancellation state and
parser identity. The public AnalogGym and ATLAS adapters now record strict
budgets and PVT conditions, but the full multi-PDK, multi-family, multi-
simulator matrix remains smaller than a domain-wide claim. The AnaFlow rows are
protocol-aligned clean-room adapters because an official implementation was not
available. The current result therefore supports benchmark-scoped comparisons.

The highest-value implementation work is to make the run/evidence contract as
strong as the two references while preserving the SPECTRA research novelty:

- `SizingTaskSnapshot` and `SimulationReceipt` schemas with canonical digests.
- Adapter capability records for PDK, topology, simulator, corner set and
  metric parser.
- Transactional intent revisions and replayable refinement traces.
- Cross-simulator metric normalization with explicit phase/unit conversions.
- Public benchmark manifests that include source commit, license, topology
  count, PVT definition, budget, seeds and known failure conditions.

These changes improve reproducibility and framework quality without claiming
that a clean-room adapter reproduces an unavailable paper implementation.

## Proposed SPECTRA framework synthesis

The completed framework should expose one pipeline:

```text
task snapshot → topology/PDK profile → intent program → deterministic netlist
→ simulator adapter → typed measurement/violation receipt → causal diagnosis
→ PVT-aware refinement → independent verifier → immutable evidence manifest
```

The novel contribution remains the coupling of interpretable intent, causal
diagnosis and PVT-aware refinement. The reference code suggests a fourth
framework-quality contribution, an auditable run contract that makes every
simulation and every refinement revision replayable across simulators.

## Audit conclusion

Analog Canvas contributes typed model/edit/simulation contracts and durable
evidence semantics. Virtuoso Bridge Lite contributes remote transport,
Cadence/Spectre adaptation, diagnostics and session safety. SPECTRA contributes
the sizing intelligence and PVT refinement policy. The three systems are
complementary. The reference code should inform contracts, adapters and
reproducibility layers, while SPECTRA's scientific claim must continue to be
based on measured public matrices and preserved negative evidence.

## Additional 2026 source and code audit

The following source snapshots were checked out under `work/reference_sources/`
on E: for benchmark and implementation inspection. They remain source references,
not vendored dependencies, and no local simulator or model was run.

| Source | Code-level observations | SPECTRA integration decision |
|---|---|---|
| AMPICBench (`4ba5fc7`) | Sky130A ngspice netlists, `corners.json`, operating-region summaries, AC/STB testbenches and metric extraction tools. The repository separates source netlists, evaluated-cell netlists and result plots. | Add source-native corner receipts and operating-region diagnostics to public benchmark manifests. |
| SGAnalog (`ebd7e69`) | Commit-pinned Tiny Tapeout circuits, graph-deduplicated splits, text-blinded SVGs, pinned ngspice-45.2 execution and post-cutoff leakage checks. The sizing task compares metrics against fabricated human designs. | Add provenance-pinned held-out tasks and leakage-aware splits when expanding from sizing into topology or tapeout-derived evaluation. |
| AnalogGym-Opt (`10093e34`) | `AmpEnv`/`LdoEnv` expose YAML-configured design variables, reward objectives, GRPO/R-GNN policy training, Pareto tracking and optional PVT proxy modes. | Include learned multi-objective and Pareto baselines under the same budget, and keep proxy PVT separate from full-corner verification. |
| opensource-analog-circuits (`e8308aa`) | 31-circuit `NgspiceBenchmark`, JSON metric specs, GA/BO examples, ASAP7 and Sky130 variants, plus a separate five-LDO mismatch package with 200-sample train and 500-sample validation seeds. | Preserve PVT, mismatch and nominal objectives as distinct axes with independent validation seeds and anti-gaming rules. |
| PARADIGM-Analog-EDA (`32d81da`) | TuRBO plus NSGA-II builds topology-specific Pareto databases, a topology classifier predicts suitable cells, and P2C Net provides warm starts. The paper package ships 1,818 records and measures cold versus warm simulation counts. | Add database-reuse and cold-start transfer rows to the external-baseline manifest and report database construction cost separately. |

These audits expand the framework contract while preserving the single SPECTRA
method in the primary claim. They do not convert source-only inspections into
measured benchmark results.
