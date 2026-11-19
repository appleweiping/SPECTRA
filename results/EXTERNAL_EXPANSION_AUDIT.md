# External benchmark expansion audit

The repository-wide task file uses the same public fixed-topology sizing schema for all 92 tasks and 12 circuit families. The server run `SIZ11g_EXT_FINAL_V3` completed 92 tasks × 8 external-primary rows × 3 seeds, for 2,208/2,208 materialized cells. Every cell used the 300 simulation-unit and 12-call caps, and the independent verifier uses 45 PVT corners on robust tasks.

The complete aggregate is recorded in `results/external_expansion_92_summary.md` and `.json`. SPECTRA reaches TT success 0.761 and robust PVT success 0.123. AnaFlow reaches TT success 0.801 and robust PVT success 0.228. Crash cells are retained in denominators and raw evidence rather than removed from the comparison.

The earlier no-schema launch, missing-API launch and 122-cell partial run remain archived under `results/raw_archive/`. They are excluded from the complete ranking. The complete expansion improves coverage to the requested 92-task/12-family scope, but its measured result does not establish a universal SOTA claim.

The raw archive is `work/remote_archive/SIZ11g_EXT_FINAL_V3.tar.gz` with SHA-256 `F123BA263ABB08BF7705038482E50FC62F7C344943528B09E1811EC23B5CDEEA`.