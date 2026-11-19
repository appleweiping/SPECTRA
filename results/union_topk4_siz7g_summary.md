# SPECTRA union-top-k4 sizing result

`SIZ7g_SPECTRA_HYBRID_UNION_TOPK4_ROBUST` evaluates one deterministic SPECTRA candidate policy on the 36-task, six-family fixed-topology track. It uses the same three seeds, 300 simulation-unit cap, 12-call cap and independent 45-corner verifier as the external rows. Candidate search unions nominal and low-voltage three-corner screens, then verifies the four best candidates on the full PVT grid.

| Framework | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Crashes |
|---|---:|---:|---:|---:|---:|---:|
| SPECTRA union-top-k4 | 108/108 | 0.9167 | 0.3333 | 0.0128 | 0.2820 | 0 |
| AnaFlow external primary | 108/108 | 0.8704 | 0.3056 | 0.0381 | 0.6667 | 2 |

This measured 36-task track exceeds AnaFlow on both success endpoints and has lower mean TT and PVT violation. The policy was selected after matched sensitivity tracks, so the result remains an exploratory candidate track rather than a preregistered primary row. Its identical 92-task expansion is complete and is reported separately because PVT success is lower than AnaFlow on that broader matrix.

Raw archive SHA-256 `BFF1F3AEDFF5C1C9544D6A0146E32CD03E9D2B21107F252441E98590AD744720` for `work/remote_archive/pvt_hybrid_union_topk4_robust.tar.gz`.
