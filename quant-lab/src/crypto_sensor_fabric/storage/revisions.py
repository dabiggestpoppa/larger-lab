"""SENSOR-B4-I06 — source revision / mutation registry.

Distinguishes SAME LOGICAL SOURCE + SAME BYTES (refetch) from SAME LOGICAL
SOURCE + DIFFERENT BYTES (revision/mutation), preserving every observation
and every revision, never overwriting history and never silently choosing
"latest".

Core identity doctrine (I06 §8):

- ``source_revision_key`` identifies the LOGICAL SOURCE / REQUEST BOUNDARY
  (what was asked for);
- ``blob_sha256`` identifies the EXACT BYTES returned;
- they are DIFFERENT objects.  The content hash NEVER enters the source
  key — otherwise mutation would mint a new "source" and become invisible.

Identity is versioned (``RevisionSourceIdentityV1``, §9): future changes
to source-key semantics require a new identity version; the descriptor is
persisted beside registry state so key derivation stays auditable and is
recomputed/verified on every catalog reload (§14).

Revision vocabulary (§6, frozen — no aliases):
``STABLE``, ``IDENTICAL_REFETCH``, ``SOURCE_MUTATION``,
``PROVIDER_DECLARED_REVISION``, ``UNKNOWN_REVISION``.

Resolution policies (§7, frozen — no FIRST/LATEST_ACQUIRED aliases):
``ERROR_ON_AMBIGUITY``, ``ALL``, ``FIRST_SEEN``, ``LATEST_SEEN``,
``EXACT_REVISION``, ``PROVIDER_DECLARED_CANONICAL``.

Registry layout (§28): immutable durable catalogs under
``catalogs/source_revisions/`` — ``segments/`` (one birth record per
revision), ``observations/`` (one per registered acquisition observation),
``declarations/`` (explicit provider revision/canonical evidence).  All
publications go through ``DurableJsonCatalog`` (staging → fsync → verify →
no-clobber publish → parent fsync); no direct ``write_text``, no overwrite.

Responsibility stays narrow (§69): identity, persistence, observation
persistence, declarations, resolution.  No job/resume/recovery/query
service.
"""

from __future__ import annotations

import hashlib
import threading
import time
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

# I04R2 §13: THE one authoritative usable-provenance eligibility predicate.
# The registry must never duplicate eligibility logic.
from .catalog import is_usable_manifest_provenance
from .enums import StorageEncoding  # re-exported for registry consumers
from .json_catalog import (
    DurableJsonCatalog,
    JsonCatalogCorrupt,
    canonical_json_bytes,
)
from .json_catalog import ensure_durable_directory

# ---------------------------------------------------------------------------
# Revision vocabulary (frozen, §6) and resolution policies (§7)
# ---------------------------------------------------------------------------


class RevisionState(str, Enum):
    """Frozen revision-segment states (§6).  No aliases."""

    STABLE = "STABLE"
    IDENTICAL_REFETCH = "IDENTICAL_REFETCH"
    SOURCE_MUTATION = "SOURCE_MUTATION"
    PROVIDER_DECLARED_REVISION = "PROVIDER_DECLARED_REVISION"
    UNKNOWN_REVISION = "UNKNOWN_REVISION"


class RevisionResolutionMode(str, Enum):
    """Frozen revision resolution policies (§7).  No old aliases."""

    ERROR_ON_AMBIGUITY = "ERROR_ON_AMBIGUITY"
    ALL = "ALL"
    FIRST_SEEN = "FIRST_SEEN"
    LATEST_SEEN = "LATEST_SEEN"
    EXACT_REVISION = "EXACT_REVISION"
    PROVIDER_DECLARED_CANONICAL = "PROVIDER_DECLARED_CANONICAL"


class ObservationState(str, Enum):
    """Immutable observation-event states (§24/§25/§31)."""

    FIRST_REGISTRATION = "FIRST_REGISTRATION"
    IDENTICAL_REFETCH = "IDENTICAL_REFETCH"
    SOURCE_MUTATION = "SOURCE_MUTATION"
    PROVIDER_DECLARED_REVISION = "PROVIDER_DECLARED_REVISION"


class MutationSeverity(str, Enum):
    """Frozen severity meaning (§37).  BLOCKER requires explicit drift
    evidence — never inferred merely because bytes differ."""

    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class RevisionError(Exception):
    """Base for the source-revision registry."""


class RevisionConfigurationError(RevisionError):
    """A commit-capable revision repository was constructed incompletely."""


class SourceRevisionCatalogCorrupt(RevisionError):
    """A committed registry fragment fails reload validation (§14/§49)."""


class RevisionContentUnavailable(RevisionError):
    """The acquisition carries no blob (§17): failure/no-data/unavailable
    acquisitions stay in acquisition history but create NO content segment.
    No zero hash is ever manufactured."""


class RevisionContentCorrupt(RevisionError):
    """Physical T0A verification failed at registration time (§18)."""


class RevisionObservationConflict(RevisionError):
    """Same acquisition_id mapped to a different revision identity (§48)."""


class RevisionObservationOrderConflict(RevisionError):
    """An observation earlier than the latest registered seen_at for the
    source key would force retroactive renumbering (§39) — forbidden."""


class RevisionTemporalAmbiguity(RevisionError):
    """Identical seen_at with differing bytes and no provable order (§40)."""


class RevisionLockHeld(RevisionError):
    """Another writer holds the per-source lock (§43/§44/§81).  Never
    auto-deleted; I08 owns stale-lock recovery."""


class RevisionAmbiguityError(RevisionError):
    """Resolution policy refuses to pick (§55/§60): ERROR_ON_AMBIGUITY with
    >1 revisions, or multiple distinct provider-canonical declarations."""


class RevisionNotFound(RevisionError):
    """No revision exists for the requested identity (§55/§59)."""


class RevisionResolutionUnavailable(RevisionError):
    """A resolution mode cannot be satisfied (§60): e.g.
    PROVIDER_DECLARED_CANONICAL with zero canonical declarations."""


# ---------------------------------------------------------------------------
# RevisionSourceIdentityV1 (§9-§12)
# ---------------------------------------------------------------------------

IDENTITY_VERSION = 1

_V1_REQUEST_FIELDS = (
    "provider_id",
    "venue",
    "sensor_family",
    "native_instrument",
    "native_granularity",
    "request_fingerprint",
    "requested_start",
    "requested_end",
    "endpoint_host",
    "endpoint_path",
    "request_family",
)


