"""SENSOR-B4-I14 — Bloc 3 → Bloc 4 durable handoff.

Wires production Bloc 3 adapter outputs (``FetchBatch`` /
``RawPayloadEnvelope``) into the accepted Bloc 4 storage writer.  This
module is COMPOSITION ONLY: no new storage semantics, no new query
semantics, no second manifest abstraction, no second resume-token
store.  Every durable write goes through the accepted public
repositories, and the resume cursor moves exclusively through
``DurableJobStateRepository.advance_checkpoint()`` — the accepted I07
gate — configured at the ``MANIFEST_COMMITTED`` floor.

Core invariant (I14 frozen contract / G4-12)::

    RESUME CHECKPOINT MUST NEVER ADVANCE BEFORE DURABLE MANIFEST COMMIT.

Seven blocking crash windows (W1..W7) are supported by construction:
the handoff is a STAGED DURABLE PROTOCOL, not one filesystem
transaction.  Earlier durable artifacts (blob, acquisition, revision,
even a manifest fragment) may survive a crash; correctness comes from
content-addressed dedupe, append-only history, accepted idempotent
completion on every append, the manifest CAS gate, and the checkpoint
proof gate.  Recovery of stale/orphan filesystem state remains owned by
I08.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ..providers.base.enums import Granularity, QualityFlagAcquisition
from ..providers.base.fingerprint import payload_hash
from ..providers.base.models import FetchBatch
from .enums import CoverageState, IntegrityState, StorageEncoding
from .enums import StorageJobStatus
from .jobs import DurableJobStateRepository
from .manifests import PartitionManifestRepository
from .models import AcquisitionRecord, PartitionManifest
from .blob_store import LocalBlobStore
from .catalog import AcquisitionRepository, BlobMetadataRepository
from .revisions import SourceRevisionRegistry


# ---------------------------------------------------------------------------
# Typed errors (integration-local; no upstream contract change)
# ---------------------------------------------------------------------------


class Bloc3HandoffError(RuntimeError):
    """Base class for I14 integration failures."""


class BatchIdentityMismatch(Bloc3HandoffError):
    """Batch identity contradicts the job identity (§6)."""


class EnvelopeIdentityMismatch(Bloc3HandoffError):
    """A raw payload envelope contradicts its batch identity (§7)."""


class EnvelopeContentHashMismatch(Bloc3HandoffError):
    """Recomputed SHA-256 of the raw body != envelope.content_hash (§8)."""


class DuplicateEnvelopeContent(Bloc3HandoffError):
    """Two envelopes in one batch carry identical raw bytes (§9)."""


# ---------------------------------------------------------------------------
# Integration-local input context (§43): a narrow typed carrier for the
# accepted upstream identity fields FetchBatch deliberately does not carry.
# ---------------------------------------------------------------------------


class BatchAlreadyCompleted(Bloc3HandoffError):
    """Retry after COMPLETE with new content intent (§50).

    I14R1 §10: this typed refusal is ALSO the terminal answer when a
    genuinely NEXT batch arrives for a COMPLETE job — COMPLETE is never
    reopened (no COMPLETE -> ACQUIRING edge exists or may be invented).
    """


class DivergentBatchRewrite(Bloc3HandoffError):
    """I14R1 §4/§9: a batch that claims a consumed checkpoint position but
    cannot prove it is the EXACT committed batch (EXACT_RETRY) nor a valid
    NEXT batch (request fetched from the committed resume token).

    Fail closed BEFORE any evidence mutation: no ACQUIRING transition, no
    checkpoint movement, no durable write."""


@dataclass(frozen=True)
class Bloc3StorageContext:
    """Narrow typed I14 input carrying EXISTING upstream identity.

    ``venue`` is a REQUIRED storage-manifest identity field with no
    authoritative source inside ``FetchBatch`` (it lives in the
    probe/contract layer); ``source_granularity`` maps the accepted
    ``Granularity`` enum onto the storage identity.  Both come from
    accepted upstream truth.  NO default exists (§44): a missing
    ``venue`` is a typed construction refusal.

    I14R1 §5/§6: ``request_resume_token`` is the accepted upstream truth
    for pagination continuation — the adapter fetched THIS batch from
    ``FetchRequest.resume_token`` (accepted Bloc 3 request field).  The
    handoff uses it ONLY to classify a CHECKPOINT_ADVANCED job's incoming
    batch (EXACT_RETRY vs NEXT_BATCH vs DIVERGENT_REWRITE): NEXT_BATCH
    requires ``request_resume_token == current.resume_token``.  Nextness
    is NEVER inferred from bytes, timestamps, row counts, manifest
    versions or provider_cursor heuristics.  None (a first page / a
    caller that does not track its request) can never continue a
    consumed checkpoint — a consumed checkpoint's NEXT_BATCH proof must
    come from upstream, not from guessing.
    """

    venue: str
    source_granularity: Granularity | None = None
    endpoint_host: str | None = None
    endpoint_path: str | None = None
    request_family: str | None = None
    request_resume_token: Any = None  # providers.base.models.ResumeToken | None

    def __post_init__(self) -> None:
        if not self.venue or not isinstance(self.venue, str):
            raise Bloc3HandoffError(
                "Bloc3StorageContext.venue is REQUIRED (no hidden default; "
                "I14 §44) — supply the venue from accepted upstream truth"
            )


# ---------------------------------------------------------------------------
# Receipt (§45): a summary of durable facts — never an authority (§46).
# Every field is re-readable from the accepted durable repositories.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BatchPersistenceReceipt:
    job_id: str
    acquisition_ids: tuple[str, ...]
    blob_shas: tuple[str, ...]
    revision_keys: tuple[str, ...]
    projection_ids: tuple[str, ...]
    manifest_id: str | None
    manifest_version: int | None
    checkpoint_advanced: bool
    resume_token: Any  # providers.base.models.ResumeToken | None
    complete: bool


#: Integration-local fault window labels (W1..W7), consumed by the test
#: fault hook.  Structural mapping: W6 also drives the accepted manifest
#: writer's own PointerFaultPoint hooks inside the CAS append.
FAULT_WINDOWS = (
    "W1_BEFORE_RAW_WRITE",
    "W2_AFTER_RAW_WRITE_BEFORE_ACQUISITION",
    "W3_AFTER_ACQUISITION_BEFORE_REVISION",
    "W4_AFTER_REVISION_BEFORE_MANIFEST",
    "W5_BEFORE_MANIFEST_APPEND",
    "W6_DURING_MANIFEST_APPEND",
    "W7_AFTER_MANIFEST_BEFORE_CHECKPOINT",
)


class Bloc3StorageHandoff:
    """One public service composing accepted Bloc 4 repositories.

    Causal sequence (I14 frozen contract §4): validate batch/envelopes →
    persist exact raw bytes as T0A → persist EvidenceBlob metadata →
    persist AcquisitionRecord(s) → register SourceRevision evidence →
    commit durable PartitionManifest → prove manifest durable → ONLY
    THEN ``advance_checkpoint()`` → optional COMPLETE transition.
    """

    def __init__(
        self,
        *,
        jobs: DurableJobStateRepository,
        blob_store: LocalBlobStore,
        blob_metadata: BlobMetadataRepository,
        acquisitions: AcquisitionRepository,
        manifests: PartitionManifestRepository,
        revisions: SourceRevisionRegistry | None = None,
        clock: Any = None,
    ) -> None:
        self._jobs = jobs
        self._store = blob_store
        self._blob_metadata = blob_metadata
        self._acquisitions = acquisitions
        self._manifests = manifests
        self._revisions = revisions
        self._clock = clock or (lambda: datetime.now().astimezone())

    # -- public API -----------------------------------------------------------

    def persist_batch(
        self,
        *,
        job_id: str,
        batch: FetchBatch,
        context: Bloc3StorageContext,
        projection_ids: list[str] | None = None,
    ) -> BatchPersistenceReceipt:
        """Persist one FetchBatch durably; advance the cursor ONLY after
        the PartitionManifest is durably committed (I14 core invariant)."""
        # §6/§7/§8: typed refusal BEFORE any storage mutation.
        self._validate_batch_identity(job_id, batch)
        self._validate_envelopes(batch)

        current = self._jobs.get_job(job_id)

        # I14R1 §4: a job at/after its committed checkpoint classifies the
        # incoming batch — EXACT_RETRY (adopt, no mutation), NEXT_BATCH
        # (continue via the accepted annotated edge, then persist) or
        # DIVERGENT_REWRITE (typed fail-closed refusal, zero mutation).
        if current.status in (
            StorageJobStatus.CHECKPOINT_ADVANCED,
            StorageJobStatus.COMPLETE,
        ):
            return self._classify_committed(job_id, batch, context, current)

        # §10: an explicitly EMPTY_VALID batch fabricates nothing.
        if not batch.raw_payloads:
            return self._persist_empty_valid(job_id, batch, context)

        # Job lifecycle: single-step forward per the frozen I07 graph.
        if current.status is StorageJobStatus.PLANNED:
            self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.ACQUIRING,
                reason="batch handoff begins",
            )

        # W1: before any durable write.
        self._raise_if_fault(job_id, FAULT_WINDOWS[0])

        self._drive_to(job_id, StorageJobStatus.RAW_STAGED)

        # Stage 1-2: T0A bytes + EvidenceBlob metadata.
        pairs = self._persist_raw_blobs(job_id, batch)

        # W2: crash AFTER raw write / BEFORE acquisition durability (§53:
        # the published immutable blob may survive — content-addressed
        # dedupe absorbs it on retry, §30).
        self._raise_if_fault(job_id, FAULT_WINDOWS[1])

        self._drive_to(job_id, StorageJobStatus.RAW_COMMITTED)

        # Stage 3: AcquisitionRecord(s).
        acquisition_ids = self._persist_acquisitions(
            job_id, batch, pairs, context
        )

        # W3: crash AFTER acquisition durability / BEFORE revision
        # registration (§53: blob + acquisition may survive).
        self._raise_if_fault(job_id, FAULT_WINDOWS[2])

        # Stage 4: revision registration through the accepted I06 path.
        revision_keys = self._register_revisions(
            acquisition_ids,
            batch,
            [computed for _sha, _deferred, computed in pairs],
        )

        # W4: crash AFTER revision registration / BEFORE manifest build.
        self._raise_if_fault(job_id, FAULT_WINDOWS[3])

        # W5: crash before manifest build/append.
        self._raise_if_fault(job_id, FAULT_WINDOWS[4])

        self._drive_to(job_id, StorageJobStatus.PROJECTION_PENDING)
        self._drive_to(job_id, StorageJobStatus.PROJECTION_COMMITTED)

        # Stage 5: durable manifest commit.  W6 fires INSIDE the accepted
        # manifest writer via its own PointerFaultPoint hooks, passed by the
        # caller-configured manifest repository — the checkpoint cannot be
        # reached from inside it.
        manifest = self._commit_manifest(
            job_id, batch, context, pairs, projection_ids or []
        )

        # W6: DURING manifest publication (§27): the CAS append has returned
        # (the manifest is durable) but the job-chain proof status is not yet
        # recorded.  §53: depending on the injected phase inside the accepted
        # writer's own PointerFaultPoint hooks, the survivor may be an orphan
        # fragment OR a committed manifest — retry adopts via the accepted
        # idempotent-completion law (§29/§33), never a duplicate version.
        self._raise_if_fault(job_id, FAULT_WINDOWS[5])

        self._drive_to(job_id, StorageJobStatus.MANIFEST_COMMITTED)

        # W7: manifest durable, checkpoint still old — the critical window.
        self._raise_if_fault(job_id, FAULT_WINDOWS[6])

        # Stage 6: THE gate.  advance_checkpoint re-proves durable truth
        # (exact acquisition + physically verified blob + manifest↔acquisition
        # source identity) from the repositories themselves.
        next_token = batch.next_resume_token  # §22: adapter-owned semantics
        self._jobs.advance_checkpoint(
            job_id,
            resume_token=next_token,
            acquisition_id=acquisition_ids[0],
            manifest_id=manifest.partition_manifest_id,
        )

        # Stage 7: completion (§23/§50) — the checkpoint gate is NOT skipped.
        complete = bool(batch.is_complete) and next_token is None
        if complete:
            # §23/§50: the checkpoint gate itself is NEVER skipped;
            # CHECKPOINT_ADVANCED -> COMPLETE is the accepted terminal step
            # of the frozen I07 graph (_drive_to only walks the
            # pre-checkpoint progress ladder).
            self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.COMPLETE,
                reason="batch complete; no next resume token (§23)",
            )

        return BatchPersistenceReceipt(
            job_id=job_id,
            acquisition_ids=tuple(acquisition_ids),
            blob_shas=tuple(sha for sha, _deferred, _computed in pairs),
            revision_keys=tuple(revision_keys),
            projection_ids=tuple(projection_ids or []),
            manifest_id=manifest.partition_manifest_id,
            manifest_version=manifest.manifest_version,
            checkpoint_advanced=True,
            resume_token=next_token,
            complete=complete,
        )

    # -- validation (§6/§7/§8) -------------------------------------------------

    def _validate_batch_identity(
        self, job_id: str, batch: FetchBatch
    ) -> None:
        birth = self._jobs.get_job(job_id)
        mismatches: list[str] = []
        if birth.provider_id != batch.provider_id:
            mismatches.append(
                f"provider {batch.provider_id!r} != job {birth.provider_id!r}"
            )
        if birth.sensor_family != batch.sensor_family:
            mismatches.append(
                f"sensor {batch.sensor_family!r} != job {birth.sensor_family!r}"
            )
        if birth.request_fingerprint != batch.request_fingerprint:
            mismatches.append(
                f"request_fingerprint {batch.request_fingerprint!r} != job "
                f"{birth.request_fingerprint!r}"
            )
        if mismatches:
            raise BatchIdentityMismatch(
                f"batch identity does not match job {job_id!r}: "
                + "; ".join(mismatches)
            )

    @staticmethod
    def _validate_envelopes(batch: FetchBatch) -> None:
        for index, envelope in enumerate(batch.raw_payloads):
            mismatches: list[str] = []
            if envelope.provider_id != batch.provider_id:
                mismatches.append(
                    f"provider {envelope.provider_id!r} != batch "
                    f"{batch.provider_id!r}"
                )
            if envelope.sensor_family != batch.sensor_family:
                mismatches.append(
                    f"sensor {envelope.sensor_family!r} != batch "
                    f"{batch.sensor_family!r}"
                )
            if envelope.request_fingerprint != batch.request_fingerprint:
                mismatches.append(
                    f"request_fingerprint {envelope.request_fingerprint!r} != "
                    f"batch {batch.request_fingerprint!r}"
                )
            if mismatches:
                raise EnvelopeIdentityMismatch(
                    f"envelope[{index}] rides a foreign identity inside "
                    f"batch {batch.request_fingerprint!r}: "
                    + "; ".join(mismatches)
                )
            # §8: never trust provider-side hashes blindly — recompute over
            # the exact body (UTF-8 for str, per Bloc 3 payload_hash law).
            body = envelope.raw_body
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            computed = payload_hash(data)
            if computed != envelope.content_hash:
                raise EnvelopeContentHashMismatch(
                    f"envelope[{index}] content_hash "
                    f"{envelope.content_hash!r} != recomputed {computed!r}"
                )

    # -- stage: T0A raw bytes + EvidenceBlob metadata (§9/§10/§11/§30) ---------

    def _persist_raw_blobs(
        self, job_id: str, batch: FetchBatch
    ) -> list[tuple[str, str | None, str]]:
        """Persist exact raw bytes; return [(sha, acquisition_id|None), ...].

        No JSON reparse, no newline/whitespace/Unicode normalization, no
        sorted-key serialization (§11): T0A is received source evidence.
        The acquisition id is deferred (None): I14R1C derives it from the
        batch's observation instant + content position so identical bytes
        re-observed at a LATER instant never collide (the pure ``fp::sha``
        scheme did), while an exact-batch retry keeps a stable id.
        """
        staged: list[tuple[str, str | None, str]] = []
        seen_shas: set[str] = set()
        for envelope in batch.raw_payloads:
            body = envelope.raw_body
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            computed_sha = hashlib.sha256(data).hexdigest()
            if computed_sha in seen_shas:
                raise DuplicateEnvelopeContent(
                    f"batch {batch.request_fingerprint!r} carries duplicate "
                    f"raw content (sha {computed_sha[:12]}...); each "
                    "envelope must carry distinct evidence"
                )
            seen_shas.add(computed_sha)
            put = self._store.put_bytes(
                data,
                storage_encoding=StorageEncoding.NONE,
                source_media_type=(
                    envelope.content_type or "application/octet-stream"
                ),
                job_id=job_id,
            )
            sha = put.blob.blob_sha256
            if sha != computed_sha:
                raise Bloc3HandoffError(
                    f"blob store returned sha {sha!r} for content hashed "
                    f"{computed_sha!r} — content addressing violated"
                )
            self._blob_metadata.append_metadata(put.blob)
            staged.append((sha, None, computed_sha))
        return staged

    # -- stage: acquisition records (§12/§13/§31/§39) --------------------------

    def _persist_acquisitions(
        self,
        job_id: str,
        batch: FetchBatch,
        pairs: list[tuple[str, str | None, str]],
        context: Bloc3StorageContext,
    ) -> list[str]:
        """One AcquisitionRecord per nonempty raw envelope.

        Mapping (written mapping table = INPUT_MAPPING_MATRIX evidence):
        provider_id→provider_id; sensor_family→sensor_family;
        native_instrument_id→native_instrument; request_fingerprint→
        request_fingerprint; requested_start/end→requested_start/end;
        actual_first/last_timestamp→actual_start/end; retrieved_at→
        request_started_at AND response_observed_at (both observation-time
        semantics, one event); clock→ingested_at; http_status→
        http_status_or_source_status; adapter_version→adapter_version;
        context.venue→venue; context.source_granularity→native_granularity.
        The accepted I04R1 secret firewall re-validates endpoint/request
        fields at append — never bypassed.

        I14R1C acquisition-id law: ``<fp>::<observed_at>::<sha>`` — the
        batch's ONE observation instant (retrieved_at) plus the envelope's
        content position.  Distinct observation instants get distinct
        acquisitions even for identical bytes (a refetch is a real event);
        an EXACT-batch retry derives the SAME ids (idempotent adoption).
        No invented per-envelope times: every envelope of one batch shares
        the single accepted response_observed_at (I06 §40 preserved).
        """
        observed = batch.retrieved_at.astimezone(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        acquisition_ids: list[str] = []
        for blob_sha, _deferred, computed_sha in pairs:
            acquisition_id = (
                f"{batch.request_fingerprint}::{observed}::{computed_sha}"
            )
            record = AcquisitionRecord(
                acquisition_id=acquisition_id,
                provider_id=batch.provider_id,
                venue=context.venue,
                sensor_family=batch.sensor_family,
                request_fingerprint=batch.request_fingerprint,
                adapter_version=batch.adapter_version,
                requested_start=batch.requested_start,
                requested_end=batch.requested_end,
                actual_start=batch.actual_first_timestamp,
                actual_end=batch.actual_last_timestamp,
                native_instrument=batch.native_instrument_id,
                native_granularity=context.source_granularity,
                request_started_at=batch.retrieved_at,
                response_observed_at=batch.retrieved_at,
                ingested_at=self._clock(),
                http_status_or_source_status=(
                    str(batch.http_status)
                    if batch.http_status is not None
                    else (batch.transport_status or "UNKNOWN")
                ),
                endpoint_host=context.endpoint_host,
                endpoint_path=context.endpoint_path,
                request_family=context.request_family,
                source_locator=f"bloc3://{batch.provider_id}/{batch.request_fingerprint}",
                blob_sha256=blob_sha,
                provider_checksum_algorithm=None,
                provider_checksum_value=None,
                provider_checksum_verified=None,
            )
            self._acquisitions.append_acquisition(record)
            acquisition_ids.append(acquisition_id)
        return acquisition_ids

    # -- stage: revision registration (§15/§32; I14R1 §19-§25 group law) --------

    def _group_observation_identity(
        self,
        batch: FetchBatch,
        member_shas: list[str],
    ) -> tuple[str, str]:
        """Deterministic observation identity over the COMPLETE group
        (I14R1 §21/§13).

        ``observation_digest`` = THE I06 domain-separated group content
        digest — ``sha256("sensor-revision-group-v1\\n" + sorted unique
        member blob SHAs)`` — order-INSENSITIVE by construction (Bloc 3
        declares no raw_payload ordering semantic, so the group is a SET;
        duplicates are already forbidden within one FetchBatch) and never
        ambiguous with a literal single blob SHA.  I06 RECOMPUTES this
        digest from durable member blobs and refuses a forged value.

        ``observation_id`` binds the group to its ONE observation instant
        (batch.retrieved_at) — never an invented per-envelope time (I06
        §40 preserved).
        """
        if self._revisions is None:  # pragma: no cover - defensive
            raise Bloc3HandoffError(
                "revision registry unavailable for group identity"
            )
        digest = self._revisions.group_content_digest(member_shas)
        seen = batch.retrieved_at.astimezone(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        return (
            f"grp::{batch.request_fingerprint}::{seen}::{digest[:16]}",
            digest,
        )

    def _register_revisions(
        self,
        acquisition_ids: list[str],
        batch: FetchBatch,
        ordered_shas: list[str],
    ) -> list[str]:
        """Register the batch's source observation through the accepted I06
        public write path (I14R1 §19-§25).

        ONE FetchBatch is ONE observation of the source containing N raw
        evidence bodies.  The observation covers the COMPLETE ordered
        envelope group through ``SourceRevisionRegistry.
        register_acquisition_group`` — I06's OWN additive group authority,
        not a second revision engine here.  A change in ANY component
        (first, middle, last), a component count change, or any content
        difference in the ordered group now becomes revision-visible;
        an identical group re-observation is I06-identical (no new
        revision).

        One observation instant: every envelope shares the batch's single
        accepted ``retrieved_at``; the handoff never manufactures times to
        force an ordering (I06 §40 preserved — same-instant differing
        groups still fail closed inside I06).
        """
        keys: list[str] = []
        if self._revisions is None or not acquisition_ids:
            return keys
        observation_id, observation_digest = self._group_observation_identity(
            batch, ordered_shas
        )
        observation = self._revisions.register_acquisition_group(
            acquisition_ids=acquisition_ids,
            observation_id=observation_id,
            observation_digest=observation_digest,
        )
        keys.append(observation.source_revision_key)
        return keys

    # -- stage: manifest commit (§19/§20/§33) -----------------------------------

    def _commit_manifest(
        self,
        job_id: str,
        batch: FetchBatch,
        context: Bloc3StorageContext,
        pairs: list[tuple[str, str | None, str]],
        projection_ids: list[str],
    ) -> PartitionManifest:
        return self._append_manifest_cas(
            batch,
            context,
            blob_refs=sorted(sha for sha, _deferred, _computed in pairs),
            projection_ids=projection_ids,
            coverage=self._coverage_state_for(batch),
            integrity=IntegrityState.LOCAL_HASH_VERIFIED,
        )

    def _append_manifest_cas(
        self,
        batch: FetchBatch,
        context: Bloc3StorageContext,
        *,
        blob_refs: list[str],
        projection_ids: list[str],
        coverage: CoverageState,
        integrity: IntegrityState,
    ) -> PartitionManifest:
        """Versioned CAS manifest append (§19/§20) with idempotent adoption
        (§29/§33): if the current pointer already references the EXACT
        intended manifest — the W6/W7 retry shape — it is re-read, proven
        durable, and adopted; no duplicate semantic version is ever
        appended by a retry."""
        partition_key = self._partition_key(batch, context)
        identity = self._manifest_identity(batch, context)
        current = self._manifests.read_current_pointer(partition_key)
        if current is not None:
            existing = self._manifests.get_manifest(
                current.partition_manifest_id
            )
            if existing is not None and self._same_intended_manifest(
                existing,
                identity,
                batch,
                context,
                blob_refs,
                projection_ids,
                coverage,
                integrity,
            ):
                return existing
            # §20: versioned CAS — next version supersedes the current.
            manifest = PartitionManifest(
                partition_manifest_id=self._manifest_id(
                    partition_key, current.manifest_version + 1
                ),
                partition_key=partition_key,
                provider=identity["provider"],
                venue=identity["venue"],
                sensor_family=identity["sensor"],
                native_instrument=identity["instrument"],
                source_granularity=context.source_granularity,
                logical_date_start=batch.requested_start,
                logical_date_end=batch.requested_end,
                blob_refs=blob_refs,
                projection_refs=projection_ids,
                coverage_state=coverage,
                integrity_state=integrity,
                created_at=self._clock(),
                manifest_version=current.manifest_version + 1,
                supersedes_manifest_id=current.partition_manifest_id,
            )
            expected: tuple[str, int] | None = (
                current.partition_manifest_id,
                current.manifest_version,
            )
        else:
            manifest = PartitionManifest(
                partition_manifest_id=self._manifest_id(partition_key, 1),
                partition_key=partition_key,
                provider=identity["provider"],
                venue=identity["venue"],
                sensor_family=identity["sensor"],
                native_instrument=identity["instrument"],
                source_granularity=context.source_granularity,
                logical_date_start=batch.requested_start,
                logical_date_end=batch.requested_end,
                blob_refs=blob_refs,
                projection_refs=projection_ids,
                coverage_state=coverage,
                integrity_state=integrity,
                created_at=self._clock(),
            )
            expected = None
        result = self._manifests.append_partition_manifest(manifest, expected)
        return result.manifest

    # -- adoption / empty-valid (§10/§34/§35/§49/§50) ---------------------------

    @staticmethod
    def _envelope_shas(batch: FetchBatch) -> list[str]:
        """Content-addressed shas of the batch's raw bodies (§8/§11 rule)."""
        shas: list[str] = []
        for envelope in batch.raw_payloads:
            body = envelope.raw_body
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            shas.append(hashlib.sha256(data).hexdigest())
        return shas

    def _classify_committed(
        self,
        job_id: str,
        batch: FetchBatch,
        context: Bloc3StorageContext,
        current: Any,
    ) -> BatchPersistenceReceipt:
        """I14R1 §4/§7-§10: classify a batch arriving at/after the committed
        checkpoint — EXACT_RETRY, NEXT_BATCH or DIVERGENT_REWRITE.

        EXACT_RETRY (same batch semantic identity as the committed batch):
        adopt durable state, mutate NOTHING.

        NEXT_BATCH (only at CHECKPOINT_ADVANCED): the incoming request was
        fetched FROM the committed resume token — proven ONLY by the
        accepted upstream field ``context.request_resume_token ==
        current.resume_token`` (§5/§6).  I14 then owns the accepted
        annotated I07 edge CHECKPOINT_ADVANCED -> ACQUIRING (nonempty
        reason) and persists the next batch through the normal pipeline.
        The public caller never drives I07 internals.

        DIVERGENT_REWRITE: anything else that claims the consumed position
        — fail closed typed BEFORE any evidence mutation (no ACQUIRING
        transition, no checkpoint movement, no durable write).

        At COMPLETE the checkpoint position is terminal: an exact final-
        batch retry is adopted read-only; any NEXT batch is a typed
        terminal refusal — COMPLETE is never reopened (§10).
        """
        shas = self._envelope_shas(batch)
        observed = batch.retrieved_at.astimezone(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        if shas:
            first_acq: str | None = (
                f"{batch.request_fingerprint}::{observed}::{shas[0]}"
            )
        else:
            # EMPTY_VALID batch: the durable anchor is the blob-less empty
            # acquisition event minted by _persist_empty_valid (I14R1 §12).
            first_acq = (
                f"{batch.request_fingerprint}::{observed}::EMPTY_VALID"
                if QualityFlagAcquisition.EMPTY_VALID
                in set(batch.quality_flags)
                else None
            )
        expected_first = (first_acq,)
        exact_retry = (
            current.last_committed_acquisition_id == expected_first[0]
            and current.resume_token == batch.next_resume_token
        )
        if exact_retry:
            # §34/§49/§50: adopt frozen facts; mutate nothing.  The receipt
            # anchor is the DURABLE anchor (§46): for an EMPTY_VALID page it
            # is the blob-less empty acquisition id.
            anchor = current.last_committed_acquisition_id
            return BatchPersistenceReceipt(
                job_id=job_id,
                acquisition_ids=(anchor,) if anchor else (),
                blob_shas=tuple(shas),
                revision_keys=(),
                projection_ids=(),
                manifest_id=current.last_manifest_id,
                manifest_version=None,
                checkpoint_advanced=False,
                resume_token=current.resume_token,
                complete=(
                    current.status is StorageJobStatus.COMPLETE
                    or (
                        bool(batch.is_complete)
                        and batch.next_resume_token is None
                    )
                ),
            )
        if current.status is StorageJobStatus.COMPLETE:
            # §10: terminal — any new batch after COMPLETE is refused; no
            # COMPLETE -> ACQUIRING edge exists or may be invented.
            raise BatchAlreadyCompleted(
                f"job {job_id!r} is COMPLETE; the job chain is frozen and "
                "no next batch may reopen it (I14R1 §10)"
            )
        # CHECKPOINT_ADVANCED: NEXT_BATCH requires upstream-provable
        # nextness — the request WAS made with the committed resume token.
        request_token = context.request_resume_token
        if request_token is not None and request_token == current.resume_token:
            self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.ACQUIRING,
                reason=(
                    "NEXT_BATCH continuation: incoming request was fetched "
                    "from the committed resume token (I14R1 §3/§4)"
                ),
            )
            return self.persist_batch(
                job_id=job_id, batch=batch, context=context
            )
        raise DivergentBatchRewrite(
            f"job {job_id!r} is past its committed checkpoint and the "
            "incoming batch proves neither EXACT_RETRY (same batch) nor "
            "NEXT_BATCH (request_resume_token == committed resume token); "
            "divergent rewrite refused before any mutation (I14R1 §4/§9)"
        )

    def _persist_empty_valid(
        self,
        job_id: str,
        batch: FetchBatch,
        context: Bloc3StorageContext,
    ) -> BatchPersistenceReceipt:
        """§10/§12/§17 (I14R1 Blocker B repair): an explicitly EMPTY_VALID
        batch is a REAL acquisition event — durable acquisition truth with
        NO fabricated bytes.

        Durable sequence (§17): durable empty AcquisitionRecord (no T0A
        blob — ``blob_sha256`` stays None; nothing is fabricated) ->
        durable zero-blob EMPTY_CONFIRMED / UNVERIFIED manifest -> THE
        accepted I07 gate ``advance_checkpoint`` — never bypassed.  A
        valid adapter ``next_resume_token`` is PRESERVED (empty partial:
        CHECKPOINT_ADVANCED with the token); an empty complete page
        (token=None) checkpoints and terminates: CHECKPOINT_ADVANCED ->
        COMPLETE.  Receipt and durable state always agree.
        """
        # Idempotence (§34): if this exact empty page already checkpointed,
        # adopt without any mutation (I14R1 §29 empty exact retry).
        current = self._jobs.get_job(job_id)
        if current.status in (
            StorageJobStatus.CHECKPOINT_ADVANCED,
            StorageJobStatus.COMPLETE,
        ):
            return self._classify_committed(job_id, batch, context, current)
        if current.status is StorageJobStatus.PLANNED:
            self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.ACQUIRING,
                reason="EMPTY_VALID handoff begins (no bytes to stage)",
            )
        partition_key = self._partition_key(batch, context)
        del partition_key  # identity flows through _append_manifest_cas
        # §34 idempotent adoption is owned by the versioned CAS append: if
        # the current manifest IS the exact intended empty manifest (W7
        # survivor / empty retry), it is adopted; an empty page arriving
        # after nonempty pages appends the next superseding version (I14R1
        # §29: nonempty -> empty next page stays a real versioned page).
        self._raise_if_fault(job_id, FAULT_WINDOWS[0])
        self._raise_if_fault(job_id, FAULT_WINDOWS[4])
        manifest = self._append_manifest_cas(
            batch,
            context,
            blob_refs=[],
            projection_ids=[],
            coverage=CoverageState.EMPTY_CONFIRMED,
            integrity=IntegrityState.UNVERIFIED,
        )
        self._drive_to(job_id, StorageJobStatus.MANIFEST_COMMITTED)
        # W7 (I14R1 §18): manifest durable / checkpoint old — the same
        # critical window as the raw path; the retry must adopt the exact
        # empty manifest + acquisition and advance exactly once.
        self._raise_if_fault(job_id, FAULT_WINDOWS[6])
        # Durable EMPTY_VALID acquisition truth (§12): one record per empty
        # page event, keyed by the observation instant, blob-less.
        observed = batch.retrieved_at.astimezone(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        acquisition_id = (
            f"{batch.request_fingerprint}::{observed}::EMPTY_VALID"
        )
        record = AcquisitionRecord(
            acquisition_id=acquisition_id,
            provider_id=batch.provider_id,
            venue=context.venue,
            sensor_family=batch.sensor_family,
            request_fingerprint=batch.request_fingerprint,
            adapter_version=batch.adapter_version,
            requested_start=batch.requested_start,
            requested_end=batch.requested_end,
            native_instrument=batch.native_instrument_id,
            native_granularity=context.source_granularity,
            request_started_at=batch.retrieved_at,
            response_observed_at=batch.retrieved_at,
            ingested_at=self._clock(),
            http_status_or_source_status=(
                str(batch.http_status)
                if batch.http_status is not None
                else (batch.transport_status or "UNKNOWN")
            ),
            endpoint_host=context.endpoint_host,
            endpoint_path=context.endpoint_path,
            request_family=context.request_family,
            source_locator=f"bloc3://{batch.provider_id}/{batch.request_fingerprint}",
            blob_sha256=None,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
        )
        self._acquisitions.append_acquisition(record)
        # THE gate — I14R1 §14/§15: the checkpoint proof carries
        # blob_sha256=None under the explicit V2 EMPTY_VALID law.  Never a
        # bypass, never a fabricated blob.
        next_token = batch.next_resume_token  # §22: adapter-owned semantics
        self._jobs.advance_checkpoint(
            job_id,
            resume_token=next_token,
            acquisition_id=acquisition_id,
            manifest_id=manifest.partition_manifest_id,
            evidence_kind="EMPTY_VALID",
        )
        complete = bool(batch.is_complete) and next_token is None
        if complete:
            self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.COMPLETE,
                reason="EMPTY_VALID page complete; no next resume token (§23)",
            )
        return BatchPersistenceReceipt(
            job_id=job_id,
            acquisition_ids=(acquisition_id,),
            blob_shas=(),
            revision_keys=(),
            projection_ids=(),
            manifest_id=manifest.partition_manifest_id,
            manifest_version=manifest.manifest_version,
            checkpoint_advanced=True,
            resume_token=next_token,
            complete=complete,
        )

    # -- laws -------------------------------------------------------------------

    @staticmethod
    def _manifest_identity(
        batch: FetchBatch, context: Bloc3StorageContext
    ) -> dict[str, Any]:
        """Typed manifest identity from the batch + context (no inference).

        ``sensor`` is the accepted SensorFamily enum member itself;
        ``instrument`` and ``venue`` are validated nonempty strings.
        """
        return {
            "provider": batch.provider_id,
            "venue": context.venue,
            "sensor": batch.sensor_family,
            "instrument": batch.native_instrument_id,
        }

    @staticmethod
    def _partition_key(
        batch: FetchBatch, context: Bloc3StorageContext
    ) -> str:
        """Accepted I04 partition identity shape (provider/venue/sensor/
        instrument/date basis) with the batch's requested window date."""
        return (
            f"{batch.provider_id}/{context.venue}/"
            f"{batch.sensor_family.value}/{batch.native_instrument_id}/"
            f"{batch.requested_start.date().isoformat()}"
        )

    @staticmethod
    def _manifest_id(partition_key: str, version: int) -> str:
        return f"{partition_key}::v{version}"

    @staticmethod
    def _same_intended_manifest(
        existing: PartitionManifest,
        identity: dict[str, Any],
        batch: FetchBatch,
        context: Bloc3StorageContext,
        blob_refs: list[str],
        projection_ids: list[str],
        coverage: CoverageState,
        integrity: IntegrityState,
    ) -> bool:
        """True when the durable current manifest IS the exact intended
        manifest of this batch (idempotent adoption shape, §29/§33)."""
        return (
            sorted(existing.blob_refs) == blob_refs
            and list(existing.projection_refs) == list(projection_ids)
            and existing.coverage_state is coverage
            and existing.integrity_state is integrity
            and existing.provider == identity["provider"]
            and existing.venue == identity["venue"]
            and existing.sensor_family == identity["sensor"]
            and existing.native_instrument == identity["instrument"]
            and existing.source_granularity == context.source_granularity
            and existing.logical_date_start == batch.requested_start
            and existing.logical_date_end == batch.requested_end
        )

    @staticmethod
    def _coverage_state_for(batch: FetchBatch) -> CoverageState:
        """Missingness truth per accepted I04 vocabulary (§58) — never zero."""
        flags = set(batch.quality_flags)
        if (
            batch.row_count == 0
            and QualityFlagAcquisition.EMPTY_VALID in flags
        ):
            return CoverageState.EMPTY_CONFIRMED
        if QualityFlagAcquisition.GAP_DETECTED in flags:
            return CoverageState.KNOWN_GAP
        if QualityFlagAcquisition.PARTIAL_INTERVAL in flags:
            return CoverageState.PARTIAL
        return CoverageState.COMPLETE_SOURCE_BOUNDARY

    # -- plumbing ---------------------------------------------------------------

    _STEP_ORDER: tuple[StorageJobStatus, ...] = (
        StorageJobStatus.ACQUIRING,
        StorageJobStatus.RAW_STAGED,
        StorageJobStatus.RAW_COMMITTED,
        StorageJobStatus.PROJECTION_PENDING,
        StorageJobStatus.PROJECTION_COMMITTED,
        StorageJobStatus.MANIFEST_COMMITTED,
    )

    def _drive_to(self, job_id: str, status: StorageJobStatus) -> None:
        """Single-step forward per the frozen I07 graph (no skips).

        Idempotent on retry: a job already AT or PAST the target status
        (e.g. surviving a crash) is left as-is; backward/needle moves are
        refused by the frozen graph, not by this helper.
        """
        from .jobs import JobTransitionConflict

        current = self._jobs.get_job(job_id).status
        order = self._STEP_ORDER
        if current not in order:
            return
        target_index = order.index(status)
        current_index = order.index(current)
        if current_index >= target_index:
            return
        for step in order[current_index + 1 : target_index + 1]:
            try:
                self._jobs.advance_status(job_id, to_status=step)
            except JobTransitionConflict:
                # Another writer moved the chain concurrently; re-read and
                # continue only if we are now at/behind the step (the job
                # lock + frozen graph own the truth — §55).
                if self._jobs.get_job(job_id).status is not step:
                    raise

    def _raise_if_fault(self, job_id: str, window: str) -> None:
        """Integration-local fault injection point (test hook).

        The hook object (if any) is attached to the instance attribute
        ``fault_windows`` by tests: a set of window labels that raise
        ``FaultSimulated`` — simulating a process crash at that window.
        No production path attaches it.
        """
        windows = getattr(self, "fault_windows", None)
        if windows and window in windows:
            raise FaultSimulated(
                f"simulated crash at {window} (job {job_id!r})"
            )


class FaultSimulated(Bloc3HandoffError):
    """Raised by the test fault hook to simulate a process crash."""
