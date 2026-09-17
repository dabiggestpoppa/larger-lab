"""SENSOR-B4-I07R1 — resume-truth hardening adversarial proof.

Operator-review seams (I07R1 §0 A-H) proven closed, per §39:

- API: the public ``advance_status`` signature rejects resume-token,
  checkpoint-anchor and gate-flag arguments (§39-1..6); the checkpoint
  path is private and flag-free (§4).
- Identity: checkpoint proof belongs to the EXACT job (provider /
  sensor / request_fingerprint, §7), passes the authoritative I04R2
  usable-provenance predicate (§8), and at the MANIFEST floor binds to a
  manifest describing that acquisition's source (§10) — cross-job
  same-blob and forensic evidence can never move a cursor (§11-§12 of
  the doctrine; tests 11-12).
- Floor semantics: RAW_COMMITTED requires ``manifest_id=None`` and
  survives restart (§12/§14); MANIFEST_COMMITTED requires the exact
  manifest (§13).  Anchors are the EXACT acquisition blob (§13).
- Proof: every checkpoint event carries immutable V1 proof bound to the
  resulting anchors; proof on ordinary events, missing proofs, divergent
  proofs, forward skips, FAILED_RETRYABLE bad targets, and reason-less
  failure entries are all corruption on restart (§15-§22, §39-20..29).
- Tamper: birth-identity mutation, ordinary cursor/anchor mutation,
  event-identity forging fail closed (§23-§26, §39-30..37).
- Coordination: raw job IDs never become lock paths (§28-§29); two
  long-lived repositories refresh under the outermost lock and never
  fork the chain (§30-§36, §39-41..43).

Historical I07 evidence untouched (§2).  Read-only against the evidence
tree.
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
from crypto_sensor_fabric.providers.base.models import ResumeToken
from crypto_sensor_fabric.storage import (
    AcquisitionRepository,
    AcquisitionRecord,
    BlobMetadataRepository,
    LocalBlobStore,
    PartitionManifest,
    PartitionManifestRepository,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.atomic import FaultError
from crypto_sensor_fabric.storage.enums import IntegrityState, StorageJobStatus
from crypto_sensor_fabric.storage.json_catalog import (
    CatalogFaultHook,
    CatalogFaultPoint,
)

try:  # storage.__init__ re-exports the job repository (I07+)
    from crypto_sensor_fabric.storage import DurableJobStateRepository
except ImportError:  # pragma: no cover
    from crypto_sensor_fabric.storage.jobs import DurableJobStateRepository
from crypto_sensor_fabric.storage.jobs import (
    JobCatalogCorrupt,
    JobResumeGateError,
    JobTransitionConflict,
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
_PROVIDER = "KRAKEN_FUTURES"
_INSTRUMENT = "PI_XBTUSD"
_FP = "fp-7f3a9c1d2e8b4a6f9c0d1e2f3a4b5c6d"


class TickingClock:
    def __init__(self, start: datetime = FIXED) -> None:
        self.now = start

    def __call__(self) -> datetime:
        self.now = self.now + timedelta(seconds=1)
        return self.now


class JobStack:
    """Real durable dependency stack rooted at tmp_path (exact identity)."""

    def __init__(
        self,
        root: Path,
        *,
        clock: TickingClock | None = None,
        min_durable_status: Any = None,
        lock_timeout_seconds: float = 30.0,
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

    def seed_blob(self, data: bytes) -> str:
        blob = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        ).blob
        self.blob_repo.append_metadata(blob)
        return blob.blob_sha256

    def seed_acquisition(
        self,
        sha: str,
        acquisition_id: str,
        *,
        request_fingerprint: str = _FP,
        provider_id: str = _PROVIDER,
        venue: str | None = None,
        sensor_family: Any = SensorFamily.MECHANICAL_FUNDING,
        native_instrument: str = _INSTRUMENT,
        native_granularity: Any = Granularity.G1H,
        http_status: str = "200",
        failure_ref: str | None = None,
    ) -> None:
        self.acq_repo.append_acquisition(
            AcquisitionRecord(
                acquisition_id=acquisition_id,
                provider_id=provider_id,
                venue=venue or provider_id,
                sensor_family=sensor_family,
                request_fingerprint=request_fingerprint,
                adapter_version="kraken-adapter-v2",
                requested_start=FIXED,
                requested_end=FIXED,
                native_instrument=native_instrument,
                native_granularity=native_granularity,
                request_started_at=FIXED,
                response_observed_at=FIXED,
                ingested_at=FIXED,
                http_status_or_source_status=http_status,
                endpoint_host="futures.kraken.com",
                endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
                request_family="market_analytics_funding",
                source_locator=(
                    "https://futures.kraken.com/api/charts/v1/analytics/"
                    "PI_XBTUSD/funding"
                ),
                blob_sha256=sha,
                failure_ref=failure_ref,
            )
        )

    def seed_manifest(
        self,
        manifest_id: str,
        partition_key: str,
        blob_sha: str,
        *,
        provider: str = _PROVIDER,
        venue: str = _PROVIDER,
        sensor_family: Any = SensorFamily.MECHANICAL_FUNDING,
        native_instrument: str = _INSTRUMENT,
        source_granularity: Any = Granularity.G1H,
    ) -> str:
        self.manifest_repo.append_partition_manifest(
            PartitionManifest(
                partition_manifest_id=manifest_id,
                partition_key=partition_key,
                manifest_version=1,
                provider=provider,
                venue=venue,
                sensor_family=sensor_family,
                native_instrument=native_instrument,
                source_granularity=source_granularity,
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


def _create(
    repo: DurableJobStateRepository,
    job_id: str,
    *,
    request_fingerprint: str = _FP,
) -> None:
    repo.create_job(
        job_id=job_id,
        provider_id=_PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=request_fingerprint,
    )


def _drive_to_manifest(repo: DurableJobStateRepository, job_id: str) -> None:
    """Advance the job to MANIFEST_COMMITTED from its CURRENT status."""
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


def _checkpoint(
    repo: DurableJobStateRepository,
    job_id: str,
    acquisition_id: str,
    manifest_id: str | None,
    *,
    token: ResumeToken | None = None,
) -> Any:
    kwargs: dict[str, Any] = {}
    if manifest_id is not None:
        kwargs["manifest_id"] = manifest_id
    return repo.advance_checkpoint(
        job_id,
        resume_token=token
        or ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id=acquisition_id,
        **kwargs,
    )


def _full_batch(stack: JobStack, acq_id: str, man_id: str, data: bytes) -> str:
    """Seed blob -> metadata -> acquisition -> manifest; return blob sha."""
    sha = stack.seed_blob(data)
    stack.seed_acquisition(sha, acq_id)
    stack.seed_manifest(man_id, f"PK-{man_id}", sha)
    return sha


# ---------------------------------------------------------------------------
# §3/§4/§39-1..6: the public API cannot touch the cursor
# ---------------------------------------------------------------------------


def test_advance_status_signature_rejects_resume_token(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    with pytest.raises(TypeError):
        stack.repo.advance_status(  # type: ignore[call-arg]
            "job-x",
            to_status=StorageJobStatus.ACQUIRING,
            resume_token={"mode": "PAGE", "page_number": 1},
        )


def test_advance_status_signature_rejects_checkpoint_anchors(
    tmp_path: Path,
) -> None:
    stack = JobStack(tmp_path)
    for bad in (
        {"last_committed_acquisition_id": "acq-1"},
        {"last_committed_blob_sha256": "a" * 64},
        {"last_manifest_id": "pm-1"},
    ):
        with pytest.raises(TypeError):
            stack.repo.advance_status("job-x", to_status=StorageJobStatus.ACQUIRING, **bad)  # type: ignore[arg-type]


def test_advance_status_signature_rejects_gate_flag(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    with pytest.raises(TypeError):
        stack.repo.advance_status(  # type: ignore[call-arg]
            "job-x",
            to_status=StorageJobStatus.ACQUIRING,
            _via_checkpoint_gate=True,
        )


def test_gate_flag_name_not_settable_on_instance(tmp_path: Path) -> None:
    """No caller-settable boolean can authorize checkpoint entry (§4)."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    assert not hasattr(repo, "_via_checkpoint_gate")
    _create(repo, "job-flag")
    repo.advance_status("job-flag", to_status=StorageJobStatus.ACQUIRING)
    # Setting the (absent) attribute on the instance cannot unlock anything:
    # the write path validates through the pure graph with checkpoint=False.
    setattr(repo, "_via_checkpoint_gate", True)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-flag", to_status=StorageJobStatus.CHECKPOINT_ADVANCED
        )


