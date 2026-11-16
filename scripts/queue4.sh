#!/bin/bash
cd /home/user/spectra
until grep -q "^QUEUE3_DONE" data/explore/explore.log; do sleep 20; done
PYTHONPATH=. python3 -m scripts.build_bench cmirror > data/bench/build_D.log 2>&1
echo BUILD_D_DONE >> data/bench/build_D.log
