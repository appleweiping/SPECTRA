#!/usr/bin/env python3
"""Run an auditable Xyce AC-translation probe over SGAnalog task decks.

This is a simulator-compatibility harness.  It deliberately does not score a
model or convert source-deck execution into a SIZ7g ranking cell.  Every task
keeps its source and translated-deck hashes, return code, timeout state, log
digest, and parsed AC aliases when Xyce emits a response table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def resolve_deck(root: Path, task: dict[str, Any]) -> Path:
    rel = Path(str(task["tb_cir"]))
    marker = "out/sim_ui/netlists/"
    if marker in rel.as_posix():
        rel = Path(rel.as_posix().replace(marker, "circuits/", 1))
    return (root / rel).resolve()


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "task"


def git_commit(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def run_probe(deck: Path, translated: Path, xyce: Path, work: Path, timeout: int) -> dict[str, Any]:
    from xyce_ac_translator import parse_artifacts, translate_ac_netlist

    source = deck.read_text(encoding="utf-8", errors="replace")
    translated_text = translate_ac_netlist(source)
    translated.write_text(translated_text, encoding="utf-8")
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [str(xyce), "-b", translated.name],
            cwd=str(work), capture_output=True, text=True, timeout=timeout,
            env=dict(os.environ),
        )
        log = (proc.stdout or "") + "\n" + (proc.stderr or "")
        metrics = parse_artifacts(translated)
        return {
            "status": "ok" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "seconds": round(time.perf_counter() - started, 4),
            "log_sha256": sha256_bytes(log.encode()),
            "log_tail": log[-2000:],
            "translated_sha256": sha256_file(translated),
            "metrics": metrics,
        }
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return {
            "status": "timeout", "returncode": None,
            "seconds": round(time.perf_counter() - started, 4),
            "log_sha256": sha256_bytes(log.encode()), "log_tail": log[-2000:],
            "translated_sha256": sha256_file(translated), "metrics": {},
        }
    except OSError as exc:
        return {
            "status": "exec_error", "returncode": None,
            "seconds": round(time.perf_counter() - started, 4),
            "error": repr(exc), "translated_sha256": sha256_file(translated),
            "metrics": {},
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sg-root", type=Path, required=True)
    parser.add_argument("--xyce", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    root = args.sg_root.resolve()
    tasks = [json.loads(line) for line in (root / "eval/sizing/tasks.jsonl").read_text().splitlines() if line.strip()]
    if args.limit is not None:
        tasks = tasks[: args.limit]
    args.work_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["task_id"])
        deck = resolve_deck(root, task)
        work = args.work_root / safe_id(task_id)
        work.mkdir(parents=True, exist_ok=True)
        translated = work / f"{safe_id(task_id)}.xyce.cir"
        row: dict[str, Any] = {
            "task_id": task_id, "dut": task.get("dut"),
            "deck_relpath": str(deck.relative_to(root)) if deck.is_relative_to(root) else str(deck),
            "deck_exists": deck.is_file(),
            "deck_sha256": sha256_file(deck) if deck.is_file() else None,
        }
        if deck.is_file():
            row["probe"] = run_probe(deck, translated, args.xyce.resolve(), work, args.timeout)
        else:
            row["probe"] = {"status": "missing_deck", "metrics": {}}
        rows.append(row)
        print(json.dumps({"task_id": task_id, "status": row["probe"]["status"]}, sort_keys=True), flush=True)

    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["probe"]["status"])
        counts[status] = counts.get(status, 0) + 1
    receipt = {
        "schema": "sganalog-xyce-ac-probe/v1",
        "benchmark": "SGAnalog",
        "source_commit": git_commit(root),
        "xyce": str(args.xyce.resolve()),
        "task_count": len(rows), "status_counts": dict(sorted(counts.items())),
        "tasks": rows,
        "ranking_eligible": False,
        "boundary": "Xyce AC translator compatibility probe only; no SIZ7g score, model ranking, or universal SOTA claim",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"task_count": len(rows), "status_counts": receipt["status_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
