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


def ensure_symlink(link: Path, target: Path, *, directory: bool = False) -> None:
    """Create a link and repair a stale link left by an interrupted run."""

    if link.is_symlink() and not link.exists():
        link.unlink()
    if not link.exists():
        link.symlink_to(target, target_is_directory=directory)


def prepare(template, topology, corner, temperature, supply, output):
    text = template.replace("HoiLee_AFFC_Pin_3", topology)
    text = re.sub(r"\.include \../mosfet_model/sky130_pdk/libs\.tech/ngspice/corners/[^\s]+", f".include ../mosfet_model/sky130_pdk/libs.tech/ngspice/corners/{corner}.spice", text)
    text = re.sub(r"\.PARAM supply_voltage\s*=\s*[^\s]+", f".PARAM supply_voltage = {supply:g}", text)
    text = text.replace(".control", f".temp {temperature:g}\n\n.control", 1)
    output.write_text(text, encoding="utf-8")
    return output


def prepare_xyce(template, topology, corner, temperature, supply, output):
    """Translate the AnalogGym ngspice control block to an explicit Xyce AC run."""

    text = template.replace("HoiLee_AFFC_Pin_3", topology)
    text = re.sub(r"\.include \.\./mosfet_model/sky130_pdk/libs\.tech/ngspice/corners/[^\s]+",
                  f".include ../mosfet_model/sky130_pdk/libs.tech/ngspice/corners/{corner}.spice", text)
    text = re.sub(r"\.PARAM supply_voltage\s*=\s*[^\s]+", f".PARAM supply_voltage = {supply:g}", text)
    lines = []
    in_control = False
    for line in text.splitlines(True):
        stripped = line.strip().lower()
        if stripped == ".control":
            in_control = True
            continue
        if in_control and stripped == ".endc":
            in_control = False
            continue
        if in_control:
            continue
        fields = stripped.split()
        if len(fields) >= 2 and fields[0] in {".measure", ".meas"} and fields[1] == "dc":
            continue
        lines.append(line.replace("ac=1", "AC 1").replace("AC=1", "AC 1"))
    translated = "".join(lines)
    translated = re.sub(
        r"(?im)^\\.meas\\s+ac\\s+phase_in_deg\\s+param=.*$",
        ".meas ac phase_in_deg find vp(opout) when vdb(opout)=0",
        translated,
    )
    translated = translated.replace(".end\n", ".AC DEC 10 0.1 1G\n.PRINT AC VDB(opout) VP(opout)\n.END\n")
    translated = re.sub(r"(?im)^\.temp\s+[^\n]+\n", "", translated)
    first_line, separator, remainder = translated.partition("\n")
    translated = f"{first_line}{separator}.temp {temperature:g}\n{remainder}"
    output.write_text(translated, encoding="utf-8")
    return output


def metrics(log):
    values = {}
    mapping = {"dcgain": "dcgain_db", "gain_bandwidth_product": "gbw_hz", "phase_in_deg": "phase_in_deg", "phase_in_rad": "phase_in_rad"}
    for line in log.splitlines():
        match = re.search(r"\b(dcgain|gain_bandwidth_product|phase_in_deg|phase_in_rad)\s*=\s*([^\s]+)", line, re.I)
        if match:
            try:
                values[mapping[match.group(1).lower()]] = float(match.group(2))
            except ValueError:
                values[mapping[match.group(1).lower()]] = None
    if values.get("phase_in_deg") is None and values.get("phase_in_rad") is not None:
        values["phase_in_deg"] = math.degrees(values["phase_in_rad"])
    if values.get("phase_in_deg") is not None:
        values["phase_margin_deg"] = 180.0 + values["phase_in_deg"]
    return values


def run(template, topology, corner, temperature, supply, simulator, work):
    testbench = work / "amp_spice_testbench"
    testbench.mkdir(parents=True, exist_ok=True)
    simulator_name = Path(simulator).name.lower()
    prepare_fn = prepare_xyce if simulator_name.startswith("xyce") else prepare
    netlist = prepare_fn(template, topology, corner, temperature, supply, testbench / "TB_Amplifier_ACDC.cir")
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


