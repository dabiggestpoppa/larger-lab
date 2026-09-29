"""Book 5 provenance adapter over the accepted Book 2 claim/evidence engines.

Book 5 owns no epistemic state machine and defines no new claim states. Every
canonical Book 5 economic fact resolves through the accepted Book 2
claim/evidence stores exactly as Book 4 does (single epistemic engine,
Constitution v0.2 §6/§13; ratified Book 5 plan v0.3 "Book 2 dependence").
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, model_validator

from .claims import Claim, ClaimStore, can_promote_to_graph
from .dependency_provenance import require_str_hashable
from .evidence import EvidenceStore


class Book5ProvenanceError(ValueError):
    """A Book 5 record cannot be canonical under accepted Book 2 truth."""


#: Attribution states that assert quantitative precision require their Book 2
#: claims to carry the matching basis qualifier (plan v0.3 Phase 4: no
#: attribution state may increase epistemic precision beyond its Book 2
#: basis; CON-2/CON-10; ALG-11). Verified at DECISION TIME against live record
#: state — construction-time validation alone is not authority.
ATTRIBUTION_BASIS_QUALIFIERS: Final[dict[str, str]] = {
    "EXACT": "PRINCIPAL_EXACT_FACT",
    "PROPORTIONAL": "PRINCIPAL_PROPORTIONAL_FACT",
}


class ClaimContextBinding(BaseModel):
    """Typed, evidence-bound Book 5-local binding of a claim to context.

    Book 2 propositions do not natively encode asset/realization/unit
    dimensions. This binding maps a canonical claim to the context dimensions
    it supports so decision-time validation can detect post-construction unit
    or asset mutation (R1-D2) — and, after R2, can no longer skip unbound
    dimensions (R2-D2).

    Epistemic honesty (plan v0.3 "Book 2 dependence"; Phase 5 of R2): the
    ``basis_claim_refs`` are canonical Book 2 claims resolved through the
    accepted claim/evidence engines; the asset/realization/unit FIELDS are a
    Book 5-local typed contextual INTERPRETATION. Book 2 proves that the
    referenced claims are canonical, current, and evidenced — it does not
    natively prove the context fields themselves, because its Proposition
    schema cannot represent them. An absent binding therefore means the
    dimension is NOT verifiable, never that it is verified:

        NO CONTEXT BINDING != CONTEXT VERIFIED
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    asset_ref: str | None = None
    realization_ref: str | None = None
    unit: str | None = None
    basis_claim_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _at_least_one_dimension(self) -> "ClaimContextBinding":
        if (
            self.asset_ref is None
            and self.realization_ref is None
            and self.unit is None
        ):
            raise ValueError(
                "context binding must establish at least one of asset_ref, "
                "realization_ref, or unit (a vacuous binding grounds nothing)"
            )
        return self


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
        self._context_bindings: dict[str, ClaimContextBinding] = {}

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

    def bind_claim_context(self, binding: ClaimContextBinding) -> None:
        """Register the evidence-bound context a canonical claim supports.

        R2 Phase 5 contract: the binding must be a typed ClaimContextBinding
        (raw dicts are refused); its subject claim must resolve as canonical
        and current; every ``basis_claim_refs`` entry must resolve through
        Book 2 as a current, evidenced canonical claim. Rebinding (duplicate
        or conflicting binding identity) is refused: bindings are
        registration-time facts, not mutable state.
        """

        if not isinstance(binding, ClaimContextBinding):
            raise Book5ProvenanceError(
                f"context binding must be a typed ClaimContextBinding, got "
                f"{type(binding).__name__}; raw binding payloads are refused"
            )
        self.resolve_claim(binding.claim_id)
        for basis_ref in binding.basis_claim_refs:
            self.resolve_claim(basis_ref)
        if binding.claim_id in self._context_bindings:
            raise Book5ProvenanceError(
                f"claim {binding.claim_id} already has a context binding"
            )
        self._context_bindings[binding.claim_id] = binding

    def validate_principal_component(self, component: object) -> None:
        """Decision-time live-state validation of a principal component.

        Required at every boundary that turns components into economic
        conclusions (R1-D1/R1-D2; R2-D2 closure). Validates the LIVE object,
        never a remembered construction: canonical type, canonical
        attribution state, resolvable current claim refs, attribution basis
        not exceeding its Book 2 claims, decimal quantity, non-empty unit,
        timezone-aware valid time, and — for quantitative authority — an
        explicit evidence-bound ClaimContextBinding establishing the
        component's asset and unit context (plus realization context when a
        realization_ref is present).

        R2-D2 closure: an absent binding is NEVER silently skipped. "No
        context binding" means "context not verified" and fails closed at a
        quantitative authority boundary (NO CONTEXT BINDING != CONTEXT
        VERIFIED).
        """

        from .book5_core import AttributionState, PrincipalComponent

        if not isinstance(component, PrincipalComponent):
            raise Book5ProvenanceError(
                f"principal component must be a typed PrincipalComponent, got "
                f"{type(component).__name__}"
            )
        state = component.attribution_state
        if not isinstance(state, AttributionState):
            raise Book5ProvenanceError(
                f"component carries non-canonical attribution state {state!r}"
            )
        resolved = self.resolve_claim_refs(component.book2_claim_refs)
        required_qualifier = ATTRIBUTION_BASIS_QUALIFIERS.get(state.value)
        if required_qualifier is not None:
            for ref, claim in zip(component.book2_claim_refs, resolved):
                if claim.proposition.qualifier != required_qualifier:
                    raise Book5ProvenanceError(
                        f"component claims attribution {state.value} but claim "
                        f"{ref} asserts qualifier {claim.proposition.qualifier}; "
                        "attribution basis exceeds its Book 2 evidence"
                    )
        from decimal import Decimal, InvalidOperation

        if component.quantity is None:
            raise Book5ProvenanceError(
                "quantitative conclusions refuse a component with missing "
                "quantity (UNKNOWN != ZERO); supply evidence or an explicit gap"
            )
        try:
            Decimal(component.quantity)
        except InvalidOperation as exc:
            raise Book5ProvenanceError(
                f"component quantity {component.quantity!r} is not a decimal"
            ) from exc
        if not component.unit:
            raise Book5ProvenanceError("component unit must be non-empty")
        from datetime import datetime as _datetime

        if isinstance(component.valid_time, _datetime) and (
            component.valid_time.tzinfo is None
        ):
            raise Book5ProvenanceError(
                "component valid_time must be timezone-aware"
            )
        # R2-D2 context closure: every claim ref of a quantitative component
        # must be context-bound; the binding must agree with the component's
        # live asset/unit (and realization) context. No dimension passes by
        # falling through a missing binding.
        if len(component.book2_claim_refs) == 0:
            raise Book5ProvenanceError(
                "quantitative component carries no Book 2 claim refs; context "
                "cannot be established"
            )
        unbound = [
            ref
            for ref in component.book2_claim_refs
            if ref not in self._context_bindings
        ]
        if unbound:
            raise Book5ProvenanceError(
                "context not verified for quantitative component: claim(s) "
                f"{', '.join(sorted(unbound))} carry no ClaimContextBinding; "
                "NO CONTEXT BINDING != CONTEXT VERIFIED — bind the claim's "
                "asset/unit/realization context explicitly before relying on "
                "it for a quantitative conclusion"
            )
        for ref in component.book2_claim_refs:
            binding = self._context_bindings[ref]
            if binding.asset_ref is not None and binding.asset_ref != component.asset_ref:
                raise Book5ProvenanceError(
                    f"component asset_ref {component.asset_ref!r} contradicts "
                    f"the context bound to claim {ref} ({binding.asset_ref!r})"
                )
            if binding.unit is not None and binding.unit != component.unit:
                raise Book5ProvenanceError(
                    f"component unit {component.unit!r} contradicts the context "
                    f"bound to claim {ref} ({binding.unit!r})"
                )
            if (
                binding.realization_ref is not None
                and binding.realization_ref != component.realization_ref
            ):
                raise Book5ProvenanceError(
                    f"component realization_ref {component.realization_ref!r} "
                    f"contradicts the context bound to claim {ref} "
                    f"({binding.realization_ref!r})"
                )
        # the binding set must ESTABLISH the component's identity dimensions,
        # not merely fail to contradict them
        established_asset = any(
            self._context_bindings[ref].asset_ref is not None
            for ref in component.book2_claim_refs
        )
        established_unit = any(
            self._context_bindings[ref].unit is not None
            for ref in component.book2_claim_refs
        )
        if not established_asset or not established_unit:
            missing = [
                dimension
                for dimension, established in (
                    ("asset_ref", established_asset),
                    ("unit", established_unit),
                )
                if not established
            ]
            raise Book5ProvenanceError(
                "context not verified for quantitative component: no binding "
                f"establishes {', '.join(missing)}; an unverifiable dimension "
                "is never a verified one"
            )
        if component.realization_ref is not None:
            established_realization = any(
                self._context_bindings[ref].realization_ref is not None
                for ref in component.book2_claim_refs
            )
            if not established_realization:
                raise Book5ProvenanceError(
                    "context not verified for quantitative component: "
                    "realization_ref is present but no binding establishes "
                    "the realization context"
                )

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
    "ATTRIBUTION_BASIS_QUALIFIERS",
    "Book5Provenance",
    "Book5ProvenanceError",
    "ClaimContextBinding",
    "ref_text",
    "require_str_hashable",
]