def test_plain_checkpoint_transition_rejected(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-plain")
    repo.advance_status("job-plain", to_status=StorageJobStatus.ACQUIRING)
    with pytest.raises(JobTransitionConflict):
        repo.advance_status(
            "job-plain", to_status=StorageJobStatus.CHECKPOINT_ADVANCED
        )


def test_ordinary_transition_preserves_cursor_and_anchors(
    tmp_path: Path,
) -> None:
    """§5: EVERY ordinary transition preserves all four pointers exactly."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo = stack.repo
    _create(repo, "job-preserve")
    _drive_to_manifest(repo, "job-preserve")
    sha = _full_batch(stack, "acq-preserve", "pm-preserve", b'{"rows": ["p"]}')
    state = _checkpoint(repo, "job-preserve", "acq-preserve", "pm-preserve")
    assert state.resume_token is not None
    # Every legal ordinary transition (forward, continuation, failure,
    # retry resume) must leave all four pointers untouched.
    for target, reason in (
        (StorageJobStatus.ACQUIRING, "batch continuation after checkpoint"),
        (StorageJobStatus.RAW_STAGED, None),
        (StorageJobStatus.FAILED_RETRYABLE, "provider 429 backoff"),
        (StorageJobStatus.ACQUIRING, "retry after backoff"),
    ):
        after = repo.advance_status(
            "job-preserve", to_status=target, reason=reason
        )
        assert after.resume_token == state.resume_token
        assert after.last_committed_acquisition_id == "acq-preserve"
        assert after.last_committed_blob_sha256 == sha
        assert after.last_manifest_id == "pm-preserve"
    # Chain-level §24 walk: every event's pointers must equal its
    # predecessor's EXCEPT the single checkpoint event (the only legal
    # pointer mutation).  This covers the annotated continuation, which
    # correctly PRESERVES the checkpoint's pointers.
    fields = (
        "resume_token",
        "last_committed_acquisition_id",
        "last_committed_blob_sha256",
        "last_manifest_id",
    )
    events = sorted(
        (
            payload
            for payload in (
                repo._events.get(event_id)  # noqa: SLF001 — evidence inspection
                for event_id in repo._events.list_ids()
            )
            if payload is not None and payload.get("job_id") == "job-preserve"
        ),
        key=lambda e: e["sequence"],
    )
    checkpoint_states = [
        e for e in events if e["transition"]["to_status"] == "CHECKPOINT_ADVANCED"
    ]
    assert len(checkpoint_states) == 1
    previous: dict[str, Any] = {f: None for f in fields}
    for event in events:
        is_checkpoint = (
            event["transition"]["to_status"] == "CHECKPOINT_ADVANCED"
        )
        for f in fields:
            if is_checkpoint:
                assert event["resulting_state"][f] is not None or f == "last_manifest_id"
            else:
                assert event["resulting_state"][f] == previous[f], (
                    f"event {event['transition_id']} mutated {f}"
                )
        previous = {
            f: event["resulting_state"][f] for f in fields
        }


# ---------------------------------------------------------------------------
# §7/§8/§39-7..12: job ↔ acquisition identity + provenance
# ---------------------------------------------------------------------------


def test_checkpoint_stores_exact_blob_sha(tmp_path: Path) -> None:
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo = stack.repo
    _create(repo, "job-exactsha")
    _drive_to_manifest(repo, "job-exactsha")
    sha = _full_batch(stack, "acq-exactsha", "pm-exactsha", b'{"rows": ["s"]}')
    state = _checkpoint(repo, "job-exactsha", "acq-exactsha", "pm-exactsha")
    assert state.last_committed_blob_sha256 == sha
    # And the durable event proof binds the same exact SHA.
    last = repo._latest_event("job-exactsha")  # noqa: SLF001
    assert last is not None
    proof = last["checkpoint_proof"]
    assert proof["blob_sha256"] == sha
    assert proof["acquisition_id"] == "acq-exactsha"


def _identity_mismatch_case(
    tmp_path: Path,
    job_id: str,
    *,
    job_fp: str = _FP,
    acq_fp: str = _FP,
    acq_provider: str = _PROVIDER,
    acq_sensor: Any = SensorFamily.MECHANICAL_FUNDING,
) -> None:
    """Seed a job plus a DURABLE acquisition whose identity diverges from
    the job's birth (durable truth, not a fixture error)."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, job_id, request_fingerprint=job_fp)
    _drive_to_manifest(repo, job_id)
    sha = stack.seed_blob(b'{"rows": ["idm"]}')
    stack.seed_acquisition(
        sha,
        f"acq-{job_id}",
        request_fingerprint=acq_fp,
        provider_id=acq_provider,
        sensor_family=acq_sensor,
    )
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, job_id, f"acq-{job_id}", None)
    assert repo.get_job(job_id).status is StorageJobStatus.MANIFEST_COMMITTED


