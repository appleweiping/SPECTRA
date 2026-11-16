#!/bin/bash
cd /home/user/spectra
until grep -q "^QUEUE_DONE" data/explore/explore.log; do sleep 30; done
PYTHONPATH=. python3 -m scripts.explore_templates ota5t >> data/explore/explore.log 2>&1
echo QUEUE2_DONE >> data/explore/explore.log
