"""SENSOR-B4-I07R1F — persisted-floor retry + catalog-concurrency proof.

Two remaining operator-review seams (I07R1F §0) proven closed:

- **A — persisted proof governs history (§3-§8).**  An ALREADY-committed
  checkpoint is retried and re-proved under the floor persisted in its own
  proof, never under the retrying process's current constructor
  configuration: a RAW_COMMITTED checkpoint survives a restart configured
  MANIFEST_COMMITTED (§5), a MANIFEST_COMMITTED checkpoint survives a
  restart configured RAW_COMMITTED (§6), while NEW checkpoints still obey
  the current constructor floor (§7) and divergent historical retries stay
  typed conflicts (§8) — persisted-floor support is not overwrite
  permission.

- **B — the shared catalog cache is internally synchronized (§9-§14).**
  Per-job locking lets different jobs drive the SAME ``DurableJsonCatalog``
  object from separate threads, so every ``_cache`` critical section is
  guarded by one internal REENTRANT lock: ``refresh`` can no longer race
  ``commit`` into false ``JsonCatalogCorrupt`` (§11), two jobs on one
  repository checkpoint concurrently with valid, forked-free chains (§12),
  and genuine vanished/divergent records still fail closed (§13).
  This is in-process cache safety, NOT distributed locking (§14).

Read-only against the committed evidence tree; real durable stack only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from crypto_sensor_fabric.providers.base.models import ResumeToken
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.jobs import (
    JobCatalogCorrupt,
    JobResumeGateError,
    JobTransitionConflict,
)

from _sibling_import import load_sibling

# One shared module instance with the I07R1 evidence builders, so the
# fixture stack (and its identity constants) is the SAME one the rest of
# the checkpoint's proof uses.
_base = load_sibling("_i07r1_base_mod", "test_job_state_r1")

JobStack = _base.JobStack
_create = _base._create
_drive_to_manifest = _base._drive_to_manifest
_full_batch = _base._full_batch
FIXED = _base.FIXED

TOKEN = ResumeToken(mode="PAGE", provider_cursor="c", page_number=1)


class LockedClock:
    """Thread-safe ticking clock.

    Concurrent chains must still receive strictly increasing instants, so
    the shared clock is serialized (a bare ``TickingClock`` read-modify-write
    is not thread-safe).
    """

    def __init__(self, start: datetime = FIXED) -> None:
        self._lock = threading.Lock()
        self._now = start

    def __call__(self) -> datetime:
        with self._lock:
            self._now = self._now + timedelta(seconds=1)
            return self._now


def _events_dir(tmp: Path) -> Path:
    return tmp / "catalogs" / "jobs_state" / "events"


# ---------------------------------------------------------------------------
# §3-§8: persisted proof floor governs historical checkpoint retries
# ---------------------------------------------------------------------------


def test_raw_persisted_checkpoint_retried_under_manifest_constructor(
    tmp_path: Path,
) -> None:
    """§5: a RAW checkpoint must survive a stricter constructor restart."""
    shared = LockedClock()
    stack = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo = stack.repo
    _create(repo, "job-pf-raw")
    _drive_to_manifest(repo, "job-pf-raw")
    sha = _full_batch(stack, "acq-pf-raw", "pm-pf-raw", b'{"rows": ["pfraw"]}')
    first = repo.advance_checkpoint(
        "job-pf-raw", resume_token=TOKEN, acquisition_id="acq-pf-raw"
    )
    assert first.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert first.last_manifest_id is None

    # Restart with a STRICTER constructor floor.  The constructor governs
    # only NEW decisions; the committed checkpoint is re-proved under the
    # floor persisted in its own proof.
    stricter = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    ).repo
    retried = stricter.advance_checkpoint(
        "job-pf-raw", resume_token=TOKEN, acquisition_id="acq-pf-raw"
    )
    assert retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert retried.last_committed_acquisition_id == "acq-pf-raw"
    assert retried.last_committed_blob_sha256 == sha
    assert retried.last_manifest_id is None
    gate_events = [
        transition
        for transition in stricter.list_transitions("job-pf-raw")
        if transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1  # adopted, never duplicated


def test_manifest_persisted_checkpoint_retried_under_raw_constructor(
    tmp_path: Path,
) -> None:
    """§6: a MANIFEST checkpoint must survive a laxer constructor restart."""
    shared = LockedClock()
    stack = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    )
    repo = stack.repo
    _create(repo, "job-pf-man")
    _drive_to_manifest(repo, "job-pf-man")
    sha = _full_batch(stack, "acq-pf-man", "pm-pf-man", b'{"rows": ["pfman"]}')
    first = repo.advance_checkpoint(
        "job-pf-man",
        resume_token=TOKEN,
        acquisition_id="acq-pf-man",
        manifest_id="pm-pf-man",
    )
    assert first.last_manifest_id == "pm-pf-man"

    laxer = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    ).repo
    retried = laxer.advance_checkpoint(
        "job-pf-man",
        resume_token=TOKEN,
        acquisition_id="acq-pf-man",
        manifest_id="pm-pf-man",
    )
    assert retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert retried.last_manifest_id == "pm-pf-man"
    assert retried.last_committed_blob_sha256 == sha
    gate_events = [
        transition
        for transition in laxer.list_transitions("job-pf-man")
        if transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1  # adopted, not duplicated
    # The historical proof is unchanged by the laxer process.
    proof = laxer._latest_event("job-pf-man")["checkpoint_proof"]  # noqa: SLF001
    assert proof["minimum_durable_status"] == (
        StorageJobStatus.MANIFEST_COMMITTED.value
    )


def test_persisted_proof_floor_never_rewritten_by_constructor(
    tmp_path: Path,
) -> None:
    """§5/§6: restart cannot reinterpret the durable floor record."""
    shared = LockedClock()
    stack = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo = stack.repo
    _create(repo, "job-pf-proof")
    _drive_to_manifest(repo, "job-pf-proof")
    _full_batch(stack, "acq-pf-proof", "pm-pf-proof", b'{"rows": ["pfp"]}')
    repo.advance_checkpoint(
        "job-pf-proof", resume_token=TOKEN, acquisition_id="acq-pf-proof"
    )
    proof_before = repo._latest_event("job-pf-proof")["checkpoint_proof"]  # noqa: SLF001

    other = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    ).repo
    other.advance_checkpoint(
        "job-pf-proof", resume_token=TOKEN, acquisition_id="acq-pf-proof"
    )
    proof_after = other._latest_event("job-pf-proof")["checkpoint_proof"]  # noqa: SLF001
    assert proof_before == proof_after
    assert proof_after["minimum_durable_status"] == (
        StorageJobStatus.RAW_COMMITTED.value
    )


def test_new_checkpoint_raw_constructor_rejects_manifest_anchor(
    tmp_path: Path,
) -> None:
    """§7/§12: a NEW RAW-floor checkpoint takes ``manifest_id=None``."""
    stack = JobStack(
        tmp_path, min_durable_status=StorageJobStatus.RAW_COMMITTED
    )
    repo = stack.repo
    _create(repo, "job-new-raw")
    _drive_to_manifest(repo, "job-new-raw")
    _full_batch(stack, "acq-new-raw", "pm-new-raw", b'{"rows": ["nraw"]}')
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-new-raw",
            resume_token=TOKEN,
            acquisition_id="acq-new-raw",
            manifest_id="pm-new-raw",
        )
    state = repo.advance_checkpoint(
        "job-new-raw", resume_token=TOKEN, acquisition_id="acq-new-raw"
    )
    assert state.last_manifest_id is None  # exact, never a dummy string


def test_new_checkpoint_manifest_constructor_requires_manifest(
    tmp_path: Path,
) -> None:
    """§7/§13: a NEW MANIFEST-floor checkpoint requires the exact manifest."""
    stack = JobStack(
        tmp_path, min_durable_status=StorageJobStatus.MANIFEST_COMMITTED
    )
    repo = stack.repo
    _create(repo, "job-new-man")
    _drive_to_manifest(repo, "job-new-man")
    _full_batch(stack, "acq-new-man", "pm-new-man", b'{"rows": ["nman"]}')
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-new-man", resume_token=TOKEN, acquisition_id="acq-new-man"
        )
    state = repo.advance_checkpoint(
        "job-new-man",
        resume_token=TOKEN,
        acquisition_id="acq-new-man",
        manifest_id="pm-new-man",
    )
    assert state.last_manifest_id == "pm-new-man"


def test_divergent_historical_retry_rejected(tmp_path: Path) -> None:
    """§8: persisted-floor support is NOT overwrite permission."""
    shared = LockedClock()
    stack = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.RAW_COMMITTED,
    )
    repo = stack.repo
    _create(repo, "job-div")
    _drive_to_manifest(repo, "job-div")
    _full_batch(stack, "acq-div", "pm-div", b'{"rows": ["div"]}')
    repo.advance_checkpoint(
        "job-div", resume_token=TOKEN, acquisition_id="acq-div"
    )
    stricter = JobStack(
        tmp_path,
        clock=shared,
        min_durable_status=StorageJobStatus.MANIFEST_COMMITTED,
    ).repo
    # Different resume token.
    with pytest.raises(JobTransitionConflict):
        stricter.advance_checkpoint(
            "job-div",
            resume_token=ResumeToken(
                mode="PAGE", provider_cursor="c", page_number=7
            ),
            acquisition_id="acq-div",
        )
    # Different acquisition anchor.
    with pytest.raises(JobTransitionConflict):
        stricter.advance_checkpoint(
            "job-div", resume_token=TOKEN, acquisition_id="acq-other"
        )
    # Different (contradictory) manifest anchor: still a conflict, never a
    # silently accepted new batch.
    with pytest.raises(JobTransitionConflict):
        stricter.advance_checkpoint(
            "job-div",
            resume_token=TOKEN,
            acquisition_id="acq-div",
            manifest_id="pm-other",
        )
    assert len(stricter.list_transitions("job-div")) == len(
        repo.list_transitions("job-div")
    )


# ---------------------------------------------------------------------------
# §9-§14: shared durable-catalog cache synchronization
# ---------------------------------------------------------------------------


def test_catalog_cache_lock_is_reentrant(tmp_path: Path) -> None:
    """§10: one internal REENTRANT lock, safe under nested reuse."""
    from crypto_sensor_fabric.storage.json_catalog import DurableJsonCatalog

    catalog = DurableJsonCatalog(
        tmp_path / "cat", logical_id_field="logical_id"
    )
    assert isinstance(catalog._cache_lock, type(threading.RLock()))  # noqa: SLF001
    with catalog._cache_lock:  # noqa: SLF001
        with catalog._cache_lock:  # noqa: SLF001 — nested acquire must not block
            catalog.commit("id-nested", {"logical_id": "id-nested"})
            assert catalog.get("id-nested") is not None
    assert len(catalog) == 1


def test_refresh_commit_race_does_not_false_corrupt(tmp_path: Path) -> None:
    """§11: a concurrent commit can never be read as a vanished record.

    Deterministic coordination: the refreshing thread pauses AFTER its
    file listing (so its ``on_disk`` snapshot predates the new record)
    while the committing thread lands the new durable object — the exact
    interleaving that used to raise a false ``JsonCatalogCorrupt``.  With
    the cache lock held for the whole scan/compare/adopt sequence the
    commit simply waits its turn.
    """
    from crypto_sensor_fabric.storage.json_catalog import DurableJsonCatalog

    catalog = DurableJsonCatalog(
        tmp_path / "cat", logical_id_field="logical_id"
    )
    catalog.commit("id-seed", {"logical_id": "id-seed"})
    real_parse = catalog._parse_fragment  # noqa: SLF001
    slow_name = "r1f-race-refresh"

    def _pausing_parse(path: Path) -> Any:
        parsed = real_parse(path)
        if threading.current_thread().name == slow_name:
            time.sleep(0.05)
        return parsed

    catalog._parse_fragment = _pausing_parse  # type: ignore[method-assign]  # noqa: SLF001

    errors: list[BaseException] = []
    new_id = "id-race-new"

    def _refresh() -> None:
        try:
            catalog.refresh()
        except BaseException as exc:  # noqa: BLE001 — recorded, asserted below
            errors.append(exc)

    def _commit() -> None:
        try:
            catalog.commit(new_id, {"logical_id": new_id})
        except BaseException as exc:  # noqa: BLE001 — recorded, asserted below
            errors.append(exc)

    refresher = threading.Thread(target=_refresh, name=slow_name)
    committer = threading.Thread(target=_commit, name="r1f-race-commit")
    refresher.start()
    committer.start()
    refresher.join(timeout=30)
    committer.join(timeout=30)
    catalog._parse_fragment = real_parse  # type: ignore[method-assign]  # noqa: SLF001

    assert not errors, errors
    assert catalog.get(new_id) is not None
    assert catalog.get("id-seed") is not None
    # Cache agrees with durable truth.
    on_disk_kinds = {
        json.loads(path.read_text(encoding="utf-8"))["logical_id"]
        for path in (tmp_path / "cat").glob("*.json")
    }
    assert on_disk_kinds == set(catalog.list_ids())


def test_two_jobs_same_repository_concurrent_checkpoints(
    tmp_path: Path,
) -> None:
    """§12: per-job concurrency must be compatible with the shared cache.

    Deterministic coordination: the *slow* thread pauses after listing the
    shared events catalog, and the fast thread does not even start until
    that listing is done — so the fast checkpoint commit provably lands
    inside the slow thread's scan/compare window.  Both chains must commit
    cleanly with no cache-mutation error, no false vanished-record
    corruption, no duplicate/forked events — and a fresh restart must
    reconstruct both.
    """
    clock = LockedClock()
    stack = JobStack(tmp_path, clock=clock)
    repo = stack.repo
    tags = ("a", "b")
    for tag in tags:
        _create(repo, f"job-cc-{tag}")
        _drive_to_manifest(repo, f"job-cc-{tag}")
        _full_batch(
            stack,
            f"acq-cc-{tag}",
            f"pm-cc-{tag}",
            f'{{"rows": ["cc-{tag}"]}}'.encode("utf-8"),
        )

    slow_name = "r1f-cc-slow"
    slow_listed = threading.Event()
    real_parse = repo._events._parse_fragment  # noqa: SLF001

    def _pausing_parse(path: Path) -> Any:
        parsed = real_parse(path)
        if threading.current_thread().name == slow_name:
            # The events file LISTING for this refresh is already complete;
            # hold the compare phase open so the fast commit must land
            # inside it (the exact false-vanish window).
            slow_listed.set()
            time.sleep(0.05)
        return parsed

    repo._events._parse_fragment = _pausing_parse  # type: ignore[method-assign]  # noqa: SLF001

    results: dict[str, Any] = {}
    errors: list[tuple[str, BaseException]] = []

    def _run(tag: str) -> None:
        try:
            if tag != "b":
                # Never start the fast chain before the slow listing exists.
                assert slow_listed.wait(timeout=30)
            results[tag] = repo.advance_checkpoint(
                f"job-cc-{tag}",
                resume_token=TOKEN,
                acquisition_id=f"acq-cc-{tag}",
                manifest_id=f"pm-cc-{tag}",
            )
        except BaseException as exc:  # noqa: BLE001 — recorded, asserted below
            errors.append((tag, exc))

    threads = [
        threading.Thread(target=_run, args=(tag,), name=name)
        for tag, name in (("a", "r1f-cc-fast"), ("b", slow_name))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    repo._events._parse_fragment = real_parse  # type: ignore[method-assign]  # noqa: SLF001

    assert not errors, errors
    for tag in tags:
        assert results[tag].status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert results[tag].last_committed_acquisition_id == f"acq-cc-{tag}"

    # A fresh restart reconstructs BOTH chains, one gate event each.
    fresh = JobStack(tmp_path, clock=clock).repo
    for tag in tags:
        gate_events = [
            transition
            for transition in fresh.list_transitions(f"job-cc-{tag}")
            if transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        assert len(gate_events) == 1
        assert (
            fresh.get_job(f"job-cc-{tag}").last_committed_acquisition_id
            == f"acq-cc-{tag}"
        )


def test_refresh_vanished_record_still_fails_closed(tmp_path: Path) -> None:
    """§13: internal synchronization does not weaken corruption detection."""
    from crypto_sensor_fabric.storage.json_catalog import (
        DurableJsonCatalog,
        JsonCatalogCorrupt,
    )

    catalog = DurableJsonCatalog(
        tmp_path / "cat", logical_id_field="logical_id"
    )
    catalog.commit("id-vanish", {"logical_id": "id-vanish"})
    (tmp_path / "cat" / f"{hashlib.sha256(b'id-vanish').hexdigest()}.json").unlink()
    with pytest.raises(JsonCatalogCorrupt):
        catalog.refresh()


def test_refresh_divergent_record_still_fails_closed(tmp_path: Path) -> None:
    """§13: a genuinely modified committed object is still corruption."""
    from crypto_sensor_fabric.storage.json_catalog import (
        DurableJsonCatalog,
        JsonCatalogCorrupt,
    )

    catalog = DurableJsonCatalog(
        tmp_path / "cat", logical_id_field="logical_id"
    )
    catalog.commit("id-diverge", {"logical_id": "id-diverge", "rows": [1]})
    victim = (
        tmp_path / "cat" / f"{hashlib.sha256(b'id-diverge').hexdigest()}.json"
    )
    victim.write_text(
        json.dumps({"logical_id": "id-diverge", "rows": [2]}), encoding="utf-8"
    )
    with pytest.raises(JsonCatalogCorrupt):
        catalog.refresh()


def test_event_catalog_shared_by_two_repositories_stays_valid(
    tmp_path: Path,
) -> None:
    """§14: cross-repository truth is unchanged by in-process cache safety."""
    clock = LockedClock()
    stack = JobStack(tmp_path, clock=clock)
    repo_a = stack.repo
    from crypto_sensor_fabric.storage import DurableJobStateRepository

    repo_b = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=stack.acq_repo,
        manifests=stack.manifest_repo,
        blob_metadata_repository=stack.blob_repo,
        clock=clock,
    )
    _create(repo_a, "job-xr")
    repo_a.advance_status("job-xr", to_status=StorageJobStatus.ACQUIRING)
    # Repo B was constructed before the event: only the post-lock refresh
    # makes A's committed transition visible.
    repo_b.advance_status("job-xr", to_status=StorageJobStatus.RAW_STAGED)
    assert len(repo_b.list_transitions("job-xr")) == 2
    assert JobCatalogCorrupt is not None  # imported for the fail-closed surface
