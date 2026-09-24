"""SENSOR-B4-I08R2R1A — measured evidence truth and false-green counterfactual."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import recovery as rec  # noqa: E402

_r2 = load_sibling("_i08r2r1_truth_r2_mod", "test_i08r2_evidence")
_integrity = load_sibling(
    "_i08r2r1_truth_integrity_mod", "test_i08r2r1_integrity_race"
)
Stack = _r2.Stack
EVIDENCE_DIR = _r2.EVIDENCE_DIR

HISTORICAL_MATRIX_SHA256 = {
    "BLOC_04_I08_CRASH_MATRIX.json": "cc5c71694a9177314c2a872a28463c7c0d531a6805bc6a9f26083949f195d63f",
    "BLOC_04_I08_QUARANTINE_MATRIX.json": "4f501f64da491fb62003377fdd7999c35983b7f4119be70b44563bc713fcc9e0",
    "BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json": "7a82d6c52bd0acfd59e682684128d4f8c8b9f672ae7c7aa5399c303a57251913",
    "BLOC_04_I08_RECOVERY_SCAN_MATRIX.json": "8a288e8bbe6ddbd39a03480b08bc573e54b92a59b1cf08f72d8dc2817aabb237",
    "BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json": "d951399cfdb09e5164be8a38515744baf3ebb3f56f6b07c48fb23d79579d829d",
    "BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json": "21b0ea691448fbe16a00982838864c0e064c0187808c2f3d4fe09c398fb29e35",
    "BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json": "c71d06fe14f7c15137a8ae57529af51289cea4d1cbe823ce21e5976917efc8a8",
    "BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json": "4f2146f415dfc5fed3b6f5e71d57b2f7ff55af9d415046f70de2c84cc5d37c06",
    "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json": "a119bfa98367552ed77cc35015513532305a274d4c634df041c9cc65dd043713",
    "BLOC_04_I08R2_OPERATION_RECORD_INTEGRITY_MATRIX.json": "c3983023de941edc220abb51d6bb2a9095ab34b44e8b3a7c822bed40b712beb3",
    "BLOC_04_I08R2_OPERATION_TERMINALITY_MATRIX.json": "86625d2df8ea329df61420f29f56e070f40bbafb149ca917c6855946c1d40ba8",
}


def evaluate_case(case: dict[str, Any]) -> str:
    """Derive a matrix verdict only from its declared required invariants."""
    required = case.get("required_invariants")
    if not isinstance(required, list) or not required:
        raise AssertionError(f"case has no required_invariants: {case!r}")
    if len(required) != len(set(required)):
        raise AssertionError(f"case has duplicate required invariants: {case!r}")
    return (
        "OK"
        if all(case.get(invariant) is True for invariant in required)
        else "FAIL"
    )


def _case(payload: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(payload)


def test_corrected_r2_lock_scenarios_use_replay_report_truth(
    tmp_path: Path,
) -> None:
    matrix = _r2.measure_i08r2_lock_clear_atomicity_matrix(tmp_path)
    cases = {row["case"]: row for row in matrix["cases"]}
    crash = cases["crash_after_unlink_replays_original"]
    present = cases["present_lock_intent_not_false_completed"]

    assert crash["apply_return_is_not_replay_report"] is True
    assert crash["replay_closed"] is True
    assert evaluate_case(crash) == "OK"
    assert present["apply_return_is_not_replay_report"] is True
    assert present["no_action"] is True
    assert present["report_left_open"] is True
    assert evaluate_case(present) == "OK"


def test_required_predicate_counterfactual_emits_fail() -> None:
    payload = {
        "case": "counterfactual_required_predicate_false",
        "completed": True,
        "one_action": True,
        "replay_closed": False,
        "required_invariants": ["completed", "one_action", "replay_closed"],
        "result": "OK",
    }
    assert evaluate_case(payload) == "FAIL"
    payload["result"] = evaluate_case(payload)
    assert payload["result"] == "FAIL"


def test_meta_evaluator_rejects_missing_or_nonboolean_invariant() -> None:
    for required in ([], ["completed", "completed"]):
        try:
            evaluate_case(
                {"case": "invalid", "completed": True, "required_invariants": required}
            )
        except AssertionError:
            pass
        else:  # pragma: no cover - assertion contract
            raise AssertionError("invalid required invariant declaration accepted")

    missing = _case(
        {
            "case": "missing",
            "required_invariants": ["completed"],
            "result": "OK",
        }
    )
    assert evaluate_case(missing) == "FAIL"
    nonboolean = _case(
        {
            "case": "nonboolean",
            "completed": "true",
            "required_invariants": ["completed"],
            "result": "OK",
        }
    )
    assert evaluate_case(nonboolean) == "FAIL"


def _measured_case(
    name: str, required_invariants: list[str], **fields: Any
) -> dict[str, Any]:
    case = {
        "case": name,
        **fields,
        "required_invariants": required_invariants,
    }
    case["result"] = evaluate_case(case)
    return case


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _historical_hashes_preserved() -> bool:
    return all(
        _sha256(EVIDENCE_DIR / filename) == expected
        for filename, expected in HISTORICAL_MATRIX_SHA256.items()
    )


def build_i08r2r1_evidence_truth_matrix(tmp: Path) -> dict[str, Any]:
    corrected = _r2.measure_i08r2_lock_clear_atomicity_matrix(tmp / "live")
    corrected_rows = {row["case"]: row for row in corrected["cases"]}
    historical = json.loads(
        (
            EVIDENCE_DIR / "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
        ).read_text(encoding="utf-8")
    )
    historical_rows = {row["case"]: row for row in historical["cases"]}
    old_crash = historical_rows["crash_after_unlink_replays_original"]
    old_present = historical_rows["present_lock_intent_not_false_completed"]
    new_crash = copy.deepcopy(corrected_rows["crash_after_unlink_replays_original"])
    new_present = copy.deepcopy(
        corrected_rows["present_lock_intent_not_false_completed"]
    )
    new_crash["case"] = "corrected_crash_after_unlink_closes_from_replay_report"
    new_crash["result"] = evaluate_case(new_crash)
    new_present["case"] = "corrected_present_lock_stays_open_without_action"
    new_present["result"] = evaluate_case(new_present)
    counterfactual = copy.deepcopy(new_crash)
    counterfactual["case"] = "counterfactual_crash_replay_not_closed"
    counterfactual["replay_closed"] = False
    counterfactual["result"] = evaluate_case(counterfactual)

    cases = [
        _measured_case(
            "historical_crash_false_green_preserved",
            ["false_green_confirmed", "historical_bytes_preserved"],
            historical_result=old_crash["result"],
            historical_replay_closed=old_crash["replay_closed"],
            false_green_confirmed=(
                old_crash["result"] == "OK"
                and old_crash["replay_closed"] is False
            ),
            historical_sha256=_sha256(
                EVIDENCE_DIR
                / "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
            ),
            historical_bytes_preserved=(
                _sha256(
                    EVIDENCE_DIR
                    / "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
                )
                == HISTORICAL_MATRIX_SHA256[
                    "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
                ]
            ),
        ),
        _measured_case(
            "historical_present_lock_false_green_preserved",
            ["false_green_confirmed", "historical_bytes_preserved"],
            historical_result=old_present["result"],
            historical_no_action=old_present["no_action"],
            historical_report_left_open=old_present["report_left_open"],
            false_green_confirmed=(
                old_present["result"] == "OK"
                and old_present["no_action"] is False
                and old_present["report_left_open"] is False
            ),
            historical_bytes_preserved=(
                _sha256(
                    EVIDENCE_DIR
                    / "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
                )
                == HISTORICAL_MATRIX_SHA256[
                    "BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json"
                ]
            ),
        ),
        new_crash,
        new_present,
        counterfactual,
    ]
    return {
        "matrix": "BLOC_04_I08R2R1_EVIDENCE_TRUTH_MATRIX",
        "checkpoint": "SENSOR-B4-I08R2R1",
        "doctrine": (
            "A measured R2R1 row is OK only when every declared invariant is "
            "true; last_replay_report owns restart truth, while apply_plan's "
            "return lists only newly applied actions"
        ),
        "historical_matrix_sha256": dict(sorted(HISTORICAL_MATRIX_SHA256.items())),
        "cases": cases,
    }


def _measure_successful_clear(
    root: Path,
) -> tuple[list[str], bool, bool]:
    stack = Stack(root)
    job_id = "job-r2r1-order"
    lock_id, lock_path = _r2._lock(root, job_id)
    owner = _integrity._OwnerRepo()
    engine = stack.engine("lock-order")
    order: list[str] = []
    original_unlink = Path.unlink
    original_fsync = rec.fsync_directory

    def observe_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == lock_path:
            rows = engine.operations.list_for_object(
                rec.SEMANTIC_JOB_LOCK, lock_id
            )
            if any(row["phase"] == "INTENT" for row in rows):
                order.append("INTENT")
            order.append("UNLINK")
        return original_unlink(path, *args, **kwargs)

    def observe_fsync(path: Path) -> None:
        if path == lock_path.parent:
            order.append("FSYNC")
        return original_fsync(path)

    pytest_monkeypatch = pytest.MonkeyPatch()
    try:
        pytest_monkeypatch.setattr(Path, "unlink", observe_unlink)
        pytest_monkeypatch.setattr(rec, "fsync_directory", observe_fsync)
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="lock-order",
        )
    finally:
        pytest_monkeypatch.undo()
    rows = engine.operations.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    phases = {row["phase"] for row in rows}
    actions = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    if "EFFECT_COMMITTED" in phases:
        order.append("EFFECT")
    if actions:
        order.append("ACTION")
    if "COMPLETED" in phases:
        order.append("COMPLETED")
    return order, len(actions) == 1, not lock_path.exists()


def build_i08r2r1_lock_clear_race_matrix(tmp: Path) -> dict[str, Any]:
    pytest_monkeypatch = pytest.MonkeyPatch()
    try:
        race = _integrity.measure_lock_clear_race(
            tmp / "boundary", pytest_monkeypatch
        )
    finally:
        pytest_monkeypatch.undo()
    order, one_action, successful_lock_absent = _measure_successful_clear(
        tmp / "successful"
    )
    held_root = tmp / "held"
    held_stack = Stack(held_root)
    held_job = "job-r2r1-held"
    held_lock_id, held_path = _r2._lock(held_root, held_job)
    held_owner = _integrity._OwnerRepo()
    held_gate = held_owner.lock_for(held_job)
    held_ready = threading.Event()
    held_release = threading.Event()

    def hold_job_lock() -> None:
        assert held_gate.acquire(blocking=False)
        held_ready.set()
        assert held_release.wait(5)

    holder = threading.Thread(target=hold_job_lock)
    holder.start()
    assert held_ready.wait(5)
    held_refused = False
    try:
        held_stack.engine("lock-held").clear_job_lock(
            held_lock_id,
            expected_job_id=held_job,
            owner_repository=held_owner,
            run_id="lock-held",
        )
    except rec.RecoveryPlanConflict:
        held_refused = True
    finally:
        held_release.set()
        holder.join(5)
        assert not holder.is_alive()

    cases = [
        _measured_case(
            "contender_blocked_at_unlink_and_fsync",
            [
                "unlink_attempted",
                "fsync_attempted",
                "contender_never_acquired",
                "lock_absent",
                "owner_map_empty",
            ],
            **race,
            contender_never_acquired=(
                race["contender_acquisitions"] == [False, False]
            ),
        ),
        _measured_case(
            "successful_clear_exact_durable_order",
            ["exact_order", "lock_absent", "one_action"],
            observed_order=order,
            exact_order=(
                order
                == ["INTENT", "UNLINK", "FSYNC", "EFFECT", "ACTION", "COMPLETED"]
            ),
            lock_absent=successful_lock_absent,
            one_action=one_action,
        ),
        _measured_case(
            "held_job_rlock_refused_without_unlink",
            ["typed_refusal", "lock_intact"],
            typed_refusal=held_refused,
            lock_intact=held_path.exists(),
        ),
    ]
    return {
        "matrix": "BLOC_04_I08R2R1_LOCK_CLEAR_RACE_MATRIX",
        "checkpoint": "SENSOR-B4-I08R2R1",
        "doctrine": (
            "The same per-job RLock remains held across final owner-map "
            "validation, unlink, and directory fsync; a contender can be "
            "refused but can never become a live owner under an unlink"
        ),
        "cases": cases,
    }


def _rejected(call: Any) -> bool:
    try:
        call()
    except rec.RecoveryOperationCorrupt:
        return True
    return False


def _coarse_action_rejected(root: Path) -> bool:
    root.mkdir(parents=True)
    stack = Stack(root)
    engine = stack.engine("coarse-action")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="coarse-action",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="planned",
        before_state={"relative_path": "locks/coarse-action.lock"},
    )
    engine._record_intent(planned, "coarse-action")
    action_id, _ = engine.journal.record(
        recovery_run_id="coarse-action",
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution="DIVERGENT",
        before_state=planned.before_state,
        after_state={"divergent": True},
        action_kind=planned.action_kind,
    )
    action = engine.journal.get(action_id)
    assert action is not None
    engine.operations.record_phase(
        recovery_run_id="coarse-action",
        action_kind=planned.action_kind,
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution=planned.resolution,
        before_state=planned.before_state,
        phase=rec.RecoveryOperationJournal.PHASE_COMPLETED,
        detail="forged coarse action",
        final_action_id=action_id,
        final_outcome=rec._canonical(
            {
                "recovery_run_id": "coarse-action",
                "action_kind": planned.action_kind,
                "object_type": planned.object_type,
                "object_id": planned.object_id,
                "problem": planned.problem,
                "resolution": "DIVERGENT",
                "before_state": planned.before_state,
                "after_state": {"divergent": True},
            }
        ),
    )
    restarted = Stack(root).engine("coarse-restart")
    return _rejected(lambda: _integrity._empty(restarted, "coarse-restart"))


def _divergent_bound_outcome_rejected(root: Path) -> bool:
    root.mkdir(parents=True)
    stack = Stack(root)
    engine = stack.engine("bound-action")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="bound-action",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="planned",
        before_state={"relative_path": "locks/bound-action.lock"},
    )
    op_id = engine._record_intent(planned, "bound-action")
    action_id, _ = engine.journal.record(
        recovery_run_id="bound-action",
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution="actual divergent action",
        before_state=planned.before_state,
        after_state={"actual": True},
        action_kind=planned.action_kind,
        operation_id=op_id,
    )
    engine.operations.record_phase(
        recovery_run_id="bound-action",
        action_kind=planned.action_kind,
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution=planned.resolution,
        before_state=planned.before_state,
        phase=rec.RecoveryOperationJournal.PHASE_COMPLETED,
        detail="forged divergent outcome",
        final_action_id=action_id,
        final_outcome=rec._canonical(
            {
                "recovery_run_id": "bound-action",
                "action_kind": planned.action_kind,
                "object_type": planned.object_type,
                "object_id": planned.object_id,
                "problem": planned.problem,
                "resolution": planned.resolution,
                "before_state": planned.before_state,
                "after_state": {"claimed": True},
            }
        ),
    )
    restarted = Stack(root).engine("bound-restart")
    return _rejected(lambda: _integrity._empty(restarted, "bound-restart"))


def build_i08r2r1_canonical_record_matrix(tmp: Path) -> dict[str, Any]:
    intent, _effect = _r2._canonical_payloads(tmp / "canonical")
    canonical_utc = copy.deepcopy(intent)
    canonical_utc["registered_at"] = "2026-01-01T00:00:00+00:00"
    accepted = (
        _rejected(lambda: rec.validate_operation_record(canonical_utc)) is False
    )
    naive = copy.deepcopy(canonical_utc)
    naive["registered_at"] = "2026-01-01T00:00:00"
    non_utc = copy.deepcopy(canonical_utc)
    non_utc["registered_at"] = "2026-01-01T05:00:00+05:00"
    malformed_results: dict[str, bool] = {}
    for field_name in ("before_state", "after_state"):
        malformed = copy.deepcopy(intent)
        malformed[field_name] = "{malformed"
        malformed_results[field_name] = _rejected(
            lambda payload=malformed: rec.validate_operation_record(payload)
        )
    cases = [
        _measured_case(
            "canonical_zero_utc_accepted",
            ["typed_validation"],
            registered_at=canonical_utc["registered_at"],
            typed_validation=accepted,
        ),
        _measured_case(
            "naive_timestamp_rejected",
            ["typed_corruption"],
            typed_corruption=_rejected(
                lambda: rec.validate_operation_record(naive)
            ),
        ),
        _measured_case(
            "aware_non_utc_timestamp_rejected",
            ["typed_corruption"],
            registered_at=non_utc["registered_at"],
            typed_corruption=_rejected(
                lambda: rec.validate_operation_record(non_utc)
            ),
        ),
        _measured_case(
            "malformed_before_state_rejected",
            ["typed_corruption"],
            typed_corruption=malformed_results["before_state"],
        ),
        _measured_case(
            "malformed_after_state_rejected",
            ["typed_corruption"],
            typed_corruption=malformed_results["after_state"],
        ),
        _measured_case(
            "coarse_tuple_wrong_action_rejected",
            ["typed_corruption"],
            same_coarse_tuple=True,
            divergent_resolution=True,
            divergent_after_state=True,
            typed_corruption=_coarse_action_rejected(tmp / "coarse"),
        ),
        _measured_case(
            "exact_bound_action_with_divergent_outcome_rejected",
            ["typed_corruption"],
            exact_operation_binding=True,
            claimed_outcome_matches_action=False,
            typed_corruption=_divergent_bound_outcome_rejected(
                tmp / "divergent"
            ),
        ),
    ]
    return {
        "matrix": "BLOC_04_I08R2R1_CANONICAL_RECORD_MATRIX",
        "checkpoint": "SENSOR-B4-I08R2R1",
        "doctrine": (
            "Durable operation rows require zero-offset UTC, typed state "
            "parsing, exact operation binding, and a canonical full outcome "
            "equal to the named final RecoveryAction"
        ),
        "cases": cases,
    }


R2R1_BUILDERS = [
    (
        build_i08r2r1_evidence_truth_matrix,
        "BLOC_04_I08R2R1_EVIDENCE_TRUTH_MATRIX.json",
    ),
    (
        build_i08r2r1_lock_clear_race_matrix,
        "BLOC_04_I08R2R1_LOCK_CLEAR_RACE_MATRIX.json",
    ),
    (
        build_i08r2r1_canonical_record_matrix,
        "BLOC_04_I08R2R1_CANONICAL_RECORD_MATRIX.json",
    ),
]


@pytest.mark.parametrize("builder,filename", R2R1_BUILDERS)
def test_r2r1_generated_matches_committed(
    builder: Any, filename: str, tmp_path: Path
) -> None:
    generated = json.dumps(
        builder(tmp_path / builder.__name__), indent=2, sort_keys=True
    ).encode("utf-8")
    assert generated == (EVIDENCE_DIR / filename).read_bytes()


@pytest.mark.parametrize("filename", [name for _builder, name in R2R1_BUILDERS])
def test_every_committed_r2r1_row_derives_result_from_required_invariants(
    filename: str,
) -> None:
    matrix = json.loads((EVIDENCE_DIR / filename).read_text(encoding="utf-8"))
    assert matrix["cases"]
    for row in matrix["cases"]:
        assert row["result"] == evaluate_case(row), row["case"]


def test_historical_i08_i08r1_i08r2_matrix_hashes_are_preserved() -> None:
    assert _historical_hashes_preserved()


def test_r2r1_builders_do_not_touch_historical_matrix_bytes(
    tmp_path: Path,
) -> None:
    before = {
        filename: _sha256(EVIDENCE_DIR / filename)
        for filename in HISTORICAL_MATRIX_SHA256
    }
    for builder, _filename in R2R1_BUILDERS:
        builder(tmp_path / builder.__name__)
    after = {
        filename: _sha256(EVIDENCE_DIR / filename)
        for filename in HISTORICAL_MATRIX_SHA256
    }
    assert after == before == HISTORICAL_MATRIX_SHA256
