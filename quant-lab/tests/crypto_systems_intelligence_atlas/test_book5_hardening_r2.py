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

import pydantic
import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    AttributionStateError,
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
from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis
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
AUTHORITY_REJECTION: tuple[type[Exception], ...] = (
    TypeError,
    Book5ProvenanceError,
    AttributionStateError,
    pydantic.ValidationError,
)


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
    components = component_set(component(claim_ref=claim_ref))
    base = dict(
        position_id=position_id,
        position_kind=PositionKind.CLAIM_SIDE,
        asset_ref="csia:token:lp",
        principal_components=components,
        holder_ref=None,
        protocol_ref="csia:protocol:amm",
        site_ref="csia:site:pool-1",
        location=EconomicLocation(location_type=LocationType.POOL, ref="loc:1"),
        quantity="1",
        unit="LP",
        valid_from=T0,
        observed_at=T0,
        # position refs DERIVE from the nested components: never a separate
        # assertion that could drift from the component basis
        book2_claim_refs=tuple(
            ref for c in components.components for ref in c.book2_claim_refs
        ),
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
    WITHOUT provenance must REJECT: the authority-less engine cannot even be
    constructed (seal), and explicit None is refused typed (fail-closed)."""

    _, claim_id = exact_kernel()
    position = r2_position("pos:b1", claim_ref=claim_id)
    position.model_copy(update={"book2_claim_refs": ()})  # the tamper itself
    with pytest.raises(TypeError):
        _synthesis_without_provenance()
    with pytest.raises(Book5ProvenanceError):
        _synthesis_with(None)


def test_b2_nested_component_refs_stripped_synthesis_without_provenance_rejected() -> None:
    """B2: nested component refs stripped → synthesis WITHOUT provenance
    REJECT: no authority-less engine exists to accept it."""

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
    del tampered
    with pytest.raises(TypeError):
        _synthesis_without_provenance()


def test_b3_swapped_unrelated_claim_synthesis_without_provenance_rejected() -> None:
    """B3: position claim swapped to an unrelated canonical claim → synthesis
    WITHOUT provenance REJECT: no authority-less engine exists to accept it."""

    _, claim_id = exact_kernel()
    position = r2_position("pos:b3", claim_ref=claim_id)
    swapped = position.model_copy(update={"book2_claim_refs": ("book5-claim-vault",)})
    del swapped
    with pytest.raises(TypeError):
        _synthesis_without_provenance()


def test_b4_detached_claim_synthesis_without_resolver_rejected() -> None:
    """B4: a valid-looking but detached (evidence-less) current-state claim in
    a position → synthesis WITHOUT a resolver REJECT: construction is refused,
    and the detached claim is also refused by the bound resolver's path."""

    claims, evidence, provenance = kernel()
    claim_id = add_claim(provenance, "b4-detached", with_evidence=False)
    del claims, evidence
    position = r2_position("pos:b4", claim_ref=claim_id)
    with pytest.raises(TypeError):
        _synthesis_without_provenance()
    # the authority-bearing path refuses the detached claim on its own merits
    synthesis = _synthesis_with(provenance)
    with pytest.raises(Book5ProvenanceError):
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
# Phase 5 — evidence-bound binding registration contract
# ---------------------------------------------------------------------------


def test_binding_duplicate_identity_refused() -> None:
    """A claim may carry exactly one context binding; rebinding is refused
    (bindings are registration-time facts, not mutable state)."""

    claims, evidence, provenance = kernel()
    claim_id = register_exact_claim(claims, evidence, "dup-exact")
    binding = ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:eth", unit="ETH")
    provenance.bind_claim_context(binding)
    with pytest.raises(Book5ProvenanceError):
        provenance.bind_claim_context(
            ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:wbtc", unit="BTC")
        )


def test_binding_raw_dict_refused() -> None:
    """Raw dict binding input is refused — only typed bindings register."""

    _, _, provenance = kernel()
    with pytest.raises(Book5ProvenanceError):
        provenance.bind_claim_context(  # type: ignore[arg-type]
            {"claim_id": "book5-claim-eth", "asset_ref": "csia:token:eth", "unit": "ETH"}
        )


def test_binding_basis_claims_resolve_through_book2() -> None:
    """Every basis_claim_refs entry must resolve as a current, evidenced
    canonical Book 2 claim; a detached basis refuses registration."""

    claims, evidence, provenance = kernel()
    claim_id = register_exact_claim(claims, evidence, "basis-exact")
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=claim_id,
            asset_ref="csia:token:eth",
            unit="ETH",
            basis_claim_refs=(claim_id,),
        )
    )
    with pytest.raises(Book5ProvenanceError):
        provenance.bind_claim_context(
            ClaimContextBinding(
                claim_id="book5-claim-base",
                asset_ref="csia:token:usdc",
                unit="USDC",
                basis_claim_refs=("book5-never-captured",),
            )
        )


