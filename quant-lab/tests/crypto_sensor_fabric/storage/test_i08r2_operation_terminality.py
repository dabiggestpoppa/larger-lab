"""SENSOR-B4-I08R2B — real crash-ordering proofs for operation terminality.

These tests use the accepted real storage stack. They inject process death only
at the durable boundaries named by I08R2, restart with fresh engine/repository
instances, and assert the ORIGINAL operation/run is closed without repeating
its effect. Historical I08R1 matrices remain frozen and are not regenerated.
"""

from __future__ import annotations

import hashlib
import json
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
from crypto_sensor_fabric.storage.enums import StorageEncoding  # noqa: E402

_recovery_tests = load_sibling(
    "_i08r2_recovery_test_mod", "test_recovery"
)
Stack = _recovery_tests.Stack


class _FaultInjected(RuntimeError):
    """Deterministic process-death boundary."""


class _OwnerRepo:
    def __init__(self) -> None:
        self._lock_owners: dict[str, dict[str, Any]] = {}
        self._job_locks: dict[str, threading.RLock] = {}

    def lock_for(self, job_id: str) -> threading.RLock:
        return self._job_locks.setdefault(job_id, threading.RLock())


def _blob_path(root: Path, sha: str) -> Path:
    from crypto_sensor_fabric.storage.paths import blob_object_key, resolve_under_root

    return resolve_under_root(root, blob_object_key(sha, StorageEncoding.NONE))


def _corrupt_plan(stack: Stack) -> tuple[str, rec.RecoveryPlanAction, Any]:
    sha = stack.seed_blob(b"valid evidence", acq_id="acq-terminality")
    _blob_path(stack.root, sha).write_bytes(b"tampered terminality bytes")
    engine = stack.engine("run-terminality")
    result = engine.scan(recovery_run_id="run-terminality")
    planned = next(
        action
        for action in result.planned_actions
        if action.action_kind == rec._ACTION_QUARANTINE_CORRUPT_BLOB
    )
    focused = rec.RecoveryScanResult(
        recovery_run_id=result.recovery_run_id,
        findings=result.findings,
        counts_by_problem=result.counts_by_problem,
        has_blockers=result.has_blockers,
        planned_actions=(planned,),
    )
    return sha, planned, focused


def _operation_rows(
    engine: rec.RecoveryEngine, object_type: str, object_id: str
) -> list[dict[str, Any]]:
    return engine.operations.list_for_object(object_type, object_id)


def _assert_terminal(
    engine: rec.RecoveryEngine,
    object_type: str,
    object_id: str,
    run_id: str,
    action_id: str,
) -> None:
    rows = _operation_rows(engine, object_type, object_id)
    assert {row["phase"] for row in rows} >= {
        "INTENT",
        "EFFECT_COMMITTED",
        "COMPLETED",
    }
    terminal = [row for row in rows if row["phase"] == "COMPLETED"]
    assert len(terminal) == 1
    assert terminal[0]["recovery_run_id"] == run_id
    assert terminal[0]["final_action_id"] == action_id
    actions = engine.journal.list_for_object(object_type, object_id)
    assert [row["recovery_action_id"] for row in actions] == [action_id]


def test_quarantine_effect_without_action_replays_original_operation(
    tmp_path: Path,
) -> None:
    stack = Stack(tmp_path)
    sha, planned, result = _corrupt_plan(stack)
    engine = stack.engine("run-a")
    real_journal_action = engine._journal_action

    def die_before_action(**kwargs: Any) -> None:
        raise _FaultInjected("death after EFFECT, before final action")

    engine._journal_action = die_before_action  # type: ignore[method-assign]
    with pytest.raises(_FaultInjected):
        engine.apply_plan(result, recovery_run_id="run-a")
    engine._journal_action = real_journal_action  # type: ignore[method-assign]
    assert {row["phase"] for row in _operation_rows(engine, "EVIDENCE_BLOB", sha)} == {
        "INTENT",
        "EFFECT_COMMITTED",
    }, [(action.action_kind, action.object_type, action.object_id) for action in result.planned_actions]
    assert engine.journal.list_for_object("EVIDENCE_BLOB", sha) == []

    restarted = Stack(tmp_path).engine("run-b")
    restarted.apply_plan(
        restarted.scan(recovery_run_id="run-b"), recovery_run_id="run-b"
    )
    rows = _operation_rows(restarted, "EVIDENCE_BLOB", sha)
    assert {row["recovery_run_id"] for row in rows} == {"run-a"}
    assert len([row for row in rows if row["phase"] == "COMPLETED"]) == 1
    actions = restarted.journal.list_for_object("EVIDENCE_BLOB", sha)
    assert len(actions) == 1
    _assert_terminal(
        restarted, "EVIDENCE_BLOB", sha, "run-a", actions[0]["recovery_action_id"]
    )
    assert not _blob_path(tmp_path, sha).exists()
    quarantined = list((tmp_path / "quarantine" / "integrity").iterdir())
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() == b"tampered terminality bytes"
    del planned


