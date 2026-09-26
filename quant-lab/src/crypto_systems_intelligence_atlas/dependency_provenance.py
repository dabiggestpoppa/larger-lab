"""Book 4 provenance adapter over the accepted Book 2 claim/evidence engines."""

from __future__ import annotations

from .claims import Claim, ClaimState, ClaimStore, can_promote_to_graph
from .evidence import EvidenceStore


class Book4ProvenanceError(ValueError):
    """A Book 4 record cannot be canonical under accepted Book 2 truth."""


class Book4Provenance:
    """Fail-closed resolver; Book 4 owns no epistemic state machine."""

    def __init__(self, claim_store: ClaimStore, evidence_store: EvidenceStore) -> None:
        self.claim_store = claim_store
        self.evidence_store = evidence_store

    def resolve_claim(
        self,
        claim_ref: str,
        *,
        expected_claim: Claim | None = None,
        require_current: bool = True,
    ) -> Claim:
        try:
            canonical = self.claim_store.require(claim_ref)
        except KeyError as exc:
            raise Book4ProvenanceError(f"unknown claim ID {claim_ref}") from exc
        if expected_claim is not None and canonical != expected_claim:
            raise Book4ProvenanceError(f"forged or detached claim object {claim_ref}")
        if require_current and not can_promote_to_graph(canonical, self.claim_store):
            raise Book4ProvenanceError(
                f"claim {claim_ref} is not canonical current graph-promotable "
                f"({canonical.claim_state.value})"
            )
        for evidence_ref in canonical.evidence_refs:
            try:
                self.evidence_store.require(evidence_ref)
            except KeyError as exc:
                raise Book4ProvenanceError(
                    f"claim {claim_ref} has detached evidence {evidence_ref}"
                ) from exc
        return canonical

    def resolve_qualifier_claim(self, claim_ref: str, *, qualifier: str) -> Claim:
        """Resolve a canonical claim that specifically asserts ``qualifier``.

        A generic canonical claim is never accepted as support for a specific
        Book 4 fact; the claim proposition must carry the fact qualifier.
        """

        claim = self.resolve_claim(claim_ref)
        if claim.proposition.qualifier != qualifier:
            raise Book4ProvenanceError(
                f"claim {claim_ref} does not assert required fact qualifier {qualifier}"
            )
        return claim

    def require_claim_set_closure(
        self,
        nested_claim_refs: tuple[str, ...],
        book2_claim_refs: tuple[str, ...],
        *,
        nested_role: str,
        record_kind: str,
    ) -> None:
        """Require every nested decision-driving claim to be declared provenance.

        The record-level ``book2_claim_refs`` set is the record's declared
        authority set; a nested decision-driving claim outside it means the
        assessment's actual authority set differs from its declared provenance.
        Referenced objects (for example a FailureDomain named by a redundancy
        record) keep their own canonical provenance and are not part of this
        closure.
        """

        declared = set(book2_claim_refs)
        for claim_ref in nested_claim_refs:
            if claim_ref not in declared:
                raise Book4ProvenanceError(
                    f"{record_kind} {nested_role} claim {claim_ref} is outside the "
                    f"record-level book2_claim_refs provenance set"
                )

    def _normalized_snapshot_set(self, source_snapshot_refs: tuple[str, ...]) -> set[str]:
        return set(source_snapshot_refs)

    def _required_snapshot_refs(
        self,
        claim_refs: tuple[str, ...],
    ) -> set[str]:
        required: set[str] = set()
        for claim_ref in claim_refs:
            claim = self.resolve_claim(claim_ref)
            for evidence_ref in claim.evidence_refs:
                raw = self.evidence_store.require(evidence_ref)
                required.add(raw.raw_snapshot_ref)
        return required

    def validate_snapshot_lineage(
        self,
        claim_refs: tuple[str, ...],
        source_snapshot_refs: tuple[str, ...],
    ) -> None:
        """Require exact snapshot lineage: all and only reachable snapshots.

        Canonical provenance is exact.  ``source_snapshot_refs`` must equal
        (as a set) the ``raw_snapshot_ref`` values reachable from the canonical
        Book 2 claims the record declares: every reachable snapshot must be
        declared, and no unrelated extra snapshot may appear.  Shared snapshots
        across claims deduplicate naturally through set equality, and no second
        snapshot registry is introduced.
        """

        if not source_snapshot_refs:
            raise Book4ProvenanceError(
                "canonical Book 4 records require source_snapshot_refs lineage"
            )
        required = self._required_snapshot_refs(claim_refs)
        supplied = self._normalized_snapshot_set(source_snapshot_refs)
        missing = sorted(required - supplied)
        extra = sorted(supplied - required)
        if missing:
            raise Book4ProvenanceError(
                f"snapshot lineage mismatch: missing required snapshots {missing}"
            )
        if extra:
            raise Book4ProvenanceError(
                f"snapshot lineage mismatch: unrelated extra snapshots {extra}"
            )

    def validate_refs(
        self,
        claim_refs: tuple[str, ...],
        *,
        supplied_claims: dict[str, Claim] | None = None,
        require_current: bool = True,
    ) -> tuple[Claim, ...]:
        if not claim_refs:
            raise Book4ProvenanceError("canonical Book 4 records require book2_claim_refs")
        supplied_claims = supplied_claims or {}
        return tuple(
            self.resolve_claim(
                ref,
                expected_claim=supplied_claims.get(ref),
                require_current=require_current,
            )
            for ref in claim_refs
        )


__all__ = ["Book4Provenance", "Book4ProvenanceError", "ClaimState"]
