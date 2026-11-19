# Main sizing comparison protocol

The primary comparison contains one SPECTRA row and seven paper-backed external framework rows.
The rows are AnalogCoder, ADO-LLM, AnaFlow, Artisan, AutoSizer, ATLAS and GLOVA. Their identities,
venues, source links, official-code availability and clean-room adaptations are recorded in
`data/bench/paper_sizing_manifest.json`.

## Primary scope

- **Tasks:** 36 fixed-topology SKY130 tasks across six families: opamp, amp, cmirror, filter, ldo and vco.
- **Robustness:** 24 nominal tasks and 12 robust tasks. Robust tasks are independently checked on the 45-corner PVT grid.
- **Seeds:** 0, 1 and 2, giving 108 task-seed cells per row and 864 primary cells in total.
- **Budget:** 300 condition-evaluation units and 12 LLM calls per cell. The task text, topology digest, variable bounds, simulator, PDK and verifier are shared.
- **Reported endpoints:** TT success, robust PVT success, normalized TT violation, normalized PVT violation, simulation units, LLM calls, wall time, token counts, crashes and failure taxonomy. Mismatch is unavailable for this public fixed-topology task file and is not used to rank the primary rows.

The 300-unit cap is the common resource constraint. The external clean-room adapters use the preregistered three-corner search objective. The native SPECTRA robust adapter uses a 45-corner PVT-aware search objective. This search-grid difference is recorded in the result schema and is a protocol caveat, while the independent 45-corner verifier and total condition-evaluation cap remain shared.

## Statistical reporting

The aggregate keeps every task-seed cell. Confidence intervals use task-clustered bootstrap resampling, so the three seeds for one task are not treated as independent tasks. SPECTRA-versus-external paired TT tests use exact sign tests with Holm correction across the seven external rows. The three-seed result is a matched-budget snapshot. It does not support a universal analog-sizing SOTA claim.

The repository-wide expansion uses `data/bench/all_sizing_tasks.jsonl`, which exposes the same sizing schema for 92
tasks across 12 circuit families. The complete server run materialized 2,208/2,208 cells across the eight
external-primary rows. Aggregate metrics and the raw archive SHA are recorded in
`results/external_expansion_92_summary.md` and `results/EXTERNAL_EXPANSION_AUDIT.md`. The expansion provides broad
coverage and failure analysis, while its measured SPECTRA row remains below AnaFlow.

## Excluded from the primary ranking

The legacy E1/EXT7g direct, Gen+TPE, SPECTRA-min, optimizer-control and template-oracle arms remain in their historical diagnostic tables. They are internal controls or privileged upper bounds, not paper-backed external frameworks, and are excluded from the primary eight-row ranking. The SPECTRA-PVT-staged run is a predeclared sensitivity analysis and is reported separately from the primary SPECTRA row.

## Current evidence

The three-seed aggregate is in `results/paper_sizing_multiseed.json` and `results/paper_sizing_multiseed.md`. The frozen full-grid SPECTRA row has TT success 0.806 and PVT success 0.194. AnaFlow has TT success 0.870 and PVT success 0.306. The matched hybrid sensitivity improves SPECTRA to TT 0.889 and PVT 0.306, tying AnaFlow on PVT, while racing lowers PVT violation without increasing PVT success. A separately archived union-top-k4 candidate track reaches TT 0.917 and PVT 0.333 on the same 36-task protocol, exceeding AnaFlow on both success endpoints. The complete 92-task expansion reports the preregistered SPECTRA row at TT 0.761 and PVT 0.123 versus AnaFlow TT 0.801 and PVT 0.228, while the family-policy sensitivity reaches TT 0.804 and PVT 0.263. The identical union-top-k4 policy is being completed on the 92-task expansion before the final candidate ranking is frozen. These values support a scoped fixed-topology comparison and do not establish whole-domain SOTA.
