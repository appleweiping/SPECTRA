#!/bin/bash
cd /home/user/spectra
until grep -q "^QUEUE2_DONE" data/explore/explore.log; do sleep 20; done
PYTHONPATH=. python3 -m scripts.explore_templates cm_psrc >> data/explore/explore.log 2>&1
echo QUEUE3_DONE >> data/explore/explore.log
