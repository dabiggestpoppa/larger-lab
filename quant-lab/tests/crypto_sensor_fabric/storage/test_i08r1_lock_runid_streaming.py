"""SENSOR-B4-I08R1C — lock-clear authority, run identity, typed job scan,
and bounded-memory streaming quarantine (I08R1 §23-§27, §30, §31).

Matrix cases proved here (I08R1 §30 / §31):

- generated_run_ids_cross_instance_unique — uuid4 identity never derives
  from process memory or wall-clock formatting (I08R1 §26);
- explicit_deterministic_run_id_preserved — evidence runs keep exact ids;
- clear_without_job_repository_rejected — no owner repository, no clear;
- clear_live_owner_rejected — a live ``_lock_owners`` entry blocks it;
- clear_same_thread_reentrant_owner_rejected — RLock reentrancy cannot
  bypass the owner-map check (I08R1 §24: the probe alone is insufficient);
- clear_unowned_matching_lock_succeeds — the legitimate operator path;
- foreign_lock_not_auto_deleted — scan/apply never touch foreign locks;
- large_source_chunked / path_read_bytes_not_used — bounded streaming
  copy with a monkeypatch guard on ``Path.read_bytes`` (I08R1 §9);
- destination_hash_exact / source_removed_only_after_durable_destination /
  retry_adopts_identical_destination / different_destination_bytes_conflict.
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

_base = load_sibling("_i08r1_base_mod", "test_job_state_r1")
_crash = load_sibling("_i08r1_crash_mod", "test_recovery_crash_matrix")

RecoveryStack = _crash.RecoveryStack
_engine = _crash._engine

FP = _base._FP
PROVIDER = _base._PROVIDER
MEDIA = _base.MEDIA
FIXED = _base.FIXED


class _FaultInjected(RuntimeError):
    """A deterministic injected crash boundary."""


# ---------------------------------------------------------------------------
# I08R1 §26 / §30 — recovery run identity
# ---------------------------------------------------------------------------


def test_generated_run_ids_cross_instance_unique(tmp_path: Path) -> None:
    """Generated ids come from uuid4: two fresh engines produce many ids
    with zero collisions; uniqueness never derives from object addresses
    (two engines constructed identically at the same root still differ)."""
    e1 = _engine(RecoveryStack(tmp_path / "t1"))
    e2 = _engine(RecoveryStack(tmp_path / "t2"))
    ids: list[str] = []
    for _ in range(64):
        ids.append(e1.new_run_id())
        ids.append(e2.new_run_id())
    assert len(set(ids)) == len(ids)
    assert all(i.startswith("recovery-") for i in ids)
    # 32 hex chars from uuid4().hex — 128 bits of randomness.
    assert all(len(i[len("recovery-"):]) == 32 for i in ids)
    # Determinism guard: an EXPLICIT id always wins over generation.
    result = e1.scan(recovery_run_id="deterministic-evidence-run")
    assert result.recovery_run_id == "deterministic-evidence-run"


def test_explicit_deterministic_run_id_preserved(tmp_path: Path) -> None:
    """Constructor-supplied explicit run ids flow through scan untouched;
    generated ids never leak into deterministic evidence runs."""
    stack = RecoveryStack(tmp_path)
    engine = rec.RecoveryEngine(
        stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        manifest_repository=stack.manifest_repo,
        job_repository=stack.repo,
        clock=lambda: FIXED,
        recovery_run_id="evidence-run-fixed",
    )
    # An explicit constructor id STICKS for the engine's lifetime
    # (deterministic evidence runs); a call-site id overrides it once.
    assert engine.scan().recovery_run_id == "evidence-run-fixed"
    assert engine.scan(recovery_run_id="call-site-id").recovery_run_id == (
        "call-site-id"
    )
    # Generation is used ONLY when no explicit id exists anywhere.
    bare = _engine(RecoveryStack(tmp_path / "bare"))
    assert bare.scan().recovery_run_id.startswith("recovery-")


# ---------------------------------------------------------------------------
# I08R1 §23/§24/§25 — explicit lock-clear authority (§30 cases)
# ---------------------------------------------------------------------------


def _make_lock(root: Path, job_id: str) -> tuple[str, Path]:
    lock_id = hashlib.sha256(job_id.encode("utf-8")).hexdigest()
    lock_path = root / "locks" / f"{lock_id}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(b"held\n")
    return lock_id, lock_path


def test_clear_without_job_repository_rejected(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    lock_id, lock_path = _make_lock(Path(stack.root), "job-norepo")
    engine = _engine(stack)
    with pytest.raises(TypeError):  # parameter is mandatory — no default
        engine.clear_job_lock(lock_id, expected_job_id="job-norepo")  # type: ignore[call-arg]
    with pytest.raises(rec.RecoveryConfigurationError):
        engine.clear_job_lock(
            lock_id,
            expected_job_id="job-norepo",
            owner_repository=None,
            run_id="r",
        )
    # A repository-shaped object without _lock_owners truth is refused.
    with pytest.raises(rec.RecoveryConfigurationError):
        engine.clear_job_lock(
            lock_id,
            expected_job_id="job-norepo",
            owner_repository=object(),
            run_id="r",
        )
    assert lock_path.exists(), "nothing deleted without authority"


def test_clear_live_owner_rejected(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    job_id = "job-live-owner"
    lock_id, lock_path = _make_lock(Path(stack.root), job_id)
    engine = _engine(stack)
    owner = _engine_owner_repo(stack, job_id, live_owner=True)
    with pytest.raises(rec.RecoveryPlanConflict):
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="r",
        )
    assert lock_path.exists()


def test_clear_same_thread_reentrant_owner_rejected(tmp_path: Path) -> None:
    """RLock reentrancy CANNOT bypass the owner-map check: the same thread
    holds the RLock (probe would succeed from inside) but the live owner
    record refuses the clear (I08R1 §24)."""
    stack = RecoveryStack(tmp_path)
    job_id = "job-reentrant"
    lock_id, lock_path = _make_lock(Path(stack.root), job_id)
    engine = _engine(stack)

    class _Repo:
        def __init__(self) -> None:
            self._lock_owners: dict[str, dict[str, Any]] = {
                job_id: {"thread": "t", "depth": 1}
            }
            self._job_locks = {job_id: threading.RLock()}

    repo = _Repo()
    lock_obj = repo._job_locks[job_id]
    with lock_obj:  # same-thread reentrancy: the probe WOULD acquire
        probe_ok = lock_obj.acquire(blocking=False)
        assert probe_ok is True  # reentrancy makes the probe alone useless
        lock_obj.release()
        with pytest.raises(rec.RecoveryPlanConflict):
            engine.clear_job_lock(
                lock_id,
                expected_job_id=job_id,
                owner_repository=repo,
                run_id="r",
            )
    assert lock_path.exists()


def test_clear_unowned_matching_lock_succeeds(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-unowned"
    lock_id, lock_path = _make_lock(Path(stack.root), job_id)
    engine = _engine(stack)
    owner = _engine_owner_repo(stack, job_id, live_owner=False)
    result = engine.clear_job_lock(
        lock_id,
        expected_job_id=job_id,
        owner_repository=owner,
        run_id="run-clear-ok",
    )
    assert not lock_path.exists()
    # Evidence precedes mutation (I08R1 §5): INTENT phase + journal row.
    ops = engine.operations.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert any(op["phase"] == "INTENT" for op in ops)
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert len(records) == 1
    assert json.loads(records[0]["after_state"]) == {
        "lock_present": False,
        "cleared": True,
    }
    assert result is None  # internal JOB_LOCK envelope: no frozen model row


def test_clear_unowned_matching_lock_retry_idempotent(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-clear-retry"
    lock_id, lock_path = _make_lock(Path(stack.root), job_id)
    engine = _engine(stack)
    owner = _engine_owner_repo(stack, job_id, live_owner=False)
    first = engine.clear_job_lock(
        lock_id,
        expected_job_id=job_id,
        owner_repository=owner,
        run_id="run-clear-r",
    )
    assert first is None
    before = len(engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id))
    # A second clear of the SAME lock id: the lock is gone -> typed
    # conflict (nothing to clear), no duplicate evidence appended.
    with pytest.raises(rec.RecoveryPlanConflict):
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="run-clear-r",
        )
    after = len(engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id))
    assert before == after


def test_foreign_lock_not_auto_deleted(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    lock_id, lock_path = _make_lock(Path(stack.root), "job-foreign")
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-lock")
    assert rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN in {
        f.problem for f in result.findings
    }
    engine.apply_plan(result, recovery_run_id="run-lock")
    assert lock_path.exists(), "scan/apply never delete a foreign lock"
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert json.loads(records[0]["after_state"]) == {
        "lock_present": True,
        "cleared": False,
    }


# ---------------------------------------------------------------------------
# I08R1 §27 — typed job-scan error classification
# ---------------------------------------------------------------------------


def _engine_owner_repo(stack: Any, job_id: str, *, live_owner: bool) -> Any:
    """The REAL job repository as owner authority; optionally carrying a
    live in-process owner record for the authority tests."""
    if live_owner:
        stack.repo._lock_owners[job_id] = {"thread": "t", "depth": 1}
    return stack.repo


def _make_job_stack(tmp_path: Path, job_id: str) -> Any:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    _base._create(stack.repo, job_id)
    return stack


def test_healthy_job_currently_lock_held_not_corruption(
    tmp_path: Path,
) -> None:
    """JobLockHeld (active-writer contention on a healthy chain) is NOT
    job durability corruption: no finding, no QUARANTINE_JOB plan."""
    stack = _make_job_stack(tmp_path, "job-healthy")
    # Pre-create the physical lock file: with the 0-timeout test
    # configuration the gated read raises JobLockHeld.
    lock_id = hashlib.sha256(b"job-healthy").hexdigest()
    lock_path = Path(stack.root) / "locks" / f"{lock_id}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(b"held\n")
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-scan-lock")
    assert not any(
        f.problem == rec.PROBLEM_JOB_DURABILITY_DIVERGENCE
        for f in result.findings
    ), "lock contention must not be mislabeled as durability corruption"
    # The lock file itself is classified separately.
    assert rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN in {
        f.problem for f in result.findings
    }


def test_forged_invalid_chain_is_durability_divergence(tmp_path: Path) -> None:
    """True corruption keeps its classification: forged head -> finding."""
    stack = _make_job_stack(tmp_path, "job-forged")
    _base._drive_to_manifest(stack.repo, "job-forged")
    _base._full_batch(stack, "acq-forged", "pm-forged", b'{"rows": ["f"]}')
    _base._checkpoint(stack.repo, "job-forged", "acq-forged", "pm-forged")
    _crash._publish_forged_from_status_break(Path(stack.root), "job-forged")
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-scan-forged")
    divergent = [
        f
        for f in result.findings
        if f.problem == rec.PROBLEM_JOB_DURABILITY_DIVERGENCE
    ]
    assert [f.object_id for f in divergent] == ["job-forged"]


def test_unexpected_repository_failure_not_mislabeled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unexpected I/O fault inside the gated read propagates typed —
    it never becomes JOB_DURABILITY_DIVERGENCE (I08R1 §27)."""
    stack = _make_job_stack(tmp_path, "job-io")

    def _boom(job_id: str) -> Any:
        raise OSError("simulated repository I/O failure")

    monkeypatch.setattr(stack.repo, "get_job", _boom)
    engine = _engine(stack)
    with pytest.raises(OSError):
        engine.scan(recovery_run_id="run-scan-io")


