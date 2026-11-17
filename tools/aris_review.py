#!/usr/bin/env python3
"""Run an ARIS-style independent review with a GPT-family model.

The previous bridge started ``claude -p`` and therefore could silently spend the
retired Claude quota. This bridge uses the same OpenAI backend as experiments,
starts a fresh cache key for every review, and supplies the reviewer with a
bounded read-only context bundle. ``--include`` can be repeated to select the
primary artifacts for a particular review.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from spectra.agent import llm
DEFAULT_INCLUDE = (
    "README.md",
    "HANDOFF.md",
    "EXPERIMENT_LOG.md",
    "NARRATIVE_REPORT.md",
    "paper/PAPER_ACCEPTANCE_CONTRACT.md",
    "paper/main.tex",
)
MAX_FILE_CHARS = 24_000
MAX_CONTEXT_CHARS = 140_000


def _safe_path(raw: str) -> Path | None:
    p = (ROOT / raw).resolve()
    try:
        p.relative_to(ROOT)
    except ValueError:
        return None
    return p if p.is_file() else None


def _paths_from_prompt(prompt: str) -> list[str]:
    """Extract likely repository-relative file paths mentioned by a review prompt."""
    candidates: list[str] = []
    for token in re.findall(r"(?<![\w])(?:[\w.-]+/)+[\w.-]+", prompt):
        if token not in candidates and _safe_path(token):
            candidates.append(token)
    return candidates


def build_context(prompt: str, includes: list[str]) -> tuple[str, list[str]]:
    paths = list(includes) if includes else list(DEFAULT_INCLUDE)
    for p in _paths_from_prompt(prompt):
        if p not in paths:
            paths.append(p)
    chunks: list[str] = []
    used: list[str] = []
    total = 0
    for raw in paths:
        p = _safe_path(raw)
        if p is None:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n[truncated by reviewer bridge]\n"
        block = f"\n===== {p.relative_to(ROOT).as_posix()} =====\n{text}\n"
        if total + len(block) > MAX_CONTEXT_CHARS:
            break
        chunks.append(block)
        used.append(p.relative_to(ROOT).as_posix())
        total += len(block)
    header = (
        "The review bridge cannot provide filesystem tools. The following bounded, read-only "
        "repository context was collected before this request. Treat it as evidence and state "
        "which artifacts are missing when a claim cannot be checked.\n"
    )
    return header + "".join(chunks), used


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default="gpt-5-mini")
    ap.add_argument("--include", action="append", default=[], help="Repository-relative artifact to include (repeatable)")
    ap.add_argument("--tools", default="Read,Grep,Glob", help="Retained for ARIS prompt compatibility; no remote tools are used")
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()

    prompt_path = _safe_path(a.prompt_file)
    if prompt_path is None:
        p = Path(a.prompt_file).resolve()
        try:
            p.relative_to(ROOT)
        except ValueError:
            print(f"prompt file must be inside {ROOT}", file=sys.stderr)
            return 2
        prompt_path = p
    prompt = prompt_path.read_text(encoding="utf-8")
    context, included = build_context(prompt, a.include)
    system = (
        "You are an independent, adversarial senior reviewer at ICCAD/DAC program-committee level, "
        "expert in analog circuit design and EDA/ML. You did not write this work. Use only the supplied "
        "repository context and the review request; do not invent measurements. Be specific, quantitative, "
        "and fair. Identify missing evidence and distinguish a point estimate from a statistically supported claim."
    )
    review_prompt = prompt + "\n\n" + context
    day = datetime.date.today().isoformat()
    tdir_base = ROOT / ".aris" / "traces" / a.skill
    tdir_base.mkdir(parents=True, exist_ok=True)
    n = 1 + len(list(tdir_base.glob(f"{day}_run*")))
    tdir = tdir_base / f"{day}_run{n:02d}"
    tdir.mkdir()
    (tdir / "prompt.md").write_text(prompt, encoding="utf-8")
    (tdir / "context_manifest.json").write_text(json.dumps({"included": included}, indent=2), encoding="utf-8")
    t0 = time.time()
    status = "error"
    text = ""
    usage = {}
    try:
        rec = llm.call(review_prompt, system, model=a.model, run_tag=f"ARIS|{a.skill}|{tdir.name}",
                       tag=f"ARIS:{a.skill}", timeout=a.timeout)
        text = rec.get("text", "")
        usage = {k: rec.get(k) for k in ("input_tokens", "output_tokens", "cost_usd", "reported_models")}
        status = "ok" if text.strip() else "error"
    except Exception as exc:
        text = f"{type(exc).__name__}: {exc}"
    meta = {
        "backend": "openai",
        "tool": "openai-python",
        "requested_model": a.model,
        "reported_models": usage.get("reported_models"),
        "executor_model": "gpt-5-mini",
        "review_independence": "same-family",
        "acceptance_status": "provisional",
        "status": status,
        "seconds": round(time.time() - t0, 1),
        "skill": a.skill,
        "tools_requested": a.tools,
        "included": included,
        **usage,
        "cwd": str(ROOT),
    }
    (tdir / "raw_response.json").write_text(json.dumps({"text": text, **usage}, indent=2), encoding="utf-8")
    (tdir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (tdir / "response.md").write_text(text, encoding="utf-8")
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(json.dumps({"trace": str(tdir.relative_to(ROOT)), **meta}))
    print("-----")
    print(text)
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