def test_action_without_terminal_is_adopted_not_duplicated(
    tmp_path: Path,
) -> None:
    stack = Stack(tmp_path)
    sha, _planned, result = _corrupt_plan(stack)
    engine = stack.engine("run-action")
    real_outcome = engine._record_outcome

    def die_before_terminal(*args: Any, **kwargs: Any) -> None:
        raise _FaultInjected("death after final action, before terminal phase")

    engine._record_outcome = die_before_terminal  # type: ignore[method-assign]
    with pytest.raises(_FaultInjected):
        engine.apply_plan(result, recovery_run_id="run-action")
    engine._record_outcome = real_outcome  # type: ignore[method-assign]
    before = engine.journal.list_for_object("EVIDENCE_BLOB", sha)
    assert len(before) == 1
    action_id = before[0]["recovery_action_id"]
    assert {row["phase"] for row in _operation_rows(engine, "EVIDENCE_BLOB", sha)} == {
        "INTENT",
        "EFFECT_COMMITTED",
    }

    restarted = Stack(tmp_path).engine("run-restart")
    restarted.apply_plan(
        restarted.scan(recovery_run_id="run-restart"),
        recovery_run_id="run-restart",
    )
    after = restarted.journal.list_for_object("EVIDENCE_BLOB", sha)
    assert [row["recovery_action_id"] for row in after] == [action_id]
    _assert_terminal(
        restarted, "EVIDENCE_BLOB", sha, "run-action", action_id
    )


def test_terminal_without_named_action_fails_closed(tmp_path: Path) -> None:
    stack = Stack(tmp_path)
    engine = stack.engine("run-corrupt")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="lock-corrupt",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="record only",
        before_state={"relative_path": "locks/lock-corrupt.lock"},
    )
    op_id = engine._record_intent(planned, "run-corrupt")
    engine._record_outcome(
        op_id,
        planned,
        "run-corrupt",
        resolution="COMPLETED: forged terminal without an action",
        final_action_id="f" * 64,
    )
    restarted = Stack(tmp_path).engine("run-restart")
    with pytest.raises(rec.RecoveryOperationCorrupt, match="NOT durable"):
        restarted.apply_plan(
            restarted.scan(recovery_run_id="run-restart"),
            recovery_run_id="run-restart",
        )


def test_both_terminal_phases_fail_closed(tmp_path: Path) -> None:
    stack = Stack(tmp_path)
    engine = stack.engine("run-both")
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_RECORD_LOCK_ONLY,
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="lock-both",
        problem=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="record only",
        before_state={"relative_path": "locks/lock-both.lock"},
    )
    op_id = engine._record_intent(planned, "run-both")
    action_id, _ = engine.journal.record(
        recovery_run_id="run-both",
        object_type=planned.object_type,
        object_id=planned.object_id,
        problem=planned.problem,
        resolution="completed",
        before_state=planned.before_state,
        after_state={"done": True},
        action_kind=planned.action_kind,
    )
    engine._record_outcome(
        op_id,
        planned,
        "run-both",
        resolution="COMPLETED: first terminal",
        final_action_id=action_id,
    )
    engine._record_outcome(
        op_id,
        planned,
        "run-both",
        resolution="UNRESOLVED: contradictory terminal",
        final_action_id=action_id,
    )
    restarted = Stack(tmp_path).engine("run-restart")
    with pytest.raises(rec.RecoveryOperationCorrupt, match="BOTH terminal"):
        restarted.apply_plan(
            restarted.scan(recovery_run_id="run-restart"),
            recovery_run_id="run-restart",
        )


def _make_lock(root: Path, job_id: str) -> tuple[str, Path]:
    lock_id = hashlib.sha256(job_id.encode("utf-8")).hexdigest()
    path = root / "locks" / f"{lock_id}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stale\n")
    return lock_id, path


def test_lock_unlink_without_effect_replays_original_operation(
    tmp_path: Path,
) -> None:
    stack = Stack(tmp_path)
    job_id = "job-lock-replay"
    lock_id, lock_path = _make_lock(tmp_path, job_id)
    engine = stack.engine("lock-run-a")
    owner = _OwnerRepo()
    real_effect = engine._record_effect

    def die_after_unlink(*args: Any, **kwargs: Any) -> None:
        raise _FaultInjected("death after unlink, before EFFECT")

    engine._record_effect = die_after_unlink  # type: ignore[method-assign]
    with pytest.raises(_FaultInjected):
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="lock-run-a",
        )
    engine._record_effect = real_effect  # type: ignore[method-assign]
    assert not lock_path.exists()
    assert {row["phase"] for row in _operation_rows(engine, rec.SEMANTIC_JOB_LOCK, lock_id)} == {
        "INTENT"
    }
    assert engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id) == []

    restarted = Stack(tmp_path).engine("lock-run-b")
    restarted.apply_plan(
        restarted.scan(recovery_run_id="lock-run-b"),
        recovery_run_id="lock-run-b",
    )
    rows = _operation_rows(restarted, rec.SEMANTIC_JOB_LOCK, lock_id)
    assert {row["recovery_run_id"] for row in rows} == {"lock-run-a"}
    actions = restarted.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert len(actions) == 1
    assert json.loads(actions[0]["after_state"]) == {
        "lock_present": False,
        "cleared": True,
        "replayed": True,
    }
    _assert_terminal(
        restarted, rec.SEMANTIC_JOB_LOCK, lock_id, "lock-run-a",
        actions[0]["recovery_action_id"],
    )


def test_lock_ownership_revalidated_immediately_after_intent(
    tmp_path: Path,
) -> None:
    stack = Stack(tmp_path)
    job_id = "job-lock-owner-race"
    lock_id, lock_path = _make_lock(tmp_path, job_id)
    engine = stack.engine("lock-race")
    owner = _OwnerRepo()
    real_intent = engine._record_intent

    def record_then_acquire(*args: Any, **kwargs: Any) -> str:
        op_id = real_intent(*args, **kwargs)
        owner._lock_owners[job_id] = {"thread": "raced", "depth": 1}
        return op_id

    engine._record_intent = record_then_acquire  # type: ignore[method-assign]
    with pytest.raises(rec.RecoveryPlanConflict, match="LIVE in-process owner"):
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="lock-race",
        )
    assert lock_path.exists()
    assert len(_operation_rows(engine, rec.SEMANTIC_JOB_LOCK, lock_id)) == 1
    assert engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id) == []
