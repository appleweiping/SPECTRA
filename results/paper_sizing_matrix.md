# Strict eight-framework fixed-topology sizing track

All rows receive the same frozen topology, variable bounds, task text, SKY130/ngspice-42 and 300 simulation-unit budget. LLM adapters share a 12-call cap. Results are reimplementations or adapters and do not reuse paper-reported numbers.

Search uses 3 corners during adaptation. An independent 45-corner verifier reports PVT pass. Missing fields remain missing and are never imputed. Pairwise p-values are single-seed descriptive snapshot statistics.

| Framework | Venue | Observed/36 | Robust n | TT success (95% Wilson CI) | PVT success (95% Wilson CI) | Mismatch n | Mean sims | Mean calls | Mean wall s | Mean cost | W/L vs AnalogCoder | Crashes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPECTRA (ours) | this work | 36/36 | 12/12 | 0.833 [0.681,0.921] | 0.250 [0.089,0.532] | 0 | 54.7 | 1.7 | 110.5 | $0.000 | 17/0 | 0 |
| AnalogCoder | AAAI-25 | 36/36 | 12/12 | 0.361 [0.225,0.524] | 0.250 [0.089,0.532] | 0 | 3.1 | 2.3 | 38.3 | $0.000 | -- | 10 |
| ADO-LLM | ICCAD-24 | 36/36 | 12/12 | 0.722 [0.560,0.842] | 0.250 [0.089,0.532] | 0 | 120.3 | 4.7 | 185.9 | $0.000 | 13/0 | 2 |
| AnaFlow | ICCAD-25 | 36/36 | 12/12 | 0.722 [0.560,0.842] | 0.333 [0.138,0.609] | 0 | 53.6 | 1.6 | 79.3 | $0.000 | 13/0 | 7 |
| Artisan | DAC-24 | 36/36 | 12/12 | 0.694 [0.531,0.820] | 0.167 [0.047,0.448] | 0 | 52.9 | 0.9 | 89.1 | $0.000 | 16/4 | 5 |
| AutoSizer | ICML-26 | 36/36 | 12/12 | 0.694 [0.531,0.820] | 0.167 [0.047,0.448] | 0 | 131.7 | 1.7 | 164.6 | $0.000 | 13/1 | 5 |
| ATLAS | ICCAD-26 | 36/36 | 12/12 | 0.333 [0.202,0.497] | 0.083 [0.015,0.354] | 0 | 87.2 | 0.0 | 76.3 | $0.000 | 5/6 | 0 |
| GLOVA | DAC-25 | 36/36 | 12/12 | 0.222 [0.117,0.381] | 0.000 [0.000,0.242] | 0 | 28.8 | 0.9 | 40.6 | $0.000 | 4/9 | 5 |

## Per-domain TT success

| Method | opamp | amp | cmirror | filter | ldo | vco |
|---|---:|---:|---:|---:|---:|---:|
| spectra | 1.000 | 0.667 | 1.000 | 0.667 | 0.833 | 0.833 |
| analogcoder | 0.667 | 0.000 | 1.000 | 0.167 | 0.000 | 0.333 |
| ado_llm | 0.833 | 0.500 | 1.000 | 0.333 | 0.833 | 0.833 |
| anaflow | 1.000 | 0.167 | 1.000 | 0.500 | 0.833 | 0.833 |
| artisan | 1.000 | 0.667 | 0.333 | 0.333 | 0.833 | 1.000 |
| autosizer | 1.000 | 0.833 | 1.000 | 0.167 | 0.333 | 0.833 |
| atlas | 0.667 | 0.000 | 0.333 | 0.000 | 0.167 | 0.833 |
| glova | 0.333 | 0.167 | 0.000 | 0.000 | 0.000 | 0.833 |

## Paired TT snapshot against SPECTRA

| Method | Common | SPECTRA wins | SPECTRA losses | Ties | Exact sign p |
|---|---:|---:|---:|---:|---:|
| analogcoder | 36 | 17 | 0 | 19 | 1.526e-05 |
| ado_llm | 36 | 5 | 1 | 30 | 0.2188 |
| anaflow | 36 | 7 | 3 | 26 | 0.3438 |
| artisan | 36 | 8 | 3 | 25 | 0.2266 |
| autosizer | 36 | 6 | 1 | 29 | 0.125 |
| atlas | 36 | 18 | 0 | 18 | 7.629e-06 |
| glova | 36 | 22 | 0 | 14 | 4.768e-07 |
