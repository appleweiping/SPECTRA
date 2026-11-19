# AnalogGym matched ngspice44 matrix

The matrix uses the same AnalogGym SKY130 topology, 300 nominal simulator evaluations, 12 calls, 45-condition PVT verification, and seeds 0/1/2 for SPECTRA and the clean-room AnaFlow adapter. The strict shard merger passed with no missing or duplicate cells and finite violations.

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall time (s) |
|---|---:|---:|---:|---:|---:|---:|
| anaflow_cleanroom | 3 | 1.0000 | 0.6667 | 0.000000 | 0.000346 | 1919.47 |
| spectra | 3 | 1.0000 | 0.6667 | 0.000000 | 0.000346 | 1912.04 |

Per-seed rows remain in the six raw JSON files. This is one public topology and one simulator stratum. It is a matched benchmark result and does not support a domain-level SOTA claim by itself.

The machine-readable aggregate is `results/analoggym_pvt_merged.json`.