def search_robust_spectra(budget, seed, evaluate, low, high, conditions):
    """Use the same simulation cap for a three-corner screening objective."""

    candidate_budget = budget // len(conditions)
    rng = np.random.default_rng(seed)
    best_x = low + 0.5 * (high - low)
    best_score = float("inf")
    first = 0
    evaluations = 0

    def visit(x, candidate_index):
        nonlocal best_x, best_score, first, evaluations
        scores = []
        for condition in conditions:
            scores.append(score(evaluate(x, condition)))
        evaluations += len(conditions)
        current = float(sum(scores) / len(scores))
        if current == 0.0 and first == 0:
            first = evaluations
        if current < best_score:
            best_score, best_x = current, np.asarray(x, dtype=float).copy()
        return current

    coverage = min(max(8, 2 * len(low)), max(1, candidate_budget // 3))
    for index, unit in enumerate(rng.random((coverage, len(low))), 1):
        visit(low + unit * (high - low), index)
    es = None
    if coverage < candidate_budget:
        import cma
        es = cma.CMAEvolutionStrategy([0.5] * len(low), 0.25,
                                       {"bounds": [0, 1], "seed": seed + 2000, "verbose": -9})
    index = coverage
    while index < candidate_budget:
        points = es.ask()[:candidate_budget - index]
        scores = []
        for point in points:
            x = low + np.clip(point, 0.0, 1.0) * (high - low)
            scores.append(visit(x, index + 1))
            index += 1
        if scores:
            es.tell(points[:len(scores)], scores)
    return best_x, best_score, first


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--topology", default="HoiLee_AFFC_Pin_3")
    parser.add_argument("--simulator", default="ngspice")
    parser.add_argument("--pdk-root", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--methods", default="spectra,anaflow_cleanroom")
    parser.add_argument("--search-profile", choices=("nominal", "spectra_robust"), default="nominal")
    parser.add_argument("--pvt-limit", type=int, default=None, help="Limit PVT conditions for capability smoke tests")
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
    if args.pvt_limit is not None:
        if args.pvt_limit < 1:
            raise SystemExit("--pvt-limit must be positive")
        pvt = pvt[:args.pvt_limit]
    root = args.output.parent / f"_{args.output.stem}_work"
    root.mkdir(parents=True, exist_ok=True)
    source_pdk = args.pdk_root.resolve()
    if not source_pdk.exists():
        raise SystemExit(f"PDK root does not exist: {source_pdk}")

    methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    unknown_methods = set(methods).difference({"spectra", "anaflow_cleanroom"})
    if unknown_methods:
        raise SystemExit(f"unknown methods: {sorted(unknown_methods)}")
    rows = []
    for seed in (int(item) for item in args.seeds.split(",") if item.strip()):
        for method in methods:
            work = root / f"s{seed}_{method}"
            work.mkdir(exist_ok=True)
            ensure_symlink(work / "spice_netlist", amp / "spice_netlist", directory=True)
            design_dir = work / "design_variables"
            design_dir.mkdir(exist_ok=True)
            (work / "mosfet_model").mkdir(exist_ok=True)
            ensure_symlink(work / "mosfet_model" / "sky130_pdk", source_pdk, directory=True)
            design_file = design_dir / args.topology

            def evaluate_nominal(x):
                write_vars(design_file, names, defaults, x)
                return run(template, args.topology, "tt", 27.0, 1.8, args.simulator, work)[0]

            def evaluate_condition(x, condition):
                write_vars(design_file, names, defaults, x)
                return run(template, args.topology, condition.corner, condition.temperature_c,
                           condition.supply_v, args.simulator, work)[0]

            start = time.perf_counter()
            if method == "spectra" and args.search_profile == "spectra_robust":
                robust_conditions = tuple(next(condition for condition in pvt if condition.name == name)
                                          for name in ("tt_27C_1.8V", "ss_-40C_1.62V", "ff_125C_1.98V"))
                best_x, best_score, first = search_robust_spectra(
                    args.budget, seed, evaluate_condition, low, high, robust_conditions
                )
            else:
                search_method = "spectra" if method == "spectra" else "random"
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
                "search_profile": args.search_profile,
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
