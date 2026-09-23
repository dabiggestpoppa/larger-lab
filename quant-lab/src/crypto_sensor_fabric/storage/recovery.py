"""SENSOR-B4-I08 — recovery / quarantine scanner (03 doc §17-§20).

TWO explicit phases (I08 §5): SCAN (READ-ONLY by default) and APPLY.

The scan NEVER deletes, moves, rewrites, registers provenance, advances
jobs, clears locks, changes manifests or moves a cursor (I08 §5).  It
classifies the current storage truth into typed findings and produces a
deterministic, sorted recovery plan.  Only
:meth:`RecoveryEngine.apply_plan` mutates state, and every applied action
leaves an append-only durable record in the recovery journal (I08 §6/§7)
under ``<t0_root>/catalogs/recovery/actions/`` through the shared
:class:`DurableJsonCatalog` primitive.

``RecoveryAction`` is the FROZEN evidence model (03 doc §17) used
verbatim for every record whose object is one of the seven frozen
``StorageObjectType`` members.  Staging artifacts and job locks are real
recovery objects but have no frozen ``StorageObjectType`` member, so
their durable journal envelope carries the semantic ``object_type``
string directly and ``storage_object_type=None`` — an internal durable
envelope rather than a frozen-model change (I08 §6 "prefer an internal
durable envelope").  The journal's narrow read surface (I08 §32) returns
typed :class:`RecoveryAction` records whenever the frozen model applies.

Doctrine (03 doc §21 + I08): no silent repair; prefer quarantine over
silent repair; never rewrite immutable historical truth; an orphan is
reconciled only when context proves what it is; a stale-looking lock
with unprovable ownership is never auto-deleted; a recovery plan is
revalidated immediately before apply (I08 §28); repeated acquisition is
safer than missing evidence.

Finding vocabulary (I08 §25 — internal, typed; no frozen-enum change):
``UNCOMMITTED_STAGING``, ``ORPHAN_DURABLE_BLOB``, ``ORPHAN_PROJECTION``,
``ORPHAN_MANIFEST``, ``CORRUPT_BLOB``, ``MISSING_MANIFEST_TARGET``,
``ACQUISITION_SOURCE_QUARANTINED``, ``JOB_DURABILITY_DIVERGENCE``,
``LOCK_PRESENT_OWNER_UNPROVEN``, ``UNKNOWN_CONTEXT``.

Quarantine categories implemented (I08 §9): ``integrity`` (corrupt
physical bytes), ``malformed`` (abandoned staging) and
``unknown_context`` (orphans whose identity cannot be proven).  The
security-specific categories of the frozen layout belong to explicit
security policy and are NOT invented here.  Quarantine destinations use
deterministic no-clobber locators under ``<t0_root>/quarantine/``; bytes
are preserved; quarantined artifacts are never canonical T0 evidence.

ZERO network, ZERO provider code, no quota policy (I09), no DuckDB /
Postgres (I10/I11), no RawEvidenceQuery service (I12).
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..contracts.base import coerce_utc
from .atomic import (
    ensure_durable_directory,
    fsync_directory,
    publish_no_replace,
)
from .blob_store import BlobMissing
from .jobs import JobError, JobLockHeld
from .json_catalog import DurableJsonCatalog, JsonCatalogConflict
from .models import RecoveryAction, StorageObjectType

# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class RecoveryError(RuntimeError):
    """Base class for the I08 recovery engine."""


class RecoveryConfigurationError(RecoveryError):
    """The recovery engine was constructed against unusable inputs."""


class RecoveryPlanConflict(RecoveryError):
    """A scanned plan no longer matches durable truth (I08 §28 TOCTOU)."""


class RecoveryActionConflict(RecoveryError):
    """Same logical action id, divergent semantics (I08 §7/§27)."""


class RecoveryQuarantineConflict(RecoveryError):
    """Different bytes target one deterministic quarantine locator (I08 §30)."""


class RecoveryPathSafetyError(RecoveryError):
    """A discovered path or planned destination escapes its root (I08 §29)."""


# ---------------------------------------------------------------------------
# Finding vocabulary + plan model
# ---------------------------------------------------------------------------

PROBLEM_UNCOMMITTED_STAGING = "UNCOMMITTED_STAGING"
PROBLEM_ORPHAN_DURABLE_BLOB = "ORPHAN_DURABLE_BLOB"
PROBLEM_ORPHAN_PROJECTION = "ORPHAN_PROJECTION"
PROBLEM_ORPHAN_MANIFEST = "ORPHAN_MANIFEST"
PROBLEM_CORRUPT_BLOB = "CORRUPT_BLOB"
PROBLEM_MISSING_MANIFEST_TARGET = "MISSING_MANIFEST_TARGET"
PROBLEM_ACQUISITION_SOURCE_QUARANTINED = "ACQUISITION_SOURCE_QUARANTINED"
PROBLEM_JOB_DURABILITY_DIVERGENCE = "JOB_DURABILITY_DIVERGENCE"
PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN = "LOCK_PRESENT_OWNER_UNPROVEN"
PROBLEM_UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"
# I08R1 §12/§14: continuation + record-only refinement findings.
PROBLEM_ORPHAN_BLOB_CONTINUATION = "ORPHAN_BLOB_CONTINUATION"

FINDING_PROBLEMS: frozenset[str] = frozenset(
    {
        PROBLEM_UNCOMMITTED_STAGING,
        PROBLEM_ORPHAN_DURABLE_BLOB,
        PROBLEM_ORPHAN_PROJECTION,
        PROBLEM_ORPHAN_MANIFEST,
        PROBLEM_CORRUPT_BLOB,
        PROBLEM_MISSING_MANIFEST_TARGET,
        PROBLEM_ACQUISITION_SOURCE_QUARANTINED,
        PROBLEM_JOB_DURABILITY_DIVERGENCE,
        PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        PROBLEM_UNKNOWN_CONTEXT,
    }
)

QUARANTINE_CATEGORY_INTEGRITY = "integrity"
QUARANTINE_CATEGORY_MALFORMED = "malformed"
QUARANTINE_CATEGORY_UNKNOWN_CONTEXT = "unknown_context"
QUARANTINE_CATEGORIES: frozenset[str] = frozenset(
    {
        QUARANTINE_CATEGORY_INTEGRITY,
        QUARANTINE_CATEGORY_MALFORMED,
        QUARANTINE_CATEGORY_UNKNOWN_CONTEXT,
    }
)

# Semantic object types for the journal envelope where the frozen
# StorageObjectType has no member (I08 §6 internal-envelope rule).
SEMANTIC_STAGING_ARTIFACT = "STAGING_ARTIFACT"
SEMANTIC_JOB_LOCK = "JOB_LOCK"

_ACTION_QUARANTINE_CORRUPT_BLOB = "QUARANTINE_CORRUPT_BLOB"
_ACTION_QUARANTINE_UNKNOWN_CONTEXT = "QUARANTINE_UNKNOWN_CONTEXT"
_ACTION_RECORD_UNREFERENCED_PROJECTION = "RECORD_UNREFERENCED_PROJECTION"
_ACTION_CONTINUE_ORPHAN_BLOB = "CONTINUE_ORPHAN_BLOB"
_ACTION_RESOLVE_ORPHAN_BLOB = "RESOLVE_ORPHAN_BLOB"
_ACTION_QUARANTINE_STAGING = "QUARANTINE_STAGING"
_ACTION_QUARANTINE_ORPHAN_PROJECTION = "QUARANTINE_ORPHAN_PROJECTION"
_ACTION_RESOLVE_ORPHAN_MANIFEST = "RESOLVE_ORPHAN_MANIFEST"
_ACTION_RECORD_MISSING_TARGET = "RECORD_MISSING_TARGET"
_ACTION_RECORD_ACQUISITION_DEPENDENCY = "RECORD_ACQUISITION_DEPENDENCY"
_ACTION_QUARANTINE_JOB = "QUARANTINE_JOB"
_ACTION_RECORD_LOCK_ONLY = "RECORD_LOCK_ONLY"

# I08R1 §9: bounded-memory streaming constants for quarantine copies.
_QUAR_COPY_CHUNK_BYTES = 1 << 20
_QUAR_COPY_MAX_CHUNKS = 1 << 12


def _quar_copy_assert_synthetic(
    source: Path, staging: Path, *skip_chunk: object
) -> None:
    """Test-only injection seam for the bounded-copy streaming proof (§9).

    The streaming proof monkeypatches this hook and asserts the bounded
    chunk stream never reads the payload through ``read_bytes``;
    production code never calls the hook (only the test does).
    """
    del source, staging, skip_chunk  # pragma: no cover - test seam only


def _quar_copy_stream(source: Path, staging: Path) -> tuple[int, str]:
    """Bounded-memory stream copy: (bytes_written, content_sha256).

    The I08R1 §9 contract: a quarantine copy must never buffer a whole
    evidence file in memory.  The payload streams in fixed chunks while
    the digest accumulates in the same pass.
    """
    _quar_copy_assert_synthetic(source, staging)
    digest = hashlib.sha256()
    total = 0
    with open(source, "rb") as src, open(staging, "wb") as dst:
        while True:
            chunk = src.read(_QUAR_COPY_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            dst.write(chunk)
            total += len(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    return total, digest.hexdigest()


_SHA256_EXPECTED_LENGTH = 64
_HEX_DIGITS = frozenset("0123456789abcdef")


def _is_sha256_hex(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_EXPECTED_LENGTH
        and all(ch in _HEX_DIGITS for ch in value)
    )


def _canonical(value: Any) -> str:
    """Deterministic canonical JSON text (sorted keys) for ids/states."""
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as raw:
        for chunk in iter(lambda: raw.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_state(state: dict[str, Any] | None) -> str | None:
    return None if state is None else _canonical(state)


@dataclass(frozen=True)
class RecoveryFinding:
    """One deterministic finding of a read-only scan (I08 §26)."""

    problem: str
    object_type: str
    object_id: str
    detail: str
    before_state: dict[str, Any] = field(default_factory=dict)
    proposed_resolution: str = ""


@dataclass(frozen=True)
class RecoveryPlanAction:
    """One explicit, revalidatable recovery action (I08 §5/§28)."""

    action_kind: str
    object_type: str
    object_id: str
    problem: str
    resolution: str
    before_state: dict[str, Any]
    after_state: dict[str, Any] = field(default_factory=dict)
    detail: str = ""


@dataclass(frozen=True)
class RecoveryScanResult:
    """Deterministic output of one read-only scan (I08 §26)."""

    recovery_run_id: str
    findings: tuple[RecoveryFinding, ...]
    counts_by_problem: dict[str, int]
    has_blockers: bool
    planned_actions: tuple[RecoveryPlanAction, ...]

    def to_dict(self) -> dict[str, Any]:
        """Canonical, sorted payload (determinism across runs)."""

        def finding_dict(f: RecoveryFinding) -> dict[str, Any]:
            return {
                "problem": f.problem,
                "object_type": f.object_type,
                "object_id": f.object_id,
                "detail": f.detail,
                "before_state": f.before_state,
                "proposed_resolution": f.proposed_resolution,
            }

        def action_dict(a: RecoveryPlanAction) -> dict[str, Any]:
            return {
                "action_kind": a.action_kind,
                "object_type": a.object_type,
                "object_id": a.object_id,
                "problem": a.problem,
                "resolution": a.resolution,
                "before_state": a.before_state,
                "after_state": a.after_state,
                "detail": a.detail,
            }

        return {
            "recovery_run_id": self.recovery_run_id,
            "findings": [finding_dict(f) for f in self.findings],
            "counts_by_problem": dict(sorted(self.counts_by_problem.items())),
            "has_blockers": self.has_blockers,
            "planned_actions": [action_dict(a) for a in self.planned_actions],
        }


def action_identity(payload: dict[str, Any]) -> str:
    """Collision-safe deterministic logical action id (I08 §7).

    Full SHA-256 over the canonical recovery semantics —
    recovery_run_id / object_type / object_id / problem / resolution /
    before_state / after_state — with registration time EXCLUDED, so an
    operational clock can never change scientific identity.
    """
    semantic = {
        "recovery_run_id": payload["recovery_run_id"],
        "object_type": payload["object_type"],
        "object_id": payload["object_id"],
        "problem": payload["problem"],
        "resolution": payload["resolution"],
        "before_state": payload.get("before_state"),
        "after_state": payload.get("after_state"),
    }
    return hashlib.sha256(_canonical(semantic).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Recovery journal (I08 §7/§27/§32)
# ---------------------------------------------------------------------------


class RecoveryJournal:
    """Append-only durable recovery journal over ``DurableJsonCatalog``.

    Physical location: ``<t0_root>/catalogs/recovery/actions/`` — hashed
    physical keys, staged fsync'd writes, no-clobber publish, corruption
    fail-closed, and the I07R1F internal cache lock.  Logical id =
    :func:`action_identity` (full SHA-256 of the canonical semantics);
    exact retries are idempotent, divergent semantics under one id raise
    :class:`RecoveryActionConflict`, and nothing is ever overwritten.
    """

    def __init__(self, t0_root: str | Path) -> None:
        self._catalog = DurableJsonCatalog(
            Path(t0_root) / "catalogs" / "recovery" / "actions",
            logical_id_field="recovery_action_id",
        )

    def record(
        self,
        *,
        recovery_run_id: str,
        object_type: str,
        object_id: str,
        problem: str,
        resolution: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        registered_at: datetime | None = None,
        action_kind: str | None = None,
    ) -> tuple[str, bool]:
        """Commit one durable recovery record; idempotent on exact retry.

        Returns ``(action_id, adopted_existing)``.  A retry with EXACTLY
        the same canonical semantics adopts the existing record (the
        journal never duplicates); the same id with divergent semantics
        raises :class:`RecoveryActionConflict`.  ``action_kind`` is
        envelope-level operational context for run dedup — the §7
        identity hash stays exactly the seven semantic fields.
        """
        if not isinstance(recovery_run_id, str) or not recovery_run_id:
            raise RecoveryConfigurationError(
                "recovery_run_id must be a nonempty string"
            )
        if not isinstance(object_id, str) or not object_id:
            raise RecoveryConfigurationError("object_id must be nonempty")
        if not isinstance(problem, str) or not problem.strip():
            raise RecoveryConfigurationError("problem must be nonempty")
        if not isinstance(resolution, str) or not resolution.strip():
            raise RecoveryConfigurationError("resolution must be nonempty")
        # Normalize once so None and {} are the SAME semantics everywhere
        # (identity, envelope, semantic comparison) — a retry that passes
        # the other spelling stays an exact retry, never a false conflict.
        before_state = before_state or {}
        after_state = after_state or {}
        storage_object_type: str | None
        try:
            storage_object_type = StorageObjectType(object_type).value
        except ValueError:
            storage_object_type = None
        logical_id = action_identity(
            {
                "recovery_run_id": recovery_run_id,
                "object_type": object_type,
                "object_id": object_id,
                "problem": problem,
                "resolution": resolution,
                "before_state": before_state or {},
                "after_state": after_state or {},
            }
        )
        envelope: dict[str, Any] = {
            "record_type": "recovery_action",
            "recovery_action_id": logical_id,
            "recovery_run_id": recovery_run_id,
            "object_type": object_type,
            "storage_object_type": storage_object_type,
            "object_id": object_id,
            "problem": problem,
            "resolution": resolution,
            "before_state": _json_state(before_state),
            "after_state": _json_state(after_state),
            "evidence_ref": None,
            "action_kind": action_kind,
            "registered_at": (
                coerce_utc(registered_at).isoformat()
                if registered_at is not None
                else datetime.now(UTC).isoformat()
            ),
        }
        try:
            committed = self._catalog.commit(logical_id, envelope)
        except JsonCatalogConflict:
            # Same logical id + different envelope bytes.  The catalog is
            # right that nothing is overwritten — but registration time is
            # NOT semantic (I08 §7), so an exact retry of the same semantics
            # ADOPTS the durable record instead of conflicting.  Genuine
            # divergence (tampered fragment, format drift) still fails typed.
            existing = self._catalog.get(logical_id)
            if existing is None or not self._same_semantics(existing, envelope):
                raise RecoveryActionConflict(
                    f"recovery action {logical_id[:12]}... already exists "
                    "with DIVERGENT semantics; nothing overwritten (I08 §7)"
                ) from None
            committed = existing
        return logical_id, committed is not envelope

    @staticmethod
    def _same_semantics(
        existing: dict[str, Any], envelope: dict[str, Any]
    ) -> bool:
        """True iff the durable record and the retry agree on ALL semantic
        fields (everything except the operational ``registered_at``)."""
        semantic_keys = (
            "record_type",
            "recovery_action_id",
            "recovery_run_id",
            "object_type",
            "storage_object_type",
            "object_id",
            "problem",
            "resolution",
            "before_state",
            "after_state",
            "evidence_ref",
            "action_kind",
        )
        return all(existing.get(k) == envelope.get(k) for k in semantic_keys)

    def get(self, recovery_action_id: str) -> dict[str, Any] | None:
        """Exact durable record by logical id, or None (I08 §32)."""
        return self._catalog.get(recovery_action_id)

    def action_ids(self) -> list[str]:
        """All durable logical action ids (sorted)."""
        return sorted(self._catalog.list_ids())

    def list_for_run(self, recovery_run_id: str) -> list[dict[str, Any]]:
        """All durable records of one recovery run (I08 §32, sorted)."""
        found = [
            payload
            for logical_id in self._catalog.list_ids()
            if (payload := self._catalog.get(logical_id)) is not None
            and payload.get("recovery_run_id") == recovery_run_id
        ]
        found.sort(key=lambda p: p["recovery_action_id"])
        return found

    def list_for_object(self, object_type: str, object_id: str) -> list[dict[str, Any]]:
        """All durable records against one object (I08 §32, sorted)."""
        found = [
            payload
            for logical_id in self._catalog.list_ids()
            if (payload := self._catalog.get(logical_id)) is not None
            and payload.get("object_type") == object_type
            and payload.get("object_id") == object_id
        ]
        found.sort(key=lambda p: p["recovery_action_id"])
        return found

    def to_recovery_action(self, payload: dict[str, Any]) -> RecoveryAction | None:
        """The frozen ``RecoveryAction`` for a record, when applicable.

        Records whose semantic object_type has a frozen
        ``StorageObjectType`` member map to the frozen model verbatim;
        internal-envelope records (staging artifacts, job locks) return
        None — the durable envelope itself is the evidence record (I08 §6).
        """
        member = payload.get("storage_object_type")
        if member is None:
            return None
        return RecoveryAction(
            recovery_run_id=payload["recovery_run_id"],
            object_type=StorageObjectType(member),
            object_id=payload["object_id"],
            problem=payload["problem"],
            resolution=payload["resolution"],
            before_state=payload.get("before_state"),
            after_state=payload.get("after_state"),
            evidence_ref=None,
        )


# ---------------------------------------------------------------------------
# Recovery operation journal (I08R1 §4) — effect-first evidence
# ---------------------------------------------------------------------------


class RecoveryOperationJournal:
    """Append-only durable OPERATION journal (I08R1 §4) over ``DurableJsonCatalog``.

    Physical location ``<t0_root>/catalogs/recovery/operations/``.  Where the
    RecoveryAction journal (I08 §7) records what recovery DID, this journal
    makes recovery effects REPLAYABLE: a durable INTENT record is committed
    BEFORE the first irreversible effect (I08R1 §5), and each later phase is
    APPENDED as a new record — never a mutation of an existing row.

    Operation identity is deterministic over (recovery_run_id, action_kind,
    object_type, object_id, planned semantics); phase is part of the record
    key, so each phase of one operation is its own append-only row.  Exact
    retries are idempotent; divergent semantics under one operation id raise
    :class:`RecoveryActionConflict` (I08R1 §4).  Registration timestamps are
    excluded from identity.
    """

    PHASE_INTENT = "INTENT"
    PHASE_EFFECT_COMMITTED = "EFFECT_COMMITTED"
    PHASE_COMPLETED = "COMPLETED"
    PHASE_UNRESOLVED = "UNRESOLVED"
    _PHASES = (
        PHASE_INTENT,
        PHASE_EFFECT_COMMITTED,
        PHASE_COMPLETED,
        PHASE_UNRESOLVED,
    )

    def __init__(self, t0_root: str | Path) -> None:
        self._catalog = DurableJsonCatalog(
            Path(t0_root) / "catalogs" / "recovery" / "operations",
            logical_id_field="recovery_operation_id",
        )

    @staticmethod
    def operation_id(
        *,
        recovery_run_id: str,
        action_kind: str,
        object_type: str,
        object_id: str,
        problem: str,
        resolution: str,
        before_state: dict[str, Any] | None,
        after_state: dict[str, Any] | None,
    ) -> str:
        """Deterministic operation identity (I08R1 §4) — full SHA-256 over
        the run + action semantics; registration time excluded."""
        semantic = {
            "recovery_run_id": recovery_run_id,
            "action_kind": action_kind,
            "object_type": object_type,
            "object_id": object_id,
            "problem": problem,
            "resolution": resolution,
            "before_state": before_state or {},
            "after_state": after_state or {},
        }
        return hashlib.sha256(_canonical(semantic).encode("utf-8")).hexdigest()

    def record_phase(
        self,
        *,
        recovery_run_id: str,
        action_kind: str,
        object_type: str,
        object_id: str,
        problem: str,
        resolution: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        phase: str = PHASE_INTENT,
        detail: str | None = None,
        registered_at: datetime | None = None,
    ) -> tuple[str, bool]:
        """Append one phase of a recovery operation (idempotent on exact retry).

        The operation id is derived from (run, action_kind, object,
        planned semantics); the phase becomes part of the physical record
        key, so each phase is an APPEND of its own row (I08R1 §4: never a
        mutation of one journal row)."""
        if phase not in self._PHASES:
            raise RecoveryConfigurationError(
                f"unknown recovery operation phase {phase!r}"
            )
        operation_id = self.operation_id(
            recovery_run_id=recovery_run_id,
            action_kind=action_kind,
            object_type=object_type,
            object_id=object_id,
            problem=problem,
            resolution=resolution,
            before_state=before_state,
            after_state=after_state,
        )
        # Each phase is its own append-only row.  EFFECT_COMMITTED rows are
        # detail-qualified: one operation may commit SEVERAL durable effects
        # (the orphan two-step reconciliation), each with its own row.
        phase_key = phase
        if phase == self.PHASE_EFFECT_COMMITTED:
            detail_key = hashlib.sha256((detail or "").encode("utf-8")).hexdigest()[:16]
            phase_key = f"{phase}:{detail_key}"
        record_id = f"{operation_id}:{phase_key}"
        envelope: dict[str, Any] = {
            "record_type": "recovery_operation",
            # The catalog identity field must equal the committed logical
            # id — the PHASE-QUALIFIED record id (each phase is its own
            # append-only row).  The phase-free operation id is carried
            # separately so all rows of one operation remain linked.
            "recovery_operation_id": record_id,
            "operation_id": operation_id,
            "phase": phase,
            "recovery_run_id": recovery_run_id,
            "action_kind": action_kind,
            "object_type": object_type,
            "object_id": object_id,
            "problem": problem,
            "resolution": resolution,
            "before_state": _json_state(before_state),
            "after_state": _json_state(after_state),
            "detail": detail,
            "registered_at": (
                coerce_utc(registered_at).isoformat()
                if registered_at is not None
                else datetime.now(UTC).isoformat()
            ),
        }
        try:
            committed = self._catalog.commit(record_id, envelope)
        except JsonCatalogConflict as exc:
            existing = self._catalog.get(record_id)
            if existing is not None and existing.get("detail") == envelope.get(
                "detail"
            ):
                committed = existing
            else:
                raise RecoveryActionConflict(
                    f"recovery operation {record_id[:12]}... already exists "
                    "with DIVERGENT phase content; nothing overwritten "
                    "(I08R1 §4)"
                ) from exc
        return operation_id, committed is not envelope

    def phases(self, operation_id: str) -> tuple[str, ...]:
        """Durably recorded phase labels of one operation, in frozen order.

        EFFECT_COMMITTED rows are detail-qualified (one operation may
        commit several durable effects); duplicates of the same phase
        collapse to the first occurrence in frozen order."""
        found: list[str] = []
        for phase in self._PHASES:
            if phase == self.PHASE_EFFECT_COMMITTED:
                if any(
                    rid.startswith(f"{operation_id}:{phase}:")
                    for rid in self._catalog.list_ids()
                ):
                    found.append(phase)
            elif self._catalog.get(f"{operation_id}:{phase}") is not None:
                found.append(phase)
        return tuple(found)

    def has_phase(self, operation_id: str, phase: str) -> bool:
        if phase == self.PHASE_EFFECT_COMMITTED:
            return any(
                rid.startswith(f"{operation_id}:{phase}:")
                for rid in self._catalog.list_ids()
            )
        return self._catalog.get(f"{operation_id}:{phase}") is not None

    def get_phase(self, operation_id: str, phase: str) -> dict[str, Any] | None:
        return self._catalog.get(f"{operation_id}:{phase}")

    def all_operations(self) -> list[dict[str, Any]]:
        """Every durable operation-phase record (sorted by record id)."""
        return [
            payload
            for rid in sorted(self._catalog.list_ids())
            if (payload := self._catalog.get(rid)) is not None
        ]

    def list_for_object(
        self, object_type: str, object_id: str
    ) -> list[dict[str, Any]]:
        """All durable operation records against one object (sorted)."""
        found = [
            payload
            for logical_id in self._catalog.list_ids()
            if (payload := self._catalog.get(logical_id)) is not None
            and payload.get("object_type") == object_type
            and payload.get("object_id") == object_id
        ]
        found.sort(key=lambda p: p["recovery_operation_id"])
        return found


# ---------------------------------------------------------------------------
# The recovery engine
# ---------------------------------------------------------------------------


class RecoveryEngine:
    """SCAN (read-only) / APPLY (explicit) recovery over one T0 root.

    Constructor dependencies are the ALREADY-ACCEPTED I04/I05/I07
    repositories — recovery adds no second implementation of any
    repository; it reads them and, for apply, mutates ONLY through their
    existing public APIs (I08 §12/§14/§15/§18: no hand-written catalog
    fragments, no manufactured provenance, no invented lineage).
    """

    def __init__(
        self,
        t0_root: str | Path,
        *,
        blob_store: Any,
        blob_metadata_repository: Any,
        acquisition_repository: Any,
        manifest_repository: Any,
        job_repository: Any = None,
        projection_artifact_repository: Any = None,
        clock: Callable[[], datetime] | None = None,
        recovery_run_id: str | None = None,
    ) -> None:
        self._t0_root = Path(t0_root)
        if not self._t0_root.is_dir():
            raise RecoveryConfigurationError(
                f"t0_root {self._t0_root!s} is not an existing directory"
            )
        self._blob_store = blob_store
        self._blob_metadata = blob_metadata_repository
        self._acquisitions = acquisition_repository
        self._manifests = manifest_repository
        self._jobs = job_repository
        self._artifacts = projection_artifact_repository
        self._clock = clock if clock is not None else (lambda: datetime.now(UTC))
        self._journal = RecoveryJournal(self._t0_root)
        self._operations = RecoveryOperationJournal(self._t0_root)
        self._orphan_context: dict[str, tuple[Any, Any]] = {}
        if recovery_run_id is not None and (
            not isinstance(recovery_run_id, str) or not recovery_run_id
        ):
            raise RecoveryConfigurationError(
                "recovery_run_id must be None or a nonempty string"
            )
        self._explicit_run_id = recovery_run_id

    # -- run ids + explicit context ------------------------------------------

    def new_run_id(self) -> str:
        """One explicit run id per scan/apply pair (I08 §8).

        I08R1 §26: operational auto-generation uses ``uuid.uuid4`` — at
        least 128 bits of cryptographically strong randomness, so ids are
        collision-safe across instances, processes and restarts.  Never a
        wall-clock format, never a temp path, never a process memory
        address (the retired ``id(self)`` scheme failed that bar).
        Deterministic evidence builders pass EXPLICIT run ids instead.
        """
        return f"recovery-{uuid.uuid4().hex}"

    def register_orphan_context(
        self, blob_sha256: str, *, evidence_blob: Any, acquisition: Any
    ) -> None:
        """EXPLICIT operator-supplied context for orphan reconciliation.

        I08 §12: reconciliation requires PROVEN context.  Context is
        registered explicitly (never guessed by the engine); the apply
        path still re-verifies the physical bytes against the
        content-addressed name before any metadata/acquisition is
        appended through the PUBLIC repository APIs, whose own validation
        remains authoritative.
        """
        if not _is_sha256_hex(blob_sha256):
            raise RecoveryConfigurationError(
                "orphan context requires the exact content sha256"
            )
        self._orphan_context[blob_sha256] = (evidence_blob, acquisition)

    @property
    def journal(self) -> RecoveryJournal:
        """The durable recovery journal (narrow read surface, I08 §32)."""
        return self._journal

    @property
    def operations(self) -> RecoveryOperationJournal:
        """The durable replayable-operation journal (I08R1 §4)."""
        return self._operations

    # -- containment (I08 §29) ----------------------------------------------

    def _contained(self, path: Path, root: Path) -> bool:
        """Lexical + resolved containment (no ``..`` escape, no symlink escape)."""
        try:
            path.relative_to(root)
        except ValueError:
            return False
        try:
            resolved = path.resolve()
            resolved_root = root.resolve()
        except OSError:
            return False
        try:
            resolved.relative_to(resolved_root)
        except ValueError:
            return False
        return True

    def _assert_contained(self, path: Path, root: Path, what: str) -> None:
        if not self._contained(path, root):
            raise RecoveryPathSafetyError(
                f"{what} {path!s} does not resolve under {root!s} (I08 §29)"
            )

    # -- quarantine locators (I08 §9/§10/§30) -------------------------------

    def quarantine_dir(self, category: str) -> Path:
        """Frozen quarantine category directory (created only on apply)."""
        if category not in QUARANTINE_CATEGORIES:
            raise RecoveryConfigurationError(
                f"unknown quarantine category {category!r}; I08 implements "
                f"{sorted(QUARANTINE_CATEGORIES)}"
            )
        return self._t0_root / "quarantine" / category

    def quarantine_destination(
        self,
        category: str,
        *,
        object_type: str,
        object_id: str,
        content_sha256: str,
        suffix: str,
    ) -> Path:
        """Deterministic no-clobber quarantine locator (I08 §10/§30).

        ``quarantine/<category>/<object_type>-<sha256(bytes)[:32]>-``
        ``<sha256(object_id)[:32]><suffix>`` — content bytes decide
        byte-identity (an exact retry adopts the existing artifact),
        object identity separates distinct objects that happen to share
        bytes.  Full digests back both halves; no raw logical id ever
        becomes a path component (I08 §29).
        """
        if not _is_sha256_hex(content_sha256):
            raise RecoveryConfigurationError(
                "quarantine locator requires the exact sha256 of the bytes"
            )
        id_part = hashlib.sha256(object_id.encode("utf-8")).hexdigest()[:32]
        name = f"{object_type}-{content_sha256[:32]}-{id_part}{suffix}"
        destination = self.quarantine_dir(category) / name
        self._assert_contained(destination, self._t0_root, "quarantine destination")
        return destination

    def _quarantine_file(
        self, source: Path, destination: Path, content_sha256: str
    ) -> bool:
        """No-clobber byte-preserving move into quarantine (I08 §10/§30).

        Publication goes through ``publish_no_replace`` (atomic
        hardlink/no-replace, same durability primitive as every blob
        commit) and the source is unlinked only afterwards, so bytes are
        preserved throughout.  An existing identical artifact is ADOPTED
        (exact retry idempotence); different bytes under the same locator
        raise :class:`RecoveryQuarantineConflict`.  Returns True when this
        call performed the move, False when an identical artifact was
        adopted.
        """
        self._assert_contained(destination, self._t0_root, "quarantine destination")
        self._assert_contained(source, self._t0_root, "quarantine source")
        if destination.exists():
            if _sha256_file(destination) == content_sha256:
                self._unlink_source_after_durable_destination(source, destination)
                return False
            raise RecoveryQuarantineConflict(
                f"quarantine destination {destination.name} already holds "
                "DIFFERENT bytes; nothing overwritten (I08 §30)"
            )
        ensure_durable_directory(destination.parent)
        staging = destination.parent / f"{destination.name}.staging"
        staging.unlink(missing_ok=True)
        # I08R1 §9: BOUNDED-MEMORY streaming copy — the source payload is
        # never buffered whole (no ``read_bytes``); bytes stream in fixed
        # chunks with the digest computed in the same pass and the staged
        # file fsync'd before publication.
        _copied, copied_sha = _quar_copy_stream(source, staging)
        if copied_sha != content_sha256:
            staging.unlink(missing_ok=True)
            raise RecoveryQuarantineConflict(
                f"quarantine copy of {destination.name} diverged from the "
                "scanned content identity; nothing published"
            )
        try:
            publish_no_replace(staging, destination)
        except OSError as exc:
            staging.unlink(missing_ok=True)
            raise RecoveryQuarantineConflict(
                f"quarantine publication failed for {destination.name}: {exc}"
            ) from exc
        fsync_directory(destination.parent)
        # I08R1 §9: the source is unlinked ONLY after the destination is
        # durably published (and its directory fsync'd).
        self._unlink_source_after_durable_destination(source, destination)
        return True

    def _unlink_source_after_durable_destination(
        self, source: Path, destination: Path
    ) -> None:
        """Remove the source only after the destination exists durably;
        fsync the source parent afterwards (I08R1 §9)."""
        if not destination.exists():
            raise RecoveryQuarantineConflict(
                f"refusing to unlink {source.name}: quarantine destination "
                f"{destination.name} is not durably present"
            )
        source.unlink(missing_ok=True)
        fsync_directory(source.parent)

    # -- interrupted-operation continuation (I08R1 §6/§8) ---------------------

    def _finalize_open_operations(self) -> list[dict[str, Any]]:
        """Adopt operations whose effect landed but whose outcome row died.

        I08R1 §6/§8: a crash AFTER a durable effect but BEFORE the final
        RecoveryAction must converge on retry — the landed effect is
        recognized as THIS operation's committed step (exact intent
        semantics), never misread as a stale plan, and no new durable
        mutation is invented here.  Adoption only runs inside APPLY
        (an apply is the explicit recovery act); scan stays read-only.
        """
        adopted: list[dict[str, Any]] = []
        for record in self._operations.all_operations():
            phases = record.get("phase")
            if phases not in ("INTENT", "EFFECT_COMMITTED"):
                continue
            if self._operations.has_phase(record["operation_id"], "COMPLETED"):
                continue
            if self._operations.has_phase(record["operation_id"], "UNRESOLVED"):
                continue
            # Operation rows store states as canonical JSON STRINGS
            # (the frozen envelope keeps text columns); parse before use.
            raw_before = record.get("before_state")
            parsed_before: dict[str, Any] = {}
            if isinstance(raw_before, str) and raw_before:
                parsed_before = dict(json.loads(raw_before))
            elif isinstance(raw_before, dict):
                parsed_before = dict(raw_before)
            planned = RecoveryPlanAction(
                action_kind=record["action_kind"],
                object_type=record["object_type"],
                object_id=record["object_id"],
                problem=record["problem"],
                resolution=record["resolution"],
                before_state=parsed_before,
            )
            effect = self._effect_already_durable(planned)
            if effect is None:
                continue
            adopted.append(
                {
                    "operation_id": record["operation_id"],
                    "action_kind": planned.action_kind,
                    "object_type": planned.object_type,
                    "object_id": planned.object_id,
                    "effect": effect,
                }
            )
        return adopted

    def _effect_already_durable(self, planned: RecoveryPlanAction) -> str | None:
        """Recognize THIS operation's durable effect (no new mutation).

        Evidence-only kinds adopt on their journaled RecoveryAction;
        quarantine kinds adopt when the canonical object is already gone
        under a prior durable record for the same object + problem.
        Returns the adopted-effect description, or None.
        """
        if planned.action_kind in (
            _ACTION_RECORD_MISSING_TARGET,
            _ACTION_RECORD_ACQUISITION_DEPENDENCY,
            _ACTION_RECORD_LOCK_ONLY,
        ):
            prior = self._journal.list_for_object(
                planned.object_type, planned.object_id
            )
            if any(r.get("problem") == planned.problem for r in prior):
                return "recovery evidence already recorded"
            return None
        if planned.action_kind in (
            _ACTION_QUARANTINE_CORRUPT_BLOB,
            _ACTION_QUARANTINE_STAGING,
            _ACTION_QUARANTINE_ORPHAN_PROJECTION,
            _ACTION_QUARANTINE_UNKNOWN_CONTEXT,
        ):
            relative = (planned.before_state or {}).get("relative_path")
            if isinstance(relative, str) and relative:
                canonical = self._t0_root / relative
                if canonical.exists():
                    return None
                prior = self._journal.list_for_object(
                    planned.object_type, planned.object_id
                )
                if any(r.get("problem") == planned.problem for r in prior):
                    return "canonical object already absent (quarantined)"
            return None
        if planned.action_kind == _ACTION_RESOLVE_ORPHAN_BLOB:
            sha_part = planned.object_id
            encoding_value = (planned.before_state or {}).get(
                "storage_encoding", "NONE"
            )
            try:
                encoding = StorageEncodingValue(encoding_value)
            except ValueError:
                return None
            object_path = self._blob_object_path(sha_part, encoding)
            if object_path.exists():
                return None
            context = self._orphan_context.get(sha_part)
            if context is not None:
                _evidence_blob, acquisition = context
                try:
                    existing = self._acquisitions.get_acquisition(
                        acquisition.acquisition_id
                    )
                except Exception:
                    return None
                if existing.model_dump() == acquisition.model_dump():
                    return "reconciliation steps already committed"
                return None
            return None
        if planned.action_kind == _ACTION_RESOLVE_ORPHAN_MANIFEST:
            manifest = self._manifest_by_id(planned.object_id)
            if manifest is None:
                return None
            try:
                chain_ids = {
                    m.partition_manifest_id
                    for m in self._manifests.list_manifest_versions(
                        manifest.partition_key
                    )
                }
            except Exception:
                return None
            if manifest.partition_manifest_id in chain_ids:
                return "manifest already joined the committed chain"
            return None
        return None

    # -- phase 1: SCAN (READ-ONLY, I08 §5) -----------------------------------

    def scan(self, *, recovery_run_id: str | None = None) -> RecoveryScanResult:
        """Read-only classification of current storage truth (I08 §5/§26).

        Produces deterministic, sorted findings plus planned safe
        actions.  NO deletion, movement, rewrite, provenance
        registration, job advancement, lock clearing or manifest change
        happens here — scanning never mutates anything.
        """
        run_id = recovery_run_id or self._explicit_run_id or self.new_run_id()
        findings: list[RecoveryFinding] = []
        self._scan_staging(findings)
        self._scan_blob_metadata(findings)
        self._scan_orphan_blobs(findings)
        self._scan_acquisition_dependencies(findings)
        self._scan_manifest_targets(findings)
        self._scan_orphan_manifests(findings)
        self._scan_projections(findings)
        self._scan_jobs(findings)
        self._scan_job_locks(findings)
        findings.sort(
            key=lambda f: (f.problem, f.object_type, f.object_id, f.detail)
        )
        counts: dict[str, int] = {}
        for finding in findings:
            counts[finding.problem] = counts.get(finding.problem, 0) + 1
        planned = [
            action
            for action in (self._plan_action_for(f) for f in findings)
            if action is not None
        ]
        return RecoveryScanResult(
            recovery_run_id=run_id,
            findings=tuple(findings),
            counts_by_problem=counts,
            has_blockers=any(
                finding.problem
                in (
                    PROBLEM_CORRUPT_BLOB,
                    PROBLEM_MISSING_MANIFEST_TARGET,
                    PROBLEM_JOB_DURABILITY_DIVERGENCE,
                )
                for finding in findings
            ),
            planned_actions=tuple(planned),
        )

    # -- individual scanners (all read-only) ---------------------------------

    def _scan_staging(self, findings: list[RecoveryFinding]) -> None:
        """§4-A: stale/abandoned staging artifacts.

        The blob store stages under ``<t0_root>/staging/**`` with
        ``<nonce>.partial`` names (verified from the implementation); a
        ``.partial`` file is NEVER evidence merely because it exists —
        each is classified UNCOMMITTED_STAGING with its exact location
        and byte identity.  Reconciliation never advances resume from
        staging (I08 §13).
        """
        staging_root = self._t0_root / "staging"
        if not staging_root.is_dir():
            return
        for path in sorted(staging_root.rglob("*.partial")):
            self._assert_contained(path, self._t0_root, "staging artifact")
            try:
                size = path.stat().st_size
                bytes_sha = _sha256_file(path)
            except OSError:
                continue
            findings.append(
                RecoveryFinding(
                    problem=PROBLEM_UNCOMMITTED_STAGING,
                    object_type=SEMANTIC_STAGING_ARTIFACT,
                    object_id=bytes_sha,
                    detail=(
                        "staged partial artifact at "
                        f"{path.relative_to(self._t0_root).as_posix()} "
                        f"({size} bytes); a .partial file is never evidence"
                    ),
                    before_state={
                        "relative_path": path.relative_to(self._t0_root).as_posix(),
                        "byte_length": size,
                        "bytes_sha256": bytes_sha,
                    },
                    proposed_resolution=(
                        "QUARANTINE_STAGING: preserve the bytes under "
                        "quarantine/malformed and never advance resume from "
                        "staging (I08 §13)"
                    ),
                )
            )

    def _scan_blob_metadata(self, findings: list[RecoveryFinding]) -> None:
        """§4-B/J: durable blob metadata vs physical bytes (03 doc §7).

        Every durable EvidenceBlob row's physical object is re-verified
        through the blob store.  Corrupt/undecodable bytes are
        CORRUPT_BLOB (detection only — never silently overwritten);
        absent bytes for durable metadata are also surfaced (canonical
        reads fail closed).  Quarantine-state rows are already-sealed
        evidence and produce NO new finding.
        """
        from .enums import IntegrityState

        for meta in self._all_blob_metadata():
            try:
                check = self._blob_store.verify_blob(
                    meta.blob_sha256,
                    meta.storage_encoding,
                    expected_byte_length=meta.byte_length,
                )
            except BlobMissing:
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_CORRUPT_BLOB,
                        object_type=StorageObjectType.EVIDENCE_BLOB.value,
                        object_id=meta.blob_sha256,
                        detail=(
                            "durable blob metadata exists but the physical "
                            "object is absent; canonical reads fail closed"
                        ),
                        before_state={
                            "storage_encoding": meta.storage_encoding.value,
                            "integrity_state": meta.integrity_state.value,
                            "physical_present": False,
                        },
                        proposed_resolution=(
                            "record recovery evidence only; bytes are never "
                            "invented and canonical use stays fail-closed"
                        ),
                    )
                )
                continue
            except Exception as exc:
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_CORRUPT_BLOB,
                        object_type=StorageObjectType.EVIDENCE_BLOB.value,
                        object_id=meta.blob_sha256,
                        detail=(
                            "physical verification failed: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                        before_state={
                            "storage_encoding": meta.storage_encoding.value,
                            "integrity_state": meta.integrity_state.value,
                            "physical_present": True,
                        },
                        proposed_resolution=(
                            "QUARANTINE_CORRUPT_BLOB with the corrupt bytes "
                            "preserved under quarantine/integrity; the "
                            "canonical object is never overwritten (I08 §11)"
                        ),
                    )
                )
                continue
            if check.integrity_state is IntegrityState.QUARANTINED_INTEGRITY_FAILURE:
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_CORRUPT_BLOB,
                        object_type=StorageObjectType.EVIDENCE_BLOB.value,
                        object_id=meta.blob_sha256,
                        detail=(
                            "physical object fails its content identity: "
                            f"{check.detail or 'no detail'}"
                        ),
                        before_state={
                            "storage_encoding": meta.storage_encoding.value,
                            "integrity_state": meta.integrity_state.value,
                            "physical_present": True,
                        },
                        proposed_resolution=(
                            "QUARANTINE_CORRUPT_BLOB with the corrupt bytes "
                            "preserved under quarantine/integrity; the "
                            "canonical object is never overwritten (I08 §11)"
                        ),
                    )
                )
                continue
            # I08R1 §12 (crash 2b): healthy verified metadata with NO
            # usable acquisition referencing it is the mid-reconciliation
            # boundary (metadata append landed, acquisition append
            # crashed).  A CONTINUATION finding — never a duplicate
            # metadata proposal; the apply path completes the missing
            # step through the public acquisition API.
            continuation = self._metadata_without_acquisition(meta.blob_sha256)
            if continuation is not None:
                findings.append(continuation)

    def _scan_orphan_blobs(self, findings: list[RecoveryFinding]) -> None:
        """§4-B (03 doc §3): committed blobs without durable metadata.

        Every physical committed object under ``blobs/sha256/**`` must
        have durable EvidenceBlob metadata; the rename-committed /
        metadata-lost crash case classifies as ORPHAN_DURABLE_BLOB.
        Context may reconcile it later through public APIs; nothing is
        deleted or registered during the scan.
        """
        from .enums import StorageEncoding

        blobs_root = self._t0_root / "blobs" / "sha256"
        if not blobs_root.is_dir():
            return
        known: set[tuple[str, str]] = {
            (meta.blob_sha256, meta.storage_encoding.value)
            for meta in self._all_blob_metadata()
        }
        for path in sorted(blobs_root.rglob("*")):
            if not path.is_file():
                continue
            name = path.name
            if name.endswith(".blob.zst"):
                sha_part, encoding_value = (
                    name[: -len(".blob.zst")],
                    StorageEncoding.ZSTD.value,
                )
            elif name.endswith(".blob"):
                sha_part, encoding_value = (
                    name[: -len(".blob")],
                    StorageEncoding.NONE.value,
                )
            else:
                continue
            if not _is_sha256_hex(sha_part):
                continue
            if (sha_part, encoding_value) in known:
                continue
            self._assert_contained(path, self._t0_root, "committed blob")
            findings.append(
                RecoveryFinding(
                    problem=PROBLEM_ORPHAN_DURABLE_BLOB,
                    object_type=StorageObjectType.EVIDENCE_BLOB.value,
                    object_id=sha_part,
                    detail=(
                        "committed physical blob "
                        f"({encoding_value}) has no durable EvidenceBlob "
                        "metadata (03 doc §3 ORPHAN_DURABLE_BLOB crash case)"
                    ),
                    before_state={
                        "storage_encoding": encoding_value,
                        "relative_path": path.relative_to(
                            self._t0_root
                        ).as_posix(),
                        "stored_byte_length": path.stat().st_size,
                    },
                    proposed_resolution=(
                        "RESOLVE_ORPHAN_BLOB: reconcile ONLY when durable "
                        "context proves the identity through EXISTING public "
                        "repository APIs; otherwise QUARANTINE under "
                        "unknown_context (I08 §12)"
                    ),
                )
            )

    def _metadata_without_acquisition(
        self, sha_part: str
    ) -> RecoveryFinding | None:
        """I08R1 §12 (crash 2b): the metadata-append / acquisition-append
        mid-reconciliation boundary, surfaced from DURABLE truth.

        A blob with durable EvidenceBlob metadata but NO usable
        AcquisitionRecord is a mid-flight ORPHAN_BLOB reconciliation
        (metadata committed, acquisition append crashed).  The finding is
        RECORD-ONLY in plan mapping (no second metadata row is ever
        proposed — provenance is never duplicated); the continuation is
        completed through the public acquisition API on explicit apply.
        Quarantine-state metadata is already-sealed evidence, not a
        continuation.
        """
        from .enums import IntegrityState

        try:
            metas = tuple(self._blob_metadata.get_blob_metadata(sha_part))
        except Exception:
            return None
        if not metas:
            return None
        usable = [
            meta
            for meta in metas
            if meta.integrity_state
            is not IntegrityState.QUARANTINED_INTEGRITY_FAILURE
        ]
        if not usable:
            return None
        if sha_part in self._acquisition_blob_shas():
            return None
        return RecoveryFinding(
            problem=PROBLEM_ORPHAN_BLOB_CONTINUATION,
            object_type=StorageObjectType.EVIDENCE_BLOB.value,
            object_id=sha_part,
            detail=(
                "durable EvidenceBlob metadata exists but no usable "
                "AcquisitionRecord references it: mid-reconciliation "
                "boundary between the metadata append and the acquisition "
                "append (I08R1 §12, crash 2b)"
            ),
            before_state={
                "metadata_durable": True,
                "acquisition_durable": False,
            },
            proposed_resolution=(
                "CONTINUE_ORPHAN_BLOB: register the acquisition through the "
                "public acquisition API with EXPLICIT operator-supplied "
                "context; provenance is never guessed and metadata is never "
                "duplicated (I08R1 §12)"
            ),
        )

    def _acquisition_blob_shas(self) -> set[str]:
        """Every blob sha referenced by a DURABLE acquisition (physical read).

        Fragments are content-addressed parquet files under
        ``catalogs/manifests/acquisitions/``; rows are decoded with the
        repository's OWN schema/decoder — never a shadow parser.
        """
        from .catalog import (
            ACQUISITION_SCHEMA,
            _acquisition_from_row,
            read_fragment,
        )

        acquisitions_root = self._t0_root / "catalogs" / "manifests" / "acquisitions"
        if not acquisitions_root.is_dir():
            return set()
        shas: set[str] = set()
        for path in sorted(acquisitions_root.glob("*.parquet")):
            try:
                rows = read_fragment(path, ACQUISITION_SCHEMA)
            except Exception:
                continue
            for row in rows:
                try:
                    record = _acquisition_from_row(row)
                except Exception:
                    continue
                if record.blob_sha256:
                    shas.add(record.blob_sha256)
        return shas

    def _scan_acquisition_dependencies(
        self, findings: list[RecoveryFinding]
    ) -> None:
        """§4-E (I08 §17): acquisitions whose source blob is unusable.

        Acquisition history is immutable forensic truth: the finding
        records the dependency; the accepted I04R2 provenance gates keep
        such acquisitions non-usable.  Nothing is rewritten.
        """
        unusable: set[str] = set()
        for meta in self._all_blob_metadata():
            try:
                verified = self._blob_metadata.has_verified_physical(
                    meta.blob_sha256
                )
            except Exception:
                verified = False
            if not verified:
                unusable.add(meta.blob_sha256)
        for record in self._all_acquisition_records():
            blob_sha = record.blob_sha256
            if blob_sha is None or blob_sha not in unusable:
                continue
            findings.append(
                RecoveryFinding(
                    problem=PROBLEM_ACQUISITION_SOURCE_QUARANTINED,
                    object_type=StorageObjectType.ACQUISITION_RECORD.value,
                    object_id=record.acquisition_id,
                    detail=(
                        f"acquisition references blob {blob_sha} whose "
                        "physical bytes are missing, corrupt or quarantined; "
                        "history remains immutable and provenance stays "
                        "non-usable"
                    ),
                    before_state={"blob_sha256": blob_sha},
                    proposed_resolution=(
                        "RECORD_ACQUISITION_DEPENDENCY: record the dependency "
                        "and verify the provenance gate still fails closed; "
                        "acquisition history is never rewritten (I08 §17)"
                    ),
                )
            )

    def _scan_manifest_targets(self, findings: list[RecoveryFinding]) -> None:
        """§4-D/§16: manifests referencing missing/corrupt physical blobs.

        Manifest history is immutable: the finding names the manifest, the
        missing/corrupt blob refs and the affected partition; no manifest
        is ever edited in place and no replacement is manufactured here.
        """
        for manifest in self._all_manifests():
            missing: list[str] = []
            for blob_ref in manifest.blob_refs:
                try:
                    verified = self._blob_metadata.has_verified_physical(blob_ref)
                except Exception:
                    verified = False
                if not verified:
                    missing.append(blob_ref)
            if missing:
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_MISSING_MANIFEST_TARGET,
                        object_type=StorageObjectType.PARTITION_MANIFEST.value,
                        object_id=manifest.partition_manifest_id,
                        detail=(
                            f"manifest references {len(missing)} missing or "
                            f"corrupt blob ref(s): {sorted(missing)}"
                        ),
                        before_state={
                            "partition_key": manifest.partition_key,
                            "manifest_version": manifest.manifest_version,
                            "missing_blob_refs": sorted(missing),
                        },
                        proposed_resolution=(
                            "RECORD_MISSING_TARGET: immutable manifest "
                            "history is NOT edited; canonical use fails "
                            "closed; a replacement, if ever justified, is a "
                            "NEW manifest version (I08 §16)"
                        ),
                    )
                )

    def _scan_orphan_manifests(self, findings: list[RecoveryFinding]) -> None:
        """§4-G (I08 §15): published fragments outside the committed chain.

        The repository's own forensic view
        (``list_orphan_manifest_fragments``) is the authority.  Recovery
        never promotes the highest version and never rewrites history.
        """
        partitions_root = self._t0_root / "catalogs" / "manifests" / "partitions"
        if not partitions_root.is_dir():
            return
        for partition_dir in sorted(p for p in partitions_root.iterdir() if p.is_dir()):
            decoded, corruption = self._read_partition_fragments(partition_dir)
            findings.extend(corruption)
            for manifest in decoded:
                try:
                    chain_ids = {
                        m.partition_manifest_id
                        for m in self._manifests.list_manifest_versions(
                            manifest.partition_key
                        )
                    }
                except Exception:
                    chain_ids = set()
                if manifest.partition_manifest_id in chain_ids:
                    continue
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_ORPHAN_MANIFEST,
                        object_type=StorageObjectType.PARTITION_MANIFEST.value,
                        object_id=manifest.partition_manifest_id,
                        detail=(
                            "published manifest fragment v"
                            f"{manifest.manifest_version} for partition "
                            f"{manifest.partition_key!r} is outside the "
                            "committed chain (no 'latest wins' promotion)"
                        ),
                        before_state={
                            "partition_key": manifest.partition_key,
                            "manifest_version": manifest.manifest_version,
                            "supersedes_manifest_id": (
                                manifest.supersedes_manifest_id
                            ),
                            "blob_refs": list(manifest.blob_refs),
                        },
                        proposed_resolution=(
                            "RESOLVE_ORPHAN_MANIFEST: reconcile ONLY when "
                            "partition identity, ancestry and every "
                            "referenced object verify and CAS semantics "
                            "permit; otherwise record an unresolved orphan "
                            "(I08 §15)"
                        ),
                    )
                )

    def _scan_projections(self, findings: list[RecoveryFinding]) -> None:
        """§4-C/H (I08 §14): orphan projection artifacts.

        ``projection_sha256`` is the SHA-256 of the physical Parquet file
        bytes (verified from the implementation), so a physical file
        whose bytes hash to no committed artifact record is
        ORPHAN_PROJECTION.  Lineage is NOT manufactured — reconciliation
        happens only through the canonical repositories when exact
        metadata proves the mapping, else quarantine.
        """
        projections_root = self._t0_root / "projections"
        if not projections_root.is_dir():
            return
        known: set[str] = set()
        if self._artifacts is not None:
            for artifact_id in self._artifacts.list_ids():
                artifact = self._artifacts.get(artifact_id)
                if artifact is not None:
                    known.add(artifact.projection_sha256)
        for path in sorted(projections_root.rglob("*.parquet")):
            if not path.is_file():
                continue
            self._assert_contained(path, self._t0_root, "projection artifact")
            bytes_sha = _sha256_file(path)
            if bytes_sha in known:
                # I08R1 §14 (crash 4): a CATALOGED projection is healthy
                # ONLY when committed manifest truth references it.  A
                # catalog row alone does not prove the projection is
                # canonical — the frozen crash boundary is exactly
                # 'projection cataloged, manifest never wrote it down'.
                if not self._projection_referenced_by_manifests(bytes_sha):
                    findings.append(
                        RecoveryFinding(
                            problem=PROBLEM_ORPHAN_PROJECTION,
                            object_type=StorageObjectType.RAW_PROJECTION.value,
                            object_id=bytes_sha,
                            detail=(
                                "cataloged projection artifact is referenced "
                                "by NO committed manifest truth (I08R1 §14: "
                                "catalog validity is not manifest truth)"
                            ),
                            before_state={
                                "relative_path": path.relative_to(
                                    self._t0_root
                                ).as_posix(),
                                "byte_length": path.stat().st_size,
                                "bytes_sha256": bytes_sha,
                                "cataloged": True,
                            },
                            proposed_resolution=(
                                "RECORD_UNREFERENCED_PROJECTION: reconcile "
                                "ONLY through the canonical manifest APIs "
                                "when exact context proves the mapping; "
                                "otherwise record unresolved; never "
                                "manufacture lineage (I08 §14)"
                            ),
                        )
                    )
                continue
            findings.append(
                RecoveryFinding(
                    problem=PROBLEM_ORPHAN_PROJECTION,
                    object_type=StorageObjectType.RAW_PROJECTION.value,
                    object_id=bytes_sha,
                    detail=(
                        "physical projection artifact has no durable "
                        "projection catalog record; lineage cannot be "
                        "assumed"
                    ),
                    before_state={
                        "relative_path": path.relative_to(
                            self._t0_root
                        ).as_posix(),
                        "byte_length": path.stat().st_size,
                        "bytes_sha256": bytes_sha,
                    },
                    proposed_resolution=(
                        "QUARANTINE under unknown_context: validate bytes + "
                        "T0A source refs; repair ONLY through canonical "
                        "projection/lineage repository APIs when "
                        "reconstruction is unambiguous; never manufacture "
                        "T0A lineage (I08 §14)"
                    ),
                )
            )

    def _projection_referenced_by_manifests(self, bytes_sha: str) -> bool:
        """True iff some COMMITTED manifest references a projection whose
        physical bytes hash to ``bytes_sha`` (I08R1 §14).

        Projection references are BY ID; the id→bytes binding comes from
        the projection catalog itself, so 'referenced' means: a committed
        manifest lists the projection id AND the catalog maps that id to
        these exact physical bytes.
        """
        for manifest in self._all_manifests():
            for projection_id in manifest.projection_refs:
                if self._artifacts is None:
                    return False
                artifact = self._artifacts.get(projection_id)
                if artifact is not None and artifact.projection_sha256 == bytes_sha:
                    return True
        return False

    def _scan_jobs(self, findings: list[RecoveryFinding]) -> None:
        """§4-F (I08 §18): job states ahead of durable evidence.

        Anchored by the accepted I07 chain: the job repository's shared
        per-job chain authority (restart's own validation) is the
        durable-truth oracle, so a divergence is detected by REVALIDATING
        each job's chain — including checkpoint proofs re-proved against
        acquisition/blob/manifest evidence.  No cursor is moved during
        the scan; the safe action is an explicit annotated transition to
        QUARANTINED through the public API, never a mutation of old
        checkpoint events.
        """
        if self._jobs is None:
            return
        for job_id in sorted(self._jobs.list_job_ids()):
            try:
                # PUBLIC gated read (I07R1I): lock -> refresh both catalogs
                # -> _validate_job_chain -> state.  A forged event published
                # after repository construction is INVISIBLE to a bare
                # chain validation over the cached catalog — the refresh is
                # what adopts it — so the scan MUST cross the same gate.
                self._jobs.get_job(job_id)
            except JobError as exc:
                # I08R1 §27: typed JOB-CLASS failures.  Normal active-writer
                # contention (JobLockHeld) is NOT durable corruption; the
                # job is skipped here (lock files are already classified by
                # LOCK_PRESENT_OWNER_UNPROVEN).  Genuine durable-chain/
                # proof failures (JobCatalogCorrupt and the other typed
                # job-state failures) are the corruption signal.
                if isinstance(exc, JobLockHeld):
                    continue
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_JOB_DURABILITY_DIVERGENCE,
                        object_type=StorageObjectType.STORAGE_JOB.value,
                        object_id=job_id,
                        detail=(
                            "job chain no longer re-proves against durable "
                            f"evidence: {type(exc).__name__}"
                        ),
                        before_state={"validation_error": type(exc).__name__},
                        proposed_resolution=(
                            "QUARANTINE_JOB: append an explicit annotated "
                            "transition to QUARANTINED (nonempty recovery "
                            "reason) through the public transition API; never "
                            "mutate old checkpoint events; refuse continued "
                            "use otherwise (I08 §18)"
                        ),
                    )
                )
            # I08R1 §27: any OTHER failure (unexpected I/O, programming
            # errors, unrelated operational faults) propagates typed — it
            # must NEVER be mislabeled as job durability corruption, and a
            # scan that cannot read a job repository is not a healthy scan.

    def _scan_job_locks(self, findings: list[RecoveryFinding]) -> None:
        """§4-I (I08 §20): lock files with unprovable ownership.

        Current lock files carry no trustworthy owner proof, so NO lock
        is ever auto-deleted and none is factually called 'stale'.  Each
        is classified LOCK_PRESENT_OWNER_UNPROVEN; the optional explicit
        operator clear is a separate, separately-journaled API.
        """
        locks_root = self._t0_root / "locks"
        if not locks_root.is_dir():
            return
        for path in sorted(locks_root.glob("*.lock")):
            self._assert_contained(path, self._t0_root, "job lock")
            findings.append(
                RecoveryFinding(
                    problem=PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
                    object_type=SEMANTIC_JOB_LOCK,
                    object_id=path.stem,
                    detail=(
                        "job lock file present; ownership cannot be proven "
                        "from its contents — never auto-deleted (I08 §20)"
                    ),
                    before_state={
                        "relative_path": path.relative_to(
                            self._t0_root
                        ).as_posix(),
                    },
                    proposed_resolution=(
                        "RECORD_LOCK_ONLY: detect/report/record; an explicit "
                        "operator clear requires the expected fingerprint, "
                        "no in-process owner and a RecoveryAction"
                    ),
                )
            )

    # -- deterministic cross-repository read helpers --------------------------
    # Scan needs a GLOBAL view of durable truth; the repositories' public
    # read APIs are keyed lookups (get by id / per-partition lists), so the
    # three helpers below iterate the durable fragment stores read-only and
    # reuse the repositories' OWN row decoders.  They never write; private
    # access is confined to these helpers and documented in the I08 evidence.

    def _all_blob_metadata(self) -> list[Any]:
        """Every durable EvidenceBlob row (sorted for determinism)."""
        from .catalog import BLOB_SCHEMA, _blob_from_row, read_fragment

        metas: list[Any] = []
        blobs_dir = self._t0_root / "catalogs" / "manifests" / "blobs"
        if not blobs_dir.is_dir():
            return metas
        seen: set[tuple[str, str]] = set()
        for path in sorted(blobs_dir.glob("*.parquet")):
            for row in read_fragment(path, BLOB_SCHEMA):
                meta = _blob_from_row(row)
                key = (meta.blob_sha256, meta.storage_encoding.value)
                if key not in seen:
                    seen.add(key)
                    metas.append(meta)
        metas.sort(key=lambda m: (m.blob_sha256, m.storage_encoding.value))
        return metas

    def _all_acquisition_records(self) -> list[Any]:
        """Every durable AcquisitionRecord (sorted for determinism)."""
        from .catalog import (
            ACQUISITION_SCHEMA,
            _acquisition_from_row,
            read_fragment,
        )

        records: list[Any] = []
        acq_dir = self._t0_root / "catalogs" / "manifests" / "acquisitions"
        if not acq_dir.is_dir():
            return records
        seen: set[str] = set()
        for path in sorted(acq_dir.glob("*.parquet")):
            for row in read_fragment(path, ACQUISITION_SCHEMA):
                record = _acquisition_from_row(row)
                if record.acquisition_id not in seen:
                    seen.add(record.acquisition_id)
                    records.append(record)
        records.sort(key=lambda r: r.acquisition_id)
        return records

    def _all_manifests(self) -> list[Any]:
        """Every DECODABLE committed PartitionManifest (sorted).

        Unparseable fragments are not manifests; they are surfaced as
        UNKNOWN_CONTEXT findings by the scan (see
        :meth:`_scan_orphan_manifests`) and the canonical integrity gates
        fail closed on them regardless.
        """
        manifests: list[Any] = []
        partitions_root = self._t0_root / "catalogs" / "manifests" / "partitions"
        if not partitions_root.is_dir():
            return manifests
        for partition_dir in sorted(p for p in partitions_root.iterdir() if p.is_dir()):
            decoded, _findings = self._read_partition_fragments(partition_dir)
            manifests.extend(decoded)
        manifests.sort(
            key=lambda m: (
                m.partition_key,
                m.manifest_version,
                m.partition_manifest_id,
            )
        )
        return manifests

    def _read_partition_fragments(
        self, partition_dir: Path
    ) -> tuple[list[Any], list[RecoveryFinding]]:
        """Decode every ``v*.parquet`` manifest fragment under one dir.

        Uses the manifests module's OWN schema/decoder.  Returns the
        decodable manifests plus UNKNOWN_CONTEXT findings for fragments
        that fail to decode (never silently skipped at scan time); the
        canonical gates fail closed on those fragments either way.
        """
        from .catalog import read_fragment
        from .manifests import MANIFEST_SCHEMA, _manifest_from_row

        manifests: list[Any] = []
        findings: list[RecoveryFinding] = []
        for path in sorted(partition_dir.glob("v*.parquet")):
            try:
                rows = read_fragment(path, MANIFEST_SCHEMA)
            except Exception as exc:
                findings.append(
                    RecoveryFinding(
                        problem=PROBLEM_UNKNOWN_CONTEXT,
                        object_type=StorageObjectType.PARTITION_MANIFEST.value,
                        object_id=path.stem,
                        detail=(
                            "manifest fragment is unparseable: "
                            f"{type(exc).__name__}"
                        ),
                        before_state={
                            "relative_path": path.relative_to(
                                self._t0_root
                            ).as_posix(),
                        },
                        proposed_resolution=(
                            "catalog-integrity corruption; the canonical "
                            "gates fail closed — quarantine/malformed is an "
                            "explicit apply decision only"
                        ),
                    )
                )
                continue
            for row in rows:
                try:
                    manifests.append(_manifest_from_row(row))
                except Exception as exc:
                    findings.append(
                        RecoveryFinding(
                            problem=PROBLEM_UNKNOWN_CONTEXT,
                            object_type=StorageObjectType.PARTITION_MANIFEST.value,
                            object_id=path.stem,
                            detail=(
                                "manifest fragment row does not decode: "
                                f"{type(exc).__name__}"
                            ),
                            before_state={
                                "relative_path": path.relative_to(
                                    self._t0_root
                                ).as_posix(),
                            },
                            proposed_resolution=(
                                "catalog-integrity corruption; the canonical "
                                "gates fail closed — quarantine/malformed is "
                                "an explicit apply decision only"
                            ),
                        )
                    )
        return manifests, findings

    # -- phase 2: APPLY (explicit, I08 §5/§6/§28) ----------------------------

    def apply_plan(
        self,
        result: RecoveryScanResult,
        *,
        recovery_run_id: str | None = None,
    ) -> list[RecoveryAction]:
        """Execute the planned actions of one scan result (I08 §5/§6).

        Every executed action REVALIDATES its target against the scanned
        before-state FIRST (I08 §28); a mismatch raises
        :class:`RecoveryPlanConflict` and that action is not applied.
        Every durable outcome leaves an append-only journal record.
        Detect/report-only findings (locks, manifest targets, acquisition
        dependencies) produce evidence records WITHOUT mutation.
        """
        run_id = recovery_run_id or result.recovery_run_id
        # I08R1 §6/§8: interrupted-but-landed operations adopt FIRST so a
        # restarted apply recognizes its own prior effect instead of
        # re-planning over it (or misreading it as stale).
        self._finalize_open_operations()
        applied: list[RecoveryAction] = []
        for planned in result.planned_actions:
            action = self._apply_one(planned, run_id)
            if action is not None:
                applied.append(action)
        return applied

    def _apply_one(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        handlers: dict[str, Callable[[RecoveryPlanAction, str], RecoveryAction | None]] = {
            _ACTION_QUARANTINE_CORRUPT_BLOB: self._execute_corrupt_blob,
            _ACTION_RESOLVE_ORPHAN_BLOB: self._execute_orphan_blob,
            _ACTION_QUARANTINE_STAGING: self._execute_staging,
            _ACTION_QUARANTINE_ORPHAN_PROJECTION: self._execute_orphan_projection,
            _ACTION_RESOLVE_ORPHAN_MANIFEST: self._execute_orphan_manifest,
            _ACTION_CONTINUE_ORPHAN_BLOB: self._execute_continue_orphan_blob,
            _ACTION_RECORD_UNREFERENCED_PROJECTION: (
                self._execute_unreferenced_projection
            ),
            _ACTION_RECORD_MISSING_TARGET: self._execute_missing_manifest_target,
            _ACTION_RECORD_ACQUISITION_DEPENDENCY: (
                self._execute_acquisition_dependency
            ),
            _ACTION_QUARANTINE_JOB: self._execute_job_divergence,
            _ACTION_RECORD_LOCK_ONLY: self._execute_lock_finding,
            _ACTION_QUARANTINE_UNKNOWN_CONTEXT: self._execute_unknown_context,
        }
        handler = handlers.get(planned.action_kind)
        if handler is None:
            raise RecoveryConfigurationError(
                f"unknown recovery action kind {planned.action_kind!r}"
            )
        # I08 §27 idempotence: within ONE run id, an action already
        # durably journaled for this object+problem is an already-applied
        # outcome — a re-apply never duplicates quarantine movement or
        # appends a divergent record.  Cross-run re-application re-runs
        # the handler (which revalidates under I08 §28).
        prior = self._journal.list_for_object(planned.object_type, planned.object_id)
        if any(
            record.get("recovery_run_id") == run_id
            and record.get("problem") == planned.problem
            and record.get("action_kind") == planned.action_kind
            for record in prior
        ):
            return None
        return handler(planned, run_id)

    def _journal_action(
        self,
        *,
        run_id: str,
        planned: RecoveryPlanAction,
        resolution: str,
        after_state: dict[str, Any] | None,
    ) -> RecoveryAction | None:
        action_id, _adopted = self._journal.record(
            recovery_run_id=run_id,
            object_type=planned.object_type,
            object_id=planned.object_id,
            problem=planned.problem,
            resolution=resolution,
            before_state=planned.before_state,
            after_state=after_state,
            registered_at=self._clock(),
            action_kind=planned.action_kind,
        )
        payload = self._journal.get(action_id)
        assert payload is not None
        return self._journal.to_recovery_action(payload)

    # -- replayable-operation phases (I08R1 §4/§5) ----------------------------

    def _operation_id(self, planned: RecoveryPlanAction, run_id: str) -> str:
        """Deterministic operation id for one planned action (I08R1 §4):
        run + action semantics, no clocks, no process state."""
        return RecoveryOperationJournal.operation_id(
            recovery_run_id=run_id,
            action_kind=planned.action_kind,
            object_type=planned.object_type,
            object_id=planned.object_id,
            problem=planned.problem,
            resolution=planned.resolution,
            before_state=planned.before_state,
            after_state=None,
        )

    def _record_intent(self, planned: RecoveryPlanAction, run_id: str) -> str:
        """Durably record INTENT before the first irreversible effect.

        I08R1 §5: if intent publication fails, the exception escapes
        BEFORE any mutation has been attempted — an effect can never
        outrun its recovery evidence.  Exact retries are idempotent.
        Returns the deterministic operation id."""
        op_id = self._operation_id(planned, run_id)
        self._operations.record_phase(
            recovery_run_id=run_id,
            action_kind=planned.action_kind,
            object_type=planned.object_type,
            object_id=planned.object_id,
            problem=planned.problem,
            resolution=planned.resolution,
            before_state=planned.before_state,
            after_state=None,
            phase=RecoveryOperationJournal.PHASE_INTENT,
            detail="durable intent recorded before the first irreversible "
            "effect (I08R1 §5)",
            registered_at=self._clock(),
        )
        return op_id

    def _record_effect(
        self,
        op_id: str,
        planned: RecoveryPlanAction,
        run_id: str,
        *,
        detail: str,
    ) -> None:
        """Append an EFFECT_COMMITTED phase row after one irreversible
        effect became durable (I08R1 §4: append-only, never in-place)."""
        self._operations.record_phase(
            recovery_run_id=run_id,
            action_kind=planned.action_kind,
            object_type=planned.object_type,
            object_id=planned.object_id,
            problem=planned.problem,
            resolution=planned.resolution,
            before_state=planned.before_state,
            after_state=None,
            phase=RecoveryOperationJournal.PHASE_EFFECT_COMMITTED,
            detail=detail,
            registered_at=self._clock(),
        )

    def _finish_unresolved(
        self,
        op_id: str,
        planned: RecoveryPlanAction,
        run_id: str,
        *,
        refusal_type: str,
        step: str,
    ) -> RecoveryAction | None:
        """Record an UNRESOLVED outcome when a repository API refused a
        reconciliation step; nothing registered, nothing overwritten."""
        resolution = (
            f"UNRESOLVED: the repository APIs refused the {step} "
            f"({refusal_type}); nothing registered, nothing overwritten"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "reconciled": False,
                "refusal": refusal_type,
                "refused_step": step,
            },
        )

    def _record_outcome(
        self,
        op_id: str,
        planned: RecoveryPlanAction,
        run_id: str,
        *,
        resolution: str,
    ) -> None:
        """Append the final COMPLETED/UNRESOLVED phase of one operation."""
        phase = (
            RecoveryOperationJournal.PHASE_UNRESOLVED
            if resolution.startswith("UNRESOLVED")
            else RecoveryOperationJournal.PHASE_COMPLETED
        )
        self._operations.record_phase(
            recovery_run_id=run_id,
            action_kind=planned.action_kind,
            object_type=planned.object_type,
            object_id=planned.object_id,
            problem=planned.problem,
            resolution=planned.resolution,
            before_state=planned.before_state,
            after_state=None,
            phase=phase,
            detail=resolution,
            registered_at=self._clock(),
        )

    def _execute_corrupt_blob(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §11: integrity quarantine for corrupt physical bytes.

        Revalidates that the object STILL fails verification (I08 §28);
        moves the corrupt bytes into ``quarantine/integrity/`` with a
        deterministic no-clobber locator (bytes preserved); the canonical
        location becomes unusable (bytes gone — every existing gate fails
        closed) and an explicit QUARANTINED_INTEGRITY_FAILURE metadata
        row is ATTEMPTED through the public ``append_metadata`` API, whose
        physical gate is expected to refuse it (recorded, never forced).
        Acquisition/manifest history is preserved untouched.
        """
        from .enums import IntegrityState

        sha_part = planned.object_id
        encoding_value = planned.before_state.get(
            "storage_encoding", "NONE"
        )
        encoding = StorageEncodingValue(encoding_value)
        # TOCTOU revalidation (I08 §28): still absent / still corrupt?
        try:
            check = self._blob_store.verify_blob(sha_part, encoding)
            state = check.integrity_state
        except BlobMissing:
            state = None
        except Exception:
            state = IntegrityState.QUARANTINED_INTEGRITY_FAILURE
        if state is IntegrityState.LOCAL_HASH_VERIFIED or state is not None and state.value in (
            "PROVIDER_HASH_VERIFIED",
        ):
            raise RecoveryPlanConflict(
                f"blob {sha_part} now verifies; the scanned CORRUPT_BLOB "
                "plan is stale (I08 §28)"
            )
        object_path = self._blob_object_path(sha_part, encoding)
        if not object_path.exists():
            # Already-quarantined (prior recovery) or independently
            # vanished: seal once, never duplicate evidence.
            prior = self._journal.list_for_object(
                StorageObjectType.EVIDENCE_BLOB.value, sha_part
            )
            if prior:
                # I08R1 §6: an interrupted operation whose effect already
                # exists converges to a COMPLETED operation on retry.
                self._record_outcome(
                    self._operation_id(planned, run_id),
                    planned,
                    run_id,
                    resolution=(
                        "COMPLETED: canonical object already absent under a "
                        "prior durable recovery record; nothing duplicated"
                    ),
                )
                return None
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "MISSING physical bytes: recovery evidence recorded; "
                    "canonical reads fail closed through the existing "
                    "integrity gates; no bytes invented"
                ),
                after_state={"physical_present": False},
            )
        self._assert_contained(object_path, self._t0_root, "canonical blob")
        content_sha = _sha256_file(object_path)
        destination = self.quarantine_destination(
            QUARANTINE_CATEGORY_INTEGRITY,
            object_type="blob",
            object_id=planned.object_id,
            content_sha256=content_sha,
            suffix=".quarantined",
        )
        # I08R1 §5: durable INTENT precedes the irreversible move.
        op_id = self._record_intent(planned, run_id)
        moved = self._quarantine_file(object_path, destination, content_sha)
        # After _quarantine_file returns, the effect IS durable in BOTH
        # branches: freshly moved, or an identical artifact adopted and
        # the canonical source unlinked (I08R1 §6 exact-retry convergence).
        # Either way the commit is recorded as its own append-only phase.
        self._record_effect(
            op_id,
            planned,
            run_id,
            detail=(
                "canonical corrupt bytes moved to quarantine/integrity"
                if moved
                else "identical quarantine artifact adopted; canonical "
                "source unlinked (exact retry)"
            ),
        )
        # Canonical location now unusable; try to append the explicit
        # quarantine metadata row through the PUBLIC API.  The physical
        # gate is EXPECTED to refuse (bytes are gone); the attempt is
        # recorded, never forced (no hand-written fragments).
        try:
            from .models import EvidenceBlob

            self._blob_metadata.append_metadata(
                EvidenceBlob(
                    blob_sha256=sha_part,
                    byte_length=planned.before_state.get("byte_length", 0),
                    stored_byte_length=planned.before_state.get(
                        "stored_byte_length", 0
                    ),
                    source_media_type=planned.before_state.get(
                        "source_media_type", "application/octet-stream"
                    ),
                    storage_encoding=encoding,
                    storage_uri=str(_blob_object_key(sha_part, encoding)),
                    integrity_state=IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
                    created_at=self._clock(),
                )
            )
            metadata_gate = "QUARANTINED_INTEGRITY_FAILURE row appended"
        except Exception as exc:
            metadata_gate = (
                f"existing gates hold (typed: {type(exc).__name__}); "
                "canonical use fails closed"
            )
        resolution = (
            "QUARANTINE_INTEGRITY: corrupt bytes preserved under "
            f"quarantine/integrity ({'moved' if moved else 'adopted'}); "
            "canonical object NOT overwritten; acquisition/manifest "
            "history preserved"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "quarantined": moved,
                "quarantine_category": QUARANTINE_CATEGORY_INTEGRITY,
                "quarantine_bytes_sha256": content_sha,
                "canonical_state": "ABSENT_QUARANTINED",
                "metadata_gate": metadata_gate,
            },
        )

    def _execute_orphan_blob(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §12 + I08R1 §7: reconcile an ORPHAN_DURABLE_BLOB only with
        proven context — as a REPLAYABLE multi-step operation.

        Preflight (before any mutation): the physical bytes verify against
        their content-addressed name and the registered context identities
        match the orphan.  Then: durable INTENT; step 1 append/adopt the
        exact EvidenceBlob metadata (phase recorded); step 2 append/adopt
        the exact AcquisitionRecord (phase recorded); COMPLETED outcome.
        A crash after step 1 leaves the retry able to RECOGNIZE the exact
        matching metadata and continue with step 2 — an already-committed
        step is never misread as a stale plan, and divergent durable state
        raises a typed conflict.  Without proven context the blob is
        quarantined as unknown_context — provenance is NEVER manufactured.
        """
        sha_part = planned.object_id
        encoding_value = planned.before_state.get(
            "storage_encoding", "NONE"
        )
        encoding = StorageEncodingValue(encoding_value)
        object_path = self._blob_object_path(sha_part, encoding)
        if not object_path.exists():
            raise RecoveryPlanConflict(
                f"orphan blob {sha_part} vanished; the scanned plan is "
                "stale (I08 §28)"
            )
        content_sha = _sha256_file(object_path)
        context = self._orphan_context.get(sha_part)
        # -- preflight (I08R1 §7): identity + semantics BEFORE mutation -----
        if context is not None and content_sha == sha_part:
            evidence_blob, acquisition = context
            if evidence_blob.blob_sha256 != sha_part:
                raise RecoveryPlanConflict(
                    "registered context evidence_blob identity does not "
                    f"match the orphan {sha_part} (I08R1 §7 preflight)"
                )
            if acquisition.blob_sha256 != sha_part:
                raise RecoveryPlanConflict(
                    "registered context acquisition blob_sha256 does not "
                    f"match the orphan {sha_part} (I08R1 §7 preflight)"
                )
            # Durable INTENT precedes the first irreversible effect.
            op_id = self._record_intent(planned, run_id)
            # -- step 1: append/adopt the EXACT EvidenceBlob metadata -------
            existing_metas: tuple[Any, ...] = ()
            try:
                existing_metas = tuple(
                    self._blob_metadata.get_blob_metadata(sha_part)
                )
            except Exception:
                existing_metas = ()
            if existing_metas:
                if not any(
                    meta.model_dump() == evidence_blob.model_dump()
                    for meta in existing_metas
                ):
                    raise RecoveryPlanConflict(
                        f"blob {sha_part} already carries DIVERGENT durable "
                        "metadata; the reconciliation plan conflicts "
                        "(I08R1 §7)"
                    )
                # Exact matching metadata already durable (crash after
                # step 1): ADOPT and continue — never "stale", never a
                # duplicate append.
            else:
                try:
                    self._blob_metadata.append_metadata(evidence_blob)
                except Exception as exc:
                    return self._finish_unresolved(
                        op_id, planned, run_id,
                        refusal_type=type(exc).__name__,
                        step="metadata append",
                    )
                self._record_effect(
                    op_id, planned, run_id,
                    detail="EvidenceBlob metadata appended for orphan",
                )
            # -- step 2: append/adopt the EXACT AcquisitionRecord -----------
            try:
                existing_acq = self._acquisitions.get_acquisition(
                    acquisition.acquisition_id
                )
            except Exception:
                existing_acq = None
            if existing_acq is not None:
                if existing_acq.model_dump() != acquisition.model_dump():
                    raise RecoveryPlanConflict(
                        "acquisition "
                        f"{acquisition.acquisition_id} already exists with "
                        "DIVERGENT content; the reconciliation plan "
                        "conflicts (I08R1 §7)"
                    )
            else:
                try:
                    self._acquisitions.append_acquisition(acquisition)
                except Exception as exc:
                    return self._finish_unresolved(
                        op_id, planned, run_id,
                        refusal_type=type(exc).__name__,
                        step="acquisition append",
                    )
                self._record_effect(
                    op_id, planned, run_id,
                    detail="AcquisitionRecord appended for orphan",
                )
            resolution = (
                "RECONCILED through existing public repository APIs with "
                "durable context proven and bytes verified (I08 §12); "
                "replayable multi-step operation (I08R1 §7)"
            )
            self._record_outcome(op_id, planned, run_id, resolution=resolution)
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=resolution,
                after_state={
                    "reconciled": True,
                    "acquisition_id": getattr(
                        acquisition, "acquisition_id", None
                    ),
                },
            )
        # No proven context (or durable metadata appeared making the orphan
        # premise stale).  Bytes that contradict their content-addressed
        # name are corrupt (integrity) regardless of registered context.
        try:
            self._blob_metadata.get_blob_metadata(sha_part)
            has_metadata = True
        except Exception:
            has_metadata = False
        if has_metadata and content_sha == sha_part:
            raise RecoveryPlanConflict(
                f"blob {sha_part} now has durable metadata; the scanned "
                "ORPHAN_DURABLE_BLOB plan is stale (I08 §28)"
            )
        category = (
            QUARANTINE_CATEGORY_INTEGRITY
            if content_sha != sha_part
            else QUARANTINE_CATEGORY_UNKNOWN_CONTEXT
        )
        destination = self.quarantine_destination(
            category,
            object_type="blob",
            object_id=planned.object_id,
            content_sha256=content_sha,
            suffix=".quarantined",
        )
        op_id = self._record_intent(planned, run_id)
        moved = self._quarantine_file(object_path, destination, content_sha)
        if moved:
            self._record_effect(
                op_id,
                planned,
                run_id,
                detail=f"orphan bytes moved to quarantine/{category}",
            )
        resolution = (
            "QUARANTINE: no durable context proves the request identity; "
            "provenance is never manufactured (I08 §12)"
            if category == QUARANTINE_CATEGORY_UNKNOWN_CONTEXT
            else "QUARANTINE_INTEGRITY: orphan bytes fail their "
            "content-addressed name; treated as corrupt, never repaired"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "quarantined": moved,
                "quarantine_category": category,
                "quarantine_bytes_sha256": content_sha,
            },
        )

    def _execute_continue_orphan_blob(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08R1 §12 (crash 2b): CONTINUE the interrupted orphan-blob
        reconciliation.

        Metadata is already durable; the missing step is the acquisition.
        Preflight (§7): the physical bytes verify against their
        content-addressed name; the operator-supplied context acquisition
        matches the orphan identity.  Metadata is NEVER duplicated and
        provenance is NEVER guessed — without EXPLICIT registered context
        the record stays unresolved and the decision goes back to the
        operator.  A crash after the acquisition append converges: retry
        recognizes the durable acquisition (exact match) and adopts.
        """
        sha_part = planned.object_id
        encoding_value = (planned.before_state or {}).get(
            "storage_encoding", "NONE"
        )
        try:
            encoding = StorageEncodingValue(encoding_value)
        except ValueError as exc:
            raise RecoveryPlanConflict(
                f"orphan continuation for {sha_part} carries an unknown "
                "storage encoding; the scanned plan is unusable (I08 §28)"
            ) from exc
        object_path = self._blob_object_path(sha_part, encoding)
        if not object_path.exists():
            raise RecoveryPlanConflict(
                f"orphan continuation target {sha_part} vanished; the "
                "scanned plan is stale (I08 §28)"
            )
        content_sha = _sha256_file(object_path)
        if content_sha != sha_part:
            raise RecoveryPlanConflict(
                f"orphan continuation target {sha_part} fails its content "
                "identity; the scanned plan is stale (I08 §28)"
            )
        context = self._orphan_context.get(sha_part)
        if context is None:
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "UNRESOLVED recorded: durable metadata has no usable "
                    "acquisition, but NO explicit context is registered; "
                    "provenance is never guessed (I08 §12/§18)"
                ),
                after_state={
                    "continued": False,
                    "unresolved_orphan": True,
                    "metadata_durable": True,
                    "acquisition_durable": False,
                },
            )
        _evidence_blob, acquisition = context
        if acquisition.blob_sha256 != sha_part:
            raise RecoveryPlanConflict(
                "registered context acquisition blob_sha256 does not match "
                f"the orphan {sha_part} (I08R1 §7 preflight)"
            )
        # Durable INTENT precedes the irreversible append (I08R1 §5).
        op_id = self._record_intent(planned, run_id)
        # CONTINUE with the acquisition step (metadata already committed).
        try:
            existing_acq = self._acquisitions.get_acquisition(
                acquisition.acquisition_id
            )
        except Exception:
            existing_acq = None
        if existing_acq is not None:
            if existing_acq.model_dump() != acquisition.model_dump():
                raise RecoveryPlanConflict(
                    "acquisition "
                    f"{acquisition.acquisition_id} already exists with "
                    "DIVERGENT content; the continuation plan conflicts "
                    "(I08R1 §7)"
                )
        else:
            try:
                self._acquisitions.append_acquisition(acquisition)
            except Exception as exc:
                return self._finish_unresolved(
                    op_id, planned, run_id,
                    refusal_type=type(exc).__name__,
                    step="acquisition append",
                )
            self._record_effect(
                op_id,
                planned,
                run_id,
                detail="AcquisitionRecord appended for mid-reconciliation orphan",
            )
        resolution = (
            "RECONCILED: mid-reconciliation continuation completed through "
            "the public acquisition API with durable metadata ADOPTED "
            "(never duplicated) and explicit proven context (I08R1 §12)"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "continued": True,
                "reconciled": True,
                "acquisition_id": getattr(acquisition, "acquisition_id", None),
            },
        )

    def _execute_unreferenced_projection(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08R1 §14 (crash 4): a CATALOGED projection referenced by no
        committed manifest — evidence record ONLY.

        A catalog row is durable identity, not garbage: the artifact is
        NEVER moved or deleted here.  Reconciliation through the manifest
        APIs is an explicit operator decision with exact context; until
        then the projection stays cataloged-but-unreferenced and the
        record keeps the seam visible.  Revalidation (I08 §28): the
        projection must still be cataloged and still unreferenced.
        """
        bytes_sha = planned.object_id
        if self._artifacts is None:
            raise RecoveryPlanConflict(
                "unreferenced-projection plan without a projection "
                "catalog; the scanned plan is unusable (I08 §28)"
            )
        if self._find_projection_file(bytes_sha) is None:
            raise RecoveryPlanConflict(
                f"cataloged projection {bytes_sha} has no physical "
                "artifact; the scanned plan is stale (I08 §28)"
            )
        cataloged = any(
            artifact is not None and artifact.projection_sha256 == bytes_sha
            for artifact in (
                self._artifacts.get(aid)
                for aid in self._artifacts.list_ids()
            )
        )
        if not cataloged:
            raise RecoveryPlanConflict(
                f"projection {bytes_sha} is no longer cataloged; the "
                "scanned plan is stale (I08 §28)"
            )
        if self._projection_referenced_by_manifests(bytes_sha):
            raise RecoveryPlanConflict(
                f"projection {bytes_sha} is now referenced by committed "
                "manifest truth; the scanned plan is stale (I08 §28)"
            )
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "RECOVERY EVIDENCE recorded: cataloged projection is "
                "referenced by NO committed manifest; reconciliation is an "
                "explicit operator decision through the canonical manifest "
                "APIs — nothing moved, lineage never manufactured (I08 §14)"
            ),
            after_state={
                "cataloged": True,
                "manifest_referenced": False,
                "recorded": True,
            },
        )

    def _execute_orphan_projection(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §14: orphan projection artifacts.

        Revalidation: the physical file must still exist and still lack a
        durable catalog record.  Lineage is never manufactured; the
        artifact is quarantined as unknown_context (inspectable, never
        canonical T0B evidence).
        """
        bytes_sha = planned.object_id
        physical = self._find_projection_file(bytes_sha)
        if physical is None:
            raise RecoveryPlanConflict(
                "orphan projection artifact vanished; the scanned plan is "
                "stale (I08 §28)"
            )
        if self._artifacts is not None:
            for artifact_id in self._artifacts.list_ids():
                artifact = self._artifacts.get(artifact_id)
                if (
                    artifact is not None
                    and artifact.projection_sha256 == bytes_sha
                ):
                    raise RecoveryPlanConflict(
                        "projection now has a durable catalog record; the "
                        "scanned plan is stale (I08 §28)"
                    )
        content_sha = _sha256_file(physical)
        destination = self.quarantine_destination(
            QUARANTINE_CATEGORY_UNKNOWN_CONTEXT,
            object_type="projection",
            object_id=planned.object_id,
            content_sha256=content_sha,
            suffix=".parquet.quarantined",
        )
        op_id = self._record_intent(planned, run_id)
        moved = self._quarantine_file(physical, destination, content_sha)
        if moved:
            self._record_effect(
                op_id,
                planned,
                run_id,
                detail="orphan projection artifact moved to quarantine/unknown_context",
            )
        resolution = (
            "QUARANTINE under unknown_context: no durable projection "
            "catalog record proves the artifact's identity; T0A lineage "
            "is never manufactured (I08 §14)"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "quarantined": moved,
                "quarantine_category": QUARANTINE_CATEGORY_UNKNOWN_CONTEXT,
                "quarantine_bytes_sha256": content_sha,
            },
        )

    def _execute_orphan_manifest(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §15: orphan manifest fragments — reconcile or record.

        Revalidation: the fragment must still exist outside the committed
        chain (I08 §28).  Reconciliation through the PUBLIC
        ``append_partition_manifest`` API happens ONLY when the ancestry
        is unambiguous (supersedes is in the chain or None) and every
        blob ref verifies; otherwise the UNRESOLVED orphan is recorded
        and no 'latest wins' promotion ever happens.
        """
        manifest_id = planned.object_id
        manifest = self._manifest_by_id(manifest_id)
        if manifest is None:
            raise RecoveryPlanConflict(
                f"orphan manifest {manifest_id} vanished; the scanned plan "
                "is stale (I08 §28)"
            )
        try:
            chain = self._manifests.list_manifest_versions(manifest.partition_key)
        except Exception as exc:
            raise RecoveryPlanConflict(
                f"manifest chain for {manifest.partition_key!r} unreadable: "
                f"{type(exc).__name__}"
            ) from exc
        chain_ids = {m.partition_manifest_id for m in chain}
        if manifest.partition_manifest_id in chain_ids:
            # I08R1 §8: a crash after append_partition_manifest succeeded
            # but before the final recovery record is NOT a stale plan —
            # the exact intended manifest is now committed-chain truth;
            # finalize/adopt the recovery outcome instead of conflicting.
            op_id = self._operation_id(planned, run_id)
            resolution = (
                "COMPLETED: manifest already joined the committed chain "
                "under this exact recovery operation; outcome adopted "
                "(I08R1 §8)"
            )
            self._record_outcome(op_id, planned, run_id, resolution=resolution)
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=resolution,
                after_state={"reconciled_into_chain": True, "adopted": True},
            )
        supersedes = manifest.supersedes_manifest_id
        ancestry_ok = supersedes is None or supersedes in chain_ids
        refs_ok = all(
            self._blob_ref_verified(ref) for ref in manifest.blob_refs
        )
        if not (ancestry_ok and refs_ok):
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "UNRESOLVED ORPHAN recorded: ancestry/references do not "
                    "verify; no 'latest wins' promotion (I08 §15)"
                ),
                after_state={
                    "unresolved_orphan": True,
                    "ancestry_ok": ancestry_ok,
                    "refs_ok": refs_ok,
                },
            )
        # I08R1 §5: durable INTENT precedes the irreversible chain append.
        op_id = self._record_intent(planned, run_id)
        # CAS attestation through the PUBLIC pointer read (I08 §15: the
        # action is taken only when CAS semantics permit).  A concurrent
        # writer that moves the pointer first still loses here — the
        # repository's own ManifestCASConflict refuses, and the refusal is
        # recorded, never overridden.
        try:
            pointer = self._manifests.read_current_pointer(manifest.partition_key)
        except Exception as exc:
            resolution = (
                "UNRESOLVED ORPHAN recorded: current pointer unreadable "
                f"({type(exc).__name__}); no override (I08 §15)"
            )
            self._record_outcome(op_id, planned, run_id, resolution=resolution)
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=resolution,
                after_state={"unresolved_orphan": True},
            )
        expected_current = (
            None
            if pointer is None
            else (pointer.partition_manifest_id, pointer.manifest_version)
        )
        try:
            self._manifests.append_partition_manifest(
                manifest, expected_current
            )
        except Exception as exc:
            resolution = (
                "UNRESOLVED ORPHAN recorded: the manifest repository "
                f"refused reconciliation ({type(exc).__name__}); no "
                "override of CAS/ancestry semantics"
            )
            self._record_outcome(op_id, planned, run_id, resolution=resolution)
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=resolution,
                after_state={
                    "unresolved_orphan": True,
                    "conflict": type(exc).__name__,
                },
            )
        self._record_effect(
            op_id,
            planned,
            run_id,
            detail="orphan manifest reconciled through the public CAS append API",
        )
        resolution = (
            "RECONCILED through the existing manifest repository API "
            "with exact ancestry and verified references (I08 §15)"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={"reconciled_into_chain": True},
        )

    def _execute_missing_manifest_target(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §16: missing/corrupt manifest blob refs — evidence only.

        Immutable manifest history is never edited.  The record names the
        manifest, the missing refs and the affected partition; canonical
        use keeps failing closed through the existing gates.
        """
        manifest_id = planned.object_id
        manifest = self._manifest_by_id(manifest_id)
        if manifest is None:
            raise RecoveryPlanConflict(
                f"manifest {manifest_id} vanished; the scanned plan is "
                "stale (I08 §28)"
            )
        missing = [
            ref
            for ref in manifest.blob_refs
            if not self._blob_ref_verified(ref)
        ]
        if not missing:
            raise RecoveryPlanConflict(
                f"manifest {manifest_id} references all verify now; the "
                "scanned MISSING_MANIFEST_TARGET plan is stale (I08 §28)"
            )
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "RECOVERY EVIDENCE recorded; immutable manifest history NOT "
                "edited; canonical use fails closed (I08 §16)"
            ),
            after_state={"missing_blob_refs": sorted(missing)},
        )

    def _execute_acquisition_dependency(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §17: acquisitions referencing quarantined/missing blobs.

        Immutable forensic truth is never rewritten; the record captures
        the dependency and VERIFIES the existing provenance gate still
        fails closed for the affected acquisition.
        """
        acquisition_id = planned.object_id
        try:
            record = self._acquisitions.get_acquisition(acquisition_id)
        except Exception as exc:
            raise RecoveryPlanConflict(
                f"acquisition {acquisition_id} no longer readable "
                f"({type(exc).__name__}); the scanned plan is stale "
                "(I08 §28)"
            ) from exc
        # I08 §17: the gate that fails closed for an unusable source blob is
        # the physical-verification gate (no verified representation exists).
        # Re-verify it NOW (TOCTOU): if the blob verifies again, the plan is
        # stale.  Acquisition history itself is never rewritten.
        if self._blob_ref_verified(record.blob_sha256 or ""):
            raise RecoveryPlanConflict(
                f"acquisition {acquisition_id} source blob verifies now; "
                "the scanned plan is stale (I08 §28)"
            )
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "RECOVERY EVIDENCE recorded; acquisition history NOT "
                "rewritten; physical-verification gate re-verified "
                "fail-closed (I08 §17)"
            ),
            after_state={
                "provenance_gate": "physical verification fails closed",
                "blob_sha256": record.blob_sha256,
            },
        )

    def _execute_job_divergence(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §18/§19: jobs ahead of durable evidence.

        Revalidation: the chain must STILL fail validation.  The safe
        action is an explicit annotated transition to QUARANTINED through
        the public ``advance_status`` API (nonempty recovery reason; the
        frozen graph permits the edge); old checkpoint events are never
        mutated.  If the transition is refused, the unresolved record is
        kept and the job stays blocked.
        """
        from .enums import StorageJobStatus

        job_id = planned.object_id
        try:
            # PUBLIC gated read: refreshes the catalogs FIRST (I07R1I), so
            # the revalidation sees current durable truth, not the scan-time
            # cache.  Any typed failure means the chain is still divergent.
            self._jobs.get_job(job_id)
            still_divergent = False
        except Exception:
            still_divergent = True
        if not still_divergent:
            raise RecoveryPlanConflict(
                f"job {job_id} chain now validates; the scanned "
                "JOB_DURABILITY_DIVERGENCE plan is stale (I08 §28)"
            )
        # I08R1 §5: durable INTENT precedes the irreversible transition.
        op_id = self._record_intent(planned, run_id)
        reason = (
            "I08 recovery: job chain failed durable revalidation "
            f"({planned.detail[:160]})"
        )
        try:
            state = self._jobs.advance_status(
                job_id,
                to_status=StorageJobStatus.QUARANTINED,
                reason=reason,
            )
            after: dict[str, Any] = {"status": state.status.value}
            resolution = (
                "JOB QUARANTINED through the public transition API with a "
                "nonempty recovery reason; old checkpoint events untouched "
                "(I08 §18)"
            )
        except Exception as exc:
            after = {"transition_refused": True, "refusal": type(exc).__name__}
            resolution = (
                "UNRESOLVED recorded: the frozen transition graph refused "
                "the QUARANTINED edge; the job remains blocked (I08 §18)"
            )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state=after,
        )

    def _execute_lock_finding(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §20: unproven job locks — detect/report/record ONLY.

        No automatic deletion, no TTL, and no 'stale' factual claim.  An
        explicit operator clear is a SEPARATE API
        (:meth:`clear_job_lock`) requiring the expected fingerprint and a
        journaled RecoveryAction — never part of apply_plan.
        """
        lock_id = planned.object_id
        lock_path = self._t0_root / "locks" / f"{lock_id}.lock"
        if not lock_path.exists():
            raise RecoveryPlanConflict(
                f"lock {lock_id} no longer present; the scanned plan is "
                "stale (I08 §28)"
            )
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "LOCK_PRESENT_OWNER_UNPROVEN recorded; ownership unprovable "
                "from contents; nothing deleted (I08 §20)"
            ),
            after_state={"lock_present": True, "cleared": False},
        )

    def _execute_staging(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """I08 §13: stale staging artifacts.

        Revalidation: the .partial file must still exist WITH THE SAME
        BYTES.  The staged bytes are preserved under
        ``quarantine/malformed/`` (a .partial is never evidence); resume
        is never advanced from staging.
        """
        relative_path = planned.before_state.get("relative_path")
        if not isinstance(relative_path, str):
            raise RecoveryPlanConflict("staging plan carries no source path")
        source = self._t0_root / relative_path
        if not source.exists():
            raise RecoveryPlanConflict(
                f"staging artifact {relative_path} vanished; the scanned "
                "plan is stale (I08 §28)"
            )
        content_sha = _sha256_file(source)
        if content_sha != planned.before_state.get("bytes_sha256"):
            raise RecoveryPlanConflict(
                f"staging artifact {relative_path} changed since the scan; "
                "the scanned plan is stale (I08 §28)"
            )
        destination = self.quarantine_destination(
            QUARANTINE_CATEGORY_MALFORMED,
            object_type="staging",
            object_id=relative_path,
            content_sha256=content_sha,
            suffix=".partial.quarantined",
        )
        op_id = self._record_intent(planned, run_id)
        moved = self._quarantine_file(source, destination, content_sha)
        if moved:
            self._record_effect(
                op_id,
                planned,
                run_id,
                detail="staging artifact moved to quarantine/malformed",
            )
        resolution = (
            "STAGING QUARANTINED (bytes preserved): a .partial file is "
            "never evidence; resume was never advanced from staging "
            "(I08 §13)"
        )
        self._record_outcome(op_id, planned, run_id, resolution=resolution)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=resolution,
            after_state={
                "quarantined": moved,
                "quarantine_category": QUARANTINE_CATEGORY_MALFORMED,
                "quarantine_bytes_sha256": content_sha,
            },
        )

    def _execute_unknown_context(
        self, planned: RecoveryPlanAction, run_id: str
    ) -> RecoveryAction | None:
        """Generic unknown-context record for unparseable catalog rows.

        The canonical integrity gates already fail closed on these;
        recovery records the evidence without touching the fragment.
        """
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "UNKNOWN_CONTEXT recorded: unparseable durable fragment; "
                "canonical gates fail closed; no fragment rewritten"
            ),
            after_state={"recorded": True},
        )

    def clear_job_lock(
        self,
        lock_id: str,
        *,
        expected_job_id: str,
        owner_repository: Any,
        run_id: str,
    ) -> RecoveryAction | None:
        """EXPLICIT operator-driven lock clear (I08 §20 + I08R1 §23/§24).

        The owner repository is MANDATORY (I08R1 §23: no optional bypass):
        deletion is authorized only when the expected job id hashes exactly
        to the lock fingerprint, the lock file exists, the job repository
        is supplied, the expected job is NOT present in the repository's
        ``_lock_owners`` truth, and the job's local RLock can be probed
        safely.  The RLock probe alone is NOT sufficient (the owning
        thread can always re-acquire an RLock) — the owner-map check is
        load-bearing.  The RecoveryAction is journaled BEFORE removal
        (evidence precedes mutation); any refusal leaves the lock exactly
        as it was.  Never invoked by apply_plan.
        """
        if owner_repository is None:
            raise RecoveryConfigurationError(
                "explicit lock clear REQUIRES an owner repository with "
                "live ownership truth; no optional bypass exists (I08R1 §23)"
            )
        if not isinstance(expected_job_id, str) or not expected_job_id:
            raise RecoveryConfigurationError(
                "explicit lock clear requires the expected job id (I08 §20)"
            )
        digest = hashlib.sha256(expected_job_id.encode("utf-8")).hexdigest()
        if digest != lock_id:
            raise RecoveryConfigurationError(
                "expected job id does not hash to the lock fingerprint; "
                "refusing the clear (I08 §20)"
            )
        lock_path = self._t0_root / "locks" / f"{lock_id}.lock"
        if not lock_path.exists():
            raise RecoveryPlanConflict(
                f"lock {lock_id} is not present; nothing to clear"
            )
        owners = getattr(owner_repository, "_lock_owners", None)
        if owners is None:
            raise RecoveryConfigurationError(
                "owner repository exposes no _lock_owners truth; refusing "
                "the clear (I08R1 §24)"
            )
        if expected_job_id in owners:
            raise RecoveryPlanConflict(
                f"job {expected_job_id!r} has a LIVE in-process owner "
                "record; refusing the clear (I08R1 §24)"
            )
        lock_obj = owner_repository._job_locks.get(expected_job_id)
        if lock_obj is not None:
            if not lock_obj.acquire(blocking=False):
                raise RecoveryPlanConflict(
                    "the job RLock is currently held; refusing the clear "
                    "(I08R1 §24)"
                )
            lock_obj.release()
        action_id, _adopted = self._journal.record(
            recovery_run_id=run_id,
            object_type=SEMANTIC_JOB_LOCK,
            object_id=lock_id,
            problem=PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
            resolution=(
                "EXPLICIT OPERATOR CLEAR: expected job fingerprint supplied, "
                "no in-process owner (probed), RecoveryAction written before "
                "removal (I08 §20)"
            ),
            before_state={"relative_path": f"locks/{lock_id}.lock"},
            after_state={"lock_present": False, "cleared": True},
            registered_at=self._clock(),
        )
        # I08R1 §5: the clear operation carries durable INTENT before the
        # irreversible unlink (the RecoveryAction above is the effect
        # record; the INTENT phase makes the operation replayable).
        clear_planned = RecoveryPlanAction(
            action_kind="OPERATOR_CLEAR_JOB_LOCK",
            object_type=SEMANTIC_JOB_LOCK,
            object_id=lock_id,
            problem=PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
            resolution="explicit operator clear with proven-absent ownership",
            before_state={"relative_path": f"locks/{lock_id}.lock"},
        )
        self._record_intent(clear_planned, run_id)
        lock_path.unlink()
        fsync_directory(lock_path.parent)
        payload = self._journal.get(action_id)
        assert payload is not None
        return self._journal.to_recovery_action(payload)

    # -- plan mapping ---------------------------------------------------------

    def _plan_action_for(self, finding: RecoveryFinding) -> RecoveryPlanAction | None:
        """Map one finding to its safe planned action (I08 §5/§26).

        Every finding gets a planned action: either an evidence-first
        quarantine move or an explicit record-only action.  Nothing here
        executes anything.  Unknown-context findings produced while
        READING catalogs (unparseable fragments) record evidence only.
        """
        if finding.problem == PROBLEM_CORRUPT_BLOB:
            kind = (
                _ACTION_QUARANTINE_CORRUPT_BLOB
                if finding.before_state.get("physical_present")
                else _ACTION_QUARANTINE_CORRUPT_BLOB
            )
        elif finding.problem == PROBLEM_ORPHAN_DURABLE_BLOB:
            kind = _ACTION_RESOLVE_ORPHAN_BLOB
        elif finding.problem == PROBLEM_UNCOMMITTED_STAGING:
            kind = _ACTION_QUARANTINE_STAGING
        elif finding.problem == PROBLEM_ORPHAN_PROJECTION:
            kind = (
                _ACTION_RECORD_UNREFERENCED_PROJECTION
                if finding.before_state.get("cataloged")
                else _ACTION_QUARANTINE_ORPHAN_PROJECTION
            )
        elif finding.problem == PROBLEM_ORPHAN_MANIFEST:
            kind = _ACTION_RESOLVE_ORPHAN_MANIFEST
        elif finding.problem == PROBLEM_MISSING_MANIFEST_TARGET:
            kind = _ACTION_RECORD_MISSING_TARGET
        elif finding.problem == PROBLEM_ACQUISITION_SOURCE_QUARANTINED:
            kind = _ACTION_RECORD_ACQUISITION_DEPENDENCY
        elif finding.problem == PROBLEM_JOB_DURABILITY_DIVERGENCE:
            kind = _ACTION_QUARANTINE_JOB
        elif finding.problem == PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN:
            kind = _ACTION_RECORD_LOCK_ONLY
        elif finding.problem == PROBLEM_ORPHAN_BLOB_CONTINUATION:
            kind = _ACTION_CONTINUE_ORPHAN_BLOB
        elif finding.problem == PROBLEM_UNKNOWN_CONTEXT:
            kind = (
                _ACTION_QUARANTINE_ORPHAN_PROJECTION
                if finding.object_type == StorageObjectType.RAW_PROJECTION.value
                else _ACTION_QUARANTINE_UNKNOWN_CONTEXT
            )
        else:  # pragma: no cover - closed vocabulary
            return None
        return RecoveryPlanAction(
            action_kind=kind,
            object_type=finding.object_type,
            object_id=finding.object_id,
            problem=finding.problem,
            resolution=finding.proposed_resolution,
            before_state=dict(finding.before_state),
            after_state={},
            detail=finding.detail,
        )

    # -- small helpers --------------------------------------------------------

    def _blob_object_path(self, sha_part: str, encoding: Any) -> Path:
        from .paths import blob_object_key, resolve_under_root

        return resolve_under_root(
            self._t0_root, blob_object_key(sha_part, encoding)
        )

    def _blob_ref_verified(self, blob_sha256: str | None) -> bool:
        """True iff SOME durable representation of the blob verifies now."""
        if not blob_sha256:
            return False
        try:
            return bool(self._blob_metadata.has_verified_physical(blob_sha256))
        except Exception:
            return False

    def _manifest_by_id(self, manifest_id: str) -> Any | None:
        for manifest in self._all_manifests():
            if manifest.partition_manifest_id == manifest_id:
                return manifest
        return None

    def _find_projection_file(self, bytes_sha: str) -> Path | None:
        projections_root = self._t0_root / "projections"
        if not projections_root.is_dir():
            return None
        for path in sorted(projections_root.rglob("*.parquet")):
            if path.is_file() and _sha256_file(path) == bytes_sha:
                return path
        return None


def StorageEncodingValue(value: str) -> Any:
    """Map a stored encoding string to the frozen enum (typed, strict)."""
    from .enums import StorageEncoding

    return StorageEncoding(value)


def _blob_object_key(sha_part: str, encoding: Any) -> Any:
    from .paths import blob_object_key

    return blob_object_key(sha_part, encoding)
