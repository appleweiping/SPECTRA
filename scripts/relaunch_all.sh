#!/bin/bash
# Idempotently (re)start experiment runners after a container restart. Runners are resumable (skip finished runs;
# LLM responses cached per run tag and call index).
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=5 SPECTRA_SIM_CONCURRENCY=4
start() {  # $1 = unique pattern, rest = command
  local pat="$1"; shift
  if ! pgrep -f -- "$pat" > /dev/null; then nohup "$@" > /dev/null 2>&1 & echo "started: $pat"; else echo "running: $pat"; fi
}
[ -f results/E1_DONE_main ] || start "exp E1 --methods spectra,direct --seeds 0,1,2" bash -c 'SPECTRA_LLM_CONCURRENCY=14 python3 -m scripts.run_bench --exp E1 --methods spectra,direct --seeds 0,1,2 --tasks data/bench/all_tasks_prio.jsonl --workers 14 >> results/E1_run_main.log 2>&1 && touch results/E1_DONE_main'
[ -f results/E1_DONE_aux ] || start "exp E1 --methods genbo,spectra_min" bash -c 'SPECTRA_LLM_CONCURRENCY=8 python3 -m scripts.run_bench --exp E1 --methods genbo,spectra_min --seeds 0,1 --tasks data/bench/all_tasks_prio.jsonl --workers 8 >> results/E1_run_aux.log 2>&1 && touch results/E1_DONE_aux'
[ -f results/E5_DONE ] || start "exp E5" bash -c 'SPECTRA_LLM_CONCURRENCY=4; for m in haiku sonnet; do python3 -m scripts.run_bench --exp E5 --methods spectra,direct --seeds 0,1 --model $m --tasks data/bench/subset_E2.jsonl --workers 4 >> results/E5_run.log 2>&1; done; touch results/E5_DONE'
