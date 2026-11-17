#!/bin/bash
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=6 SPECTRA_SIM_CONCURRENCY=4
R="python3 -m scripts.run_bench --exp E1"
while pgrep -f "exp E1 --methods spectra,direct,genbo,spectra_min --seeds 0" > /dev/null; do sleep 30; done
SPECTRA_LLM_CONCURRENCY=14 $R --methods spectra,direct,genbo,spectra_min --seeds 0 --tasks data/bench/E1_primary.jsonl --workers 16 >> results/E1_v2.log 2>&1
SPECTRA_LLM_CONCURRENCY=14 $R --methods spectra,direct --seeds 1 --tasks data/bench/E1_t3.jsonl --workers 14 >> results/E1_v2.log 2>&1
touch results/E1_V2_DONE
