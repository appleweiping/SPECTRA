# AMPICBench ngspice-44.2 PVT capability receipt

The server replayed the source `corners.json` files for all 9 AMPICBench Bias and Opamp decks using ngspice-44.2. Each deck exposes 15 source conditions, yielding 135 condition runs. All 135/135 returned code 0 without fatal errors.

| Group | Decks | Conditions/deck | Successful conditions |
|---|---:|---:|---:|
| Bias_Circuits | 2 | 15 | 30 |
| Opamps | 7 | 15 | 105 |

This is a cross-corner simulator capability receipt. AMPICBench still requires a parameter injector and common metric schema for a matched SPECTRA/AnaFlow sizing ranking.
