ARIS /paper-claim-audit — zero-context evidence verification. You have no context about this project except the files.
Read paper/main.tex, paper/sections/*.tex, paper/numbers.tex, paper/tables/*.tex and the result files:
results/E1_summary.json, results/comparisons.json, results/E4_summary.json, results/E4_haiku_summary.json,
results/E4_tests.json, results/E1_failures.json, results/E1_spectra_prediction_accuracy.json,
results/pvt_failure_conditions.json, results/mc_yield.json, results/pilot/testbench_validation.json,
data/bench/tasks.jsonl, data/bench/designer_tasks.jsonl.
For EVERY quantitative claim in the paper (numbers in text and tables, comparative statements, counts, statistical
statements), find the backing value in the result files and classify it: VERIFIED (matches, incl. rounding),
MISMATCH (value differs: give both), UNSUPPORTED (no file supports it), OVERCLAIM (number right but wording stronger
than the statistics allow, e.g. "significant"/"outperforms" without p<0.05). Also flag hand-typed numbers in
sections/*.tex that are not benchmark constants.
Output: a markdown table (claim | location | value in paper | value in file | verdict), then a summary count per
verdict, then exactly one final line: CLAIM_AUDIT: PASS (no MISMATCH/UNSUPPORTED/OVERCLAIM), WARN (only minor rounding
or wording), or FAIL.
