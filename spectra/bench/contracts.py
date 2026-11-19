"""Versioned task and simulation evidence contracts.

The public benchmark runners predate one shared run envelope and therefore
emit a few compatible JSON shapes.  These small dataclasses provide a stable
identity and receipt layer without coupling the sizing agent to a simulator.
They deliberately perform validation only.  Simulation remains the
responsibility of the existing remote runners.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, Sequence

from .cross_domain import PvtCondition


TASK_SNAPSHOT_SCHEMA = "spectra-task-snapshot/v1"
SIMULATION_RECEIPT_SCHEMA = "spectra-simulation-receipt/v1"


def _text(value: Any, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{field_name} must be a non-empty string")
    return result


def _finite(value: Any, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _canonical_value(value: Any) -> Any:
    """Convert dataclasses and nested mappings to JSON-stable values."""

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _canonical_value(value.to_dict())
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, set):
        return [_canonical_value(item) for item in sorted(value, key=str)]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("canonical JSON cannot contain a non-finite float")
    return value


def canonical_json(value: Any) -> str:
    """Return deterministic UTF-8 JSON suitable for hashing and receipts."""

    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_digest(value: Any) -> str:
    """Hash the canonical JSON representation of *value*."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TaskSnapshot:
    """Immutable identity of one sizing task and its evaluation contract."""

    track_id: str
    task_id: str
    source: str
    source_commit: str
    topology_digest: str
    pdk_id: str
    simulator_id: str
    simulator_version: str
    metric_names: tuple[str, ...]
    pvt_conditions: tuple[PvtCondition, ...] = ()
    budget_simulations: int = 0
    budget_llm_calls: int = 0
    seed: int = 0
    parser_version: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    schema: ClassVar[str] = TASK_SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        for name in (
            "track_id",
            "task_id",
            "source",
            "source_commit",
            "topology_digest",
            "pdk_id",
            "simulator_id",
            "simulator_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        metrics = tuple(_text(item, "metric name") for item in self.metric_names)
        if len(set(metrics)) != len(metrics):
            raise ValueError("metric_names must be unique")
        object.__setattr__(self, "metric_names", metrics)
        conditions = tuple(self.pvt_conditions)
        if len({condition.name for condition in conditions}) != len(conditions):
            raise ValueError("pvt_conditions must have unique names")
        object.__setattr__(self, "pvt_conditions", conditions)
        for name in ("budget_simulations", "budget_llm_calls"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        object.__setattr__(self, "parser_version", str(self.parser_version).strip())
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "track_id": self.track_id,
            "task_id": self.task_id,
            "source": self.source,
            "source_commit": self.source_commit,
            "topology_digest": self.topology_digest,
            "pdk_id": self.pdk_id,
            "simulator_id": self.simulator_id,
            "simulator_version": self.simulator_version,
            "metric_names": list(self.metric_names),
            "pvt_conditions": [condition.to_dict() for condition in self.pvt_conditions],
            "budget_simulations": self.budget_simulations,
            "budget_llm_calls": self.budget_llm_calls,
            "seed": self.seed,
            "parser_version": self.parser_version,
            "metadata": dict(self.metadata),
        }

    def canonical_json(self) -> str:
        return canonical_json(self)

    @property
    def digest(self) -> str:
        return sha256_digest(self)


@dataclass(frozen=True)
class ConditionReceipt:
    """One simulator condition and its normalized violation."""

    name: str
    normalized_violation: float
    passed: bool
    metrics: Mapping[str, Any] = field(default_factory=dict)
    missing_metrics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "condition name"))
        object.__setattr__(
            self,
            "normalized_violation",
            _finite(self.normalized_violation, "normalized_violation"),
        )
        object.__setattr__(self, "passed", bool(self.passed))
        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(
            self,
            "missing_metrics",
            tuple(_text(item, "missing metric") for item in self.missing_metrics),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.name,
            "normalized_violation": self.normalized_violation,
            "pass": self.passed,
            "metrics": dict(self.metrics),
            "missing_metrics": list(self.missing_metrics),
        }


