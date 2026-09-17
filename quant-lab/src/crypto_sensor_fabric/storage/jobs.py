"""SENSOR-B4-I07R1 — durable job state + sealed resume coupling.

Hardens the accepted I07 architecture (operator review seams A-H closed;
I07R1 §0).  The broad design is PRESERVED — frozen vocabulary, append-only
birth + transition chain, durable cursor advancement, crash/idempotence
handling, local per-job coordination, restart validation, read-only
evidence.  What changed is the truth contract:

- **Gate-only cursor mutation (I07R1 §3/§4)** — the public
  ``advance_status`` signature carries ONLY ``(job_id, *, to_status,
  reason, evidence_ref, expected_from)``.  Resume-token and
  checkpoint-anchor fields are unreachable by callers, and no
  ``_via_checkpoint_gate``-style flag exists anywhere: ordinary
  transitions can never enter ``CHECKPOINT_ADVANCED`` nor mutate the
  cursor/anchors, and the gated path is a PRIVATE primitive that receives
  an already-proven, fully validated resulting state.

- **Ordinary transitions preserve pointers (I07R1 §5)** — for every
  non-checkpoint transition the resulting state keeps
  ``resume_token``, ``last_committed_acquisition_id``,
  ``last_committed_blob_sha256`` and ``last_manifest_id`` exactly as they
  were.  Durable states are re-validated (never trusted from
  ``model_copy``) before publication (I07R1 §6).

- **Evidence belongs to the job (I07R1 §7-§13)** — checkpoint proof
  resolves the durable acquisition and requires exact job identity
  (provider / sensor_family / request_fingerprint), the authoritative
  I04R2 ``is_usable_manifest_provenance`` predicate (no duplicated
  eligibility logic — a forensic acquisition stays durable history but
  never moves the cursor), physical blob verification, and — at the
  MANIFEST_COMMITTED floor — exact manifest↔acquisition source identity
  (provider, venue, sensor_family, native_instrument,
  source_granularity, blob in refs).  Same bytes under another job or
  source are rejected: content equality does not transfer identity.
  The RAW_COMMITTED floor requires ``manifest_id is None`` (no dummy
  anchors) and stores the exact acquisition/blob; the MANIFEST_COMMITTED
  floor requires the exact proven manifest.  All anchors describe the
  same batch.

- **Checkpoint proof is durable (I07R1 §15-§18)** — every
  ``CHECKPOINT_ADVANCED`` event carries repository-internal immutable
  ``checkpoint_proof`` metadata (closed ``proof_version == 1``: floor,
  acquisition_id, blob_sha256, manifest_id) bound exactly to the
  resulting state's anchors.  Proof on a non-checkpoint event, or a
  checkpoint without proof, is corruption.

- **One transition validator (I07R1 §20-§22)** — the exact V1 transition
  graph (single forward steps, checkpoint-only entry, the single
  retry-resume edge ``FAILED_RETRYABLE -> ACQUIRING``, the annotated
  continuation edge, reason requirements, terminal closure) is ONE pure
  rule function reused by both the write path and restart replay.  The
  reader enforces the same state machine the writer did.

- **Restart replay is the writer's validator (I07R1 §19/§23-§27)** —
  birth identity is immutable across every event; ordinary events
  preserve pointers exactly; event IDs bind ``job_id:sequence``;
  ``resulting.updated_at == transition.transitioned_at``; historical
  checkpoints are re-proved under the floor PERSISTED IN THEIR OWN
  PROOF (constructor configuration governs only NEW checkpoints).

- **Safe coordination (I07R1 §28-§36)** — lock filenames are
  ``sha256(utf8(job_id)).hexdigest() + ".lock"`` (raw logical IDs never
  become filesystem paths), and acquiring the OUTERMOST per-job file
  lock REFRESHES the durable catalogs from disk (validated reload, no
  raw reads) before any state is read, so long-lived repositories never
  act on stale views; cross-repository races cannot fork the chain.

- **One checkpoint-proof authority (I07R1G §3-§9)** — proof EXISTENCE is
  not proof VALIDITY.  The runtime exact-retry path and restart replay
  both validate a persisted checkpoint proof through the SAME authority
  (:func:`validate_checkpoint_proof` + ``_validate_checkpoint_proof``):
  closed V1 schema (wrong type, missing field, unknown version), durability
  floor, proof↔resulting-state anchor binding, and durable re-proof under
  the floor persisted in the proof.  A long-lived repository whose
  post-lock refresh adopts a forged head must reject exactly what a fresh
  restart rejects — typed :class:`JobCatalogCorrupt`, never a raw
  ``KeyError``/``ValueError`` and never a silent adoption.

LOCAL filesystem truth only.  No network, no provider code, no I08
recovery scanner, no quota, no DuckDB/Postgres (later checkpoints).
"""

from __future__ import annotations

import hashlib
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .atomic import ensure_durable_directory
from .catalog import (
    AcquisitionRepository,
    is_usable_manifest_provenance,
)
from .enums import StorageJobStatus
from .json_catalog import (
    CatalogFaultHook,
    DurableJsonCatalog,
    JsonCatalogConflict,
)
from .manifests import PartitionManifestRepository
from .models import StorageJobState, StorageJobTransition

__all__ = [
    "JobError",
    "JobIdentityConflict",
    "JobTransitionConflict",
    "JobUnknown",
    "JobLockHeld",
    "JobResumeGateError",
    "JobCatalogCorrupt",
    "MIN_DURABLE_STATES",
    "CHECKPOINT_PROOF_VERSION",
    "validate_checkpoint_proof",
    "DurableJobStateRepository",
]


# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class JobError(RuntimeError):
    """Base type for the durable job state repository."""


class JobIdentityConflict(JobError):
    """A job_id already exists durably with different identity semantics."""


class JobTransitionConflict(JobError):
    """The requested transition violates the frozen state machine."""


class JobUnknown(JobError):
    """The job_id has no durable birth record."""


class JobLockHeld(JobError):
    """Another writer holds the per-job lock (never auto-deleted; I08)."""


class JobResumeGateError(JobError):
    """§16 gate: durable proof for the batch is missing — cursor NOT advanced."""


class JobCatalogCorrupt(JobError):
    """Persisted job chain violates a cross-constraint on restart."""


# ---------------------------------------------------------------------------
# Frozen transition rules (I07R1 §20-§22): ONE validator, two callers
# ---------------------------------------------------------------------------

