#!/bin/bash
# E1 final protocol (v3): robust then T3; T1/T2/designer use the runs already completed.
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=6 SPECTRA_SIM_CONCURRENCY=4
R="python3 -m scripts.run_bench --exp E1"
SPECTRA_LLM_CONCURRENCY=12 $R --methods spectra,direct --seeds 0,1 --tasks data/bench/E1_robust.jsonl --workers 12 >> results/E1_v2.log 2>&1 &
SPECTRA_LLM_CONCURRENCY=8  $R --methods genbo,spectra_min --seeds 0 --tasks data/bench/E1_robust.jsonl --workers 6 >> results/E1_v2.log 2>&1 &
wait
SPECTRA_LLM_CONCURRENCY=12 $R --methods spectra,direct --seeds 0,1 --tasks data/bench/E1_t3.jsonl --workers 12 >> results/E1_v2.log 2>&1 &
SPECTRA_LLM_CONCURRENCY=8  $R --methods genbo,spectra_min --seeds 0 --tasks data/bench/E1_t3.jsonl --workers 8 >> results/E1_v2.log 2>&1 &
wait
touch results/E1_V2_DONE