@dataclass(frozen=True)
class SimulationReceipt:
    """Immutable evidence emitted after one sizing cell is evaluated."""

    task_digest: str
    method: str
    seed: int
    simulator_id: str
    simulator_version: str
    netlist_digest: str
    simulations: int
    llm_calls: int
    tt_violation: float
    pvt_violation: float
    conditions: tuple[ConditionReceipt, ...] = ()
    status: str = "completed"
    parser_version: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    schema: ClassVar[str] = SIMULATION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        for name in (
            "task_digest",
            "method",
            "simulator_id",
            "simulator_version",
            "netlist_digest",
            "status",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        for name in ("simulations", "llm_calls"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("tt_violation", "pvt_violation"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        conditions = tuple(self.conditions)
        if len({condition.name for condition in conditions}) != len(conditions):
            raise ValueError("conditions must have unique names")
        object.__setattr__(self, "conditions", conditions)
        object.__setattr__(self, "parser_version", str(self.parser_version).strip())
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "task_digest": self.task_digest,
            "method": self.method,
            "seed": self.seed,
            "simulator_id": self.simulator_id,
            "simulator_version": self.simulator_version,
            "netlist_digest": self.netlist_digest,
            "simulations": self.simulations,
            "llm_calls": self.llm_calls,
            "tt_violation": self.tt_violation,
            "pvt_violation": self.pvt_violation,
            "conditions": [condition.to_dict() for condition in self.conditions],
            "status": self.status,
            "parser_version": self.parser_version,
            "metadata": dict(self.metadata),
        }

    def canonical_json(self) -> str:
        return canonical_json(self)

    @property
    def digest(self) -> str:
        return sha256_digest(self)


def finite_violation_errors(
    value: Mapping[str, Any] | SimulationReceipt,
    *,
    expected_conditions: Sequence[str] | None = None,
    expected_simulations: int | None = None,
    expected_llm_calls: int | None = None,
) -> list[str]:
    """Return validation errors for receipt violation fields and budgets.

    The function accepts a dataclass or a legacy JSON mapping, allowing old
    public shards to be audited before they are converted to a receipt.
    """

    payload = value.to_dict() if isinstance(value, SimulationReceipt) else dict(value)
    errors: list[str] = []

    def walk(node: Any, path: str = "") -> None:
        if isinstance(node, Mapping):
            for key, item in node.items():
                child = f"{path}.{key}" if path else str(key)
                if "violation" in str(key).lower():
                    if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)):
                        errors.append(f"{child} must be finite")
                walk(item, child)
        elif isinstance(node, (list, tuple)):
            for index, item in enumerate(node):
                walk(item, f"{path}[{index}]")

    walk(payload)
    if expected_simulations is not None and payload.get("simulations") != expected_simulations:
        errors.append(
            f"simulations={payload.get('simulations')!r}, expected {expected_simulations}"
        )
    if expected_llm_calls is not None and payload.get("llm_calls") != expected_llm_calls:
        errors.append(f"llm_calls={payload.get('llm_calls')!r}, expected {expected_llm_calls}")
    if expected_conditions is not None:
        observed = [
            str(item.get("condition"))
            for item in payload.get("conditions", [])
            if isinstance(item, Mapping)
        ]
        missing = sorted(set(expected_conditions).difference(observed))
        extra = sorted(set(observed).difference(expected_conditions))
        if missing:
            errors.append(f"missing conditions: {missing}")
        if extra:
            errors.append(f"unexpected conditions: {extra}")
    return errors


def validate_receipt(value: Mapping[str, Any] | SimulationReceipt, **kwargs: Any) -> None:
    """Raise ``ValueError`` when a receipt violates finite/budget checks."""

    errors = finite_violation_errors(value, **kwargs)
    if errors:
        raise ValueError("invalid simulation receipt: " + "; ".join(errors))

