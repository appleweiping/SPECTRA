#!/usr/bin/env python3
"""Offline smoke test for the versioned benchmark contracts.

This script exercises serialization, digest stability and finite-violation
validation. It never invokes a simulator or an LLM.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spectra.bench.contracts import (
    ConditionReceipt,
    SimulationReceipt,
    TaskSnapshot,
    finite_violation_errors,
    sha256_digest,
    validate_receipt,
)
from spectra.bench.cross_domain import make_pvt_grid


def main() -> None:
    conditions = make_pvt_grid()[:2]
    task = TaskSnapshot(
        track_id="offline-contract-smoke",
        task_id="amp-0",
        source="smoke",
        source_commit="local",
        topology_digest="topology-digest",
        pdk_id="sky130",
        simulator_id="ngspice",
        simulator_version="44.2",
        metric_names=("gain", "ugbw"),
        pvt_conditions=conditions,
        budget_simulations=300,
        budget_llm_calls=12,
        seed=0,
        parser_version="metrics-v1",
    )
    receipt = SimulationReceipt(
        task_digest=task.digest,
        method="spectra",
        seed=0,
        simulator_id="ngspice",
        simulator_version="44.2",
        netlist_digest="netlist-digest",
        simulations=300,
        llm_calls=12,
        tt_violation=0.0,
        pvt_violation=0.125,
        conditions=tuple(
            ConditionReceipt(
                name=condition.name,
                normalized_violation=0.0 if index == 0 else 0.25,
                passed=index == 0,
                metrics={"gain": 100.0, "ugbw": 1.0e6},
            )
            for index, condition in enumerate(conditions)
        ),
        parser_version="metrics-v1",
    )
    validate_receipt(
        receipt,
        expected_conditions=[condition.name for condition in conditions],
        expected_simulations=300,
        expected_llm_calls=12,
    )
    assert task.digest == sha256_digest(task.to_dict()), "task digest is not canonical"
    bad = receipt.to_dict()
    bad["pvt_violation"] = float("inf")
    assert finite_violation_errors(bad), "non-finite violation was not rejected"
    print("contracts smoke: PASS", task.digest[:12], receipt.digest[:12])


if __name__ == "__main__":
    main()
