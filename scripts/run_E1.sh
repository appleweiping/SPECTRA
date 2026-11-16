#!/bin/bash
# E1 main comparison: all tasks x 3 seeds x {SPECTRA, AnalogCoder-style, Gen+TPE, SPECTRA-min}.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_LLM_CONCURRENCY=12 SPECTRA_SIM_CONCURRENCY=4
cat data/bench/tasks.jsonl data/bench/designer_tasks.jsonl data/bench/control_tasks.jsonl > data/bench/all_tasks.jsonl
python3 -m scripts.run_bench --exp E1 --methods spectra,direct,genbo,spectra_min --seeds 0,1,2 \
    --tasks data/bench/all_tasks.jsonl --workers 12 >> results/E1_run.log 2>&1
echo E1_DONE >> results/E1_run.log