#: The frozen linear progress order (03 doc §15).  Failure/quarantine
#: states are side states and are NOT part of this order.
_PROGRESS_ORDER: tuple[StorageJobStatus, ...] = (
    StorageJobStatus.PLANNED,
    StorageJobStatus.ACQUIRING,
    StorageJobStatus.RAW_STAGED,
    StorageJobStatus.RAW_COMMITTED,
    StorageJobStatus.PROJECTION_PENDING,
    StorageJobStatus.PROJECTION_COMMITTED,
    StorageJobStatus.MANIFEST_COMMITTED,
    StorageJobStatus.CHECKPOINT_ADVANCED,
    StorageJobStatus.COMPLETE,
)

_FAILURE_STATES: frozenset[StorageJobStatus] = frozenset(
    {
        StorageJobStatus.FAILED_RETRYABLE,
        StorageJobStatus.FAILED_TERMINAL,
        StorageJobStatus.QUARANTINED,
    }
)

#: Explicitly configurable §16 minimum durable states.  The frozen
#: recommended default is MANIFEST_COMMITTED; RAW_COMMITTED is the weaker
#: explicit floor (blob physically verified, acquisition durable).
MIN_DURABLE_STATES: frozenset[StorageJobStatus] = frozenset(
    {StorageJobStatus.RAW_COMMITTED, StorageJobStatus.MANIFEST_COMMITTED}
)

#: Closed V1 checkpoint-proof schema version (I07R1 §16).
CHECKPOINT_PROOF_VERSION = 1

#: Closed V1 checkpoint-proof field set (I07R1G §5): exactly these five.
CHECKPOINT_PROOF_FIELDS: frozenset[str] = frozenset(
    {
        "proof_version",
        "minimum_durable_status",
        "acquisition_id",
        "blob_sha256",
        "manifest_id",
    }
)


def validate_checkpoint_proof(
    event_id: str, proof: Any
) -> tuple[StorageJobStatus, str, str, str | None]:
    """THE authoritative checkpoint-proof contract (I07R1G §4-§8, pure).

    Returns ``(floor, acquisition_id, blob_sha256, manifest_id)``.  Every
    failure mode of a persisted proof — absent, wrong Python type, not the
    closed V1 field set, unknown version, missing/unknown/non-durability
    floor, empty anchors, RAW floor contradicting a manifest anchor,
    MANIFEST floor without one — is typed :class:`JobCatalogCorrupt`.  No
    Python implementation exception (``KeyError``/``TypeError``/
    ``ValueError``) may escape as the public corruption classification
    (I07R1G §8), and the SAME rules serve runtime retry and restart replay
    so the two can never drift (I07R1G §4/§10/§15).
    """
    label = f"checkpoint {event_id[:12]}..."
    if proof is None:
        # I07R1 §18: a checkpoint without its immutable proof is corruption.
        raise JobCatalogCorrupt(f"{label} carries no checkpoint_proof")
    if not isinstance(proof, dict):
        raise JobCatalogCorrupt(
            f"{label} proof is not a mapping "
            f"({type(proof).__name__})"
        )
    supplied = set(proof)
    if supplied != CHECKPOINT_PROOF_FIELDS:
        raise JobCatalogCorrupt(
            f"{label} proof is not the closed V1 schema: missing "
            f"{sorted(CHECKPOINT_PROOF_FIELDS - supplied)}, unexpected "
            f"{sorted(supplied - CHECKPOINT_PROOF_FIELDS)}"
        )
    version = proof["proof_version"]
    if isinstance(version, bool) or version != CHECKPOINT_PROOF_VERSION:
        # §16: closed V1 — no silent future-version reading.
        raise JobCatalogCorrupt(
            f"{label} carries unknown checkpoint proof_version {version!r}"
        )
    floor_value = proof["minimum_durable_status"]
    if not isinstance(floor_value, str):
        raise JobCatalogCorrupt(
            f"{label} proof carries a non-string minimum_durable_status "
            f"{floor_value!r}"
        )
    try:
        floor = StorageJobStatus(floor_value)
    except ValueError as exc:
        raise JobCatalogCorrupt(
            f"{label} proof carries unknown minimum_durable_status "
            f"{floor_value!r}"
        ) from exc
    if floor not in MIN_DURABLE_STATES:
        raise JobCatalogCorrupt(
            f"{label} proof carries non-durability floor {floor.value}"
        )
    acquisition_id = proof["acquisition_id"]
    blob_sha = proof["blob_sha256"]
    if (
        not isinstance(acquisition_id, str)
        or not acquisition_id
        or not isinstance(blob_sha, str)
        or not blob_sha
    ):
        raise JobCatalogCorrupt(
            f"{label} proof carries invalid acquisition/blob anchors"
        )
    manifest_id = proof["manifest_id"]
    if floor is StorageJobStatus.RAW_COMMITTED and manifest_id is not None:
        raise JobCatalogCorrupt(
            f"{label} was authorized at the RAW floor but persists a "
            "manifest anchor (I07R1 §12)"
        )
    if floor is StorageJobStatus.MANIFEST_COMMITTED and (
        not isinstance(manifest_id, str) or not manifest_id
    ):
        raise JobCatalogCorrupt(
            f"{label} was authorized at the MANIFEST floor but persists no "
            "manifest anchor (I07R1 §13)"
        )
    return floor, acquisition_id, blob_sha, manifest_id


def _progress_rank(status: StorageJobStatus) -> int | None:
    try:
        return _PROGRESS_ORDER.index(status)
    except ValueError:
        return None


def _nonempty(reason: str | None) -> bool:
    return reason is not None and bool(reason.strip())


