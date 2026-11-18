"""Create the public fixed-topology sizing track from a frozen task subset.

The sizing track removes the hidden reference point used to certify the design
benchmark and exposes only the topology family, variable bounds, testbench and
specification. Every external sizing adapter therefore receives the same
topology and search space. The original topconf6 file remains unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path

from spectra.bench.templates import T
from spectra.paths import ROOT


def build(source: str, destination: str) -> int:
    src = ROOT / source
    dst = ROOT / destination
    source_rows = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    families = getattr(build, "families", None)
    per_family = getattr(build, "per_family", None)
    if families and per_family:
        source_rows = [task for family in families for task in sorted(
            [row for row in source_rows if row.get("family") == family],
            key=lambda row: (not bool(row.get("robust")), row["id"]))[:per_family]]
    rows = []
    for task in source_rows:
        template_name = task.get("ref", {}).get("template")
        if template_name not in T:
            raise ValueError(f"task {task['id']} has no public sizing template")
        template = T[template_name]
        public = {k: v for k, v in task.items() if k not in {"ref", "ref_metrics"}}
        public["sizing"] = {
            "template": template_name,
            "variables": [
                {"name": v.name, "lo": v.lo, "hi": v.hi, "log": v.log, "integer": v.integer}
                for v in template["vars"]
            ],
            "topology_source": "spectra.bench.templates",
            "topology_digest": hashlib.sha256(inspect.getsource(template["build"]).encode()).hexdigest(),
        }
        rows.append(public)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(f"wrote {len(rows)} fixed-topology sizing tasks to {dst}")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/bench/topconf6.jsonl")
    parser.add_argument("--destination", default="data/bench/topconf6_sizing.jsonl")
    parser.add_argument("--families", default="")
    parser.add_argument("--per-family", type=int, default=0)
    args = parser.parse_args()
    build.families = [f for f in args.families.split(",") if f]
    build.per_family = args.per_family
    build(args.source, args.destination)