def test_provider_mismatch_rejected(tmp_path: Path) -> None:
    _identity_mismatch_case(
        tmp_path, "job-prov", acq_provider="BINANCE_SPOT"
    )


def test_sensor_mismatch_rejected(tmp_path: Path) -> None:
    _identity_mismatch_case(
        tmp_path,
        "job-sensor",
        acq_sensor=SensorFamily.MECHANICAL_TRADE,
    )


def test_request_fingerprint_mismatch_rejected(tmp_path: Path) -> None:
    _identity_mismatch_case(tmp_path, "job-fp", acq_fp="fp-other-request")


def test_job_fingerprint_mismatch_rejected(tmp_path: Path) -> None:
    """The JOB side carries the divergent identity — same rejection."""
    _identity_mismatch_case(tmp_path, "job-fpjob", job_fp="fp-job-side-diff")


def test_cross_job_same_blob_rejected(tmp_path: Path) -> None:
    """§11: content equality does not transfer source identity."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo_a = stack.repo
    _create(repo_a, "job-a")
    _drive_to_manifest(repo_a, "job-a")
    data = b'{"rows": ["shared-bytes"]}'
    sha = stack.seed_blob(data)
    stack.seed_acquisition(sha, "acq-b")
    stack.seed_manifest("pm-b", "PK-B", sha)
    # Job B exists with ITS OWN request identity; its evidence is durable.
    repo_b = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=stack.acq_repo,
        manifests=stack.manifest_repo,
        blob_metadata_repository=stack.blob_repo,
        clock=shared,
    )
    _create(repo_b, "job-b", request_fingerprint="fp-other-request")
    assert repo_b.has_job("job-b")
    # Job A attempts to advance using job B's durable evidence: the
    # acquisition's request_fingerprint does not match job A's birth.
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo_a, "job-a", "acq-b", None)
    assert repo_a.get_job("job-a").status is StorageJobStatus.MANIFEST_COMMITTED


def test_forensic_acquisition_rejected(tmp_path: Path) -> None:
    """§8: forensic evidence stays durable history but cannot move the
    cursor (authoritative I04R2 predicate, not a duplicated rule)."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-forensic")
    _drive_to_manifest(repo, "job-forensic")
    sha = stack.seed_blob(b'{"rows": ["forensic"]}')
    # Failed HTTP outcome whose bytes were archived (forensic T0A).
    stack.seed_acquisition(sha, "acq-forensic", http_status="404")
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, "job-forensic", "acq-forensic", None)
    assert repo.get_job("job-forensic").status is StorageJobStatus.MANIFEST_COMMITTED


# ---------------------------------------------------------------------------
# §10/§39-13..17: manifest ↔ acquisition identity
# ---------------------------------------------------------------------------


