# AnalogPortBench golden replay recovery

- status: `complete_recovery`
- source commit: `5dc16f1c01858664f1912a84abfc06fd4c69f6de`
- simulator: `ngspice-44.2`
- completed jobs: `250/250`
- recovered jobs: `8/8`
- recovered failures: `0`
- ranking eligible: `False`

The eight jobs that exceeded the upstream 900-second run were rerun with the same source evaluator and fixed corner names. Every recovered corner passed the bundled golden checks. This completes the benchmark-integrity replay, but it is not a SPECTRA or AnaFlow answer matrix. The receipt remains excluded from SIZ7g and XSOTA-1.

| Golden | Corner | Elapsed seconds | Pass |
|---|---|---:|:---:|
| `ota_tele_ws_1v8` | `ff` | 189.849 | True |
| `ota_tele_ws_1v8` | `fs` | 187.776 | True |
| `ota_tele_ws_1v8` | `sf` | 238.265 | True |
| `ota_tele_ws_hard_1_fast` | `ff` | 29.635 | True |
| `ota_tele_ws_hard_1_fast` | `fs` | 31.677 | True |
| `ota_tele_ws_hard_1_fast` | `sf` | 18.495 | True |
| `ota_tele_ws_hard_1_fast` | `ss` | 20.992 | True |
| `ota_tele_ws_hard_1_fast` | `tt` | 23.934 | True |
