# Cross-simulator capability receipt

The server has two source-built simulators available for the AnalogGym SKY130 netlist.

| Simulator | Version | Binary SHA-256 | Capability evidence |
|---|---|---|---|
| ngspice | 44.2/KLU | `8bd71b6fcdf47033623a2e7eaf38f97b657031df27d400f486b6928e9bc25fe4` | Official source build and smoke, recorded in `results/remote_sim_build_report.md` |
| Xyce | 7.10.0-opensource, serial | `5abf2b7d1dba7c582c37dd64a3773bebf8e76402d7e4898057016965f8cfae79` | Official source build and AnalogGym AC smoke |

The Xyce adapter removes the ngspice `.control` block, converts `ac=1` source syntax to Xyce syntax, removes DC-only measures from the AC run, and uses an explicit `.AC` analysis. Xyce parses the SKY130 BSIM4 model tree and completes the AC solve. The smoke uses one nominal condition and one simulator evaluation, so it is a capability receipt only. It does not enter a ranking until the matched 300-evaluation, 45-condition, three-seed matrix is complete.

The machine-readable receipt is `results/cross_simulator_capability_receipt.json`. The raw smoke row is `results/analoggym_xyce_smoke2.json`.