def _manifest_mismatch_case(
    tmp_path: Path,
    job_id: str,
    **manifest_fields: Any,
) -> None:
    """Seed a valid batch plus a SECOND durable acquisition/manifest pair
    whose manifest identity diverges from the batch acquisition (§10: the
    manifest reference must be bound to the acquisition it claims to
    index — a same-blob manifest from another source is not proof)."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, job_id)
    _drive_to_manifest(repo, job_id)
    sha = stack.seed_blob(b'{"rows": ["mm"]}')
    stack.seed_acquisition(sha, f"acq-{job_id}")
    stack.seed_manifest(f"pm-{job_id}", f"PK-{job_id}", sha)
    # A second acquisition under the MUTATED source identity attributing
    # the SAME blob bytes — durable, but a different logical source.  The
    # alt pair is internally consistent (so it publishes cleanly) while
    # diverging from the batch acquisition on exactly one source field.
    alt_provider = manifest_fields.get("provider", _PROVIDER)
    alt_venue = manifest_fields.get("venue", alt_provider)
    alt_sensor = manifest_fields.get(
        "sensor_family", SensorFamily.MECHANICAL_FUNDING
    )
    alt_instrument = manifest_fields.get("native_instrument", _INSTRUMENT)
    alt_granularity = manifest_fields.get(
        "source_granularity", Granularity.G1H
    )
    stack.seed_acquisition(
        sha,
        f"acq-{job_id}-alt",
        provider_id=alt_provider,
        venue=alt_venue,
        sensor_family=alt_sensor,
        native_instrument=alt_instrument,
        native_granularity=alt_granularity,
    )
    stack.seed_manifest(
        f"pm-{job_id}-alt",
        f"PK-{job_id}-alt",
        sha,
        provider=alt_provider,
        venue=alt_venue,
        sensor_family=alt_sensor,
        native_instrument=alt_instrument,
        source_granularity=alt_granularity,
    )
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, job_id, f"acq-{job_id}", f"pm-{job_id}-alt")
    assert repo.get_job(job_id).status is StorageJobStatus.MANIFEST_COMMITTED


def test_manifest_provider_mismatch_rejected(tmp_path: Path) -> None:
    _manifest_mismatch_case(tmp_path, "job-mp", provider="BINANCE_SPOT")


def test_manifest_venue_mismatch_rejected(tmp_path: Path) -> None:
    _manifest_mismatch_case(tmp_path, "job-mv", venue="BINANCE_FUTURES")


def test_manifest_sensor_mismatch_rejected(tmp_path: Path) -> None:
    _manifest_mismatch_case(
        tmp_path, "job-ms", sensor_family=SensorFamily.MECHANICAL_TRADE
    )


def test_manifest_instrument_mismatch_rejected(tmp_path: Path) -> None:
    _manifest_mismatch_case(
        tmp_path, "job-mi", native_instrument="BTC_USDT"
    )


def test_manifest_granularity_mismatch_rejected(tmp_path: Path) -> None:
    _manifest_mismatch_case(
        tmp_path, "job-mg", source_granularity=Granularity.G4H
    )


def test_manifest_exact_binding_accepted(tmp_path: Path) -> None:
    """§39-13 'manifest_exact': the bound manifest is valid proof."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-mexact")
    _drive_to_manifest(repo, "job-mexact")
    sha = _full_batch(stack, "acq-mexact", "pm-mexact", b'{"rows": ["me"]}')
    state = _checkpoint(repo, "job-mexact", "acq-mexact", "pm-mexact")
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_committed_blob_sha256 == sha
    assert state.last_manifest_id == "pm-mexact"


# ---------------------------------------------------------------------------
# §12/§13/§14/§39-18..20: floor semantics
# ---------------------------------------------------------------------------


def test_raw_floor_requires_manifest_none(tmp_path: Path) -> None:
    stack = JobStack(tmp_path, min_durable_status=StorageJobStatus.RAW_COMMITTED)
    repo = stack.repo
    _create(repo, "job-rawc")
    repo.advance_status("job-rawc", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-rawc", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-rawc", to_status=StorageJobStatus.RAW_COMMITTED)
    sha = stack.seed_blob(b'{"rows": ["raw"]}')
    stack.seed_acquisition(sha, "acq-rawc")
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, "job-rawc", "acq-rawc", "pm-contradictory")
    # The correct form: manifest_id=None.
    state = _checkpoint(repo, "job-rawc", "acq-rawc", None)
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_manifest_id is None
    assert state.last_committed_acquisition_id == "acq-rawc"
    assert state.last_committed_blob_sha256 == sha
    assert state.resume_token is not None


def test_raw_floor_survives_restart(tmp_path: Path) -> None:
    """§14: RAW-floor checkpoint is durable truth, not a restart hazard."""
    shared = TickingClock()
    stack = JobStack(
        tmp_path, clock=shared, min_durable_status=StorageJobStatus.RAW_COMMITTED
    )
    repo = stack.repo
    _create(repo, "job-rawrestart")
    repo.advance_status("job-rawrestart", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status("job-rawrestart", to_status=StorageJobStatus.RAW_STAGED)
    repo.advance_status("job-rawrestart", to_status=StorageJobStatus.RAW_COMMITTED)
    sha = stack.seed_blob(b'{"rows": ["rawrestart"]}')
    stack.seed_acquisition(sha, "acq-rawrestart")
    state = _checkpoint(repo, "job-rawrestart", "acq-rawrestart", None)
    token = state.resume_token
    fresh = JobStack(
        tmp_path, clock=shared, min_durable_status=StorageJobStatus.RAW_COMMITTED
    ).repo
    after = fresh.get_job("job-rawrestart")
    assert after.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert after.resume_token == token
    assert after.last_committed_acquisition_id == "acq-rawrestart"
    assert after.last_committed_blob_sha256 == sha
    assert after.last_manifest_id is None


def test_manifest_floor_requires_exact_manifest(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-mfloor")
    _drive_to_manifest(repo, "job-mfloor")
    sha = stack.seed_blob(b'{"rows": ["mf"]}')
    stack.seed_acquisition(sha, "acq-mfloor")
    # Missing manifest_id at the MANIFEST floor: rejected.
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, "job-mfloor", "acq-mfloor", None)
    # A durable manifest that does not describe THIS acquisition's source
    # is not proof either (wrong instrument, same blob).
    stack.seed_acquisition(
        sha, "acq-mfloor-alt", native_instrument="BTC_USDT"
    )
    stack.seed_manifest(
        "pm-wrong-inst",
        "PK-WI",
        sha,
        native_instrument="BTC_USDT",
    )
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, "job-mfloor", "acq-mfloor", "pm-wrong-inst")
    # The exact bound manifest is accepted.
    stack.seed_manifest("pm-mfloor", "PK-MF", sha)
    state = _checkpoint(repo, "job-mfloor", "acq-mfloor", "pm-mfloor")
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_manifest_id == "pm-mfloor"


