"""SENSOR-B4-I09R1C — evidence truth, authority, and admission microseal matrices.

The historical I09 evidence tree is immutable. R1 builders are pure, generate
in memory, and are byte-compared only after explicit D publication.
"""

from __future__ import annotations

import hashlib
import json
import sys
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
from crypto_sensor_fabric.storage.models import StorageQuotaState  # noqa: E402
from crypto_sensor_fabric.storage.quota import (  # noqa: E402
    STORAGE_CAPACITY_BLOCKED,
    QuotaConfig,
    QuotaFacts,
    QuotaWritePolicyError,
    WriteDisposition,
    classify_storage,
    decide_storage_write,
)
from crypto_sensor_fabric.storage.retention import (  # noqa: E402
    ConfidenceBand,
    RetentionConfig,
    RetentionConfigurationError,
    StorageEstimateInput,
    UniverseTier,
    assess_destructive_retention,
    assess_storage_admission,
    estimate_storage,
)

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
HISTORICAL_I09_HASHES = {
    "BLOC_04_I09_WATERMARK_BOUNDARY_MATRIX.json": "39646fa3e7e602fd01d4026e3b6a8167fefbcb62457f7862a196d8171fe4938d",
    "BLOC_04_I09_PRIORITY_PAUSE_MATRIX.json": "5635a53dc48e12b5f6091a3f43872d98742733865902b5ce7bc6505b71e59bad",
    "BLOC_04_I09_STORAGE_ESTIMATOR_MATRIX.json": "c5ca8981cd5d3f620db6879f467fcbe24b91795ea102465b5e4c8000d4c38c1f",
    "BLOC_04_I09_NONDESTRUCTIVE_RETENTION_MATRIX.json": "3de1aaeda90f68664e3090f8c7b274d55357170c0a4aeb7bc9917b5c1a4296f7",
    "BLOC_04_I09_QUOTA_SIMULATION.json": "1baa5d44a2725b1e37b0d9a6483f6453c781227f76286d7ab065c16022e895b6",
    "BLOC_04_I09_QUOTA_STORAGE_ESTIMATOR_EVIDENCE.md": "724336539c9b4ef114e2d3e27e8ed86c3d99aa0039c4ec97224a1446399bb317",
}
_CONFIG = QuotaConfig(absolute_free_floor_bytes=20)
_OBSERVED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def stable_evidence_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def evaluate_case(case: dict[str, Any]) -> str:
    required = case.get("required_invariants")
    if not isinstance(required, list) or not required:
        raise AssertionError(f"case has no required_invariants: {case!r}")
    if len(required) != len(set(required)):
        raise AssertionError(f"case has duplicate required invariants: {case!r}")
    return "OK" if all(case.get(name) is True for name in required) else "FAIL"


def _case(name: str, required: list[str], **fields: Any) -> dict[str, Any]:
    row = {"case": name, **fields, "required_invariants": required}
    row["result"] = evaluate_case(row)
    return row


def _matrix(name: str, rows: list[dict[str, Any]], **fields: Any) -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I09R1",
        "matrix": name,
        **fields,
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "ok": sum(row["result"] == "OK" for row in rows),
            "fail": sum(row["result"] == "FAIL" for row in rows),
        },
    }


def _state(used: int, *, capacity: int = 1000, floor: int = 20) -> StorageQuotaState:
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


def _raw_state(
    pressure: DiskPressure,
    *,
    used: int,
    free: int,
    ratio: float,
    floor: int = 20,
) -> StorageQuotaState:
    return StorageQuotaState(
        pressure_state=pressure,
        priority_class=None,
        used_bytes=used,
        capacity_bytes=1000,
        free_bytes=free,
        utilization_ratio=ratio,
        absolute_free_floor_bytes=floor,
        observed_at=_OBSERVED_AT,
    )


def _estimate(total: int, budget: int = 2_000, duration: int = 86_400):
    return estimate_storage(
        StorageEstimateInput(
            provider="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            universe_tier=UniverseTier.U0,
            instrument="BTC-PERP",
            expected_days=1,
            sample_raw_bytes=total,
            sample_projection_bytes=0,
            sample_duration=duration,
            available_budget_bytes=budget,
        ),
        config=RetentionConfig(),
    )


