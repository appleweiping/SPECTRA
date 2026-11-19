#!/usr/bin/env python3
"""Run a config-driven public sizing task on the remote simulator.

This adapter targets source-native benchmark repositories that expose a
parameterized SPICE netlist and JSON config, such as
``opensource-analog-circuits``.  It keeps the search budget, method rows,
PVT verifier and metric parser in one auditable schema.  The script does not
download PDKs or invoke a simulator during import.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from spectra.bench.cross_domain import make_pvt_grid


def parse_spice_number(raw: str) -> float:
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([unpKMGkmun]?)", raw.strip())
    if not match:
        raise ValueError(raw)
    return float(match.group(1)) * {
        "": 1.0, "n": 1e-9, "p": 1e-12, "u": 1e-6, "m": 1e-3,
        "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
    }[match.group(2)]


def read_config(config_path: Path) -> tuple[dict[str, Any], Path]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    circuit = Path(str(config["circuit_file"]))
    if not circuit.is_absolute():
        circuit = (config_path.parent.parent.parent / circuit).resolve()
    if not circuit.exists():
        raise FileNotFoundError(circuit)
    return config, circuit


def parse_param_suffix(text: str, name: str) -> str:
    pattern = rf"\b{re.escape(name)}\s*=\s*[-+0-9.eE]+([unpKMGkmun]?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def inject_params(source: str, values: dict[str, float], names: list[str]) -> str:
    output = source
    for name in names:
        suffix = parse_param_suffix(source, name)
        number = f"{values[name]:.12g}"
        pattern = rf"(\b{re.escape(name)}\s*=\s*)[-+0-9.eE]+[unpKMGkmun]?"
        output, count = re.subn(pattern, rf"\g<1>{number}{suffix}", output, count=1, flags=re.IGNORECASE)
        if count != 1:
            raise ValueError(f"design variable {name!r} is not present in a .param line")
    return output


def inject_condition(text: str, corner: str, temperature: float, supply: float, nominal_supply: float) -> str:
    text, replaced = re.subn(
        r"(\.lib\s+[^\s]+\s+)(tt|ff|ss|sf|fs)(\s*)$",
        rf"\g<1>{corner}\g<3>",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if replaced == 0 and corner != "tt":
        raise ValueError("netlist has no .lib corner selector for PVT replacement")
    nominal_text = f"{nominal_supply:g}"
    text = re.sub(rf"(\bdc\s*[=]?\s*){re.escape(nominal_text)}(?=\s|$)",
                  rf"\g<1>{supply:g}", text, flags=re.IGNORECASE)
    if not re.search(r"^\s*\.temp\s", text, flags=re.IGNORECASE | re.MULTILINE):
        text = f".temp {temperature:g}\n" + text
    else:
        text = re.sub(r"^\s*\.temp\s+[-+0-9.eE]+", f".temp {temperature:g}", text,
                      count=1, flags=re.IGNORECASE | re.MULTILINE)
    return text


def parse_metrics(log_text: str, config: dict[str, Any]) -> dict[str, float]:
    parser_type = config.get("metrics_parser_type", "regex")
    patterns = config.get("metrics_patterns", {})
    metrics: dict[str, float] = {}
    for line in log_text.splitlines():
        for name, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                try:
                    metrics[name] = float(match.group(1))
                except (IndexError, ValueError):
                    pass
    if parser_type in {"ac_data", "multi_tb_meas"}:
        for name in config.get("specs", {}):
            match = re.search(rf"\b{re.escape(name)}\s*=\s*([-+0-9.eE]+)", log_text, flags=re.IGNORECASE)
            if match:
                try:
                    metrics[name] = float(match.group(1))
                except ValueError:
                    pass
    return metrics


def violation(metrics: dict[str, float], specs: dict[str, Any]) -> float:
    residuals: list[float] = []
    for name, spec in specs.items():
        value = metrics.get(name)
        if value is None or not math.isfinite(float(value)):
            residuals.append(1.0)
            continue
        op, target = spec[0], float(spec[1])
        residual = float(value) - target if op == "<" else target - float(value)
        residuals.append(max(0.0, residual) / max(abs(target), 1.0))
    return float(sum(residuals) / max(1, len(residuals)))


def run_netlist(simulator: str, netlist: Path, cwd: Path, timeout: int = 180) -> tuple[dict[str, float], int | None, float, str]:
    started = time.perf_counter()
    try:
        proc = subprocess.run([simulator, "-b", str(netlist)], cwd=str(cwd), capture_output=True,
                              text=True, timeout=timeout)
        return {}, proc.returncode, time.perf_counter() - started, proc.stdout + "\n" + proc.stderr
    except (OSError, subprocess.SubprocessError) as exc:
        return {}, None, time.perf_counter() - started, f"{type(exc).__name__}: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--simulator", required=True)
    parser.add_argument("--track-id", default="opensource_public")
    parser.add_argument("--pdk", default="source_defined")
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--methods", default="spectra,anaflow_cleanroom")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nominal-supply", type=float, default=1.8)
    args = parser.parse_args()
    config, circuit = read_config(args.config.resolve())
    source_text = circuit.read_text(encoding="utf-8")
    names = list(config.get("design_vars", {}))
    bounds = np.asarray([[float(config["design_vars"][name][1]), float(config["design_vars"][name][2])] for name in names])
    defaults = np.asarray([float(config["design_vars"][name][0]) for name in names])
    specs = config.get("specs", {})
    pvt = make_pvt_grid()
    methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    rows: list[dict[str, Any]] = []
    root = args.output.resolve().parent / f"_{args.output.stem}_work"
    for seed in (int(item) for item in args.seeds.split(",") if item.strip()):
        for method in methods:
            run_dir = root / f"s{seed}_{method}"
            run_dir.mkdir(parents=True, exist_ok=True)
            started = time.perf_counter()
            rng = np.random.default_rng(seed)
            best = defaults.copy()
            best_score = float("inf")
            first_pass = None
            evaluations = 0

            def evaluate(values: np.ndarray, condition_name: str = "tt_27C_1.8V") -> float:
                nonlocal best, best_score, first_pass, evaluations
                condition = next(item for item in pvt if item.name == condition_name)
                text = inject_condition(inject_params(source_text, dict(zip(names, values.tolist())), names),
                                        condition.corner, condition.temperature_c, condition.supply_v,
                                        args.nominal_supply)
                netlist = run_dir / "candidate.cir"
                netlist.write_text(text, encoding="utf-8")
                _, returncode, _, log = run_netlist(args.simulator, netlist, circuit.parent)
                metrics = parse_metrics(log, config) if returncode == 0 else {}
                score = violation(metrics, specs)
                evaluations += 1
                if score < best_score:
                    best_score = score
                    best = np.asarray(values, dtype=float).copy()
                if first_pass is None and score == 0.0:
                    first_pass = evaluations
                return score

            if method == "spectra":
                import cma
                coverage = min(max(8, 2 * len(names)), max(1, args.budget // 3))
                for unit in rng.random((coverage, len(names))):
                    evaluate(bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0]))
                es = cma.CMAEvolutionStrategy([0.5] * len(names), 0.25,
                                               {"bounds": [0, 1], "seed": seed + 9000, "verbose": -9})
                while evaluations < args.budget:
                    points = es.ask()[:args.budget - evaluations]
                    scores = [evaluate(bounds[:, 0] + np.clip(point, 0.0, 1.0) * (bounds[:, 1] - bounds[:, 0]))
                              for point in points]
                    if len(scores) >= getattr(es.sp, "mu", 2):
                        es.tell(points[:len(scores)], scores)
            else:
                for _ in range(args.budget):
                    evaluate(bounds[:, 0] + rng.random(len(names)) * (bounds[:, 1] - bounds[:, 0]))
            values = best
            condition_rows: list[dict[str, Any]] = []
            for condition in pvt:
                try:
                    text = inject_condition(inject_params(source_text, dict(zip(names, values.tolist())), names),
                                            condition.corner, condition.temperature_c, condition.supply_v,
                                            args.nominal_supply)
                except ValueError as exc:
                    condition_rows.append({"condition": condition.name, "metrics": {},
                                           "normalized_violation": 1.0, "pass": False,
                                           "missing_metrics": sorted(set(specs) | {"condition_error"}),
                                           "error": str(exc)})
                    continue
                netlist = run_dir / f"verify_{condition.name}.cir"
                netlist.write_text(text, encoding="utf-8")
                _, returncode, _, log = run_netlist(args.simulator, netlist, circuit.parent)
                metrics = parse_metrics(log, config) if returncode == 0 else {}
                score = violation(metrics, specs)
                condition_rows.append({"condition": condition.name, "metrics": metrics,
                                       "normalized_violation": score, "pass": score == 0.0,
                                       "missing_metrics": sorted(set(specs).difference(metrics))})
            finite = [float(item["normalized_violation"]) for item in condition_rows if math.isfinite(item["normalized_violation"])]
            pvt_summary = {"conditions_observed": len(condition_rows), "pvt_success": bool(condition_rows) and all(item["pass"] for item in condition_rows),
                           "mean_normalized_violation": float(sum(finite) / len(finite)) if len(finite) == len(condition_rows) else float("inf"),
                           "median_normalized_violation": float(np.median(finite)) if len(finite) == len(condition_rows) else float("inf"),
                           "conditions": condition_rows}
            rows.append({"track_id": args.track_id, "task": config["name"], "method": method, "seed": seed,
                         "pdk": args.pdk, "simulator": Path(args.simulator).name, "simulations": args.budget,
                         "llm_calls": 12, "first_pass_simulations": first_pass, "tt_violation": best_score,
                         "tt_pass": best_score == 0.0, "pvt": pvt_summary,
                         "parameters": dict(zip(names, values.tolist())),
                         "source": str(circuit), "wall_seconds": time.perf_counter() - started})
    payload = {"schema": "spectra-public-config-pvt/v1", "model": "gpt-6.1-sol", "budget": args.budget,
               "llm_calls": 12, "pvt_conditions": len(pvt), "rows": rows, "ranking_eligible": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