def validate_transition(
    current: StorageJobStatus,
    target: StorageJobStatus,
    reason: str | None,
    *,
    checkpoint: bool,
) -> None:
    """THE exact V1 transition graph (I07R1 §21) — pure, no repository state.

    ``checkpoint=True`` marks the gated resume edge: only that edge may
    target ``CHECKPOINT_ADVANCED`` (the proof authorizes the cursor jump
    past intermediate operational states).  The write path raises
    :class:`JobTransitionConflict`; restart replay converts failures to
    :class:`JobCatalogCorrupt` so persisted events must pass the SAME
    graph that would have authorized them originally (I07R1 §20).
    """
    if current in (StorageJobStatus.COMPLETE, StorageJobStatus.FAILED_TERMINAL):
        raise JobTransitionConflict(
            f"{current.value} is terminal; no exits from a frozen job chain"
        )
    if current is StorageJobStatus.QUARANTINED:
        # I08 owns recovery; v1 treats quarantine as terminal here.
        raise JobTransitionConflict(
            "QUARANTINED jobs are recovered by I08, not by I07 transitions"
        )
    if checkpoint != (target is StorageJobStatus.CHECKPOINT_ADVANCED):
        if target is StorageJobStatus.CHECKPOINT_ADVANCED:
            raise JobTransitionConflict(
                "CHECKPOINT_ADVANCED is entered only via advance_checkpoint "
                "(durable-proof gate), never via a plain transition"
            )
        raise JobTransitionConflict(
            "the gated checkpoint edge must target CHECKPOINT_ADVANCED"
        )
    if current is target:
        raise JobTransitionConflict("noop transition is not recorded")
    if target in _FAILURE_STATES:
        # Entering any failure state requires an explicit reason
        # (I07R1 §22) — replay enforces the same (§39-29).
        if not _nonempty(reason):
            raise JobTransitionConflict(
                f"entering {target.value} requires a nonempty failure "
                "reason (no silent failure transitions)"
            )
        return
    if current is StorageJobStatus.FAILED_RETRYABLE:
        # The ONLY retry-resume edge: FAILED_RETRYABLE -> ACQUIRING with a
        # nonempty reason.  No direct jumps back into staged/committed
        # states (I07R1 §21).
        if target is StorageJobStatus.ACQUIRING:
            if not _nonempty(reason):
                raise JobTransitionConflict(
                    "retry resume from FAILED_RETRYABLE requires a nonempty "
                    "reason (backward moves are never silent)"
                )
            return
        raise JobTransitionConflict(
            f"FAILED_RETRYABLE may only resume to ACQUIRING, not "
            f"{target.value}"
        )
    current_rank = _progress_rank(current)
    target_rank = _progress_rank(target)
    if current_rank is None or target_rank is None:
        raise JobTransitionConflict(
            f"cannot transition {current.value} -> {target.value}"
        )
    if target_rank - current_rank == 1:
        return
    if target_rank > current_rank:
        if checkpoint and target is StorageJobStatus.CHECKPOINT_ADVANCED:
            # The gated edge IS the proof: durable evidence at or above the
            # floor authorizes the cursor jump past intermediate states.
            return
        raise JobTransitionConflict(
            f"state machine advances one step at a time; "
            f"{current.value} -> {target.value} skips states"
        )
    # Backward move between progress states: only the annotated
    # batch-continuation edge CHECKPOINT_ADVANCED -> ACQUIRING.
    if (
        current is StorageJobStatus.CHECKPOINT_ADVANCED
        and target is StorageJobStatus.ACQUIRING
    ):
        if not _nonempty(reason):
            raise JobTransitionConflict(
                "CHECKPOINT_ADVANCED -> ACQUIRING is a backward move and "
                "requires a nonempty continuation reason"
            )
        return
    raise JobTransitionConflict(
        f"silent backward move {current.value} -> {target.value} is "
        "forbidden (03 doc §15)"
    )


def _clock_now() -> datetime:
    return datetime.now(UTC)


def _validated_state(state: StorageJobState) -> StorageJobState:
    """Round-trip a durable state through FULL pydantic validation (I07R1 §6).

    ``model_copy(update=...)`` results are never persisted unvalidated: the
    JSON dump forces every nested model (ResumeToken), enum, datetime and
    semantic validator to re-run, so a malformed token/blob SHA/state
    fails BEFORE the event becomes durable.
    """
    return StorageJobState.model_validate(state.model_dump(mode="json"))


def _event_semantics(event: dict[str, Any]) -> dict[str, Any]:
    """Canonical event semantics EXCLUDING operational clock fields.

    Two committed events with identical semantics are the same logical
    event (exact retry after a lost publication race adopts the existing
    record); a difference in anything else is a real conflict.  The
    checkpoint proof is semantic (it binds the proof to the anchors), so
    it participates in comparison.
    """

    def scrub(payload: Any) -> Any:
        if isinstance(payload, dict):
            return {
                k: scrub(v)
                for k, v in sorted(payload.items())
                if k not in {"updated_at", "transitioned_at", "registered_at"}
            }
        if isinstance(payload, list):
            return [scrub(v) for v in payload]
        return payload

    return scrub(event)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Repository-internal event record (wraps the frozen transition model)
# ---------------------------------------------------------------------------


def _build_event_record(
    *,
    job_id: str,
    sequence: int,
    transition: StorageJobTransition,
    resulting_state: StorageJobState,
) -> dict[str, Any]:
    return {
        "record_kind": "job_event",
        "job_id": job_id,
        "sequence": sequence,
        "transition_id": transition.transition_id,
        "transition": transition.model_dump(mode="json"),
        "resulting_state": resulting_state.model_dump(mode="json"),
    }