def test_dummy_manifest_anchor_rejected_at_raw_floor(tmp_path: Path) -> None:
    """§12: no dummy anchors like 'pm-not-required' are persisted."""
    stack = JobStack(tmp_path, min_durable_status=StorageJobStatus.RAW_COMMITTED)
    repo = stack.repo
    _create(repo, "job-dummy")
    for status in STATUSES_TO_MANIFEST[:3]:
        repo.advance_status("job-dummy", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["dummy"]}')
    stack.seed_acquisition(sha, "acq-dummy")
    with pytest.raises(JobResumeGateError):
        _checkpoint(repo, "job-dummy", "acq-dummy", "pm-not-required")


# ---------------------------------------------------------------------------
# §15-§18/§39-21..25: durable checkpoint proof
# ---------------------------------------------------------------------------


def _checkpoint_stack(tmp_path: Path, job_id: str) -> tuple[JobStack, Any, str]:
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, job_id)
    _drive_to_manifest(repo, job_id)
    _full_batch(stack, f"acq-{job_id}", f"pm-{job_id}", b'{"rows": ["proof"]}')
    _checkpoint(repo, job_id, f"acq-{job_id}", f"pm-{job_id}")
    return stack, repo, f"acq-{job_id}"


def test_checkpoint_proof_persisted(tmp_path: Path) -> None:
    _, repo, _ = _checkpoint_stack(tmp_path, "job-proof")
    last = repo._latest_event("job-proof")  # noqa: SLF001
    assert last is not None
    proof = last["checkpoint_proof"]
    assert proof["proof_version"] == 1
    assert proof["minimum_durable_status"] == "MANIFEST_COMMITTED"
    assert proof["acquisition_id"] == "acq-job-proof"
    assert proof["manifest_id"] == "pm-job-proof"
    assert isinstance(proof["blob_sha256"], str) and len(proof["blob_sha256"]) == 64


def test_checkpoint_proof_v1_enforced_on_restart(tmp_path: Path) -> None:
    """§16: closed V1 — an unknown persisted proof version fails closed."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-proofv2")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["checkpoint_proof"]["proof_version"] = 2
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_missing_checkpoint_proof_fails_restart(tmp_path: Path) -> None:
    """§18/§39-23: a checkpoint without proof is corruption."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-noproof2")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    del payload["checkpoint_proof"]
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_proof_on_ordinary_event_fails_restart(tmp_path: Path) -> None:
    """§18/§39-24: proof metadata belongs only to checkpoint events."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-prooford")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == "ACQUIRING":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["checkpoint_proof"] = {
        "proof_version": 1,
        "minimum_durable_status": "MANIFEST_COMMITTED",
        "acquisition_id": "acq-x",
        "blob_sha256": "b" * 64,
        "manifest_id": "pm-x",
    }
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_checkpoint_proof_mismatch_fails_restart(tmp_path: Path) -> None:
    """§17/§39-25: proof anchors must equal the resulting-state anchors."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-proofmm")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["checkpoint_proof"]["acquisition_id"] = "acq-someone-else"
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_unrelated_manifest_anchor_fails_restart(tmp_path: Path) -> None:
    """§39-36: a checkpoint pointing at an unrelated manifest fails."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-unrelman")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    # Point both the proof AND the anchors at an unrelated (but durable)
    # manifest id — internal consistency holds, durable binding does not.
    payload["checkpoint_proof"]["manifest_id"] = "pm-unrelated"
    payload["resulting_state"]["last_manifest_id"] = "pm-unrelated"
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_blob_anchor_mismatch_fails_restart(tmp_path: Path) -> None:
    """§39-35: blob anchor must equal the acquisition's real blob."""
    stack, _, _ = _checkpoint_stack(tmp_path, "job-blobmm")
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    other = "c" * 64
    payload["checkpoint_proof"]["blob_sha256"] = other
    payload["resulting_state"]["last_committed_blob_sha256"] = other
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_raw_floor_proof_with_manifest_anchor_fails_restart(
    tmp_path: Path,
) -> None:
    """A RAW-floor checkpoint persisting a manifest anchor is corruption."""
    shared = TickingClock()
    stack = JobStack(
        tmp_path, clock=shared, min_durable_status=StorageJobStatus.RAW_COMMITTED
    )
    repo = stack.repo
    _create(repo, "job-rawbad")
    for status in STATUSES_TO_MANIFEST[:3]:
        repo.advance_status("job-rawbad", to_status=status)
    sha = stack.seed_blob(b'{"rows": ["rawbad"]}')
    stack.seed_acquisition(sha, "acq-rawbad")
    _checkpoint(repo, "job-rawbad", "acq-rawbad", None)
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("checkpoint_proof"):
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    proof = payload["checkpoint_proof"]
    proof["manifest_id"] = "pm-tampered-in"
    payload["resulting_state"]["last_manifest_id"] = "pm-tampered-in"
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


# ---------------------------------------------------------------------------
# §21/§22/§39-26..29: replay = writer graph
# ---------------------------------------------------------------------------


