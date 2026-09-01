"""SENSOR-B4-I01/I02 — immutable T0 raw-evidence lake: contracts + identity primitives.

I01 froze the STORAGE CONTRACT vocabulary (models + enums).  I02 freezes HOW
immutable evidence is IDENTIFIED and ADDRESSED: exact-source SHA-256 primitives
(checksums.py) and content-addressed blob keys + safe reversible path encoding
(paths.py).  Neither checkpoint persists anything: no blob writer, no atomic
backend, no manifest repository, no compression engine, no DuckDB/Postgres,
no network.

Dependency direction (frozen):
- storage -> may import frozen provider/base shared contracts (SensorFamily,
  ResumeToken, QualityFlagAcquisition, AdapterEvidenceRef)
- provider adapters MUST NOT import storage

See `evidence/bloc_04/BLOC_04_I01_STORAGE_CONTRACTS_EVIDENCE.md` and
`evidence/bloc_04/BLOC_04_I02_CONTENT_ADDRESSING_EVIDENCE.md`.
"""

from .checksums import (
    Sha256Result,
    checksum_algorithm_from_name,
    compute_checksum,
    sha256_bytes,
    sha256_chunks,
    sha256_file,
    sha256_stream,
    validate_sha256_hex,
    verify_checksum,
)
from .enums import (
    BackupClass,
    ChecksumAlgorithm,
    CoverageState,
    DateBasis,
    DiskPressure,
    IntegrityState,
    ProjectionState,
    RevisionPolicy,
    RevisionState,
    StorageEncoding,
    StorageJobStatus,
    StorageObjectType,
    StoragePriority,
)
from .models import (
    AcquisitionRecord,
    BackupState,
    EvidenceBlob,
    ExportManifest,
    IntegrityCheck,
    PartitionManifest,
    ProjectionLineage,
    RawEvidenceQuery,
    RawEvidenceResult,
    RawNormalizationBatch,
    RawProjectionArtifact,
    RecoveryAction,
    SourceRevision,
    StorageJobState,
    StorageJobTransition,
    StorageQuotaState,
)
from .paths import (
    BLOB_KEY_PREFIX,
    DEFAULT_HASH_PREFIX_LENGTH,
    blob_object_key,
    escape_path_segment,
    projection_object_key,
    resolve_under_root,
    unescape_path_segment,
)

__all__ = [
    # paths / addressing
    "BLOB_KEY_PREFIX",
    "DEFAULT_HASH_PREFIX_LENGTH",
    # models
    "AcquisitionRecord",
    # enums
    "BackupClass",
    "BackupState",
    "ChecksumAlgorithm",
    "CoverageState",
    "DateBasis",
    "DiskPressure",
    "EvidenceBlob",
    "ExportManifest",
    "IntegrityCheck",
    "IntegrityState",
    "PartitionManifest",
    "ProjectionLineage",
    "ProjectionState",
    "RawEvidenceQuery",
    "RawEvidenceResult",
    "RawNormalizationBatch",
    "RawProjectionArtifact",
    "RecoveryAction",
    "RevisionPolicy",
    "RevisionState",
    # checksums / identity primitives
    "Sha256Result",
    "SourceRevision",
    "StorageEncoding",
    "StorageJobState",
    "StorageJobStatus",
    "StorageJobTransition",
    "StorageObjectType",
    "StoragePriority",
    "StorageQuotaState",
    "blob_object_key",
    "checksum_algorithm_from_name",
    "compute_checksum",
    "escape_path_segment",
    "projection_object_key",
    "resolve_under_root",
    "sha256_bytes",
    "sha256_chunks",
    "sha256_file",
    "sha256_stream",
    "unescape_path_segment",
    "validate_sha256_hex",
    "verify_checksum",
]
