#!/usr/bin/env python3
"""Write a readable comparison for a matched AnalogGym robust receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--topology", required=True)
    args = parser.parse_args()

    receipt = json.loads(args.merged.read_text(encoding="utf-8"))
    aggregate = receipt["aggregate"]
    rows = []
    for method in ("spectra", "anaflow_cleanroom"):
        values = aggregate[method]
        rows.append(
            "| {method} | {tt:.3f} | {pvt:.3f} | {ttv:.6f} | {pvtv:.6f} | {wall:.1f} |".format(
                method="SPECTRA" if method == "spectra" else "AnaFlow clean-room",
                tt=values["tt_success"],
                pvt=values["pvt_success"],
                ttv=values["mean_tt_violation"],
                pvtv=values["mean_pvt_violation"],
                wall=values["mean_wall_seconds"],
            )
        )
    spectra = aggregate["spectra"]
    anaflow = aggregate["anaflow_cleanroom"]
    pvt_delta = spectra["pvt_success"] - anaflow["pvt_success"]
    violation_delta = anaflow["mean_pvt_violation"] - spectra["mean_pvt_violation"]
    wall_delta = spectra["mean_wall_seconds"] - anaflow["mean_wall_seconds"]
    text = """# AnalogGym robust PVT comparison

- Topology: `{topology}`
- Contract: `{budget}` simulations, `{calls}` calls, seeds `0,1,2`, `{conditions}` verifier conditions
- Profile: `spectra_robust` for SPECTRA and matched `nominal` clean-room AnaFlow
- Ranking eligible: `{eligible}`

| Method | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds |
|---|---:|---:|---:|---:|---:|
{rows}

SPECTRA's PVT-success delta versus AnaFlow is `{pvt_delta:+.3f}` and its mean-PVT-violation reduction is `{violation_delta:+.6f}`. Its mean-wall-time delta is `{wall_delta:+.1f}` seconds. The receipt is a matched public sensitivity stratum and is included by the literal XSOTA audit. It does not by itself establish universal analog-sizing SOTA.
""".format(
        topology=args.topology,
        budget=receipt["budget"],
        calls=receipt["llm_calls"],
        conditions=receipt["pvt_conditions"],
        eligible=receipt["ranking_eligible"],
        rows="\n".join(rows),
        pvt_delta=pvt_delta,
        violation_delta=violation_delta,
        wall_delta=wall_delta,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
