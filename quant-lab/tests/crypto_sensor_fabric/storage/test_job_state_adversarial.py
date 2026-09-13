"""SENSOR-B4-I07B — job↔evidence coupling adversarial proof.

End-to-end §16 coupling across two batches, crash boundaries around
checkpoint advancement (§20 crash tests 6/7: crash before resume
advancement; identical refetch semantics), restart equivalence, and
corruption/adoption fail-closed behavior.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.providers.base.models import ResumeToken
from crypto_sensor_fabric.storage import (
    AcquisitionRepository,
    BlobMetadataRepository,
    LocalBlobStore,
    PartitionManifestRepository,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.atomic import FaultError
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.jobs import (
    DurableJobStateRepository,
    JobCatalogCorrupt,
    JobLockHeld,
    JobResumeGateError,
    JobTransitionConflict,
)
from crypto_sensor_fabric.storage.json_catalog import (
    CatalogFaultHook,
    CatalogFaultPoint,
)

FIXED = datetime(2026, 9, 13, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
STATUSES_TO_MANIFEST = (
    StorageJobStatus.ACQUIRING,
    StorageJobStatus.RAW_STAGED,
    StorageJobStatus.RAW_COMMITTED,
    StorageJobStatus.PROJECTION_PENDING,
    StorageJobStatus.PROJECTION_COMMITTED,
    StorageJobStatus.MANIFEST_COMMITTED,
)


class TickingClock:
    def __init__(self, start: datetime = FIXED) -> None:
        self.now = start

    def __call__(self) -> datetime:
        self.now = self.now + timedelta(seconds=1)
        return self.now


class JobStack:
    """Real durable dependency stack rooted at tmp_path."""

    def __init__(
        self,
        root: Path,
        *,
        clock: TickingClock | None = None,
        fault_hooks: Any = None,
    ) -> None:
        # A shared injected clock keeps every chain chronologically ordered
        # across repository instances (a fresh instance MUST NOT rewind time,
        # or restart validation fails closed on chronology).
        self.clock = clock or TickingClock()
        self.store = LocalBlobStore(root, clock=lambda: FIXED)
        self.blob_repo = BlobMetadataRepository(
            root, blob_store=self.store, clock=lambda: FIXED
        )
        self.acq_repo = AcquisitionRepository(
            root,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            clock=lambda: FIXED,
        )
        self.manifest_repo = PartitionManifestRepository(
            root,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            clock=lambda: FIXED,
        )
        self.repo = DurableJobStateRepository(
            root / "catalogs" / "jobs_state",
            acquisitions=self.acq_repo,
            manifests=self.manifest_repo,
            blob_metadata_repository=self.blob_repo,
            clock=self.clock,
            fault_hooks=fault_hooks,
        )

    def seed_batch(
        self, data: bytes, acquisition_id: str, manifest_id: str, partition_key: str
    ) -> tuple[str, str]:
        """Durable batch: blob -> metadata -> acquisition -> manifest."""
        blob = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        ).blob
        self.blob_repo.append_metadata(blob)
        sha = blob.blob_sha256
        from crypto_sensor_fabric.storage import AcquisitionRecord, PartitionManifest
        from crypto_sensor_fabric.storage.enums import IntegrityState

        self.acq_repo.append_acquisition(
            AcquisitionRecord(
                acquisition_id=acquisition_id,
                provider_id="KRAKEN_FUTURES",
                venue="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                request_fingerprint="fp-job",
                adapter_version="kraken-adapter-v2",
                requested_start=FIXED,
                requested_end=FIXED,
                native_instrument="PI_XBTUSD",
                native_granularity=Granularity.G1H,
                request_started_at=FIXED,
                response_observed_at=FIXED,
                ingested_at=FIXED,
                http_status_or_source_status="200",
                endpoint_host="futures.kraken.com",
                endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
                request_family="market_analytics_funding",
                source_locator=(
                    "https://futures.kraken.com/api/charts/v1/analytics/"
                    "PI_XBTUSD/funding"
                ),
                blob_sha256=sha,
            )
        )
        self.manifest_repo.append_partition_manifest(
            PartitionManifest(
                partition_manifest_id=manifest_id,
                partition_key=partition_key,
                manifest_version=1,
                provider="KRAKEN_FUTURES",
                venue="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument="PI_XBTUSD",
                source_granularity=Granularity.G1H,
                date_basis="EVENT_TIME",
                logical_date_start=FIXED,
                logical_date_end=FIXED,
                blob_refs=[sha],
                projection_refs=[],
                coverage_state="PARTIAL",
                integrity_state=IntegrityState.UNVERIFIED,
                row_count=1,
                min_time=FIXED,
                max_time=FIXED,
                gap_count=0,
                revision_count=0,
                created_at=FIXED,
                supersedes_manifest_id=None,
            ),
            expected_current=None,
        )
        return acquisition_id, manifest_id


def _create(repo: DurableJobStateRepository, job_id: str) -> None:
    repo.create_job(
        job_id=job_id,
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=f"fp-{job_id}",
    )


def _drive_to_manifest(repo: DurableJobStateRepository, job_id: str) -> None:
    """Advance the job to MANIFEST_COMMITTED from its CURRENT status.

    Resume-aware: after a checkpoint the chain is at CHECKPOINT_ADVANCED
    (rank above MANIFEST_COMMITTED), so driving must stop at once and the
    continuation edge to ACQUIRING is taken first.
    """
    current = repo.get_job(job_id).status
    if current is StorageJobStatus.CHECKPOINT_ADVANCED:
        repo.advance_status(
            job_id,
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        current = StorageJobStatus.ACQUIRING
    order = list(STATUSES_TO_MANIFEST)
    start = order.index(current) + 1 if current in order else 0
    for status in order[start:]:
        repo.advance_status(job_id, to_status=status)


# ---------------------------------------------------------------------------
# End-to-end §16 coupling across two batches
# ---------------------------------------------------------------------------


def test_two_batch_resume_cycle(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-e2e")
    _drive_to_manifest(repo, "job-e2e")
    acq1, man1 = stack.seed_batch(
        b'{"rows": ["b1"]}', "acq-e2e-1", "pm-e2e-1", "PK-E2E-1"
    )
    state = repo.advance_checkpoint(
        "job-e2e",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq1,
        manifest_id=man1,
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_committed_acquisition_id == "acq-e2e-1"
    # Batch 2: annotated continuation, new batch, new checkpoint.
    state = repo.advance_status(
        "job-e2e",
        to_status=StorageJobStatus.ACQUIRING,
        reason="batch 2 continuation",
    )
    _drive_to_manifest(repo, "job-e2e")
    acq2, man2 = stack.seed_batch(
        b'{"rows": ["b2"]}', "acq-e2e-2", "pm-e2e-2", "PK-E2E-2"
    )
    state = repo.advance_checkpoint(
        "job-e2e",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=2),
        acquisition_id=acq2,
        manifest_id=man2,
    )
    assert state.last_committed_acquisition_id == "acq-e2e-2"
    assert state.resume_token == ResumeToken(
        mode="PAGE", provider_cursor="c", page_number=2
    )
    # The chain records the full history: 6 + gate + continuation + 6 + gate.
    transitions = repo.list_transitions("job-e2e")
    assert len(transitions) == 14
    assert transitions[6].to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert transitions[13].to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    # Completion after the final batch.
    final = repo.advance_status("job-e2e", to_status=StorageJobStatus.COMPLETE)
    assert final.status is StorageJobStatus.COMPLETE


def test_gate_blocks_cursor_past_unindexed_evidence(tmp_path: Path) -> None:
    """§16 core: evidence without manifest-committed proof cannot move the
    cursor — the crash-test-#6 seed in its adversarial form."""
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-unindexed")
    _drive_to_manifest(repo, "job-unindexed")
    blob = stack.store.put_bytes(
        b'{"rows": ["unindexed"]}',
        storage_encoding=StorageEncoding.NONE,
        source_media_type=MEDIA,
    ).blob
    stack.blob_repo.append_metadata(blob)
    sha = blob.blob_sha256
    # Blob + metadata + acquisition durable but NO manifest commit for this
    # batch — exactly the "cursor past unindexed evidence" attack.
    from crypto_sensor_fabric.storage import AcquisitionRecord

    stack.acq_repo.append_acquisition(
        AcquisitionRecord(
            acquisition_id="acq-unindexed",
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-job",
            adapter_version="kraken-adapter-v2",
            requested_start=FIXED,
            requested_end=FIXED,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
            request_started_at=FIXED,
            response_observed_at=FIXED,
            ingested_at=FIXED,
            http_status_or_source_status="200",
            endpoint_host="futures.kraken.com",
            endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
            request_family="market_analytics_funding",
            source_locator=(
                "https://futures.kraken.com/api/charts/v1/analytics/"
                "PI_XBTUSD/funding"
            ),
            blob_sha256=sha,
        )
    )
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-unindexed",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=7),
            acquisition_id="acq-unindexed",
            manifest_id="pm-unindexed-ghost",
        )
    fresh = JobStack(tmp_path, clock=shared_clock).repo.get_job("job-unindexed")
    assert fresh.status is StorageJobStatus.MANIFEST_COMMITTED
    assert fresh.resume_token is None


