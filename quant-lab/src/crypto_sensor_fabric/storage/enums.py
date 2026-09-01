"""SENSOR-B4-I01 — frozen storage enum vocabularies.

Every member set below is frozen by the Bloc 4 planning books
(`bloc_04/07_BLOC_04_FREEZE_MANIFEST.md` §5–§6 and the companion architecture
docs).  Changing a member set is a schema-breaking change.

Revision-policy reconciliation (freeze manifest §4): the older partition-doc
vocabulary `FIRST_ACQUIRED` / `LATEST_ACQUIRED` is NOT used.  The final frozen
revision policy is `FIRST_SEEN` / `LATEST_SEEN` (plus the other members below).
No aliasing between the two sets is introduced.

Integrity and coverage remain SEPARATE enum classes: a partial partition may
contain verified blobs; a complete-looking partition may still have integrity
failure.
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class IntegrityState(_StrEnum):
    """Frozen integrity vocabulary (freeze manifest §5).  Not a goodness score."""

    UNVERIFIED = "UNVERIFIED"
    LOCAL_HASH_VERIFIED = "LOCAL_HASH_VERIFIED"
    PROVIDER_HASH_VERIFIED = "PROVIDER_HASH_VERIFIED"
    QUARANTINED_INTEGRITY_FAILURE = "QUARANTINED_INTEGRITY_FAILURE"
    MISSING_BLOB = "MISSING_BLOB"
    PROJECTION_INVALID = "PROJECTION_INVALID"


class CoverageState(_StrEnum):
    """Frozen coverage vocabulary (freeze manifest §5).  No numeric-zero semantics."""

    COMPLETE_SOURCE_BOUNDARY = "COMPLETE_SOURCE_BOUNDARY"
    PARTIAL = "PARTIAL"
    KNOWN_GAP = "KNOWN_GAP"
    EMPTY_CONFIRMED = "EMPTY_CONFIRMED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    FAILED = "FAILED"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    HISTORY_UNAVAILABLE = "HISTORY_UNAVAILABLE"
    QUARANTINED = "QUARANTINED"
    REVISION_CONFLICT = "REVISION_CONFLICT"


class RevisionPolicy(_StrEnum):
    """Frozen raw-query revision policy (freeze manifest §6).

    Default research-safe behavior is ERROR_ON_AMBIGUITY: never silently pick
    a revision when the source evidence is ambiguous.
    """

    ERROR_ON_AMBIGUITY = "ERROR_ON_AMBIGUITY"
    ALL = "ALL"
    FIRST_SEEN = "FIRST_SEEN"
    LATEST_SEEN = "LATEST_SEEN"
    EXACT_REVISION = "EXACT_REVISION"
    PROVIDER_DECLARED_CANONICAL = "PROVIDER_DECLARED_CANONICAL"


class RevisionState(_StrEnum):
    """Frozen source-revision state (03 integrity/revision doc §15–§17).

    Different bytes must remain representable as distinct revisions; there is
    NO "latest wins" assumption baked into the vocabulary.
    """

    STABLE = "STABLE"
    IDENTICAL_REFETCH = "IDENTICAL_REFETCH"
    SOURCE_MUTATION = "SOURCE_MUTATION"
    PROVIDER_DECLARED_REVISION = "PROVIDER_DECLARED_REVISION"
    UNKNOWN_REVISION = "UNKNOWN_REVISION"


class ProjectionState(_StrEnum):
    """Frozen T0B projection lifecycle (05 query/replay doc §8).

    Invalid projections remain historical records; no deletion implication.
    """

    VALID = "VALID"
    SUPERSEDED = "SUPERSEDED"
    INVALID_PARSER = "INVALID_PARSER"
    INVALID_SOURCE = "INVALID_SOURCE"
    INVALID_LINEAGE = "INVALID_LINEAGE"


class StorageEncoding(_StrEnum):
    """Allowed LOCAL storage wrapper encodings (freeze manifest §7).

    The wrapper must NOT change the source hash definition: blob_sha256 always
    hashes the exact provider-source bytes BEFORE optional wrapper compression.
    Compression itself is implemented later (I02+), not in I01.
    """

    NONE = "NONE"
    ZSTD = "ZSTD"


class DateBasis(_StrEnum):
    """Date-basis semantics for partition/query windows (02 partition doc §5).

    Never silently use ingestion date as event date.
    """

    EVENT_TIME = "EVENT_TIME"
    PROVIDER_FILE_DATE = "PROVIDER_FILE_DATE"
    SNAPSHOT_TIME = "SNAPSHOT_TIME"
    UNKNOWN = "UNKNOWN"


class StoragePriority(_StrEnum):
    """Frozen storage priority classes (freeze manifest §3).

    Storage POLICY only — never a market-importance score.
    """

    P0 = "P0"  # CRITICAL_PERMANENT
    P1 = "P1"  # HIGH_VALUE_PERMANENT_COMPRESS
    P2 = "P2"  # HIGH_VOLUME_SELECTIVE
    P3 = "P3"  # REBUILDABLE


class DiskPressure(_StrEnum):
    """Frozen disk-pressure states (freeze manifest §4).

    The enum does NOT bake the 70/85/95 thresholds; threshold policy/config
    comes later (I09 quota logic).
    """

    NORMAL = "NORMAL"
    WATCH = "WATCH"
    CONSTRAINED = "CONSTRAINED"
    CRITICAL = "CRITICAL"


class BackupClass(_StrEnum):
    """Frozen backup evidence classes (freeze manifest §5/F18, 04 doc §13).

    No object may call itself fully backed up merely because manifest metadata
    exists.
    """

    UNBACKED = "UNBACKED"
    MANIFEST_BACKED = "MANIFEST_BACKED"
    SECOND_COPY_VERIFIED = "SECOND_COPY_VERIFIED"
    OFFSITE_VERIFIED = "OFFSITE_VERIFIED"


class StorageJobStatus(_StrEnum):
    """Frozen storage-job state machine vocabulary (03 doc §8, freeze §2).

    I01 provides the typed vocabulary only; transition enforcement arrives
    with durable job state (I07).
    """

    PLANNED = "PLANNED"
    ACQUIRING = "ACQUIRING"
    RAW_STAGED = "RAW_STAGED"
    RAW_COMMITTED = "RAW_COMMITTED"
    PROJECTION_PENDING = "PROJECTION_PENDING"
    PROJECTION_COMMITTED = "PROJECTION_COMMITTED"
    MANIFEST_COMMITTED = "MANIFEST_COMMITTED"
    CHECKPOINT_ADVANCED = "CHECKPOINT_ADVANCED"
    COMPLETE = "COMPLETE"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    QUARANTINED = "QUARANTINED"


class StorageObjectType(_StrEnum):
    """Typed object identity for integrity checks / recovery actions.

    Not one of the frozen "exact value" vocabularies above; a small typed
    vocabulary so IntegrityCheck.object_type and RecoveryAction.object_type
    are closed strings rather than free text.
    """

    EVIDENCE_BLOB = "EVIDENCE_BLOB"
    ACQUISITION_RECORD = "ACQUISITION_RECORD"
    RAW_PROJECTION = "RAW_PROJECTION"
    PARTITION_MANIFEST = "PARTITION_MANIFEST"
    SOURCE_REVISION = "SOURCE_REVISION"
    STORAGE_JOB = "STORAGE_JOB"
    EXPORT_MANIFEST = "EXPORT_MANIFEST"
