# External-primary SIZ7g evaluation

This is the primary comparison for the single SPECTRA framework. Legacy SPECTRA-min, optimizer controls and oracle rows are excluded from the primary claim and retained in audit artifacts. External rows are paper-backed clean-room adapters.

| Framework | Source venue | Cells | TT | PVT | Mean TT violation | Mean PVT violation |
|---|---|---:|---:|---:|---:|---:|
| SPECTRA (ours) | this work | 108/108 | 0.806 | 0.194 | 0.1180 | 0.5648 |
| AnalogCoder | AAAI-25 | 108/108 | 0.472 | 0.250 | 0.5577 | 0.9239 |
| ADO-LLM | ICCAD-24 | 108/108 | 0.750 | 0.167 | 0.0545 | 0.6366 |
| AnaFlow | ICCAD-25 | 108/108 | 0.870 | 0.306 | 0.0381 | 0.6667 |
| Artisan | DAC-24 | 108/108 | 0.713 | 0.083 | 0.1540 | 1.4791 |
| AutoSizer | ICML-26 | 108/108 | 0.806 | 0.139 | 0.0565 | 1.2401 |
| ATLAS | ICCAD-26 | 108/108 | 0.352 | 0.083 | 0.3660 | 0.9956 |
| GLOVA | DAC-25 | 108/108 | 0.352 | 0.028 | 0.4623 | 0.5313 |

## Protocol

- Six circuit domains and 36 frozen fixed-topology tasks.
- Three seeds, 108 cells per framework, 864 primary cells.
- 300 simulation units and 12 LLM calls per cell.
- Independent 45-corner verifier.
- SPECTRA uses its disclosed full-grid PVT-aware search objective. External adapters use the preregistered three-corner search objective.

## Scope

SPECTRA leads the reported mean PVT-violation endpoint only through the post-fix staged sensitivity track. AnaFlow leads TT and PVT success in the primary matrix. The evidence supports a fixed-topology track result and does not establish universal analog-sizing SOTA across arbitrary topologies, PDKs, simulators or mismatch protocols.
