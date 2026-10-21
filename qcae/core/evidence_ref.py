"""EvidenceRef — a reference to durable evidence supporting a claim.

Canon Book I 0.4. Evidence lives in durable artifacts, not model context
(0.4.1). An EvidenceRef anchors a claim to an artifact identity plus the
evidence class it supplies (0.4.2), optionally with verification provenance.

The artifact digest is the anchor: content-addressed, revision-scoped, never
silently rewritten (0.4.3, 0.4.7). LLM interpretation is analysis, not proof,
so E0-class refs never satisfy evidence gates on their own (0.4.5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_hex_hash,
    require_identifier,
    require_non_empty_str,
)
from qcae.core.vocabulary import EvidenceClass


@dataclass(frozen=True)
class EvidenceRef(SerializableRecord):
    SCHEMA_VERSION = 1

    # Immutable artifact identity (sha256 over canonical artifact bytes/metadata).
    artifact_digest: str
    evidence_class: EvidenceClass

    # What this evidence is about: stable ID of the claim's subject
    # (atom, candidate, component, relationship, decision...).
    subject_id: str

    # Revision scope (canon 0.4.7): the reviewed revision this evidence covers.
    revision: str = ""

    # Where the artifact can be retrieved by the evidence store (P1 binds this
    # to the physical store; the digest is the durable identity).
    locator: str = ""
    collected_at: str = ""
    collected_by: str = ""

    _COERCIONS = {"evidence_class": lambda v: coerce_enum(v, EvidenceClass)}

    def validate(self) -> None:
        require_hex_hash(self.artifact_digest, "artifact_digest", min_length=8)
        if not isinstance(self.evidence_class, EvidenceClass):
            raise QcaeValidationError(
                f"evidence_class must be an EvidenceClass member, got {self.evidence_class!r}"
            )
        require_identifier(self.subject_id, "subject_id")
        if self.locator:
            require_non_empty_str(self.locator, "locator")
        if self.collected_by:
            require_non_empty_str(self.collected_by, "collected_by")


def make_evidence_ref(**kwargs) -> EvidenceRef:
    """Build and validate an evidence ref in one call."""
    ref = EvidenceRef(**kwargs)
    ref.validate()
    return ref
