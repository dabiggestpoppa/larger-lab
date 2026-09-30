"""SENSOR-B4-I14 — Bloc 3 → Bloc 4 durable handoff tests.

All fixtures are synthetic/offline (§38): no socket, no live provider.
Core G4-12 blocking proof: adapter output persists AND the resume
checkpoint advances ONLY after durable PartitionManifest commit — and
the suite FAILS if the sequence is deliberately inverted (§66).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402


from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.providers.base.enums import (  # noqa: E402
    Granularity,
    PaginationMode,
    QualityFlagAcquisition,
)
from crypto_sensor_fabric.providers.base.fingerprint import (  # noqa: E402
    payload_hash,
)
from crypto_sensor_fabric.providers.base.models import (  # noqa: E402
    FetchBatch,
    RawPayloadEnvelope,
    ResumeToken,
)
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    StorageEncoding,
    StorageJobStatus,
)
from crypto_sensor_fabric.storage.integration import (  # noqa: E402
    BatchIdentityMismatch,
    Bloc3StorageContext,
    Bloc3StorageHandoff,
    DuplicateEnvelopeContent,
    EnvelopeContentHashMismatch,
    EnvelopeIdentityMismatch,
    FAULT_WINDOWS,
    FaultSimulated,
)
from crypto_sensor_fabric.storage.jobs import (  # noqa: E402
    DurableJobStateRepository,
)
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    SourceRevisionRegistry,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)


class TickingClock:
    """Deterministic advancing clock (fresh repositories read the same
    durable history; the clock only orders new events)."""

    def __init__(self) -> None:
        self._value = FIXED

    def __call__(self) -> datetime:
        self._value = self._value + timedelta(seconds=1)
        return self._value


def make_envelope(
    body: bytes,
    *,
    provider_id: str = "kraken",
    sensor_family: SensorFamily = SensorFamily.MECHANICAL_TRADE,
    request_fingerprint: str = "fp-job",
    content_type: str = "application/json",
) -> RawPayloadEnvelope:
    return RawPayloadEnvelope(
        provider_id=provider_id,
        sensor_family=sensor_family,
        request_fingerprint=request_fingerprint,
        content_type=content_type,
        raw_body=body,
        content_hash=payload_hash(body),
        adapter_version="1.0",
    )


def make_batch(
    bodies: list[bytes],
    *,
    provider_id: str = "kraken",
    sensor_family: SensorFamily = SensorFamily.MECHANICAL_TRADE,
    request_fingerprint: str = "fp-job",
    native_instrument_id: str = "XBT/USD",
    requested_start: datetime | None = None,
    retrieved_at: datetime | None = None,
    next_resume_token: ResumeToken | None = None,
    is_complete: bool = False,
    row_count: int | None = None,
    quality_flags: list[QualityFlagAcquisition] | None = None,
) -> FetchBatch:
    start = requested_start or datetime(2026, 1, 15, tzinfo=UTC)
    return FetchBatch(
        provider_id=provider_id,
        sensor_family=sensor_family,
        native_instrument_id=native_instrument_id,
        request_fingerprint=request_fingerprint,
        requested_start=start,
        requested_end=start + timedelta(minutes=59, seconds=59),
        raw_payloads=[
            make_envelope(
                body,
                provider_id=provider_id,
                sensor_family=sensor_family,
                request_fingerprint=request_fingerprint,
            )
            for body in bodies
        ],
        row_count=(len(bodies) * 5 if row_count is None else row_count),
        next_resume_token=next_resume_token,
        is_complete=is_complete,
        http_status=200,
        retrieved_at=retrieved_at or datetime(2026, 1, 15, 1, 0, tzinfo=UTC),
        quality_flags=quality_flags or [],
        adapter_version="1.0",
    )


def make_context() -> Bloc3StorageContext:
    return Bloc3StorageContext(
        venue="kraken_spot",
        source_granularity=Granularity.G1M,
        endpoint_host="api.kraken.example",
        endpoint_path="/v3/trades",
        request_family="trades",
    )


class HandoffStack:
    """Real durable dependency stack rooted at a tmp root (§47/§16: every
    crash test reconstructs ALL repositories from disk — no shared memory)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.t0a = root / "t0a"
        self.t0a.mkdir(parents=True, exist_ok=True)
        self.store = LocalBlobStore(str(self.t0a), clock=lambda: FIXED)
        self.blob_repo = BlobMetadataRepository(
            self.t0a, blob_store=self.store, clock=lambda: FIXED
        )
        self.acq_repo = AcquisitionRepository(
            self.t0a,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            clock=lambda: FIXED,
        )
        self.manifest_repo = PartitionManifestRepository(
            self.t0a,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            clock=lambda: FIXED,
        )
        self.registry = SourceRevisionRegistry(
            self.t0a / "revisions",
            acquisition_repository=self.acq_repo,
            blob_metadata_repository=self.blob_repo,
            blob_store=self.store,
            clock=lambda: FIXED,
        )
        self.jobs_repo = DurableJobStateRepository(
            root / "t0a" / "catalogs" / "jobs_state",
            acquisitions=self.acq_repo,
            manifests=self.manifest_repo,
            blob_metadata_repository=self.blob_repo,
            clock=lambda: FIXED,
            min_durable_status=__import__(
                "crypto_sensor_fabric.storage.jobs", fromlist=["StorageJobStatus"]
            ).StorageJobStatus.MANIFEST_COMMITTED,
        )
        self.handoff = Bloc3StorageHandoff(
            jobs=self.jobs_repo,
            blob_store=self.store,
            blob_metadata=self.blob_repo,
            acquisitions=self.acq_repo,
            manifests=self.manifest_repo,
            revisions=self.registry,
            clock=lambda: FIXED,
        )

    def fresh(self) -> "HandoffStack":
        """Reconstruct EVERYTHING from disk (§47 restart proof)."""
        return HandoffStack(self.root)


