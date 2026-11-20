# IHP SG13G2 capability receipt

- schema: `spectra-ihp-sg13g2-capability/v1`
- source commit: `e73adb4045731ddec21634146d536380057f6a26`
- source files observed by the reproducible audit: 7267
- source tree file-list SHA-256: `728d11eb1dd0915e55789ebe414985e10c241b4ae0ff484e66aa49b24ff546f2`
- PDK: `ihp-sg13g2`
- simulator: `ngspice-44.2`
- status: `source_audit_pass_model_runtime_blocked`
- ranking eligible: `False`

No matched sizing task, independent verifier or AnaFlow cell. Native smoke did not complete a valid device simulation.

## Native smoke

The reproducible server audit `scripts/audit_ihp_sg13g2.py` attempted `op` using `pmos_nmos_op.cir` and returned code `1` in 0.129 seconds.
ngspice reported `Unknown model type psp103va / could not find a valid modelname`. The PDK ships PSP103 model files, but this server installation has no loaded PSP103 OSDI plugin.

This receipt is capability evidence only. It is excluded from the matched SIZ7g and XSOTA-1 aggregates until a runnable model runtime, source-native task contract, independent verifier and matched AnaFlow cell exist.
