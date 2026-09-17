"""SENSOR-B4-I07A — durable job state repository tests.

Covers the frozen job-durability doctrine (03 doc §15) and §16 resume
coupling:

- durable birth + append-only event chain across restart;
- single-step forward progression along the frozen linear order;
- backward moves require an explicit reason (never silent);
- failure transitions require reasons; terminal states are terminal;
- CHECKPOINT_ADVANCED is entered ONLY through the durable-proof gate;
- §16 resume gate: no cursor advancement without durable acquisition +
  physically-verified blob + manifest-committed proof;
- crash-safe atomic publication with exact-retry adoption;
- per-job coordination (in-process + file lock, never auto-deleted);
- restart/corruption fail-closed validation, including durable
  re-anchoring of committed checkpoint state.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
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
    JobIdentityConflict,
    JobLockHeld,
    JobResumeGateError,
    JobTransitionConflict,
    JobUnknown,
)
from crypto_sensor_fabric.storage.json_catalog import (
    CatalogFaultHook,
    CatalogFaultPoint,
)

FIXED = datetime(2026, 9, 13, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"


class TickingClock:
    """Monotone injected clock; each call advances by one second."""

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
        min_durable_status: Any = None,
        lock_timeout_seconds: float = 30.0,
        fault_hooks: Any = None,
    ) -> None:
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
        kwargs: dict[str, Any] = {}
        if min_durable_status is not None:
            kwargs["min_durable_status"] = min_durable_status
        self.repo = DurableJobStateRepository(
            root / "catalogs" / "jobs_state",
            acquisitions=self.acq_repo,
            manifests=self.manifest_repo,
            blob_metadata_repository=self.blob_repo,
            clock=self.clock,
            lock_timeout_seconds=lock_timeout_seconds,
            fault_hooks=fault_hooks,
            **kwargs,
        )

    # -- durable truth builders ----------------------------------------------

    def seed_blob(self, data: bytes) -> str:
        blob = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        ).blob
        self.blob_repo.append_metadata(blob)
        return blob.blob_sha256

    def seed_acquisition(self, sha: str, acquisition_id: str) -> None:
        from crypto_sensor_fabric.storage import AcquisitionRecord

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

    def seed_manifest(
        self, manifest_id: str, partition_key: str, blob_sha: str
    ) -> str:
        from crypto_sensor_fabric.providers.base.enums import Granularity as G
        from crypto_sensor_fabric.storage import PartitionManifest
        from crypto_sensor_fabric.storage.enums import IntegrityState

        self.manifest_repo.append_partition_manifest(
            PartitionManifest(
                partition_manifest_id=manifest_id,
                partition_key=partition_key,
                manifest_version=1,
                provider="KRAKEN_FUTURES",
                venue="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument="PI_XBTUSD",
                source_granularity=G.G1H,
                date_basis="EVENT_TIME",
                logical_date_start=FIXED,
                logical_date_end=FIXED,
                blob_refs=[blob_sha],
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
        return manifest_id


def _create(repo: DurableJobStateRepository, job_id: str) -> None:
    repo.create_job(
        job_id=job_id,
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        # I07R1 §9: job/request identity is EXACT — acquisitions seeded by
        # JobStack.seed_acquisition carry fp-job, so every job created for
        # those acquisitions must present the same fingerprint.
        request_fingerprint="fp-job",
    )


# ---------------------------------------------------------------------------
# Durability + state machine (§15)
# ---------------------------------------------------------------------------


def test_birth_persists_and_survives_restart(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    stack.repo.create_job(
        job_id="job-restart",
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="fp-1",
    )
    fresh = JobStack(tmp_path).repo
    state = fresh.get_job("job-restart")
    assert state.status is StorageJobStatus.PLANNED
    assert state.provider_id == "KRAKEN_FUTURES"
    assert state.request_fingerprint == "fp-1"


def test_forward_progression_is_single_step(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-forward")
    statuses = [
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ]
    for status in statuses:
        state = repo.advance_status("job-forward", to_status=status)
        assert state.status is status
    transitions = repo.list_transitions("job-forward")
    assert [t.to_status for t in transitions] == statuses
    assert [t.from_status for t in transitions] == [
        StorageJobStatus.PLANNED
    ] + statuses[:-1]


def test_state_skipping_rejected(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-skip")
    repo.advance_status("job-skip", to_status=StorageJobStatus.ACQUIRING)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-skip", to_status=StorageJobStatus.PROJECTION_PENDING
        )


def test_silent_backward_move_rejected(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-backward")
    repo.advance_status("job-backward", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-backward", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-backward", to_status=StorageJobStatus.RAW_COMMITTED)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status("job-backward", to_status=StorageJobStatus.ACQUIRING)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-backward", to_status=StorageJobStatus.ACQUIRING, reason="retry"
        )


def test_failure_transition_requires_reason(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-fail")
    repo.advance_status("job-fail", to_status=StorageJobStatus.ACQUIRING)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status("job-fail", to_status=StorageJobStatus.FAILED_RETRYABLE)
    state = repo.advance_status(
        "job-fail",
        to_status=StorageJobStatus.FAILED_RETRYABLE,
        reason="provider 429 backoff",
    )
    assert state.status is StorageJobStatus.FAILED_RETRYABLE


def test_retry_resume_requires_reason_and_is_annotated(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-retry")
    repo.advance_status("job-retry", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-retry",
        to_status=StorageJobStatus.FAILED_RETRYABLE,
        reason="network drop",
    )
    with pytest.raises(JobTransitionConflict):
        repo.advance_status("job-retry", to_status=StorageJobStatus.ACQUIRING)
    state = repo.advance_status(
        "job-retry", to_status=StorageJobStatus.ACQUIRING, reason="retry after backoff"
    )
    assert state.status is StorageJobStatus.ACQUIRING


def test_terminal_states_have_no_exits(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-terminal")
    repo.advance_status("job-terminal", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-terminal",
        to_status=StorageJobStatus.FAILED_TERMINAL,
        reason="request window outside provider retention",
    )
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-terminal", to_status=StorageJobStatus.ACQUIRING, reason="x"
        )


def test_quarantined_is_terminal_in_v1(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-quarantine")
    repo.advance_status("job-quarantine", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-quarantine",
        to_status=StorageJobStatus.QUARANTINED,
        reason="integrity gate",
    )
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-quarantine", to_status=StorageJobStatus.ACQUIRING, reason="x"
        )


def test_expected_from_cas_guard(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-cas")
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-cas",
            to_status=StorageJobStatus.ACQUIRING,
            expected_from=StorageJobStatus.RAW_COMMITTED,
        )
    state = repo.advance_status(
        "job-cas",
        to_status=StorageJobStatus.ACQUIRING,
        expected_from=StorageJobStatus.PLANNED,
    )
    assert state.status is StorageJobStatus.ACQUIRING


def test_identity_conflict_on_differing_birth(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-identity")
    with pytest.raises(JobIdentityConflict):
        repo.create_job(
            job_id="job-identity",
            provider_id="GATE_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-other",
        )


def test_unknown_job_typed(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    with pytest.raises(JobUnknown):
        stack.repo.get_job("no-such-job")
    with pytest.raises(JobUnknown):
        stack.repo.advance_status(
            "no-such-job", to_status=StorageJobStatus.ACQUIRING
        )


def test_list_job_ids_and_has_job(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    _create(stack.repo, "job-a")
    _create(stack.repo, "job-b")
    assert stack.repo.list_job_ids() == ["job-a", "job-b"]
    assert stack.repo.has_job("job-a")
    assert not stack.repo.has_job("ghost")


# ---------------------------------------------------------------------------
# §16 resume coupling
# ---------------------------------------------------------------------------


def test_checkpoint_requires_durable_proof(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-gate")
    repo.advance_status("job-gate", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-gate", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-gate", to_status=StorageJobStatus.RAW_COMMITTED)
    repo.advance_status("job-gate", to_status=StorageJobStatus.PROJECTION_PENDING)
    repo.advance_status("job-gate", to_status=StorageJobStatus.PROJECTION_COMMITTED)
    repo.advance_status("job-gate", to_status=StorageJobStatus.MANIFEST_COMMITTED)
    sha = stack.seed_blob(b'{"rows": ["batch-1"]}')
    stack.seed_acquisition(sha, "acq-gate")
    manifest_id = stack.seed_manifest("pm-gate", "PK-GATE", sha)
    from crypto_sensor_fabric.providers.base.models import ResumeToken as RT

    token = RT(mode="PAGE", provider_cursor="cursor-1", page_number=3)
    state = repo.advance_checkpoint(
        "job-gate",
        resume_token=token,
        acquisition_id="acq-gate",
        manifest_id=manifest_id,
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.resume_token == token
    assert state.last_committed_acquisition_id == "acq-gate"
    assert state.last_manifest_id == manifest_id


def test_checkpoint_gate_fails_without_manifest(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-nomanifest")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-nomanifest", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-2"]}')
    stack.seed_acquisition(sha, "acq-nom")
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-nomanifest",
            resume_token={"mode": "OFFSET", "page_number": 2},
            acquisition_id="acq-nom",
            manifest_id="pm-ghost",
        )
    # Cursor NOT advanced (§16 fail closed).
    assert (
        stack.repo.get_job("job-nomanifest").status
        is StorageJobStatus.MANIFEST_COMMITTED
    )
    assert stack.repo.get_job("job-nomanifest").resume_token is None


def test_checkpoint_gate_fails_without_verified_blob(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-noblob")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-noblob", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-3"]}')
    stack.seed_acquisition(sha, "acq-noblob")
    manifest_id = stack.seed_manifest("pm-noblob", "PK-NOBLOB", sha)
    # Corrupt the physical bytes after durable registration (exact layout:
    # blobs/sha256/<h0h1>/<h2h3>/<sha>.blob).
    blob_key = (
        tmp_path
        / "blobs"
        / "sha256"
        / sha[0:2]
        / sha[2:4]
        / f"{sha}.blob"
    )
    assert blob_key.is_file(), f"expected blob at {blob_key}"
    data = bytearray(blob_key.read_bytes())
    data[0] ^= 0xFF
    blob_key.write_bytes(bytes(data))
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-noblob",
            resume_token={"mode": "OFFSET", "page_number": 4},
            acquisition_id="acq-noblob",
            manifest_id=manifest_id,
        )
    assert (
        stack.repo.get_job("job-noblob").status
        is StorageJobStatus.MANIFEST_COMMITTED
    )


def test_checkpoint_gate_fails_without_acquisition(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-noacq")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-noacq", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-4"]}')
    # The manifest's blob needs its own durable provenance (I04R1); the
    # BATCH acquisition id passed to the gate is the one that must be
    # missing.
    stack.seed_acquisition(sha, "acq-manifest-only")
    manifest_id = stack.seed_manifest("pm-noacq", "PK-NOACQ", sha)
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-noacq",
            resume_token={"mode": "PAGE", "page_number": 1},
            acquisition_id="acq-ghost",
            manifest_id=manifest_id,
        )


def test_checkpoint_gate_fails_when_manifest_lacks_blob(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-wrongblob")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-wrongblob", to_status=status)
    sha_a = stack.seed_blob(b'{"rows": ["batch-a"]}')
    sha_b = stack.seed_blob(b'{"rows": ["batch-b"]}')
    stack.seed_acquisition(sha_a, "acq-a")
    stack.seed_acquisition(sha_b, "acq-manifest-blob")
    stack.seed_manifest("pm-wrong", "PK-WRONG", sha_b)
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-wrongblob",
            resume_token={"mode": "PAGE", "page_number": 5},
            acquisition_id="acq-a",
            manifest_id="pm-wrong",
        )


def test_checkpoint_requires_manifest_committed_status(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-early")
    repo.advance_status("job-early", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-early", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-early", to_status=StorageJobStatus.RAW_COMMITTED)
    sha = stack.seed_blob(b'{"rows": ["batch-5"]}')
    stack.seed_acquisition(sha, "acq-early")
    manifest_id = stack.seed_manifest("pm-early", "PK-EARLY", sha)
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-early",
            resume_token={"mode": "PAGE", "page_number": 1},
            acquisition_id="acq-early",
            manifest_id=manifest_id,
        )


def test_checkpoint_advancement_from_weak_floor(tmp_path: Path) -> None:
    """Explicit weaker floor (RAW_COMMITTED) is the only other legal gate."""
    stack = JobStack(tmp_path, min_durable_status=StorageJobStatus.RAW_COMMITTED)
    repo = stack.repo
    _create(repo, "job-weakfloor")
    repo.advance_status("job-weakfloor", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-weakfloor", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-weakfloor", to_status=StorageJobStatus.RAW_COMMITTED)
    sha = stack.seed_blob(b'{"rows": ["batch-6"]}')
    stack.seed_acquisition(sha, "acq-weak")
    from crypto_sensor_fabric.providers.base.models import ResumeToken as RT

    state = repo.advance_checkpoint(
        "job-weakfloor",
        resume_token=RT(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-weak",
        manifest_id=None,  # I07R1 §12: RAW floor takes no manifest anchor
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_manifest_id is None


def test_checkpoint_double_advance_rejected(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-double")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-double", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-7"]}')
    stack.seed_acquisition(sha, "acq-double")
    manifest_id = stack.seed_manifest("pm-double", "PK-DOUBLE", sha)
    token = None
    from crypto_sensor_fabric.providers.base.models import ResumeToken as RT

    token = RT(mode="PAGE", provider_cursor="c", page_number=1)
    repo.advance_checkpoint(
        "job-double",
        resume_token=token,
        acquisition_id="acq-double",
        manifest_id=manifest_id,
    )
    stack.seed_acquisition(sha, "acq-double-2")
    with pytest.raises(JobTransitionConflict):
        repo.advance_checkpoint(
            "job-double",
            resume_token=RT(mode="PAGE", provider_cursor="c2", page_number=2),
            acquisition_id="acq-double-2",
            manifest_id=manifest_id,
        )


def test_checkpoint_via_plain_transition_forbidden(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-plain")
    repo.advance_status("job-plain", to_status=StorageJobStatus.ACQUIRING)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-plain", to_status=StorageJobStatus.CHECKPOINT_ADVANCED
        )


def test_batch_continuation_after_checkpoint(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-continuation")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-continuation", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-8"]}')
    stack.seed_acquisition(sha, "acq-cont")
    manifest_id = stack.seed_manifest("pm-cont", "PK-CONT", sha)
    from crypto_sensor_fabric.providers.base.models import ResumeToken as RT

    repo.advance_checkpoint(
        "job-continuation",
        resume_token=RT(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-cont",
        manifest_id=manifest_id,
    )
    state = repo.advance_status(
        "job-continuation",
        to_status=StorageJobStatus.ACQUIRING,
        reason="next batch after checkpoint",
    )
    assert state.status is StorageJobStatus.ACQUIRING
    # The resume token persists across the continuation (active resume point).
    assert state.resume_token is not None
    # ...and the annotated backward edge is recorded explicitly.
    transitions = repo.list_transitions("job-continuation")
    assert transitions[-1].from_status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert transitions[-1].reason is not None


def test_min_durable_status_validated(tmp_path: Path) -> None:
    with pytest.raises(JobResumeGateError):
        JobStack(
            tmp_path, min_durable_status=StorageJobStatus.PLANNED
        ).repo  # noqa: B018 — construction itself must fail


# ---------------------------------------------------------------------------
# Crash / adoption / coordination / corruption
# ---------------------------------------------------------------------------


def test_crash_before_publication_leaves_old_chain(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    _create(stack.repo, "job-crash")
    faulted = JobStack(
        tmp_path,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.BEFORE_STAGED_WRITE),
    )
    # A NEW job's birth attempt hits the injected fault mid-publication.
    with pytest.raises(FaultError):
        faulted.repo.create_job(
            job_id="job-crash-new",
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-crash-new",
        )
    # No partial birth survived the crash.
    assert not stack.repo.has_job("job-crash-new")
    # The pre-existing job is untouched and its identity stays sealed.
    assert stack.repo.get_job("job-crash").status is StorageJobStatus.PLANNED
    with pytest.raises(JobIdentityConflict):
        stack.repo.create_job(
            job_id="job-crash",
            provider_id="OTHER",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="other",
        )


def test_stale_job_lock_never_auto_deleted(tmp_path: Path) -> None:
    """I07R1 §28: the physical lock key is sha256(utf8(job_id)).lock —
    raw logical IDs never become filesystem paths."""
    stack = JobStack(tmp_path)
    _create(stack.repo, "job-lock")
    locks_root = tmp_path / "catalogs" / "jobs_state" / "locks"
    locks_root.mkdir(parents=True, exist_ok=True)
    lock_key = hashlib.sha256("job-lock".encode("utf-8")).hexdigest()
    lock_path = locks_root / f"{lock_key}.lock"
    lock_path.write_text("stale\n", encoding="utf-8")
    stale_repo = JobStack(tmp_path, lock_timeout_seconds=0.0).repo
    with pytest.raises(JobLockHeld):
        stale_repo.advance_status(
            "job-lock", to_status=StorageJobStatus.ACQUIRING
        )
    assert lock_path.read_text(encoding="utf-8") == "stale\n"


def test_corrupt_event_fails_restart(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-corrupt")
    repo.advance_status("job-corrupt", to_status=StorageJobStatus.ACQUIRING)
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    names = sorted(p.name for p in events_dir.glob("*.json"))
    assert names, "expected a committed event fragment"
    path = events_dir / names[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["transition"]["to_status"] = "NOT_A_STATUS"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_missing_anchored_acquisition_fails_restart(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-anchor")
    for status in (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        repo.advance_status("job-anchor", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["batch-9"]}')
    stack.seed_acquisition(sha, "acq-anchor")
    manifest_id = stack.seed_manifest("pm-anchor", "PK-ANCHOR", sha)
    from crypto_sensor_fabric.providers.base.models import ResumeToken as RT

    repo.advance_checkpoint(
        "job-anchor",
        resume_token=RT(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-anchor",
        manifest_id=manifest_id,
    )
    # Deregister the anchored acquisition fragment (isolated tamper at the
    # deterministic physical locator used by AcquisitionRepository).
    victim = (
        tmp_path
        / "catalogs"
        / "manifests"
        / "acquisitions"
        / (hashlib.sha256(b"acq-anchor").hexdigest() + ".parquet")
    )
    assert victim.is_file(), f"expected acquisition fragment at {victim}"
    victim.unlink()
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_concurrent_transitions_serialize(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-concurrent")
    errors: list[Exception] = []

    def worker() -> None:
        try:
            repo.advance_status("job-concurrent", to_status=StorageJobStatus.ACQUIRING)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Exactly one event appended; losers fail typed, never fork the chain.
    assert len(repo.list_transitions("job-concurrent")) == 1
    for exc in errors:
        assert isinstance(exc, JobTransitionConflict | JobLockHeld)


def test_uncommitted_proof_never_advances_cursor(tmp_path: Path) -> None:
    """The crash-test-#6 seed: evidence without proof cannot move the cursor."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-noproof")
    repo.advance_status("job-noproof", to_status=StorageJobStatus.ACQUIRING)
    sha = stack.seed_blob(b'{"rows": ["batch-10"]}')
    stack.seed_acquisition(sha, "acq-noproof")
    # Blob + acquisition durable, but the job has never reached
    # MANIFEST_COMMITTED — no proof, no advancement.
    with pytest.raises(JobResumeGateError):
        repo.advance_checkpoint(
            "job-noproof",
            resume_token={"mode": "PAGE", "page_number": 9},
            acquisition_id="acq-noproof",
            manifest_id="pm-any",
        )
    fresh = JobStack(tmp_path).repo
    state = fresh.get_job("job-noproof")
    assert state.status is StorageJobStatus.ACQUIRING
    assert state.resume_token is None