def _event_id(job_id: str, sequence: int) -> str:
    """Canonical event identity: ``{job_id}:{sequence:06d}`` (I07R1 §26)."""
    return f"{job_id}:{sequence:06d}"


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class DurableJobStateRepository:
    """Durable, restart-safe ``StorageJobState`` + sealed resume coupling.

    Append-only chain per job: birth record (status PLANNED) + immutable
    event records.  Current state is materialized from the chain on load
    and validated against cross-constraints (fail closed) using the SAME
    transition graph the write path enforces (I07R1 §20).
    """

    def __init__(
        self,
        root: str | Path,
        *,
        acquisitions: AcquisitionRepository,
        manifests: PartitionManifestRepository,
        blob_metadata_repository: Any,
        clock: Any = None,
        min_durable_status: StorageJobStatus = StorageJobStatus.MANIFEST_COMMITTED,
        lock_timeout_seconds: float = 30.0,
        fault_hooks: CatalogFaultHook | None = None,
    ) -> None:
        if min_durable_status not in MIN_DURABLE_STATES:
            raise JobResumeGateError(
                f"min_durable_status must be one of "
                f"{sorted(s.value for s in MIN_DURABLE_STATES)}, got "
                f"{min_durable_status!r}"
            )
        self._root = Path(root)
        self._jobs_root = self._root / "jobs"
        self._events_root = self._root / "events"
        self._locks_root = self._root / "locks"
        self._acquisitions = acquisitions
        self._manifests = manifests
        self._blob_metadata = blob_metadata_repository
        self._clock = clock or _clock_now
        self._min_durable_status = min_durable_status
        self._lock_timeout_seconds = lock_timeout_seconds
        self._process_lock = threading.Lock()
        self._job_locks: dict[str, threading.RLock] = {}
        # Per-job file-lock ownership for re-entrancy within one thread
        # (advance_checkpoint appends its event under the same job lock;
        # I07R1 §32: nested entries never re-refresh).
        self._lock_owners: dict[str, dict[str, Any]] = {}
        self._births = DurableJsonCatalog(
            self._jobs_root,
            logical_id_field="job_id",
            fault_hooks=fault_hooks,
        )
        self._events = DurableJsonCatalog(
            self._events_root,
            logical_id_field="transition_id",
            fault_hooks=fault_hooks,
        )
        self._validate_cross_constraints()

    # -- reads ---------------------------------------------------------------

    def get_job(self, job_id: str) -> StorageJobState:
        """Materialized current ``StorageJobState`` (frozen model)."""
        birth = self._births.get(job_id)
        if birth is None:
            raise JobUnknown(f"job {job_id!r} has no durable birth record")
        latest = self._latest_event(job_id)
        if latest is None:
            return StorageJobState.model_validate(birth["job_state"])
        return StorageJobState.model_validate(latest["resulting_state"])

    def has_job(self, job_id: str) -> bool:
        return self._births.has(job_id)

    def list_job_ids(self) -> list[str]:
        return self._births.list_ids()

    def list_transitions(self, job_id: str) -> list[StorageJobTransition]:
        """Frozen ``StorageJobTransition`` records in chain order."""
        if not self._births.has(job_id):
            raise JobUnknown(f"job {job_id!r} has no durable birth record")
        events = self._job_events(job_id)
        return [
            StorageJobTransition.model_validate(event["transition"])
            for event in events
        ]

    # -- job lifecycle -------------------------------------------------------

    def create_job(
        self,
        *,
        job_id: str,
        provider_id: str,
        sensor_family: Any,
        request_fingerprint: str,
    ) -> StorageJobState:
        """Durably register a job in state PLANNED (idempotent on identity)."""
        with self._job_lock(job_id):
            existing = self._births.get(job_id)
            if existing is not None:
                prior = StorageJobState.model_validate(existing["job_state"])
                same_identity = (
                    prior.provider_id == provider_id
                    and prior.sensor_family == sensor_family
                    and prior.request_fingerprint == request_fingerprint
                )
                if not same_identity:
                    raise JobIdentityConflict(
                        f"job {job_id!r} already exists with different "
                        "identity semantics"
                    )
                return self.get_job(job_id)
            birth_state = _validated_state(
                StorageJobState(
                    job_id=job_id,
                    provider_id=provider_id,
                    sensor_family=sensor_family,
                    request_fingerprint=request_fingerprint,
                    status=StorageJobStatus.PLANNED,
                    updated_at=self._clock(),
                )
            )
            payload = {
                "record_kind": "job_birth",
                "job_id": job_id,
                "job_state": birth_state.model_dump(mode="json"),
            }
            self._commit_adopting(
                self._births, job_id, payload, conflict_error=JobIdentityConflict
            )
            return birth_state

    def advance_status(
        self,
        job_id: str,
        *,
        to_status: StorageJobStatus,
        reason: str | None = None,
        evidence_ref: Any = None,
        expected_from: StorageJobStatus | None = None,
    ) -> StorageJobState:
        """Append one explicit ORDINARY transition and return the new state.

        The public signature is exactly ``(job_id, *, to_status, reason,
        evidence_ref, expected_from)`` (I07R1 §3): no resume token, no
        checkpoint anchors, no gate flag.  ``CHECKPOINT_ADVANCED`` is
        unreachable here (§4) and every ordinary transition PRESERVES the
        cursor/anchor pointers exactly (§5).  Forward progression is
        single-step; failure entries and the two annotated backward edges
        require a nonempty ``reason``.
        """
        with self._job_lock(job_id):
            current = self.get_job(job_id)
            if expected_from is not None and current.status is not expected_from:
                raise JobTransitionConflict(
                    f"job {job_id!r} is {current.status.value}, caller "
                    f"expected {expected_from.value}"
                )
            validate_transition(
                current.status, to_status, reason, checkpoint=False
            )
            transition = StorageJobTransition(
                transition_id=_event_id(
                    job_id, self._next_sequence(job_id)
                ),
                job_id=job_id,
                from_status=current.status,
                to_status=to_status,
                transitioned_at=self._clock(),
                reason=reason,
                evidence_ref=evidence_ref,
            )
            # §5/§6: pointers preserved EXACTLY, state fully re-validated
            # (never a bare model_copy) before durability.
            next_state = _validated_state(
                current.model_copy(
                    update={
                        "status": to_status,
                        "updated_at": transition.transitioned_at,
                    }
                )
            )
            self._append_event(transition, next_state)
            return next_state

    # -- §16 sealed resume coupling (I07R1 §4: private, gate-only) -----------

    def advance_checkpoint(
        self,
        job_id: str,
        *,
        resume_token: Any,
        acquisition_id: str,
        manifest_id: str | None = None,
    ) -> StorageJobState:
        """Persist        ``resume_token`` as the active resume point (§16).

        The ONLY way a chain reaches ``CHECKPOINT_ADVANCED``.  Allowed
        only when the batch's T0 evidence is durably proven at or above
        the configured floor AND belongs to THIS exact job (I07R1 §7-§13):
        acquisition identity-bound, authoritative-usable provenance,
        physically verified blob, and — at the MANIFEST_COMMITTED floor —
        an exactly source-bound manifest.  At the RAW_COMMITTED floor the
        caller must pass ``manifest_id=None``; at MANIFEST_COMMITTED the
        manifest_id is mandatory.  Failure NEVER advances the cursor.

        Floor authority splits by checkpoint age (I07R1F §3-§7): the
        CONSTRUCTOR floor shapes only a NEW checkpoint's caller input and
        proof; an ALREADY-committed checkpoint is retried and re-proved
        under the floor persisted in its own proof, so a restart with a
        different ``min_durable_status`` can neither reinterpret nor
        refuse durable history.
        """
        with self._job_lock(job_id):
            current = self.get_job(job_id)
            if current.status is StorageJobStatus.CHECKPOINT_ADVANCED:
                # I07R1F §3-§4: detect an existing checkpoint FIRST.  The
                # current-floor shape rules below must never run against
                # an old retry — durable history outranks restarted config.
                return self._retry_committed_checkpoint(
                    job_id=job_id,
                    resume_token=resume_token,
                    acquisition_id=acquisition_id,
                    manifest_id=manifest_id,
                )
            if current.status is StorageJobStatus.COMPLETE:
                raise JobTransitionConflict(
                    "COMPLETE is terminal; the job chain is frozen"
                )
            # NEW checkpoint: the CURRENT constructor floor governs (§7).
            floor = self._min_durable_status
            self._require_checkpoint_shape(floor, manifest_id)
            self._require_checkpoint_eligible(current.status, floor)
            blob_sha = self._prove_batch_durable(
                job_id=job_id,
                acquisition_id=acquisition_id,
                manifest_id=manifest_id,
                floor=floor,
            )
            return self._append_checkpoint_event(
                job_id=job_id,
                current=current,
                resume_token=resume_token,
                acquisition_id=acquisition_id,
                blob_sha=blob_sha,
                manifest_id=manifest_id,
                floor=floor,
            )

    def _append_checkpoint_event(
        self,
        *,
        job_id: str,
        current: StorageJobState,
        resume_token: Any,
        acquisition_id: str,
        blob_sha: str,
        manifest_id: str | None,
        floor: StorageJobStatus,
    ) -> StorageJobState:
        """PRIVATE gated primitive (I07R1 §4): append a proven checkpoint.

        Receives an already-proven batch and constructs the resulting
        state EXPLICITLY (no caller-settable flag exists), fully
        validated, with the immutable checkpoint proof attached to the
        event record (I07R1 §15/§17).
        """
        transitioned_at = self._clock()
        transition = StorageJobTransition(
            transition_id=_event_id(job_id, self._next_sequence(job_id)),
            job_id=job_id,
            from_status=current.status,
            to_status=StorageJobStatus.CHECKPOINT_ADVANCED,
            transitioned_at=transitioned_at,
            reason=(
                f"resume advanced after durable proof: acquisition "
                f"{acquisition_id}"
                + (
                    f", manifest {manifest_id}"
                    if manifest_id is not None
                    else " (raw floor: no manifest required)"
                )
            ),
        )
        try:
            next_state = _validated_state(
                StorageJobState(
                    job_id=job_id,
                    provider_id=current.provider_id,
                    sensor_family=current.sensor_family,
                    request_fingerprint=current.request_fingerprint,
                    resume_token=resume_token,
                    last_committed_acquisition_id=acquisition_id,
                    last_committed_blob_sha256=blob_sha,
                    last_manifest_id=manifest_id,
                    status=StorageJobStatus.CHECKPOINT_ADVANCED,
                    updated_at=transitioned_at,
                )
            )
        except ValidationError as exc:
            # §6: a malformed resume token / invalid state fails BEFORE the
            # event becomes durable.
            raise JobResumeGateError(
                f"checkpoint produced an invalid job state: {exc}"
            ) from exc
        event = _build_event_record(
            job_id=job_id,
            sequence=int(transition.transition_id.rsplit(":", 1)[-1]),
            transition=transition,
            resulting_state=next_state,
        )
        event["checkpoint_proof"] = {
            "proof_version": CHECKPOINT_PROOF_VERSION,
            "minimum_durable_status": floor.value,
            "acquisition_id": acquisition_id,
            "blob_sha256": blob_sha,
            "manifest_id": manifest_id,
        }
        self._commit_adopting(
            self._events,
            transition.transition_id,
            event,
            conflict_error=JobTransitionConflict,
        )
        return next_state

    # -- durability floor + proof (I07R1 §7-§13, §19, §25) --------------------

    def _require_checkpoint_shape(
        self, floor: StorageJobStatus, manifest_id: str | None
    ) -> None:
        """Reject a NEW-checkpoint caller shape that contradicts the floor.

        §12: at RAW_COMMITTED there IS no manifest anchor, so a supplied
        ``manifest_id`` is contradictory input (never a dummy string).
        §13: MANIFEST_COMMITTED requires the exact durable manifest.  This
        applies to NEW checkpoints ONLY — a historical retry is governed by
        its persisted proof, not by this process's configuration
        (I07R1F §3).
        """
        if floor is StorageJobStatus.RAW_COMMITTED and manifest_id is not None:
            raise JobResumeGateError(
                "min_durable_status is RAW_COMMITTED: checkpoint takes "
                "manifest_id=None (no manifest anchor exists at this floor)"
            )
        if floor is StorageJobStatus.MANIFEST_COMMITTED and manifest_id is None:
            raise JobResumeGateError(
                "min_durable_status is MANIFEST_COMMITTED: checkpoint "
                "requires the exact durable manifest_id"
            )

    def _retry_committed_checkpoint(
        self,
        *,
        job_id: str,
        resume_token: Any,
        acquisition_id: str,
        manifest_id: str | None,
    ) -> StorageJobState:
        """Adopt an EXACT retry of an already-committed checkpoint (I07R1F §3).

        Validation and re-proof use the durability floor PERSISTED IN THAT
        CHECKPOINT'S OWN PROOF (I07R1 §19): a process restarted with a
        different ``min_durable_status`` must never reinterpret — nor
        refuse to re-confirm — durable history.  Only an exact batch match
        (same resume token, acquisition anchor and manifest anchor) is
        adopted; divergent semantics stay a typed conflict (I07R1 §8/§35).
        """
        last = self._latest_event(job_id)
        if last is None:
            # Cannot happen for a CHECKPOINT_ADVANCED head, but prove it.
            raise JobCatalogCorrupt(
                f"job {job_id!r} is CHECKPOINT_ADVANCED with no durable "
                "event record"
            )
        try:
            committed = StorageJobState.model_validate(
                last.get("resulting_state")
            )
        except Exception as exc:
            raise JobCatalogCorrupt(
                f"job {job_id!r} checkpoint event carries an invalid "
                f"resulting state: {exc}"
            ) from exc
        # I07R1G §3/§4/§9: the SAME proof authority restart replay uses.
        # Proof EXISTENCE is not proof VALIDITY — schema, closed version,
        # persisted floor, proof↔result anchors and the durable re-proof are
        # all re-validated BEFORE any retry can be adopted (never a raw
        # KeyError/ValueError, never a silently adopted forged head).
        self._validate_checkpoint_proof(
            event_id=str(last.get("transition_id", job_id)),
            job_id=job_id,
            proof=last.get("checkpoint_proof"),
            resulting=committed,
        )
        # §9 step 4 / §14: a valid proof plus a DIVERGENT caller request is a
        # typed transition conflict — a valid record is not a corrupt one.
        same_batch = (
            committed.last_committed_acquisition_id == acquisition_id
            and committed.last_manifest_id == manifest_id
            and committed.resume_token == resume_token
        )
        if not same_batch:
            raise JobTransitionConflict(
                "job is already CHECKPOINT_ADVANCED for a different batch; "
                "the next batch continues via an annotated ACQUIRING "
                "transition, not another checkpoint advancement"
            )
        return committed

    def _require_checkpoint_eligible(
        self, status: StorageJobStatus, floor: StorageJobStatus
    ) -> None:
        current_rank = _progress_rank(status)
        floor_rank = _progress_rank(floor)
        if (
            current_rank is not None
            and floor_rank is not None
            and current_rank >= floor_rank
        ):
            return
        raise JobResumeGateError(
            f"resume advancement requires batch evidence at {floor.value}; "
            f"job status is {status.value} (§16: the cursor never advances "
            "past unindexed evidence)"
        )

    def _prove_batch_durable(
        self,
        *,
        job_id: str,
        acquisition_id: str,
        manifest_id: str | None,
        floor: StorageJobStatus,
    ) -> str:
        """Resolve §16 proof from durable truth (never caller claims).

        Returns the exact proven ``blob_sha256``.  Enforces, in order:
        durable acquisition resolution; job↔acquisition identity (§7);
        the authoritative I04R2 usable-provenance predicate (§8); physical
        blob verification; and at the MANIFEST_COMMITTED floor the exact
        manifest↔acquisition source identity (§10).  The SAME routine
        re-proves historical checkpoints at restart under the floor
        persisted in each proof (I07R1 §19/§25).
        """
        try:
            acquisition = self._acquisitions.get_acquisition(acquisition_id)
        except Exception as exc:  # noqa: BLE001 — fail closed on any probe error
            raise JobResumeGateError(
                f"batch acquisition {acquisition_id!r} is not durable: {exc}"
            ) from exc
        job_birth = self._births.get(job_id)
        if job_birth is None:
            raise JobResumeGateError(
                f"job {job_id!r} has no durable birth record"
            )
        birth = StorageJobState.model_validate(job_birth["job_state"])
        if (
            acquisition.provider_id != birth.provider_id
            or acquisition.sensor_family != birth.sensor_family
            or acquisition.request_fingerprint != birth.request_fingerprint
        ):
            # §7: evidence must belong to THIS exact job/request.  Same
            # bytes from another job never transfer identity (§11).
            raise JobResumeGateError(
                f"acquisition {acquisition_id!r} does not belong to job "
                f"{job_id!r} (identity mismatch: provider "
                f"{acquisition.provider_id!r} vs {birth.provider_id!r}, "
                f"sensor {acquisition.sensor_family} vs "
                f"{birth.sensor_family}, request_fingerprint "
                f"{acquisition.request_fingerprint!r} vs "
                f"{birth.request_fingerprint!r})"
            )
        if not is_usable_manifest_provenance(acquisition):
            # §8: the ONE authoritative I04R2 rule.  A forensic failed
            # acquisition stays durable T0A history but may NOT move the
            # active cursor.
            raise JobResumeGateError(
                f"acquisition {acquisition_id!r} does not carry usable "
                "manifest provenance (I04R2 §5): forensic/failed evidence "
                "never advances the resume cursor"
            )
        blob_sha = acquisition.blob_sha256
        if not blob_sha:
            raise JobResumeGateError(
                f"batch acquisition {acquisition_id!r} carries no blob — "
                "nothing durable to anchor the resume point to"
            )
        try:
            verified = bool(
                self._blob_metadata.has_verified_physical(blob_sha)
            )
        except Exception as exc:  # noqa: BLE001 — fail closed on any probe error
            raise JobResumeGateError(
                f"physical verification for blob {blob_sha} could not be "
                f"proven: {exc}"
            ) from exc
        if not verified:
            raise JobResumeGateError(
                f"blob {blob_sha} is not physically verified — resume "
                "point may not advance past unverified evidence"
            )
        if floor is StorageJobStatus.RAW_COMMITTED:
            # §12: at the raw floor there IS no manifest anchor; the exact
            # acquisition + exact blob are the whole proof.
            return blob_sha
        assert manifest_id is not None  # enforced by advance_checkpoint
        try:
            manifest = self._manifests.get_manifest(manifest_id)
        except Exception as exc:
            raise JobResumeGateError(
                f"batch manifest {manifest_id!r} is not durable: {exc}"
            ) from exc
        if (
            manifest.provider != acquisition.provider_id
            or manifest.venue != acquisition.venue
            or manifest.sensor_family != acquisition.sensor_family
            or manifest.native_instrument != acquisition.native_instrument
            or manifest.source_granularity != acquisition.native_granularity
        ):
            # §10: a manifest reference is not proof until it is bound to
            # the acquisition it claims to index.
            raise JobResumeGateError(
                f"manifest {manifest_id} does not describe the batch "
                f"acquisition source (provider {manifest.provider!r} vs "
                f"{acquisition.provider_id!r}, venue {manifest.venue!r} vs "
                f"{acquisition.venue!r}, sensor "
                f"{manifest.sensor_family} vs {acquisition.sensor_family}, "
                f"instrument {manifest.native_instrument!r} vs "
                f"{acquisition.native_instrument!r}, granularity "
                f"{manifest.source_granularity} vs "
                f"{acquisition.native_granularity})"
            )
        if blob_sha not in manifest.blob_refs:
            raise JobResumeGateError(
                f"manifest {manifest_id} does not contain batch blob "
                f"{blob_sha} — the batch is not manifest-committed"
            )
        return blob_sha

    # -- chain plumbing --------------------------------------------------------

    def _job_events(self, job_id: str) -> list[dict[str, Any]]:
        events = []
        for event_id in self._events.list_ids():
            payload = self._events.get(event_id)
            assert payload is not None
            if payload.get("job_id") == job_id:
                events.append(payload)
        events.sort(key=lambda e: e["sequence"])
        return events

    def _latest_event(self, job_id: str) -> dict[str, Any] | None:
        events = self._job_events(job_id)
        return events[-1] if events else None

    def _next_sequence(self, job_id: str) -> int:
        latest = self._latest_event(job_id)
        return (latest["sequence"] + 1) if latest else 1

    def _append_event(
        self, transition: StorageJobTransition, resulting: StorageJobState
    ) -> None:
        payload = _build_event_record(
            job_id=transition.job_id,
            sequence=int(transition.transition_id.rsplit(":", 1)[-1]),
            transition=transition,
            resulting_state=resulting,
        )
        self._commit_adopting(
            self._events,
            transition.transition_id,
            payload,
            conflict_error=JobTransitionConflict,
        )

    def _commit_adopting(
        self,
        catalog: DurableJsonCatalog,
        logical_id: str,
        payload: dict[str, Any],
        *,
        conflict_error: type[JobError],
    ) -> dict[str, Any]:
        """Commit with exact-retry adoption (I06 §37 doctrine).

        A lost publication race (crash after publish, before return) can
        leave the record committed while the caller saw failure.  An exact
        retry re-derives the same logical id; if the committed payload
        matches on all semantics except operational clocks, adopt it.
        Any other divergence raises ``conflict_error`` (typed) — divergence
        is visible, never silently adopted.  Disk truth is read ONLY
        through the catalog's validated refresh/get path (I07R1 §36) —
        never a raw JSON read that bypasses integrity parsing.
        """
        try:
            return catalog.commit(logical_id, payload)
        except JsonCatalogConflict as exc:
            existing = catalog.get(logical_id)
            if existing is not None:
                if _event_semantics(existing) == _event_semantics(payload):
                    return existing
                raise conflict_error(
                    f"durable record {logical_id!r} diverges from the retry "
                    "payload (semantic conflict, no adoption)"
                ) from exc
            # The winner may exist only on disk (committed by a lost-race
            # writer this process never cached): validated refresh first.
            catalog.refresh()
            existing = catalog.get(logical_id)
            if existing is not None and _event_semantics(
                existing
            ) == _event_semantics(payload):
                return existing
            raise conflict_error(
                f"durable record {logical_id!r} diverges from the retry "
                "payload (semantic conflict, no adoption)"
            ) from exc

    # -- coordination (I06 §43/§44 pattern + I07R1 §28-§32) --------------------

    def _lock_path(self, job_id: str) -> Path:
        """Safe physical lock key (I07R1 §28): sha256(utf8(job_id)).lock.

        Raw logical IDs NEVER become filesystem paths — traversal,
        drive letters, separators, Unicode or unbounded-length IDs cannot
        escape the locks root, and distinct IDs map to distinct full
        digests (§29).
        """
        key = hashlib.sha256(job_id.encode("utf-8")).hexdigest()
        return self._locks_root / f"{key}.lock"

    def _job_lock(self, job_id: str) -> Any:
        outer = self._job_locks.setdefault(job_id, threading.RLock())
        return _NestedFileLock(outer, self, job_id)

    def _acquire_file_lock(self, job_id: str) -> Any:
        if not self._locks_root.exists():
            ensure_durable_directory(self._locks_root)
        lock_path = self._lock_path(job_id)
        deadline = time.monotonic() + self._lock_timeout_seconds
        while True:
            try:
                handle = open(lock_path, "x")
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise JobLockHeld(
                        f"job lock held for {job_id!r}; stale locks are "
                        "recovery evidence, never auto-deleted (I08)"
                    ) from None
                time.sleep(0.01)
                continue
            handle.write("held\n")
            handle.flush()
            return handle

    def _release_file_lock(self, handle: Any, job_id: str) -> None:
        try:
            handle.close()
            self._lock_path(job_id).unlink(missing_ok=True)
        except OSError:
            # A crash mid-release leaves recovery evidence for I08.
            pass

    def _refresh_durable_truth(self) -> None:
        """Validated post-lock reload of durable births + events (§30-§31).

        Called on OUTERMOST per-job file-lock acquisition only (§32): the
        cache-backed catalogs re-scan committed fragments through the
        existing corruption validator, adopt newly committed objects, and
        fail closed on any divergence or vanished record — so state
        reads, sequence selection, CAS checks and retry classification
        always see current durable truth, never a stale view.
        """
        self._births.refresh()
        self._events.refresh()

    # -- restart validation (I07R1 §19-§27) --------------------------------------

    def _validate_cross_constraints(self) -> None:
        """Fail closed on any chain that violates the frozen doctrine.

        Replay uses the SAME :func:`validate_transition` graph as the
        write path (I07R1 §20): forward skips, ungated checkpoints,
        missing/divergent proofs, silent backward moves and reason-less
        failure entries are corruption, not merely "unexpected".
        """
        seen_jobs: dict[str, dict[str, Any]] = {}
        for job_id in self._births.list_ids():
            birth = self._births.get(job_id)
            assert birth is not None
            if birth.get("record_kind") != "job_birth":
                raise JobCatalogCorrupt(
                    f"jobs/{job_id[:12]}... is not a job_birth record"
                )
            try:
                state = StorageJobState.model_validate(birth["job_state"])
            except Exception as exc:
                raise JobCatalogCorrupt(
                    f"birth state for job {job_id!r} is invalid: {exc}"
                ) from exc
            if state.job_id != job_id:
                raise JobCatalogCorrupt(
                    f"birth record for {job_id!r} carries job_id="
                    f"{state.job_id!r}"
                )
            if state.status is not StorageJobStatus.PLANNED:
                raise JobCatalogCorrupt(
                    f"birth state for job {job_id!r} must be PLANNED, got "
                    f"{state.status.value}"
                )
            seen_jobs[job_id] = birth
        for event_id in self._events.list_ids():
            payload = self._events.get(event_id)
            assert payload is not None
            event_job_id = payload.get("job_id")
            if (
                not isinstance(event_job_id, str)
                or event_job_id not in seen_jobs
            ):
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... references unknown job "
                    f"{event_job_id!r}"
                )
            job_id = event_job_id
            try:
                transition = StorageJobTransition.model_validate(
                    payload["transition"]
                )
                resulting = StorageJobState.model_validate(
                    payload["resulting_state"]
                )
            except Exception as exc:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... is invalid: {exc}"
                ) from exc
            sequence = payload.get("sequence")
            if not isinstance(sequence, int) or sequence < 1:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... has invalid sequence "
                    f"{sequence!r}"
                )
            # §26: exact canonical event identity — job_id + zero-padded
            # sequence, bound consistently across the top-level logical id
            # (catalog-verified against the filename) and the transition.
            if event_id != _event_id(job_id, sequence):
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... claims non-canonical "
                    f"identity for job {job_id!r} sequence {sequence!r}"
                )
            if transition.transition_id != event_id:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... claims transition_id="
                    f"{transition.transition_id!r}"
                )
            if transition.job_id != job_id:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... carries job_id="
                    f"{transition.job_id!r}"
                )
            if resulting.job_id != job_id:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... resulting state carries "
                    f"job_id={resulting.job_id!r}"
                )
            if resulting.status is not transition.to_status:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... resulting status "
                    f"{resulting.status.value} != transition target "
                    f"{transition.to_status.value}"
                )
            # §23: birth identity is immutable through every event.
            birth_state = StorageJobState.model_validate(
                seen_jobs[job_id]["job_state"]
            )
            if (
                resulting.provider_id != birth_state.provider_id
                or resulting.sensor_family != birth_state.sensor_family
                or resulting.request_fingerprint
                != birth_state.request_fingerprint
            ):
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... mutates the immutable birth "
                    f"identity of job {job_id!r}"
                )
            # §27: the resulting state is written AT the transition instant.
            if resulting.updated_at != transition.transitioned_at:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... resulting updated_at "
                    f"{resulting.updated_at} != transition instant "
                    f"{transition.transitioned_at}"
                )
            proof = payload.get("checkpoint_proof")
            is_checkpoint = (
                transition.to_status is StorageJobStatus.CHECKPOINT_ADVANCED
            )
            if is_checkpoint:
                # I07R1G §4: the ONE proof authority — the very same call
                # the runtime exact-retry path makes, so reader and writer
                # can never disagree about a persisted proof (§18/§25).
                self._validate_checkpoint_proof(
                    event_id=event_id,
                    job_id=job_id,
                    proof=proof,
                    resulting=resulting,
                )
            elif proof is not None:
                # §18: proof metadata belongs only to checkpoint events.
                raise JobCatalogCorrupt(
                    f"non-checkpoint event {event_id[:12]}... carries "
                    "checkpoint_proof"
                )
            # §20: replay enforces the EXACT graph the writer enforces.
            try:
                validate_transition(
                    transition.from_status,
                    transition.to_status,
                    transition.reason,
                    checkpoint=is_checkpoint,
                )
            except JobTransitionConflict as exc:
                raise JobCatalogCorrupt(
                    f"event {event_id[:12]}... violates the frozen "
                    f"transition graph: {exc}"
                ) from exc
        # Per-job chain validation: contiguity, linkage, chronology,
        # ordinary-event pointer immutability.
        for job_id, birth in seen_jobs.items():
            events = self._job_events(job_id)
            birth_state = StorageJobState.model_validate(birth["job_state"])
            previous = birth_state
            expected_sequence = 1
            for event in events:
                if event["sequence"] != expected_sequence:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} chain expects sequence "
                        f"{expected_sequence}, found {event['sequence']!r} "
                        "(contiguity violated)"
                    )
                expected_sequence += 1
                transition = StorageJobTransition.model_validate(
                    event["transition"]
                )
                resulting = StorageJobState.model_validate(
                    event["resulting_state"]
                )
                if transition.from_status is not previous.status:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} chain break at "
                        f"{transition.transition_id}: from_status "
                        f"{transition.from_status.value} != previous "
                        f"{previous.status.value}"
                    )
                if transition.transitioned_at < previous.updated_at:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} transition chronology moves "
                        "backward at " + transition.transition_id
                    )
                if not is_checkpoint_event(event):
                    # §24: ordinary events preserve the cursor/anchors
                    # exactly — a tampered pointer is corruption.
                    for field in (
                        "resume_token",
                        "last_committed_acquisition_id",
                        "last_committed_blob_sha256",
                        "last_manifest_id",
                    ):
                        if getattr(resulting, field) != getattr(previous, field):
                            raise JobCatalogCorrupt(
                                f"ordinary event {event['transition_id']} "
                                f"mutates {field} (I07R1 §24: only "
                                "checkpoint events move the cursor)"
                            )
                previous = resulting

    def _validate_checkpoint_proof(
        self,
        *,
        event_id: str,
        job_id: str,
        proof: Any,
        resulting: StorageJobState,
    ) -> None:
        """THE one checkpoint-proof authority for runtime AND restart (I07R1G §4).

        The pure :func:`validate_checkpoint_proof` owns structure, the closed
        V1 version, the durability floor and the floor↔manifest rule; this
        method adds the proof↔resulting-state anchor binding (I07R1 §17) and
        the durable batch re-proof under the floor PERSISTED IN THE PROOF
        (I07R1 §19/§25) — the repository constructor's current configuration
        governs only NEW checkpoints.

        Called by the exact-retry path (before any adoption) and by restart
        replay, so a long-lived repository that refreshes a forged head
        rejects EXACTLY what a fresh restart rejects (I07R1G §9/§10).
        """
        floor, acquisition_id, blob_sha, manifest_id = (
            validate_checkpoint_proof(event_id, proof)
        )
        # §17: the proof must bind EXACTLY to the resulting state's anchors.
        if (
            acquisition_id != resulting.last_committed_acquisition_id
            or blob_sha != resulting.last_committed_blob_sha256
            or manifest_id != resulting.last_manifest_id
        ):
            raise JobCatalogCorrupt(
                f"checkpoint {event_id[:12]}... proof anchors diverge from "
                "the resulting state anchors"
            )
        # §25: full durable re-proof under the persisted floor.
        try:
            proven_blob = self._prove_batch_durable(
                job_id=job_id,
                acquisition_id=acquisition_id,
                manifest_id=manifest_id,
                floor=floor,
            )
        except JobResumeGateError as exc:
            raise JobCatalogCorrupt(
                f"checkpoint {event_id[:12]}... no longer re-proves against "
                f"durable truth: {exc}"
            ) from exc
        if proven_blob != blob_sha:
            raise JobCatalogCorrupt(
                f"checkpoint {event_id[:12]}... re-proved blob "
                f"{proven_blob} != persisted anchor {blob_sha}"
            )


