"""SENSOR-B4-I09C — deterministic quota/storage evidence and false-green guard.

Builders are pure and serialize through one canonical byte function. Normal
pytest never writes the committed evidence tree: it regenerates each matrix in
memory and compares it byte-for-byte with the published checkpoint bytes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.storage.enums import DiskPressure, StoragePriority  # noqa: E402
from crypto_sensor_fabric.storage.quota import (  # noqa: E402
    STORAGE_CAPACITY_BLOCKED,
    QuotaConfig,
    QuotaFacts,
    WriteDisposition,
    classify_storage,
    decide_storage_write,
)
from crypto_sensor_fabric.storage.retention import (  # noqa: E402
    ConfidenceBand,
    RetentionPolicy,
    StorageEstimateInput,
    StorageEstimationError,
    UniverseTier,
    assess_destructive_retention,
    estimate_storage,
    retention_policy,
)

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
_OBSERVED_AT = datetime(2026, 1, 1, tzinfo=UTC)
_CONFIG = QuotaConfig(absolute_free_floor_bytes=20)


def stable_evidence_bytes(payload: dict[str, Any]) -> bytes:
    """Return the sole deterministic serialization used by I09 evidence."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def evaluate_case(case: dict[str, Any]) -> str:
    """Derive OK iff every declared required invariant is boolean true."""
    required = case.get("required_invariants")
    if not isinstance(required, list) or not required:
        raise AssertionError(f"case has no required_invariants: {case!r}")
    if len(required) != len(set(required)):
        raise AssertionError(f"case has duplicate required invariants: {case!r}")
    return "OK" if all(case.get(name) is True for name in required) else "FAIL"


def _case(name: str, required_invariants: list[str], **fields: Any) -> dict[str, Any]:
    row = {"case": name, **fields, "required_invariants": required_invariants}
    row["result"] = evaluate_case(row)
    return row


def _state(used: int, capacity: int = 10_000, floor: int = 20) -> Any:
    return classify_storage(
        QuotaFacts(
            capacity_bytes=capacity,
            used_bytes=used,
            free_bytes=capacity - used,
            absolute_free_floor_bytes=floor,
        ),
        config=_CONFIG,
        observed_at=_OBSERVED_AT,
    )


def build_watermark_boundary_matrix() -> dict[str, Any]:
    boundaries = (
        ("just_below_70_normal", 6_999, DiskPressure.NORMAL),
        ("at_70_watch", 7_000, DiskPressure.WATCH),
        ("just_below_85_watch", 8_499, DiskPressure.WATCH),
        ("at_85_constrained", 8_500, DiskPressure.CONSTRAINED),
        ("just_below_95_constrained", 9_499, DiskPressure.CONSTRAINED),
        ("at_95_critical", 9_500, DiskPressure.CRITICAL),
        ("at_100_critical", 10_000, DiskPressure.CRITICAL),
    )
    rows = []
    for name, used, expected in boundaries:
        actual = _state(used).pressure_state
        rows.append(
            _case(
                name,
                ["exact_classification"],
                capacity_bytes=10_000,
                used_bytes=used,
                byte_derived_utilization_millionths=(used * 1_000_000) // 10_000,
                expected_pressure=expected.value,
                actual_pressure=actual.value,
                exact_classification=actual is expected,
            )
        )
    return {
        "checkpoint": "SENSOR-B4-I09",
        "matrix": "WATERMARK_BOUNDARY",
        "policy": {"watch_percent": 70, "constrained_percent": 85, "critical_percent": 95},
        "arithmetic": "integer cross-products; equality belongs to higher pressure",
        "rows": rows,
        "summary": {"rows": len(rows), "ok": sum(row["result"] == "OK" for row in rows), "fail": sum(row["result"] == "FAIL" for row in rows)},
    }


