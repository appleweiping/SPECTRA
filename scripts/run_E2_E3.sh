#!/bin/bash
# E2 (priority order per review round 1) then E3.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=5 SPECTRA_SIM_CONCURRENCY=4 SPECTRA_LLM_CONCURRENCY=10
python3 -m scripts.run_bench --exp E2 --methods spectra_nodiag,spectra_nointent --seeds 0,1,2 \
    --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E2_run.log 2>&1
python3 - <<'PY'
import json
ts = [json.loads(l) for l in open("data/bench/subset_E2.jsonl")]
with open("data/bench/subset_T3.jsonl", "w") as f:
    for t in ts:
        if not t.get("robust") and str(t["tier"]) == "3": f.write(json.dumps(t) + "\n")
ts = [json.loads(l) for f in ["data/bench/tasks.jsonl", "data/bench/designer_tasks.jsonl"] for l in open(f)]
with open("data/bench/robust_tasks.jsonl", "w") as f:
    for t in ts:
        if t.get("robust"): f.write(json.dumps(t) + "\n")
PY
python3 -m scripts.run_bench --exp E2 --methods spectra_noknow,direct_noknow --seeds 0,1 \
    --tasks data/bench/subset_T3.jsonl --workers 10 >> results/E2_run.log 2>&1
python3 -m scripts.run_bench --exp E2 --methods spectra_norefine,genbo_cmaes --seeds 0,1 \
    --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E2_run.log 2>&1
python3 -m scripts.run_bench --exp E3 --methods genbo_full,spectra_pvt_nominal,spectra_pvt_all --seeds 0,1 \
    --tasks data/bench/robust_tasks.jsonl --workers 8 >> results/E3_run.log 2>&1
python3 -m scripts.run_bench --exp E2 --methods oracle_cmaes --seeds 0,1 \
    --tasks data/bench/subset_E2.jsonl --workers 4 >> results/E2_run.log 2>&1
touch results/E2E3_DONE
