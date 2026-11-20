# Cross-domain capability receipt v6

- schema: `spectra-cross-domain-capability/v1`
- manifest_sha256: `ca98e2bafa60fbcbc29892010d3b5cbae63ac637764c3c16b333e573609d8ef9`
- ranking_eligible: `False`
- ranking_reason: Capability receipt only. A matched cell still requires task digest, PDK/model digest, corners, verifier, seed and budget evidence.

## Simulator inventory

| simulator | available | version |
|---|---:|---|
| hspice | False | unavailable |
| ngspice | True | ** ngspice-44.2 : Circuit level simulation program |
| spectre | False | unavailable |
| xyce | True | Xyce Release 7.10.0-opensource |

## Public source tracks

| track | source commit | files | PDKs | simulators |
|---|---|---:|---|---|
| analoggym_amp_ldo | `0a9d1390ade361e2b4a2d33181e22367edbb8afc` | 227 | sky130 | ngspice-44.2, Xyce-7.10 |
| opensource_31 | `e8308aa273c1a6737a5dee89178c4d48270ff87e` | 3405 | ptm45, ptm180, sky130, bjt_public, asap7 | ngspice-44.2, Xyce-7.10 |
| ampicbench_public | `4ba5fc7a9b082df144225672e33d58a8e162af96` | 257 | sky130 | ngspice-44.2, Xyce-7.10 |
| sganalog_tapeout | `ebd7e694b79cbe8475c42bd41cf4620c5d537a0f` | 6731 | sky130 | ngspice-44.2 (native harness), ngspice-45.2 (upstream source protocol) |
| atlas_dual_pdk | `dd23c5ba7beb598909be593e4a84c81dab92cc69` | 101 | sky130, gf180mcu | ngspice-44.2 |
| analog_design_bench | `972f7cd7c95381134387b250edf18f3bd23bdd25` | 996 | sky130 | ngspice |
| loadbench_ml | `03cc45620afbbbee19652d83d625f26f3368d951` | 9 | sky130 | ngspice-44.2 (source-defined) |
| analog_port_bench | `5dc16f1c01858664f1912a84abfc06fd4c69f6de` | 8394 | gf180mcu, sky130 | ngspice |

This is a capability inventory. It does not constitute a matched sizing result or an XSOTA-1 pass.
