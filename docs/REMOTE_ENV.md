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
