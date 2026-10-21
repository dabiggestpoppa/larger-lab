"""Candidate — a particular implementation proposed to satisfy an atom or contract.

Canon Book I 1.3.3 (Implementation Candidate) and 0.5.5: candidate status means
only "this source may implement some or all of the capability"; it implies no
trust. Claims carry their own VerificationLevel and are never silently upgraded
(canon 0.2.2: no claim may silently upgrade itself into verified fact).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_str_list,
)
from qcae.core.vocabulary import VerificationLevel


class CandidateSourceKind(StrEnum):
    """Where the candidate implementation came from (canon 1.3.3 entity classes)."""

    INTERNAL_CODE = "INTERNAL_CODE"
    REPOSITORY = "REPOSITORY"
    PACKAGE = "PACKAGE"
    SERVICE = "SERVICE"
    SPECIFICATION = "SPECIFICATION"
    PAPER = "PAPER"


@dataclass(frozen=True)
class Candidate(SerializableRecord):
    SCHEMA_VERSION = 1

    candidate_id: str
    name: str
    source_kind: CandidateSourceKind

    # Stable reference to the source container (repo owner/name@revision,
    # package ecosystem/name/version, paper DOI/arXiv ID, internal path).
    # External identifiers are attributes, never identity (canon 1.3.16).
    source_ref: str = ""
    revision: str = ""

    # What this candidate claims to implement, and how far that claim is
    # verified. Scope: atom IDs, or "CAP-...:contract" for whole-contract claims.
    claims_atoms: Tuple[str, ...] = ()
    claim_verification: VerificationLevel = VerificationLevel.DISCOVERED

    discovered_via: str = ""
    notes: str = ""

    _COERCIONS = {
        "source_kind": lambda v: coerce_enum(v, CandidateSourceKind),
        "claim_verification": lambda v: coerce_enum(v, VerificationLevel),
    }

    def validate(self) -> None:
        require_identifier(self.candidate_id, "candidate_id")
        require_non_empty_str(self.name, "name")
        if not isinstance(self.source_kind, CandidateSourceKind):
            raise QcaeValidationError(
                f"source_kind must be a CandidateSourceKind member, got {self.source_kind!r}"
            )
        if self.source_kind == CandidateSourceKind.INTERNAL_CODE:
            if not self.source_ref:
                raise QcaeValidationError(
                    "internal candidates must reference their internal source path"
                )
        if not self.claims_atoms:
            raise QcaeValidationError(
                "candidate must claim at least one atom or contract scope; a "
                "candidate with no capability claim is not an acquisition object "
                "(canon 0.2.1: capability is the acquisition object)"
            )
        require_str_list(self.claims_atoms, "claims_atoms")
        for ref in self.claims_atoms:
            require_identifier(ref, "claims_atoms entry")
        if not isinstance(self.claim_verification, VerificationLevel):
            raise QcaeValidationError(
                f"claim_verification must be a VerificationLevel member, "
                f"got {self.claim_verification!r}"
            )
        if self.claim_verification in (
            VerificationLevel.CONTRACT_VERIFIED,
            VerificationLevel.DOMAIN_VERIFIED,
        ) and not self.revision:
            raise QcaeValidationError(
                "contract/domain-verified claims must anchor to an immutable "
                "revision (canon 0.4.3: a moving branch name is not enough)"
            )


def make_candidate(**kwargs) -> Candidate:
    """Build and validate a candidate in one call."""
    candidate = Candidate(**kwargs)
    candidate.validate()
    return candidate
