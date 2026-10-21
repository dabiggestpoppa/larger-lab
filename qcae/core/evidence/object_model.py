"""Evidence object model — Book IV 9.1.

Two separate dimensions, never conflated:

- ``EvidenceObjectType`` — what *kind* of evidence object this is
  (source anchor, test result, claim, ...).
- ``EvidenceClass`` (Book I 0.4.2, E0–E9) — how strong its verification
  standing is. An object's type never implies its strength.

Raw evidence and interpretation remain separate (9.1 Raw vs Interpretation):
an EvidenceArtifact stores observed facts; interpretation is a linked
EvidenceArtifact of type CLAIM/CONTRADICTION/UNCERTAINTY whose raw
counterpart is recorded via lineage (P1-C04), never by rewriting the raw
record. History is append-oriented: corrections supersede or contradict via
explicit lineage edges, never by mutating historical conclusions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_enum,
    require_hex_hash,
    require_identifier,
    require_non_empty_str,
    require_str_list,
)
from qcae.core.vocabulary import EvidenceClass

__all__ = [
    "EvidenceObjectType",
    "FreshnessState",
    "ScopeDimensions",
    "EvidenceArtifact",
    "RAW_OBJECT_TYPES",
    "INTERPRETATION_OBJECT_TYPES",
    "make_evidence_artifact",
]


class EvidenceObjectType(str, Enum):
    """What kind of evidence object this is (Book IV 9.1)."""

    SOURCE_ANCHOR = "SOURCE_ANCHOR"
    ARTIFACT = "ARTIFACT"
    OBSERVATION = "OBSERVATION"
    TEST_RESULT = "TEST_RESULT"
    BENCHMARK_RESULT = "BENCHMARK_RESULT"
    DATASET_RECORD = "DATASET_RECORD"
    CLAIM = "CLAIM"
    CONTRADICTION = "CONTRADICTION"
    DECISION = "DECISION"
    AUTHORITY_RECORD = "AUTHORITY_RECORD"
    UNCERTAINTY = "UNCERTAINTY"


class FreshnessState(str, Enum):
    """Reusability standing of a belief/evidence object (Book IV 9.6)."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"


#: Object types that are observed facts rather than evaluator conclusions.
RAW_OBJECT_TYPES = frozenset(
    {
        EvidenceObjectType.SOURCE_ANCHOR,
        EvidenceObjectType.ARTIFACT,
        EvidenceObjectType.OBSERVATION,
        EvidenceObjectType.TEST_RESULT,
        EvidenceObjectType.BENCHMARK_RESULT,
        EvidenceObjectType.DATASET_RECORD,
    }
)
#: Object types that are evaluator conclusions derived from raw evidence.
INTERPRETATION_OBJECT_TYPES = frozenset(
    {EvidenceObjectType.CLAIM, EvidenceObjectType.CONTRADICTION, EvidenceObjectType.UNCERTAINTY}
)


