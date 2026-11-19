# AnalogGym cross-topology public track

The completed ngspice-44.2 track covers two source-native AnalogGym SKY130 topologies, HoiLee_AFFC_Pin_3 and Leung_NMCF_Pin_3. Each topology has SPECTRA and the clean-room AnaFlow adapter at 300 nominal simulations, 12 calls, 45 PVT conditions, and seeds 0/1/2. The Xyce-7.10 track is complete for HoiLee_AFFC_Pin_3 under the same protocol.

| Topology | Simulator | Method | Cells | TT success | PVT success | Mean PVT violation |
|---|---|---|---:|---:|---:|---:|
| HoiLee_AFFC_Pin_3 | ngspice-44.2 | SPECTRA | 3 | 1.0000 | 0.6667 | 0.000346 |
| HoiLee_AFFC_Pin_3 | ngspice-44.2 | AnaFlow clean-room | 3 | 1.0000 | 0.6667 | 0.000346 |
| HoiLee_AFFC_Pin_3 | Xyce-7.10 | SPECTRA | 3 | 1.0000 | 0.3333 | 0.084900 |
| HoiLee_AFFC_Pin_3 | Xyce-7.10 | AnaFlow clean-room | 3 | 1.0000 | 0.3333 | 0.084900 |
| Leung_NMCF_Pin_3 | ngspice-44.2 | SPECTRA | 3 | 1.0000 | 0.3333 | 0.015552 |
| Leung_NMCF_Pin_3 | ngspice-44.2 | AnaFlow clean-room | 3 | 1.0000 | 0.3333 | 0.015552 |

All six rows are complete matched cells with finite violations. The public cross-topology evidence establishes reproducibility across two AnalogGym topologies and two simulator implementations on HoiLee. Every quality endpoint is tied between SPECTRA and the clean-room adapter. These rows do not establish universal AnaFlow superiority or domain-level SOTA.
