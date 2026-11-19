# AMPICBench ngspice-44.2 capability receipt

The server ran all 9 shipped AMPICBench Bias_Circuits and Opamps decks with official ngspice-44.2 after resolving the source's `/opt/pdks/sky130A` model path to the pinned server SKY130 PDK. All 9/9 decks returned code 0 without fatal errors. This is a source capability receipt; the decks are not yet a common parameterized sizing/PVT ranking API.

| Deck group | Cells | Successful | Wall-time range (s) |
|---|---:|---:|---:|
| Bias_Circuits | 2 | 2 | 7.53–7.77 |
| Opamps | 7 | 7 | 6.42–8.39 |

The source includes per-corner operating-region data and AC/STB measurements. A matched SPECTRA/AnaFlow sizing track needs a parameter injector and a common metric schema before these decks can enter ranking.
