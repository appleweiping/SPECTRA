# Analog LLM / circuit-generation repos: what they contain and what we can reuse

Date of analysis: 2026-11-16. All repos are shallow clones under `/home/user/refs/repos/<dir>`, and the commit used is listed for each one.
This is a static read only. Per instructions, no repo scripts were executed. An attempt to sanity-simulate an AnalogGym deck in our
ngspice-42 (`/usr/bin/ngspice`, KLU build) was blocked by the session permission policy, so **runnability claims below rest on
code/netlist inspection plus reference output files shipped in the repos, not on our own simulation.**
laiyao1/AnalogCoder was out of scope; it is handled elsewhere.

---

## 0. Summary table

| # | Project | Clone dir (commit) | URL | License | Content type | Simulator / models | Value for us |
|---|---|---|---|---|---|---|---|
| 1 | **AnalogGym** (ICCAD'24) | `analoggym` (0a9d139, 2025-10-29) | github.com/CODA-Team/AnalogGym | BSD-3-Clause; bundled sky130 is Apache-2.0 | Sizing benchmark: netlists, testbenches, design vars, RL example | **ngspice (≥42) + sky130** for AMP/LDO. Other categories need Spectre/HSPICE with proprietary 40/65/180 nm PDKs | **High.** Primary sizing benchmark candidate |
| 1b | AnalogGym-Opt (TCAD'26), derivative | `analoggym-opt` (10093e3, 2026-09-16) | github.com/Computing-Intelligent-Decision-Team/AnalogGym-Opt | MIT | Cleaned AnalogGym port: 16 amps + 1 LDO as YAML configs, sky130 sensors/refs, MCP server | ngspice + sky130 (bundled, unzipped) | **High.** Best-organized version of the AnalogGym circuits. Also the closest competitor, since it is "LLM-oriented" |
| 1c | opensource-analog-circuits, derivative | `opensource-analog-circuits` (e8308aa, 2026-08-05) | github.com/jialinlu/opensource-analog-circuits | **No LICENSE file** | 31-circuit ngspice sizing suite (AnalogGym amps/LDOs + PTM/sky130 hobby circuits) with a generic JSON harness | ngspice-46, sky130, PTM 45/180, ASAP7 (OSDI) | Medium. Use the harness idea and the sky130 bin/load-time notes; licensing is unclear |
| 2 | **AnalogGenie** (ICLR'25) | `analoggenie` (efc2535, 2025-04-26) | github.com/xz-group/AnalogGenie | MIT (code). Dataset includes textbook screenshots | Topology dataset (3,350 circuits, 4,152 `.cir`) + GPT model | None. Topology only, no sizing or simulation in repo | Medium. Topology corpus for novelty/validity metrics and retrieval |
| 3 | **LaMAGIC / LaMAGIC2** (ICML'24/'25) | `lamagic` (0cde737, 2025-08-16) | github.com/turtleben/LaMAGIC | **No LICENSE file** | Training code for power-converter topology LM. Data and checkpoints on HF | ngspice, ideal switches, fixed L/C/R | Low. Different domain (3–6-component DC-DC converters) |
| 4 | **CktGNN / OCB** (ICLR'23) | `cktgnn` (416cd03, 2023-09-11) | github.com/zehao-dong/CktGNN | MIT | Ckt-Bench-101 (10k) and Ckt-Bench-301 (50k) behavioral op-amp graphs with gain/PM/BW/FoM | **Cadence Spectre/Ocean**, behavioral gm-R-C stages (no transistors) | Low–medium. Only as a GNN/BO baseline dataset, not transistor-level |
| 5a | **AnalogXpert** (ISEDA'25) | `analogxpert` (72a4e45, 2026-07-17) | github.com/zhywhite/AnalogXpert | **No LICENSE file** | Structured-spec → op-amp topology prompts, 30 real + 2,000 synthetic queries, golden subcircuits | No simulation. TSMC N28 CDL subcircuits (PDK not bundled) | Medium. Spec-schema ideas and topology-synthesis tasks |
| 5b | **EEsizer** (TCAS-I'25) | `eesizer` (3af9421, 2026-04-23) | github.com/eelab-dev/EEsizer | MIT | LLM sizing agent notebooks, 9 netlists, PTM cards | ngspice + **PTM 90/130/180 nm** (bundled) | Medium. Baseline method and PTM cards. Measurement code is brittle |
| 5c | **Masala-CHAI** (arXiv'24/'25) | `masala-chai` (7478979, 2026-10-25) | github.com/jitendra-bhandari/Masala-CHAI | MIT (empty copyright holder) | Schematic-image → SPICE pipeline, 1,815 schematic images, `analoggenie.jsonl` (2,950 description→netlist pairs) | ngspice syntax check only, toy level-1 models | Low–medium. NL→netlist pairs. Images are from textbooks (copyright) |
| 5d | **AnalogCoder-Pro** (TCAD'26) | `analogcoderpro` (5db764d, 2026-10-30) | github.com/laiyao1/AnalogCoderPro | **No LICENSE file** | 29 generation tasks + 16 "Opt" tasks, PySpice testbenches, Optuna sizing | ngspice via PySpice + **BPTM 45 nm** (`mosfet_model/45nm_bulk.txt`), VDD 1.2 V | **High as a baseline** (end-to-end gen+size). Tasks/metrics to compare against |
| 5e | AMSnet | `amsnet` = lll143653/amsnet (**wrong project**: ECCV'24 image denoising), `amsnet-kg` (empty README), `amsnet2-site` (project page only) | github.com/AMS-Net/amsnet-kg-public, amsnet2-0.github.io | n/a | No usable analog code or data on GitHub | n/a | None |
| 5f | Artisan (DAC'24), AmpAgent, ADO-LLM (ICCAD'24), AnaFlow (2025) | not found | GitHub repo search for name, name+analog, in:readme returned nothing relevant | n/a | No public code found | n/a | Paper-only baselines (reimplement or cite) |

Other repos found during search that may matter later (not analyzed): `xz-group/AnalogGenie-Lite`, `PKU-IDEA/PANDA` (DAC'25 end-to-end),
`aprilaihub/agentic-analog-sizing`, `TheWind-upBird/Analogagent`, `eelab-dev/EEschematic`, `levantlabs/circuitrubric-bench`,
`Why0912/AMSBench`, `qhy991/Awesome-LLM-Circuit-Agent` (cloned as `awesome-llm-circuit-agent`, a good survey list).

---

## 1. AnalogGym (priority)

**URL / license:** https://github.com/CODA-Team/AnalogGym, BSD-3-Clause (© 2024 CODA-Team). Paper: ICCAD'24, arXiv 2409.08534.
**Claimed scope:** 30 topologies in 5 categories: sensing front ends, voltage references, amplifiers (AMP), LDOs, PLLs.
**Actually open-PDK runnable (ngspice + sky130): AMP and LDO only.** The other categories are tied to confidential PDKs:
- `AnalogGym/Charge Pump/circuit/tran_27corner.sp` uses HSPICE with `smic.40/hspice/v1p4/l0040ll_v1p4_1r.lib` (SMIC 40 nm, not bundled).
- `AnalogGym/Phase-Locked Loop/` uses Spectre/OCEAN (`pll_vco.ocn`, `cds.lib`) with a proprietary PDK.
- `AnalogGym/Sensing Front End/*` and `Voltage Reference/` are Spectre/HSPICE netlists with `nch_mac` (TSMC-style 180/65 nm). The PDK paths are deliberately omitted ("confidentiality agreements").
- `AnalogGym/Amplifier/spectre_netlist/*` headers say they were generated from `TSMC22ULL_Std_AMP_LIB`. These are topology only.

### 1.1 Amplifier suite (sky130, ngspice)
Files: `AnalogGym/Amplifier/{spice_netlist,design_variables,schematic,spectre_netlist}/<name>`, `amp_spice_testbench/TB_Amplifier_{ACDC,Tran}.cir`, `perf_extraction_amp.py`.

Every netlist is a `.subckt <name> gnda vdda vinn vinp vout` using `sky130_fd_pr__{n,p}fet_01v8`. It has an **internal ideal bias current source** (`I0 … 'CURRENT_0_BIAS'`), **ideal capacitors** (`'CAPACITOR_k'`) and ideal resistors (`'RESISTOR_k'`, in kΩ in the bounds code). Sizing parameters are **grouped/matched** names such as `MOSFET_8_2_W_gm1_PMOS`, `…_L_…`, `…_M_…`, so one parameter set drives several matched devices.

| Netlist (spice_netlist/) | Topology (compensation) | #MOS | C | R | #design vars |
|---|---|---|---|---|---|
| Alfio_RAFFC_Pin_3 | reversed active-feedback FC | 24 | 2 | 0 | 29 |
| Fan_SMC_Pin_3 | single Miller | 24 | 1 | 0 | 25 |
| HoiLee_AFFC_Pin_3 | active-feedback FC | 30 | 2 | 0 | 35 |
| Leung_DFCFC1_Pin_3 | damping-factor-control FC | 26 | 2 | 0 | 32 |
| Leung_DFCFC2_Pin_3 | DFCFC variant | 26 | 2 | 0 | 29 |
| Leung_NMCF_Pin_3 | nested Miller + feedforward | 24 | 2 | 0 | 26 |
| Leung_NMCNR_Pin_3 | nested Miller + nulling R | 24 | 2 | 1 | 24 |
| Peng_ACBC_Pin_3 | active-capacitor buffered | 27 | 2 | 0 | 35 |
| Peng_IAC_Pin_3 | impedance-adapting | 34 | 2 | 1 | 33 |
| Peng_TCFC_Pin_3 | transconductance-capacitance FC | 32 | 2 | 0 | 26 |
| Qu2017_AZC_Pin_3 | active-zero comp. | 25 | 3 | 4 | 40 |
| Ramos_PFC_Pin_3 | positive-feedback comp. | 24 | 2 | 0 | 26 |
| Sau_CFCC_Pin_3 | current-feedback comp. | 24 | 1 | 0 | 31 |
| Song_DACFC_Pin_3 | dual active-cap FC | 37 | 2 | 0 | 35 |
| Tan_CLIA_Pin_3 | (CLIA) | 25 | 2 | 1 | 30 |
| Yan_AZ_Pin_3 | active-zero | 21 | 2 | 3 | 38 |
| **Qu_LEC_Pin_3** | — | **file is 0 bytes (broken)** | | | 30 |

That gives 16 usable three-stage op-amps. `design_variables/` also contains `Cascode_Miller_Pin_2`, `Cascode_Null_Pin_1`,
`Davide_ASMIHF_Pin_3` and `TwoSt_SMCNR_Pin_2` with **no matching netlist**. The default `design_variables/*` values are
placeholders (all W=1, L=1, M=4, C≈2–5 pF, Ib≈1–20 µA). They are not tuned designs.

**Testbench (`TB_Amplifier_ACDC.cir`)** puts 5 copies of the op-amp in one deck. VDD=1.8 V, VCM=0.25·VDD=0.45 V, `PARAM_CLOAD=500p` (the per-circuit CL in §1.3 differs), `.include …/sky130_pdk/libs.tech/ngspice/corners/tt.spice`, `.param mc_mm_switch=0 mc_pr_switch=0`:
- **Open-loop gain / GBW / PM:** unity-feedback loop broken with `Lfb opout opout_dc 1T` and `Cin opout_dc signal_in 1T`, which gives a DC-closed, AC-open loop with the AC stimulus injected into **vinn**. Measured with `ac dec 10 0.1 1G`:
  `dcgain = vdb(opout) at 0.1 Hz`, `GBW = f where vdb(opout)=0`, `PM = vp(opout) at UGF`. Because the input is inverting, the phase starts at +180°, so the measured phase equals PM directly. The deck converts rad→deg.
- **CMRR:** `cmrrdc = vdb(cm3) at 0.1 Hz` in a follower with CM AC injected (`vcmac1/vcmac2`). It is reported as a **negative dB** number, and the target is ≤ −80.
- **PSRR+/−:** unity-gain follower, AC=1 on VDD or GND, `vdb` at 0.1 Hz (negative dB).
- **DC (temp sweep −40…125 °C, unity follower):** `TC = PP(Vout)/AVG(Vout)/165`, which measures offset drift. `Power = −I(VDD)·VDD at 25 °C`. `Vos = Vout(25 °C) − VCM`.
- **Tran (`TB_Amplifier_Tran.cir`):** unity follower, 0.3→0.5 V pulse at 1 µs, width `10/GBW_ideal` with GBW_ideal fixed at 5e4, so 200 µs. `tran 1u 4.01e-4`. "SR" = 0.1 V / (time to cross 0.4 V), which is a midpoint-delay proxy and not a true slope. The Python `perf_extraction_amp.py::analyze_amplifier_performance` instead computes SR as dV/dt at the midpoint and the settling time to ±1 % (`d0=0.01`).
- **FoMs:** FOM_S = GBW[MHz]·CL[pF]/P[mW] and FOM_L = SR[V/µs]·CL[pF]/P[mW]. Area = sqrt(ΣW·L·M [µm²] + ΣR[kΩ]·5 + ΣC[F]·1e12·1085) (ad hoc, from `perf_extraction_amp.py::extract_meas`). The README has a composite FOM_AMP with penalty `max(1, x/x_ref)` for vn, TC and Vos.

### 1.2 LDO suite (sky130, ngspice)
Files: `AnalogGym/Low Dropout Regulator/spice_netlist/{LDO_netlist.txt (Basic_LDO), ldo_1/ldo_2/ldo_folded_cascode/ldo_simple_*}`,
`ldo_spice_testbench/TB_LDO_{ACDC,Tran}.cir` + per-LDO decks, `design_variables/*.txt`, `perf_extraction_LDO.py`. That is 5 LDOs.
Testbench: VDD=1.8 V, Vref=0.4 V, Vout target 1.6 V (feedback 300k/100k, so dropout is 0.2 V), load cap sky130 MIM `cap_mim_m3_1 W=30 L=30 m=M_CL`, Iload 5 mA (min) to 55 mA (max).
Metrics: line regulation (VDD 1.62–1.98 V), load regulation (Iload sweep), power at min/max load, Vos=Vout−1.6, loop gain/GBW/PM (broken loop, both loads), PSRR at 0.1 Hz, and load-step under/overshoot (`tran 10n 100u`, 5→55 mA). Dropout files appear in `RGNN_RL/simulations/LDO_TB_Vdrop_*`.
LDO targets (`RGNN_RL/ckt_graphs.py::GraphLDOtestbench`): LDR 0.1, LNR 0.01, P_max 90 µW(?)/P_min 9 µW (units inconsistent), Vos 2 mV, PSRR −40 dB, GBW 2 MHz, PM 60°, under/overshoot 0.1 V.

### 1.3 Spec targets (amplifiers), from `RGNN_RL/ckt_graphs.py`
Common to all AMP graphs: PM ≥ 60°, DC gain ≥ 130 dB, PSRR± ≤ −80 dB, CMRR ≤ −80 dB, |Vos| ≤ 0.06 mV, TC ≤ 10 ppm/°C, settling ≤ 1 µs, VDD = 1.8 V.
A "baseline" set is also given (gain 90 dB, PSRR/CMRR −60 dB, settling 5 µs, TC 50 ppm, Vos 0.1 mV) and is used for FoM normalization. Units: Power in mW, GBW in Hz, SR in V/µs, Area in sqrt(µm²)-ish.

| Graph class | CL | GBW tgt | Power tgt (mW) | SR tgt (V/µs) | FOM_S tgt | FOM_L tgt | Area tgt |
|---|---|---|---|---|---|---|---|
| NMCF | 100 pF | 1.2 MHz | 0.3 | 0.6 | 300 | 160 | 150 |
| DFCFC1 | 100 pF | 1.05 MHz | 0.3 | 1.3 | 300 | 400 | 80 |
| DFCFC2 | 100 pF | 4 MHz | 0.25 | 1.25 | 1200 | 500 | 80 |
| NMCNR (**class defined twice**; the 2nd wins: gain 140 dB, PSRR/CMRR −90) | 100 pF | 2.5 MHz | 0.3 | 0.6 | 833 | 200 | 160 |
| SMC | 120 pF | 1.5 MHz | 0.2 | 0.4 | 600 | 200 | 80 |
| PFC | 130 pF | 1 MHz | 0.3 | 0.4 | 450 | 175 | 200 |
| ACBC | 500 pF | 1 MHz | 0.2 | 0.4 | 2500 | 1000 | 80 |
| CFCC | 500 pF | 4 MHz | 0.2 | 0.8 | 10000 | 2000 | 80 |
| AFFC | 120 pF | 2 MHz | 0.2 | 2.2 | 1200 | 1320 | 80 |
| IAC | 150 pF | 3.5 MHz | 0.25 | 1.2 | 2100 | 720 | 80 |
| RAFFC | 500 pF | 1.2 MHz | 0.3 | 1.2 | 2000 | 2000 | 150 |
| AZ | 15 nF | 5 MHz | 0.3 | 0.1 | 250000 | 5000 | 80 |
| AZC | 18 nF | 3 MHz | 0.5 | 0.3 | 108000 | 10800 | 80 |
| TCFC / ASMIHF | — | 1 MHz | "2e2" (µW?) | "4e5" (V/s?) | — | — | — (different unit convention, TC 1 ppm, PSRR −90) |

The **reward** (`RGNN_RL/AMP_*.py::_get_info`) sums per-spec normalized scores `min((x−t)/(x+t), 0)` (or the inverse for lower-is-better). Episode success means reward ≥ 0, i.e. all specs met.
AnalogGym-Opt (`circuit_configs/*.yaml`) **resets most circuits to generic defaults** (gain 100 dB, GBW 1 MHz, P 0.3 mW, SR 0.4 V/µs, PM 60°). Only NMCF, NMCNR, DFCFC1/2 and PFC keep the stricter AnalogGym numbers, and CLs vary from 10 pF (SMC) to 15 nF (AZ).

### 1.4 Sizing variable ranges
- `perf_extraction_amp.py::TB_Amplifier_ACDC` (HoiLee_AFFC example, 24 dims): L, W ∈ [0.5, 5] µm, M ∈ circuit-specific integer windows (e.g. [325, 340] for the output device), C ∈ [5, 15] pF, Ib ∈ [1, 5] µA.
- `RGNN_RL/ckt_graphs.py` (RL action space): W ∈ [0.5, 10] µm, L ∈ [0.5, 5] µm, M ∈ [1, 50] (output stage [100, 500]; LDO pass device [100, 1000]), Ib ∈ [1, 30] µA. Caps are sky130 MIM 30×30 µm units, M ∈ [1, 30], where 1 unit ≈ 1.82 pF.
- AnalogGym-Opt YAML: W [0.5,10] step 0.1, L [0.5,5] step 0.1, M [1,50] step 1, Ib [1,120] µA, C multiplier [1,30].
- **Units:** sky130 ngspice models set `.option scale=1.0u` (in `libs.tech/ngspice/all.spice`, pulled in by `corners/tt.spice`), so instance W and L are in **µm**.
- **Bin coverage (checked by parsing model files):** `nfet_01v8` tt has 180 bins with no gaps for L∈[0.15,5], W∈[0.36,10] µm. `pfet_01v8` tt has 108 bins and requires **W ≥ 0.42 µm** (W<0.42 is uncovered). AnalogGym ranges (W≥0.5) are therefore safe. Our agent must clamp W≥0.42 µm for pfet.

### 1.5 PDK / model files
- `PDK/sky130_pdk.zip` (17.8 MB, unpacks to 105 MB) and `RGNN_RL/mosfet_model/sky130_pdk.zip` are nearly identical. They hold an open_pdks-style `sky130A` subset (`libs.tech/{ngspice,klayout,magic,netgen,xschem,…}`, `libs.ref/sky130_fd_pr/{spice,gds,lef,mag}`) plus stray `modelcard.nmos/pmos` (BSIM3 level 8, unrelated).
- ngspice entry points: `sky130_pdk/libs.tech/ngspice/sky130.lib.spice` (`.lib tt|ss|ff|sf|fs`) or, as AnalogGym does, `corners/tt.spice` plus `r+c/res_typical__cap_typical*.spice` and `corners/tt/specialized_cells.spice`. Device models are `libs.ref/sky130_fd_pr/spice/sky130_fd_pr__{nfet,pfet}_01v8__tt.{pm3,corner}.spice` and `sky130_fd_pr__cap_mim_m3_1`.
- The license is **Apache-2.0** (SkyWater headers in each file). The zip has **no top-level LICENSE/NOTICE**, so add one if we redistribute. `libs.tech/ngspice/spinit` sets `ngbehavior=hsa` and `ng_nomodcheck`. AnalogGym does not use it explicitly.
- The **same sky130 model files** (identical md5 for `nfet_01v8__tt.pm3.spice`) ship unzipped in `analoggym-opt/simulation_files/sky130_pdk/` and `opensource-analog-circuits/sky130_pdk/`.
- **ngspice version:** README warns that conda's ngspice-41 gives wrong results for DC temp/current sweeps and asks for ≥42. Our `/usr/bin/ngspice` is ngspice-42.
- **Cost:** the jialinlu suite reports about 17 s per sky130 run (full corner/model parse). Batch several analyses per deck, as AnalogGym does, or keep ngspice resident (shared lib / `pyngspice`-style) for agent loops.
- AnalogGym-Opt ships reference outputs simulated from its init points (e.g. `simulation_files/amp_smc/AMP_SMC_ACDC_{AC,DC,GBW_PM}`: gain 69.9 dB, GBW 1.92 MHz, PM 89.3°, P 1.45 mW). This is evidence that the decks run in ngspice (they used a Windows build).

### 1.6 Bugs / caveats found
1. `Amplifier/spice_netlist/Qu_LEC_Pin_3` is empty. 4 variable files have no netlist.
2. `Amplifier/amp_spice_testbench/TB_Amplifier_Tran.cir` writes `write tran.dat v(vout3)` **without `set filetype=ascii` and without vin**, but `perf_extraction_amp.py::extract_tran_data` expects ASCII with 3 vectors. The RGNN_RL deck (`RGNN_RL/simulations/AMP_NMCF_Tran.cir`) is the consistent one. `extract_tran_data` also returns 2 values on error while callers unpack 3, and `__main__` unpacks a dict.
3. The transient uses a fixed `tran 1u 4.01e-4` (1 µs step), so the **1 µs settling target cannot be resolved**. The step width is fixed by `GBW_ideal=5e4` rather than the circuit's GBW.
4. The SR in `.meas` is a midpoint-delay proxy. TC is offset drift. CMRR/PSRR are negative-dB conventions.
5. `ckt_graphs.py` defines `GraphAMPNMCNR` twice. TCFC/ASMIHF use different units.
6. TB CL=500 pF while per-circuit CLs are 10 pF–18 nF. Ideal caps in `AnalogGym/Amplifier` vs MIM caps + `Ib` pin in `RGNN_RL`/AnalogGym-Opt. **The two variants are not interchangeable.**
7. `RGNN_RL/` bundles torch wheel binaries and a Dockerfile (python 3.10, torch 1.13). Do not install.
8. All measurement parsing goes through fixed filenames in the CWD via `os.system('cd … && ngspice …')`, so it is not parallel-safe. AnalogGym-Opt fixes this with per-action directories.

---

## 1b. AnalogGym-Opt (derivative, MIT)
- Of all the clones, this is the cleanest **ngspice+sky130** version of AnalogGym: 16 amps (`amp_{nmcf,nmcnr,dfcfc1,dfcfc2,pfc,raffc,smc,affc,acbc,iac,tcfc,azc,cfcc,dacfc,clia,az}`) and `ldo_basic`. Each has `circuit_configs/<name>.yaml` (device groups, ranges, steps, init, targets, CL, netlist hierarchy, GNN graph) and `simulation_files/<name>/` (netlist `*_Pin_3_HSPICE_130.txt`, `*_ACDC.cir`, `*_Tran.cir`, `*_vars.spice`, reference outputs).
- It also ports sensors and references to sky130 (`sensor_ptat_*`, `sensor_fe_*`, `ref_three_output`, `ref_sub_vi`) as simulation-only decks. Its README warns that absolute levels and TC shift from the original confidential PDKs.
- PVT mode (`AmpEnv.py`): processes {ss,fs,tt,sf,ff} × VDD {1.62,1.98} × T {−25,125 °C} + tt, giving 21 corners.
- Area model (`AmpEnv.py::_calculate_area`): sqrt(ΣW·L·M·1e‑6 + C_units·1.823·1089 + R·5e‑3).
- `datasets/analog_performance/` holds 358,234 historical amp performance records (18 topologies, 22/180 nm proprietary). These are not sky130 results.
- It ships `.claude/skills/*` and `.mcp.json` (launches `python tools/mcp_server.py`). **Treat as untrusted. Do not start Claude Code with that directory as CWD and do not enable its MCP server.**
- It positions itself as "LLM-oriented sizing infrastructure", which makes it the **most direct prior work to position against** for the sizing part.

## 1c. opensource-analog-circuits (jialinlu)
- `benchmark/ngspice_benchmark.py` is a generic harness: JSON `design_vars {name:[default,lb,ub]}` and `specs {metric:[">",v]}`, regex `.param` injection, parsers `ac_data|regex|multi_tb_meas`, objective `sum_violations|weighted_sum|max_violation`. It is a nice, minimal API to mirror.
- It includes AnalogGym amps/LDOs with only gain/UGF/PM specs (gain>60 dB, UGF>1 MHz, PM>60°; LDO gain>40 dB, UGF>100 kHz, PM>45°), plus sky130 hobby circuits (bgr, ldo, lp_opamp, por, vco), PTM 45/180 op-amps and ASAP7 (BSIM-CMG via OSDI, ngspice-46 docker).
- **No LICENSE.** `circuits/ptm180nm_opamp/ptm180nm.lib` ("Typical parameters for academic use") is **not** the canonical ASU PTM card: it differs from EEsizer's `ptm_180.txt` and has a symmetric ±0.3999 Vth. Avoid it.

---

## 2. AnalogGenie (ICLR'25)
- **URL / license:** github.com/xz-group/AnalogGenie, MIT (© 2025 XZ Group). Processed data at HF `JianGao666/AnalogGenie`, checkpoint at `JianGao666/AnalogGenie`.
- **Content:** `Dataset/<id>/` (3,350 dirs, IDs 1–3502, 4,152 `.cir`). Each has a Spectre-style netlist (`M0 (D G S B) nmos4`, `R0 (a b) resistor`, **no sizes or values**), `Port<id>.txt`, `Pagenumber<id>.txt`, and `Book<id>.png`/`Cadence<id>.png` screenshots.
- **Sources (`Dataset/data_categorization.md`):** Razavi (Analog, RF), Camenzind, Johns&Martin, Gray-Meyer, Allen-Holberg, and papers. Classes: amplifiers/op-amps (~400 + textbook), bandgaps (1461–1780), LDOs (2181–2630), comparators, LNAs, mixers, PAs, VCOs, power converters (1191–1460), and SC samplers (2631–3502).
- **Device vocabulary:** nmos4, pmos4, npn/pnp, R, C, L, diode, plus INVERTER, TRANSMISSION_GATE, XOR, PFD macros.
- **Code:** `SPICE2GRAPH_{compress,full}.py` (netlist to pin-level adjacency), `Augmentation*.py` (Eulerian-circuit sequences), `Models/GPT.py` (6-layer, 384-d decoder), `Pretrain.py`, `Inference.py`. **No simulator, sizing or model cards.** The paper's sizing/FoM evaluation is not in the repo.
- **Reuse:** the topology corpus serves as a reference set for **validity/novelty/uniqueness metrics** and few-shot retrieval. The pin-level graph conversion fits isomorphism-based novelty checks.
- **Avoid:** redistributing `Book*.png` (textbook scans, copyright beyond the MIT code license).

## 3. LaMAGIC / LaMAGIC2 (ICML'24/'25)
- github.com/turtleben/LaMAGIC. **No LICENSE file.** Data at HF `turtleben/LaMAGIC-dataset` and checkpoints at `turtleben/LaMAGIC2-*`.
- Domain: **power-converter topologies** with 3–6 components (switches Sa/Sb, L, C) and a duty cycle in {0.1…0.9}. The LM is flan-T5 or a custom transformer.
- Simulation (`parsers/simulation.py::convert_netlist_cki/simulate/calculate_efficiency`): ngspice `tran 10n 4000u` with ideal `SW` switches (as coded, Ron=Ra=100 kΩ and Roff=Rb=1 Ω; looks inverted but is driven by complementary gates), Vin=100 V, Rin=0.1, Rout=50, Cout=10 µF, L=100 µH, C=10 µF, f=1 MHz. Metrics: **voltage conversion ratio and efficiency**. A `.model MOSN NMOS level=8` is declared but unused.
- Reuse: only the idea of an "LM-generated topology → automatic SPICE validity check" metric. The circuit domain does not match op-amps/LDOs.

## 4. CktGNN / Open Circuit Benchmark (ICLR'23)
- github.com/zehao-dong/CktGNN, MIT.
- `OCB/CktBench101/` has 10,000 circuits (`ckt_bench_101*.pkl`, `perform101.csv`: valid, gain, pm, bw, fom). `OCB/CktBench301/` has 50,000 circuits (zipped pkl, `perform301.csv`).
- Circuits are **behavioral op-amps**: DAGs of subgraph types (In/Out, R, C, RC, ±gm with R/C) realized as `vccs` + R + C stages (`OCB/src/simulator/circuit_test.txt`). There are no transistors or PDK.
- Simulator: **Spectre via OCEAN** (`OCB/src/simulator/ocean.txt`: `ac 1 Hz–100 GHz`, `dB20(VF(OUT)/VF(in))`, `phaseMargin`, `unityGainFreq`).
- FoM (`graph_to_fom.py`): `1.2·|gain|/100 + 1.6·pm/(−90) + 10·|ugw|/1e9`. CSV values are normalized.
- Reuse: baseline dataset only if we compare against GNN/BO topology search. The behavioral stages could be ported to ngspice (`G` elements) but are not transistor-level.

## 5a. AnalogXpert (ISEDA'25)
- github.com/zhywhite/AnalogXpert, **no LICENSE**. Uses the OpenAI API (gpt-4o, gpt-3.5).
- Task: structured spec → op-amp topology via subcircuit composition. Query schema: stage count, compensation, feedback, input/output signal type, input device type, topology (CS, folded, telescopic…), load type, tail bias, and pin names.
- Data: `goldendata/user_querry_real_select.txt` (30 real), `user_querry_synthetic.txt` (2,000), `user_querry_synthetic_select.txt` (100), `subckts.txt`, `blocks*.txt`. Building blocks are in `SubCircuit/Basicmacro/*` (auCdl from **TSMC N28**, `.INCLUDE /disks/nas0/...tsmcN28...`, not usable).
- Evaluation: proofreading error rate vs golden (`Self_detect*.py`, `simulation_detect.py` parse logs). **No SPICE simulation.**
- Reuse: the spec schema is good inspiration for our structured "spec → topology" prompts and topology-correctness checking.

## 5b. EEsizer (TCAS-I'25)
- github.com/eelab-dev/EEsizer, MIT (© 2025 EElab.dev). Code lives only in Jupyter notebooks (`agent_test_{gpt,claude,gemini}/*.ipynb`).
- Circuits (`initial_circuit_netlist/`): R_load, diode_load, inverter, nand, osc3, 5T OTA+buffer, telescopic cascode, xor, complementary class-AB op-amp (20T). VDD 1.8 V, CL 10 pF, RL 1 kΩ, ideal bias voltages.
- Models (bundled): `agent_test_gpt/ptm_{90,130,180}.txt` (PTM BSIM4 level 54 for 90/130; 180 nm BSIM3 level 49) and `agent_test_claude/180nm_bulk.txt` (= PTM 180). **PTM** comes from ASU NIMO, is free for research and is widely redistributed, but has no OSS license text. Verify the terms before bundling.
- Measurements (notebook functions): `ac_gain` (|H| at first point), `bandwidth` (−3 dB), `unity_bandwidth`, `phase_margin` (argmin |gain_dB| on the grid, then a 0°/180° heuristic), `power`, `output_swing`, `offset`, `ICMR`, `cmrr_tran`, `thd_input_range`. Several **rewrite netlist lines by device name** (e.g. replace `in1` on `M1`/`M4`). This is brittle and circuit-specific.
- Loop: ≤20–25 iterations, 5 % spec tolerance, LLM tool-calling picks simulations. Spec examples: gain>60 dB, UGBW>10 MHz, PM>50°, P<50 mW, CMRR>100 dB, THD<−26 dB, swing>1.7 V, offset<1 mV, ICMR>1.6 V.
- Reuse: the **baseline method**, a list of metrics and NL spec phrasing, and the PTM 90/130/180 cards (for a non-sky130 track).

## 5c. Masala-CHAI
- github.com/jitendra-bhandari/Masala-CHAI, MIT.
- `Dataset/data_{1..5}/` contains 1,815 schematic images (textbooks). `analoggenie.jsonl` has 2,950 chat-format pairs (NL description → AnalogGenie-style netlist without sizes). The pipeline is YOLO + Hough + GPT-4o. V2 agents (`agents_v2/`) use an ngspice pass/fail judge with toy `.model NMOS NMOS (VTH0=0.4 KP=200u)` models.
- Reuse: `analoggenie.jsonl` could seed NL→topology few-shot data or an eval set. It inherits textbook provenance. **Avoid** redistributing the images.

## 5d. AnalogCoder-Pro (TCAD'26)
- github.com/laiyao1/AnalogCoderPro, **no LICENSE file**. It extends AnalogCoder (which is out of scope here).
- Benchmark `problem_set.tsv`: tasks 1–29 for generation (amps, current mirror, inverter, comparator, passive filters, Gilbert mixer, 2-stage/telescopic op-amps, RC/Wien oscillators, integrator, differentiator, adder, subtractor, Schmitt, Wien VCO) and **tasks 51–66 for "Opt"** (topology + sizing, maximizing gain, GBW, or FoM = GBW[MHz]·CL[pF]/P[mW] with CL 10 pF (GBW) or 100 pF (FoM)).
- Testbenches: `problem_check/*.py` (PySpice, e.g. `Opamp.py` checks all MOSFET Id > 10 µA, then CM vs DM gain at 100 Hz). Sizing in `optimize/circuit_optimizer_helper.py` (Optuna TPE, DC-bias search for input, AC 1 Hz–10 GHz, **GBW = first downward 0-dB crossing with linear interpolation**, penalties −500/−10).
- Models: `mosfet_model/45nm_bulk.txt` (BPTM 45 nm, BSIM4 level 54) and `mosfet_model/model.py` (same values as a dict). VDD 1.2 V. Lengths fixed during sizing. W range e.g. 45 nm–22.5 µm (log).
- Reuse: the **main end-to-end baseline** (gen + BO sizing) with a directly comparable FoM definition. Its task list and conventions should be mirrored in our evaluation. Its generation tasks lack numeric specs, while the Opt tasks are single-objective.

## 5e/5f. Not available
- **AMSnet:** no public code or data found. `lll143653/amsnet` is unrelated (image denoising). `AMS-Net/amsnet-kg-public` contains only an empty README. AMSNet 2.0/AMSBench exist as project pages (arXiv 2505.09155) and `Why0912/AMSBench` (not analyzed).
- **Artisan, AmpAgent, ADO-LLM, AnaFlow:** no public repositories found via GitHub repository search (name, name+"analog"/"opamp", in:readme). Treat them as paper-only baselines.

---

## 6. What we should reuse / what to avoid

### Reuse
1. **Sizing benchmark circuits:** the 16 AnalogGym three-stage op-amps in the AnalogGym-Opt form:
   `repos/analoggym-opt/simulation_files/amp_*/AMP_*_Pin_3_HSPICE_130.txt` (netlists with `Ib` pin + MIM caps) + `circuit_configs/amp_*.yaml` (variable groups, ranges, init, CL).
   For a simpler ideal-C variant, use `repos/analoggym/AnalogGym/Amplifier/spice_netlist/*` (uniform pins `gnda vdda vinn vinp vout`, ideal I/C/R) + `design_variables/*`.
   Add the LDOs: `repos/analoggym/AnalogGym/Low Dropout Regulator/spice_netlist/{LDO_netlist.txt,ldo_*}` + `ldo_spice_testbench/TB_LDO_*.cir`, or `analoggym-opt/simulation_files/ldo_basic/`.
2. **Testbench methodology** (copy the structure into our own deck): `repos/analoggym/RGNN_RL/simulations/AMP_NMCF_ACDC.cir` and `AMP_NMCF_Tran.cir`. They give a 1T-L/1T-C loop-break for open-loop gain/UGF/PM, follower decks for CMRR/PSRR, a DC temp sweep for power/Vos/TC, `wrdata` ASCII outputs, and `set units=degrees`. Also `TB_LDO_ACDC.cir` and `TB_LDO_Tran.cir` for LDO metrics.
3. **Spec tables:** `repos/analoggym/RGNN_RL/ckt_graphs.py` (per-circuit targets/baselines, §1.3) and `analoggym-opt/circuit_configs/*.yaml`. These can be used as "hard" and "generic" spec tiers. Score normalization: `(x−t)/(x+t)` clipped at 0 (`RGNN_RL/AMP_NMCF.py::_get_info`).
4. **sky130 models for ngspice-42:** `repos/analoggym-opt/simulation_files/sky130_pdk/libs.tech/ngspice/{sky130.lib.spice,corners/*.spice,all.spice}` and `libs.ref/sky130_fd_pr/spice/` (already unzipped; the same files are in `analoggym/PDK/sky130_pdk.zip`). Apache-2.0: keep the headers and add a NOTICE. Only `libs.tech/ngspice` + `libs.ref/sky130_fd_pr/spice` are needed. Drop gds/mag/klayout to save ~90 MB.
5. **Settling/SR post-processing:** the algorithm in `repos/analoggym/AnalogGym/Amplifier/perf_extraction_amp.py::analyze_amplifier_performance` (±1 % band, slope at midpoint). Reimplement it rather than copy, because of the bugs in §1.6.
6. **GBW/FoM conventions for comparability with AnalogCoder-Pro:** `repos/analogcoderpro/optimize/circuit_optimizer_helper.py::evaluate_circuit` (first downward 0-dB crossing with interpolation, FoM = GBW[MHz]·CL[pF]/P[mW], CL=100 pF) and the task list `repos/analogcoderpro/problem_set.tsv` (Opt tasks 51–66).
7. **Generic harness API idea:** `repos/opensource-analog-circuits/benchmark/ngspice_benchmark.py` (JSON design_vars/specs, `meets_specs`, normalized x∈[0,1]^d, sim_count/sim_time). Mirror the API; do not copy the code (no license).
8. **Topology references:** `repos/analoggenie/Dataset/*/*.cir` + `SPICE2GRAPH_compress.py` (pin-level graphs) for novelty/isomorphism checks. Use `repos/analogxpert/goldendata/user_querry_*` for structured spec schema ideas. Use `repos/masala-chai/analoggenie.jsonl` for NL→netlist few-shot data (check provenance).
9. **PTM cards for a second technology track:** `repos/eesizer/agent_test_gpt/ptm_{90,130,180}.txt` and `repos/analogcoderpro/mosfet_model/45nm_bulk.txt` (BPTM 45 nm, used by AnalogCoder/-Pro, so results stay directly comparable).

### Avoid
1. AnalogGym categories needing proprietary PDKs: `Charge Pump/` (SMIC40 HSPICE), `Phase-Locked Loop/` (Spectre/OCEAN), `Sensing Front End/`, `Voltage Reference/`, `Amplifier/spectre_netlist/` (TSMC22 origin). The sky130 ports in AnalogGym-Opt change the absolute behaviour.
2. `AnalogGym/Amplifier/spice_netlist/Qu_LEC_Pin_3` (empty). Netlist-less variable files (`Cascode_*`, `Davide_ASMIHF_Pin_3`, `TwoSt_SMCNR_Pin_2`). Placeholder `design_variables/*` values used as "initial designs".
3. Taking AnalogGym's TB numbers at face value: `TB_Amplifier_Tran.cir` output is incompatible with `perf_extraction_amp.py`. The 1 µs tran step cannot resolve a 1 µs settling spec. "SR" is a midpoint proxy. The 130 dB gain target is extreme and uses negative-dB CMRR/PSRR conventions. Define our own measurement spec and document it.
4. conda ngspice-41. Use ngspice ≥42 (we have 42). Per-sim sky130 parse time (~17 s) makes naive per-candidate `ngspice -b` too slow for agent loops, so batch or keep a resident process.
5. sky130 pfet with W<0.42 µm (no model bin). Mixing the MIM-cap/`Ib`-pin variant with the ideal-C variant in one table.
6. `repos/opensource-analog-circuits/circuits/ptm180nm_opamp/ptm180nm.lib` (non-canonical PTM). Anything from that repo redistributed as-is (no license).
7. Redistributing textbook images (`analoggenie/Dataset/*/Book*.png`, `masala-chai/Dataset/*`). Redistributing code from LaMAGIC, AnalogXpert, AnalogCoder-Pro or opensource-analog-circuits (no license, so all rights reserved). Cite and reimplement instead.
8. EEsizer's notebook measurement helpers (device-name string rewriting, grid-argmin PM) and CktGNN OCB (behavioral, Spectre-only) as evaluation code.
9. Executing anything in `analoggym-opt/.claude/skills/` or `.mcp.json`, `analoggym/RGNN_RL/*.whl`, or repo `environment.yml`/Dockerfiles.

## 10. NEMESIS2.0 (server source inspection)

- **Source:** `https://github.com/UMN-EDA/NEMESIS`, inspected on the server at commit
  `3e52a9bee1a78eda63ac6db7111b598aba6ddbee` under
  `/path/to/bench_sources/NEMESIS`. The repository is BSD-3-Clause.
- **Files read:** `README.md`, `llm_aided_modelling.sh`, `design_sizer.py`,
  `extract_equations.py`, `vectorization_agent.py`, `perform_hspice_simulations.py`,
  `repair_model.py`, `feedback_manager.py`, and the `Universal/` layout described by the
  README. SHA-256 values for the principal driver and model-generation files are preserved in
  the server command log and the literature read-status ledger.
- **Workflow:** netlist and schematic interpretation → three gm/Id operating-point profiles →
  LLM equation generation → SPICE error checking/repair → vectorized evaluator → GA/PSO/DE
  sizing → independent HSPICE verification. The code keeps model-generation artifacts,
  equation history, sizing reports and SPICE reports in a run directory.
- **Protocol facts:** the paper uses five OTA and two comparator topologies, 15/6 metrics,
  five independent equation-generation runs, 5% model-error tolerance, 13,475 candidate
  evaluations for optimizer portability, and final HSPICE verification. Equation throughput,
  surrogate error and final SPICE pass are separate endpoints.
- **Boundary:** no HSPICE run was started on the server because the licensed simulator and
  foundry model paths are unavailable. NEMESIS2.0 is therefore a read-and-provenance reference
  and a future surrogate baseline, not a current SPECTRA result or a SIZ7g ranking row.

## 11. AnalogPortBench (server source inspection)

- **Source:** `https://github.com/saeidrajabii/AnalogPortBench`, inspected on the server at
  commit `5dc16f1c01858664f1912a84abfc06fd4c69f6de` under
  `/path/to/bench_sources/AnalogPortBench`. The repository is MIT-licensed.
- **Files read:** `README.md`, `benchmark/config.py`, `benchmark/circuits.py`,
  `benchmark/evaluate.py`, `benchmark/measure.py`, `benchmark/netlist.py`,
  `benchmark/sim.py`, `benchmark/techs.py`, `benchmark/baseline_v2.py`,
  `benchmark/naive_port.py`, `benchmark/make_specs.py`, `benchmark/make_scaled_specs.py`,
  `scripts/setup_env.sh`, `prompts/system.txt`, and representative T1/T2/T3/T4 prompts.
- **Workflow:** the model receives a 0.18 µm source netlist and target specification, returns a
  SKY130 netlist, passes interface/netlist checks, then is scored with ngspice DC/AC/step/swing
  measurements and transistor operating-region checks. Simulation feedback can be returned for
  up to three attempts. T4 tasks deliberately encode infeasible specifications and score an
  `INFEASIBLE` declaration separately from a feasible design pass.
- **Boundary:** the repository provides a cross-PDK transfer harness, not a fixed-topology
  SIZ7g optimizer. No model answer was executed for SPECTRA, so this is a code/provenance
  reference and future transfer track only.

## 12. LOADBench evaluation scripts (server source inspection)

- **Source:** `https://github.com/FilipeAz/LOADBench-Scripts`, inspected on the server at
  commit `03cc45620afbbbee19652d83d625f26f3368d951` under
  `/path/to/bench_sources/LOADBench-Scripts`. The checkout contains no
  `LICENSE` file, so the scripts are not vendored into SPECTRA. The source-only
  receipt is `results/loadbench_scripts_source_audit.json`.
- **Files read:** `README.md`, `struct_matcher.py`,
  `circuit_generation_coverage.py`, `topology_selection_eval.py`,
  `optimization_helper.py`, and `inverse_sizing.py`. The five public evaluation
  endpoints are structural topology matching/coverage, top-k and mean first-hit
  rank, 12-D hypervolume ratio against NSGA-II, and inverse-sizing MAPE,
  outlier, specification-satisfaction, R² and FoM.
- **Protocol facts:** the README identifies 15 held-out op-amp names for topology
  and inverse-sizing tests and fixes a 12-objective physical-space reference
  point with a `pygmo` FPRAS approximation (`epsilon=delta=0.01`, fixed seed).
  The source scripts accept CSV/DataFrame inputs and make the metric directions
  explicit. SPECTRA's audit runs deterministic synthetic one-row checks for
  top-k/MFHR and inverse sizing only.
- **Boundary:** the public data release was not downloaded, no LOADBench
  netlist was simulated, and no SPECTRA or AnaFlow task cell was produced. The
  audit is a reproducibility/provenance entry and a future data/ML capability
  track, not a SIZ7g ranking row or XSOTA-1 evidence.