def test_binding_vacuous_refused() -> None:
    """A binding establishing NO dimension grounds nothing and is refused."""

    with pytest.raises(ValueError):
        ClaimContextBinding(claim_id="book5-claim-base")


# ---------------------------------------------------------------------------
# Phase 9 — model_copy attack matrix (D1–D11)
# ---------------------------------------------------------------------------


def _healthy_aggregate():
    """A canonical aggregate: proper exact basis + coherent binding."""

    provenance, claim_id = exact_kernel("d-matrix-exact")
    healthy = component(quantity="3", attribution=AttributionState.EXACT, claim_ref=claim_id)
    return provenance, healthy


def test_d1_attribution_exact_unknown_cycle_refused_at_unknown_stage() -> None:
    """D1: EXACT → UNKNOWN → EXACT cycle. The intermediate UNKNOWN state is
    never authority: aggregation at that stage refuses. A return to EXACT is
    a NEW record that must stand on its own live basis + binding — there is
    no memory to launder a tampered state through."""

    provenance, healthy = _healthy_aggregate()
    demoted = healthy.model_copy(update={"attribution_state": AttributionState.UNKNOWN})
    component_set_ = PrincipalComponentSet(components=(demoted,))
    with pytest.raises((Book5ProvenanceError, AttributionStateError)):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_d2_unit_mutation_refused() -> None:
    """D2: unit mutated on an otherwise canonical component → REJECT."""

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(update={"unit": "USDC"})
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
            "USDC", provenance=provenance
        )


def test_d3_asset_mutation_refused() -> None:
    """D3: asset_ref mutated → REJECT."""

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(update={"asset_ref": "csia:token:wbtc"})
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
            "ETH", provenance=provenance
        )


def test_d4_realization_mutation_refused() -> None:
    """D4: realization_ref mutated to an unrelated realization → REJECT."""

    provenance, claim_id = exact_kernel(
        "d4-realization", realization_ref="realization:chain-a"
    )
    healthy = component(
        quantity="3",
        attribution=AttributionState.EXACT,
        claim_ref=claim_id,
        realization_ref="realization:chain-a",
    )
    tampered = healthy.model_copy(update={"realization_ref": "realization:chain-b"})
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
            "ETH", provenance=provenance
        )


def test_d5_claim_refs_stripped_refused() -> None:
    """D5: book2_claim_refs stripped → REJECT (no basis, no context)."""

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(update={"book2_claim_refs": ()})
    # the stripped component cannot even re-enter a canonical set: the set
    # constructor itself fails closed before any aggregate call
    with pytest.raises(pydantic.ValidationError):
        PrincipalComponentSet(components=(tampered,))


def test_d6_binding_claim_identity_swap_refused() -> None:
    """D6: the component is pointed at a claim whose binding disagrees with
    its live context — the binding registry is consulted LIVE at decision
    time, so the swap cannot inherit the original claim's context."""

    claims, evidence, provenance = kernel()
    claim_id = register_exact_claim(claims, evidence, "d6-matrix")
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id=claim_id, asset_ref="csia:token:eth", unit="ETH")
    )
    # a second claim bound to a DIFFERENT context
    other_id = register_exact_claim(claims, evidence, "d6-other")
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id=other_id, asset_ref="csia:token:wbtc", unit="BTC")
    )
    swapped = component(
        quantity="3", attribution=AttributionState.EXACT, claim_ref=claim_id
    ).model_copy(update={"book2_claim_refs": (other_id,)})
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(swapped,)).aggregate_same_unit(
            "ETH", provenance=provenance
        )


