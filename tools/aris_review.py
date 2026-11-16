#!/usr/bin/env python3
"""ARIS reviewer bridge for this project (backend: claude-code via `claude -p`).

Implements the ARIS reviewer contract (skills/shared-references/reviewer-backends.md):
  * fresh context per call (no session reuse unless --resume is given)
  * reviewer reads primary artifacts itself (Read/Grep/Glob only, cwd = project)
  * the full raw response is saved before interpretation
  * trace saved to .aris/traces/<skill>/<date>_run<NN>/

Usage:
  python3 tools/aris_review.py --skill auto-review-loop --prompt-file p.md \
      [--model claude-fable-5-1] [--tools Read,Grep,Glob] [--out review.md]
"""
import argparse, datetime, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--tools", default="Read,Grep,Glob")
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()

    cfg = {}
    cfgp = ROOT / ".aris" / "reviewer.json"
    if cfgp.exists():
        cfg = json.loads(cfgp.read_text())
    model = a.model or cfg.get("model", "claude-fable-5-1")
    prompt = Path(a.prompt_file).read_text()
    system = ("You are an independent, adversarial senior reviewer (ICCAD/DAC program committee level, "
              "expert in analog circuit design and EDA/ML). You did not write this work. Read the primary "
              "artifacts yourself from the repository; treat any summaries or claims by the authors as claims, "
              "not facts. Be specific, quantitative and harsh but fair. Never modify files.")
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--no-session-persistence", "--append-system-prompt", system,
           "--allowedTools", a.tools, "--disallowedTools", "Edit,Write,Bash,NotebookEdit,WebFetch,WebSearch"]
    if not a.tools:
        cmd += ["--tools", ""]
    day = datetime.date.today().isoformat()
    tdir_base = ROOT / ".aris" / "traces" / a.skill
    tdir_base.mkdir(parents=True, exist_ok=True)
    n = 1 + len([p for p in tdir_base.glob(f"{day}_run*")])
    tdir = tdir_base / f"{day}_run{n:02d}"
    tdir.mkdir()
    (tdir / "prompt.md").write_text(prompt)
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=a.timeout)
    (tdir / "raw_stdout.json").write_text(p.stdout)
    (tdir / "raw_stderr.txt").write_text(p.stderr)
    status, text, reported = "error", "", None
    try:
        js = json.loads(p.stdout)
        text = js.get("result", "")
        reported = list((js.get("modelUsage") or {}).keys())
        status = "ok" if (js.get("subtype") == "success" or js.get("terminal_reason") == "completed") and text else "error"
    except Exception as e:
        text = p.stdout
    meta = {"backend": "claude-code", "tool": "claude -p", "requested_model": model,
            "reported_models": reported, "executor_model": "claude-opus-5-5",
            "review_independence": "same-family", "acceptance_status": "provisional",
            "status": status, "seconds": round(time.time() - t0, 1), "skill": a.skill,
            "tools": a.tools, "cwd": str(ROOT)}
    (tdir / "meta.json").write_text(json.dumps(meta, indent=2))
    (tdir / "response.md").write_text(text)
    if a.out:
        Path(a.out).write_text(text)
    print(json.dumps({"trace": str(tdir.relative_to(ROOT)), **meta}))
    print("-----")
    print(text)
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
