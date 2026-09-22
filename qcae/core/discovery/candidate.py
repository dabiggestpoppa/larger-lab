"""Canonical (merged) discovery candidate — canon 2.1.12.

"The same project may appear through GitHub, GitHubDaily, package registries,
papers, and web search. QCAE should merge discovery paths into one canonical
candidate while preserving all source paths. Do not count repeated discovery as
independent evidence of capability quality."

The laws that follow from that paragraph, all enforced structurally:

- **Every path is preserved.** ``merged_locators``/``lead_ids`` keep all
  discovery paths, so provenance survives the merge instead of collapsing to the
  winner.
- **Identity is content-addressed, not counted.** ``canonical_key`` is derived
  from the normalized locator and kind, so merging is deterministic and no
  counter or registry state can change a candidate's identity between runs.
- **Duplicates are not corroboration.** ``independent_path_count`` counts
  distinct *source classes* (a GitHub hit and a package-registry hit are not
  independent technical proof either, which is why the ranking layer still
  treats it as an investigation-priority signal only), and
  ``duplicate_path_count`` is reported separately as duplication, never as
  evidence of quality.
- **A merged candidate is still unverified.** ``claim_verification`` is always
  ``DISCOVERED``: merging metadata cannot promote a claim (canon 2.7.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from qcae.core.discovery.lead import CandidateKind
from qcae.core.discovery.plan import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum, coerce_enum_tuple
from qcae.core.validation import (
    require_enum,
    require_enum_tuple,
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
    require_str_list,
)
from qcae.core.vocabulary import VerificationLevel

__all__ = ["CanonicalCandidate", "make_canonical_candidate"]


@dataclass(frozen=True)
class CanonicalCandidate(SerializableRecord):
    """One canonical candidate backed by every discovery path that found it."""

    SCHEMA_VERSION = 1

    canonical_id: str
    canonical_key: str
    candidate_kind: CandidateKind
    canonical_locator: str
    merged_locators: Tuple[str, ...]
    lead_ids: Tuple[str, ...]
    source_classes: Tuple[SourceClass, ...]
    claims_atoms: Tuple[str, ...]
    ready_lead_ids: Tuple[str, ...] = ()
    retrieved_revisions: Tuple[str, ...] = ()
    license_claims: Tuple[str, ...] = ()
    constraint_conflicts: Tuple[str, ...] = ()
    languages: Tuple[str, ...] = ()
    novelty_family: str = ""
    notes: str = ""

    _COERCIONS = {
        "candidate_kind": lambda v: coerce_enum(v, CandidateKind),
        "merged_locators": tuple,
        "lead_ids": tuple,
        "source_classes": lambda v: coerce_enum_tuple(v, SourceClass),
        "claims_atoms": tuple,
        "ready_lead_ids": tuple,
        "retrieved_revisions": tuple,
        "license_claims": tuple,
        "constraint_conflicts": tuple,
        "languages": tuple,
    }

    def validate(self) -> None:
        require_identifier(self.canonical_id, "canonical_id")
        require_non_empty_str(self.canonical_key, "canonical_key")
        require_enum(self.candidate_kind, CandidateKind, "candidate_kind")
        require_non_empty_str(self.canonical_locator, "canonical_locator")

        require_str_list(self.merged_locators, "merged_locators")
        if not self.merged_locators:
            raise QcaeValidationError(
                "a canonical candidate must preserve at least one discovery path "
                "(canon 2.1.12)"
            )
        require_no_duplicates(self.merged_locators, "merged_locators")
        if self.canonical_locator not in self.merged_locators:
            raise QcaeValidationError(
                "the canonical locator must be one of the preserved discovery paths"
            )

        require_str_list(self.lead_ids, "lead_ids")
        if not self.lead_ids:
            raise QcaeValidationError(
                "a canonical candidate must cite the leads that produced it; "
                "candidate identity is not allowed to appear without provenance"
            )
        require_no_duplicates(self.lead_ids, "lead_ids")
        require_no_duplicates(self.ready_lead_ids, "ready_lead_ids")
        unknown_ready = sorted(set(self.ready_lead_ids) - set(self.lead_ids))
        if unknown_ready:
            raise QcaeValidationError(
                f"ready_lead_ids names leads this candidate does not carry: {unknown_ready}"
            )

        require_enum_tuple(self.source_classes, SourceClass, "source_classes")
        if not self.source_classes:
            raise QcaeValidationError(
                "a canonical candidate must record the source classes that found it "
                "(canon 2.1.12 preserves discovery paths)"
            )
        require_no_duplicates([sc.value for sc in self.source_classes], "source_classes")

        require_str_list(self.claims_atoms, "claims_atoms")
        if not self.claims_atoms:
            raise QcaeValidationError(
                "a candidate with no capability claim is not an acquisition object "
                "(canon 0.2.1)"
            )
        require_no_duplicates(self.claims_atoms, "claims_atoms")
        for name in ("retrieved_revisions", "license_claims", "constraint_conflicts",
                     "languages"):
            require_str_list(getattr(self, name), name)
        require_no_duplicates(self.retrieved_revisions, "retrieved_revisions")

    # -- derived standing ---------------------------------------------------

    @property
    def claim_verification(self) -> VerificationLevel:
        """Always ``DISCOVERED``: merging discovery paths is not verification."""
        return VerificationLevel.DISCOVERED

    @property
    def duplicate_path_count(self) -> int:
        """Discovery observations beyond the first (canon 2.1.12 duplication).

        Canon 2.1.12: "Do not count repeated discovery as independent evidence
        of capability quality." This counter exists so that repetition is
        *visible* and scored as duplication, never as corroboration.
        """
        return max(0, len(self.lead_ids) - 1)

    @property
    def distinct_locator_count(self) -> int:
        """How many distinct locators were merged into this candidate."""
        return len(self.merged_locators)

    @property
    def independent_path_count(self) -> int:
        """Distinct source classes — an investigation-priority signal only.

        Canon 2.1.12 explicitly refuses to treat repeated discovery as independent
        evidence of capability quality, so this never feeds a verification state.
        """
        return len(self.source_classes)

    @property
    def deeper_intelligence_ready(self) -> bool:
        """Whether any contributing lead carried an immutable, complete anchor."""
        return bool(self.ready_lead_ids)

    @property
    def has_constraint_conflicts(self) -> bool:
        """Whether any contributing lead reported an obvious hard-constraint conflict."""
        return bool(self.constraint_conflicts)


def make_canonical_candidate(**kwargs) -> CanonicalCandidate:
    """Build and validate a canonical candidate in one call."""
    candidate = CanonicalCandidate(**kwargs)
    candidate.validate()
    return candidate