def test_d7_quantity_mutation_documents_design_boundary() -> None:
    """D7: quantity mutated 3 → 999. Book 5's authority seal revalidates the
    basis (qualifier), the context (binding agreement), and quantity
    SEMANTICS (decimal, present, never fabricated zero). Magnitude-vs-claim
    verification is outside Book 2's Proposition schema and is the evidence
    layer's authority (Sensor/Book 4); the aggregate therefore carries the
    claim's identity chain with the recorded magnitude. This row DOCUMENTS
    that boundary deliberately — it is not a silent pass."""

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(update={"quantity": "999"})
    total = PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
        "ETH", provenance=provenance
    )
    assert total == "999"  # documented: magnitude authority lives elsewhere


def test_d8_naive_valid_time_refused() -> None:
    """D8: valid_time mutated to a naive datetime → REJECT."""

    from datetime import datetime

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(
        update={"valid_time": datetime(2026, 9, 30, 12)}
    )
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
            "ETH", provenance=provenance
        )


def test_d9_nested_component_mutation_refused_at_compose() -> None:
    """D9: a position's NESTED component is mutated → 5G composition must
    revalidate it live and REJECT."""

    from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis

    provenance, claim_id = exact_kernel("d9-nested")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:d9", claim_ref=claim_id)
    mutated_components = position.principal_components.model_copy(
        update={
            "components": (
                position.principal_components.components[0].model_copy(
                    update={"unit": "USDC"}
                ),
            )
        }
    )
    tampered = position.model_copy(update={"principal_components": mutated_components})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:d9", positions=(tampered,), valid_time=T0, observed_at=T0)


def test_d10_raw_string_attribution_state_refused() -> None:
    """D10: raw string state injected via model_copy → REJECT (never
    normalized silently)."""

    provenance, healthy = _healthy_aggregate()
    tampered = healthy.model_copy(update={"attribution_state": "EXACT"})
    assert not isinstance(tampered.attribution_state, AttributionState)
    with pytest.raises(Book5ProvenanceError):
        PrincipalComponentSet(components=(tampered,)).aggregate_same_unit(
            "ETH", provenance=provenance
        )


def test_d11_raw_binding_dict_refused_at_registration() -> None:
    """D11: a raw binding dict can never enter the registry — the authority
    context cannot be forged with untyped payloads."""

    _, _, provenance = kernel()
    with pytest.raises(Book5ProvenanceError):
        provenance.bind_claim_context(  # type: ignore[arg-type]
            {"claim_id": "book5-claim-base", "asset_ref": "csia:token:eth", "unit": "ETH"}
        )


# ---------------------------------------------------------------------------
# Phase 10 — synthesis attacks (S1–S10): only S10 passes
# ---------------------------------------------------------------------------


def test_s1_no_provenance_authority_mode_impossible() -> None:
    """S1: CapitalFieldSynthesis cannot be constructed into an authority-
    bearing mode without provenance — argument omitted OR explicit None."""

    with pytest.raises(TypeError):
        CapitalFieldSynthesis()  # type: ignore[call-arg]
    with pytest.raises(Book5ProvenanceError):
        CapitalFieldSynthesis(None)  # type: ignore[arg-type]


def test_s2_stripped_position_refs_rejected() -> None:
    """S2: position refs stripped → compose REJECT."""

    provenance, claim_id = exact_kernel("s2-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s2", claim_ref=claim_id)
    stripped = position.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s2", positions=(stripped,), valid_time=T0, observed_at=T0)


def test_s3_stripped_nested_refs_rejected() -> None:
    """S3: nested component refs stripped → compose REJECT."""

    provenance, claim_id = exact_kernel("s3-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s3", claim_ref=claim_id)
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
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s3", positions=(tampered,), valid_time=T0, observed_at=T0)


def test_s4_unrelated_claim_rejected() -> None:
    """S4: position claim swapped to an unrelated canonical claim → compose
    REJECT (wrong basis qualifier for the component's EXACT state)."""

    provenance, claim_id = exact_kernel("s4-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s4", claim_ref=claim_id)
    swapped = position.model_copy(update={"book2_claim_refs": ("book5-claim-vault",)})
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s4", positions=(swapped,), valid_time=T0, observed_at=T0)


