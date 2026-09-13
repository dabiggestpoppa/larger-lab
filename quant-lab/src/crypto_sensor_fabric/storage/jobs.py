"""SENSOR-B4-I07 — durable job state + resume coupling.

Implements the frozen job-durability doctrine of
``bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md``:

- **§15 job durability** — ``StorageJobState`` survives process restart.
  The state machine uses the FROZEN ``storage.enums.StorageJobStatus``
  vocabulary and the FROZEN ``storage.models.StorageJobState`` /
  ``StorageJobTransition`` models (one canonical vocabulary, I06R1 §3-§5
  doctrine).  Persistence is append-only immutable catalogs: a birth
  record per job plus one immutable event record per transition; the
  current state is MATERIALIZED from the chain, never mutated in place.

- **A job may not move backward silently.**  Forward progression along
  the frozen linear order is always allowed.  Entering a failure state
  requires an explicit reason.  Leaving ``FAILED_RETRYABLE`` (or an
  annotated continuation from ``CHECKPOINT_ADVANCED``) is a backward move
  that is legal ONLY when the transition carries a nonempty reason —
  i.e. a new, explicit chain record explaining the repair/continuation.

- **§16 resume invariant** — ``resume_token`` may become the active
  resume point only if the batch's required T0 evidence has reached
  ``MANIFEST_COMMITTED`` (frozen recommended default) or the explicitly
  configured minimum durable state.  The proof is resolved from durable
  truth (acquisition exists, blob physically verified, manifest exists
  and contains the batch blob) — never from caller claims.  A failed
  gate never advances the cursor (fail closed).

- **Crash semantics** — every state change is ONE atomic durable catalog
  commit (staging -> fsync -> verify -> no-clobber publish -> dir fsync).
  A crash leaves either the old chain or the new chain, never an
  intermediate.  An exact retry after a lost publication race adopts the
  already-committed record when semantics (excluding operational clock
  fields) match, and fails typed on any real divergence.

- **Coordination** — per-job local filesystem lock + in-process lock
  (I06 §43 pattern).  Locks are never auto-deleted; I08 owns stale-lock
  recovery.  LOCAL truth only: not distributed coordination.

LOCAL filesystem truth only.  No network, no provider code, no I08
recovery scanner, no quota, no DuckDB/Postgres (later checkpoints).
"""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .atomic import ensure_durable_directory
from .catalog import AcquisitionRepository, CatalogError
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
# Frozen transition rules
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


def _progress_rank(status: StorageJobStatus) -> int | None:
    try:
        return _PROGRESS_ORDER.index(status)
    except ValueError:
        return None


def _clock_now() -> datetime:
    return datetime.now(UTC)


