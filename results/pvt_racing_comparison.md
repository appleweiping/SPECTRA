# Robust PVT racing comparison

`SIZ7g_SPECTRA_RACING_MS_FAST` evaluates the explicit `racing` strategy on the
same 36 fixed-topology tasks, three seeds, 300 simulation units and 12-call cap
as the stored SIZ7g SPECTRA rows. The strategy screens candidates on the three
search corners and verifies the selected candidates on all 45 verifier corners.

| Strategy | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation |
|---|---:|---:|---:|---:|---:|
| Stored SPECTRA full-grid rows | 108 | 0.8056 | 0.1944 | 0.1180 | 0.5648 |
| SPECTRA racing smoke rerun | 108 | 0.8148 | 0.1944 | 0.0915 | 0.3885 |

The paired PVT violation comparison uses 36 robust task-seed cells. Racing is
lower on 20 cells, higher on 6 and tied on 10. The exact two-sided sign-test
snapshot is 0.00936 before any multiplicity correction. PVT success remains
tied at 7/36, so this experiment supports a violation reduction component and
does not establish a PVT-success or universal SOTA lead.

The raw archive is `work/remote_archive/pvt_racing_ms_fast.tar` with SHA-256
`B102426E01BA73A862B45571CC507D304F43BD2A0C310FAD5CBB36409A59C5A9`.
