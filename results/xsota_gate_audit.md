# XSOTA-1 gate audit

SPECTRA must strictly beat matched AnaFlow on TT success, PVT success, mean TT violation, and mean PVT violation in every declared public stratum

Strict gate: **NOT MET**
Comparable strata: 9; uncovered receipts: 11.

| Receipt | Tier | TT lead | PVT lead | TT violation lead | PVT violation lead | All endpoints |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `analoggym_leung_pvt_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `analoggym_leung_pvt_robust_merged.json` | uncovered | no | no | no | no | no |
| `analoggym_leung_xyce_merged.json` | strict-pvt-comparison | yes | yes | yes | yes | yes |
| `analoggym_pvt_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `analoggym_pvt_robust_merged.json` | uncovered | no | no | no | no | no |
| `analoggym_xyce_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `atlas_gf180_matched_merged.json` | uncovered | no | no | no | no | no |
| `public_v2_bjt_merged.json` | uncovered | no | no | no | no | no |
| `public_v2_ptm180_merged.json` | uncovered | no | no | no | no | no |
| `public_v2_sky130_lp_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `public_v3_asap7_ldo_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `public_v4_ldo_simple_merged.json` | strict-pvt-comparison | no | no | yes | yes | no |
| `public_v5_bjt_merged.json` | uncovered | no | no | no | no | no |
| `public_v5_ptm180_merged.json` | uncovered | no | no | no | no | no |
| `public_v6_sky130_lp_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `public_v7_ptm45_merged.json` | uncovered | no | no | no | no | no |
| `public_v8_sky130_lp_xyce_merged.json` | strict-pvt-comparison | no | no | no | no | no |
| `public_x1_bjt_merged.json` | uncovered | no | no | no | no | no |
| `public_x1_v2_bjt_merged.json` | uncovered | no | no | no | no | no |
| `public_x1_v3_bjt_merged.json` | uncovered | no | no | no | no | no |

Uncovered or capability-only receipts remain in this audit and count against the literal gate. A benchmark-scoped lead does not change the gate result.
