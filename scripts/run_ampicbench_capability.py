#!/usr/bin/env python3
"""Run the shipped AMPICBench decks as a server-side capability receipt.

AMPICBench provides source-native ngspice decks and corner operating-region
files, but it does not expose one parameterized sizing API.  This runner keeps
the capability check separate from matched SPECTRA ranking and records every
deck's simulator status and error tail.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--simulator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--pvt", action="store_true", help="replay source corners.json conditions")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    decks = sorted(source_root.glob("Bias_Circuits/*/*.cir"))
    decks.extend(sorted(source_root.glob("Opamps/*/*.cir")))
    if not decks:
        raise SystemExit(f"no AMPICBench decks found under {source_root}")

    results: list[dict] = []
    for deck in decks:
        corner_file = deck.parent / "corners.json"
        corners = json.loads(corner_file.read_text(encoding="utf-8")) if args.pvt and corner_file.exists() else {"tt_27": {}}
        condition_rows: list[dict] = []
        work_root = args.output.resolve().parent / "_ampicbench_capability_work" / deck.parent.name
        work_root.mkdir(parents=True, exist_ok=True)
        for condition in sorted(corners):
            match = re.fullmatch(r"(tt|ff|ss|sf|fs)_(-?\d+)", condition)
            if match:
                corner, temperature = match.group(1), float(match.group(2))
            else:
                corner, temperature = "tt", 27.0
            text = deck.read_text(encoding="utf-8")
            text, replaced = re.subn(r"(\.lib\s+[^\s]+\s+)(tt|ff|ss|sf|fs)(\s*)$",
                                     rf"\g<1>{corner}\g<3>", text,
                                     flags=re.IGNORECASE | re.MULTILINE)
            if replaced == 0 and corner != "tt":
                condition_rows.append({"condition": condition, "returncode": None,
                                       "error": "missing .lib corner selector", "metrics_lines": []})
                continue
            text = re.sub(r"^\s*\.temp\s+[-+0-9.eE]+", f".temp {temperature:g}", text,
                          count=1, flags=re.IGNORECASE | re.MULTILINE)
            if not re.search(r"^\s*\.temp\s", text, flags=re.IGNORECASE | re.MULTILINE):
                text = f".temp {temperature:g}\n" + text
            netlist = work_root / f"{deck.stem}_{condition}.cir"
            netlist.write_text(text, encoding="utf-8")
            started = time.perf_counter()
            try:
                completed = subprocess.run([str(args.simulator), "-b", netlist.name], cwd=str(work_root),
                                           capture_output=True, text=True, timeout=args.timeout)
                output = completed.stdout + "\n" + completed.stderr
                parsed = [line for line in output.splitlines() if re.search(r"=\s*[-+0-9.eE]+", line)]
                artifact_metrics: list[str] = []
                for artifact_name in ("stb_meas.txt", "op_nodes.txt", "op_devices.txt"):
                    artifact = work_root / artifact_name
                    if artifact.exists():
                        try:
                            artifact_metrics.extend(
                                line for line in artifact.read_text(encoding="utf-8", errors="replace").splitlines()
                                if re.search(r"=\s*[-+0-9.eE]+", line)
                            )
                        except OSError:
                            pass
                condition_rows.append({"condition": condition, "returncode": completed.returncode,
                                       "elapsed": time.perf_counter() - started,
                                       "fatal": "fatal error" in output.lower(),
                                       "metrics_lines": (parsed + artifact_metrics)[-40:],
                                       "error_tail": output.splitlines()[-12:]})
            except (OSError, subprocess.SubprocessError) as exc:
                condition_rows.append({"condition": condition, "error": f"{type(exc).__name__}: {exc}",
                                       "elapsed": time.perf_counter() - started, "metrics_lines": []})
        results.append({"deck": str(deck.relative_to(source_root)), "conditions": condition_rows,
                        "conditions_observed": len(condition_rows),
                        "complete": bool(condition_rows) and all(row.get("returncode") == 0 and not row.get("fatal") for row in condition_rows),
                        "simulations": len(condition_rows)})

    payload = {
        "schema": "ampicbench-capability/v2",
        "source_root": str(source_root),
        "simulator": str(args.simulator.resolve()),
        "count": len(results), "pvt": bool(args.pvt),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failures = [row for row in results if not row.get("complete")]
    print(json.dumps({"count": len(results), "successful": len(results) - len(failures), "failures": len(failures)}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