def _identity_field(name: str, value: Any) -> Any:
    """Canonicalize one identity field (§10): enums by value, timestamps as
    UTC ISO-8601, native strings EXACTLY as persisted."""
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            # AcquisitionRecord already normalizes to aware UTC; a naive
            # value here would silently change key semantics.
            raise RevisionConfigurationError(
                f"identity field {name!r} is a naive datetime; the registry "
                "derives keys only from offset-aware acquisition timestamps"
            )
        return value.astimezone(UTC).isoformat()
    return value


class RevisionSourceIdentityV1(BaseModel):
    """Closed V1 source-identity descriptor (§9-§12).

    Frozen field set: REQUEST semantics only.  Observation/result fields —
    acquisition_id, blob_sha256, adapter_version, wall clocks, HTTP status,
    checksums, resume tokens, quality flags, failure_ref — are structurally
    excluded (§11): they describe what came back, not what was asked for.
    ``source_locator`` is deliberately absent (§12): it may be a temporary
    delivery URL or transport-resolved locator; request_fingerprint +
    request semantics are the generic identity authority.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity_version: int = IDENTITY_VERSION
    provider_id: str
    venue: str
    sensor_family: str
    native_instrument: str
    native_granularity: str | None
    request_fingerprint: str
    requested_start: str
    requested_end: str
    endpoint_host: str | None
    endpoint_path: str | None
    request_family: str | None

    @classmethod
    def from_acquisition(cls, acquisition: Any) -> "RevisionSourceIdentityV1":
        """Derive the descriptor from durable acquisition REQUEST semantics."""
        data: dict[str, Any] = {}
        for name in _V1_REQUEST_FIELDS:
            data[name] = _identity_field(name, getattr(acquisition, name))
        return cls(**data)  # type: ignore[arg-type]

    def to_descriptor(self) -> dict[str, Any]:
        """Language-neutral canonical descriptor (§13)."""
        return {
            "identity_version": self.identity_version,
            "fields": {name: getattr(self, name) for name in _V1_REQUEST_FIELDS},
        }

    def source_revision_key(self) -> str:
        """``SHA256(canonical_json_bytes(descriptor))`` — full 64 lowercase
        hex (§13).  Never derived from content."""
        digest = hashlib.sha256(
            canonical_json_bytes(self.to_descriptor())
        ).hexdigest()
        return digest


# ---------------------------------------------------------------------------
# Durable records
# ---------------------------------------------------------------------------


class RevisionSegmentRecord(BaseModel):
    """Immutable segment-birth record — one per revision (§22/§29/§32).

    ``segment_id`` = ``<source_revision_key>:<revision_number>`` is the
    catalog logical id: one source key owns MANY revision segments, so the
    key alone can never be the physical identity.  The segment birth IS the
    first observation (preferred simplest v1): ``first_acquisition_id``
    preserves the binding, and subsequent observations are separate
    append-only records (§30/§31).  No ``last_seen_at`` is persisted here —
    it is materialized from observations so identical refetches never
    rewrite history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_type: str = "source_revision_segment"
    segment_id: str
    source_revision_key: str
    identity_version: int
    identity_descriptor: dict[str, Any]
    revision_number: int
    blob_sha256: str
    first_seen_at: str  # response_observed_at of the first acquisition
    first_acquisition_id: str
    revision_state: str
    revision_reason: str
    registered_at: str  # operational audit clock (§21) — not chronology


class RevisionObservationRecord(BaseModel):
    """Immutable observation event — one per subsequent registered
    acquisition (§24/§31).  Chronology is ``seen_at`` =
    response_observed_at (§20).  ``usable_provenance`` is preserved
    explicitly: revision evidence never promotes forensic acquisitions
    (§19)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_type: str = "source_revision_observation"
    observation_id: str
    acquisition_id: str
    source_revision_key: str
    revision_number: int
    blob_sha256: str
    seen_at: str
    observation_state: str
    usable_provenance: bool
    severity: str
    registered_at: str


class RevisionDeclarationRecord(BaseModel):
    """Explicit provider declaration evidence (§33-§36).

    Never inferred from bytes/ETag/last-modified/status/filenames.  A
    revision declaration (bytes changed, provider says so) or a canonical
    declaration (provider designates a revision canonical) must carry a
    durable ``evidence_ref``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_type: str = "source_revision_declaration"
    declaration_id: str
    source_revision_key: str
    revision_number: int | None  # None = declaration precedes the segment
    declaration_kind: str  # "revision" | "canonical"
    evidence_ref: str
    declared_at: str
    registered_at: str


# ---------------------------------------------------------------------------
# Dependency protocols (§16) — mandatory, no optional proof dependencies
# ---------------------------------------------------------------------------


@runtime_checkable
class RevisionAcquisitionSource(Protocol):
    """Sealed acquisition dependency: resolve durable truth, never accept a
    caller-supplied record as authority (§15)."""

    def get_acquisition(self, acquisition_id: str) -> Any: ...


@runtime_checkable
class RevisionBlobSource(Protocol):
    """Sealed blob dependencies: durable metadata + physical verification
    (§18)."""

    def get_blob_metadata(self, blob_sha256: str) -> Any: ...


@runtime_checkable
class RevisionPhysicalStore(Protocol):
    def verify_blob(
        self,
        blob_sha256: str,
        storage_encoding: Any,
        *,
        expected_byte_length: int | None = None,
    ) -> Any: ...


def _require(
    value: Any,
    *,
    protocol: Any,
    name: str,
    capability: str,
) -> None:
    if value is None:
        raise RevisionConfigurationError(
            f"SourceRevisionRegistry requires {name}"
        )
    if not isinstance(value, protocol):
        raise RevisionConfigurationError(
            f"{name} must satisfy the {capability} contract "
            "(I06 §16 — no optional proof dependencies)"
        )


# ---------------------------------------------------------------------------
# Public materialized view (§50/§54)
# ---------------------------------------------------------------------------


class RevisionResolution(BaseModel):
    """Narrow resolution result (§54).  Ambiguity stays visible."""

    model_config = ConfigDict(frozen=True)

    source_revision_key: str
    policy: str
    selected_revision_numbers: list[int]
    ambiguous: bool
    all_revision_numbers: list[int]
    provider_canonical_revision_number: int | None = None


