"""Data contracts for public cross-domain sizing benchmarks.

The sizing agent remains independent of any particular public benchmark.  This
module records the provenance and execution capabilities needed before a cell
can enter a matched comparison.  It deliberately does not infer missing PDK,
simulator, corner, or metric information.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class CrossDomainTask:
    """Immutable task provenance attached to every benchmark cell."""

    track_id: str
    task_id: str
    source: str
    source_commit: str
    topology_digest: str
    pdk_id: str
    simulator_id: str
    simulator_version: str
    corners: tuple[str, ...]
    metric_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PvtCondition:
    """One immutable process, temperature and supply operating condition."""

    corner: str
    temperature_c: float
    supply_v: float

    @property
    def name(self) -> str:
        return f"{self.corner}_{self.temperature_c:g}C_{self.supply_v:g}V"

    def to_dict(self) -> dict[str, Any]:
        return {
            "corner": self.corner,
            "temperature_c": self.temperature_c,
            "supply_v": self.supply_v,
            "name": self.name,
        }


def make_pvt_grid(
    corners: Iterable[str] = ("tt", "ff", "ss", "sf", "fs"),
    temperatures_c: Iterable[float] = (-40.0, 27.0, 125.0),
    supplies_v: Iterable[float] = (1.62, 1.8, 1.98),
) -> tuple[PvtCondition, ...]:
    """Create a deterministic PVT grid with nominal TT first."""

    values = [PvtCondition(c, float(t), float(v))
              for c in corners for t in temperatures_c for v in supplies_v]
    nominal = PvtCondition("tt", 27.0, 1.8)
    return tuple([nominal] + [value for value in values if value != nominal])


def aggregate_pvt(
    metrics_by_condition: Mapping[str, Mapping[str, float]],
    specs: Mapping[str, Mapping[str, float] | tuple[str, float]],
) -> dict[str, Any]:
    """Aggregate a corner-complete result without hiding crashes or omissions."""

    condition_rows: list[dict[str, Any]] = []
    all_values: list[float] = []
    for condition, metrics in metrics_by_condition.items():
        per_metric = positive_normalized_violation(metrics, specs)
        finite = [value for value in per_metric.values() if value != float("inf")]
        missing = [name for name, value in per_metric.items() if value == float("inf")]
        violation = float("inf") if missing else (sum(finite) / max(1, len(finite)))
        condition_rows.append({
            "condition": condition,
            "metrics": dict(metrics),
            "metric_violation": per_metric,
            "normalized_violation": violation,
            "pass": not missing and violation == 0.0,
            "missing_metrics": missing,
        })
        if math.isfinite(violation):
            all_values.append(violation)
    pvt_pass = bool(condition_rows) and all(row["pass"] for row in condition_rows)
    return {
        "conditions_observed": len(condition_rows),
        "pvt_success": pvt_pass,
        "mean_normalized_violation": float("inf") if len(all_values) != len(condition_rows) else sum(all_values) / len(all_values),
        "median_normalized_violation": float("inf") if len(all_values) != len(condition_rows) else float(median(all_values)),
        "conditions": condition_rows,
    }


def validate_budget(record: Mapping[str, Any], simulations: int, llm_calls: int) -> list[str]:
    """Return budget violations for a cell.  Exact caps are required for ranking."""

    errors: list[str] = []
    observed_simulations = record.get("simulations")
    observed_calls = record.get("llm_calls")
    if observed_simulations != simulations:
        errors.append(f"simulations={observed_simulations!r}, expected {simulations}")
    if observed_calls != llm_calls:
        errors.append(f"llm_calls={observed_calls!r}, expected {llm_calls}")
    return errors


def sha256_file(path: str | os.PathLike[str]) -> str:
    """Return the SHA-256 digest of a public topology or model file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load and minimally validate the frozen cross-domain manifest."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "spectra-cross-domain/v1":
        raise ValueError("unsupported cross-domain manifest schema")
    tracks = payload.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("cross-domain manifest has no tracks")
    required = {"id", "source", "pdks", "simulators", "families", "seeds", "budget"}
    for track in tracks:
        missing = required.difference(track)
        if missing:
            raise ValueError(f"track {track.get('id', '<unknown>')} missing {sorted(missing)}")
    return payload


def positive_normalized_violation(
    values: Mapping[str, float],
    specs: Mapping[str, Mapping[str, float] | tuple[str, float]],
) -> dict[str, float]:
    """Compute per-metric positive residuals with task-local tolerances.

    ``specs`` accepts either ``{"op": ">", "target": ..., "tolerance": ...}``
    or the compact ``(op, target)`` form.  A missing value is represented by
    ``inf`` so crashes and parser omissions remain failures in aggregation.
    """

    result: dict[str, float] = {}
    for name, spec in specs.items():
        value = values.get(name)
        if isinstance(spec, Mapping):
            op = str(spec["op"])
            target = float(spec["target"])
            tolerance = float(spec.get("tolerance", max(abs(target), 1.0)))
        else:
            op, target = spec
            target = float(target)
            tolerance = max(abs(target), 1.0)
        if value is None:
            result[name] = float("inf")
            continue
        residual = target - float(value) if op == ">" else float(value) - target
        result[name] = max(0.0, residual) / tolerance
    return result


def _creationflags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def simulator_capabilities(
    names: Iterable[str] = ("ngspice", "xyce", "spectre", "hspice"),
    paths: Mapping[str, str | os.PathLike[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Probe binaries without treating an unavailable licensed tool as a pass.

    ``paths`` supports server installations kept outside ``PATH``. Existing
    callers retain PATH lookup when it is omitted.
    """

    result: dict[str, dict[str, Any]] = {}
    for name in names:
        configured = paths.get(name) if paths else None
        binary = str(configured) if configured else shutil.which(name)
        if binary and not Path(binary).is_file():
            binary = None
        entry: dict[str, Any] = {"binary": binary, "available": binary is not None, "version": None}
        if binary:
            try:
                proc = subprocess.run(
                    [binary, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=_creationflags(),
                )
                output = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
                meaningful = [line.strip() for line in output if line.strip(" *\t")]
                entry["version"] = meaningful[0][:240] if meaningful else None
            except (OSError, subprocess.SubprocessError) as exc:
                entry["probe_error"] = type(exc).__name__
        result[name] = entry
    return result


def write_receipt(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    """Write a stable JSON receipt used by audits and server synchronization."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
