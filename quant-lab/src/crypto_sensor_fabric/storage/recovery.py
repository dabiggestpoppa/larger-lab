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
import threading
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
_ACTION_RESOLVE_ORPHAN_BLOB = "RESOLVE_ORPHAN_BLOB"
_ACTION_QUARANTINE_STAGING = "QUARANTINE_STAGING"
_ACTION_QUARANTINE_ORPHAN_PROJECTION = "QUARANTINE_ORPHAN_PROJECTION"
_ACTION_RESOLVE_ORPHAN_MANIFEST = "RESOLVE_ORPHAN_MANIFEST"
_ACTION_RECORD_MISSING_TARGET = "RECORD_MISSING_TARGET"
_ACTION_RECORD_ACQUISITION_DEPENDENCY = "RECORD_ACQUISITION_DEPENDENCY"
_ACTION_QUARANTINE_JOB = "QUARANTINE_JOB"
_ACTION_RECORD_LOCK_ONLY = "RECORD_LOCK_ONLY"

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
        self._run_counter = 0
        self._run_lock = threading.Lock()
        self._journal = RecoveryJournal(self._t0_root)
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

        Deterministic for tests (explicit ids are accepted by the
        scanner); collision-safe for operations: monotonic counter under a
        lock, full hex digest — never a wall-clock format, never a temp
        path.
        """
        with self._run_lock:
            self._run_counter += 1
            digest = hashlib.sha256(
                f"recovery-run:{id(self)}:{self._run_counter}".encode("utf-8")
            ).hexdigest()
        return f"recovery-{digest[:32]}-{self._run_counter:06d}"

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
                source.unlink(missing_ok=True)
                return False
            raise RecoveryQuarantineConflict(
                f"quarantine destination {destination.name} already holds "
                "DIFFERENT bytes; nothing overwritten (I08 §30)"
            )
        ensure_durable_directory(destination.parent)
        staging = destination.parent / f"{destination.name}.staging"
        staging.unlink(missing_ok=True)
        staging.write_bytes(source.read_bytes())
        try:
            publish_no_replace(staging, destination)
        except OSError as exc:
            staging.unlink(missing_ok=True)
            raise RecoveryQuarantineConflict(
                f"quarantine publication failed for {destination.name}: {exc}"
            ) from exc
        source.unlink(missing_ok=True)
        fsync_directory(destination.parent)
        return True

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
            except Exception as exc:
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
        moved = self._quarantine_file(object_path, destination, content_sha)
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
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "QUARANTINE_INTEGRITY: corrupt bytes preserved under "
                f"quarantine/integrity ({'moved' if moved else 'adopted'}); "
                "canonical object NOT overwritten; acquisition/manifest "
                "history preserved"
            ),
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
        """I08 §12: reconcile an ORPHAN_DURABLE_BLOB only with proven context.

        Revalidation: the orphan metadata must STILL be absent and the
        bytes still present (I08 §28).  The bytes are verified against
        their content-addressed name.  With registered durable context,
        reconciliation goes through the PUBLIC ``append_metadata`` /
        ``append_acquisition`` APIs (their validation remains
        authoritative; a refusal leaves the orphan unresolved).  Without
        proven context the blob is quarantined as unknown_context —
        provenance is NEVER manufactured.
        """
        sha_part = planned.object_id
        encoding_value = planned.before_state.get(
            "storage_encoding", "NONE"
        )
        encoding = StorageEncodingValue(encoding_value)
        try:
            self._blob_metadata.get_blob_metadata(sha_part)
            has_metadata = True
        except Exception:
            has_metadata = False
        if has_metadata:
            raise RecoveryPlanConflict(
                f"blob {sha_part} now has durable metadata; the scanned "
                "ORPHAN_DURABLE_BLOB plan is stale (I08 §28)"
            )
        object_path = self._blob_object_path(sha_part, encoding)
        if not object_path.exists():
            raise RecoveryPlanConflict(
                f"orphan blob {sha_part} vanished; the scanned plan is "
                "stale (I08 §28)"
            )
        content_sha = _sha256_file(object_path)
        context = self._orphan_context.get(sha_part)
        if context is not None and content_sha == sha_part:
            evidence_blob, acquisition = context
            try:
                self._blob_metadata.append_metadata(evidence_blob)
                self._acquisitions.append_acquisition(acquisition)
            except Exception as exc:
                return self._journal_action(
                    run_id=run_id,
                    planned=planned,
                    resolution=(
                        "UNRESOLVED: the repository APIs refused the "
                        f"registered context ({type(exc).__name__}); nothing "
                        "registered, nothing overwritten"
                    ),
                    after_state={
                        "reconciled": False,
                        "refusal": type(exc).__name__,
                    },
                )
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "RECONCILED through existing public repository APIs with "
                    "durable context proven and bytes verified (I08 §12)"
                ),
                after_state={
                    "reconciled": True,
                    "acquisition_id": getattr(
                        acquisition, "acquisition_id", None
                    ),
                },
            )
        # No proven context (or bytes contradict their name): quarantine.
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
        moved = self._quarantine_file(object_path, destination, content_sha)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "QUARANTINE: no durable context proves the request identity; "
                "provenance is never manufactured (I08 §12)"
                if category == QUARANTINE_CATEGORY_UNKNOWN_CONTEXT
                else "QUARANTINE_INTEGRITY: orphan bytes fail their "
                "content-addressed name; treated as corrupt, never repaired"
            ),
            after_state={
                "quarantined": moved,
                "quarantine_category": category,
                "quarantine_bytes_sha256": content_sha,
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
        moved = self._quarantine_file(physical, destination, content_sha)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "QUARANTINE under unknown_context: no durable projection "
                "catalog record proves the artifact's identity; T0A lineage "
                "is never manufactured (I08 §14)"
            ),
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
            raise RecoveryPlanConflict(
                f"manifest {manifest_id} joined the committed chain; the "
                "scanned plan is stale (I08 §28)"
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
        # CAS attestation through the PUBLIC pointer read (I08 §15: the
        # action is taken only when CAS semantics permit).  A concurrent
        # writer that moves the pointer first still loses here — the
        # repository's own ManifestCASConflict refuses, and the refusal is
        # recorded, never overridden.
        try:
            pointer = self._manifests.read_current_pointer(manifest.partition_key)
        except Exception as exc:
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "UNRESOLVED ORPHAN recorded: current pointer unreadable "
                    f"({type(exc).__name__}); no override (I08 §15)"
                ),
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
            return self._journal_action(
                run_id=run_id,
                planned=planned,
                resolution=(
                    "UNRESOLVED ORPHAN recorded: the manifest repository "
                    f"refused reconciliation ({type(exc).__name__}); no "
                    "override of CAS/ancestry semantics"
                ),
                after_state={
                    "unresolved_orphan": True,
                    "conflict": type(exc).__name__,
                },
            )
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "RECONCILED through the existing manifest repository API "
                "with exact ancestry and verified references (I08 §15)"
            ),
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
        moved = self._quarantine_file(source, destination, content_sha)
        return self._journal_action(
            run_id=run_id,
            planned=planned,
            resolution=(
                "STAGING QUARANTINED (bytes preserved): a .partial file is "
                "never evidence; resume was never advanced from staging "
                "(I08 §13)"
            ),
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
        owner_repository: Any = None,
        run_id: str,
    ) -> RecoveryAction | None:
        """EXPLICIT operator-driven lock clear (I08 §20).

        Executes ONLY when: the expected job id hashes exactly to the
        lock fingerprint, the lock file exists, and — when an owner
        repository is supplied — no in-process owner currently holds that
        job's RLock (best-effort non-blocking probe, documented
        limitation).  The RecoveryAction is journaled BEFORE removal
        (evidence precedes mutation); failure of the probe or hash check
        refuses the clear entirely.  Never invoked by apply_plan.
        """
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
        if owner_repository is not None:
            lock_obj = owner_repository._job_locks.get(expected_job_id)
            if lock_obj is not None:
                if not lock_obj.acquire(blocking=False):
                    raise RecoveryPlanConflict(
                        "an in-process owner currently holds the job lock; "
                        "refusing the clear (I08 §20)"
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
            kind = _ACTION_QUARANTINE_ORPHAN_PROJECTION
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
