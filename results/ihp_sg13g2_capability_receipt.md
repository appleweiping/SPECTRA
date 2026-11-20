# IHP SG13G2 capability receipt

- schema: `spectra-ihp-sg13g2-capability/v1`
- source commit: `e73adb4045731ddec21634146d536380057f6a26`
- source files observed by the reproducible audit: 7267
- source tree file-list SHA-256: `728d11eb1dd0915e55789ebe414985e10c241b4ae0ff484e66aa49b24ff546f2`
- PDK: `ihp-sg13g2`
- ngspice: `ngspice-44.2`, native OP smoke passed
- Xyce: `Xyce-7.10`, source deck compatibility smoke returned `pdk_deck_unsupported`
- ranking eligible: `False`

The server audit compiled the PDK's PSP103, PSP103-NQS, R3-CMC, MOSVAR, CMOMI and CMOMF Verilog-A models with the OpenVAF 0.3-compatible binary (`openvaf 23.5.0`). The six OSDI artifact hashes are recorded in the JSON receipt. The native ngspice operating-point smoke returned code `0` in under one second and reported finite `v(out)` and `i(vdd)` values.

The same source `.lib` device deck was probed with Xyce-7.10. Xyce returned code `1` because the ngspice source deck does not define a compatible `SG13_LV_NMOS` subcircuit for Xyce. The raw diagnostic is retained in `results/ihp_sg13g2_native_xyce_smoke.stdout`. This is a simulator compatibility boundary, not a fabricated cross-simulator result.

This is PDK and model-runtime capability evidence only. It is excluded from the matched SIZ7g and XSOTA-1 aggregates because the source does not provide a common 300-evaluation sizing task, an independent verifier, or a matched AnaFlow cell. No SOTA score is inferred from either smoke.