def is_checkpoint_event(event: dict[str, Any]) -> bool:
    """True when the event's target is CHECKPOINT_ADVANCED (proof-bearing)."""
    to_status = (event.get("transition") or {}).get("to_status")
    return to_status == StorageJobStatus.CHECKPOINT_ADVANCED.value


class _NestedFileLock:
    """Acquires the per-job file lock while holding the in-process lock.

    Re-entrant within one thread: the gated checkpoint path appends its
    event under the already-held job lock, so a nested entry only bumps a
    depth counter instead of deadlocking on its own file.  On OUTERMOST
    acquisition (I07R1 §30-§32) the durable catalogs are refreshed from
    disk BEFORE any state is read, so long-lived repositories and
    cross-process contenders always classify against current truth.
    """

    def __init__(
        self, process_lock: threading.RLock, repo: DurableJobStateRepository,
        job_id: str,
    ) -> None:
        self._process_lock = process_lock
        self._repo = repo
        self._job_id = job_id
        self._handle: Any = None
        self._nested = False

    def __enter__(self) -> "_NestedFileLock":
        self._process_lock.acquire()
        try:
            ident = threading.get_ident()
            state = self._repo._lock_owners.get(self._job_id)
            if state is not None and state["thread"] == ident:
                state["depth"] += 1
                self._nested = True
            else:
                self._handle = self._repo._acquire_file_lock(self._job_id)
                self._repo._lock_owners[self._job_id] = {
                    "thread": ident,
                    "depth": 1,
                }
                self._nested = False
                # I07R1 §30: the lock serializes writers; the REFRESH
                # makes the serialized view truthful.  (§32: outermost
                # entries only — nested entries reuse the fresh view.)
                self._repo._refresh_durable_truth()
        except BaseException:
            self._process_lock.release()
            raise
        return self

    def __exit__(self, *exc_info: Any) -> None:
        try:
            if self._nested:
                state = self._repo._lock_owners.get(self._job_id)
                if state is not None:
                    state["depth"] -= 1
            else:
                self._repo._lock_owners.pop(self._job_id, None)
                if self._handle is not None:
                    self._repo._release_file_lock(self._handle, self._job_id)
        finally:
            self._process_lock.release()