def semantic_digest(stack: HandoffStack, job_id: str) -> str:
    """Canonical final durable state digest (§48)."""
    state = stack.jobs_repo.get_job(job_id)
    payloads: dict[str, object] = {
        "job_status": state.status.value,
        "resume_mode": (
            state.resume_token.mode.value if state.resume_token else None
        ),
        "resume_page": (
            state.resume_token.page_number if state.resume_token else None
        ),
        "resume_cursor": (
            state.resume_token.provider_cursor if state.resume_token else None
        ),
        "last_acq": state.last_committed_acquisition_id,
        "last_blob": state.last_committed_blob_sha256,
        "last_manifest": state.last_manifest_id,
        "transitions": [
            [t.from_status.value, t.to_status.value]
            for t in stack.jobs_repo.list_transitions(job_id)
        ],
        "blobs": sorted(
            b.blob_sha256 for b in stack.blob_repo.list_all_blob_metadata()
        ),
        "acquisitions": sorted(
            a.acquisition_id
            for a in stack.acq_repo.list_all_acquisitions()
        ),
        "manifests": sorted(
            m.partition_manifest_id
            for m in stack.manifest_repo.list_all_current_manifests()
        ),
        "revision_segments": sorted(
            s.segment_id
            for key in stack.registry.list_source_revision_keys()
            for s in stack.registry.list_segment_records(key)
        ),
    }
    canonical = json.dumps(
        payloads, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def register_job(stack: HandoffStack, job_id: str, batch: FetchBatch) -> None:
    stack.jobs_repo.create_job(
        job_id=job_id,
        provider_id=batch.provider_id,
        sensor_family=batch.sensor_family,
        request_fingerprint=batch.request_fingerprint,
    )


# ---------------------------------------------------------------------------
# Core G4-12 handoff tests
# ---------------------------------------------------------------------------


class TestBatchIdentityAndContentLaw:
    def test_batch_identity_mismatch_refused_before_mutation(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}'])
        register_job(stack, "job-1", batch)
        other = make_batch([b'{"a": 1}'], request_fingerprint="fp-OTHER")
        with pytest.raises(BatchIdentityMismatch):
            stack.handoff.persist_batch(
                job_id="job-1", batch=other, context=make_context()
            )
        # No storage mutation happened.
        assert stack.jobs_repo.get_job("job-1").status is StorageJobStatus.PLANNED
        assert not list(stack.t0a.glob("objects/**"))

    def test_foreign_envelope_refused(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}'])
        register_job(stack, "job-1", batch)
        foreign = make_envelope(
            b'{"b": 2}', request_fingerprint="fp-foreign"
        )
        bad = batch.model_copy(update={"raw_payloads": [foreign]})
        with pytest.raises(EnvelopeIdentityMismatch):
            stack.handoff.persist_batch(
                job_id="job-1", batch=bad, context=make_context()
            )

    def test_content_hash_mismatch_refused(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}'])
        register_job(stack, "job-1", batch)
        lying = make_envelope(b'{"a": 1}')
        lying = lying.model_copy(update={"content_hash": "0" * 64})
        bad = batch.model_copy(update={"raw_payloads": [lying]})
        with pytest.raises(EnvelopeContentHashMismatch):
            stack.handoff.persist_batch(
                job_id="job-1", batch=bad, context=make_context()
            )

    def test_duplicate_content_in_batch_refused(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}', b'{"a": 1}'])
        register_job(stack, "job-1", batch)
        with pytest.raises(DuplicateEnvelopeContent):
            stack.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )

    def test_multi_envelope_batch_persists_all(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"p": 1}', b'{"p": 2}', b'{"p": 3}'])
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert len(receipt.acquisition_ids) == 3
        assert len(receipt.blob_shas) == 3
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        assert sorted(manifest.blob_refs) == sorted(receipt.blob_shas)


