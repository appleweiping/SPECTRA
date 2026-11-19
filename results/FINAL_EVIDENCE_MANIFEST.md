# Final evidence manifest

The strict sizing evidence was generated on the westc server and retained there under
`/root/autodl-tmp/spectra-analog-agent/results/raw/`. The local audit bundle is
`work/remote_archive/siz7g_final_bundle.tar.gz`.

| Item | Value |
|---|---|
| Final source checkout | Verified by `git rev-parse HEAD` on local E:, server and GitHub after the unified-policy run |
| Primary run source | `017536507bbf283ba5cfffbbc9f6d098bdd01250` |
| Post-fix staged run source | `3347b38c19efe60dfbaa5bd71c7fe898207ea199` |
| Server checkout | `/root/autodl-tmp/spectra-analog-agent` |
| Primary archive SHA-256 | `8a360f800f0460e3bcfed188ead3d77dca4c6e6bf56832aa39c90d3eb1348a5a` |
| Post-fix staged archive SHA-256 | `56695cd111867bff21df3847832e87610e9c20d0cc50f66ba310c217e6e4f6db` |
| Expansion audit archive SHA-256 | `dbec58bf6ed7386179efa1fee71f857dc439b69dcadc2a5830184b4c30d8d8f5` |
| Primary cells | 8 frameworks × 36 tasks × 3 seeds = 864 |
| Budget | 300 simulation units and 12 LLM calls per task cell |
| Verifier | 45-corner PVT grid |
| Primary SPECTRA | TT 0.806, PVT 0.194, TT violation 0.1180, PVT violation 0.5648 |
| Staged SPECTRA sensitivity, post-fix | TT 0.815, PVT 0.222, TT violation 0.1071, PVT violation 0.5009 |

The primary protocol records SPECTRA's full-grid PVT-aware search objective and the preregistered three-corner
search objective used by the external clean-room adapters. The verifier and reported budget are shared. The
component track remains a mixed-effect ablation and is not converted into an all-components-win claim. The
post-fix staged rerun replaced the earlier pre-fix staged sensitivity result in the tracked summary.

The complete 92-task expansion is recorded in `results/EXTERNAL_EXPANSION_AUDIT.md`. It contains 2,208/2,208
external-primary cells across eight rows, 12 families and three seeds. The SPECTRA family-policy candidate covers
276/276 additional cells. The unified union-top-k4 candidate is being evaluated on the same 92-task matrix before
the final ranking is frozen.
