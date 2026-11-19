"""Data contracts for public cross-domain sizing benchmarks.

The sizing agent remains independent of any particular public benchmark.  This
module records the provenance and execution capabilities needed before a cell
can enter a matched comparison.  It deliberately does not infer missing PDK,
simulator, corner, or metric information.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
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


def simulator_capabilities(names: Iterable[str] = ("ngspice", "xyce", "spectre", "hspice")) -> dict[str, dict[str, Any]]:
    """Probe binaries without treating an unavailable licensed tool as a pass."""

    result: dict[str, dict[str, Any]] = {}
    for name in names:
        binary = shutil.which(name)
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
                entry["version"] = output[0][:240] if output else None
            except (OSError, subprocess.SubprocessError) as exc:
                entry["probe_error"] = type(exc).__name__
        result[name] = entry
    return result


def write_receipt(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    """Write a stable JSON receipt used by audits and server synchronization."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
