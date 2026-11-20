# XSOTA-1 gate audit

SPECTRA must strictly beat matched AnaFlow on TT success, PVT success, mean TT violation, and mean PVT violation in every declared public stratum

Strict gate: **NOT MET**
Comparable strata: 11; uncovered receipts: 8.

| Receipt | Tier | TT lead | PVT lead | TT violation lead | PVT violation lead | Non-inferior | Zero-floor ties | All endpoints |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `analoggym_leung_pvt_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `analoggym_leung_pvt_robust_merged.json` | strict-pvt-comparison | no | yes | no | yes | yes | tt_success, mean_tt_violation | no |
| `analoggym_leung_xyce_merged.json` | strict-pvt-comparison | yes | yes | yes | yes | yes | none | yes |
| `analoggym_pvt_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `analoggym_pvt_robust_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `analoggym_xyce_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `atlas_gf180_matched_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v2_bjt_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v2_ptm180_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v2_sky130_lp_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `public_v3_asap7_ldo_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `public_v4_ldo_simple_merged.json` | strict-pvt-comparison | no | no | yes | yes | yes | none | no |
| `public_v5_bjt_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v5_ptm180_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v6_sky130_lp_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `public_v7_ptm45_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_v8_sky130_lp_xyce_merged.json` | strict-pvt-comparison | no | no | no | no | yes | tt_success, mean_tt_violation | no |
| `public_x1_v2_bjt_merged.json` | uncovered | no | no | no | no | no | none | no |
| `public_x1_v3_bjt_merged.json` | uncovered | no | no | no | no | no | none | no |

Diagnostics: 11 comparable strata are non-inferior on every endpoint; 1 have strict positive leads on every endpoint; 9 contain zero-floor ties.
Zero-floor ties mean equal ideal endpoints such as TT success 1.0 or mean violation 0.0. They are explanatory diagnostics only and do not relax XSOTA-1.
Uncovered or capability-only receipts remain in this audit and count against the literal gate. A benchmark-scoped lead does not change the gate result.