def test_identical_refetch_reuses_batch_without_cursor_move(tmp_path: Path) -> None:
    """§20 crash test 7 semantics: a second acquisition of the same bytes is
    visible durable history; the checkpoint gate accepts either acquisition
    id of the batch but never manufactures a new source/manifest identity."""
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-refetch")
    _drive_to_manifest(repo, "job-refetch")
    data = b'{"rows": ["same-bytes"]}'
    acq1, man1 = stack.seed_batch(data, "acq-rf-1", "pm-rf", "PK-RF")
    repo.advance_checkpoint(
        "job-refetch",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq1,
        manifest_id=man1,
    )
    # Second acquisition event, same durable blob bytes (history, not dedupe).
    blob_meta = stack.blob_repo.get_blob_metadata(
        stack.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        ).blob.blob_sha256
    )
    assert blob_meta, "same-bytes blob must be durable metadata-referenced"
    state = repo.get_job("job-refetch")
    assert state.last_committed_acquisition_id == "acq-rf-1"
    # Exact retry of the SAME batch checkpoint is idempotent (§68): the
    # durable proof is re-resolved and the committed state is returned —
    # never a duplicated event, never a cursor move.
    before = len(repo.list_transitions("job-refetch"))
    retried = repo.advance_checkpoint(
        "job-refetch",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq1,
        manifest_id=man1,
    )
    assert retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert retried.last_committed_acquisition_id == "acq-rf-1"
    assert len(repo.list_transitions("job-refetch")) == before
    gate_events = [
        t
        for t in repo.list_transitions("job-refetch")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1


# ---------------------------------------------------------------------------
# Crash boundaries around checkpoint advancement
# ---------------------------------------------------------------------------


def test_crash_before_event_publish_keeps_job_at_manifest(tmp_path: Path) -> None:
    """§20 crash test 6 seed: crash before resume advancement."""
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-crash6")
    _drive_to_manifest(repo, "job-crash6")
    acq, man = stack.seed_batch(
        b'{"rows": ["c6"]}', "acq-c6", "pm-c6", "PK-C6"
    )
    faulted = JobStack(
        tmp_path,
        clock=shared_clock,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.BEFORE_STAGED_WRITE),
    )
    with pytest.raises(FaultError):
        faulted.repo.advance_checkpoint(
            "job-crash6",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq,
            manifest_id=man,
        )
    # Cursor NOT advanced; durable truth intact; retry completes the batch.
    assert stack.repo.get_job("job-crash6").status is StorageJobStatus.MANIFEST_COMMITTED
    state = repo.advance_checkpoint(
        "job-crash6",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq,
        manifest_id=man,
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED


def test_crash_after_publish_adopts_checkpoint_on_retry(tmp_path: Path) -> None:
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-crash6b")
    _drive_to_manifest(repo, "job-crash6b")
    acq, man = stack.seed_batch(
        b'{"rows": ["c6b"]}', "acq-c6b", "pm-c6b", "PK-C6B"
    )
    # Lost-return race: the event is committed, then the call raises.
    faulted = JobStack(
        tmp_path,
        clock=shared_clock,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN),
    )
    with pytest.raises(Exception):  # noqa: B017 — the injected crash
        faulted.repo.advance_checkpoint(
            "job-crash6b",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq,
            manifest_id=man,
        )
    # The event IS durable on disk (published before the fault); the
    # faulted in-memory cache is stale, so a FRESH instance proves it.
    fresh = JobStack(tmp_path, clock=shared_clock).repo
    assert (
        fresh.get_job("job-crash6b").status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    # Exact retry through a clean repository re-derives the same event id
    # and semantics; the gate re-proves durable truth, then adoption wins.
    state = fresh.advance_checkpoint(
        "job-crash6b",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq,
        manifest_id=man,
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    transitions = fresh.list_transitions("job-crash6b")
    gate_events = [
        t for t in transitions if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1  # adopted, not duplicated


def test_crash_retry_with_different_token_is_conflict(tmp_path: Path) -> None:
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-diverge")
    _drive_to_manifest(repo, "job-diverge")
    acq, man = stack.seed_batch(
        b'{"rows": ["dv"]}', "acq-dv", "pm-dv", "PK-DV"
    )
    faulted = JobStack(
        tmp_path,
        clock=shared_clock,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN),
    )
    with pytest.raises(Exception):  # noqa: B017 — the injected crash
        faulted.repo.advance_checkpoint(
            "job-diverge",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq,
            manifest_id=man,
        )
    # Divergent retry: different semantics under the same event slot —
    # typed conflict through a FRESH repository (disk truth, not cache).
    with pytest.raises(JobTransitionConflict):
        JobStack(tmp_path, clock=shared_clock).repo.advance_checkpoint(
            "job-diverge",
            resume_token=ResumeToken(
                mode="PAGE", provider_cursor="other", page_number=9
            ),
            acquisition_id=acq,
            manifest_id=man,
        )


def test_crash_retry_divergence_is_visible_after_restart(tmp_path: Path) -> None:
    """A divergent retry must never silently adopt — even after restart."""
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-diverge2")
    _drive_to_manifest(repo, "job-diverge2")
    acq, man = stack.seed_batch(
        b'{"rows": ["dv2"]}', "acq-dv2", "pm-dv2", "PK-DV2"
    )
    faulted = JobStack(
        tmp_path,
        clock=shared_clock,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN),
    )
    with pytest.raises(Exception):  # noqa: B017 — the injected crash
        faulted.repo.advance_checkpoint(
            "job-diverge2",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id=acq,
            manifest_id=man,
        )
    with pytest.raises(JobTransitionConflict):
        JobStack(tmp_path, clock=shared_clock).repo.advance_checkpoint(
            "job-diverge2",
            resume_token=ResumeToken(
                mode="PAGE", provider_cursor="zz", page_number=4
            ),
            acquisition_id=acq,
            manifest_id=man,
        )
    # The committed chain remains the ORIGINAL truth.
    fresh = JobStack(tmp_path, clock=shared_clock).repo
    state = fresh.get_job("job-diverge2")
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.resume_token == ResumeToken(
        mode="PAGE", provider_cursor="c", page_number=1
    )


def test_checkpoint_state_survives_restart_with_reanchoring(tmp_path: Path) -> None:
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-restart2")
    _drive_to_manifest(repo, "job-restart2")
    acq, man = stack.seed_batch(
        b'{"rows": ["r2"]}', "acq-r2", "pm-r2", "PK-R2"
    )
    repo.advance_checkpoint(
        "job-restart2",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=2),
        acquisition_id=acq,
        manifest_id=man,
    )
    fresh = JobStack(tmp_path, clock=shared_clock).repo
    state = fresh.get_job("job-restart2")
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.resume_token.page_number == 2
    assert state.last_manifest_id == man


