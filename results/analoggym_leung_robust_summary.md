# AnalogGym Leung robust SPECTRA sensitivity

The Leung_NMCF_Pin_3 robust sensitivity uses ngspice-44.2, seeds 0/1/2, a 300-simulation cap, 12-call cap, and an independent 45-condition verifier. The SPECTRA search screens TT, slow-low and fast-high representative corners under the same cap. The clean-room AnaFlow matched reference is the completed nominal Leung row in `results/analoggym_leung_summary.md`.

| Track | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation |
|---|---:|---:|---:|---:|---:|
| SPECTRA robust | 3 | 1.0000 | 0.6667 | 0.000000 | 0.002469 |
| AnaFlow clean-room nominal | 3 | 1.0000 | 0.3333 | 0.000000 | 0.015552 |

This sensitivity improves the Leung PVT endpoint and mean PVT violation relative to the matched clean-room reference. It is reported as a predeclared robust-search sensitivity and is kept separate from the frozen eight-row primary matrix.
