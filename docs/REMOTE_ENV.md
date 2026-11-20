# Remote execution environment

Recorded 2026-11-16/17 from the westc server. Secrets are intentionally excluded.

| Item | Value |
|---|---|
| Host | `connect.westc.seetacloud.com:39737` |
| Project checkout | `/root/autodl-tmp/spectra-analog-agent` |
| Working storage | `/root/autodl-tmp` (the `/autodl-fs/data` mount is nearly full; `/autodl-pub/data` is read-only on this instance) |
| Hardware | 2 × NVIDIA GeForce RTX 4090 D, 24,564 MiB each; 32 CPU cores; 124 GB RAM |
| Simulators | Legacy ngspice-42 remains archived at `/root/autodl-tmp/ngspice-42-install`. The public cross-domain runs use official ngspice-44.2, binary SHA-256 `8bd71b6fcdf47033623a2e7eaf38f97b657031df27d400f486b6928e9bc25fe4`, prefix `/root/autodl-tmp/sim-build/ngspice-44.2-install`, and Xyce 7.10 serial, binary SHA-256 `5abf2b7d1dba7c582c37dd64a3773bebf8e76402d7e4898057016965f8cfae79`, prefix `/root/autodl-tmp/sim-build/xyce-7.10-serial-install` |
| Python | 3.12.3 from `/root/miniconda3/bin/python` |
| Packages | numpy 2.4.6, scipy 1.18.1, cma 4.6.0, optuna 5.1.0, matplotlib 3.11.0, openai 3.51.0 |
| Git | 2.34.1; checkout verified at the same commit as GitHub `main` |

The API environment is held outside the repository at `/root/autodl-tmp/spectra-gpt.env` with mode 600 and is
never committed. The selected experiment model is `gpt-6.1-sol`; experiment scripts keep the model configurable
through `SPECTRA_MODEL` but default to this exact ID and refuse to run without `OPENAI_API_KEY`.

The gateway does not publish a USD tariff for this model. Runs therefore record input/output token counts and leave
`cost_usd` at zero unless the operator supplies the two `SPECTRA_OPENAI_*_PRICE_USD_PER_MILLION` overrides.
The only admissible benchmark backbone for this handoff is GPT-6.1-sol; results from other model IDs are not part of
the experiment chain. A fresh server preflight on 2026-11-17 found `gpt-6.1-sol` in `/models` and a minimal chat
request returned `OK.` with the gateway reporting `gpt-6.1-sol`.

The six-domain extension used a frozen 36-task subset and the same 12-call/300-simulation
budget for every row. The completed EXT7g run contains 224 raw records covering the four
GPT arms, Gen+CMA-ES and three privileged oracle arms. The final raw archive was copied to
the E: workspace after SHA-256 verification. Its hash is recorded in
`work/remote_archive/ext_final_raw.tar.sha256`. The long-request recovery pass used
`SPECTRA_OPENAI_MAX_COMPLETION_TOKENS=4096`, `SPECTRA_OPENAI_TIMEOUT=30`, and
`SPECTRA_OPENAI_RETRIES=1`, preserving timeout outcomes as crash records.

The strict paper sizing track completed 252 unique records for 36 tasks × 7 paper-backed adapters. The component
mechanism track completed 270 unique records for 18 tasks × 5 arms × 3 seeds. The combined raw-evidence archive is
`work/remote_archive/sizing_component_final.tar` with SHA-256
`221B11AC6409F075D7D67B6D91FF0220797B13539732FD6A94E38F91BF79DC0F`.

The strict eight-row SIZ7g rerun added the native fixed-topology SPECTRA row. It contains 288 observed cells,
36 tasks per row, 12 robust tasks, a 300 simulation-unit cap and a 12-call cap. The uniform final strict archive is
`work/remote_archive/siz7g_spectra_uniform_final.tar` with SHA-256
`B47560536B9478C9B0CA157024B24FF0BD22D149EBEABBCFE6C063BA012711B0`. SPECTRA records 30/36 TT passes and
3/12 independent PVT passes. The matrix is a single-seed descriptive snapshot and mismatch is unavailable for
the public task file. Earlier mixed-version and timeout-recovery archives remain on the server for audit.