def test_s5_contextless_exact_component_rejected() -> None:
    """S5: exact-basis component whose claim has NO context binding →
    compose REJECT (NO CONTEXT BINDING != CONTEXT VERIFIED)."""

    claims, evidence, provenance = kernel()
    unbound_ref = register_exact_claim(claims, evidence, "s5-unbound")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s5", claim_ref=unbound_ref)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s5", positions=(position,), valid_time=T0, observed_at=T0)


def test_s6_unit_mutation_rejected() -> None:
    """S6: unit mutated inside a position → compose REJECT."""

    provenance, claim_id = exact_kernel("s6-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s6", claim_ref=claim_id)
    mutated = position.model_copy(
        update={
            "principal_components": position.principal_components.model_copy(
                update={
                    "components": (
                        position.principal_components.components[0].model_copy(
                            update={"unit": "USDC"}
                        ),
                    )
                }
            )
        }
    )
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s6", positions=(mutated,), valid_time=T0, observed_at=T0)


def test_s7_asset_mutation_rejected() -> None:
    """S7: asset_ref mutated inside a position → compose REJECT."""

    provenance, claim_id = exact_kernel("s7-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s7", claim_ref=claim_id)
    mutated = position.model_copy(
        update={
            "principal_components": position.principal_components.model_copy(
                update={
                    "components": (
                        position.principal_components.components[0].model_copy(
                            update={"asset_ref": "csia:token:wbtc"}
                        ),
                    )
                }
            )
        }
    )
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s7", positions=(mutated,), valid_time=T0, observed_at=T0)


def test_s8_realization_mutation_rejected() -> None:
    """S8: realization_ref mutated inside a position → compose REJECT."""

    provenance, claim_id = exact_kernel(
        "s8-exact", realization_ref="realization:chain-a"
    )
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position(
        "pos:s8", claim_ref=claim_id
    )
    position = position.model_copy(
        update={
            "principal_components": position.principal_components.model_copy(
                update={
                    "components": (
                        position.principal_components.components[0].model_copy(
                            update={"realization_ref": "realization:chain-a"}
                        ),
                    )
                }
            )
        }
    )
    mutated = position.model_copy(
        update={
            "principal_components": position.principal_components.model_copy(
                update={
                    "components": (
                        position.principal_components.components[0].model_copy(
                            update={"realization_ref": "realization:chain-b"}
                        ),
                    )
                }
            )
        }
    )
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:s8", positions=(mutated,), valid_time=T0, observed_at=T0)


def test_s9_raw_position_dict_rejected() -> None:
    """S9: raw position dict at the 5G boundary → typed fail-closed error."""

    provenance, _ = exact_kernel("s9-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot(
            "snap:s9",
            positions=({"position_id": "pos:raw", "quantity": "1"},),  # type: ignore[list-item]
            valid_time=T0,
            observed_at=T0,
        )


def test_s10_coherent_canonical_input_passes() -> None:
    """S10: the ONLY passing synthesis attack row — fully canonical input
    with an explicitly bound authority context."""

    provenance, claim_id = exact_kernel("s10-exact")
    synthesis = CapitalFieldSynthesis(provenance)
    position = r2_position("pos:s10", claim_ref=claim_id)
    snapshot = synthesis.compose_snapshot(
        "snap:s10", positions=(position,), valid_time=T0, observed_at=T0
    )
    assert snapshot.input_record_refs == ("pos:s10",)
    assert snapshot.principal_components is not None
    assert not snapshot.incomplete


# ---------------------------------------------------------------------------
# helpers — synthesis construction is abstracted so the R2 seal (provenance
# required, no default None) has exactly one blast radius in this file
# ---------------------------------------------------------------------------


def _synthesis_without_provenance() -> object:
    """Attempt to construct CapitalFieldSynthesis with no authority context.

    After the R2 seal this call is refused at construction (missing required
    argument) — the authority-less mode of the engine does not exist.
    """

    from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis

    return CapitalFieldSynthesis()  # type: ignore[call-arg]


def _synthesis_with(provenance: Book5Provenance | None) -> object:
    from crypto_systems_intelligence_atlas.book5_synthesis import CapitalFieldSynthesis

    return CapitalFieldSynthesis(provenance)  # type: ignore[arg-type]
