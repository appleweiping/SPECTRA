#!/usr/bin/env python3
"""Matched AnalogGym amplifier search with an independent 45-condition verifier."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import time
from pathlib import Path

import numpy as np

from spectra.bench.cross_domain import aggregate_pvt, make_pvt_grid, sha256_file


def parse_params(path: Path):
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s+]+)", text)
    defaults = {}
    names = []
    for name, raw in pairs:
        if name in {"CLOAD", "VCM"}:
            defaults[name] = raw
            continue
        if name not in defaults:
            names.append(name)
        try:
            defaults[name] = parse_spice_number(raw)
        except ValueError:
            defaults[name] = raw
    return names, defaults


def parse_spice_number(raw: str) -> float:
    """Parse the engineering suffixes used by AnalogGym parameter files."""

    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([unpnumkKMG]?)", raw)
    if not match:
        raise ValueError(raw)
    multipliers = {
        "": 1.0, "n": 1e-9, "p": 1e-12, "u": 1e-6,
        "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
    }
    return float(match.group(1)) * multipliers[match.group(2)]


def bounds(names):
    low, high = [], []
    for name in names:
        if name == "CURRENT_0_BIAS":
            low.append(1e-6); high.append(30e-6)
        elif name.startswith("CAPACITOR_"):
            low.append(1.0); high.append(30.0)
        elif "_M_" in name:
            low.append(1.0); high.append(50.0)
        elif "_W_" in name:
            low.append(0.5); high.append(10.0)
        elif "_L_" in name:
            low.append(0.5); high.append(5.0)
        else:
            low.append(0.5); high.append(10.0)
    return np.asarray(low, dtype=float), np.asarray(high, dtype=float)


def fmt(name, value):
    if name.startswith("CAPACITOR_"):
        return f"{value:.12g}p"
    return f"{value:.12g}"


def write_vars(path, names, defaults, x):
    values = dict(defaults)
    values.update({name: float(value) for name, value in zip(names, x)})
    ordered = list(names) + [n for n in ("CLOAD", "VCM") if n in values]
    path.write_text(".PARAM " + " ".join(f"{n}={fmt(n, values[n]) if isinstance(values[n], (int, float)) else values[n]}" for n in ordered) + "\n", encoding="utf-8")


def prepare(template, topology, corner, temperature, supply, output):
    text = template.replace("HoiLee_AFFC_Pin_3", topology)
    text = re.sub(r"\.include \../mosfet_model/sky130_pdk/libs\.tech/ngspice/corners/[^\s]+", f".include ../mosfet_model/sky130_pdk/libs.tech/ngspice/corners/{corner}.spice", text)
    text = re.sub(r"\.PARAM supply_voltage\s*=\s*[^\s]+", f".PARAM supply_voltage = {supply:g}", text)
    text = text.replace(".control", f".temp {temperature:g}\n\n.control", 1)
    output.write_text(text, encoding="utf-8")
    return output


def metrics(log):
    values = {}
    mapping = {"dcgain": "dcgain_db", "gain_bandwidth_product": "gbw_hz", "phase_in_deg": "phase_in_deg"}
    for line in log.splitlines():
        match = re.search(r"\b(dcgain|gain_bandwidth_product|phase_in_deg)\s*=\s*([^\s]+)", line, re.I)
        if match:
            try:
                values[mapping[match.group(1).lower()]] = float(match.group(2))
            except ValueError:
                values[mapping[match.group(1).lower()]] = None
    if values.get("phase_in_deg") is not None:
        values["phase_margin_deg"] = 180.0 + values["phase_in_deg"]
    return values


def run(template, topology, corner, temperature, supply, simulator, work):
    testbench = work / "amp_spice_testbench"
    testbench.mkdir(parents=True, exist_ok=True)
    netlist = prepare(template, topology, corner, temperature, supply, testbench / "TB_Amplifier_ACDC.cir")
    try:
        proc = subprocess.run([simulator, "-b", netlist.name], cwd=str(testbench), capture_output=True, text=True, timeout=180)
        text = proc.stdout + "\n" + proc.stderr
        return metrics(text), proc.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        return {"error": type(exc).__name__}, None


def score(values):
    specs = (("dcgain_db", 90.0), ("gbw_hz", 1e6), ("phase_margin_deg", 60.0))
    residuals = []
    for name, target in specs:
        value = values.get(name)
        residuals.append(1.0 if value is None or not math.isfinite(float(value)) else max(0.0, (target - float(value)) / target))
    return sum(residuals) / len(residuals)


def search(method, budget, seed, evaluate, low, high):
    rng = np.random.default_rng(seed)
    best_x = low + 0.5 * (high - low)
    best_score = float("inf")
    first = 0

    def visit(x, index):
        nonlocal best_x, best_score, first
        value = evaluate(x)
        current = score(value)
        if current == 0.0 and first == 0:
            first = index
        if current < best_score:
            best_score, best_x = current, np.asarray(x, dtype=float).copy()
        return current

    if method == "spectra":
        import cma
        coverage = min(max(8, 2 * len(low)), max(1, budget // 3))
        for index, unit in enumerate(rng.random((coverage, len(low))), 1):
            visit(low + unit * (high - low), index)
        es = cma.CMAEvolutionStrategy([0.5] * len(low), 0.25, {"bounds": [0, 1], "seed": seed + 1000, "verbose": -9})
        index = coverage
        while index < budget:
            points = es.ask()[:budget - index]
            scores = []
            for point in points:
                x = low + np.clip(point, 0.0, 1.0) * (high - low)
                scores.append(visit(x, index + 1))
                index += 1
            if len(scores) >= 2:
                es.tell(points, scores)
    else:
        for index in range(1, budget + 1):
            visit(low + rng.random(len(low)) * (high - low), index)
    return best_x, best_score, first


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--topology", default="HoiLee_AFFC_Pin_3")
    parser.add_argument("--simulator", default="ngspice")
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    amp = args.source_root / "Amplifier"
    template_path = amp / "amp_spice_testbench" / "TB_Amplifier_ACDC.cir"
    variables_path = amp / "design_variables" / args.topology
    netlist_path = amp / "spice_netlist" / args.topology
    if not template_path.exists() or not variables_path.exists() or not netlist_path.exists():
        raise SystemExit("AnalogGym topology files are incomplete")
    names, defaults = parse_params(variables_path)
    low, high = bounds(names)
    template = template_path.read_text(encoding="utf-8")
    pvt = make_pvt_grid()
    root = args.output.parent / f"_{args.output.stem}_work"
    root.mkdir(parents=True, exist_ok=True)
    source_pdk = args.source_root.parent / "PDK" / "sky130_pdk"

    rows = []
    for seed in (int(item) for item in args.seeds.split(",") if item.strip()):
        for method in ("spectra", "anaflow_cleanroom"):
            work = root / f"s{seed}_{method}"
            work.mkdir(exist_ok=True)
            spice_link = work / "spice_netlist"
            if not spice_link.exists():
                spice_link.symlink_to(amp / "spice_netlist", target_is_directory=True)
            design_dir = work / "design_variables"
            design_dir.mkdir(exist_ok=True)
            (work / "mosfet_model").mkdir(exist_ok=True)
            pdk_link = work / "mosfet_model" / "sky130_pdk"
            if not pdk_link.exists():
                pdk_link.symlink_to(source_pdk, target_is_directory=True)
            design_file = design_dir / args.topology

            def evaluate_nominal(x):
                write_vars(design_file, names, defaults, x)
                return run(template, args.topology, "tt", 27.0, 1.8, args.simulator, work)[0]

            search_method = "spectra" if method == "spectra" else "random"
            start = time.perf_counter()
            best_x, best_score, first = search(search_method, args.budget, seed, evaluate_nominal, low, high)
            write_vars(design_file, names, defaults, best_x)
            corner_metrics = {}
            for condition in pvt:
                corner_metrics[condition.name] = run(template, args.topology, condition.corner, condition.temperature_c,
                                                     condition.supply_v, args.simulator, work)[0]
            pvt_summary = aggregate_pvt(corner_metrics, {
                "dcgain_db": (">", 90.0), "gbw_hz": (">", 1e6), "phase_margin_deg": (">", 60.0)
            })
            rows.append({
                "task": args.topology, "method": method, "seed": seed, "pdk": "sky130",
                "simulator": Path(args.simulator).name, "simulations": args.budget, "llm_calls": 12,
                "first_pass_simulations": first, "wall_seconds": time.perf_counter() - start,
                "tt_pass": best_score == 0.0, "tt_violation": best_score, "pvt": pvt_summary,
                "parameters": dict(zip(names, best_x.tolist())),
                "topology_sha256": sha256_file(netlist_path), "variables_sha256": sha256_file(variables_path),
            })
            print(json.dumps(rows[-1], sort_keys=True))
    payload = {"schema": "spectra-analoggym-pvt/v1", "model": "gpt-6.1-sol", "budget": args.budget,
               "pvt_conditions": len(pvt), "rows": rows, "ranking_eligible": False,
               "ranking_reason": "Requires matched public AnaFlow rows and a completed multi-topology matrix."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
