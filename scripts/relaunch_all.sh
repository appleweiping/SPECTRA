#!/bin/bash
cd /home/user/spectra
start() { local pat="$1"; shift; if ! pgrep -f -- "$pat" > /dev/null; then nohup "$@" > /dev/null 2>&1 & echo "started: $pat"; else echo "running: $pat"; fi; }
[ -f results/E1_V2_DONE ] || start "run_E1_v3.sh" bash scripts/run_E1_v3.sh
[ -f results/E2E3_DONE ] || start "run_E2_E3_v2.sh" bash scripts/run_E2_E3_v2.sh
[ -f results/RERUN600_DONE ] || start "run_rerun_cap600.sh" bash scripts/run_rerun_cap600.sh
[ -f results/MC_DONE ] || start "run_mc.sh" bash scripts/run_mc.sh
