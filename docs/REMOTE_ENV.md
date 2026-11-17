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
never committed. The configured proxy currently advertises GPT-5.6-sol/GPT-5.6-terra and does not advertise
`gpt-5-mini`; this is a pending model-selection decision, so experiment scripts keep the model configurable through
`SPECTRA_MODEL` and refuse to run without `OPENAI_API_KEY`.

Validation: one short `gpt-5.6-sol` request returned `OK`; `gpt-5-mini` was absent from the advertised catalog and a
direct request returned HTTP 503 from the proxy. No benchmark run was started under the wrong model.
