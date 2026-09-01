"""SENSOR-B4-I01 — immutable T0 raw-evidence lake: typed storage vocabulary.

This package freezes the STORAGE CONTRACT vocabulary only.  It performs no
persistence, no hashing, no paths, no compression, no manifest repository and
no network.  Those responsibilities belong to later checkpoints (I02+).

Dependency direction (frozen):
- storage -> may import frozen provider/base shared contracts (SensorFamily,
  ResumeToken, QualityFlagAcquisition, AdapterEvidenceRef)
- provider adapters MUST NOT import storage

See `evidence/bloc_04/BLOC_04_I01_STORAGE_CONTRACTS_EVIDENCE.md`.
"""

from .enums import (
    BackupClass,
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

__all__ = [
    # enums
    "BackupClass",
    "CoverageState",
    "DateBasis",
    "DiskPressure",
    "IntegrityState",
    "ProjectionState",
    "RevisionPolicy",
    "RevisionState",
    "StorageEncoding",
    "StorageJobStatus",
    "StorageObjectType",
    "StoragePriority",
    # models
    "AcquisitionRecord",
    "BackupState",
    "EvidenceBlob",
    "ExportManifest",
    "IntegrityCheck",
    "PartitionManifest",
    "ProjectionLineage",
    "RawEvidenceQuery",
    "RawEvidenceResult",
    "RawNormalizationBatch",
    "RawProjectionArtifact",
    "RecoveryAction",
    "SourceRevision",
    "StorageJobState",
    "StorageJobTransition",
    "StorageQuotaState",
]
