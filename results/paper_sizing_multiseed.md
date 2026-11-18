# Three-seed strict sizing track

Seed 0 is from SIZ7g and seeds 1/2 are from SIZ7g_MS_FINAL. All methods use the frozen 36-task, 300-simulation-unit, 12-call protocol. Bootstrap intervals resample task IDs, preserving seed dependence.

| Framework | Cells | TT success | Task-cluster TT 95% | PVT success | Task-cluster PVT 95% | Mean TT violation | Mean PVT violation | Crashes |
|---|---:|---:|---|---:|---|---:|---:|---:|
| spectra | 108/108 | 0.806 [0.721,0.869] | [0.6944, 0.9074] | 0.222 [0.117,0.381] | [0.0278, 0.4444] | 0.1028 | 0.5643 | 0 |
| analogcoder | 108/108 | 0.454 [0.363,0.548] | [0.3056, 0.6111] | 0.250 [0.138,0.411] | [0.0, 0.5] | 0.5103 | 0.9802 | 10 |
| ado_llm | 108/108 | 0.750 [0.661,0.822] | [0.6204, 0.8704] | 0.194 [0.098,0.350] | [0.0, 0.4167] | 0.0535 | 0.6153 | 2 |
| anaflow | 108/108 | 0.815 [0.731,0.877] | [0.7222, 0.8981] | 0.306 [0.180,0.469] | [0.0833, 0.5556] | 0.0396 | 0.7342 | 7 |
| artisan | 108/108 | 0.704 [0.612,0.782] | [0.5741, 0.8241] | 0.139 [0.061,0.287] | [0.0, 0.3056] | 0.1691 | 1.4565 | 5 |
| autosizer | 108/108 | 0.778 [0.691,0.846] | [0.6574, 0.8796] | 0.139 [0.061,0.287] | [0.0, 0.3333] | 0.0572 | 1.2401 | 5 |
| atlas | 108/108 | 0.352 [0.268,0.446] | [0.2222, 0.4815] | 0.083 [0.029,0.218] | [0.0, 0.1944] | 0.3660 | 0.9956 | 2 |
| glova | 108/108 | 0.343 [0.260,0.436] | [0.2037, 0.4815] | 0.028 [0.005,0.142] | [0.0, 0.0833] | 0.4681 | 0.5340 | 5 |

## Paired SPECTRA comparisons

| Framework | Common cells | SPECTRA wins | losses | ties | Exact sign p | Cluster bootstrap diff 95% |
|---|---:|---:|---:|---:|---:|---|
| analogcoder | 108 | 40 | 2 | 66 | 4.111e-10 | [0.213, 0.4907] |
| ado_llm | 108 | 16 | 10 | 82 | 0.3269 | [-0.0741, 0.1852] |
| anaflow | 108 | 11 | 12 | 85 | 1 | [-0.1111, 0.0833] |
| artisan | 108 | 23 | 12 | 73 | 0.08953 | [-0.037, 0.25] |
| autosizer | 108 | 13 | 10 | 85 | 0.6776 | [-0.0741, 0.1389] |
| atlas | 108 | 55 | 6 | 47 | 5.381e-11 | [0.2963, 0.6111] |
| glova | 108 | 53 | 3 | 52 | 8.137e-13 | [0.3241, 0.6019] |

## Per-domain rates

| Method | Family | Cells | TT | PVT |
|---|---|---:|---:|---:|
| spectra | amp | 18 | 0.778 | 0.000 |
| spectra | cmirror | 18 | 1.000 | 1.000 |
| spectra | filter | 18 | 0.667 | 0.333 |
| spectra | ldo | 18 | 0.722 | 0.000 |
| spectra | opamp | 18 | 0.722 | 0.083 |
| spectra | vco | 18 | 0.944 | 0.000 |
| analogcoder | amp | 18 | 0.111 | 0.000 |
| analogcoder | cmirror | 18 | 1.000 | 1.000 |
| analogcoder | filter | 18 | 0.222 | 1.000 |
| analogcoder | ldo | 18 | 0.000 | 0.000 |
| analogcoder | opamp | 18 | 0.722 | 0.000 |
| analogcoder | vco | 18 | 0.667 | 0.000 |
| ado_llm | amp | 18 | 0.667 | 0.000 |
| ado_llm | cmirror | 18 | 1.000 | 1.000 |
| ado_llm | filter | 18 | 0.333 | 0.333 |
| ado_llm | ldo | 18 | 0.889 | 0.000 |
| ado_llm | opamp | 18 | 0.722 | 0.000 |
| ado_llm | vco | 18 | 0.889 | 0.000 |
| anaflow | amp | 18 | 0.556 | 0.000 |
| anaflow | cmirror | 18 | 1.000 | 1.000 |
| anaflow | filter | 18 | 0.611 | 1.000 |
| anaflow | ldo | 18 | 0.889 | 0.000 |
| anaflow | opamp | 18 | 0.889 | 0.167 |
| anaflow | vco | 18 | 0.944 | 0.000 |
| artisan | amp | 18 | 0.833 | 0.000 |
| artisan | cmirror | 18 | 0.389 | 0.167 |
| artisan | filter | 18 | 0.278 | 0.000 |
| artisan | ldo | 18 | 0.833 | 0.000 |
| artisan | opamp | 18 | 0.889 | 0.333 |
| artisan | vco | 18 | 1.000 | 0.000 |
| autosizer | amp | 18 | 0.833 | 0.000 |
| autosizer | cmirror | 18 | 0.944 | 0.833 |
| autosizer | filter | 18 | 0.333 | 0.000 |
| autosizer | ldo | 18 | 0.611 | 0.000 |
| autosizer | opamp | 18 | 1.000 | 0.000 |
| autosizer | vco | 18 | 0.944 | 0.000 |
| atlas | amp | 18 | 0.111 | 0.000 |
| atlas | cmirror | 18 | 0.389 | 0.167 |
| atlas | filter | 18 | 0.111 | 0.000 |
| atlas | ldo | 18 | 0.222 | 0.000 |
| atlas | opamp | 18 | 0.611 | 0.000 |
| atlas | vco | 18 | 0.667 | 0.333 |
| glova | amp | 18 | 0.333 | 0.000 |
| glova | cmirror | 18 | 0.222 | 0.000 |
| glova | filter | 18 | 0.000 | 0.000 |
| glova | ldo | 18 | 0.222 | 0.000 |
| glova | opamp | 18 | 0.444 | 0.083 |
| glova | vco | 18 | 0.833 | 0.000 |