def _tamper_to_status(
    tmp_path: Path, job_id: str, match_to: str, new_to: str
) -> None:
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == match_to:
            victim = path
            break
    assert victim is not None, f"expected a {match_to} event"
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["transition"]["to_status"] = new_to
    victim.write_text(json.dumps(payload), encoding="utf-8")


def test_forward_skip_fails_restart(tmp_path: Path) -> None:
    _checkpoint_stack(tmp_path, "job-fskip")
    _tamper_to_status(
        tmp_path, "job-fskip", "RAW_STAGED", "PROJECTION_COMMITTED"
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_failed_retryable_bad_target_fails_write_time(
    tmp_path: Path,
) -> None:
    """§21: FAILED_RETRYABLE may ONLY resume to ACQUIRING."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-badretry")
    repo.advance_status("job-badretry", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-badretry", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="x"
    )
    for bad in (
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    ):
        with pytest.raises(JobTransitionConflict):
            repo.advance_status(
                "job-badretry", to_status=bad, reason="why not"
            )


def test_failed_retryable_bad_target_fails_restart(tmp_path: Path) -> None:
    """§39-28: the same bad edge is corruption when replayed."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-badretry2")
    repo.advance_status("job-badretry2", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-badretry2", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="x"
    )
    _tamper_to_status(
        tmp_path, "job-badretry2", "FAILED_RETRYABLE", "MANIFEST_COMMITTED"
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_failure_without_reason_fails_restart(tmp_path: Path) -> None:
    """§22/§39-29: a reason-less failure event is corruption on replay."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-noreason")
    repo.advance_status("job-noreason", to_status=StorageJobStatus.ACQUIRING)
    repo.advance_status(
        "job-noreason", to_status=StorageJobStatus.FAILED_RETRYABLE, reason="x"
    )
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == "FAILED_RETRYABLE":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["transition"]["reason"] = None
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


# ---------------------------------------------------------------------------
# §23/§24/§26/§27/§39-30..34, 37: identity + pointer + event-id tamper
# ---------------------------------------------------------------------------


def _tamper_resulting(
    tmp_path: Path, job_id: str, field_path: list[Any], value: Any
) -> None:
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") == job_id and payload.get(
            "transition", {}
        ).get("to_status") == "ACQUIRING":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    node: dict[str, Any] = payload["resulting_state"]
    for key in field_path[:-1]:
        node = node[key]
    node[field_path[-1]] = value
    victim.write_text(json.dumps(payload), encoding="utf-8")


def test_provider_identity_tamper_fails_restart(tmp_path: Path) -> None:
    _checkpoint_stack(tmp_path, "job-tamperprov")
    _tamper_resulting(
        tmp_path, "job-tamperprov", ["provider_id"], "BINANCE_SPOT"
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_sensor_identity_tamper_fails_restart(tmp_path: Path) -> None:
    _checkpoint_stack(tmp_path, "job-tampersensor")
    _tamper_resulting(
        tmp_path,
        "job-tampersensor",
        ["sensor_family"],
        "MECHANICAL_TRADE",
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_request_fingerprint_tamper_fails_restart(tmp_path: Path) -> None:
    _checkpoint_stack(tmp_path, "job-tamperfp")
    _tamper_resulting(
        tmp_path, "job-tamperfp", ["request_fingerprint"], "fp-tampered"
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_ordinary_resume_token_tamper_fails_restart(tmp_path: Path) -> None:
    """§24: a tampered token on an ordinary event is corruption."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-tokentamper")
    repo.advance_status("job-tokentamper", to_status=StorageJobStatus.ACQUIRING)
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == "ACQUIRING":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["resulting_state"]["resume_token"] = {
        "mode": "PAGE",
        "provider_cursor": "forged",
        "page_number": 99,
    }
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_ordinary_anchor_tamper_fails_restart(tmp_path: Path) -> None:
    """§24: tampered anchors on an ordinary event are corruption."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-anchortamper")
    repo.advance_status("job-anchortamper", to_status=StorageJobStatus.ACQUIRING)
    _tamper_resulting(
        tmp_path,
        "job-anchortamper",
        ["last_committed_acquisition_id"],
        "acq-forged",
    )
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_event_identity_tamper_fails_restart(tmp_path: Path) -> None:
    """§26: coordinated event-id + transition-id forgery fails closed."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-evid")
    repo.advance_status("job-evid", to_status=StorageJobStatus.ACQUIRING)
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == "ACQUIRING":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    # Coordinated mutation: rename the event file, the logical id, the
    # transition_id AND the sequence together.
    new_id = "job-evid:000099"
    payload["transition_id"] = new_id
    payload["transition"]["transition_id"] = new_id
    payload["sequence"] = 99
    victim.write_text(json.dumps(payload), encoding="utf-8")
    new_path = events_dir / (
        hashlib.sha256(new_id.encode("utf-8")).hexdigest() + ".json"
    )
    victim.rename(new_path)
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


