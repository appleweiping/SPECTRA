# Open-source analog circuits ngspice-44.2 baseline smoke

The five-category smoke uses the repository native `NgspiceBenchmark`, each default point, and the server ngspice-44.2 binary. It verifies that the PDK/model include paths and metric parsers execute before a matched sizing sweep. It is a capability receipt, not a ranking matrix.

| Category | Config | Variables | Metrics | Success | Wall (s) | Objective |
|---|---|---:|---|---:|---:|---:|
| ptm180 | `circuits/ptm180nm_opamp/config.json` | 19 | gain=51.2726; ugf=2.96573e+07; pm=180.759 | True | 0.026 | 0.1454568333333333 |
| sky130 | `circuits/sky130_lp_opamp/config.json` | 6 | gain=72.7675; ugf=8.43978e+08; pm=179.855 | True | 7.184 | 0.0 |
| bjt | `circuits/bjt_ce_amp/config.json` | 5 | vout=11.3701 | True | 0.026 | 0.0 |
| ldo_sky130 | `circuits/ldo_simple/config.json` | 16 | vout=-5.38226; dcgain=4.60453; ugf=4.46481e+06 | True | 10.750 | 1012.6494068 |
| asap7 | `circuits/ldo_1/config_asap7.json` | 8 | vout=0.488792; dcgain=71.6543; ugf=3.21619e+08; pm=0.94358 | True | 26.934 | 0.9790315577777777 |

Covered model/PDK classes are PTM180, SKY130, public BJT, SKY130 LDO and ASAP7. The full matched protocol still needs a common PVT adapter for each source task. The ASAP7 source harness depends on Docker, so this receipt uses the shipped netlist and local ngspice-44.2 OSDI model directly after the server PDK path was resolved.