def build_priority_pause_matrix() -> dict[str, Any]:
    scenarios = (
        ("normal_p0", 1_000, 100, StoragePriority.P0, WriteDisposition.PROCEED, False),
        ("normal_p2", 1_000, 100, StoragePriority.P2, WriteDisposition.PROCEED, False),
        ("watch_p2_safe", 7_000, 100, StoragePriority.P2, WriteDisposition.WARN, False),
        ("constrained_p0_safe", 8_500, 100, StoragePriority.P0, WriteDisposition.PROCEED, False),
        ("constrained_p1_safe", 8_500, 100, StoragePriority.P1, WriteDisposition.PROCEED, False),
        ("constrained_p2_deferred", 8_500, 100, StoragePriority.P2, WriteDisposition.DEFER, False),
        ("constrained_p3_paused", 8_500, 100, StoragePriority.P3, WriteDisposition.PAUSE, False),
        ("critical_p0_safe", 9_500, 100, StoragePriority.P0, WriteDisposition.WARN, False),
        ("critical_p1_blocked", 9_500, 100, StoragePriority.P1, WriteDisposition.BLOCK, True),
        ("critical_p2_blocked", 9_500, 100, StoragePriority.P2, WriteDisposition.BLOCK, True),
        ("critical_p3_blocked", 9_500, 100, StoragePriority.P3, WriteDisposition.BLOCK, True),
        ("p0_floor_equality_safe", 9_000, 1_000, StoragePriority.P0, WriteDisposition.PROCEED, False),
        ("p0_one_byte_floor_breach_blocked", 9_000, 1_001, StoragePriority.P0, WriteDisposition.BLOCK, True),
        ("zero_free_blocks_p0", 10_000, 0, StoragePriority.P0, WriteDisposition.BLOCK, True),
    )
    rows = []
    for name, used, write, priority, expected, blocked in scenarios:
        decision = decide_storage_write(
            _state(used), projected_write_bytes=write, priority=priority
        )
        rows.append(
            _case(
                name,
                ["actual_disposition_matches", "blocked_code_consistent"],
                pressure=_state(used).pressure_state.value,
                priority=priority.value,
                projected_write_bytes=write,
                projected_free_bytes=decision.projected_free_bytes,
                absolute_free_floor_bytes=decision.absolute_free_floor_bytes,
                expected_disposition=expected.value,
                actual_disposition=decision.disposition.value,
                actual_disposition_matches=decision.disposition is expected,
                blocked_code=decision.blocked_code,
                blocked_code_consistent=(decision.blocked_code == STORAGE_CAPACITY_BLOCKED) if blocked else decision.blocked_code is None,
            )
        )
    false_green = _case(
        "counterfactual_p0_allowed_one_byte_below_floor",
        ["floor_respected", "blocked_at_floor_breach"],
        pressure="NORMAL",
        priority="P0",
        projected_free_bytes=19,
        absolute_free_floor_bytes=20,
        actual_disposition="PROCEED",
        floor_respected=False,
        blocked_at_floor_breach=False,
    )
    rows.append(false_green)
    return {
        "checkpoint": "SENSOR-B4-I09",
        "matrix": "PRIORITY_PAUSE",
        "absolute_floor_rule": "safe iff free_bytes - projected_write_bytes >= absolute_free_floor_bytes",
        "rows": rows,
        "summary": {"rows": len(rows), "ok": sum(row["result"] == "OK" for row in rows), "fail": sum(row["result"] == "FAIL" for row in rows)},
    }


def _sample(**overrides: Any) -> StorageEstimateInput:
    values: dict[str, Any] = {
        "provider": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_TRADE,
        "universe_tier": UniverseTier.U0,
        "instrument": "BTC-PERP",
        "expected_days": 10,
        "sample_raw_bytes": 86_401,
        "sample_projection_bytes": 8_641,
        "sample_duration": 86_400,
        "available_budget_bytes": 2_000_000,
    }
    values.update(overrides)
    return StorageEstimateInput(**values)