def _event_semantics(event: dict[str, Any]) -> dict[str, Any]:
    """Canonical event semantics EXCLUDING operational clock fields.

    Two committed events with identical semantics are the same logical
    event (exact retry after a lost publication race adopts the existing
    record); a difference in anything else is a real conflict.
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


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class DurableJobStateRepository:
    """Durable, restart-safe ``StorageJobState`` + resume coupling (I07).

    Append-only chain per job: birth record (status PLANNED) + immutable
    event records.  Current state is materialized from the chain on load
    and validated against cross-constraints (fail closed).
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
        self._file_locks: dict[str, Any] = {}
        # Per-job file-lock ownership for re-entrancy within one thread
        # (advance_checkpoint calls advance_status under the same job lock).
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
            birth_state = StorageJobState(
                job_id=job_id,
                provider_id=provider_id,
                sensor_family=sensor_family,
                request_fingerprint=request_fingerprint,
                status=StorageJobStatus.PLANNED,
                updated_at=self._clock(),
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
        resume_token: Any = None,
        last_committed_acquisition_id: str | None = None,
        last_committed_blob_sha256: str | None = None,
        last_manifest_id: str | None = None,
        _via_checkpoint_gate: bool = False,
    ) -> StorageJobState:
        """Append one explicit transition and return the new current state.

        Forward progression is always allowed.  Entering a failure state
        and any backward move (retry resume / annotated continuation)
        require a nonempty ``reason`` — backward moves are never silent.
        ``_via_checkpoint_gate`` is internal: only the durable-proof
        checkpoint path may target CHECKPOINT_ADVANCED.
        """
        with self._job_lock(job_id):
            current = self.get_job(job_id)
            if expected_from is not None and current.status is not expected_from:
                raise JobTransitionConflict(
                    f"job {job_id!r} is {current.status.value}, caller "
                    f"expected {expected_from.value}"
                )
            self._check_transition_allowed(
                current.status, to_status, reason,
                via_gate=_via_checkpoint_gate,
            )
            transition = StorageJobTransition(
                transition_id=self._event_id(job_id, self._next_sequence(job_id)),
                job_id=job_id,
                from_status=current.status,
                to_status=to_status,
                transitioned_at=self._clock(),
                reason=reason,
                evidence_ref=evidence_ref,
            )
            next_state = current.model_copy(
                update={
                    "status": to_status,
                    "updated_at": transition.transitioned_at,
                    "resume_token": (
                        resume_token
                        if resume_token is not None
                        else current.resume_token
                    ),
                    "last_committed_acquisition_id": (
                        last_committed_acquisition_id
                        if last_committed_acquisition_id is not None
                        else current.last_committed_acquisition_id
                    ),
                    "last_committed_blob_sha256": (
                        last_committed_blob_sha256
                        if last_committed_blob_sha256 is not None
                        else current.last_committed_blob_sha256
                    ),
                    "last_manifest_id": (
                        last_manifest_id
                        if last_manifest_id is not None
                        else current.last_manifest_id
                    ),
                }
            )
            self._append_event(transition, next_state)
            return next_state

    # -- §16 resume coupling --------------------------------------------------

    def advance_checkpoint(
        self,
        job_id: str,
        *,
        resume_token: Any,
        acquisition_id: str,
        manifest_id: str,
    ) -> StorageJobState:
        """Persist ``resume_token`` as the active resume point (§16).

        Allowed only when the batch's T0 evidence is durably proven at or
        above the configured minimum state: the acquisition exists, its
        blob is physically verified, and (for the default
        ``MANIFEST_COMMITTED`` floor) the manifest exists durably and
        contains the batch blob.  Failure NEVER advances the cursor.
        """
        with self._job_lock(job_id):
            current = self.get_job(job_id)
            if current.status is StorageJobStatus.CHECKPOINT_ADVANCED:
                # Exact retry of the SAME batch after a lost-return crash is
                # idempotence (§68), not a second advancement: re-prove the
                # durable chain, then return the already-committed state.
                # Divergent semantics are a typed conflict.
                last = self._latest_event(job_id)
                if last is not None:
                    committed = StorageJobState.model_validate(
                        last["resulting_state"]
                    )
                    same_batch = (
                        committed.last_committed_acquisition_id
                        == acquisition_id
                        and committed.last_manifest_id == manifest_id
                        and committed.resume_token == resume_token
                    )
                    if same_batch:
                        # Idempotence is not permission to trust stale
                        # evidence (I05R3 §10 doctrine): re-prove.
                        self._prove_batch_durable(acquisition_id, manifest_id)
                        return committed
                raise JobTransitionConflict(
                    "job is already CHECKPOINT_ADVANCED for a different "
                    "batch; the next batch continues via an annotated "
                    "ACQUIRING transition, not another checkpoint "
                    "advancement"
                )
            if current.status is StorageJobStatus.COMPLETE:
                raise JobTransitionConflict(
                    "COMPLETE is terminal; the job chain is frozen"
                )
            self._require_checkpoint_eligible(current.status)
            self._prove_batch_durable(acquisition_id, manifest_id)
            return self.advance_status(
                job_id,
                to_status=StorageJobStatus.CHECKPOINT_ADVANCED,
                reason=(
                    f"resume advanced after durable proof: acquisition "
                    f"{acquisition_id}, manifest {manifest_id}"
                ),
                resume_token=resume_token,
                last_committed_acquisition_id=acquisition_id,
                last_manifest_id=manifest_id,
                _via_checkpoint_gate=True,
            )

    # -- transition rules (§15) ----------------------------------------------

    def _check_transition_allowed(
        self,
        current: StorageJobStatus,
        target: StorageJobStatus,
        reason: str | None,
        *,
        via_gate: bool = False,
    ) -> None:
        if current in _FAILURE_STATES and target is current:
            # unreachable via frozen noop guard, kept for clarity
            raise JobTransitionConflict("noop transition is not recorded")
        if current in (StorageJobStatus.COMPLETE, StorageJobStatus.FAILED_TERMINAL):
            raise JobTransitionConflict(
                f"{current.value} is terminal; no exits from a frozen "
                "job chain"
            )
        if current is StorageJobStatus.QUARANTINED:
            # I08 owns recovery; v1 treats quarantine as terminal here.
            raise JobTransitionConflict(
                "QUARANTINED jobs are recovered by I08, not by I07 transitions"
            )
        entering_failure = target in _FAILURE_STATES
        if entering_failure:
            if not reason or not reason.strip():
                raise JobTransitionConflict(
                    f"entering {target.value} requires a nonempty failure "
                    "reason (no silent failure transitions)"
                )
            return
        if target is StorageJobStatus.CHECKPOINT_ADVANCED and not via_gate:
            # §16: the resume point may only move through the gated path.
            raise JobTransitionConflict(
                "CHECKPOINT_ADVANCED is entered only via advance_checkpoint "
                "(durable-proof gate), never via a plain transition"
            )
        current_rank = _progress_rank(current)
        target_rank = _progress_rank(target)
        if current_rank is None:
            # retry resume: FAILED_RETRYABLE -> a progress state
            if current is StorageJobStatus.FAILED_RETRYABLE:
                if not reason or not reason.strip():
                    raise JobTransitionConflict(
                        "retry resume from FAILED_RETRYABLE requires a "
                        "nonempty reason (backward moves are never silent)"
                    )
                return
            raise JobTransitionConflict(
                f"cannot leave {current.value} to {target.value}"
            )
        if target_rank is None:
            raise JobTransitionConflict(
                f"cannot enter {target.value} without a failure reason"
            )
        if target_rank - current_rank == 1:
            return
        if target_rank > current_rank:
            if via_gate and target is StorageJobStatus.CHECKPOINT_ADVANCED:
                # The gated edge IS the proof: durable evidence at or above
                # the configured floor authorizes the cursor jump past the
                # intermediate operational states.
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
            if not reason or not reason.strip():
                raise JobTransitionConflict(
                    "CHECKPOINT_ADVANCED -> ACQUIRING is a backward move "
                    "and requires a nonempty continuation reason"
                )
            return
        raise JobTransitionConflict(
            f"silent backward move {current.value} -> {target.value} is "
            "forbidden (03 doc §15)"
        )

    def _require_checkpoint_eligible(self, status: StorageJobStatus) -> None:
        current_rank = _progress_rank(status)
        floor_rank = _progress_rank(self._min_durable_status)
        if (
            current_rank is not None
            and floor_rank is not None
            and current_rank >= floor_rank
        ):
            return
        raise JobResumeGateError(
            f"resume advancement requires batch evidence at "
            f"{self._min_durable_status.value}; job status is "
            f"{status.value} (§16: the cursor never advances past "
            "unindexed evidence)"
        )

    def _prove_batch_durable(self, acquisition_id: str, manifest_id: str) -> None:
        """Resolve §16 proof from durable truth (never caller claims)."""
        try:
            acquisition = self._acquisitions.get_acquisition(acquisition_id)
        except CatalogError as exc:
            raise JobResumeGateError(
                f"batch acquisition {acquisition_id!r} is not durable: {exc}"
            ) from exc
        blob_sha = acquisition.blob_sha256
        if not blob_sha:
            raise JobResumeGateError(
                f"batch acquisition {acquisition_id!r} carries no blob — "
                "nothing durable to anchor the resume point to"
            )
        verified = False
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
        if self._min_durable_status is StorageJobStatus.RAW_COMMITTED:
            return
        try:
            manifest = self._manifests.get_manifest(manifest_id)
        except Exception as exc:
            raise JobResumeGateError(
                f"batch manifest {manifest_id!r} is not durable: {exc}"
            ) from exc
        if blob_sha not in manifest.blob_refs:
            raise JobResumeGateError(
                f"manifest {manifest_id} does not contain batch blob "
                f"{blob_sha} — the batch is not manifest-committed"
            )

    # -- chain plumbing --------------------------------------------------------

    def _event_id(self, job_id: str, sequence: int) -> str:
        return f"{job_id}:{sequence:06d}"

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
        is visible, never silently adopted, never silently generic.
        """
        try:
            return catalog.commit(logical_id, payload)
        except JsonCatalogConflict as exc:
            existing = catalog.get(logical_id)
            if existing is not None and _event_semantics(
                existing
            ) == _event_semantics(payload):
                return existing
            # The conflicting record may exist only on disk (committed by a
            # lost-race writer this process never cached).
            from .json_catalog import catalog_physical_key

            on_disk = catalog.root / catalog_physical_key(logical_id)
            if existing is None and on_disk.is_file():
                try:
                    disk_payload = json.loads(
                        on_disk.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError):
                    disk_payload = None
                if disk_payload is not None and _event_semantics(
                    disk_payload
                ) == _event_semantics(payload):
                    return disk_payload
            raise conflict_error(
                f"durable record {logical_id!r} diverges from the retry "
                f"payload (semantic conflict, no adoption)"
            ) from exc

    # -- coordination (I06 §43/§44 pattern) ------------------------------------

    def _job_lock(self, job_id: str) -> Any:
        outer = self._job_locks.setdefault(job_id, threading.RLock())
        return _NestedFileLock(outer, self, job_id)

    def _acquire_file_lock(self, job_id: str) -> Any:
        if not self._locks_root.exists():
            ensure_durable_directory(self._locks_root)
        lock_path = self._locks_root / f"{job_id}.lock"
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
            (self._locks_root / f"{job_id}.lock").unlink(missing_ok=True)
        except OSError:
            # A crash mid-release leaves recovery evidence for I08.
            pass

    # -- restart validation -----------------------------------------------------

    def _validate_cross_constraints(self) -> None:
        """Fail closed on any chain that violates the frozen doctrine."""
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
            # Durable re-anchoring (I06R1 §11 doctrine): a checkpoint-bearing
            # state is only truthful if its committed pointers still resolve
            # to durable evidence.  Internal consistency is not enough.
            anchor_acq = resulting.last_committed_acquisition_id
            if anchor_acq is not None:
                try:
                    acquisition = self._acquisitions.get_acquisition(anchor_acq)
                except Exception as exc:
                    raise JobCatalogCorrupt(
                        f"event {event_id[:12]}... anchors acquisition "
                        f"{anchor_acq!r} which is not durable: {exc}"
                    ) from exc
                blob_sha = acquisition.blob_sha256
                try:
                    verified = (
                        bool(blob_sha)
                        and self._blob_metadata.has_verified_physical(blob_sha)
                    )
                except Exception as exc:
                    raise JobCatalogCorrupt(
                        f"event {event_id[:12]}... anchored blob could not "
                        f"be verified: {exc}"
                    ) from exc
                if not verified:
                    raise JobCatalogCorrupt(
                        f"event {event_id[:12]}... anchors acquisition "
                        f"{anchor_acq!r} whose blob is not physically "
                        "verified"
                    )
            anchor_manifest = resulting.last_manifest_id
            if anchor_manifest is not None:
                try:
                    self._manifests.get_manifest(anchor_manifest)
                except Exception as exc:
                    raise JobCatalogCorrupt(
                        f"event {event_id[:12]}... anchors manifest "
                        f"{anchor_manifest!r} which is not durable: {exc}"
                    ) from exc
        # Per-job chain validation: contiguity, linkage, chronology.
        for job_id, birth in seen_jobs.items():
            events = self._job_events(job_id)
            birth_state = StorageJobState.model_validate(birth["job_state"])
            previous_status = birth_state.status
            previous_time = birth_state.updated_at
            previous_rank = _progress_rank(previous_status)
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
                if transition.from_status is not previous_status:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} chain break at "
                        f"{transition.transition_id}: from_status "
                        f"{transition.from_status.value} != previous "
                        f"{previous_status.value}"
                    )
                if transition.transitioned_at < previous_time:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} transition chronology moves "
                        "backward at " + transition.transition_id
                    )
                if resulting.updated_at < transition.transitioned_at:
                    raise JobCatalogCorrupt(
                        f"job {job_id!r} state updated_at precedes its "
                        f"transition at {transition.transition_id}"
                    )
                rank = _progress_rank(resulting.status)
                if (
                    previous_rank is not None
                    and rank is not None
                    and rank < previous_rank
                ):
                    reason = transition.reason
                    allowed_backward = (
                        previous_status is StorageJobStatus.CHECKPOINT_ADVANCED
                        and resulting.status is StorageJobStatus.ACQUIRING
                    ) or (previous_status is StorageJobStatus.FAILED_RETRYABLE)
                    if not (allowed_backward and reason and reason.strip()):
                        raise JobCatalogCorrupt(
                            f"job {job_id!r} contains a silent backward "
                            f"move at {transition.transition_id}"
                        )
                previous_status = resulting.status
                previous_time = resulting.updated_at
                previous_rank = rank


class _NestedFileLock:
    """Acquires the per-job file lock while holding the in-process lock.

    Re-entrant within one thread: the gated checkpoint path calls the
    transition path under the already-held job lock, so a nested entry
    only bumps a depth counter instead of deadlocking on its own file.
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