def build_simulation_truth_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name, used, write, priority, expected, expected_code in (
        ("exact_floor_permitted", 900, 80, StoragePriority.P0, WriteDisposition.PROCEED, None),
        ("one_byte_below_floor_blocked", 900, 81, StoragePriority.P0, WriteDisposition.BLOCK, STORAGE_CAPACITY_BLOCKED),
        ("normal_safe_p0", 100, 100, StoragePriority.P0, WriteDisposition.PROCEED, None),
        ("watch_safe_p2", 700, 100, StoragePriority.P2, WriteDisposition.WARN, None),
        ("constrained_p2_deferred", 850, 100, StoragePriority.P2, WriteDisposition.DEFER, None),
        ("critical_p0_warn", 950, 0, StoragePriority.P0, WriteDisposition.WARN, None),
        ("critical_p1_blocked", 950, 0, StoragePriority.P1, WriteDisposition.BLOCK, STORAGE_CAPACITY_BLOCKED),
    ):
        decision = decide_storage_write(
            _state(used),
            projected_write_bytes=write,
            priority=priority,
            config=_CONFIG,
        )
        relationship = (
            "ABOVE_FLOOR"
            if decision.projected_free_bytes > decision.absolute_free_floor_bytes
            else "AT_FLOOR"
            if decision.projected_free_bytes == decision.absolute_free_floor_bytes
            else "BELOW_FLOOR"
        )
        rows.append(
            _case(
                name,
                ["disposition_matches", "blocked_code_matches", "floor_relationship_correct"],
                projected_free_bytes=decision.projected_free_bytes,
                absolute_free_floor_bytes=decision.absolute_free_floor_bytes,
                floor_relationship=relationship,
                expected_disposition=expected.value,
                actual_disposition=decision.disposition.value,
                disposition_matches=decision.disposition is expected,
                expected_blocked_code=expected_code,
                actual_blocked_code=decision.blocked_code,
                blocked_code_matches=decision.blocked_code == expected_code,
                floor_relationship_correct=(
                    relationship == "AT_FLOOR"
                    if name == "exact_floor_permitted"
                    else relationship == "BELOW_FLOOR"
                    if name == "one_byte_below_floor_blocked"
                    else relationship == "ABOVE_FLOOR"
                ),
            )
        )
    historical = json.loads(
        (EVIDENCE_DIR / "BLOC_04_I09_QUOTA_SIMULATION.json").read_text(encoding="utf-8")
    )
    old = next(row for row in historical["scenarios"] if row["scenario"] == "floor_breach_p0_blocked")
    rows.append(
        _case(
            "historical_false_scenario_preserved",
            ["historical_bytes_preserved", "historical_defect_confirmed"],
            historical_projected_free_bytes=old["projected_free_bytes"],
            historical_absolute_free_floor_bytes=old["absolute_free_floor_bytes"],
            historical_disposition=old["disposition"],
            historical_blocked_code=old["blocked_code"],
            historical_bytes_preserved=_sha256(EVIDENCE_DIR / "BLOC_04_I09_QUOTA_SIMULATION.json")
            == HISTORICAL_I09_HASHES["BLOC_04_I09_QUOTA_SIMULATION.json"],
            historical_defect_confirmed=(
                old["projected_free_bytes"] > old["absolute_free_floor_bytes"]
                and old["disposition"] == "PROCEED"
                and old["blocked_code"] is None
            ),
        )
    )
    rows.append(
        _case(
            "counterfactual_one_byte_below_floor_permitted",
            ["disposition_matches", "floor_relationship_correct"],
            projected_free_bytes=19,
            absolute_free_floor_bytes=20,
            expected_disposition="BLOCK",
            actual_disposition="PROCEED",
            disposition_matches=False,
            floor_relationship_correct=False,
        )
    )
    return _matrix(
        "SIMULATION_TRUTH",
        rows,
        rule="Every scenario declares required invariants; no simulation exception remains.",
    )


def _essential_attack(priority: StoragePriority) -> tuple[bool, str]:
    try:
        decide_storage_write(
            _state(950),
            projected_write_bytes=0,
            priority=priority,
            essential=True,  # type: ignore[call-arg]
            config=_CONFIG,
        )
    except TypeError as exc:
        return True, str(exc)
    return False, "accepted"


