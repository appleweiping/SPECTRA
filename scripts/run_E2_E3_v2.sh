#!/bin/bash
# Continuation chain (reduced): waits for the running E2 core ablations, then the rest.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=5 SPECTRA_SIM_CONCURRENCY=4 SPECTRA_LLM_CONCURRENCY=10
R="python3 -m scripts.run_bench"
while pgrep -f "exp E2 --methods spectra_nodiag,spectra_nointent" > /dev/null; do sleep 30; done
$R --exp E2 --methods spectra_nodiag,spectra_nointent --seeds 0,1 --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E2_run.log 2>&1
python3 - <<'PY'
import json
ts = [json.loads(l) for l in open("data/bench/subset_E2.jsonl")]
with open("data/bench/subset_T3.jsonl", "w") as f:
    for t in ts:
        if not t.get("robust") and str(t["tier"]) == "3": f.write(json.dumps(t) + "\n")
PY
$R --exp E2 --methods spectra_noknow,direct_noknow,spectra_norefine,genbo_cmaes --seeds 0 --tasks data/bench/subset_T3.jsonl --workers 10 >> results/E2_run.log 2>&1
$R --exp E3 --methods genbo_full,spectra_pvt_nominal,spectra_pvt_all --seeds 0 --tasks data/bench/subset_robust.jsonl --workers 8 >> results/E3_run.log 2>&1
for m in haiku sonnet; do $R --exp E5 --methods spectra,direct --seeds 0 --model $m --tasks data/bench/subset_E2.jsonl --workers 6 >> results/E5_run.log 2>&1; done
touch results/E2E3_DONE
