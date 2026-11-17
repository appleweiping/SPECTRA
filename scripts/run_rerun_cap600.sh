#!/bin/bash
# Native 600-cap re-runs of robust E2 runs archived from the 1200-cap protocol (see EXPERIMENT_LOG 2026-11-17 04:40).
# E1 and E5 re-runs are picked up by their own chains (job lists are rebuilt when each step starts).
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=6 SPECTRA_SIM_CONCURRENCY=4
until [ -f results/E2E3_DONE ]; do sleep 60; done
SPECTRA_LLM_CONCURRENCY=10 python3 -m scripts.run_bench --exp E2 --methods spectra_nodiag,spectra_nointent --seeds 0,1 --tasks data/bench/subset_E2.jsonl --workers 10 >> results/E2_run.log 2>&1
touch results/RERUN600_DONE
