# SPECTRA union-top-k4 92-task expansion

`SIZ11g_SPECTRA_UNION_TOPK4_EXT_V1` completes the identical union-top-k4 candidate policy on all 92 tasks, 12 families and three seeds. Every cell uses the 300 simulation-unit and 12-call caps, and robust cells use the independent 45-corner verifier. The server produced 276/276 cells with zero crashes.

| Framework | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Crashes |
|---|---:|---:|---:|---:|---:|---:|
| SPECTRA union-top-k4 | 276/276 | 0.8261 | 0.2105 | 0.0594 | 0.2931 | 0 |
| AnaFlow external primary | 276/276 | 0.8010 | 0.2280 | 0.0527 | 0.6053 | 2 |
| SPECTRA family-policy sensitivity | 276/276 | 0.8043 | 0.2632 | 0.0698 | 0.3822 | 0 |

The identical union-top-k4 policy exceeds AnaFlow on TT success and mean PVT violation, but its PVT success is lower on this expansion. The family-policy sensitivity is the measured 92-task candidate that exceeds AnaFlow on both success endpoints. These are complete benchmark-scoped results, not evidence for universal performance on unseen topologies, PDKs, simulators or mismatch protocols.

Raw archive SHA-256 `3B38D3683E3840A72364BAA63452EF78B90CAF12FDADE6FB9C20FD9ED7201D6A` for `work/remote_archive/SIZ11g_SPECTRA_UNION_TOPK4_EXT_V1.tar.gz`.
