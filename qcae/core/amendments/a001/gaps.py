"""A-001 gap taxonomy with ownership routing (amendment §3).

The narrowest applicable gap type is classified before work is routed. QCAE
must not silently reinterpret all failures as capability gaps: an
EXECUTION_FAILURE belongs to the execution/service owner first, and only
becomes QCAE work when evidence shows acquisition/repair/replacement is
required. KNOWLEDGE_GAPs route to Research Mesh, not to QCAE discovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier


class GapType(StrEnum):
    """Institutional gap taxonomy (A-001 §3)."""

    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    CAPABILITY_GAP = "CAPABILITY_GAP"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    INSTITUTIONAL_LEARNING_CANDIDATE = "INSTITUTIONAL_LEARNING_CANDIDATE"
    MIXED_GAP = "MIXED_GAP"


class GapOwner(StrEnum):
    """Owner domains for gap routing (A-001 §1, §3)."""

    RESEARCH_MESH = "RESEARCH_MESH"
    QCAE = "QCAE"
    EXECUTION_SERVICE_OWNER = "EXECUTION_SERVICE_OWNER"
    INSTITUTION_TRANSFORMATION_GOVERNOR = "INSTITUTION_TRANSFORMATION_GOVERNOR"


#: Primary ownership routing per gap type (A-001 §3). MIXED_GAP requires
#: decomposition — it has no single owner by construction.
GAP_OWNERSHIP = {
    GapType.KNOWLEDGE_GAP: GapOwner.RESEARCH_MESH,
    GapType.CAPABILITY_GAP: GapOwner.QCAE,
    GapType.EXECUTION_FAILURE: GapOwner.EXECUTION_SERVICE_OWNER,
    GapType.INSTITUTIONAL_LEARNING_CANDIDATE: GapOwner.INSTITUTION_TRANSFORMATION_GOVERNOR,
}


@dataclass(frozen=True)
class MixedGapDecomposition(SerializableRecord):
    """Decomposition of a MIXED_GAP into separately owned, linked child gaps.

    A-001 §3: "One objective may generate multiple linked gaps. They remain
    separately typed and separately owned." A mixed gap may never be handed to
    a single owner as-is.
    """

    SCHEMA_VERSION = 1

    mixed_gap_id: str
    component_gaps: Tuple["GapRef", ...]

    _NESTED_RECORDS = {"component_gaps": "GapRef"}

    def validate(self) -> None:
        require_identifier(self.mixed_gap_id, "mixed_gap_id")
        if len(self.component_gaps) < 2:
            raise QcaeValidationError(
                "MIXED_GAP decomposition requires at least two component gaps; "
                "a single-owned gap must be typed directly (A-001 §3)"
            )
        if not any(ref.gap_type in (GapType.KNOWLEDGE_GAP, GapType.CAPABILITY_GAP) for ref in self.component_gaps):
            raise QcaeValidationError(
                "MIXED_GAP decomposition must contain at least one "
                "KNOWLEDGE_GAP or CAPABILITY_GAP component (A-001 §3)"
            )
        for ref in self.component_gaps:
            ref.validate()


@dataclass(frozen=True)
class GapRef(SerializableRecord):
    """A typed gap reference: identity + gap type, used in decompositions,
    handoffs, and cross-registry references."""

    SCHEMA_VERSION = 1

    gap_id: str
    gap_type: GapType

    _COERCIONS = {"gap_type": lambda v: coerce_enum(v, GapType)}

    def validate(self) -> None:
        require_identifier(self.gap_id, "gap_id")
        if not isinstance(self.gap_type, GapType):
            raise QcaeValidationError(
                f"gap_type must be a GapType member, got {self.gap_type!r}"
            )
