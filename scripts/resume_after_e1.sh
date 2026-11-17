#!/bin/bash
# resume paused E2/E3/E5 chain once E1 seed-0 primary phase has finished
cd /home/user/spectra
while pgrep -f "exp E1 --methods spectra,direct,genbo,spectra_min --seeds 0" > /dev/null; do sleep 60; done
for pid in $(pgrep -f "run_E2_E3_v2.sh") $(pgrep -f "run_bench --exp E2") $(pgrep -f "run_bench --exp E3") $(pgrep -f "run_bench --exp E5"); do kill -CONT $pid; done
