# Remote execution environment

Recorded 2026-11-16/17 from the westc server. Secrets are intentionally excluded.

| Item | Value |
|---|---|
| Host | `connect.westc.seetacloud.com:39737` |
| Project checkout | `/root/autodl-tmp/spectra-analog-agent` |
| Working storage | `/root/autodl-tmp` (the `/autodl-fs/data` mount is nearly full; `/autodl-pub/data` is read-only on this instance) |
| Hardware | 2 × NVIDIA GeForce RTX 4090 D, 24,564 MiB each; 32 CPU cores; 124 GB RAM |
| Simulator | ngspice-42 built from the official `ngspice-42.tar.gz` source; SHA-256 `737fe3846ab2333a250dfadf1ed6ebe1860af1d8a5ff5e7803c772cc4256e50a`; install prefix `/root/autodl-tmp/ngspice-42-install` |
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
mechanism evidence. The final source checkout is synchronized to GitHub `main` at commit
`017536507bbf283ba5cfffbbc9f6d098bdd01250`. The eight-row primary aggregate has 864/864 observed cells.
SPECTRA reaches 0.806 TT, 0.194 PVT, 0.1180 mean TT violation and 0.5648 mean PVT violation. The staged
variant reaches 0.833 TT, 0.222 PVT, 0.1052 mean TT violation and 0.5063 mean PVT violation. These results
are scoped to the frozen fixed-topology benchmark and are not a universal SOTA claim.
