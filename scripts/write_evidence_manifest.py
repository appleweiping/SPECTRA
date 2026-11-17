"""Write an auditable manifest for one GPT experiment chain.

The manifest follows the same boundary used by Analog Canvas: authored benchmark
facts and experiment inputs are immutable evidence, while simulator outputs and
paper products are derived artifacts.  It never reads or records API secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from spectra.paths import ROOT


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def command(*args: str) -> str | None:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_state() -> dict[str, object]:
    return {
        "commit": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "status_porcelain": command("git", "status", "--short") or "",
    }


def task_facts() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    bench = ROOT / "data" / "bench"
    for path in sorted(bench.glob("*.jsonl")):
        out.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return out


def run_files(experiments: list[str]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    raw = ROOT / "results" / "raw"
    for exp in experiments:
        base = raw / exp
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            rel = path.relative_to(ROOT).as_posix()
            record: dict[str, object] = {
                "experiment": exp,
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    for key in ("method", "model", "seed", "status", "task_id", "calls", "simulations"):
                        if key in payload:
                            record[key] = payload[key]
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                record["parse_error"] = True
            out.append(record)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default="results/evidence_manifest.json")
    ap.add_argument("--experiments", default="E1g,E2g,E3g,E4g,E5g")
    ap.add_argument("--model", default=os.environ.get("SPECTRA_MODEL", "gpt-6.1-sol"))
    args = ap.parse_args()

    experiments = [x.strip() for x in args.experiments.split(",") if x.strip()]
    files = run_files(experiments)
    statuses: dict[str, int] = {}
    models: set[str] = set()
    for item in files:
        status = item.get("status")
        if isinstance(status, str):
            statuses[status] = statuses.get(status, 0) + 1
        model = item.get("model")
        if isinstance(model, str):
            models.add(model)

    manifest = {
        "schema": "spectra-evidence-manifest/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "requested_model": args.model,
        "observed_models": sorted(models),
        "experiments": experiments,
        "git": git_state(),
        "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "simulator": command(os.environ.get("SPECTRA_NGSPICE", "ngspice"), "-v"),
        "benchmark_inputs": task_facts(),
        "raw_runs": {"count": len(files), "status_counts": statuses, "files": files},
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output.relative_to(ROOT)} ({len(files)} raw JSON files)")


if __name__ == "__main__":
    main()
