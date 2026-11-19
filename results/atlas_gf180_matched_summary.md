# ATLAS GF180 matched public PVT track

The matched ATLAS two-stage GF180 task uses the shipped public corner netlists, ngspice-44.2, three seeds, 300 nominal simulations, 12 GPT calls, and an independent 17-condition verifier. The strict merger reports 6/6 seed-method cells with finite violations.

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall (s) |
|---|---:|---:|---:|---:|---:|---:|
| spectra | 3 | 0.0000 | 0.0000 | 0.052511 | 0.165142 | 57.28 |
| anaflow_cleanroom | 3 | 0.0000 | 0.0000 | 0.060912 | 0.184697 | 55.62 |

The GF180 task is feasibility-challenging under the frozen public specifications. Both methods have zero TT/PVT success cells at this budget. SPECTRA has lower mean TT and PVT violation than the clean-room AnaFlow adapter on this stratum, so the evidence supports a violation-axis lead rather than an endpoint-success SOTA claim.

The clean-room adapter is protocol-aligned and uses the same task, budget, simulator, verifier, seeds, and output schema. It is not an official AnaFlow implementation.
