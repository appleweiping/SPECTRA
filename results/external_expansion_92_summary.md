# Complete 92-task external sizing expansion

The server run `SIZ11g_EXT_FINAL_V3` covers 92 tasks, 12 circuit families, three seeds and all eight external-primary rows. Every method has 276/276 materialized cells. Each cell uses the 300-simulation and 12-call caps with the independent 45-corner verifier.

| Framework | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Crashes |
|---|---:|---:|---:|---:|---:|---:|
| spectra | 276/276 | 0.761 | 0.123 | 0.0972 | 0.5931 | 0 |
| analogcoder | 276/276 | 0.391 | 0.175 | 0.5415 | 1.0013 | 4 |
| ado_llm | 276/276 | 0.565 | 0.105 | 0.0857 | 0.4296 | 7 |
| anaflow | 276/276 | 0.801 | 0.228 | 0.0527 | 0.6053 | 2 |
| artisan | 276/276 | 0.728 | 0.088 | 0.1486 | 0.8738 | 4 |
| autosizer | 276/276 | 0.681 | 0.088 | 0.0490 | 0.7285 | 4 |
| atlas | 276/276 | 0.275 | 0.070 | 0.5232 | 0.4934 | 10 |
| glova | 276/276 | 0.236 | 0.035 | 0.4488 | 0.1473 | 3 |

SPECTRA does not exceed AnaFlow on this 92-task expansion. The expansion therefore supports coverage and failure analysis, not a universal SOTA claim. Crash cells are retained in the denominators and raw archives.
