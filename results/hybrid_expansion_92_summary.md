# SPECTRA hybrid 92-task sensitivity

`SIZ11g_SPECTRA_HYBRID_EXT_V1` reruns SPECTRA only on all 92 tasks, 12 families and three seeds with the same 300-simulation and 12-call caps. It is a sensitivity track because the primary external matrix uses the preregistered full-grid SPECTRA adapter.

| Framework | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation |
|---|---:|---:|---:|---:|---:|
| SPECTRA full-grid expansion | 276 | 0.761 | 0.123 | 0.0972 | 0.5931 |
| SPECTRA hybrid expansion | 276 | 0.841 | 0.193 | 0.0544 | 0.4423 |
| AnaFlow external expansion | 276 | 0.801 | 0.228 | 0.0527 | 0.6053 |

Hybrid exceeds AnaFlow on TT success but remains below it on robust PVT success. This does not support a strict AnaFlow TT/PVT lead or a universal SOTA claim.

Raw archive SHA-256 `6C1D3816D7DBCA22DB8198934B06ABE872B071EBCDC2D6E4552AD6D2A982F83B`.