def _policy_attack(state: StorageQuotaState, priority: StoragePriority = StoragePriority.P2):
    try:
        decide_storage_write(
            state,
            projected_write_bytes=0,
            priority=priority,
            config=_CONFIG,
        )
    except QuotaWritePolicyError as exc:
        return True, str(exc)
    return False, "accepted"


def build_priority_authority_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for priority in (StoragePriority.P1, StoragePriority.P2, StoragePriority.P3):
        refused, detail = _essential_attack(priority)
        rows.append(
            _case(
                f"essential_bypass_removed_{priority.value.lower()}",
                ["caller_bypass_refused"],
                priority=priority.value,
                attack="essential=True",
                typed_refusal=refused,
                detail=detail,
                caller_bypass_refused=refused,
            )
        )
    attacks = (
        ("forged_normal_critical_bytes", _raw_state(DiskPressure.NORMAL, used=950, free=50, ratio=0.95)),
        ("stale_watch_critical_bytes", _raw_state(DiskPressure.WATCH, used=950, free=50, ratio=0.95)),
        ("stale_critical_normal_bytes", _raw_state(DiskPressure.CRITICAL, used=100, free=900, ratio=0.1)),
        ("used_free_capacity_contradiction", _raw_state(DiskPressure.CRITICAL, used=600, free=300, ratio=0.6)),
        ("ratio_contradiction", _raw_state(DiskPressure.CRITICAL, used=950, free=50, ratio=0.5)),
        ("floor_config_contradiction", _raw_state(DiskPressure.CRITICAL, used=950, free=50, ratio=0.95, floor=0)),
    )
    for name, state in attacks:
        refused, detail = _policy_attack(state)
        rows.append(
            _case(
                name,
                ["untrusted_state_refused"],
                supplied_pressure=state.pressure_state.value,
                used_bytes=state.used_bytes,
                capacity_bytes=state.capacity_bytes,
                free_bytes=state.free_bytes,
                utilization_ratio=state.utilization_ratio,
                absolute_free_floor_bytes=state.absolute_free_floor_bytes,
                typed_refusal=refused,
                detail=detail,
                untrusted_state_refused=refused,
            )
        )
    for priority, expected in (
        (StoragePriority.P0, WriteDisposition.WARN),
        (StoragePriority.P1, WriteDisposition.BLOCK),
        (StoragePriority.P2, WriteDisposition.BLOCK),
        (StoragePriority.P3, WriteDisposition.BLOCK),
    ):
        decision = decide_storage_write(
            _state(950), projected_write_bytes=0, priority=priority, config=_CONFIG
        )
        rows.append(
            _case(
                f"critical_{priority.value.lower()}_exact_matrix",
                ["disposition_matches", "blocked_code_matches"],
                priority=priority.value,
                expected_disposition=expected.value,
                actual_disposition=decision.disposition.value,
                disposition_matches=decision.disposition is expected,
                expected_blocked_code=STORAGE_CAPACITY_BLOCKED if expected is WriteDisposition.BLOCK else None,
                actual_blocked_code=decision.blocked_code,
                blocked_code_matches=decision.blocked_code == (STORAGE_CAPACITY_BLOCKED if expected is WriteDisposition.BLOCK else None),
            )
        )
    p0_floor = decide_storage_write(
        _state(950), projected_write_bytes=31, priority=StoragePriority.P0, config=_CONFIG
    )
    rows.append(
        _case(
            "critical_p0_hard_floor_precedence",
            ["disposition_matches", "blocked_code_matches"],
            expected_disposition="BLOCK",
            actual_disposition=p0_floor.disposition.value,
            disposition_matches=p0_floor.disposition is WriteDisposition.BLOCK,
            expected_blocked_code=STORAGE_CAPACITY_BLOCKED,
            actual_blocked_code=p0_floor.blocked_code,
            blocked_code_matches=p0_floor.blocked_code == STORAGE_CAPACITY_BLOCKED,
        )
    )
    return _matrix(
        "PRIORITY_AUTHORITY",
        rows,
        policy="P0 alone continues at CRITICAL; every write revalidates byte facts and config authority.",
    )


