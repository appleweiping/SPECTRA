# AnalogGym robust cross-simulator sensitivity

The sensitivity contract is fixed at 300 simulator evaluations, 12 calls, seeds 0/1/2, and 45 independent PVT verifier conditions. SPECTRA uses the disclosed spectra_robust three-corner search. The clean-room AnaFlow rows use the same budget and verifier with nominal search. The frozen primary track is not overwritten.

| Simulator | Topology | Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds | 45/45 finite |
|---|---|---|---:|---:|---:|---:|---:|---:|:---:|
| ngspice-44.2 | HoiLee_AFFC_Pin_3 | spectra | 3 | 1.000 | 0.667 | 0.000000 | 0.000346 | 2069.9 | yes |
| ngspice-44.2 | HoiLee_AFFC_Pin_3 | anaflow_cleanroom | 3 | 1.000 | 0.667 | 0.000000 | 0.000346 | 1466.8 | yes |
| ngspice-44.2 | Leung_NMCF_Pin_3 | spectra | 3 | 1.000 | 0.667 | 0.000000 | 0.002469 | 2935.0 | yes |
| ngspice-44.2 | Leung_NMCF_Pin_3 | anaflow_cleanroom | 3 | 1.000 | 0.333 | 0.000000 | 0.015552 | 2445.8 | yes |
| Xyce-7.10 | HoiLee_AFFC_Pin_3 | spectra | 3 | 0.333 | 0.333 | 0.047664 | 0.077823 | 729.3 | yes |
| Xyce-7.10 | HoiLee_AFFC_Pin_3 | anaflow_cleanroom | 3 | 1.000 | 0.333 | 0.000000 | 0.084900 | 732.3 | yes |
| Xyce-7.10 | Leung_NMCF_Pin_3 | spectra | 3 | 0.667 | 0.333 | 0.035259 | 0.035090 | 588.9 | yes |
| Xyce-7.10 | Leung_NMCF_Pin_3 | anaflow_cleanroom | 3 | 0.667 | 0.333 | 0.002182 | 2.418563 | 590.7 | yes |

The Xyce robust SPECTRA cells are individually retained as six raw receipts under results/analoggym_xyce_robust_s*_spectra.json and results/analoggym_leung_xyce_robust_s*_spectra.json. Each has 300 simulations, 12 calls, 45 unique conditions, no missing metrics, and finite normalized violations. The matching AnaFlow rows are the existing six nominal Xyce receipts and were merged without rewriting them.

This is a benchmark- and simulator-scoped sensitivity result. The HoiLee Xyce arm has a TT-success deficit and PVT-success tie, and the literal XSOTA-1 audit therefore remains strict_gate_pass=false.