def _canonical_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise RevisionConfigurationError(
            "chronology timestamps must be offset-aware"
        )
    return value.astimezone(UTC).isoformat()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class SourceRevisionRegistry:
    """Durable, append-only source-revision registry (I06).

    One physical catalog per record family under ``<root>/``:

    - ``segments/``      — revision birth records (immutable);
    - ``observations/``  — subsequent acquisition observations (immutable);
    - ``declarations/``  — explicit provider declaration evidence.

    Classification (§22-§27, §39-§41) is serialized per ``source_revision_key``
    by a local filesystem lock (§43) so concurrent writers can never fork
    revision numbering.  No distributed coordination is claimed.
    """

    def __init__(
        self,
        root: Path,
        *,
        acquisition_repository: Any = None,
        blob_metadata_repository: Any = None,
        blob_store: Any = None,
        clock: Any = None,
        lock_timeout_seconds: float = 5.0,
    ) -> None:
        """Contract for a registration clock injection (§21); defaults to
        wall time.  Operational only — never revision chronology.
        ``lock_timeout_seconds`` bounds how long a registration waits for a
        contended per-source file lock before failing typed (§44).  A
        pre-existing stale lock is never auto-deleted; tests may inject 0
        for fail-fast semantics."""
        _require(
            acquisition_repository,
            protocol=RevisionAcquisitionSource,
            name="acquisition_repository",
            capability="RevisionAcquisitionSource",
        )
        _require(
            blob_metadata_repository,
            protocol=RevisionBlobSource,
            name="blob_metadata_repository",
            capability="RevisionBlobSource",
        )
        _require(
            blob_store,
            protocol=RevisionPhysicalStore,
            name="blob_store",
            capability="RevisionPhysicalStore",
        )
        self._acquisitions = acquisition_repository
        self._blob_metadata = blob_metadata_repository
        self._blob_store = blob_store
        self._clock = clock or (lambda: datetime.now(UTC))
        self._lock_timeout_seconds = lock_timeout_seconds
        self._root = Path(root)
        self._lock_root = self._root / "locks"
        self._process_lock = threading.Lock()
        self._key_locks: dict[str, threading.RLock] = {}
        self._file_locks: dict[str, Any] = {}
        try:
            self._segments = DurableJsonCatalog(
                self._root / "segments",
                logical_id_field="segment_id",
            )
            self._observations = DurableJsonCatalog(
                self._root / "observations",
                logical_id_field="observation_id",
            )
            self._declarations = DurableJsonCatalog(
                self._root / "declarations",
                logical_id_field="declaration_id",
            )
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._segments_by_key: dict[str, list[RevisionSegmentRecord]] = {}
        self._observations_by_key: dict[str, list[RevisionObservationRecord]] = {}
        self._declarations_by_key: dict[str, list[RevisionDeclarationRecord]] = {}
        self._acquisition_bindings: dict[str, tuple[str, int, str]] = {}
        self._load_all()

    # -- loading -------------------------------------------------------------

    def _load_segments(self) -> None:
        for logical_id, payload in self._catalog_items(self._segments):
            try:
                record = RevisionSegmentRecord(**payload)
            except Exception as exc:
                raise SourceRevisionCatalogCorrupt(
                    f"revision segment fragment corrupt: {exc}"
                ) from exc
            self._validate_segment(record, logical_id)
            self._segments_by_key.setdefault(record.source_revision_key, []).append(
                record
            )

    def _catalog_items(self, catalog: DurableJsonCatalog):
        return ((lid, catalog.get(lid)) for lid in catalog.list_ids())

    def _validate_segment(
        self, record: RevisionSegmentRecord, logical_id: str
    ) -> None:
        # §14: the persisted descriptor must recompute to the stored key.
        # The fragment filename binds to the segment_id, not the source key:
        # one source key owns many revision segments.
        if record.segment_id != logical_id:
            raise SourceRevisionCatalogCorrupt(
                "segment fragment does not bind to its segment_id"
            )
        expected_segment_id = (
            f"{record.source_revision_key}:{record.revision_number}"
        )
        if record.segment_id != expected_segment_id:
            raise SourceRevisionCatalogCorrupt(
                "segment_id does not bind to (source_revision_key, "
                "revision_number)"
            )
        if record.record_type != "source_revision_segment":
            raise SourceRevisionCatalogCorrupt("wrong segment record_type")
        fields = record.identity_descriptor.get("fields", {})
        try:
            rebuilt = RevisionSourceIdentityV1(
                identity_version=record.identity_version,
                **fields,  # type: ignore[arg-type]
            )
        except Exception as exc:
            raise SourceRevisionCatalogCorrupt(
                f"identity descriptor for {logical_id!r} is invalid: {exc}"
            ) from exc
        if rebuilt.source_revision_key() != record.source_revision_key:
            raise SourceRevisionCatalogCorrupt(
                "identity descriptor does not recompute to the stored "
                f"source_revision_key for fragment {logical_id!r}"
            )

    def _load_observations(self) -> None:
        for logical_id, payload in self._catalog_items(self._observations):
            try:
                record = RevisionObservationRecord(**payload)
            except Exception as exc:
                raise SourceRevisionCatalogCorrupt(
                    f"observation fragment corrupt: {exc}"
                ) from exc
            if record.observation_id != logical_id:
                raise SourceRevisionCatalogCorrupt(
                    "observation fragment does not bind to its observation_id"
                )
            self._observations_by_key.setdefault(
                record.source_revision_key, []
            ).append(record)
            self._acquisition_bindings[record.acquisition_id] = (
                record.source_revision_key,
                record.revision_number,
                record.blob_sha256,
            )

    def _load_declarations(self) -> None:
        for logical_id, payload in self._catalog_items(self._declarations):
            try:
                record = RevisionDeclarationRecord(**payload)
            except Exception as exc:
                raise SourceRevisionCatalogCorrupt(
                    f"declaration fragment corrupt: {exc}"
                ) from exc
            if record.declaration_id != logical_id:
                raise SourceRevisionCatalogCorrupt(
                    "declaration fragment does not bind to its declaration_id"
                )
            self._declarations_by_key.setdefault(
                record.source_revision_key, []
            ).append(record)

    def _validate_cross_constraints(self) -> None:
        # §49 restart validation.
        for key, segments in self._segments_by_key.items():
            numbers = sorted(s.revision_number for s in segments)
            if numbers != list(range(1, len(numbers) + 1)):
                raise SourceRevisionCatalogCorrupt(
                    f"revision numbers for {key[:12]}... are not contiguous "
                    "from 1"
                )
            seen_numbers: set[int] = set()
            for seg in segments:
                if seg.revision_number in seen_numbers:
                    raise SourceRevisionCatalogCorrupt(
                        "duplicate revision number in committed segments"
                    )
                seen_numbers.add(seg.revision_number)
                try:
                    acq = self._acquisitions.get_acquisition(
                        seg.first_acquisition_id
                    )
                except Exception as exc:
                    raise SourceRevisionCatalogCorrupt(
                        f"segment first acquisition "
                        f"{seg.first_acquisition_id!r} does not exist durably"
                    ) from exc
                if acq.blob_sha256 != seg.blob_sha256:
                    raise SourceRevisionCatalogCorrupt(
                        "segment first acquisition blob does not match the "
                        "segment blob"
                    )
        # §49: observations reference existing revisions, blob matches, the
        # acquisition exists durably with the SAME blob, and no acquisition
        # belongs to two revisions.  Seen times obey accepted ordering.
        all_bindings: dict[str, tuple[str, int, str]] = {}
        for key, observations in self._observations_by_key.items():
            segments = {
                s.revision_number: s for s in self._segments_by_key.get(key, [])
            }
            for obs in observations:
                seg = segments.get(obs.revision_number)
                if seg is None:
                    raise SourceRevisionCatalogCorrupt(
                        f"observation {obs.observation_id!r} references a "
                        "revision that does not exist"
                    )
                if obs.blob_sha256 != seg.blob_sha256:
                    raise SourceRevisionCatalogCorrupt(
                        "observation blob does not match its revision segment"
                    )
                prior = all_bindings.get(obs.acquisition_id)
                if prior is not None and prior != (
                    obs.source_revision_key,
                    obs.revision_number,
                    obs.blob_sha256,
                ):
                    raise SourceRevisionCatalogCorrupt(
                        f"acquisition {obs.acquisition_id!r} belongs to two "
                        "revision observations"
                    )
                all_bindings[obs.acquisition_id] = (
                    obs.source_revision_key,
                    obs.revision_number,
                    obs.blob_sha256,
                )
                try:
                    acq = self._acquisitions.get_acquisition(obs.acquisition_id)
                except Exception as exc:
                    raise SourceRevisionCatalogCorrupt(
                        f"observation acquisition {obs.acquisition_id!r} does "
                        "not exist durably"
                    ) from exc
                if acq.blob_sha256 != obs.blob_sha256:
                    raise SourceRevisionCatalogCorrupt(
                        "observation acquisition blob does not match the "
                        "observation"
                    )
                latest = self._latest_seen_for(key)
                if obs.seen_at < latest:
                    raise SourceRevisionCatalogCorrupt(
                        "committed observation violates seen-time ordering "
                        f"for {key[:12]}..."
                    )
        for key, declarations in self._declarations_by_key.items():
            segments = {
                s.revision_number for s in self._segments_by_key.get(key, [])
            }
            for dec in declarations:
                if (
                    dec.revision_number is not None
                    and dec.revision_number not in segments
                ):
                    raise SourceRevisionCatalogCorrupt(
                        f"declaration {dec.declaration_id!r} references a "
                        "revision that does not exist"
                    )

    def _load_all(self) -> None:
        self._load_segments()
        self._load_observations()
        self._load_declarations()
        self._validate_cross_constraints()

    # -- per-source writer coordination (§43-§44) ----------------------------

    def _key_lock(self, source_revision_key: str) -> threading.RLock:
        with self._process_lock:
            lock = self._key_locks.setdefault(
                source_revision_key, threading.RLock()
            )
            return lock

    def _acquire_file_lock(self, source_revision_key: str) -> Any:
        """Source-key-scoped local filesystem lock (§43).  An existing lock
        is NEVER auto-deleted (§44/§81); I08 owns stale-lock policy.  A
        bounded wait tolerates a concurrent writer that is mid-registration
        for the SAME source key; the wait is capped by
        ``lock_timeout_seconds``."""
        if not self._lock_root.exists():
            ensure_durable_directory(self._lock_root)
        lock_path = self._lock_root / f"{source_revision_key}.lock"
        deadline = time.monotonic() + self._lock_timeout_seconds
        while True:
            try:
                # No-clobber create: only one winner per source key.
                handle = open(lock_path, "x")
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise RevisionLockHeld(
                        f"source lock held for key {source_revision_key[:12]}...; "
                        "stale locks are recovery evidence, never auto-deleted "
                        "(I06 §44)"
                    ) from None
                time.sleep(0.01)
                continue
            handle.write("held\n")
            handle.flush()
            return handle

    def _release_file_lock(self, handle: Any, source_revision_key: str) -> None:
        try:
            handle.close()
            lock_path = self._lock_root / f"{source_revision_key}.lock"
            lock_path.unlink(missing_ok=True)
        except OSError:
            # A crash mid-release leaves recovery evidence for I08.
            pass

    # -- physical truth (§17/§18) ---------------------------------------------

    def _resolve_durable_acquisition(self, acquisition_id: str) -> Any:
        try:
            acquisition = self._acquisitions.get_acquisition(acquisition_id)
        except Exception as exc:
            raise RevisionContentUnavailable(
                f"acquisition {acquisition_id!r} does not exist durably"
            ) from exc
        if acquisition is None:
            raise RevisionContentUnavailable(
                f"acquisition {acquisition_id!r} does not exist durably"
            )
        blob_sha = acquisition.blob_sha256
        if not blob_sha:
            raise RevisionContentUnavailable(
                f"acquisition {acquisition_id!r} carries no blob_sha256 "
                "(failure/no-data/unavailable acquisitions never create a "
                "content revision segment; no zero hash is manufactured)"
            )
        metas = self._blob_metadata.get_blob_metadata(blob_sha)
        if not metas:
            raise RevisionContentCorrupt(
                f"blob {blob_sha} has no durable EvidenceBlob metadata"
            )
        verified = False
        for meta in metas:
            try:
                check = self._blob_store.verify_blob(
                    meta.blob_sha256,
                    meta.storage_encoding,
                    expected_byte_length=meta.byte_length,
                )
            except Exception as exc:
                # Missing/absent physical bytes: absence != corruption, but
                # neither can mint revision truth (I06 §18).
                raise RevisionContentCorrupt(
                    f"blob {blob_sha} physical verification could not "
                    f"complete: {exc}"
                ) from exc
            if check.integrity_state.name == "LOCAL_HASH_VERIFIED":
                verified = True
                break
        if not verified:
            raise RevisionContentCorrupt(
                f"blob {blob_sha} has no physically verified representation "
                "(presence-only is insufficient — I06 §18)"
            )
        return acquisition

    def _usable_provenance(self, acquisition: Any) -> bool:
        """§19: forensic acquisitions may be OBSERVED (the provider returned
        exact bytes) but are never promoted to usable science.  Delegates to
        THE one I04R2 §13 eligibility predicate — no duplicated rule."""
        return is_usable_manifest_provenance(acquisition)

    def _birth_observation_view(self, segment: RevisionSegmentRecord) -> RevisionObservationRecord:
        """The synthetic §32 first-observation view of a segment birth.  The
        birth acquisition's usable-provenance state is resolved from DURABLE
        acquisition truth, never assumed True (§19)."""
        try:
            acq = self._acquisitions.get_acquisition(segment.first_acquisition_id)
            usable = self._usable_provenance(acq)
        except Exception:
            usable = False
        state_for = {
            RevisionState.STABLE.value: ObservationState.FIRST_REGISTRATION,
            RevisionState.SOURCE_MUTATION.value: ObservationState.SOURCE_MUTATION,
            RevisionState.PROVIDER_DECLARED_REVISION.value: (
                ObservationState.PROVIDER_DECLARED_REVISION
            ),
        }
        severity_for = {
            RevisionState.STABLE.value: MutationSeverity.INFO,
            RevisionState.SOURCE_MUTATION.value: MutationSeverity.WARNING,
            RevisionState.PROVIDER_DECLARED_REVISION.value: (
                MutationSeverity.NOTICE
            ),
        }
        return RevisionObservationRecord(
            observation_id=f"{segment.first_acquisition_id}",
            acquisition_id=segment.first_acquisition_id,
            source_revision_key=segment.source_revision_key,
            revision_number=segment.revision_number,
            blob_sha256=segment.blob_sha256,
            seen_at=segment.first_seen_at,
            observation_state=state_for[segment.revision_state].value,
            usable_provenance=usable,
            severity=severity_for[segment.revision_state].value,
            registered_at=segment.registered_at,
        )

    # -- registration ----------------------------------------------------------

    def register_acquisition(
        self,
        acquisition_id: str,
        *,
        provider_declaration: dict[str, Any] | None = None,
    ) -> RevisionObservationRecord:
        """Resolve the durable acquisition, verify its blob, classify the
        observation against the source's revision history and persist it
        append-only (§15-§47).  ``provider_declaration`` is EXPLICIT
        evidence (§33) — never inferred."""
        if not isinstance(acquisition_id, str) or not acquisition_id:
            raise RevisionConfigurationError(
                "acquisition_id must be a nonempty string"
            )

        # Idempotence path (§47): re-resolve, re-verify, recompute, compare.
        existing_binding = self._acquisition_bindings.get(acquisition_id)
        if existing_binding is not None:
            return self._idempotent_reregister(
                acquisition_id, existing_binding
            )

        # Resolve durable truth + physical verification FIRST.
        acquisition = self._resolve_durable_acquisition(acquisition_id)
        identity = RevisionSourceIdentityV1.from_acquisition(acquisition)
        key = identity.source_revision_key()
        blob_sha = acquisition.blob_sha256
        seen_at = _canonical_utc(acquisition.response_observed_at)
        usable = self._usable_provenance(acquisition)

        file_lock = self._acquire_file_lock(key)
        try:
            with self._key_lock(key):
                segments = self._segments_by_key.get(key, [])
                if segments:
                    return self._classify_against_history(
                        key=key,
                        identity=identity,
                        acquisition_id=acquisition_id,
                        blob_sha=blob_sha,
                        seen_at=seen_at,
                        usable=usable,
                        segments=sorted(
                            segments, key=lambda s: s.revision_number
                        ),
                        provider_declaration=provider_declaration,
                    )
                return self._register_first_observation(
                    key=key,
                    identity=identity,
                    acquisition_id=acquisition_id,
                    blob_sha=blob_sha,
                    seen_at=seen_at,
                    usable=usable,
                )
        finally:
            self._release_file_lock(file_lock, key)

    def _register_first_observation(
        self,
        *,
        key: str,
        identity: RevisionSourceIdentityV1,
        acquisition_id: str,
        blob_sha: str,
        seen_at: str,
        usable: bool,
    ) -> RevisionObservationRecord:
        """§23: no prior revision exists — rev1 STABLE.  The segment birth
        IS the first observation (§32)."""
        registered_at = _canonical_utc(self._clock())
        segment = RevisionSegmentRecord(
            source_revision_key=key,
            segment_id=f"{key}:1",
            identity_version=identity.identity_version,
            identity_descriptor=identity.to_descriptor(),
            revision_number=1,
            blob_sha256=blob_sha,
            first_seen_at=seen_at,
            first_acquisition_id=acquisition_id,
            revision_state=RevisionState.STABLE.value,
            revision_reason="first observation of this logical source",
            registered_at=registered_at,
        )
        try:
            self._segments.commit(f"{key}:1", segment.model_dump(mode="json"))
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._segments_by_key.setdefault(key, []).append(segment)
        self._acquisition_bindings[acquisition_id] = (key, 1, blob_sha)
        return RevisionObservationRecord(
            observation_id=f"{acquisition_id}",
            acquisition_id=acquisition_id,
            source_revision_key=key,
            revision_number=1,
            blob_sha256=blob_sha,
            seen_at=seen_at,
            observation_state=ObservationState.FIRST_REGISTRATION.value,
            usable_provenance=usable,
            severity=MutationSeverity.INFO.value,
            registered_at=registered_at,
        )

    def _classify_against_history(
        self,
        *,
        key: str,
        identity: RevisionSourceIdentityV1,
        acquisition_id: str,
        blob_sha: str,
        seen_at: str,
        usable: bool,
        segments: list[RevisionSegmentRecord],
        provider_declaration: dict[str, Any] | None,
    ) -> RevisionObservationRecord:
        current = segments[-1]
        latest_seen = self._latest_seen_for(key)
        if seen_at < latest_seen:
            raise RevisionObservationOrderConflict(
                f"observation seen_at {seen_at} precedes the latest "
                f"registered seen_at {latest_seen} for source "
                f"{key[:12]}...; retroactive insertion with renumbering is "
                "forbidden (I06 §39)"
            )
        # §68 crash completion: a prior invocation may have committed a
        # segment birth and crashed before its observation record.  Re-registering
        # the SAME birth acquisition completes the chain in place — it must
        # never masquerade as a refetch of a different classification.
        birth_segment = next(
            (
                s
                for s in segments
                if s.first_acquisition_id == acquisition_id
            ),
            None,
        )
        if birth_segment is not None:
            return self._complete_birth_observation(
                key=key, segment=birth_segment, usable=usable
            )
        if provider_declaration is not None:
            self._validate_declaration_payload(provider_declaration)
        if blob_sha == current.blob_sha256:
            # §24/§41: identical bytes to the CURRENT segment — no new
            # revision, ever.  §34: an explicit provider declaration with
            # unchanged bytes is preserved as declaration evidence only;
            # the content revision number remains unchanged.
            if provider_declaration is not None:
                self._commit_declaration(
                    declaration_id=f"{acquisition_id}:revision",
                    key=key,
                    revision_number=current.revision_number,
                    declaration_kind="revision",
                    evidence_ref=str(provider_declaration["evidence_ref"]),
                    declared_at=str(
                        provider_declaration.get(
                            "declared_at", _canonical_utc(self._clock())
                        )
                    ),
                )
            return self._register_identical_refetch(
                key=key,
                acquisition_id=acquisition_id,
                current=current,
                seen_at=seen_at,
                usable=usable,
            )
        # §40: identical seen_at with differing bytes — source order cannot
        # be proven; fail closed.  Acquisition evidence stays durable.
        if seen_at == latest_seen:
            raise RevisionTemporalAmbiguity(
                f"same seen_at {seen_at} with differing bytes for source "
                f"{key[:12]}...; source order cannot be proven — fail "
                "closed (I06 §40)"
            )
        return self._register_new_revision(
            key=key,
            identity=identity,
            acquisition_id=acquisition_id,
            blob_sha=blob_sha,
            seen_at=seen_at,
            usable=usable,
            current=current,
            provider_declaration=provider_declaration,
        )

    @staticmethod
    def _validate_declaration_payload(
        provider_declaration: dict[str, Any],
    ) -> None:
        """§33: declaration evidence is EXPLICIT — kind + durable
        evidence_ref are mandatory; status/ETag/filename are never
        consulted."""
        if provider_declaration.get("declaration_kind") != "revision":
            raise RevisionConfigurationError(
                "provider_declaration at registration must be a "
                "'revision' declaration"
            )
        if not provider_declaration.get("evidence_ref"):
            raise RevisionConfigurationError(
                "provider declaration requires durable evidence_ref "
                "(never inferred — I06 §33)"
            )

    def _complete_birth_observation(
        self,
        *,
        key: str,
        segment: RevisionSegmentRecord,
        usable: bool,
    ) -> RevisionObservationRecord:
        """§68: finish a partially registered birth (segment committed,
        observation record missing) with the segment's OWN classification —
        never a different revision chain."""
        state_for = {
            RevisionState.STABLE.value: ObservationState.FIRST_REGISTRATION,
            RevisionState.SOURCE_MUTATION.value: ObservationState.SOURCE_MUTATION,
            RevisionState.PROVIDER_DECLARED_REVISION.value: (
                ObservationState.PROVIDER_DECLARED_REVISION
            ),
        }
        severity_for = {
            RevisionState.STABLE.value: MutationSeverity.INFO,
            RevisionState.SOURCE_MUTATION.value: MutationSeverity.WARNING,
            RevisionState.PROVIDER_DECLARED_REVISION.value: (
                MutationSeverity.NOTICE
            ),
        }
        record = RevisionObservationRecord(
            observation_id=f"{segment.first_acquisition_id}",
            acquisition_id=segment.first_acquisition_id,
            source_revision_key=key,
            revision_number=segment.revision_number,
            blob_sha256=segment.blob_sha256,
            seen_at=segment.first_seen_at,
            observation_state=state_for[segment.revision_state].value,
            usable_provenance=usable,
            severity=severity_for[segment.revision_state].value,
            registered_at=_canonical_utc(self._clock()),
        )
        try:
            self._observations.commit(
                record.observation_id, record.model_dump(mode="json")
            )
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._observations_by_key.setdefault(key, []).append(record)
        self._acquisition_bindings[record.acquisition_id] = (
            key,
            segment.revision_number,
            segment.blob_sha256,
        )
        return record

    def _latest_seen_for(self, key: str) -> str:
        segments = self._segments_by_key.get(key, [])
        latest = max(
            (s.first_seen_at for s in segments), default=None
        )
        observations = self._observations_by_key.get(key, [])
        obs_latest = max(
            (o.seen_at for o in observations), default=None
        )
        candidates = [v for v in (latest, obs_latest) if v is not None]
        return max(candidates) if candidates else ""

    def _register_identical_refetch(
        self,
        *,
        key: str,
        acquisition_id: str,
        current: RevisionSegmentRecord,
        seen_at: str,
        usable: bool,
    ) -> RevisionObservationRecord:
        """§24: NO new revision number.  Append an immutable observation;
        last_seen_at is MATERIALIZED from observations (§30)."""
        registered_at = _canonical_utc(self._clock())
        observation_id = f"{acquisition_id}"
        record = RevisionObservationRecord(
            observation_id=observation_id,
            acquisition_id=acquisition_id,
            source_revision_key=key,
            revision_number=current.revision_number,
            blob_sha256=current.blob_sha256,
            seen_at=seen_at,
            observation_state=ObservationState.IDENTICAL_REFETCH.value,
            usable_provenance=usable,
            severity=MutationSeverity.INFO.value,
            registered_at=registered_at,
        )
        try:
            self._observations.commit(
                observation_id, record.model_dump(mode="json")
            )
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._observations_by_key.setdefault(key, []).append(record)
        # A duplicate observation_id means the same acquisition_id was
        # already mapped by an observation record — compare and type-conflict
        # on divergence (§48) rather than silently adopt.
        prior = self._acquisition_bindings.get(acquisition_id)
        if prior is not None and prior != (key, current.revision_number, current.blob_sha256):
            raise RevisionObservationConflict(
                f"acquisition {acquisition_id!r} is already bound to "
                f"revision {prior[1]} of {prior[0][:12]}...; refusing to "
                "rebind (I06 §48)"
            )

    def _register_new_revision(
        self,
        *,
        key: str,
        identity: RevisionSourceIdentityV1,
        acquisition_id: str,
        blob_sha: str,
        seen_at: str,
        usable: bool,
        current: RevisionSegmentRecord,
        provider_declaration: dict[str, Any] | None,
    ) -> RevisionObservationRecord:
        """§25/§33: new bytes → new revision.  PROVIDER_DECLARED_REVISION
        ONLY with explicit declaration evidence; otherwise SOURCE_MUTATION
        (WARNING — BLOCKER requires explicit drift evidence, §37)."""
        if provider_declaration is not None:
            self._validate_declaration_payload(provider_declaration)
        new_number = current.revision_number + 1
        state = (
            RevisionState.PROVIDER_DECLARED_REVISION.value
            if provider_declaration is not None
            else RevisionState.SOURCE_MUTATION.value
        )
        reason = (
            "provider explicitly declared a new revision"
            if provider_declaration is not None
            else "observed bytes differ from the current revision"
        )
        severity = (
            MutationSeverity.NOTICE.value
            if provider_declaration is not None
            else MutationSeverity.WARNING.value
        )
        registered_at = _canonical_utc(self._clock())
        segment_id = f"{key}:{new_number}"
        segment = RevisionSegmentRecord(
            source_revision_key=key,
            segment_id=segment_id,
            identity_version=identity.identity_version,
            identity_descriptor=identity.to_descriptor(),
            revision_number=new_number,
            blob_sha256=blob_sha,
            first_seen_at=seen_at,
            first_acquisition_id=acquisition_id,
            revision_state=state,
            revision_reason=reason,
            registered_at=registered_at,
        )
        try:
            self._segments.commit(segment_id, segment.model_dump(mode="json"))
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._segments_by_key.setdefault(key, []).append(segment)
        observation_id = f"{acquisition_id}"
        record = RevisionObservationRecord(
            observation_id=observation_id,
            acquisition_id=acquisition_id,
            source_revision_key=key,
            revision_number=new_number,
            blob_sha256=blob_sha,
            seen_at=seen_at,
            observation_state=(
                ObservationState.PROVIDER_DECLARED_REVISION.value
                if provider_declaration is not None
                else ObservationState.SOURCE_MUTATION.value
            ),
            usable_provenance=usable,
            severity=severity,
            registered_at=registered_at,
        )
        try:
            self._observations.commit(
                observation_id, record.model_dump(mode="json")
            )
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._observations_by_key.setdefault(key, []).append(record)
        if provider_declaration is not None:
            self._commit_declaration(
                declaration_id=f"{acquisition_id}:revision",
                key=key,
                revision_number=new_number,
                declaration_kind="revision",
                evidence_ref=str(provider_declaration["evidence_ref"]),
                declared_at=str(
                    provider_declaration.get(
                        "declared_at", _canonical_utc(self._clock())
                    )
                ),
            )
        self._acquisition_bindings[acquisition_id] = (
            key,
            new_number,
            blob_sha,
        )
        return record

    def _idempotent_reregister(
        self,
        acquisition_id: str,
        binding: tuple[str, int, str],
    ) -> RevisionObservationRecord:
        """§47/§77: re-resolve durable acquisition, RE-VERIFY the physical
        blob, recompute the key, compare the exact binding.  No stale
        cached success over corrupt/changed truth."""
        key, revision_number, blob_sha = binding
        acquisition = self._resolve_durable_acquisition(acquisition_id)
        identity = RevisionSourceIdentityV1.from_acquisition(acquisition)
        recomputed = identity.source_revision_key()
        if recomputed != key or acquisition.blob_sha256 != blob_sha:
            raise RevisionObservationConflict(
                f"acquisition {acquisition_id!r} is durably bound to "
                f"revision {revision_number} of {key[:12]}... but the "
                "current durable acquisition/blob no longer matches that "
                "binding (I06 §48)"
            )
        usable = self._usable_provenance(acquisition)
        return RevisionObservationRecord(
            observation_id=f"{acquisition_id}",
            acquisition_id=acquisition_id,
            source_revision_key=key,
            revision_number=revision_number,
            blob_sha256=blob_sha,
            seen_at=_canonical_utc(acquisition.response_observed_at),
            observation_state=ObservationState.IDENTICAL_REFETCH.value,
            usable_provenance=usable,
            severity=MutationSeverity.INFO.value,
            registered_at=_canonical_utc(self._clock()),
        )

    # -- declarations (§33-§36) -------------------------------------------------

    def declare_provider_revision(
        self,
        *,
        source_revision_key: str,
        revision_number: int,
        evidence_ref: str,
        declared_at: datetime | None = None,
        declaration_id: str | None = None,
    ) -> RevisionDeclarationRecord:
        """Explicit provider revision/canonical declaration evidence
        (§33-§35).  Never inferred."""
        if revision_number not in self._segment_numbers(source_revision_key):
            raise RevisionNotFound(
                f"declaration targets revision {revision_number} of "
                f"{source_revision_key[:12]}... which does not exist"
            )
        return self._commit_declaration(
            declaration_id=declaration_id
            or f"decl-{len(self._declarations_by_key.get(source_revision_key, [])) + 1}-{revision_number}",
            key=source_revision_key,
            revision_number=revision_number,
            declaration_kind="revision",
            evidence_ref=evidence_ref,
            declared_at=_canonical_utc(declared_at or self._clock()),
        )

    def declare_provider_canonical(
        self,
        *,
        source_revision_key: str,
        revision_number: int,
        evidence_ref: str,
        declared_at: datetime | None = None,
        declaration_id: str | None = None,
    ) -> RevisionDeclarationRecord:
        """Explicit CANONICAL designation (§35): a persisted declaration
        binding source key + revision number + evidence + canonical=true."""
        if revision_number not in self._segment_numbers(source_revision_key):
            raise RevisionNotFound(
                f"canonical declaration targets revision {revision_number} "
                f"of {source_revision_key[:12]}... which does not exist"
            )
        return self._commit_declaration(
            declaration_id=declaration_id
            or f"canon-{len(self._declarations_by_key.get(source_revision_key, [])) + 1}-{revision_number}",
            key=source_revision_key,
            revision_number=revision_number,
            declaration_kind="canonical",
            evidence_ref=evidence_ref,
            declared_at=_canonical_utc(declared_at or self._clock()),
        )

    def _commit_declaration(
        self,
        *,
        declaration_id: str,
        key: str,
        revision_number: int | None,
        declaration_kind: str,
        evidence_ref: str,
        declared_at: str,
    ) -> RevisionDeclarationRecord:
        record = RevisionDeclarationRecord(
            declaration_id=declaration_id,
            source_revision_key=key,
            revision_number=revision_number,
            declaration_kind=declaration_kind,
            evidence_ref=evidence_ref,
            declared_at=declared_at,
            registered_at=_canonical_utc(self._clock()),
        )
        try:
            self._declarations.commit(
                declaration_id, record.model_dump(mode="json")
            )
        except JsonCatalogCorrupt as exc:
            raise SourceRevisionCatalogCorrupt(str(exc)) from exc
        self._declarations_by_key.setdefault(key, []).append(record)
        return record

    def _segment_numbers(self, key: str) -> set[int]:
        return {
            s.revision_number for s in self._segments_by_key.get(key, [])
        }

    # -- materialized reads (§50-§53) ---------------------------------------------

    def get_revision(self, source_revision_key: str, revision_number: int):
        """Materialized frozen SourceRevision view (§50): first_seen from
        segment birth, last_seen materialized from observations, reason and
        state from the birth classification.  The persisted birth record is
        NEVER mutated."""
        for seg in self._segments_by_key.get(source_revision_key, []):
            if seg.revision_number == revision_number:
                last_seen = seg.first_seen_at
                for obs in self._observations_by_key.get(
                    source_revision_key, []
                ):
                    if (
                        obs.revision_number == revision_number
                        and obs.seen_at > last_seen
                    ):
                        last_seen = obs.seen_at
                return SourceRevision(
                    source_revision_key=source_revision_key,
                    revision_number=seg.revision_number,
                    blob_sha256=seg.blob_sha256,
                    first_seen_at=seg.first_seen_at,
                    last_seen_at=last_seen,
                    revision_state=seg.revision_state,
                    revision_reason=seg.revision_reason,
                    first_acquisition_id=seg.first_acquisition_id,
                )
        return None

    def list_revisions(self, source_revision_key: str) -> list["SourceRevision"]:
        """Revision 1..N in revision_number order (§51); identical refetches
        never add segments."""
        segments = sorted(
            self._segments_by_key.get(source_revision_key, []),
            key=lambda s: s.revision_number,
        )
        return [
            rev
            for rev in (
                self.get_revision(source_revision_key, s.revision_number)
                for s in segments
            )
            if rev is not None
        ]

    def list_observations(self, source_revision_key: str) -> list[RevisionObservationRecord]:
        """Every registered observation in deterministic source-observation
        order (§52)."""
        records = sorted(
            self._observations_by_key.get(source_revision_key, []),
            key=lambda o: (o.seen_at, o.acquisition_id),
        )
        segments = {
            s.revision_number: s
            for s in self._segments_by_key.get(source_revision_key, [])
        }
        first = segments.get(1)
        if first is not None:
            synthetic = self._birth_observation_view(first)
            by_id = {r.observation_id: r for r in records}
            by_id.setdefault(synthetic.observation_id, synthetic)
            records = sorted(
                by_id.values(), key=lambda o: (o.seen_at, o.acquisition_id)
            )
        return records

    def revision_for_acquisition(
        self, acquisition_id: str
    ) -> tuple[str, int] | None:
        """Reverse lookup (§53): acquisition → (source key, revision)."""
        binding = self._acquisition_bindings.get(acquisition_id)
        if binding is None:
            segments = [
                s
                for segs in self._segments_by_key.values()
                for s in segs
                if s.first_acquisition_id == acquisition_id
            ]
            if not segments:
                return None
            seg = segments[0]
            return seg.source_revision_key, seg.revision_number
        return binding[0], binding[1]

    # -- resolution (§54-§61) -------------------------------------------------

    def resolve(
        self,
        source_revision_key: str,
        policy: RevisionResolutionMode,
        *,
        revision_number: int | None = None,
    ) -> RevisionResolution:
        """Deterministic revision resolution (§55-§61).  Selection resolves
        VERSION IDENTITY only — never integrity/usability promotion (§62)."""
        segments = sorted(
            self._segments_by_key.get(source_revision_key, []),
            key=lambda s: s.revision_number,
        )
        numbers = [s.revision_number for s in segments]
        policy = RevisionResolutionMode(policy)

        def result(
            selected: list[int],
            *,
            ambiguous: bool = False,
            canonical: int | None = None,
        ) -> RevisionResolution:
            return RevisionResolution(
                source_revision_key=source_revision_key,
                policy=policy.value,
                selected_revision_numbers=selected,
                ambiguous=ambiguous,
                all_revision_numbers=numbers,
                provider_canonical_revision_number=canonical,
            )

        if policy is RevisionResolutionMode.ALL:
            return result(numbers)
        if policy is RevisionResolutionMode.FIRST_SEEN:
            # §57: a revision SELECTION rule, not automatic PIT truth.
            if not numbers:
                raise RevisionNotFound(
                    f"no revisions registered for {source_revision_key[:12]}..."
                )
            return result([numbers[0]])
        if policy is RevisionResolutionMode.LATEST_SEEN:
            # §58: the latest OBSERVED source state, not economic truth.
            if not numbers:
                raise RevisionNotFound(
                    f"no revisions registered for {source_revision_key[:12]}..."
                )
            return result([numbers[-1]])
        if policy is RevisionResolutionMode.EXACT_REVISION:
            if revision_number is None or revision_number < 1:
                raise RevisionConfigurationError(
                    "EXACT_REVISION requires an explicit revision_number >= 1"
                )
            if revision_number not in numbers:
                raise RevisionNotFound(
                    f"revision {revision_number} not found for "
                    f"{source_revision_key[:12]}..."
                )
            return result([revision_number])
        if policy is RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL:
            canonicals: set[int] = set()
            for dec in self._declarations_by_key.get(source_revision_key, []):
                if dec.declaration_kind != "canonical":
                    continue
                if dec.revision_number is None:
                    continue
                canonicals.add(dec.revision_number)
            if not canonicals:
                raise RevisionResolutionUnavailable(
                    "PROVIDER_DECLARED_CANONICAL requires explicit canonical "
                    "declaration evidence; none exists "
                    f"for {source_revision_key[:12]}..."
                )
            if len(canonicals) > 1:
                raise RevisionAmbiguityError(
                    "multiple distinct provider-canonical revisions "
                    f"{sorted(canonicals)} for {source_revision_key[:12]}...; "
                    "no 'latest wins' (I06 §60)"
                )
            return result([next(iter(canonicals))], canonical=next(iter(canonicals)))
        # ERROR_ON_AMBIGUITY (default research-safe behavior, §55).
        if not numbers:
            raise RevisionNotFound(
                f"no revisions registered for {source_revision_key[:12]}..."
            )
        if len(numbers) > 1:
            raise RevisionAmbiguityError(
                f"{len(numbers)} revisions exist for "
                f"{source_revision_key[:12]}...; ERROR_ON_AMBIGUITY never "
                "silently picks latest (I06 §55)"
            )
        return result([numbers[0]])