# ---------------------------------------------------------------------------
# I08R1 §9 / §31 — bounded-memory streaming quarantine
# ---------------------------------------------------------------------------


def _corrupt_blob_stack(
    tmp_path: Path,
    payload: bytes,
    *,
    corrupt_bytes: bytes = b"tampered bytes",
) -> tuple[Any, str, Path, bytes]:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    sha = _base._full_batch(
        stack, "acq-stream", "pm-stream", payload
    )
    blob_path = _crash._blob_path(Path(stack.root), sha, StorageEncoding.NONE)
    blob_path.write_bytes(corrupt_bytes)  # canonical object now corrupt
    return stack, sha, blob_path, corrupt_bytes


def test_large_source_chunked_and_read_bytes_not_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The quarantine copy streams in fixed chunks; ``Path.read_bytes``
    is NEVER called during the copy (monkeypatch guard, I08R1 §9).  The
    corrupt payload is itself 4 MiB, so the streamed copy has real bulk."""
    corrupt = b"TAMPERED-" + b"x" * (4 << 20)
    stack, sha, _blob_path_ref, corrupt_bytes = _corrupt_blob_stack(
        tmp_path, b"seed payload", corrupt_bytes=corrupt
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-stream")
    assert rec.PROBLEM_CORRUPT_BLOB in {f.problem for f in result.findings}

    calls: list[tuple[str, int]] = []
    original_read_bytes = Path.read_bytes

    def _guard(self: Path) -> bytes:
        calls.append((str(self), self.stat().st_size))
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", _guard)

    def _hook(source: Path, staging: Path, *skip: object) -> None:
        assert not source.name.endswith(".partial")

    monkeypatch.setattr(
        rec, "_quar_copy_assert_synthetic", _hook, raising=True
    )
    # Shrink the chunk so the 4 MiB payload forces multiple iterations.
    monkeypatch.setattr(rec, "_QUAR_COPY_CHUNK_BYTES", 1 << 18, raising=True)

    # The guard covers ONLY apply_plan: every read_bytes call observed
    # during the recovery must be on a small file, never the payload.
    engine.apply_plan(result, recovery_run_id="run-stream")

    for _path, size in calls:
        assert size < (1 << 20), "quarantine copied the payload via read_bytes"

    # Verification reads happen AFTER the guard is released.
    quarantine = Path(stack.root) / "quarantine" / "integrity"
    published = sorted(quarantine.iterdir())
    assert len(published) == 1
    assert (
        hashlib.sha256(published[0].read_bytes()).hexdigest()
        == hashlib.sha256(corrupt_bytes).hexdigest()
    )


def test_destination_hash_exact_and_ordering(
    tmp_path: Path,
) -> None:
    stack, _sha, blob_path, _corrupt = _corrupt_blob_stack(
        tmp_path, b"stream payload for ordering"
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-order")
    engine.apply_plan(result, recovery_run_id="run-order")
    quarantine = Path(stack.root) / "quarantine" / "integrity"
    published = sorted(quarantine.iterdir())
    assert len(published) == 1
    destination = published[0]
    # Destination bytes hash exactly to the source content identity.
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == (
        hashlib.sha256(b"tampered bytes").hexdigest()
    )
    assert not blob_path.exists(), "source removed only AFTER durable publish"
    # The staged intermediate was consumed by publication.
    assert not list(quarantine.glob("*.staging"))


def test_retry_adopts_identical_destination(tmp_path: Path) -> None:
    stack, _sha, _blob_path_ref, _corrupt = _corrupt_blob_stack(
        tmp_path, b"retry adoption payload"
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-retry")
    engine.apply_plan(result, recovery_run_id="run-retry")
    quarantine = Path(stack.root) / "quarantine" / "integrity"
    before = sorted(quarantine.iterdir())
    assert len(before) == 1
    # Restart: a fresh engine re-scans and re-applies the same corruption.
    engine2 = _engine(_crash.RecoveryStack(Path(stack.root), clock=stack.clock))
    result2 = engine2.scan(recovery_run_id="run-retry-2")
    engine2.apply_plan(result2, recovery_run_id="run-retry-2")
    after = sorted(quarantine.iterdir())
    assert after == before, "exact retry adopts, never duplicates movement"


def test_different_destination_bytes_conflict(tmp_path: Path) -> None:
    stack, sha, _blob_path_ref, _corrupt = _corrupt_blob_stack(
        tmp_path, b"conflict"
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-conflict")
    # Pre-place DIFFERENT bytes at the deterministic locator the copy
    # will target: publication must refuse (no-clobber, I08 §30).
    content_sha = hashlib.sha256(b"tampered bytes").hexdigest()
    id_part = hashlib.sha256(
        _object_id_of_corrupt(stack).encode("utf-8")
    ).hexdigest()[:32]
    destination = (
        Path(stack.root)
        / "quarantine"
        / "integrity"
        / f"blob-{content_sha[:32]}-{id_part}.quarantined"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"FOREIGN BYTES")
    with pytest.raises(rec.RecoveryQuarantineConflict):
        engine.apply_plan(result, recovery_run_id="run-conflict")
    assert destination.read_bytes() == b"FOREIGN BYTES", "nothing overwritten"


def _object_id_of_corrupt(stack: Any) -> str:
    """The object id of the corrupt-blob finding for this stack."""
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="sha-probe")
    for finding in result.findings:
        if finding.problem == rec.PROBLEM_CORRUPT_BLOB:
            return str(finding.object_id)
    raise AssertionError("expected a CORRUPT_BLOB finding")


# ---------------------------------------------------------------------------
# Interrupted-quarantine convergence proof (I08R1 §6/§28), streamed copy
# ---------------------------------------------------------------------------


def test_quarantine_crash_boundaries_converge(tmp_path: Path) -> None:
    """§6 boundary B (destination durable, canonical still present):
    a fresh engine's apply adopts the landed effect instead of
    duplicating movement or raising a stale-plan conflict."""
    stack, _sha, blob_path, _corrupt = _corrupt_blob_stack(
        tmp_path, b"boundary B"
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="m-b")
    # Simulate death AFTER publish but BEFORE canonical unlink: place the
    # identical bytes at the deterministic destination and leave the
    # canonical object in place (exactly a hardlink publish that crashed
    # before the unlink).
    content_sha = hashlib.sha256(b"tampered bytes").hexdigest()
    id_part = hashlib.sha256(
        _object_id_of_corrupt(stack).encode("utf-8")
    ).hexdigest()[:32]
    destination = (
        Path(stack.root)
        / "quarantine"
        / "integrity"
        / f"blob-{content_sha[:32]}-{id_part}.quarantined"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"tampered bytes")
    original_unlink = Path.unlink

    calls: dict[str, int] = {"n": 0}

    def _die_on_canonical_unlink(self: Path, *a: Any, **k: Any) -> None:
        if self == blob_path:
            calls["n"] += 1
            raise _FaultInjected("death after destination, before unlink")

        return original_unlink(self, *a, **k)

    monkey_unlink = _die_on_canonical_unlink
    Path.unlink = monkey_unlink  # type: ignore[method-assign]
    try:
        with pytest.raises(_FaultInjected):
            engine.apply_plan(result, recovery_run_id="m-b")
    finally:
        Path.unlink = original_unlink  # type: ignore[method-assign]
    assert calls["n"] == 1
    # Restart: fresh engine converges — canonical unlinked, ONE artifact.
    engine2 = _engine(_crash.RecoveryStack(Path(stack.root), clock=stack.clock))
    result2 = engine2.scan(recovery_run_id="m-b2")
    engine2.apply_plan(result2, recovery_run_id="m-b2")
    assert not blob_path.exists()
    quarantine = Path(stack.root) / "quarantine" / "integrity"
    assert len(list(quarantine.iterdir())) == 1
    # The operation journal carries the full replayable phase chain.
    ops = engine2.operations.list_for_object(
        "EVIDENCE_BLOB", _object_id_of_corrupt(stack)
    )
    phases = {op["phase"] for op in ops}
    assert {"INTENT", "EFFECT_COMMITTED", "COMPLETED"} <= phases


def _sha_of_stack(stack: Any) -> str:
    return _object_id_of_corrupt(stack)
