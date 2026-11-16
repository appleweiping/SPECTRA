#!/bin/bash
# E1 main comparison. All tasks x 3 seeds. Oracle only on tasks with a reference template.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_LLM_CONCURRENCY=10 SPECTRA_SIM_CONCURRENCY=4
cat data/bench/tasks.jsonl data/bench/designer_tasks.jsonl data/bench/control_tasks.jsonl > data/bench/all_tasks.jsonl
python3 -m scripts.run_bench --exp E1 --methods spectra,direct,genbo,spectra_min --seeds 0,1,2 \
    --tasks data/bench/all_tasks.jsonl --workers 10 >> results/E1_run.log 2>&1
cat data/bench/tasks.jsonl data/bench/control_tasks.jsonl > data/bench/ref_tasks.jsonl
python3 -m scripts.run_bench --exp E1 --methods oracle_cmaes --seeds 0,1,2 --tasks data/bench/ref_tasks.jsonl \
    --workers 4 >> results/E1_run.log 2>&1
echo E1_DONE >> results/E1_run.log