The final matched three-seed extension is stored in
`work/remote_archive/siz7g_final_bundle.tar.gz` with SHA-256
`8a360f800f0460e3bcfed188ead3d77dca4c6e6bf56832aa39c90d3eb1348a5a`. It contains the 288-cell seed-0 rerun,
the 576-cell seed-1/2 rerun, the 108-cell staged PVT sensitivity track, and the complete legacy component
mechanism evidence. The final source checkout is synchronized to GitHub `main`; the exact handoff commit is recorded
by `git rev-parse HEAD` in the delivery verification. The eight-row primary aggregate has 864/864 observed cells.
The primary SIZ7g files were generated from source commit `017536507bbf283ba5cfffbbc9f6d098bdd01250`.
SPECTRA reaches 0.806 TT, 0.194 PVT, 0.1180 mean TT violation and 0.5648 mean PVT violation. The post-fix staged
variant was generated from source commit `3347b38c19efe60dfbaa5bd71c7fe898207ea199` and reaches
0.815 TT, 0.222 PVT, 0.1071 mean TT violation and 0.5009 mean PVT violation.
The post-fix archive is `work/remote_archive/siz7g_final_postfix_bundle.tar.gz` with SHA-256
`56695cd111867bff21df3847832e87610e9c20d0cc50f66ba310c217e6e4f6db`. These results are scoped to the frozen
fixed-topology benchmark and are not a universal SOTA claim.

The repository-wide expansion audit archive is `work/remote_archive/siz11g_external_expansion_audit.tar.gz` with
SHA-256 `dbec58bf6ed7386179efa1fee71f857dc439b69dcadc2a5830184b4c30d8d8f5`. It contains the 48-cell preflight,
the 122-cell partial run, and the two infrastructure-failure archives. None of these partial records enter the
primary ranking.

The public cross-domain protocol keeps the AnalogGym, AMPICBench, opensource-analog-circuits and ATLAS source
receipts under `results/cross_domain_capability_receipt_v2.*`. The AnalogGym HoiLee and Leung amplifier tracks have
complete 45-condition verifiers under ngspice-44.2 and matched Xyce-7.10 reruns. The ATLAS GF180 capability receipt
is `results/atlas_gf180_ngspice44_capability.*`.
It records a successful ngspice-44.2 execution over all 18 shipped GF180 corner netlists at budget 50 and zero
feasible designs, so it is retained as capability evidence and excluded from matched ranking.

The completed matched public PVT additions are archived in `results/analoggym_cross_topology_summary.md` and
`results/atlas_gf180_matched_summary.md`. AnalogGym covers HoiLee_AFFC_Pin_3 on ngspice-44.2 and Xyce-7.10 plus
Leung_NMCF_Pin_3 on ngspice-44.2, with three seeds, 300 nominal simulations, 12 calls and 45 verifier conditions
per method-topology cell. The ATLAS GF180 track covers three seeds for SPECTRA and the clean-room AnaFlow adapter
under ngspice-44.2 with 300 simulations, 12 calls and all 17 conditions present in the shipped public YAML. The
strict shard receipts retain every condition and reject non-finite violations.

The public-source expansion is executed only on this server. The immutable source checkouts are
`jialinlu/opensource-analog-circuits` and `AMPICLab/AMPICBench`. The former has a 32-config ngspice-44.2
capability receipt, and the latter has 9 source decks with per-corner replay receipts. PTM180 and embedded-BJT
source configs use the strict 300-simulation/12-call adapter with seeds 0/1/2, but their source metric contracts
are TT-only and therefore remain outside PVT ranking. The SKY130 low-power op-amp matched PVT shards are running
with the same budget and the canonical 45-condition verifier. The ASAP7 LDO track has completed all six cells under
the 45-condition verifier. Both methods pass TT on all three seeds but fail the PVT endpoint with mean violation
0.8, while SPECTRA uses 960.65 wall seconds per cell versus 1009.99 for the clean-room AnaFlow adapter. The public
BJT adapter also completes a matched Xyce-7.10 TT-only track by parsing Xyce `.mt0` artifacts. Xyce native execution
of the public SKY130 AC deck remains diagnostic because it emits no comparable AC metric table.
