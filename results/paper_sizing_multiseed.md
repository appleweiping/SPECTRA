# Three-seed strict sizing track

Seed 0 is from SIZ7g_FINAL and seeds 1/2 are from SIZ7g_MS_FINAL. All methods use the frozen 36-task, 300-simulation-unit, 12-call protocol. Bootstrap intervals resample task IDs, preserving seed dependence.

| Framework | Cells | TT success | Task-cluster TT 95% | PVT success | Task-cluster PVT 95% | Mean TT violation | Mean PVT violation | Crashes |
|---|---:|---:|---|---:|---|---:|---:|---:|
| spectra | 108/108 | 0.806 [0.721,0.869] | [0.6759, 0.9167] | 0.194 [0.098,0.350] | [0.0, 0.4167] | 0.1180 | 0.5648 | 0 |
| analogcoder | 108/108 | 0.472 [0.381,0.566] | [0.3241, 0.6204] | 0.250 [0.138,0.411] | [0.0, 0.5] | 0.5577 | 0.9239 | 0 |
| ado_llm | 108/108 | 0.750 [0.661,0.822] | [0.6111, 0.8704] | 0.167 [0.079,0.319] | [0.0, 0.4167] | 0.0545 | 0.6366 | 0 |
| anaflow | 108/108 | 0.870 [0.794,0.921] | [0.7778, 0.9444] | 0.306 [0.180,0.469] | [0.0833, 0.5556] | 0.0381 | 0.6667 | 0 |
| artisan | 108/108 | 0.713 [0.622,0.790] | [0.5833, 0.8333] | 0.083 [0.029,0.218] | [0.0, 0.1667] | 0.1540 | 1.4791 | 0 |
| autosizer | 108/108 | 0.806 [0.721,0.869] | [0.6944, 0.8981] | 0.139 [0.061,0.287] | [0.0, 0.3333] | 0.0565 | 1.2401 | 0 |
| atlas | 108/108 | 0.352 [0.268,0.446] | [0.2222, 0.4815] | 0.083 [0.029,0.218] | [0.0, 0.1944] | 0.3660 | 0.9956 | 2 |
| glova | 108/108 | 0.352 [0.268,0.446] | [0.213, 0.5] | 0.028 [0.005,0.142] | [0.0, 0.0833] | 0.4623 | 0.5313 | 0 |

## Paired SPECTRA comparisons

| Framework | Common cells | SPECTRA wins | losses | ties | Exact sign p | Holm p (7 tests) | Cluster bootstrap diff 95% |
|---|---:|---:|---:|---:|---:|---|---|
| analogcoder | 108 | 38 | 2 | 68 | 1.493e-09 | 7.467e-09 | [0.1852, 0.4815] |
| ado_llm | 108 | 19 | 13 | 76 | 0.3771 | 0.7542 | [-0.1111, 0.213] |
| anaflow | 108 | 7 | 14 | 87 | 0.1892 | 0.5677 | [-0.1759, 0.0463] |
| artisan | 108 | 22 | 12 | 74 | 0.1214 | 0.4858 | [-0.0648, 0.2593] |
| autosizer | 108 | 11 | 11 | 86 | 1 | 1 | [-0.1204, 0.1204] |
| atlas | 108 | 57 | 8 | 43 | 3.163e-10 | 1.898e-09 | [0.2685, 0.6296] |
| glova | 108 | 52 | 3 | 53 | 1.542e-12 | 1.1e-11 | [0.2963, 0.6111] |

## Per-domain rates

| Method | Family | Cells | TT | PVT |
|---|---|---:|---:|---:|
| spectra | amp | 18 | 0.833 | 0.000 |
| spectra | cmirror | 18 | 1.000 | 1.000 |
| spectra | filter | 18 | 0.667 | 0.333 |
| spectra | ldo | 18 | 0.667 | 0.000 |
| spectra | opamp | 18 | 0.667 | 0.000 |
| spectra | vco | 18 | 1.000 | 0.000 |
| analogcoder | amp | 18 | 0.222 | 0.000 |
| analogcoder | cmirror | 18 | 1.000 | 1.000 |
| analogcoder | filter | 18 | 0.222 | 1.000 |
| analogcoder | ldo | 18 | 0.000 | 0.000 |
| analogcoder | opamp | 18 | 0.667 | 0.000 |
| analogcoder | vco | 18 | 0.722 | 0.000 |
| ado_llm | amp | 18 | 0.722 | 0.000 |
| ado_llm | cmirror | 18 | 1.000 | 1.000 |
| ado_llm | filter | 18 | 0.278 | 0.000 |
| ado_llm | ldo | 18 | 0.889 | 0.000 |
| ado_llm | opamp | 18 | 0.722 | 0.000 |
| ado_llm | vco | 18 | 0.889 | 0.000 |
| anaflow | amp | 18 | 0.833 | 0.000 |
| anaflow | cmirror | 18 | 1.000 | 1.000 |
| anaflow | filter | 18 | 0.611 | 1.000 |
| anaflow | ldo | 18 | 0.889 | 0.000 |
| anaflow | opamp | 18 | 0.889 | 0.167 |
| anaflow | vco | 18 | 1.000 | 0.000 |
| artisan | amp | 18 | 0.889 | 0.000 |
| artisan | cmirror | 18 | 0.389 | 0.167 |
| artisan | filter | 18 | 0.333 | 0.000 |
| artisan | ldo | 18 | 0.833 | 0.000 |
| artisan | opamp | 18 | 0.833 | 0.167 |
| artisan | vco | 18 | 1.000 | 0.000 |
| autosizer | amp | 18 | 0.889 | 0.000 |
| autosizer | cmirror | 18 | 0.944 | 0.833 |
| autosizer | filter | 18 | 0.389 | 0.000 |
| autosizer | ldo | 18 | 0.667 | 0.000 |
| autosizer | opamp | 18 | 1.000 | 0.000 |
| autosizer | vco | 18 | 0.944 | 0.000 |
| atlas | amp | 18 | 0.111 | 0.000 |
| atlas | cmirror | 18 | 0.389 | 0.167 |
| atlas | filter | 18 | 0.111 | 0.000 |
| atlas | ldo | 18 | 0.222 | 0.000 |
| atlas | opamp | 18 | 0.611 | 0.000 |
| atlas | vco | 18 | 0.667 | 0.333 |
| glova | amp | 18 | 0.389 | 0.000 |
| glova | cmirror | 18 | 0.222 | 0.000 |
| glova | filter | 18 | 0.000 | 0.000 |
| glova | ldo | 18 | 0.222 | 0.000 |
| glova | opamp | 18 | 0.444 | 0.083 |
| glova | vco | 18 | 0.833 | 0.000 |