def build_backfill_admission_matrix() -> dict[str, Any]:
    scenarios = (
        ("over_budget_blocked", _estimate(101, budget=100), _state(100), StoragePriority.P0, WriteDisposition.BLOCK),
        ("within_budget_floor_breach_blocked", _estimate(81), _state(900), StoragePriority.P0, WriteDisposition.BLOCK),
        ("within_budget_safe_admitted", _estimate(100), _state(100), StoragePriority.P0, WriteDisposition.PROCEED),
        ("constrained_p2_deferred", _estimate(10), _state(850), StoragePriority.P2, WriteDisposition.DEFER),
        ("constrained_p3_paused", _estimate(10), _state(850), StoragePriority.P3, WriteDisposition.PAUSE),
        ("critical_p1_blocked", _estimate(10), _state(950), StoragePriority.P1, WriteDisposition.BLOCK),
        ("critical_p2_blocked", _estimate(10), _state(950), StoragePriority.P2, WriteDisposition.BLOCK),
        ("critical_p3_blocked", _estimate(10), _state(950), StoragePriority.P3, WriteDisposition.BLOCK),
        ("p0_floor_refused", _estimate(81), _state(900), StoragePriority.P0, WriteDisposition.BLOCK),
    )
    rows = []
    for name, estimate, state, priority, expected in scenarios:
        decision = assess_storage_admission(
            estimate, state, priority=priority, quota_config=_CONFIG
        )
        expected_code = STORAGE_CAPACITY_BLOCKED if expected is WriteDisposition.BLOCK else None
        rows.append(
            _case(
                name,
                ["disposition_matches", "blocked_code_matches", "estimate_budget_truth_visible"],
                estimated_total=estimate.estimated_total,
                available_budget_bytes=estimate.available_budget_bytes,
                budget_excess_bytes=estimate.budget_excess_bytes,
                within_budget=estimate.within_budget,
                expected_disposition=expected.value,
                actual_disposition=decision.disposition.value,
                disposition_matches=decision.disposition is expected,
                expected_blocked_code=expected_code,
                actual_blocked_code=decision.blocked_code,
                blocked_code_matches=decision.blocked_code == expected_code,
                estimate_budget_truth_visible=(
                    estimate.within_budget
                    or (not estimate.within_budget and estimate.budget_excess_bytes > 0)
                ),
            )
        )
    return _matrix(
        "BACKFILL_ADMISSION",
        rows,
        policy="Oversize blocks before execution; budget-safe estimates pass through authoritative quota and floor policy.",
    )


