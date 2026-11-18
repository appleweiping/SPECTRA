# Component mechanism ablation

Experiment `E2g_mech` uses 18 tasks across six domains, three seeds and a common GPT-6.1-sol budget.

| Arm | Observed/expected | TT success | PVT success | Mean violation | Mean sims | Mean calls | Intent fraction | Refine traces | Card events |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spectra | 54/54 | 0.630 | 0.389 | 0.04 | 96.70 | 3.85 | 0.94 | 30 | 220 |
| spectra_nodiag | 54/54 | 0.648 | 0.556 | 0.09 | 90.37 | 4.17 | 0.90 | 43 | 251 |
| spectra_nointent | 54/54 | 0.648 | 0.667 | 0.10 | 70.48 | 2.96 | 0.00 | 23 | 126 |
| spectra_norefine | 54/54 | 0.426 | 0.278 | 0.00 | 16.61 | 2.41 | 0.95 | 0 | 142 |
| spectra_noknow | 54/54 | 0.426 | 0.333 | 0.00 | 36.56 | 1.63 | 0.91 | 9 | 0 |

Paired comparisons

| Ablation arm | Common runs | TT wins by full arm | TT losses by full arm | Mean score delta |
|---|---:|---:|---:|---:|
| spectra_nodiag | 54 | 6 | 7 | -0.03159218015451592 |
| spectra_nointent | 54 | 7 | 8 | -0.08397011414696649 |
| spectra_norefine | 54 | 15 | 4 | 0.0047604937687418586 |
| spectra_noknow | 54 | 14 | 3 | 0.005618578421919464 |
