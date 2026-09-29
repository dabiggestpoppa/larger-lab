"""Book 5 provenance adapter over the accepted Book 2 claim/evidence engines.

Book 5 owns no epistemic state machine and defines no new claim states. Every
canonical Book 5 economic fact resolves through the accepted Book 2
claim/evidence stores exactly as Book 4 does (single epistemic engine,
Constitution v0.2 §6/§13; ratified Book 5 plan v0.3 "Book 2 dependence").
"""

from __future__ import annotations


from .claims import Claim, ClaimStore, can_promote_to_graph
from .dependency_provenance import require_str_hashable
from .evidence import EvidenceStore


class Book5ProvenanceError(ValueError):
    """A Book 5 record cannot be canonical under accepted Book 2 truth."""


class Book5Provenance:
    """Fail-closed resolver; Book 5 owns no epistemic state machine.

    Mirrors the accepted Book 4 adapter semantics (single epistemic engine):
    claim refs must be canonical strings, claims must exist, be graph-
    promotable in their current state, and carry attached evidence. For
    quantitative records the claim proposition must carry the economics
    qualifier so unrelated claims cannot support an economic fact.
    """

    def __init__(self, claim_store: ClaimStore, evidence_store: EvidenceStore) -> None:
        self.claim_store = claim_store
        self.evidence_store = evidence_store

    def resolve_claim(
        self,
        claim_ref: object,
        *,
        expected_claim: Claim | None = None,
        require_current: bool = True,
    ) -> Claim:
        ref = require_str_hashable(claim_ref, role="book5 claim_ref")
        try:
            canonical = self.claim_store.require(ref)
        except KeyError as exc:
            raise Book5ProvenanceError(f"unknown claim ID {ref}") from exc
        if expected_claim is not None and canonical != expected_claim:
            raise Book5ProvenanceError(f"forged or detached claim object {ref}")
        if require_current and not can_promote_to_graph(canonical, self.claim_store):
            raise Book5ProvenanceError(
                f"claim {ref} is not canonical current graph-promotable "
                f"({canonical.claim_state.value})"
            )
        for evidence_ref in canonical.evidence_refs:
            try:
                self.evidence_store.require(evidence_ref)
            except KeyError as exc:
                raise Book5ProvenanceError(
                    f"claim {ref} has detached evidence {evidence_ref}"
                ) from exc
        return canonical

    def resolve_economics_claim(self, claim_ref: object, *, qualifier: str) -> Claim:
        """Resolve a canonical claim that specifically asserts ``qualifier``.

        A generic canonical claim is never accepted as support for a Book 5
        economic fact; the claim proposition must carry the qualifier.
        """

        claim = self.resolve_claim(claim_ref)
        if claim.proposition.qualifier != qualifier:
            raise Book5ProvenanceError(
                f"claim {ref_text(claim)} does not assert required economics "
                f"qualifier {qualifier}"
            )
        return claim

    def resolve_claim_refs(
        self,
        claim_refs: object,
        *,
        qualifier: str | None = None,
    ) -> tuple[Claim, ...]:
        """Validate a tuple of Book 2 claim refs (mandatory on Book 5 records).

        Empty evidence bindings are refused — every canonical Book 5 economic
        fact is Book 2-backed (plan v0.3 B5-P1).
        """

        if isinstance(claim_refs, str) or not isinstance(claim_refs, tuple):
            raise Book5ProvenanceError(
                "book2_claim_refs must be a tuple of canonical claim refs"
            )
        if len(claim_refs) == 0:
            raise Book5ProvenanceError(
                "canonical Book 5 economic facts require at least one Book 2 claim ref"
            )
        resolved: list[Claim] = []
        for ref in claim_refs:
            if qualifier is not None:
                resolved.append(self.resolve_economics_claim(ref, qualifier=qualifier))
            else:
                resolved.append(self.resolve_claim(ref))
        return tuple(resolved)


def ref_text(claim: Claim) -> str:
    return claim.claim_id


__all__ = [
    "Book5Provenance",
    "Book5ProvenanceError",
    "ref_text",
    "require_str_hashable",
]