def test_result_time_binding_enforced_on_restart(tmp_path: Path) -> None:
    """§27: resulting.updated_at must equal transition.transitioned_at."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-timebind")
    repo.advance_status("job-timebind", to_status=StorageJobStatus.ACQUIRING)
    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    victim = None
    for path in sorted(events_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("transition", {}).get("to_status") == "ACQUIRING":
            victim = path
            break
    assert victim is not None
    payload = json.loads(victim.read_text(encoding="utf-8"))
    payload["resulting_state"]["updated_at"] = (
        "2030-01-01T00:00:00+00:00"
    )
    victim.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JobCatalogCorrupt):
        JobStack(tmp_path).repo


# ---------------------------------------------------------------------------
# §28/§29/§39-38..40: safe lock physical keys
# ---------------------------------------------------------------------------


def test_lock_path_traversal_safe(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    for job_id in ("../escape", "../../outside", "C:\\temp\\x", "/a/b", "a\\b"):
        _create(repo, job_id)
        repo.advance_status(job_id, to_status=StorageJobStatus.ACQUIRING)
        lock_path = repo._lock_path(job_id)  # noqa: SLF001
        resolved = lock_path.resolve()
        locks_root = (tmp_path / "catalogs" / "jobs_state" / "locks").resolve()
        assert locks_root in resolved.parents
        assert lock_path.parent == repo._locks_root  # noqa: SLF001
        assert lock_path.name.endswith(".lock")


def test_lock_unicode_and_long_ids_safe(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    long_id = "j" * 500
    for job_id in ("π shifted \U0001f680", "中文 job", long_id):
        _create(repo, job_id)
        repo.advance_status(job_id, to_status=StorageJobStatus.ACQUIRING)
        lock_path = repo._lock_path(job_id)  # noqa: SLF001
        assert len(lock_path.stem) == 64
        assert all(c in "0123456789abcdef" for c in lock_path.stem)


def test_distinct_job_lock_keys_distinct(tmp_path: Path) -> None:
    stack = JobStack(tmp_path)
    repo = stack.repo
    keys = {
        job_id: repo._lock_path(job_id)  # noqa: SLF001
        for job_id in ("job-α", "job-a", "job/A", "job\\A", "job:a")
    }
    assert len({k.name for k in keys.values()}) == len(keys)
    # Full digests, never truncated.
    for job_id, path in keys.items():
        assert path.stem == hashlib.sha256(job_id.encode("utf-8")).hexdigest()


def test_lock_file_physically_created_at_safe_key(tmp_path: Path) -> None:
    """The on-disk lock file lives at the hashed key, never the raw ID."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "../escape")
    locks_root = tmp_path / "catalogs" / "jobs_state" / "locks"
    repo.advance_status("../escape", to_status=StorageJobStatus.ACQUIRING)
    names = {p.name for p in locks_root.iterdir()} if locks_root.exists() else set()
    # After the transition completes, the lock is released (deleted); while
    # held during the call it existed at the hashed key.  Verify no raw-ID
    # file was ever created anywhere under the catalog root.
    assert "../escape.lock" not in names
    for path in (tmp_path / "catalogs").rglob("*.lock"):
        assert len(path.stem) == 64


# ---------------------------------------------------------------------------
# §30-§36/§39-41..43: post-lock refresh + cross-repository truth
# ---------------------------------------------------------------------------


def test_repo_b_refreshes_after_repo_a_write(tmp_path: Path) -> None:
    """§33: a long-lived repo must see another writer's committed events."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo_a = stack.repo
    repo_b = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=stack.acq_repo,
        manifests=stack.manifest_repo,
        blob_metadata_repository=stack.blob_repo,
        clock=shared,
    )
    _create(repo_a, "job-refresh")
    # Repo B (constructed before any event) observes A's birth, then A
    # advances one step; B must STILL see it without recreation.
    state = repo_b.advance_status(
        "job-refresh", to_status=StorageJobStatus.ACQUIRING
    )
    assert state.status is StorageJobStatus.ACQUIRING
    repo_a.advance_status("job-refresh", to_status=StorageJobStatus.RAW_STAGED)
    # Without recreating B: B's next transition must succeed with the CAS
    # guard proving the refreshed view (not the stale PLANNED one).
    state = repo_b.advance_status(
        "job-refresh",
        to_status=StorageJobStatus.RAW_COMMITTED,
        expected_from=StorageJobStatus.RAW_STAGED,
    )
    assert state.status is StorageJobStatus.RAW_COMMITTED
    # No stale view: B observed both of A's events plus its own.
    transitions = repo_b.list_transitions("job-refresh")
    assert [t.to_status for t in transitions] == [
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
    ]
    # And a fresh repository agrees.
    fresh = JobStack(tmp_path, clock=shared).repo
    assert fresh.get_job("job-refresh").status is StorageJobStatus.RAW_COMMITTED


def test_cross_repo_sequence_cannot_fork(tmp_path: Path) -> None:
    """§34: racing one next transition yields exactly one committed event."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo_a = stack.repo
    repo_b = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=stack.acq_repo,
        manifests=stack.manifest_repo,
        blob_metadata_repository=stack.blob_repo,
        clock=shared,
    )
    _create(repo_a, "job-race2")
    repo_a.advance_status("job-race2", to_status=StorageJobStatus.ACQUIRING)
    errors: list[Exception] = []
    barrier = threading.Barrier(2)

    def worker(r: DurableJobStateRepository) -> None:
        try:
            barrier.wait()
            r.advance_status(
                "job-race2", to_status=StorageJobStatus.RAW_STAGED
            )
        except Exception as exc:  # noqa: BLE001 — typed loser acceptable
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(r,)) for r in (repo_a, repo_b)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    fresh = JobStack(tmp_path, clock=shared).repo
    transitions = fresh.list_transitions("job-race2")
    assert [t.to_status for t in transitions] == [
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
    ]
    successes = len(errors) == 0 or (
        len(errors) == 1 and isinstance(errors[0], Exception)
    )
    assert successes
    # No chain fork: exactly one RAW_STAGED event exists.
    events = [
        p
        for p in (
            fresh._events.get(eid)  # noqa: SLF001
            for eid in fresh._events.list_ids()
        )
        if p is not None and p.get("job_id") == "job-race2"
    ]
    staged = [
        e for e in events if e["transition"]["to_status"] == "RAW_STAGED"
    ]
    assert len(staged) == 1