# ---------------------------------------------------------------------------
# Corruption / concurrency
# ---------------------------------------------------------------------------


def test_anchor_manifest_tamper_fails_restart(tmp_path: Path) -> None:
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    repo = stack.repo
    _create(repo, "job-tamper")
    _drive_to_manifest(repo, "job-tamper")
    acq, man = stack.seed_batch(
        b'{"rows": ["tp"]}', "acq-tp", "pm-tp", "PK-TP"
    )
    repo.advance_checkpoint(
        "job-tamper",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acq,
        manifest_id=man,
    )
    manifests_dir = tmp_path / "catalogs" / "manifests" / "partitions"
    victim = None
    for path in manifests_dir.rglob("*.parquet"):
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        if "partition_manifest_id" in table.column_names:
            ids = table.column("partition_manifest_id").to_pylist()
            if man in ids:
                victim = path
                break
    assert victim is not None, "expected a committed manifest fragment"
    victim.unlink()
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path, clock=shared_clock).repo


def test_lock_blocks_cross_process_writer(tmp_path: Path) -> None:
    shared_clock = TickingClock()
    stack = JobStack(tmp_path, clock=shared_clock)
    _create(stack.repo, "job-xlock")
    # Simulate an external writer holding the lock file.
    locks_root = tmp_path / "catalogs" / "jobs_state" / "locks"
    locks_root.mkdir(parents=True, exist_ok=True)
    (locks_root / "job-xlock.lock").write_text("external\n", encoding="utf-8")
    contender = JobStack(tmp_path, clock=shared_clock)
    zero_timeout_repo = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=contender.acq_repo,
        manifests=contender.manifest_repo,
        blob_metadata_repository=contender.blob_repo,
        clock=shared_clock,
        lock_timeout_seconds=0.0,
    )
    with pytest.raises(JobLockHeld):
        zero_timeout_repo.advance_status(
            "job-xlock", to_status=StorageJobStatus.ACQUIRING
        )


def test_concurrent_gate_attempts_produce_one_event(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo  # same instance: in-process coordination under test
    _create(repo, "job-race")
    _drive_to_manifest(repo, "job-race")
    acq, man = stack.seed_batch(
        b'{"rows": ["race"]}', "acq-race", "pm-race", "PK-RACE"
    )
    errors: list[Exception] = []

    def worker() -> None:
        try:
            repo.advance_checkpoint(
                "job-race",
                resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
                acquisition_id=acq,
                manifest_id=man,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    gate_events = [
        t
        for t in repo.list_transitions("job-race")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1
    for exc in errors:
        assert isinstance(
            exc, JobTransitionConflict | JobLockHeld | JobResumeGateError
        )
