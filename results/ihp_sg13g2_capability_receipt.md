# IHP SG13G2 capability receipt

- schema: `spectra-ihp-sg13g2-capability/v1`
- source commit: `e73adb4045731ddec21634146d536380057f6a26`
- source files observed by the reproducible audit: 7267
- source tree file-list SHA-256: `728d11eb1dd0915e55789ebe414985e10c241b4ae0ff484e66aa49b24ff546f2`
- PDK: `ihp-sg13g2`
- simulator: `ngspice-44.2`
- status: `source_audit_and_native_smoke_pass`
- ranking eligible: `False`

The server audit compiled the PDK's PSP103, PSP103-NQS, R3-CMC, MOSVAR, CMOMI and CMOMF Verilog-A models with the OpenVAF 0.3-compatible binary (`openvaf 23.5.0`). The resulting six OSDI artifact hashes are recorded in the JSON receipt. A native one-netlist operating-point smoke then returned code `0` in under one second and reported finite `v(out)` and `i(vdd)` values.

This is PDK and model-runtime capability evidence only. It is excluded from the matched SIZ7g and XSOTA-1 aggregates because the source does not provide a common 300-evaluation sizing task, an independent verifier, or a matched AnaFlow cell. No SOTA score is inferred from this smoke.