@dataclass(frozen=True)
class ScopeDimensions(SerializableRecord):
    """Structured, explicit scope keys a belief is bounded by (Book IV 9.6).

    Not every dimension applies to every record; inapplicable dimensions stay
    empty strings. Structured so later monitoring/revalidation can match them
    mechanically (P1 stores the invalidation dependencies; monitoring is P11).
    """

    SCHEMA_VERSION = 1

    implementation_revision: str = ""
    contract_version: str = ""
    environment: str = ""
    platform: str = ""
    dataset: str = ""
    market_regime: str = ""
    instrument: str = ""
    timeframe: str = ""
    acquisition_form: str = ""
    policy_version: str = ""
    research_mesh_evidence_version: str = ""
    external_provider_revision: str = ""

    def validate(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value is None or not isinstance(value, str):
                raise QcaeValidationError(
                    f"scope dimension {name!r} must be a string or empty, "
                    f"got {value!r}"
                )
        if all(not getattr(self, name) for name in self.__dataclass_fields__):
            raise QcaeValidationError(
                "scope must set at least one dimension; unscoped beliefs are not allowed"
            )


@dataclass(frozen=True)
class EvidenceArtifact(SerializableRecord):
    """A durable, provenance-linked evidence object (Book IV 9.1).

    Identity: ``evidence_id`` is the stable handle; ``integrity_digest`` is
    the sha256 over this record's own canonical payload (content addressing
    of the metadata), so any tampering with recorded fields is detectable.

    Raw vs interpretation: raw observation records carry the artifact
    reference and no interpretation; interpretation records must cite their
    raw counterpart through lineage (``derived_from``) recorded by the
    RelationshipRegistry — enforced at service level, not here.
    """

    SCHEMA_VERSION = 1

    evidence_id: str
    subject_id: str
    evidence_object_type: EvidenceObjectType
    evidence_class: EvidenceClass
    artifact_digest: str
    producer: str
    created_at: str
    scope: ScopeDimensions
    freshness: FreshnessState = FreshnessState.CURRENT
    revision: str = ""
    locator: str = ""
    collected_at: str = ""
    collected_by: str = ""
    summary: str = ""
    interpretation_status: str = ""
    valid_from: str = ""
    valid_until: str = ""
    stale_at: str = ""
    stale_reason: str = ""
    revalidation_triggers: Tuple[str, ...] = ()
    data_classification: str = "PUBLIC"
    rights_status: str = ""
    external_owner_domain: str = ""
    superseded_by: str = ""

    _COERCIONS = {
        "evidence_object_type": lambda v: coerce_enum(v, EvidenceObjectType),
        "evidence_class": lambda v: coerce_enum(v, EvidenceClass),
        "freshness": lambda v: coerce_enum(v, FreshnessState),
        "revalidation_triggers": tuple,  # JSON arrays -> tuple for canonical equality
    }

    _NESTED_RECORDS = {"scope": ScopeDimensions}

    def validate(self) -> None:
        require_identifier(self.evidence_id, "evidence_id")
        require_identifier(self.subject_id, "subject_id")
        require_enum(self.evidence_object_type, EvidenceObjectType, "evidence_object_type")
        require_enum(self.evidence_class, EvidenceClass, "evidence_class")
        require_hex_hash(self.artifact_digest, "artifact_digest", min_length=8)
        require_non_empty_str(self.producer, "producer")
        require_non_empty_str(self.created_at, "created_at")
        self.scope.validate()
        require_str_list(self.revalidation_triggers, "revalidation_triggers")
        if self.locator:
            require_non_empty_str(self.locator, "locator")
        if self.summary:
            require_non_empty_str(self.summary, "summary")
        if self.interpretation_status:
            require_non_empty_str(self.interpretation_status, "interpretation_status")
        if self.freshness in (FreshnessState.STALE, FreshnessState.HISTORICAL_ONLY):
            require_non_empty_str(self.stale_reason, "stale_reason")
        if self.data_classification:
            require_non_empty_str(self.data_classification, "data_classification")
        # Interpretation objects must not masquerade as raw observation with
        # no provenance of what they interpret.
        if self.evidence_object_type in INTERPRETATION_OBJECT_TYPES and not self.interpretation_status:
            raise QcaeValidationError(
                f"interpretation object type {self.evidence_object_type.value} requires "
                "interpretation_status describing the evaluator conclusion"
            )
        # Superseded evidence keeps its identity but points forward.
        if self.superseded_by:
            require_identifier(self.superseded_by, "superseded_by")
            if self.superseded_by == self.evidence_id:
                raise QcaeValidationError("evidence cannot supersede itself")
        if self.valid_until and self.valid_from and self.valid_until < self.valid_from:
            raise QcaeValidationError("valid_until precedes valid_from")


def make_evidence_artifact(**kwargs) -> EvidenceArtifact:
    """Build and validate an evidence artifact in one call."""
    artifact = EvidenceArtifact(**kwargs)
    artifact.validate()
    return artifact
