"""Book 5 HARDENING R2 — mandatory authority context + quantitative context
closure.

Defect classes under test, each demonstrated against the R1-hardened kernel:

R2-D1   provenance is OPTIONAL at ``PrincipalComponentSet.aggregate_same_unit``
        — omitting the resolver silently downgrades the boundary to a bare
        enum check (A1–A5).
R2-D1B  ``CapitalFieldSynthesis`` may be constructed without a provenance
        resolver; the canonical-input validators then early-return (B1–B5).
R2-D2   ``validate_principal_component`` skips unbound claims
        (``binding is None: continue``) — attribution basis can be correct
        while asset/unit/realization context is never verified (C1–C8).

Central R2 invariant (Phase 8): forgetting an optional argument must never
change the epistemic strength of an output. An absent context binding is
never treated as a verified context.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    EconomicLocation,
    LocationType,
    PrincipalComponentSet,
)
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    CapitalPosition,
    PositionKind,
)
from crypto_systems_intelligence_atlas.book5_support import (
    NOW,
    add_claim,
    component,
    component_set,
    kernel,
    make_claim,
    make_evidence,
)
from crypto_systems_intelligence_atlas.claims import ClaimStore
from crypto_systems_intelligence_atlas.evidence import EvidenceStore

T0 = NOW

#: A missing resolver must be indistinguishable from a refused one: either the
#: call cannot happen (missing required keyword) or the kernel raises the typed
#: provenance error. Both are fail-closed; neither may return a total.
AUTHORITY_REJECTION: tuple[type[Exception], ...] = (TypeError, Book5ProvenanceError)


def register_exact_claim(
    claims: ClaimStore, evidence: EvidenceStore, tag: str
) -> str:
    """Register one canonical PRINCIPAL_EXACT_FACT claim on the given stores."""

    evidence_ref = make_evidence(evidence, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    claims.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    return claim_id


def exact_kernel(
    tag: str = "eth-exact",
    *,
    bind: bool = True,
    asset_ref: str = "csia:token:eth",
    unit: str = "ETH",
    realization_ref: str | None = None,
) -> tuple[Book5Provenance, str]:
    """One kernel whose stores carry a canonical exact-basis claim.

    Returns ``(provenance, claim_id)``. With ``bind=True`` (the R2 canonical
    positive fixture) an explicit ClaimContextBinding establishes the
    component's asset/unit (+ realization) context; with ``bind=False`` the
    exact-basis claim exists but NO binding does — the isolated R2-D2
    reproduction state.
    """

    claims, evidence, provenance = kernel()
    claim_id = register_exact_claim(claims, evidence, tag)
    if bind:
        provenance.bind_claim_context(
            ClaimContextBinding(
                claim_id=claim_id,
                asset_ref=asset_ref,
                realization_ref=realization_ref,
                unit=unit,
            )
        )
    return provenance, claim_id


def r2_position(
    position_id: str,
    *,
    claim_ref: str,
    **overrides: object,
) -> CapitalPosition:
    base = dict(
        position_id=position_id,
        position_kind=PositionKind.CLAIM_SIDE,
        asset_ref="csia:token:lp",
        principal_components=component_set(component(claim_ref=claim_ref)),
        holder_ref=None,
        protocol_ref="csia:protocol:amm",
        site_ref="csia:site:pool-1",
        location=EconomicLocation(location_type=LocationType.POOL, ref="loc:1"),
        quantity="1",
        unit="LP",
        valid_from=T0,
        observed_at=T0,
        book2_claim_refs=(claim_ref,),
    )
    base.update(overrides)
    return CapitalPosition(**base)


# ---------------------------------------------------------------------------
# R2-D1 / Phase 1 — provenance omission at the aggregate authority boundary
# ---------------------------------------------------------------------------


def test_a1_unknown_to_exact_without_provenance_rejected() -> None:
    """A1: UNKNOWN → model_copy EXACT → aggregate WITHOUT provenance REJECT."""

    original = component(
        quantity="3", attribution=AttributionState.UNKNOWN, claim_ref="book5-claim-eth"
    )
    tampered = original.model_copy(update={"attribution_state": AttributionState.EXACT})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(AUTHORITY_REJECTION):
        component_set_.aggregate_same_unit("ETH")


def test_a2_comingled_to_exact_without_provenance_rejected() -> None:
    """A2: COMMINGLED → model_copy EXACT → aggregate WITHOUT provenance REJECT."""

    original = component(
        quantity="800",
        attribution=AttributionState.COMMINGLED,
        claim_ref="book5-claim-pool",
        unit="USDC",
        asset_ref="csia:token:usdc",
    )
    tampered = original.model_copy(update={"attribution_state": AttributionState.EXACT})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(AUTHORITY_REJECTION):
        component_set_.aggregate_same_unit("USDC")


def test_a3_generic_economic_fact_marked_exact_without_provenance_rejected() -> None:
    """A3: generic ECONOMIC_FACT marked EXACT → aggregate WITHOUT provenance
    REJECT. A forgotten resolver must not mint an authoritative total."""

    exact_marked = component(
        quantity="3", attribution=AttributionState.EXACT, claim_ref="book5-claim-eth"
    )
    component_set_ = PrincipalComponentSet(components=(exact_marked,))
    with pytest.raises(AUTHORITY_REJECTION):
        component_set_.aggregate_same_unit("ETH")


def test_a3b_generic_economic_fact_marked_exact_with_provenance_rejected() -> None:
    """A3b: the same generic-basis EXACT component is also rejected when the
    resolver IS supplied — the basis, not the argument, is the authority."""

    provenance, _ = exact_kernel()
    exact_marked = component(
        quantity="3", attribution=AttributionState.EXACT, claim_ref="book5-claim-eth"
    )
    component_set_ = PrincipalComponentSet(components=(exact_marked,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_a4_exact_basis_without_resolver_rejected() -> None:
    """A4: proper PRINCIPAL_EXACT_FACT basis but no authority resolver supplied
    → REJECT. Omitting the argument and passing None explicitly are both
    fail-closed; neither may produce an economic total."""

    _, claim_id = exact_kernel()
    exact = component(quantity="3", attribution=AttributionState.EXACT, claim_ref=claim_id)
    component_set_ = PrincipalComponentSet(components=(exact,))
    with pytest.raises(AUTHORITY_REJECTION):
        component_set_.aggregate_same_unit("ETH")
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=None)


def test_a5_exact_basis_with_live_provenance_and_context_passes() -> None:
    """A5: proper EXACT component + live Book5Provenance + proper exact basis
    + coherent context binding → PASS."""

    provenance, claim_id = exact_kernel()
    exact = component(quantity="3", attribution=AttributionState.EXACT, claim_ref=claim_id)
    component_set_ = PrincipalComponentSet(components=(exact,))
    assert component_set_.aggregate_same_unit("ETH", provenance=provenance) == "3"


# ---------------------------------------------------------------------------
# R2-D1B / Phase 1 — synthesis without a provenance resolver
# ---------------------------------------------------------------------------


def test_b1_position_refs_stripped_synthesis_without_provenance_rejected() -> None:
    """B1: valid position → model_copy(book2_claim_refs=()) → synthesis built
    WITHOUT provenance → compose_snapshot must REJECT."""

    _, claim_id = exact_kernel()
    position = r2_position("pos:b1", claim_ref=claim_id)
    stripped = position.model_copy(update={"book2_claim_refs": ()})
    synthesis = _synthesis_without_provenance()
    with pytest.raises(AUTHORITY_REJECTION):
        synthesis.compose_snapshot("snap:b1", positions=(stripped,), valid_time=T0, observed_at=T0)


def test_b2_nested_component_refs_stripped_synthesis_without_provenance_rejected() -> None:
    """B2: nested component refs stripped → synthesis WITHOUT provenance
    REJECT."""

    _, claim_id = exact_kernel()
    position = r2_position("pos:b2", claim_ref=claim_id)
    stripped_components = position.principal_components.model_copy(
        update={
            "components": (
                position.principal_components.components[0].model_copy(
                    update={"book2_claim_refs": ()}
                ),
            )
        }
    )
    tampered = position.model_copy(update={"principal_components": stripped_components})
    synthesis = _synthesis_without_provenance()
    with pytest.raises(AUTHORITY_REJECTION):
        synthesis.compose_snapshot("snap:b2", positions=(tampered,), valid_time=T0, observed_at=T0)


def test_b3_swapped_unrelated_claim_synthesis_without_provenance_rejected() -> None:
    """B3: position claim swapped to an unrelated canonical claim → synthesis
    WITHOUT provenance REJECT."""

    _, claim_id = exact_kernel()
    position = r2_position("pos:b3", claim_ref=claim_id)
    swapped = position.model_copy(update={"book2_claim_refs": ("book5-claim-vault",)})
    synthesis = _synthesis_without_provenance()
    with pytest.raises(AUTHORITY_REJECTION):
        synthesis.compose_snapshot("snap:b3", positions=(swapped,), valid_time=T0, observed_at=T0)


def test_b4_detached_claim_synthesis_without_resolver_rejected() -> None:
    """B4: a valid-looking but detached (evidence-less) current-state claim in
    a position → synthesis WITHOUT a resolver REJECT."""

    claims, evidence, provenance = kernel()
    claim_id = add_claim(provenance, "b4-detached", with_evidence=False)
    del claims, evidence
    position = r2_position("pos:b4", claim_ref=claim_id)
    synthesis = _synthesis_without_provenance()
    with pytest.raises(AUTHORITY_REJECTION):
        synthesis.compose_snapshot("snap:b4", positions=(position,), valid_time=T0, observed_at=T0)


def test_b5_canonical_input_with_explicit_provenance_passes() -> None:
    """B5: proper canonical input + explicitly bound provenance → PASS."""

    provenance, claim_id = exact_kernel()
    synthesis = _synthesis_with(provenance)
    position = r2_position("pos:b5", claim_ref=claim_id)
    snapshot = synthesis.compose_snapshot(
        "snap:b5", positions=(position,), valid_time=T0, observed_at=T0
    )
    assert snapshot.input_record_refs == ("pos:b5",)
    assert snapshot.principal_components is not None


# ---------------------------------------------------------------------------
# R2-D2 / Phase 3 — isolated context-binding bypass (attribution basis is
# already correct; ONLY the asset/unit/realization context is unprotected)
# ---------------------------------------------------------------------------


def test_c1_unit_mutated_while_claim_unbound_rejected() -> None:
    """C1: canonical exact claim, NO binding; coherent ETH component; unit
    ETH → USDC via model_copy; authority aggregation WITH provenance must
    REJECT (today it passes because the unbound claim is skipped)."""

    provenance, claim_id = exact_kernel("c1-exact", bind=False)
    coherent = component(quantity="3", claim_ref=claim_id)
    tampered = coherent.model_copy(update={"unit": "USDC"})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("USDC", provenance=provenance)


def test_c2_asset_mutated_while_claim_unbound_rejected() -> None:
    """C2: same setup, asset_ref ETH → WBTC; authority aggregation WITH
    provenance must REJECT."""

    provenance, claim_id = exact_kernel("c2-exact", bind=False)
    coherent = component(quantity="3", claim_ref=claim_id)
    tampered = coherent.model_copy(update={"asset_ref": "csia:token:wbtc"})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_c3_realization_mutated_while_claim_unbound_rejected() -> None:
    """C3: same setup, realization chain-A → unrelated chain-B; authority
    aggregation WITH provenance must REJECT."""

    provenance, claim_id = exact_kernel("c3-exact", bind=False)
    coherent = component(
        quantity="3", claim_ref=claim_id, realization_ref="realization:chain-a"
    )
    tampered = coherent.model_copy(update={"realization_ref": "realization:chain-b"})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_c4_contextless_exact_component_fails_closed() -> None:
    """C4: unmodified component with a correct exact basis but no context
    binding → quantitative authority FAILS CLOSED, because asset/unit context
    cannot be verified. An unverifiable dimension is never a verified one."""

    provenance, claim_id = exact_kernel("c4-exact", bind=False)
    coherent = component(quantity="3", claim_ref=claim_id)
    component_set_ = PrincipalComponentSet(components=(coherent,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_c5_coherent_explicit_binding_passes() -> None:
    """C5: same component with an explicit coherent ClaimContextBinding →
    PASS."""

    provenance, claim_id = exact_kernel("c5-exact", bind=True)
    coherent = component(quantity="3", claim_ref=claim_id)
    component_set_ = PrincipalComponentSet(components=(coherent,))
    assert component_set_.aggregate_same_unit("ETH", provenance=provenance) == "3"


def test_c6_binding_disagreeing_unit_rejected() -> None:
    """C6: binding disagrees with the component's unit → REJECT."""

    provenance, claim_id = exact_kernel("c6-exact", bind=True, unit="USDC")
    coherent = component(quantity="3", claim_ref=claim_id)  # unit ETH
    component_set_ = PrincipalComponentSet(components=(coherent,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_c7_binding_disagreeing_asset_rejected() -> None:
    """C7: binding disagrees with the component's asset_ref → REJECT."""

    provenance, claim_id = exact_kernel("c7-exact", bind=True, asset_ref="csia:token:wbtc")
    coherent = component(quantity="3", claim_ref=claim_id)  # asset ETH
    component_set_ = PrincipalComponentSet(components=(coherent,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_c8_binding_disagreeing_realization_rejected() -> None:
    """C8: binding disagrees with the component's realization_ref → REJECT."""

    provenance, claim_id = exact_kernel(
        "c8-exact", bind=True, realization_ref="realization:chain-z"
    )
    coherent = component(
        quantity="3", claim_ref=claim_id, realization_ref="realization:chain-a"
    )
    component_set_ = PrincipalComponentSet(components=(coherent,))
    with pytest.raises(Book5ProvenanceError):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


# ---------------------------------------------------------------------------
# helpers — synthesis construction is abstracted so the R2 seal (provenance
# required, no default None) has exactly one blast radius in this file
# ---------------------------------------------------------------------------


def _synthesis_without_provenance() -> object:
    """Construct CapitalFieldSynthesis the way the R2 defect does: with no
    authority context at all. After the R2 seal this call is itself refused."""

    from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis

    return CapitalFieldSynthesis()  # type: ignore[call-arg]


def _synthesis_with(provenance: Book5Provenance) -> object:
    from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis

    return CapitalFieldSynthesis(provenance=provenance)
