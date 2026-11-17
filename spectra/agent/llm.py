"""Stateless LLM calls with a persistent cache.

The project used to shell out to the Claude Code CLI.  Claude is no longer an
allowed backend for this project, so calls now go through the OpenAI Python
client.  The public :func:`call` contract and cache/usage record format remain
unchanged; this keeps the experiment runners and cached results compatible.

The OpenAI import is intentionally lazy.  Importing the rest of SPECTRA (for
example to analyse old results) must still work on a machine without the
optional ``openai`` package.  A clear ``LLMError`` is raised only when a GPT
call is actually requested.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

from ..paths import ROOT

CACHE = Path(os.environ.get("SPECTRA_LLM_CACHE", ROOT / "data" / "llm_cache"))
USAGE = ROOT / "results" / "llm_usage.jsonl"
_lock = threading.Lock()
_sem = threading.Semaphore(int(os.environ.get("SPECTRA_LLM_CONCURRENCY", "8")))
# Aliases used by the run scripts.  Keep this table deliberately GPT-only: a
# stale ``--model opus``/``claude-*`` invocation must fail instead of silently
# sending data to the retired Claude backend.
MODELS = {
    "gpt": "gpt-6.1-sol",
    "openai": "gpt-6.1-sol",
    "gpt-mini": "gpt-6.1-sol",
    "gpt-6.1-sol": "gpt-6.1-sol",
    "gpt61-sol": "gpt-6.1-sol",
    "gpt-5.1": "gpt-5.1",
    "gpt5.1": "gpt-5.1",
    "gpt-5": "gpt-5",
    "gpt5": "gpt-5",
}

# USD per one million tokens.  The configured GPT-6.1-sol gateway does not
# publish a USD tariff, so its default is deliberately zero rather than an
# invented price.  Operators can set the two SPECTRA_OPENAI_*_PRICE variables
# when an accountable tariff is available; token counts remain recorded either
# way.
_DEFAULT_PRICES = {
    "gpt-6.1-sol": (0.0, 0.0),
    "gpt-5.1": (1.25, 10.00),
    "gpt-5": (1.25, 10.00),
}


class LLMError(Exception):
    pass


def call(prompt: str, system: str, model: str = "gpt-6.1-sol", run_tag: str = "", tag: str = "", timeout: int = 900,
         retries: int = 6, effort: str | None = None) -> dict:
    model_id = MODELS.get(model.lower(), model)
    if model_id.lower().startswith("claude") or model.lower() in {"opus", "sonnet", "haiku", "fable"}:
        raise LLMError(
            f"Claude model '{model}' is disabled for this project. "
            "Use a GPT alias such as --model gpt-6.1-sol or --model gpt-5.1."
        )
    if not (model_id.lower().startswith("gpt-") or model_id.lower().startswith(("o1", "o3", "o4"))):
        raise LLMError(
            f"Unsupported LLM model '{model}'. Use an OpenAI GPT model "
            "(for example gpt-6.1-sol or gpt-5.1)."
        )
    key = hashlib.sha256(json.dumps([model_id, system, prompt, run_tag, effort]).encode()).hexdigest()
    cp = CACHE / key[:2] / f"{key}.json"
    if cp.exists():
        d = json.loads(cp.read_text())
        d["cached"] = True
        return d
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - exercised in deployment
        raise LLMError(
            "The GPT backend requires the optional 'openai' package. "
            "Install it with: python -m pip install openai"
        ) from exc
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set; refusing to make an unauthenticated GPT call")

    # The SDK uses HTTPS directly and does not create a console process.  This
    # keeps Windows runs headless (the project's CREATE_NO_WINDOW policy still
    # applies to any future subprocess-based launcher).
    client = OpenAI(api_key=api_key, timeout=timeout)
    last = ""
    for attempt in range(retries):
        t0 = time.time()
        with _sem:
            try:
                kwargs = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                }
                # GPT family models support reasoning_effort on Chat
                # Completions.  Omit it when unset to preserve model defaults.
                if effort:
                    kwargs["reasoning_effort"] = effort
                p = client.chat.completions.create(**kwargs)
            except Exception as exc:
                last = f"{type(exc).__name__}: {exc}"
                if attempt + 1 < retries:
                    time.sleep(min(300, 15 * 2 ** attempt))
                continue
        dt = time.time() - t0
        try:
            choice = p.choices[0]
            text = choice.message.content or ""
        except Exception as exc:
            last = f"Malformed OpenAI response: {exc}"
            if attempt + 1 < retries:
                time.sleep(min(300, 15 * 2 ** attempt))
            continue
        if not text.strip():
            last = "OpenAI returned an empty response"
            if attempt + 1 < retries:
                time.sleep(min(300, 15 * 2 ** attempt))
            continue
        u = getattr(p, "usage", None)
        input_tokens = int(getattr(u, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(u, "completion_tokens", 0) or 0)
        # ``prompt_tokens`` already includes cached input in the Chat
        # Completions API.  Some compatible gateways expose ``input_tokens``
        # instead, so accept that spelling as a fallback.
        if not input_tokens:
            input_tokens = int(getattr(u, "input_tokens", 0) or 0)
        if not output_tokens:
            output_tokens = int(getattr(u, "output_tokens", 0) or 0)
        in_price, out_price = _prices_for(model_id)
        cost = input_tokens / 1_000_000 * in_price + output_tokens / 1_000_000 * out_price
        reported_model = getattr(p, "model", None) or model_id
        rec = {"text": text, "model": model_id, "seconds": round(dt, 2),
               "input_tokens": input_tokens,
               "output_tokens": output_tokens,
               "cost_usd": round(cost, 8),
               "reported_models": [reported_model]}
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(rec))
        with _lock:
            USAGE.parent.mkdir(parents=True, exist_ok=True)
            with open(USAGE, "a") as f:
                f.write(json.dumps({"t": time.time(), "tag": tag, "run_tag": run_tag, **{k: v for k, v in rec.items() if k != "text"}}) + "\n")
        rec["cached"] = False
        return rec
    raise LLMError(f"LLM call failed after {retries} attempts: {last}")


def _prices_for(model_id: str) -> tuple[float, float]:
    """Return (input, output) USD/M tokens, with environment overrides."""
    base = model_id.lower()
    # Prefix matching lets dated model IDs (e.g. gpt-5.1-2026-...) use the
    # corresponding published price while still allowing explicit overrides.
    in_default, out_default = next(
        (v for k, v in _DEFAULT_PRICES.items() if base == k or base.startswith(k + "-")),
        (0.0, 0.0),
    )
    def env_price(name: str, default: float) -> float:
        raw = os.environ.get(name)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError as exc:
            raise LLMError(f"{name} must be a number, got {raw!r}") from exc
    return (
        env_price("SPECTRA_OPENAI_INPUT_PRICE_USD_PER_MILLION", in_default),
        env_price("SPECTRA_OPENAI_OUTPUT_PRICE_USD_PER_MILLION", out_default),
    )


def extract_block(text: str, lang: str) -> str | None:
    """Return the LAST fenced code block of the given language (or any if lang='')."""
    import re
    blocks = re.findall(r"```(\w*)\s*\n(.*?)```", text, re.S)
    cands = [b for l, b in blocks if (not lang or l.lower() == lang)]
    return cands[-1] if cands else None


def extract_json(text: str, merge: bool = True):
    """Parse ```json blocks. With merge=True all dict blocks are merged in order (later keys win), because models
    often split e.g. {"action": ...} and {"params": ..., "bounds": ...} into separate blocks."""
    import re
    if merge:
        merged, found = {}, False
        for lang, body in re.findall(r"```(\w*)\s*\n(.*?)```", text, re.S):
            if lang.lower() not in ("json", ""):
                continue
            try:
                d = json.loads(body)
            except Exception:
                continue
            if isinstance(d, dict):
                merged.update(d); found = True
        if found:
            return merged
    b = extract_block(text, "json")
    for cand in ([b] if b else []) + [text]:
        if not cand:
            continue
        try:
            return json.loads(cand)
        except Exception:
            s, e = cand.find("{"), cand.rfind("}")
            if s >= 0 and e > s:
                try:
                    return json.loads(cand[s:e + 1])
                except Exception:
                    pass
    return None
