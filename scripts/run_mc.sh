#!/bin/bash
# Mismatch Monte Carlo after all robust runs are final (E1, E3 and the 600-cap re-runs).
cd /home/user/spectra
export PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=6 SPECTRA_SIM_CONCURRENCY=4
until [ -f results/E1_V2_DONE ] && [ -f results/E2E3_DONE ] && [ -f results/RERUN600_DONE ]; do sleep 60; done
python3 -m scripts.mc_yield 100 >> results/mc_yield.log 2>&1
touch results/MC_DONE
