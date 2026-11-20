#!/usr/bin/env python3
"""Run one reproducible AnalogPortBench source-native evaluator smoke.

This adapter deliberately executes the public AnalogPortBench evaluator rather
than manufacturing a transfer score.  By default it evaluates a bundled
golden SKY130 netlist so that the PDK, simulator and metric parser are tested.
The receipt always marks the run as ranking-ineligible because a golden
reference is not a SPECTRA answer and AnalogPortBench does not define a
matched SIZ7g/AnaFlow transfer protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def simulator_version(executable: Path) -> str | None:
    try:
        completed = subprocess.run(
            [str(executable), "-v"], capture_output=True, text=True,
            check=False, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return text.splitlines()[0] if text else None


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    root = args.source_root.resolve()
    evaluator = root / "benchmark" / "evaluate.py"
    if not evaluator.is_file():
        raise FileNotFoundError(f"AnalogPortBench evaluator not found: {evaluator}")

    netlist = (args.netlist or root / "benchmark" / "golden" / f"{args.golden_name}.sp").resolve()
    if not netlist.is_file():
        raise FileNotFoundError(f"Smoke netlist not found: {netlist}")

    label = args.label or f"spectra_source_smoke_{args.corner}"
    python = args.python.resolve()
    simulator = args.ngspice.resolve()
    env = os.environ.copy()
    env["PDK_ROOT"] = str(args.pdk_root.resolve())
    env["NGSPICE"] = str(simulator)
    command = [
        str(python), str(evaluator), args.circuit, str(netlist),
        "--tech", args.tech, "--vdd", str(args.vdd),
        "--corner", args.corner, "--label", label,
    ]
    completed = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True,
        check=False, timeout=args.timeout,
    )
    result_path = root / "build" / "eval" / args.circuit / label / "result.json"
    result: dict[str, Any] | None = None
    if result_path.is_file():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result = None

    status = "completed" if completed.returncode == 0 and result and result.get("pass") else "failed"
    return {
        "schema": "analog-port-bench/source-native-smoke/v1",
        "status": status,
        "smoke_type": "source_native_evaluator",
        "source_root": str(root),
        "source_commit": git_commit(root),
        "evaluator": str(evaluator),
        "simulator": {
            "path": str(simulator),
            "version": simulator_version(simulator),
        },
        "pdk_root": str(args.pdk_root.resolve()),
        "task": {
            "circuit": args.circuit,
            "golden_name": args.golden_name if args.netlist is None else None,
            "tech": args.tech,
            "vdd": args.vdd,
            "corner": args.corner,
            "label": label,
        },
        "netlist": {
            "path": str(netlist),
            "sha256": sha256(netlist),
            "provenance": "source_golden_reference" if args.netlist is None else "caller_supplied_candidate",
        },
        "command": command,
        "returncode": completed.returncode,
        "timeout_seconds": args.timeout,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "result_path": str(result_path),
        "result": result,
        "ranking_eligible": False,
        "ranking_blocker": (
            "This source-native smoke has no SPECTRA transfer answer, matched AnaFlow answer, "
            "or common SIZ7g budget. It is evaluator/PDK integrity evidence only."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--pdk-root", type=Path, required=True)
    parser.add_argument("--ngspice", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--circuit", default="ota_tele")
    parser.add_argument("--golden-name", default="ota_tele_1v8")
    parser.add_argument("--netlist", type=Path)
    parser.add_argument("--tech", default="sky130_lvt")
    parser.add_argument("--vdd", type=float, default=1.8)
    parser.add_argument("--corner", default="tt")
    parser.add_argument("--label")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_smoke(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "ranking_eligible", "source_commit")}))
    raise SystemExit(0 if receipt["status"] == "completed" else 1)


if __name__ == "__main__":
    main()
