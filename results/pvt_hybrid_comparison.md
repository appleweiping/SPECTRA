# Robust PVT hybrid comparison

`SIZ7g_SPECTRA_HYBRID_MS_FAST` evaluates the hybrid corner-search strategy on the same 36 frozen fixed-topology tasks, three seeds, 300 simulation units and 12-call cap as the stored primary rows. It screens candidates on three corners and verifies up to three candidates on all 45 PVT corners.

| Strategy | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation |
|---|---:|---:|---:|---:|---:|
| Stored SPECTRA full-grid rows | 108 | 0.8056 | 0.1944 | 0.1180 | 0.5648 |
| SPECTRA hybrid candidate search | 108 | 0.8889 | 0.3056 | 0.0713 | 0.4463 |
| AnaFlow external primary row | 108 | 0.8704 | 0.3056 | 0.0381 | 0.6667 |

Hybrid exceeds AnaFlow on TT success and ties it on PVT success. The result is a separately measured strategy track and does not support a strict PVT-success lead or a universal SOTA claim. The primary external ranking remains unchanged until a single strategy is selected before evaluation.

Raw archive SHA-256 `45416EAA35A64600D2DA2A3787917EFB00B2E7FD9B4A14764B3F511706EF9574` for `work/remote_archive/pvt_hybrid_ms_fast.tar.gz`.