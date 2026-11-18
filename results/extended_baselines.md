# Six-domain external-framework matrix

All rows use the frozen GPT-6.1-sol task text, SKY130/ngspice-42 and the same budget. Oracle rows are privileged upper bounds and are not fair LLM comparisons.

| Framework | Observed/36 | TT success (95% Wilson CI) | PVT success | Mean sims | Mean calls | Mismatch n | W/L vs SPECTRA | Crashes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spectra | 36/36 | 0.806 [0.650,0.902] | -- | 18.1 | 3.4 | 0 | -- | 5 |
| direct | 36/36 | 0.750 [0.589,0.863] | -- | 2.6 | 3.6 | 0 | 2/4 | 5 |
| genbo | 36/36 | 0.417 [0.271,0.578] | -- | 116.0 | 1.8 | 0 | 0/14 | 5 |
| spectra_min | 36/36 | 0.583 [0.422,0.729] | -- | 55.3 | 1.6 | 0 | 0/8 | 6 |
| genbo_cmaes | 36/36 | 0.500 [0.345,0.655] | -- | 4.7 | 0.7 | 0 | 2/13 | 18 |
| oracle_random* | 36/36 | 0.333 [0.202,0.497] | -- | 240.9 | 0.0 | 0 | 3/20 | 0 |
| oracle_cmaes* | 36/36 | 0.750 [0.589,0.863] | -- | 113.0 | 0.0 | 0 | 7/9 | 0 |
| oracle_tpe* | 36/36 | 0.694 [0.531,0.820] | -- | 153.9 | 0.0 | 0 | 6/10 | 0 |

*Privileged template-oracle upper bound.
