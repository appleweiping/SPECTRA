# AMPICBench ngspice-44.2 source-corner capability receipt

The server replayed the nine shipped AMPICBench decks over every source-declared corner in `corners.json`. The run used official ngspice-44.2 and recorded every condition, return code, elapsed time, simulator diagnostics, and artifact metric lines. This is a source-native PVT capability audit. It is not a matched SPECTRA-versus-AnaFlow sizing ranking because the decks do not expose a common parameterized design-variable and objective contract.

| Quantity | Value |
|---|---:|
| Decks | 9 |
| Conditions per deck | 15 |
| Total conditions | 135 |
| Successful conditions | 135 |
| Fatal simulator conditions | 0 |
| Conditions with artifact metric lines | 135 |
| Simulator | ngspice-44.2 |

The artifact stream includes operating-point node/device values and, for STB decks, `ugf`, `pm_raw`, `dcgain_db`, `f180`, and `gm_db`. The complete JSON receipt is `results/ampicbench_ng44_pvt_capability_v2.json`. Capability success is kept separate from ranking success.