def build_storage_estimator_matrix() -> dict[str, Any]:
    base = _sample()
    first = estimate_storage(base)
    second = estimate_storage(deepcopy(base))
    longer = estimate_storage(_sample(expected_days=base.expected_days + 1))
    low = estimate_storage(_sample(sample_duration=60, sample_raw_bytes=1))
    medium = estimate_storage(_sample(sample_duration=3_600))
    high = estimate_storage(_sample(sample_duration=86_400))
    overrun = estimate_storage(_sample(available_budget_bytes=1))
    rows = [
        _case(
            "deterministic_reconciliation",
            ["same_inputs_same_output", "components_reconcile", "integer_ceil_math"],
            bytes_per_day_raw=first.bytes_per_day_raw,
            bytes_per_day_projection=first.bytes_per_day_projection,
            estimated_total=first.estimated_total,
            expected_raw_per_day=86_401,
            expected_projection_per_day=8_641,
            same_inputs_same_output=first == second,
            components_reconcile=first.estimated_total == (first.bytes_per_day_raw + first.bytes_per_day_projection) * base.expected_days,
            integer_ceil_math=(first.bytes_per_day_raw, first.bytes_per_day_projection) == (86_401, 8_641),
        ),
        _case(
            "expected_days_monotonic",
            ["longer_not_smaller"],
            shorter_total=first.estimated_total,
            longer_total=longer.estimated_total,
            longer_not_smaller=longer.estimated_total >= first.estimated_total,
        ),
        _case(
            "budget_overrun_visible",
            ["overrun_detected", "excess_reconciles"],
            estimated_total=overrun.estimated_total,
            available_budget_bytes=overrun.available_budget_bytes,
            budget_excess_bytes=overrun.budget_excess_bytes,
            within_budget=overrun.within_budget,
            overrun_detected=not overrun.within_budget,
            excess_reconciles=overrun.budget_excess_bytes == overrun.estimated_total - overrun.available_budget_bytes,
        ),
        _case(
            "confidence_is_coverage_label",
            ["truthful_coverage_labels"],
            bands=[low.confidence_band.value, medium.confidence_band.value, high.confidence_band.value],
            expected_bands=["LOW", "MEDIUM", "HIGH"],
            truthful_coverage_labels=[low.confidence_band, medium.confidence_band, high.confidence_band] == [ConfidenceBand.LOW, ConfidenceBand.MEDIUM, ConfidenceBand.HIGH],
        ),
    ]
    for name, overrides in (
        ("zero_duration_typed_failure", {"sample_duration": 0}),
        ("negative_raw_typed_failure", {"sample_raw_bytes": -1}),
        ("negative_projection_typed_failure", {"sample_projection_bytes": -1}),
    ):
        try:
            estimate_storage(_sample(**overrides))
        except StorageEstimationError:
            failed_typed = True
        else:
            failed_typed = False
        rows.append(_case(name, ["invalid_input_fails_typed"], invalid_input_fails_typed=failed_typed))
    false_green = _case(
        "counterfactual_components_do_not_reconcile",
        ["components_reconcile"],
        bytes_per_day_raw=first.bytes_per_day_raw,
        bytes_per_day_projection=first.bytes_per_day_projection,
        estimated_total=first.estimated_total + 1,
        components_reconcile=False,
    )
    rows.append(false_green)
    return {
        "checkpoint": "SENSOR-B4-I09",
        "matrix": "STORAGE_ESTIMATOR",
        "math": "ceil(sample_component_bytes * 86400 / sample_duration), then total = (raw_per_day + projection_per_day) * expected_days",
        "confidence_basis": "sample coverage labels only; no unsupported statistical interval",
        "rows": rows,
        "summary": {"rows": len(rows), "ok": sum(row["result"] == "OK" for row in rows), "fail": sum(row["result"] == "FAIL" for row in rows)},
    }


def build_nondestructive_retention_matrix() -> dict[str, Any]:
    universe_rows = []
    for tier, expected in (
        (UniverseTier.U0, RetentionPolicy.SELECTIVE),
        (UniverseTier.U1, RetentionPolicy.COARSE_OR_METRICS),
        (UniverseTier.U2, RetentionPolicy.DISABLED_DEFAULT),
    ):
        decision = retention_policy(SensorFamily.MECHANICAL_BOOK_SNAPSHOT, tier)
        universe_rows.append(
            _case(
                f"book_policy_{tier.value.lower()}",
                ["policy_matches", "t0a_preserved"],
                universe_tier=tier.value,
                actual_policy=decision.policy.value,
                expected_policy=expected.value,
                policy_matches=decision.policy is expected,
                t0a_preserved=decision.preserve_t0a,
            )
        )
    t0a_rows = []
    for name, flags in (
        ("old", {"age_days": 10_000}),
        ("huge", {"size_bytes": 100 * 1024**4}),
        ("provider_repeatable_looking", {"duplicate_looking": True}),
        ("duplicate_looking", {"duplicate_looking": True, "revised": True}),
        ("revised", {"revised": True}),
    ):
        decision = assess_destructive_retention(
            priority=StoragePriority.P0, is_t0a=True, **flags
        )
        t0a_rows.append(
            _case(
                f"t0a_{name}_refused",
                ["destructive_action_refused", "t0a_preserved"],
                evidence_flags=list(decision.evidence_flags),
                reason=decision.reason,
                destructive_action_refused=not decision.allowed,
                t0a_preserved=decision.preserve_t0a,
            )
        )
    p3 = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=False)
    p2 = assess_destructive_retention(priority=StoragePriority.P2, is_t0a=False)
    rows = universe_rows + t0a_rows + [
        _case(
            "only_p3_non_t0a_evictable",
            ["p3_evictable", "p2_not_evictable"],
            p3_allowed=p3.allowed,
            p2_allowed=p2.allowed,
            p3_evictable=p3.allowed,
            p2_not_evictable=not p2.allowed,
        )
    ]
    return {
        "checkpoint": "SENSOR-B4-I09",
        "matrix": "NONDESTRUCTIVE_RETENTION",
        "doctrine": "NO AUTOMATIC DESTRUCTIVE T0A RETENTION IN V1",
        "rows": rows,
        "summary": {"rows": len(rows), "ok": sum(row["result"] == "OK" for row in rows), "fail": sum(row["result"] == "FAIL" for row in rows)},
    }


