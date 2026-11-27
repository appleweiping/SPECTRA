#!/usr/bin/env python3
"""Produce a capability and provenance receipt for public benchmark sources.

The audit is intentionally conservative.  A missing source root, PDK, or
simulator is recorded as unavailable and never converted into a benchmark pass.
Run it on the server before launching a cross-domain matrix, for example::

    python3 scripts/cross_domain_capability_audit.py \
      --manifest data/bench/cross_domain_manifest.json \
      --source-root opensource_31=/path/to/bench_sources/opensource-analog-circuits \
      --source-root atlas_dual_pdk=/path/to/bench_sources/atlas \
      --output results/cross_domain_capability_receipt.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from spectra.bench.cross_domain import load_manifest, simulator_capabilities, write_receipt


def _git_commit(root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() or None


def _source_digest(root: Path) -> tuple[int, str]:
    """Hash path names and file bytes while excluding a repository's .git data."""

    digest = hashlib.sha256()
    count = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative + b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        count += 1
    return count, digest.hexdigest()


def _parse_roots(values: list[str]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for value in values:
        track, separator, path = value.partition("=")
        if not separator or not track or not path:
            raise ValueError(f"--source-root must use TRACK=PATH: {value}")
        roots[track] = Path(path).expanduser().resolve()
    return roots


def build_receipt(
    manifest_path: Path,
    roots: dict[str, Path],
    simulator_paths: dict[str, Path],
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    tracks: list[dict[str, Any]] = []
    for track in manifest["tracks"]:
        track_id = track["id"]
        root = roots.get(track_id)
        entry: dict[str, Any] = {
            "id": track_id,
            "declared_pdks": list(track.get("pdks", [])),
            "declared_simulators": list(track.get("simulators", [])),
            "declared_families": list(track.get("families", [])),
            "source_root": str(root) if root else None,
            "source_available": bool(root and root.is_dir()),
            "source_commit": _git_commit(root) if root and root.is_dir() else None,
            "source_file_count": 0,
            "source_tree_sha256": None,
        }
        if root and root.is_dir():
            count, digest = _source_digest(root)
            entry["source_file_count"] = count
            entry["source_tree_sha256"] = digest
        tracks.append(entry)
    return {
        "schema": "spectra-cross-domain-capability/v1",
        "manifest": str(manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "simulators": simulator_capabilities(paths=simulator_paths),
        "tracks": tracks,
        "ranking_eligible": False,
        "ranking_reason": "Capability receipt only. A matched cell still requires task digest, PDK/model digest, corners, verifier, seed and budget evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", action="append", default=[], metavar="TRACK=PATH")
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="probe a simulator binary outside PATH",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_receipt(
        args.manifest.resolve(),
        _parse_roots(args.source_root),
        _parse_roots(args.simulator),
    )
    write_receipt(args.output, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
