# Component contribution audit

The matched mechanism track has 18 tasks, three seeds and 54 runs per arm. A component is supported when its prespecified mechanism axis improves with the full arm. This is not an essentiality claim on every endpoint.

| Component | Ablation | Evidence axis | Full | Ablated | Delta | Paired TT W/L | Supported |
|---|---|---|---:|---:|---:|---:|---|
| diagnosis | spectra_nodiag | violation_reduction | 0.0404 | 0.0873 | +0.0469 | 6/7 | PASS |
| intent-program abstraction | spectra_nointent | violation_reduction | 0.0404 | 0.1048 | +0.0644 | 7/8 | PASS |
| PVT-aware refinement | spectra_norefine | endpoint_success | 0.6296 | 0.4259 | +0.2037 | 15/4 | PASS |
| knowledge cards | spectra_noknow | endpoint_success | 0.6296 | 0.4259 | +0.2037 | 14/3 | PASS |

The raw endpoint and event-level tables remain in `results/component_mechanism_matrix.json`; no arm or task is removed from this audit.
