"""LLM access through the Claude Code CLI (`claude -p`), stateless calls.

* tools disabled, custom system prompt, JSON output -> text + usage
* on-disk cache keyed by (model, system, prompt, run_tag) so reruns are free and
  independent trials (different run_tag) are independent samples
* every call appended to results/llm_usage.jsonl (tokens, cost, latency)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from ..paths import ROOT

CACHE = Path(os.environ.get("SPECTRA_LLM_CACHE", ROOT / "data" / "llm_cache"))
USAGE = ROOT / "results" / "llm_usage.jsonl"
_lock = threading.Lock()
_sem = threading.Semaphore(int(os.environ.get("SPECTRA_LLM_CONCURRENCY", "8")))
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5",
          "fable": "claude-fable-5-1"}


class LLMError(Exception):
    pass


def call(prompt: str, system: str, model: str = "opus", run_tag: str = "", tag: str = "", timeout: int = 900,
         retries: int = 3, effort: str | None = None) -> dict:
    model_id = MODELS.get(model, model)
    key = hashlib.sha256(json.dumps([model_id, system, prompt, run_tag, effort]).encode()).hexdigest()
    cp = CACHE / key[:2] / f"{key}.json"
    if cp.exists():
        d = json.loads(cp.read_text())
        d["cached"] = True
        return d
    cmd = ["claude", "-p", prompt, "--model", model_id, "--output-format", "json", "--tools", "",
           "--system-prompt", system, "--no-session-persistence", "--strict-mcp-config"]
    if effort:
        cmd += ["--effort", effort]
    last = ""
    for attempt in range(retries):
        t0 = time.time()
        with _sem:
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd="/tmp")
            except subprocess.TimeoutExpired:
                last = "timeout"; continue
        dt = time.time() - t0
        try:
            js = json.loads(p.stdout)
        except Exception:
            last = (p.stdout + p.stderr)[-500:]
            time.sleep(5 * (attempt + 1)); continue
        text = js.get("result") or ""
        if js.get("is_error") or not text:
            last = str(js)[:500]
            time.sleep(5 * (attempt + 1)); continue
        u = js.get("usage", {})
        rec = {"text": text, "model": model_id, "seconds": round(dt, 2),
               "input_tokens": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
               "output_tokens": u.get("output_tokens", 0), "cost_usd": js.get("total_cost_usd", 0.0),
               "reported_models": list((js.get("modelUsage") or {}).keys())}
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(rec))
        with _lock:
            USAGE.parent.mkdir(parents=True, exist_ok=True)
            with open(USAGE, "a") as f:
                f.write(json.dumps({"t": time.time(), "tag": tag, "run_tag": run_tag, **{k: v for k, v in rec.items() if k != "text"}}) + "\n")
        rec["cached"] = False
        return rec
    raise LLMError(f"LLM call failed after {retries} attempts: {last}")


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