def build_quota_simulation() -> dict[str, Any]:
    """Frozen repository-consistent equivalent of quota_simulation.json."""
    scenarios = (
        ("normal_safe", 1_000, 100, StoragePriority.P0),
        ("watch_safe", 7_000, 100, StoragePriority.P2),
        ("constrained_p2_deferred", 8_500, 100, StoragePriority.P2),
        ("constrained_p0_safe", 8_500, 100, StoragePriority.P0),
        ("critical_p1_blocked", 9_500, 100, StoragePriority.P1),
        ("floor_breach_p0_blocked", 1_000, 1_000, StoragePriority.P0),
    )
    results = []
    for name, used, write, priority in scenarios:
        state = _state(used)
        decision = decide_storage_write(
            state, projected_write_bytes=write, priority=priority
        )
        results.append(
            {
                "scenario": name,
                "pressure": state.pressure_state.value,
                "priority": priority.value,
                "projected_write_bytes": write,
                "projected_free_bytes": decision.projected_free_bytes,
                "absolute_free_floor_bytes": decision.absolute_free_floor_bytes,
                "disposition": decision.disposition.value,
                "blocked_code": decision.blocked_code,
            }
        )
    return {
        "schema_version": "1.0",
        "checkpoint": "SENSOR-B4-I09",
        "network_accessed": False,
        "filesystem_mutated": False,
        "scenarios": results,
    }


BUILDERS = (
    ("build_watermark_boundary_matrix", "BLOC_04_I09_WATERMARK_BOUNDARY_MATRIX.json"),
    ("build_priority_pause_matrix", "BLOC_04_I09_PRIORITY_PAUSE_MATRIX.json"),
    ("build_storage_estimator_matrix", "BLOC_04_I09_STORAGE_ESTIMATOR_MATRIX.json"),
    ("build_nondestructive_retention_matrix", "BLOC_04_I09_NONDESTRUCTIVE_RETENTION_MATRIX.json"),
    ("build_quota_simulation", "BLOC_04_I09_QUOTA_SIMULATION.json"),
)


def test_required_invariant_evaluator_rejects_false_green() -> None:
    false_green = {
        "required_invariants": ["first", "second"],
        "first": True,
        "second": False,
        "result": "OK",
    }
    assert evaluate_case(false_green) == "FAIL"
    false_green["result"] = evaluate_case(false_green)
    assert false_green["result"] == "FAIL"
    with pytest.raises(AssertionError):
        evaluate_case({"required_invariants": [], "result": "OK"})
    with pytest.raises(AssertionError):
        evaluate_case({"required_invariants": ["x", "x"], "x": True})


def test_every_builder_is_byte_deterministic() -> None:
    for builder_name, _ in BUILDERS:
        builder = globals()[builder_name]
        assert stable_evidence_bytes(builder()) == stable_evidence_bytes(builder())


@pytest.mark.parametrize("builder_name,filename", BUILDERS)
def test_generated_matches_committed(builder_name: str, filename: str) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    generated = stable_evidence_bytes(globals()[builder_name]())
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes; "
        "publish changes explicitly, never through pytest"
    )


def test_every_committed_row_derives_result_from_required_invariants() -> None:
    for builder_name, filename in BUILDERS:
        if builder_name == "build_quota_simulation":
            continue
        payload = json.loads((EVIDENCE_DIR / filename).read_text(encoding="utf-8"))
        assert payload["rows"]
        assert payload["summary"]["rows"] == len(payload["rows"])
        assert payload["summary"]["ok"] + payload["summary"]["fail"] == len(payload["rows"])
        for row in payload["rows"]:
            assert row["result"] == evaluate_case(row)
    matrices = [json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8")) for _, name in BUILDERS[:-1]]
    counterfactuals = [row for matrix in matrices for row in matrix["rows"] if row["result"] == "FAIL"]
    assert len(counterfactuals) == 2
    assert all(row["case"].startswith("counterfactual_") for row in counterfactuals)


def test_evidence_directory_untouched_by_generation() -> None:
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(EVIDENCE_DIR.glob("BLOC_04_I09*.json"))
    }
    for builder_name, _ in BUILDERS:
        globals()[builder_name]()
    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(EVIDENCE_DIR.glob("BLOC_04_I09*.json"))
    }
    assert before == after