class TestG412CoreFlow:
    def test_successful_batch_advances_checkpoint_after_manifest(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        token = ResumeToken(
            mode=PaginationMode.PAGE, page_number=2
        )
        batch = make_batch(
            [b'{"rows": [1, 2, 3]}'],
            next_resume_token=token,
        )
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        # §51 structural ordering proof: the manifest is durable and
        # re-readable BEFORE the checkpoint exists.
        manifest = stack.manifest_repo.get_manifest(receipt.manifest_id)
        assert receipt.blob_shas[0] in manifest.blob_refs
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.last_manifest_id == receipt.manifest_id
        assert state.resume_token is not None
        assert state.resume_token.page_number == 2

    def test_checkpoint_refuses_without_manifest_at_manifest_floor(
        self, tmp_path
    ) -> None:
        """The G4-12 core: the accepted I07 gate cannot be passed with raw
        evidence alone at the MANIFEST_COMMITTED floor."""
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}'])
        register_job(stack, "job-1", batch)
        stack.jobs_repo.advance_status(
            "job-1", to_status=StorageJobStatus.ACQUIRING
        )
        stack.jobs_repo.advance_status(
            "job-1", to_status=StorageJobStatus.RAW_STAGED
        )
        from crypto_sensor_fabric.storage import StorageEncoding
        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        data = b'{"a": 1}'
        put = stack.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE,
            source_media_type="application/json",
        )
        stack.blob_repo.append_metadata(put.blob)
        record = AcquisitionRecord(
            acquisition_id="acq-no-manifest",
            provider_id=batch.provider_id,
            venue="kraken_spot",
            sensor_family=batch.sensor_family,
            request_fingerprint=batch.request_fingerprint,
            adapter_version="1.0",
            requested_start=batch.requested_start,
            requested_end=batch.requested_end,
            native_instrument=batch.native_instrument_id,
            native_granularity=Granularity.G1M,
            request_started_at=batch.retrieved_at,
            response_observed_at=batch.retrieved_at,
            ingested_at=FIXED,
            http_status_or_source_status="200",
            endpoint_host="api.kraken.example",
            endpoint_path="/v3/trades",
            request_family="trades",
            source_locator="bloc3://kraken/fp",
            blob_sha256=put.blob.blob_sha256,
        )
        stack.acq_repo.append_acquisition(record)
        from crypto_sensor_fabric.storage.jobs import JobResumeGateError

        with pytest.raises(JobResumeGateError):
            stack.jobs_repo.advance_checkpoint(
                "job-1",
                resume_token=None,
                acquisition_id="acq-no-manifest",
                manifest_id=None,
            )
        # Cursor did NOT move.
        state = stack.jobs_repo.get_job("job-1")
        assert state.resume_token is None
        assert state.status is not StorageJobStatus.CHECKPOINT_ADVANCED

    def test_partial_batch_keeps_resume_token_no_complete(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        token = ResumeToken(mode=PaginationMode.PAGE, page_number=7)
        batch = make_batch([b'{"a": 1}'], next_resume_token=token)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert receipt.complete is False
        state = stack.jobs_repo.get_job("job-1")
        assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED

    def test_complete_batch_reaches_complete_exactly_once(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"a": 1}'], is_complete=True)
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert receipt.complete is True
        assert stack.jobs_repo.get_job("job-1").status is (
            StorageJobStatus.COMPLETE
        )
        # §50: retry after COMPLETE must not mutate the frozen chain.
        frozen = semantic_digest(stack, "job-1")
        again = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert again.complete is True
        assert again.checkpoint_advanced is False
        assert semantic_digest(stack, "job-1") == frozen


class TestEmptyValidLaw:
    def test_empty_valid_batch_never_fabricates_bytes(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [],
            row_count=0,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
        )
        register_job(stack, "job-1", batch)
        receipt = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        # §10: no fake T0A bytes.  A zero-envelope EMPTY_VALID batch carries
        # no acquisition, so there is nothing to anchor a manifest-floor
        # checkpoint to — the handoff records durable truth (nothing) and
        # the adapter's cursor semantics are untouched (no token invented).
        assert receipt.blob_shas == ()
        assert receipt.acquisition_ids == ()
        state = stack.jobs_repo.get_job("job-1")
        assert state.resume_token is None


# -------------------------------------------------------------------------
# W1-W7 crash/restart matrix (§27/§28/§47/§48)
# -------------------------------------------------------------------------


def _crash_case(tmp_path, window: str):  # type: ignore[no-untyped-def]
    """Run the same batch with a crash injected at ``window``, restart with
    FRESH repositories, retry, and compare to the clean-run digest."""
    clean_root = tmp_path / "clean"
    clean_root.mkdir()
    clean = HandoffStack(clean_root)
    token = ResumeToken(mode=PaginationMode.PAGE, page_number=3)
    batch = make_batch([b'{"crash": 1}'], next_resume_token=token)
    register_job(clean, "job-1", batch)
    clean_receipt = clean.handoff.persist_batch(
        job_id="job-1", batch=batch, context=make_context()
    )
    clean_digest = semantic_digest(clean, "job-1")

    crash_root = tmp_path / "crash"
    crash_root.mkdir()
    crashed = HandoffStack(crash_root)
    register_job(crashed, "job-1", batch)
    crashed.handoff.fault_windows = {window}
    with pytest.raises(FaultSimulated):
        crashed.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
    before_token = crashed.jobs_repo.get_job("job-1").resume_token

    # §47: fresh repositories — nothing in memory survives the crash.
    restarted = crashed.fresh()
    after_token = restarted.jobs_repo.get_job("job-1").resume_token
    retry_receipt = restarted.handoff.persist_batch(
        job_id="job-1", batch=batch, context=make_context()
    )
    return (
        clean,
        clean_receipt,
        clean_digest,
        before_token,
        after_token,
        restarted,
        retry_receipt,
    )


class TestCrashRestartMatrix:
    @pytest.mark.parametrize("window", list(FAULT_WINDOWS))
    def test_resume_never_advances_and_digest_matches(
        self, tmp_path, window
    ) -> None:
        (
            clean,
            clean_receipt,
            clean_digest,
            before_token,
            after_token,
            restarted,
            retry_receipt,
        ) = _crash_case(tmp_path, window)
        # §28: resume token after crash == before crash (None here — no
        # prior batch).  No crash window consumes the batch.
        assert after_token == before_token
        assert after_token is None
        # §48: final durable semantic state matches the clean run.
        assert semantic_digest(restarted, "job-1") == clean_digest
        assert retry_receipt.manifest_id == clean_receipt.manifest_id
        assert retry_receipt.checkpoint_advanced is True

    def test_w7_manifest_durable_checkpoint_old_adopted(
        self, tmp_path
    ) -> None:
        """§29: after W7 the manifest IS durable; retry must NOT append a
        duplicate semantic manifest version and must advance exactly once."""
        clean_root = tmp_path / "clean"
        clean_root.mkdir()
        clean = HandoffStack(clean_root)
        batch = make_batch(
            [b'{"w7": 1}'],
            next_resume_token=ResumeToken(
                mode=PaginationMode.PAGE, page_number=9
            ),
        )
        register_job(clean, "job-1", batch)
        clean_receipt = clean.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )

        crash_root = tmp_path / "crash"
        crash_root.mkdir()
        crashed = HandoffStack(crash_root)
        register_job(crashed, "job-1", batch)
        crashed.handoff.fault_windows = {FAULT_WINDOWS[6]}  # W7
        with pytest.raises(FaultSimulated):
            crashed.handoff.persist_batch(
                job_id="job-1", batch=batch, context=make_context()
            )
        # The manifest IS durable but the checkpoint is OLD.
        assert (
            crashed.manifest_repo.get_manifest(clean_receipt.manifest_id)
            is not None
        )
        state = crashed.jobs_repo.get_job("job-1")
        assert state.status is not StorageJobStatus.CHECKPOINT_ADVANCED
        assert state.resume_token is None

        restarted = crashed.fresh()
        retry = restarted.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        assert retry.manifest_id == clean_receipt.manifest_id
        # Exactly ONE checkpoint transition across BOTH runs.
        checkpoint_transitions = [
            t
            for t in restarted.jobs_repo.list_transitions("job-1")
            if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        assert len(checkpoint_transitions) == 1
        assert semantic_digest(restarted, "job-1") == semantic_digest(
            clean, "job-1"
        )


# -------------------------------------------------------------------------
# Idempotence (§34/§49) and revision progression (§16)
# -------------------------------------------------------------------------


class TestDuplicateDelivery:
    def test_same_batch_persisted_twice_is_stable(self, tmp_path) -> None:
        stack = HandoffStack(tmp_path / "s")
        token = ResumeToken(mode=PaginationMode.PAGE, page_number=4)
        batch = make_batch([b'{"dup": 1}'], next_resume_token=token)
        register_job(stack, "job-1", batch)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        digest = semantic_digest(stack, "job-1")
        second = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        # Content dedupe; no second semantic advance (§34/§49).
        assert semantic_digest(stack, "job-1") == digest
        assert second.checkpoint_advanced is False
        assert first.checkpoint_advanced is True


class TestRevisionProgression:
    def test_same_request_different_bytes_two_revisions(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        first = make_batch([b'{"v": "A"}'])
        register_job(stack, "job-1", first)
        r1 = stack.handoff.persist_batch(
            job_id="job-1", batch=first, context=make_context()
        )
        stack.jobs_repo.advance_status(
            "job-1",
            to_status=StorageJobStatus.ACQUIRING,
            reason="batch continuation after checkpoint",
        )
        second = make_batch(
            [b'{"v": "B"}'],
            request_fingerprint=first.request_fingerprint,
            # §16: a LATER fetch — the accepted I06 §40 law refuses to
            # order two different byte-states observed at the same instant,
            # and the handoff never invents observation times.
            retrieved_at=first.retrieved_at + timedelta(minutes=1),
        )
        r2 = stack.handoff.persist_batch(
            job_id="job-1", batch=second, context=make_context()
        )
        assert r1.blob_shas != r2.blob_shas
        for sha in (*r1.blob_shas, *r2.blob_shas):
            assert stack.store.blob_exists(
                sha, StorageEncoding.NONE
            )
        assert r2.manifest_version == r1.manifest_version + 1
        manifest = stack.manifest_repo.get_manifest(r2.manifest_id)
        assert manifest.supersedes_manifest_id == r1.manifest_id


# -------------------------------------------------------------------------
# Concurrency (§55/§56)
# -------------------------------------------------------------------------


class TestConcurrency:
    def test_same_job_persisted_twice_single_checkpoint(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch(
            [b'{"race": 1}'],
            next_resume_token=ResumeToken(
                mode=PaginationMode.PAGE, page_number=5
            ),
        )
        register_job(stack, "job-1", batch)
        first = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        outcome = stack.handoff.persist_batch(
            job_id="job-1", batch=batch, context=make_context()
        )
        checkpoint_transitions = [
            t
            for t in stack.jobs_repo.list_transitions("job-1")
            if t.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
        ]
        assert len(checkpoint_transitions) == 1
        assert outcome.checkpoint_advanced is False
        assert stack.manifest_repo.get_manifest(first.manifest_id)

    def test_same_blob_two_jobs_distinct_checkpoints(
        self, tmp_path
    ) -> None:
        stack = HandoffStack(tmp_path / "s")
        body = b'{"shared": true}'
        batch_a = make_batch([body], request_fingerprint="fp-job-a")
        batch_b = make_batch([body], request_fingerprint="fp-job-b")
        register_job(stack, "job-a", batch_a)
        register_job(stack, "job-b", batch_b)
        ra = stack.handoff.persist_batch(
            job_id="job-a", batch=batch_a, context=make_context()
        )
        rb = stack.handoff.persist_batch(
            job_id="job-b", batch=batch_b, context=make_context()
        )
        # Content dedupe: same blob SHA (§56).
        assert ra.blob_shas == rb.blob_shas
        # Identity-bound acquisitions/checkpoints stay per-job.
        assert ra.acquisition_ids != rb.acquisition_ids
        sa = stack.jobs_repo.get_job("job-a")
        sb = stack.jobs_repo.get_job("job-b")
        assert (
            sa.last_committed_acquisition_id
            != sb.last_committed_acquisition_id
        )


# -------------------------------------------------------------------------
# §66/§67: inversion + anti-bypass proofs
# -------------------------------------------------------------------------


class TestSequenceInversionFails:
    def test_inverted_sequence_cannot_advance_checkpoint(
        self, tmp_path
    ) -> None:
        """§66: the G4-12 proof FAILS if the sequence is inverted — from
        RAW state, with NO manifest, the accepted gate refuses."""
        stack = HandoffStack(tmp_path / "s")
        batch = make_batch([b'{"inverted": 1}'])
        register_job(stack, "job-1", batch)
        stack.jobs_repo.advance_status(
            "job-1", to_status=StorageJobStatus.ACQUIRING
        )
        stack.jobs_repo.advance_status(
            "job-1", to_status=StorageJobStatus.RAW_STAGED
        )
        stack.jobs_repo.advance_status(
            "job-1", to_status=StorageJobStatus.RAW_COMMITTED
        )
        from crypto_sensor_fabric.storage.jobs import JobResumeGateError

        with pytest.raises(JobResumeGateError):
            stack.jobs_repo.advance_checkpoint(
                "job-1",
                resume_token=ResumeToken(
                    mode=PaginationMode.PAGE, page_number=1
                ),
                acquisition_id="never-persisted",
                manifest_id=None,
            )


if __name__ == "__main__":
    raise SystemExit("run with pytest")