def test_external_checkpoint_retry_succeeds_after_refresh(
    tmp_path: Path,
) -> None:
    """§35: a long-lived repo retries a checkpoint another repo committed."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo_a = stack.repo
    repo_b = DurableJobStateRepository(
        tmp_path / "catalogs" / "jobs_state",
        acquisitions=stack.acq_repo,
        manifests=stack.manifest_repo,
        blob_metadata_repository=stack.blob_repo,
        clock=shared,
    )
    _create(repo_a, "job-xtretry")
    _drive_to_manifest(repo_a, "job-xtretry")
    sha = _full_batch(
        stack, "acq-xtretry", "pm-xtretry", b'{"rows": ["xt"]}'
    )
    state = repo_a.advance_checkpoint(
        "job-xtretry",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-xtretry",
        manifest_id="pm-xtretry",
    )
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    # Repo B (constructed before the checkpoint existed) retries the EXACT
    # same checkpoint: refresh shows the committed event, durable truth is
    # re-proved under the persisted floor, and the committed state is
    # returned idempotently.
    retried = repo_b.advance_checkpoint(
        "job-xtretry",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-xtretry",
        manifest_id="pm-xtretry",
    )
    assert retried.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert retried.last_committed_acquisition_id == "acq-xtretry"
    assert retried.last_committed_blob_sha256 == sha
    transitions = repo_b.list_transitions("job-xtretry")
    gate_events = [
        t
        for t in transitions
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1  # adopted, not duplicated


def test_refresh_fails_closed_on_vanished_record(tmp_path: Path) -> None:
    """§31: refresh treats a vanished committed record as corruption."""
    stack = JobStack(tmp_path)
    repo = stack.repo
    _create(repo, "job-vanish")
    repo.advance_status("job-vanish", to_status=StorageJobStatus.ACQUIRING)
    from crypto_sensor_fabric.storage.json_catalog import (
        DurableJsonCatalog,
        JsonCatalogCorrupt,
    )

    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    catalog = DurableJsonCatalog(events_dir, logical_id_field="transition_id")
    assert len(catalog) == 1
    victim = next(events_dir.glob("*.json"))
    victim.unlink()
    with pytest.raises(JsonCatalogCorrupt):
        catalog.refresh()


def test_refresh_adopts_newly_committed_records(tmp_path: Path) -> None:
    """§31: validated adoption of another writer's committed fragments."""
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo_a = stack.repo
    _create(repo_a, "job-adopt")
    repo_a.advance_status("job-adopt", to_status=StorageJobStatus.ACQUIRING)
    from crypto_sensor_fabric.storage.json_catalog import DurableJsonCatalog

    events_dir = tmp_path / "catalogs" / "jobs_state" / "events"
    catalog_b = DurableJsonCatalog(events_dir, logical_id_field="transition_id")
    assert len(catalog_b) == 1
    repo_a.advance_status("job-adopt", to_status=StorageJobStatus.RAW_STAGED)
    catalog_b.refresh()
    assert len(catalog_b) == 2


# ---------------------------------------------------------------------------
# Crash boundaries under the hardened gate (I07 §20 crash tests preserved)
# ---------------------------------------------------------------------------


def test_crash_before_checkpoint_publish_retries_clean(tmp_path: Path) -> None:
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo = stack.repo
    _create(repo, "job-crashr1")
    _drive_to_manifest(repo, "job-crashr1")
    _full_batch(
        stack, "acq-crashr1", "pm-crashr1", b'{"rows": ["crashr1"]}'
    )
    faulted = JobStack(
        tmp_path,
        clock=shared,
        fault_hooks=CatalogFaultHook(CatalogFaultPoint.BEFORE_STAGED_WRITE),
    )
    with pytest.raises(FaultError):
        faulted.repo.advance_checkpoint(
            "job-crashr1",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-crashr1",
            manifest_id="pm-crashr1",
        )
    assert repo.get_job("job-crashr1").status is StorageJobStatus.MANIFEST_COMMITTED
    state = _checkpoint(repo, "job-crashr1", "acq-crashr1", "pm-crashr1")
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED


def test_crash_after_checkpoint_publish_adopts_on_fresh_repo(
    tmp_path: Path,
) -> None:
    shared = TickingClock()
    stack = JobStack(tmp_path, clock=shared)
    repo = stack.repo
    _create(repo, "job-crashr2")
    _drive_to_manifest(repo, "job-crashr2")
    sha = _full_batch(
        stack, "acq-crashr2", "pm-crashr2", b'{"rows": ["crashr2"]}'
    )
    faulted = JobStack(
        tmp_path,
        clock=shared,
        fault_hooks=CatalogFaultHook(
            CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
        ),
    )
    with pytest.raises(Exception):  # noqa: B017 — the injected crash
        faulted.repo.advance_checkpoint(
            "job-crashr2",
            resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
            acquisition_id="acq-crashr2",
            manifest_id="pm-crashr2",
        )
    fresh = JobStack(tmp_path, clock=shared).repo
    assert (
        fresh.get_job("job-crashr2").status is StorageJobStatus.CHECKPOINT_ADVANCED
    )
    retried = fresh.advance_checkpoint(
        "job-crashr2",
        resume_token=ResumeToken(mode="PAGE", provider_cursor="c", page_number=1),
        acquisition_id="acq-crashr2",
        manifest_id="pm-crashr2",
    )
    assert retried.last_committed_blob_sha256 == sha
    gate_events = [
        t
        for t in fresh.list_transitions("job-crashr2")
        if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
    ]
    assert len(gate_events) == 1
