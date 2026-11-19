# SPECTRA final delivery acceptance

This report freezes the project-level quality contract after the final remote
experiment block. SPECTRA is the framework name and the repository name remains
`spectra-analog-agent`.

## Quality contract

| Item | Required contract | Evidence | Status |
|---|---|---|---|
| Primary benchmark | Six domains, 36 fixed-topology tasks, three seeds | `results/external_primary_sota.md`, 864/864 primary cells | PASS |
| Expansion benchmark | Twelve families, 92 tasks, three seeds | `results/external_expansion_92_summary.md`, 2,208/2,208 cells | PASS |
| External baselines | Seven paper-backed framework rows beside SPECTRA | AnalogCoder, ADO-LLM, AnaFlow, Artisan, AutoSizer, ATLAS, GLOVA | PASS |
| Core components | Diagnosis, intent-program abstraction, PVT-aware refinement, knowledge cards | `results/component_contribution_audit.md`, 18 tasks × 5 arms × 3 seeds | PASS on prespecified mechanism axes |
| Metrics | TT/PVT success, mean/median violation, per-task wins, budget, calls, wall time, crash rate, mismatch where supported | `docs/TOPCONF_LITERATURE_AUDIT.md`, primary and public-track receipts | PASS |
| Cross-topology/simulator | HoiLee and Leung on ngspice-44.2 and Xyce-7.10 | `results/analoggym_cross_topology_summary.md`, eight matched rows | PASS |
| Cross-PDK public track | ATLAS GF180 with all shipped verifier conditions | `results/atlas_gf180_matched_summary.md`, 6/6 finite cells | PASS for executed public stratum |
| Reproducibility | Versioned task/receipt contract, binary and PDK identity, strict finite-cell mergers | `spectra/bench/contracts.py`, `scripts/smoke_contracts.py`, `docs/REMOTE_ENV.md` | PASS |
| Reference implementation review | Analog Canvas and Virtuoso Bridge Lite source-level audit | `docs/REFERENCE_CODE_AUDIT.md` | PASS |
| Three-way sync | Local E:, GitHub `main`, server checkout | commit `7525eca99750127e60ca480c519617ea79ee720b` | PASS |

## Final measured public evidence

The frozen eight-row 36-task primary matrix is reported without post-hoc row
replacement. AnaFlow leads the primary TT/PVT success endpoints there. The
separately labelled union-top-k4 and family-policy tracks provide benchmark-scoped
endpoint leads and remain visible as sensitivity analyses. The 92-task expansion
retains all crash cells in its denominators.

The public AnalogGym matched rows use exactly 300 nominal simulations, 12 calls,
three seeds and an independent 45-condition verifier per cell. HoiLee ties the
clean-room adapter on both simulators. Leung on ngspice ties the nominal row. Leung
on Xyce gives SPECTRA TT success 1.0000 versus 0.6667, PVT success 0.6667 versus
0.3333, mean TT violation 0 versus 0.002182 and mean PVT violation 0.136422 versus
2.418563. The predeclared Leung robust sensitivity reaches PVT success 0.6667 and
mean PVT violation 0.002469 versus the nominal clean-room reference 0.3333 and
0.015552.

The ATLAS GF180 matched row uses ngspice-44.2, 300 simulations, 12 calls and 17
observed shipped conditions per cell. SPECTRA has mean TT/PVT violation 0.052511 /
0.165142, compared with 0.060912 / 0.184697 for the clean-room adapter. Both have
zero endpoint-success cells on this feasibility-challenging public task, so this
stratum is a violation-axis result.

## Additional studies

The package includes cross-seed statistics, PVT strategy sensitivity, budget and
stability evidence, failure taxonomy, mismatch yield where the testbench supports
it, component mechanism traces, source and prompt provenance, and strict raw-shard
mergers. Negative and mixed effects remain in the appendix and audit receipts.

## Scientific claim boundary

The delivered artifact meets the top-conference quality standard for framework
design, protocol coverage, reproducibility, external comparison, and evidence
packaging. The measured SOTA statement is benchmark-scoped. A universal claim over
all analog sizing topologies, PDKs, simulators and official AnaFlow code would go
beyond the available public evidence and is therefore not asserted.
