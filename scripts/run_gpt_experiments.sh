#!/usr/bin/env bash
# GPT-5 mini experiment chain. Run from the server checkout after exporting
# OPENAI_API_KEY. Each stage writes a new experiment namespace (E1g..E5g), so
# historical Claude-backed results are never mixed with the primary analysis.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
MODEL="${SPECTRA_MODEL:-gpt-5-mini}"
WORKERS="${SPECTRA_WORKERS:-8}"
export SPECTRA_GLOBAL_SIM_SLOTS="${SPECTRA_GLOBAL_SIM_SLOTS:-6}"
export SPECTRA_SIM_CONCURRENCY="${SPECTRA_SIM_CONCURRENCY:-4}"
export SPECTRA_LLM_CONCURRENCY="${SPECTRA_LLM_CONCURRENCY:-10}"

run() {
  echo "+ $*" >&2
  python -m scripts.run_bench "$@"
}

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is required; refusing to start paid experiments" >&2
  exit 2
fi

# Fail before spending tokens when a proxy does not advertise the requested
# model (the local proxy may expose a different GPT catalog than api.openai.com).
python - "$MODEL" <<'PY'
import os, sys
from openai import OpenAI
model = sys.argv[1]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
ids = {m.id for m in client.models.list().data}
if model not in ids:
    available = sorted(x for x in ids if x.startswith("gpt-"))
    raise SystemExit(f"Requested model {model!r} is not advertised by the configured endpoint; GPT models: {available}")
print(f"Using advertised model {model}", file=sys.stderr)
PY

# E1g: seed 0 for all four methods on the 61-task primary endpoint, then two
# additional seeds for SPECTRA and the direct baseline on certified T3 tasks.
run --exp E1g --model "$MODEL" --methods spectra,direct,genbo,spectra_min --seeds 0 \
    --tasks data/bench/E1_primary.jsonl --workers "$WORKERS"
run --exp E1g --model "$MODEL" --methods spectra,direct --seeds 1,2 \
    --tasks data/bench/E1_t3.jsonl --workers "$WORKERS"

# E2g: matched component ablations; the subset files freeze task membership.
run --exp E2g --model "$MODEL" --methods spectra_nodiag,spectra_nointent --seeds 0,1 \
    --tasks data/bench/subset_E2.jsonl --workers "$WORKERS"
run --exp E2g --model "$MODEL" --methods spectra_norefine,spectra_noknow,direct_noknow --seeds 0 \
    --tasks data/bench/subset_T3.jsonl --workers "$WORKERS"

# E3g: PVT strategy comparison on the robust subset.
run --exp E3g --model "$MODEL" --methods genbo_full,spectra_pvt_nominal --seeds 0 \
    --tasks data/bench/subset_robust.jsonl --workers "$WORKERS"

# E5g: a same-backbone scaling arm on the primary subset (seed 0).
run --exp E5g --model "$MODEL" --methods spectra,direct --seeds 0 \
    --tasks data/bench/subset_primary.jsonl --workers "$WORKERS"

# E4g: identical fault pool for raw and SPECTRA diagnostic evidence.
python -m scripts.fault_injection "$MODEL"

echo "GPT experiment chain complete; run the parameterized analysis/finalization pipeline next." >&2
