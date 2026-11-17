Round 2 of negotiating the acceptance contract for an ICCAD paper (experiments still running). In round 1 you
rejected the contract with 11 numbered demands (paper/.contract_r1.md). The executor revised the contract
(paper/PAPER_ACCEPTANCE_CONTRACT.md) and changed code/text accordingly; verify against the repository, do not trust
this summary:
- 1200-cap robust runs moved to results/raw_cap1200_archive/ and being re-run natively at 600 (EXPERIMENT_LOG.md last
  entry; scripts/analyze.py now excludes >600-cap robust runs; scripts/run_rerun_cap600.sh).
- scripts/comparisons.py (matched-task blocks) feeds tables and text; scripts/make_tables.py computes seed ranges in
  captions; scripts/pvt_failures.py restricted to E1 main methods with a run list; TIER_GROUPS/load_common in analyze.py.
- paper/sections/*.tex: "pre-registered" removed; setup discloses LUT asymmetry, caching, re-runs and the harness fix;
  bench metrics paragraph drops wall-clock; Declare-Infeasible count macro; PVT failure statements macro-generated.
Judge the CONTRACT (is it complete, checkable and satisfiable?), not whether the draft already satisfies it
(experiments and MC yield are pending). Same scope rules as before: no hashing schemes or speculative machinery; say
plainly what is fine; do not manufacture findings.
End with exactly one line:
CONTRACT_ACCEPTED: yes    or    CONTRACT_ACCEPTED: no
followed by numbered revision demands if no.
