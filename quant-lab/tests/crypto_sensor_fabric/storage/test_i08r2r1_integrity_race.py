"""SENSOR-B4-I08R2R1B — lock-race and canonical-record microseal tests."""

from __future__ import annotations

import copy
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _p in (str(_SRC), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import recovery as rec  # noqa: E402

_recovery = load_sibling("_i08r2r1_b_recovery_mod", "test_recovery")
_truth = load_sibling("_i08r2r1_b_truth_mod", "test_i08r2_evidence")
Stack = _recovery.Stack


class _OwnerRepo:
    def __init__(self) -> None:
        self._lock_owners: dict[str, dict[str, Any]] = {}
        self._job_locks: dict[str, threading.RLock] = {}

    def lock_for(self, job_id: str) -> threading.RLock:
        return self._job_locks.setdefault(job_id, threading.RLock())


def _empty(engine: rec.RecoveryEngine, run_id: str) -> None:
    engine.apply_plan(
        rec.RecoveryScanResult(
            recovery_run_id=run_id,
            findings=(),
            counts_by_problem={},
            has_blockers=False,
            planned_actions=(),
        ),
        recovery_run_id=run_id,
    )


def measure_lock_clear_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """Measure a contender at both irreversible clear boundaries."""
    stack = Stack(tmp_path)
    job_id = "job-final-boundary-race"
    lock_id, lock_path = _truth._lock(tmp_path, job_id)
    owner = _OwnerRepo()
    engine = stack.engine("lock-boundary")
    attempts: list[str] = []
    acquired: list[bool] = []

    def contend() -> None:
        def attempt() -> None:
            gate = owner.lock_for(job_id)
            got = gate.acquire(blocking=False)
            acquired.append(got)
            if got:
                owner._lock_owners[job_id] = {
                    "thread": "contender",
                    "depth": 1,
                }
                owner._lock_owners.pop(job_id, None)
                gate.release()

        thread = threading.Thread(target=attempt)
        thread.start()
        thread.join(5)
        assert not thread.is_alive()

    original_unlink = Path.unlink

    def unlink_boundary(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == lock_path:
            attempts.append("unlink")
            contend()
        return original_unlink(path, *args, **kwargs)

    original_fsync = rec.fsync_directory

    def fsync_boundary(path: Path) -> None:
        if path == lock_path.parent:
            attempts.append("fsync")
            contend()
        return original_fsync(path)

    monkeypatch.setattr(Path, "unlink", unlink_boundary)
    monkeypatch.setattr(rec, "fsync_directory", fsync_boundary)
    engine.clear_job_lock(
        lock_id,
        expected_job_id=job_id,
        owner_repository=owner,
        run_id="lock-boundary",
    )
    return {
        "unlink_attempted": "unlink" in attempts,
        "fsync_attempted": "fsync" in attempts,
        "contender_acquisitions": acquired,
        "lock_absent": not lock_path.exists(),
        "owner_map_empty": not owner._lock_owners,
    }


def test_clear_holds_job_authority_through_unlink_and_fsync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    measured = measure_lock_clear_race(tmp_path, monkeypatch)
    assert measured == {
        "unlink_attempted": True,
        "fsync_attempted": True,
        "contender_acquisitions": [False, False],
        "lock_absent": True,
        "owner_map_empty": True,
    }


def test_operation_timestamp_requires_zero_utc_offset(tmp_path: Path) -> None:
    intent, _effect = _truth._canonical_payloads(tmp_path / "timestamps")
    accepted = copy.deepcopy(intent)
    rec.validate_operation_record(accepted)
    for value in (
        "2026-01-01T00:00:00",
        "2026-01-01T05:00:00+05:00",
    ):
        payload = copy.deepcopy(intent)
        payload["registered_at"] = value
        with pytest.raises(rec.RecoveryOperationCorrupt):
            rec.validate_operation_record(payload)


@pytest.mark.parametrize("field_name", ["before_state", "after_state"])
def test_malformed_state_json_is_typed_corruption(
    tmp_path: Path, field_name: str
) -> None:
    intent, _effect = _truth._canonical_payloads(tmp_path / field_name)
    payload = copy.deepcopy(intent)
    payload[field_name] = "{malformed"
    with pytest.raises(rec.RecoveryOperationCorrupt):
        rec.validate_operation_record(payload)


def test_terminal_rejects_same_coarse_tuple_with_wrong_action_semantics(
    tmp_path: Path,
) -> None:
    root = tmp_path / "wrong-final-action"
    root.mkdir(parents=True)
    stack = Stack(root)
    engine = stack.engine("wrong-final")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="wrong-final",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="planned resolution",
        before_state={"relative_path": "locks/wrong-final.lock"},
    )
    engine._record_intent(planned, "wrong-final")
    action_id, _ = engine.journal.record(
        recovery_run_id="wrong-final",
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution="DIVERGENT final resolution",
        before_state=planned.before_state,
        after_state={"claimed": "wrong"},
        action_kind=planned.action_kind,
    )
    # Forge the terminal row directly to model a previously-written
    # catalog that points at an independently constructed action. The
    # production writer now refuses this earlier, but restart must also
    # reject the durable shape.
    action = engine.journal.get(action_id)
    assert action is not None
    engine.operations.record_phase(
        recovery_run_id="wrong-final",
        action_kind=planned.action_kind,
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution=planned.resolution,
        before_state=planned.before_state,
        phase=rec.RecoveryOperationJournal.PHASE_COMPLETED,
        detail="COMPLETED: divergent final action",
        final_action_id=action_id,
        final_outcome=rec._canonical(
            {
                "recovery_run_id": action["recovery_run_id"],
                "action_kind": action["action_kind"],
                "object_type": action["object_type"],
                "object_id": action["object_id"],
                "problem": action["problem"],
                "resolution": action["resolution"],
                "before_state": rec._parse_state_field(action["before_state"]),
                "after_state": rec._parse_state_field(action["after_state"]),
            }
        ),
    )
    restarted = Stack(root).engine("wrong-final-restart")
    with pytest.raises(rec.RecoveryOperationCorrupt, match="exact operation_id"):
        _empty(restarted, "wrong-final-restart")


def test_terminal_rejects_divergent_outcome_from_exact_bound_action(
    tmp_path: Path,
) -> None:
    root = tmp_path / "divergent-final-outcome"
    root.mkdir(parents=True)
    stack = Stack(root)
    engine = stack.engine("divergent-final")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="divergent-final",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="planned resolution",
        before_state={"relative_path": "locks/divergent-final.lock"},
    )
    op_id = engine._record_intent(planned, "divergent-final")
    action_id, _ = engine.journal.record(
        recovery_run_id="divergent-final",
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution="DIVERGENT durable action resolution",
        before_state=planned.before_state,
        after_state={"actual": "divergent"},
        action_kind=planned.action_kind,
        operation_id=op_id,
    )
    # Even an exactly operation-bound action cannot satisfy a terminal row
    # whose claimed full outcome diverges from the action's durable semantics.
    engine.operations.record_phase(
        recovery_run_id="divergent-final",
        action_kind=planned.action_kind,
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution=planned.resolution,
        before_state=planned.before_state,
        phase=rec.RecoveryOperationJournal.PHASE_COMPLETED,
        detail="COMPLETED: divergent final outcome claim",
        final_action_id=action_id,
        final_outcome=rec._canonical(
            {
                "recovery_run_id": "divergent-final",
                "action_kind": planned.action_kind,
                "object_type": planned.object_type,
                "object_id": planned.object_id,
                "problem": planned.problem,
                "resolution": planned.resolution,
                "before_state": planned.before_state,
                "after_state": {"claimed": "not the durable action"},
            }
        ),
    )
    restarted = Stack(root).engine("divergent-final-restart")
    with pytest.raises(rec.RecoveryOperationCorrupt, match="does not exactly match"):
        _empty(restarted, "divergent-final-restart")
