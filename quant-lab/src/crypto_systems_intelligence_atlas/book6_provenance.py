"""Book 6 provenance adapter over the accepted Book 2 claim/evidence engines.

Book 6 owns measurement definitions and descriptive measured state. It owns NO
epistemic state machine, defines NO claim state, and mints NO Book 2 claim
(ratified D6M-1 = A: a ``MeasurementObservation`` is a Book 6-local derived
record that CITES Book 2 authority; it is not itself a claim).

Currentness is therefore inherited, never owned. This adapter resolves the
cited ``source_claim_refs`` through the accepted Book 2 engines
(``ClaimStore`` / ``can_promote_to_graph`` / ``EvidenceStore``) and re-checks them
at every authority-bearing use — the Book 4/Book 5 lesson:

    REGISTERED THEN != AUTHORITATIVE NOW

An absent or decayed Book 2 claim makes the citing measurement unavailable for
authority; it never converts the measurement into a claim, and it never
fabricates a value.
"""

from __future__ import annotations

from typing import Final

from .claims import Claim, ClaimStore, can_promote_to_graph
from .dependency_provenance import require_str_hashable
from .evidence import EvidenceStore


class Book6ProvenanceError(ValueError):
    """A Book 6 record cannot be authoritative under accepted Book 2 truth."""


#: Book 6 claim states that are canonical-current and graph-promotable under the
#: accepted Book 2 machine. Recorded as documentation only: Book 6 READS Book 2
#: currentness through ``can_promote_to_graph`` and never re-implements it, so
#: this tuple can never diverge from Book 2 in behaviour.
BOOK2_CURRENT_STATES: Final[frozenset[str]] = frozenset(
    {"OBSERVED", "CORROBORATED", "INFERRED"}
)


class Book6Provenance:
    """Narrow adapter: Book 2 authority in, Book 6 availability out.

    Responsibilities (ratified plan v0.2 §3):

    - resolve ``source_claim_refs``;
    - require current / promotable Book 2 authority at DECISION time;
    - fail closed on unknown, detached, stale, contested, rejected or superseded
      input wherever current authority is required;
    - never introduce a Book 6 claim state;
    - never mint a Book 2 claim.
    """

    def __init__(
        self,
        claim_store: ClaimStore,
        evidence_store: EvidenceStore,
        *,
        require_provenance: bool = True,
    ) -> None:
        if require_provenance is not True:
            raise Book6ProvenanceError(
                "Book 6 authority operations require an explicit provenance "
                "resolver; a defaulted or disabled resolver is refused"
            )
        self.claim_store = claim_store
        self.evidence_store = evidence_store

    # -- authority resolution -------------------------------------------------

    def resolve_claim(
        self,
        claim_ref: object,
        *,
        expected_claim: Claim | None = None,
        require_current: bool = True,
    ) -> Claim:
        """Resolve one cited Book 2 claim, live, at decision time."""

        ref = require_str_hashable(claim_ref, role="book6 claim_ref")
        try:
            canonical = self.claim_store.require(ref)
        except KeyError as exc:
            raise Book6ProvenanceError(f"unknown Book 2 claim {ref}") from exc
        if expected_claim is not None and canonical != expected_claim:
            raise Book6ProvenanceError(
                f"forged or detached Book 2 claim object {ref}"
            )
        if require_current and not can_promote_to_graph(canonical, self.claim_store):
            raise Book6ProvenanceError(
                f"Book 2 claim {ref} is not canonical current graph-promotable "
                f"({canonical.claim_state.value}); a citing Book 6 record "
                f"therefore has no current authority"
            )
        for evidence_ref in canonical.evidence_refs:
            try:
                self.evidence_store.require(evidence_ref)
            except KeyError as exc:
                raise Book6ProvenanceError(
                    f"Book 2 claim {ref} has detached evidence {evidence_ref}"
                ) from exc
        return canonical

    def resolve_source_claim_refs(
        self, source_claim_refs: tuple[str, ...], *, require_current: bool = True
    ) -> tuple[Claim, ...]:
        """Resolve every cited Book 2 claim; fail closed on the first problem.

        A measurement may not assert a value while ANY of its cited authority is
        unresolved — partial authority is not authority.
        """

        if not source_claim_refs:
            raise Book6ProvenanceError(
                "a Book 6 observation asserting a value must cite at least one "
                "Book 2 source claim"
            )
        return tuple(
            self.resolve_claim(ref, require_current=require_current)
            for ref in source_claim_refs
        )

    def validate_value_authority(
        self, source_claim_refs: tuple[str, ...]
    ) -> str:
        """Return a stable authority verdict for a value-bearing observation.

        Returns ``"AUTHORITATIVE"`` only when every cited claim is canonical,
        current and evidenced at this instant. The verdict is derived, never
        remembered from construction.
        """

        self.resolve_source_claim_refs(source_claim_refs, require_current=True)
        return "AUTHORITATIVE"

    def claim_is_current(self, claim_ref: str) -> bool:
        """Return whether a cited claim is currently promotable (no raise)."""

        try:
            self.resolve_claim(claim_ref, require_current=True)
        except Book6ProvenanceError:
            return False
        return True


__all__ = ["BOOK2_CURRENT_STATES", "Book6Provenance", "Book6ProvenanceError"]
