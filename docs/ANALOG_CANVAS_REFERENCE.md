# Analog Canvas reference alignment

This project uses [Analog Canvas](https://github.com/cascode-ai/analog-canvas) as an engineering reference for reproducible circuit-agent workflows. The reference is architectural guidance, not a dependency and not a source of benchmark numbers.

| Analog Canvas principle | SPECTRA implementation | Evidence or boundary |
|---|---|---|
| Circuit facts, authored testbench and specifications are kept together | A benchmark task records family, ports, testbench, quantitative specs and the rendered natural-language request | `data/bench/*.jsonl`, `spectra/bench/nl.py`, `paper/sections/bench.tex` |
| Simulation runs consume an immutable input snapshot and return separate artifacts | Each run is isolated by experiment, method, task and seed; the returned program is re-simulated outside the agent budget | `scripts/run_bench.py`, `spectra/agent/sandbox.py`, `paper/sections/bench.tex` |
| Deterministic export and structured measurements matter more than prose logs | Netlists, metric checks, PVT records and diagnosis JSON are generated from structured records; paper tables are regenerated from `results/` | `spectra/sim/evaluate.py`, `scripts/analyze.py`, `scripts/make_tables.py` |
| Agents should use typed operations and explicit lifecycle boundaries | SPECTRA keeps model calls, program execution, simulator evaluation, diagnosis and paper generation as separate stages with explicit experiment namespaces | `spectra/agent/llm.py`, `scripts/run_gpt_experiments.sh`, `scripts/finalize_paper.sh` |
| A run must be auditable and recoverable | The finalization pipeline now writes `results/evidence_manifest.json` with commit, benchmark-input hashes, raw-run hashes, model IDs, status counts and simulator version | `scripts/write_evidence_manifest.py` |

The reference also makes a boundary that SPECTRA preserves: an editor or agent can prepare a circuit and its specs, but electrical correctness comes from an independent simulator and explicit measurements. A schematic or language-model response alone is not treated as a passing result. SPECTRA therefore does not import the Analog Canvas editor, hosted service, or project format into the benchmark; it adopts only the reproducibility and evidence boundaries that fit a server-side research evaluation.
