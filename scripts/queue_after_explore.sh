#!/bin/bash
cd /home/user/spectra
until grep -q "^app_noninv" data/explore/explore.log; do sleep 20; done
PYTHONPATH=. python3 -m scripts.explore_templates fcasc sf cm_psrc >> data/explore/explore.log 2>&1
PYTHONPATH=. python3 -m scripts.gen_lut tt ff ss sf fs T=-40 T=125 > data/lut/gen_temps.log 2>&1
echo QUEUE_DONE >> data/explore/explore.log
