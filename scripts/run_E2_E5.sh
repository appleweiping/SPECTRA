#!/bin/bash
# E2 ablations + Gen+CMA-ES on the stratified subset; E3 PVT strategies on robust tasks; E5 backbones.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_LLM_CONCURRENCY=10 SPECTRA_SIM_CONCURRENCY=4
python3 -m scripts.make_subset
python3 -m scripts.run_bench --exp E2 --methods spectra_nodiag,spectra_nointent,spectra_norefine,genbo_cmaes,oracle_cmaes --seeds 0,1,2 \
    --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E2_run.log 2>&1
python3 - <<'PY'
import json
ts = [json.loads(l) for f in ["data/bench/tasks.jsonl", "data/bench/designer_tasks.jsonl"] for l in open(f)]
with open("data/bench/robust_tasks.jsonl", "w") as f:
    for t in ts:
        if t.get("robust"): f.write(json.dumps(t) + "\n")
PY
python3 -m scripts.run_bench --exp E3 --methods spectra_pvt_all,spectra_pvt_nominal --seeds 0,1,2 \
    --tasks data/bench/robust_tasks.jsonl --workers 8 >> results/E3_run.log 2>&1
for m in sonnet haiku; do
  python3 -m scripts.run_bench --exp E5 --methods spectra,direct --seeds 0,1 --model $m \
      --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E5_run.log 2>&1
done
echo E2E5_DONE >> results/E2_run.log
