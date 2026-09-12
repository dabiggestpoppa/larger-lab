"""Core evidence domain records (Book IV 9.1, 9.6)."""

from qcae.core.evidence.object_model import (
    INTERPRETATION_OBJECT_TYPES,
    RAW_OBJECT_TYPES,
    EvidenceArtifact,
    EvidenceObjectType,
    FreshnessState,
    ScopeDimensions,
    make_evidence_artifact,
)

__all__ = [
    "EvidenceArtifact",
    "EvidenceObjectType",
    "FreshnessState",
    "ScopeDimensions",
    "RAW_OBJECT_TYPES",
    "INTERPRETATION_OBJECT_TYPES",
    "make_evidence_artifact",
]
