# AnalogGym SKY130 AMP TT smoke

This receipt records one reproducible public AnalogGym testbench execution on the server. It is a simulator smoke check only. It is not a sizing experiment, PVT evaluation, AnaFlow comparison, or ranking result.

- Source: CODA-Team/AnalogGym, commit `0a9d1390ade361e2b4a2d33181e22367edbb8afc`
- Netlist: `AnalogGym/Amplifier/amp_spice_testbench/TB_Amplifier_ACDC.cir`
- Command: `cd <workspace>/bench_sources/AnalogGym/AnalogGym/Amplifier/amp_spice_testbench && <workspace>/ngspice-42-install/bin/ngspice -b TB_Amplifier_ACDC.cir`
- PDK: `sky130`
- PDK zip SHA-256: `bc46a070e6c8c217e61e97355ed2ab3f029706a99b5053a80860cd98963e1ce8`
- Simulator binary: `<workspace>/ngspice-42-install/bin/ngspice`
- Simulator binary SHA-256: `0d7d86d9b3e67fb54d35c2a4dec55024e7ea5668ca20a74961360e8f25dcc3b3`
- Return code: `0`
- Raw log SHA-256: `2310c77da48cd39b8b60a370c22a6b5e5015c192c1de8a6f191625f9d654171c`

## Reported TT measurements

| Metric | Value |
|---|---:|
| `dcgain_db` | 90.07545 |
| `gain_bandwidth_product_hz` | 838366.0 |
| `phase_in_deg` | 8.05217 |

The source testbench completed with return code 0 under ngspice-42. The receipt explicitly sets `ranking_eligible=false`, `sizing=false`, and `pvt=false`.

The batch log also contains a later `phase_in_deg = failed` line after the first numeric AC measurement. The receipt preserves the first numeric occurrence for traceability and remains ineligible for sizing or PVT ranking.

Full machine-readable provenance is in [`analoggym_amp_tt_smoke.json`](analoggym_amp_tt_smoke.json).
