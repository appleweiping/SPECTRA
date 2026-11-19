# AnalogGym Xyce matched matrix

The Xyce track uses the same AnalogGym topology, SKY130 models, 300 nominal simulator evaluations, 12 calls, 45-condition PVT verifier, and seeds 0/1/2 for SPECTRA and the clean-room AnaFlow adapter. The six shard files passed `scripts/merge_analoggym_shards.py` with no duplicate, missing, budget, or non-finite-violation errors.

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall time (s) |
|---|---:|---:|---:|---:|---:|---:|
| SPECTRA | 3 | 1.0000 | 0.3333 | 0.0000 | 0.084900 | 848.74 |
| AnaFlow clean-room | 3 | 1.0000 | 0.3333 | 0.0000 | 0.084900 | 878.30 |

The two methods are tied on this single AnalogGym topology under Xyce. The result is a completed matched cross-simulator benchmark stratum, not a domain-level SOTA claim. The raw rows are the six `results/analoggym_xyce_s{0,1,2}_{spectra,anaflow_cleanroom}.json` files, and the machine-readable aggregate is `results/analoggym_xyce_merged.json`.
