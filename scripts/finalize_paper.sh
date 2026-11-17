#!/bin/bash
# Regenerate every analysis, table, figure and macro from results/ (order of PAPER_ACCEPTANCE_CONTRACT A3), then compile.
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=.
python3 -m scripts.analyze --exp E1
python3 -m scripts.comparisons
python3 -m scripts.pvt_failures
python3 -m scripts.failure_analysis E1
python3 -m scripts.spectra_failures
python3 -m scripts.prediction_accuracy E1 spectra
python3 -m scripts.e4_tests
python3 -m scripts.make_tables
python3 -m scripts.bench_stats
python3 -m scripts.make_figures
python3 -m scripts.paper_numbers
cd paper && latexmk -pdf -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
pdfinfo main.pdf | grep Pages
grep -c "Overfull\|undefined" main.log || true
