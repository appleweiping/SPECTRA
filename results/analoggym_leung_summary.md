# AnalogGym matched Leung_NMCF_Pin_3 matrix

This public SKY130 topology uses the same 300 nominal simulator evaluations, 12 calls, 45-condition PVT verification, and seeds 0/1/2 for SPECTRA and the clean-room AnaFlow adapter. The strict shard merger passed with no missing or duplicate cells and finite violations.

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall time (s) |
|---|---:|---:|---:|---:|---:|---:|
| anaflow_cleanroom | 3 | 1.0000 | 0.3333 | 0.000000 | 0.015552 | 1808.60 |
| spectra | 3 | 1.0000 | 0.3333 | 0.000000 | 0.015552 | 1142.06 |

SPECTRA and the clean-room adapter tie on TT/PVT success and normalized violation on this topology. The lower SPECTRA wall time is an efficiency observation, not a quality endpoint. This is a matched public-topology result and does not support a domain-level SOTA claim by itself.

The machine-readable aggregate is `results/analoggym_leung_pvt_merged.json`.
