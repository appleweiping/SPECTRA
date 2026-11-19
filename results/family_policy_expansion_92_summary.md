# SPECTRA family-policy expansion result

The complete `SIZ11g_SPECTRA_FAMILY_EXT_V1` run covers 92 tasks, 12 families, three seeds and 276/276 SPECTRA cells under the same 300-simulation and 12-call caps. The deterministic policy uses nominal hybrid corners for `opamp` and `opamp_app`, and low-voltage hybrid corners for every other family. This policy was added after the matched sensitivity tracks and is therefore reported as an exploratory final-candidate track rather than the preregistered full-grid primary row.

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
| SPECTRA family-policy | 276/276 | 0.804 | 0.263 | 0.0698 | 0.3822 | 0 |

On this complete 92-task/12-family external benchmark, the family-policy row exceeds AnaFlow on both TT and PVT success. It is the best measured row on both success endpoints in this matrix. The evidence supports benchmark-scoped SOTA for the stated SIZ11g protocol. It does not prove performance on arbitrary unseen topologies, PDKs, simulators or mismatch protocols.
