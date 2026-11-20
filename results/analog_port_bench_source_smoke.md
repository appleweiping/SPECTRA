# AnalogPortBench source-native smoke

This receipt records one real server-side invocation of the public
AnalogPortBench evaluator. It is an evaluator and PDK integrity check, not a
SPECTRA or AnaFlow transfer result.

- Source commit: `5dc16f1c01858664f1912a84abfc06fd4c69f6de`
- Circuit and netlist: `ota_tele`, source golden `ota_tele_1v8.sp`
- Target: SKY130 LVT, 1.8 V, TT, ngspice-44.2
- Result: `PASS` for all 9 source checks
- Representative metrics: gain 70.95 dB, UGF 58.87 MHz, phase margin 62.4 deg, power 201.29 uW, swing 0.538 V, triode devices 0
- Ranking eligible: `False`

The netlist provenance is `source_golden_reference`. No SPECTRA answer,
matched AnaFlow answer, common SIZ7g budget, or independent transfer verifier
is attached. The strict blocker remains in
`results/analog_port_bench_source_smoke.json`.