class SourceRevision(BaseModel):
    """Frozen materialized revision view (§50)."""

    model_config = ConfigDict(frozen=True)

    source_revision_key: str
    revision_number: int
    blob_sha256: str
    first_seen_at: str
    last_seen_at: str
    revision_state: str
    revision_reason: str
    first_acquisition_id: str


__all__ = [
    "IDENTITY_VERSION",
    "MutationSeverity",
    "ObservationState",
    "RevisionAcquisitionSource",
    "RevisionAmbiguityError",
    "RevisionBlobSource",
    "RevisionConfigurationError",
    "RevisionContentCorrupt",
    "RevisionContentUnavailable",
    "RevisionDeclarationRecord",
    "RevisionError",
    "RevisionLockHeld",
    "RevisionNotFound",
    "RevisionObservationConflict",
    "RevisionObservationOrderConflict",
    "RevisionObservationRecord",
    "RevisionPhysicalStore",
    "RevisionResolution",
    "RevisionResolutionMode",
    "RevisionResolutionUnavailable",
    "RevisionSegmentRecord",
    "RevisionSourceIdentityV1",
    "RevisionState",
    "RevisionTemporalAmbiguity",
    "SourceRevision",
    "SourceRevisionCatalogCorrupt",
    "SourceRevisionRegistry",
    "StorageEncoding",
]