def build_retention_config_safety_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for field in ("u2_full_depth_books_enabled", "automatic_t0a_destructive_actions"):
        for value in ("false", "true", 0, 1, None, [], {}):
            try:
                RetentionConfig(**{field: value})
            except RetentionConfigurationError as exc:
                refused = True
                detail = str(exc)
            else:
                refused = False
                detail = "accepted"
            rows.append(
                _case(
                    f"boolean_type_attack_{field}_{type(value).__name__}_{str(value).replace(' ', '_')}",
                    ["type_confusion_refused"],
                    field=field,
                    attacked_value=value,
                    typed_refusal=refused,
                    detail=detail,
                    type_confusion_refused=refused,
                )
            )
    rows.extend(
        [
            _case("valid_u2_false", ["valid_exact_bool_accepted"], field="u2_full_depth_books_enabled", value=False, valid_exact_bool_accepted=RetentionConfig(u2_full_depth_books_enabled=False).u2_full_depth_books_enabled is False),
            _case("valid_u2_true", ["valid_exact_bool_accepted"], field="u2_full_depth_books_enabled", value=True, valid_exact_bool_accepted=RetentionConfig(u2_full_depth_books_enabled=True).u2_full_depth_books_enabled is True),
            _case("valid_automatic_t0a_false", ["valid_exact_bool_accepted"], field="automatic_t0a_destructive_actions", value=False, valid_exact_bool_accepted=RetentionConfig(automatic_t0a_destructive_actions=False).automatic_t0a_destructive_actions is False),
        ]
    )
    flags = {"age_days": 10_000, "size_bytes": 100 * 1024**4, "duplicate_looking": True, "revised": True}
    for priority in StoragePriority:
        decision = assess_destructive_retention(priority=priority, is_t0a=True, **flags)
        rows.append(
            _case(
                f"t0a_refused_{priority.value.lower()}_all_flags",
                ["destructive_action_refused", "t0a_preserved"],
                priority=priority.value,
                evidence_flags=list(decision.evidence_flags),
                destructive_action_refused=not decision.allowed,
                t0a_preserved=decision.preserve_t0a,
            )
        )
    p3_t0a = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=True)
    p3_non_t0a = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=False)
    rows.append(
        _case(
            "p3_t0a_cannot_inherit_eviction",
            ["p3_t0a_refused", "p3_non_t0a_evictable"],
            p3_t0a_allowed=p3_t0a.allowed,
            p3_non_t0a_allowed=p3_non_t0a.allowed,
            p3_t0a_refused=not p3_t0a.allowed,
            p3_non_t0a_evictable=p3_non_t0a.allowed,
        )
    )
    tiny_high = _estimate(1, duration=86_400)
    rows.append(
        _case(
            "tiny_24h_sample_high_is_coverage_only",
            ["high_label_observed", "not_calibrated_probability", "not_representativeness_proof"],
            sample_bytes=1,
            sample_duration_seconds=86_400,
            confidence_band=tiny_high.confidence_band.value,
            high_label_observed=tiny_high.confidence_band is ConfidenceBand.HIGH,
            not_calibrated_probability=True,
            not_representativeness_proof=True,
        )
    )
    return _matrix(
        "RETENTION_CONFIG_SAFETY",
        rows,
        confidence_limitation="HIGH means >=24h duration coverage only; not a calibrated probability, confidence interval, or proof of representative activity.",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


BUILDERS: tuple[tuple[str, str], ...] = (
    ("build_simulation_truth_matrix", "BLOC_04_I09R1_SIMULATION_TRUTH_MATRIX.json"),
    ("build_priority_authority_matrix", "BLOC_04_I09R1_PRIORITY_AUTHORITY_MATRIX.json"),
    ("build_backfill_admission_matrix", "BLOC_04_I09R1_BACKFILL_ADMISSION_MATRIX.json"),
    ("build_retention_config_safety_matrix", "BLOC_04_I09R1_RETENTION_CONFIG_SAFETY_MATRIX.json"),
)


def test_required_invariant_evaluator_is_fail_closed() -> None:
    row = {"required_invariants": ["safe", "truthful"], "safe": True, "truthful": False, "result": "OK"}
    assert evaluate_case(row) == "FAIL"
    with pytest.raises(AssertionError):
        evaluate_case({"result": "OK"})


@pytest.mark.parametrize("builder_name,filename", BUILDERS)
def test_r1_generated_matches_committed(builder_name: str, filename: str) -> None:
    generated = stable_evidence_bytes(globals()[builder_name]())
    assert generated == (EVIDENCE_DIR / filename).read_bytes()


@pytest.mark.parametrize("builder_name,_filename", BUILDERS)
def test_every_r1_row_derives_result(builder_name: str, _filename: str) -> None:
    payload = globals()[builder_name]()
    assert payload["summary"]["rows"] == len(payload["rows"])
    assert payload["summary"]["ok"] + payload["summary"]["fail"] == len(payload["rows"])
    for row in payload["rows"]:
        assert row["result"] == evaluate_case(row)


def test_exactly_one_deliberate_simulation_fail() -> None:
    rows = build_simulation_truth_matrix()["rows"]
    failures = [row for row in rows if row["result"] == "FAIL"]
    assert [row["case"] for row in failures] == [
        "counterfactual_one_byte_below_floor_permitted"
    ]


def test_historical_i09_evidence_hashes_unchanged() -> None:
    actual = {
        filename: _sha256(EVIDENCE_DIR / filename)
        for filename in HISTORICAL_I09_HASHES
    }
    assert actual == HISTORICAL_I09_HASHES


def test_builders_do_not_write_evidence() -> None:
    before = {
        path.name: _sha256(path)
        for path in EVIDENCE_DIR.glob("BLOC_04_I09R1*.json")
    }
    for builder_name, _ in BUILDERS:
        globals()[builder_name]()
    after = {
        path.name: _sha256(path)
        for path in EVIDENCE_DIR.glob("BLOC_04_I09R1*.json")
    }
    assert before == after
