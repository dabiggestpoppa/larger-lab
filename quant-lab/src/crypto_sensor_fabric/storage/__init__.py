"""SENSOR-B4-I01/I02/I03/I04 — immutable T0 raw-evidence lake storage surface.

- I01 froze the STORAGE CONTRACT vocabulary (models + enums).
- I02 froze HOW immutable evidence is IDENTIFIED and ADDRESSED: exact-source
  SHA-256 primitives (checksums.py) and content-addressed blob keys + safe
  reversible path encoding (paths.py).
- I03 implements the ATOMIC FILESYSTEM BACKEND: streaming NONE/ZSTD wrapper
  (compression.py), generic no-clobber durability primitives (atomic.py) and
  the immutable ``LocalBlobStore`` put/exists/open/verify surface
  (blob_store.py) — commit sequence through parent-directory fsync only.
- I04 implements the DURABLE ACQUISITION + MANIFEST CATALOG: immutable
  PyArrow Parquet catalog fragments with durable metadata for EvidenceBlob
  and AcquisitionRecord (catalog.py), and append-only PartitionManifest
  versions with a transactional current pointer, partition-scoped writer
  locks and expected-current CAS (manifests.py).

NOT implemented: T0B projections (I05), recovery scanner (I08), DuckDB/Postgres,
resume advancement, network.

Dependency direction (frozen):
- storage -> may import frozen provider/base shared contracts (SensorFamily,
  ResumeToken, QualityFlagAcquisition, AdapterEvidenceRef)
- provider adapters MUST NOT import storage

Fault hooks / operation recorders / fsync helpers are test seams inside
`atomic.py` and are intentionally NOT part of this public export surface.

See `evidence/bloc_04/` for the checkpoint evidence files.
"""

from .atomic import (
    AtomicPublishError,
    AtomicPublishTargetExists,
    ComponentTooLong,
    CrossFilesystemAtomicityError,
    DurabilityUnsupported,
)
from .blob_store import (
    BlobIntegrityError,
    BlobMissing,
    BlobPutResult,
    ExistingBlobIntegrityConflict,
    InvalidStorageRoot,
    LocalBlobStore,
    ProviderChecksumMismatch,
    PutDisposition,
    StagedVerificationError,
    StagingWriteError,
    UnsafeObjectKey,
)
from .catalog import (
    ACQUISITION_SCHEMA,
    AcquisitionIdentityConflict,
    AcquisitionNotFound,
    AcquisitionRepository,
    BLOB_SCHEMA,
    BlobMetadataConflict,
    BlobMetadataNotFound,
    BlobMetadataRepository,
    BlobStorageKey,
    CatalogDurabilityError,
    CatalogError,
    CatalogFragmentReceipt,
    CatalogIntegrityError,
    CatalogNotFound,
    DanglingBlobReference,
    LocalEvidenceCatalog,
    ProjectionReferenceUnavailable,
    canonical_nested_json,
    model_canonical_json,
    publish_immutable_fragment,
    read_fragment,
    resolve_catalog_root,
)
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
from .compression import EncodeResult, encode_source_stream, iter_decode_stored
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
from .manifests import (
    CurrentPointerCorrupt,
    CurrentPointerDangling,
    MANIFEST_SCHEMA,
    ManifestAppendResult,
    ManifestCASConflict,
    ManifestDisposition,
    ManifestIdentityConflict,
    ManifestLockHeld,
    ManifestNotFound,
    ManifestVersionConflict,
    PartitionCurrentPointer,
    PartitionManifestRepository,
    PointerFaultPoint,
    RaisePointerFaultHook,
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
    blob_object_key,
    escape_path_segment,
    projection_object_key,
    resolve_under_root,
    unescape_path_segment,
)

__all__ = [
    # catalog schemas
    "ACQUISITION_SCHEMA",
    "BLOB_SCHEMA",
    "MANIFEST_SCHEMA",
    # catalog repositories + errors
    "AcquisitionIdentityConflict",
    "AcquisitionNotFound",
    "AcquisitionRepository",
    "BlobMetadataConflict",
    "BlobMetadataNotFound",
    "BlobMetadataRepository",
    "BlobStorageKey",
    "CatalogDurabilityError",
    "CatalogError",
    "CatalogFragmentReceipt",
    "CatalogIntegrityError",
    "CatalogNotFound",
    "CurrentPointerCorrupt",
    "CurrentPointerDangling",
    "DanglingBlobReference",
    "LocalEvidenceCatalog",
    "ManifestAppendResult",
    "ManifestCASConflict",
    "ManifestDisposition",
    "ManifestIdentityConflict",
    "ManifestLockHeld",
    "ManifestNotFound",
    "ManifestVersionConflict",
    "PartitionCurrentPointer",
    "PartitionManifestRepository",
    "PointerFaultPoint",
    "ProjectionReferenceUnavailable",
    "RaisePointerFaultHook",
    "canonical_nested_json",
    "model_canonical_json",
    "publish_immutable_fragment",
    "read_fragment",
    "resolve_catalog_root",
    # paths / addressing
    "BLOB_KEY_PREFIX",
    # models
    "AcquisitionRecord",
    # atomic durability errors
    "AtomicPublishError",
    "AtomicPublishTargetExists",
    # enums
    "BackupClass",
    "BackupState",
    "BlobIntegrityError",
    "BlobMissing",
    "BlobPutResult",
    "ChecksumAlgorithm",
    "ComponentTooLong",
    "CoverageState",
    "CrossFilesystemAtomicityError",
    "DateBasis",
    "DiskPressure",
    "DurabilityUnsupported",
    "EncodeResult",
    "EvidenceBlob",
    "ExistingBlobIntegrityConflict",
    "ExportManifest",
    "IntegrityCheck",
    "IntegrityState",
    "InvalidStorageRoot",
    "LocalBlobStore",
    "PartitionManifest",
    "ProjectionLineage",
    "ProjectionState",
    "ProviderChecksumMismatch",
    "PutDisposition",
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
    "StagedVerificationError",
    "StagingWriteError",
    "StorageEncoding",
    "StorageJobState",
    "StorageJobStatus",
    "StorageJobTransition",
    "StorageObjectType",
    "StoragePriority",
    "StorageQuotaState",
    "UnsafeObjectKey",
    "blob_object_key",
    "checksum_algorithm_from_name",
    "compute_checksum",
    "encode_source_stream",
    "escape_path_segment",
    "iter_decode_stored",
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
