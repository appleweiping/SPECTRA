#!/bin/bash
# Regenerate every analysis, table, figure and macro from results/ (order of PAPER_ACCEPTANCE_CONTRACT A3), then compile.
# The defaults point at the GPT-6.1-sol namespaces.  Set SPECTRA_*_EXP only when
# intentionally reproducing the historical E1/E4 artifacts.
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=.
MAIN_EXP="${SPECTRA_MAIN_EXP:-E1g}"
E2_EXP="${SPECTRA_E2_EXP:-E2g}"
E3_EXP="${SPECTRA_E3_EXP:-E3g}"
E4_EXP="${SPECTRA_E4_EXP:-E4g}"
E5_EXP="${SPECTRA_E5_EXP:-E5g}"
E4_ALT_EXP="${SPECTRA_E4_ALT_EXP-}"
E4_TESTS="${SPECTRA_E4_TESTS:-E4g_tests}"
export SPECTRA_MAIN_EXP="$MAIN_EXP" SPECTRA_E2_EXP="$E2_EXP" SPECTRA_E3_EXP="$E3_EXP" \
  SPECTRA_E4_EXP="$E4_EXP" SPECTRA_E5_EXP="$E5_EXP" SPECTRA_E4_ALT_EXP="$E4_ALT_EXP" \
  SPECTRA_E4_MAIN_LABEL="${SPECTRA_E4_MAIN_LABEL:-GPT-6.1-sol}" SPECTRA_STRIP_MODEL_SUFFIX=1
python3 -m scripts.analyze --exp "$MAIN_EXP" --strip-model-suffix
python3 -m scripts.comparisons --e1 "$MAIN_EXP" --e2 "$E2_EXP" --e3 "$E3_EXP" --e5 "$E5_EXP" --strip-model-suffix
python3 -m scripts.mc_yield "${SPECTRA_MC_N:-100}" --e1 "$MAIN_EXP" --e3 "$E3_EXP"
python3 -m scripts.pvt_failures "$MAIN_EXP"
python3 -m scripts.failure_analysis "$MAIN_EXP"
python3 -m scripts.spectra_failures "$MAIN_EXP"
python3 -m scripts.prediction_accuracy "$MAIN_EXP" spectra
python3 -m scripts.e4_tests --main "$E4_EXP" --alt "$E4_ALT_EXP" --main-key main --output "$E4_TESTS"
python3 -m scripts.make_tables
python3 -m scripts.bench_stats
python3 -m scripts.make_figures "$MAIN_EXP"
python3 -m scripts.paper_numbers --main-exp "$MAIN_EXP" --e4-exp "$E4_EXP" --e4-alt-exp "$E4_ALT_EXP" --e4-tests "$E4_TESTS"
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
pdfinfo main.pdf | grep Pages
if grep -Eq "Overfull|undefined" main.log; then
  echo "LaTeX warnings found in paper/main.log" >&2
  exit 3
fi
