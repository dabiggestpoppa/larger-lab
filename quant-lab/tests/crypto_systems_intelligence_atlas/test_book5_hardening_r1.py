"""Book 5 HARDENING R1 — decision-point live-state validation +
no-fabricated-principal semantics.

Defect classes under test (each demonstrated against the pre-R1 kernel):

R1-D1  PrincipalComponent attribution upgradeable via model_copy (A1–A7)
R1-D2  unit/asset context mutable without basis revalidation (B1–B4)
R1-D3  missing quantity fabricated as "0"; flow-only snapshots manufacture a
       placeholder principal (C1–C4, D1–D6)
R1-D4  raw post-construction inputs crash with AttributeError instead of
       typed fail-closed errors (E1–E6)
R1-D5  5G composition accepts model_copy-mutated records with stripped or
       swapped claim refs (F1–F5)
"""

from __future__ import annotations

from datetime import UTC

import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    EconomicLocation,
    LocationType,
    PrincipalComponentSet,
)
from crypto_systems_intelligence_atlas.book5_lineage import (
    CapitalPrincipalLineageGraph,
    LineageError,
    VALUATION_NOT_AUTHORIZED,
)
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    CapitalFlow,
    CapitalPosition,
    FlowType,
    PositionKind,
)
from crypto_systems_intelligence_atlas.book5_support import (
    LATER,
    NOW,
    component,
    component_set,
    contribution,
    kernel,
    lineage_node,
    make_claim,
    make_evidence,
)
from crypto_systems_intelligence_atlas.book5_synthesis import (
    CapitalFieldSynthesis,
    SynthesisWriteLedger,
)

UTC = UTC
T0 = NOW


@pytest.fixture(autouse=True)
def _bind_kernel_flow_context(monkeypatch):
    """R3 context seal adaptation for the R1 corpus.

    R1's flow-only defect demonstrations (D1–D6) cite ``book5-claim-eth``
    through ``make_flow()``. After the R3 non-component context seal, a flow
    claim with NO QuantitativeRecordContextBinding is refused at 5G
    composition (NO BINDING != CONTEXT VERIFIED) — which is not the defect
    class R1 documents (fabricated principals, placeholder tokens, stripped
    claim refs). Binding the flow context (asset ETH / unit ETH) for the
    fixture claim on every fresh kernel keeps these rows pointed at exactly
    their original defects.
    """

    from crypto_systems_intelligence_atlas.book5_provenance import (
        QuantitativeRecordContextBinding,
        QuantitativeRecordKind,
    )

    original_kernel = kernel

    def kernel_with_flow_context():
        claims, evidence, provenance = original_kernel()
        provenance.bind_quantitative_record_context(
            QuantitativeRecordContextBinding(
                claim_id="book5-claim-eth",
                record_kind=QuantitativeRecordKind.FLOW,
                asset_ref="csia:token:eth",
                unit="ETH",
            )
        )
        return claims, evidence, provenance

    monkeypatch.setitem(globals(), "kernel", kernel_with_flow_context)
T1 = LATER


def make_position(position_id="pos:r1", *, components=None, **overrides):
    resolved_components = components or component_set(
        component(claim_ref="book5-claim-eth")
    )
    base = dict(
        position_id=position_id,
        position_kind=PositionKind.CLAIM_SIDE,
        asset_ref="csia:token:lp",
        principal_components=resolved_components,
        holder_ref=None,
        protocol_ref="csia:protocol:amm",
        site_ref="csia:site:pool-1",
        location=EconomicLocation(location_type=LocationType.POOL, ref="loc:1"),
        quantity="1",
        unit="LP",
        valid_from=T0,
        observed_at=T0,
        # position refs DERIVE from the nested components: never a separate
        # assertion that could drift from the component basis (R2 S4 closure)
        book2_claim_refs=tuple(
            dict.fromkeys(
                ref
                for c in resolved_components.components
                for ref in c.book2_claim_refs
            )
        ),
    )
    base.update(overrides)
    return CapitalPosition(**base)


def make_flow(flow_id="flow:r1", **overrides):
    base = dict(
        flow_id=flow_id,
        flow_type=FlowType.TRANSFER,
        asset_ref="csia:token:eth",
        quantity="1",
        unit="ETH",
        from_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="b"),
        valid_time=T0,
        observed_at=T0,
        book2_claim_refs=("book5-claim-eth",),
    )
    base.update(overrides)
    return CapitalFlow(**base)


# ---------------------------------------------------------------------------
# R1-D1 / Phase 1 — component attribution basis (A1–A7)
# ---------------------------------------------------------------------------


def _live_provenance():
    return kernel()[2]


def test_a1_unknown_component_upgraded_to_exact_rejected() -> None:
    """A1: UNKNOWN → model_copy EXACT → aggregate must REJECT."""

    provenance = _live_provenance()
    original = component(quantity="3", attribution=AttributionState.UNKNOWN, claim_ref="book5-claim-eth")
    tampered = original.model_copy(update={"attribution_state": AttributionState.EXACT})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_a2_comingled_component_upgraded_to_exact_rejected() -> None:
    """A2: COMMINGLED → model_copy EXACT → aggregate must REJECT."""

    provenance = _live_provenance()
    original = component(
        quantity="800",
        attribution=AttributionState.COMMINGLED,
        claim_ref="book5-claim-pool",
    )
    tampered = original.model_copy(update={"attribution_state": AttributionState.EXACT})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("USDC", provenance=provenance)


def test_a3_proportional_with_generic_claim_rejected() -> None:
    """A3: PROPORTIONAL backed only by a generic (non-proportional) claim."""

    provenance = _live_provenance()
    proportional = component(
        quantity="3",
        attribution=AttributionState.PROPORTIONAL,
        claim_ref="book5-claim-eth",
        share_fraction="0.5",
    )
    component_set_ = PrincipalComponentSet(components=(proportional,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_a4_exact_with_non_exact_claim_rejected() -> None:
    """A4: EXACT backed by a generic (non-exact) claim must be rejected at
    the authority boundary."""

    provenance = _live_provenance()
    exact = component(quantity="3", attribution=AttributionState.EXACT, claim_ref="book5-claim-eth")
    component_set_ = PrincipalComponentSet(components=(exact,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_a5_exact_with_canonical_exact_basis_passes() -> None:
    """A5: proper EXACT component + canonical PRINCIPAL_EXACT_FACT claim."""

    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "exact-basis")
    claims.add_initial(
        make_claim("book5-claim-eth-exact", evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    )
    exact = component(
        quantity="3", attribution=AttributionState.EXACT, claim_ref="book5-claim-eth-exact"
    )
    component_set_ = PrincipalComponentSet(components=(exact,))
    assert component_set_.aggregate_same_unit("ETH", provenance=provenance) == "3"


def test_a6_proportional_with_canonical_proportional_basis_passes() -> None:
    """A6: proper PROPORTIONAL component + PRINCIPAL_PROPORTIONAL_FACT claim."""

    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "prop-basis")
    claims.add_initial(
        make_claim(
            "book5-claim-eth-prop", evidence_ref=evidence_ref, qualifier="PRINCIPAL_PROPORTIONAL_FACT"
        )
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth-prop", asset_ref="csia:token:eth", unit="ETH")
    )
    proportional = component(
        quantity="3",
        attribution=AttributionState.PROPORTIONAL,
        claim_ref="book5-claim-eth-prop",
        share_fraction="0.5",
    )
    component_set_ = PrincipalComponentSet(components=(proportional,))
    assert component_set_.aggregate_same_unit("ETH", provenance=provenance) == "3"


def test_a7_raw_string_state_normalized_only_after_validation() -> None:
    """A7: raw "EXACT" injected via model_copy is never silently trusted."""

    provenance = _live_provenance()
    original = component(quantity="3", attribution=AttributionState.UNKNOWN, claim_ref="book5-claim-eth")
    tampered = original.model_copy(update={"attribution_state": "EXACT"})
    assert not isinstance(tampered.attribution_state, AttributionState)
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


# ---------------------------------------------------------------------------
# R1-D2 / Phase 3 — unit/asset context (B1–B4)
# ---------------------------------------------------------------------------


def test_b1_eth_asset_with_swapped_usdc_unit_rejected_on_aggregate() -> None:
    """B1: ETH asset + ETH claim, unit mutated to USDC → aggregate USDC REJECT."""

    provenance = _live_provenance()
    tampered = component(quantity="3", claim_ref="book5-claim-eth").model_copy(
        update={"unit": "USDC"}
    )
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("USDC", provenance=provenance)


def test_b2_realization_ref_swapped_to_unrelated_rejected() -> None:
    """B2: realization_ref swapped to an unrelated realization → REJECT."""

    provenance = _live_provenance()
    tampered = component(
        quantity="3",
        claim_ref="book5-claim-eth",
        realization_ref="realization:chain-1",
    ).model_copy(update={"realization_ref": "realization:totally-unrelated"})
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("realization:totally-unrelated", provenance=provenance)


def test_b3_asset_ref_changed_while_claim_unchanged_rejected() -> None:
    """B3: asset_ref changed, claim refs unchanged → REJECT."""

    provenance = _live_provenance()
    tampered = component(quantity="3", claim_ref="book5-claim-eth").model_copy(
        update={"asset_ref": "csia:token:wbtc"}
    )
    component_set_ = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        component_set_.aggregate_same_unit("ETH", provenance=provenance)


def test_b4_coherent_context_with_canonical_claim_passes() -> None:
    """B4: valid asset/unit/realization context + canonical supporting claim."""

    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "exact-basis")
    claims.add_initial(
        make_claim("book5-claim-eth-exact", evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id="book5-claim-eth-exact",
            asset_ref="csia:token:eth",
            unit="ETH",
            realization_ref="realization:chain-1",
        )
    )
    coherent = component(
        quantity="3",
        claim_ref="book5-claim-eth-exact",
        realization_ref="realization:chain-1",
    )
    component_set_ = PrincipalComponentSet(components=(coherent,))
    assert (
        component_set_.aggregate_same_unit("realization:chain-1", provenance=provenance) == "3"
    )


# ---------------------------------------------------------------------------
# R1-D3 / Phase 4 — no fabricated zero (C1–C4)
# ---------------------------------------------------------------------------


def test_c1_missing_quantity_never_becomes_zero() -> None:
    """C1: quantity=None edge → materialization must NOT produce "0"."""

    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(contribution("l:eth", "rec:x", quantity=None, unit=None))
    components = g.inspect_components_for("rec:x")
    for c in components.components:
        assert c.quantity != "0"


def test_c2_missing_quantity_explicit_representation() -> None:
    """C2: missing quantity with known attribution → explicit gap, not a
    fabricated quantitative component."""

    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(contribution("l:eth", "rec:x", quantity=None, unit=None))
    components = g.inspect_components_for("rec:x")
    # either the component carries an explicit missing-quantity marker (None)
    # or the set is empty-with-gap; silently materialized numbers are illegal
    for c in components.components:
        assert c.quantity is None or c.quantity == ""


def test_c3_observed_zero_is_representable() -> None:
    """C3: an explicitly evidenced zero is legal."""

    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(contribution("l:eth", "rec:x", quantity="0", unit="ETH"))
    components = g.inspect_components_for("rec:x")
    assert components.components[0].quantity == "0"


def test_c4_missing_and_observed_zero_distinguishable() -> None:
    """C4: missing quantity and observed zero must remain distinguishable."""

    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(contribution("l:eth", "rec:missing", quantity=None, unit=None))
    g.add_edge(contribution("l:eth", "rec:zero", quantity="0", unit="ETH"))
    missing = g.inspect_components_for("rec:missing")
    zero = g.inspect_components_for("rec:zero")
    assert zero.components[0].quantity == "0"
    for c in missing.components:
        assert c.quantity != "0"


# ---------------------------------------------------------------------------
# R1-D3 / Phase 5 — flow-only synthesis (D1–D6)
# ---------------------------------------------------------------------------


def test_d1_flow_only_snapshot_has_no_fabricated_principal() -> None:
    """D1: flows-only composition must not manufacture principal components."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    snapshot = synthesis.compose_snapshot(
        "snap:flow-only", flows=(make_flow(),), valid_time=T0, observed_at=T0
    )
    if snapshot.principal_components is not None:
        for c in snapshot.principal_components.components:
            assert c.asset_ref != "csia:token:none"
            assert c.unit != "NONE"


def test_d2_flow_only_snapshot_expresses_incomplete_state() -> None:
    """D2: flow-only snapshot carries an explicit gap/incomplete state."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    snapshot = synthesis.compose_snapshot(
        "snap:flow-only", flows=(make_flow(),), valid_time=T0, observed_at=T0
    )
    assert snapshot.principal_components is None or snapshot.incomplete


def test_d3_no_placeholder_token_none_anywhere() -> None:
    """D3: "csia:token:none" must never appear in any 5G output."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    snapshot = synthesis.compose_snapshot(
        "snap:flow-only", flows=(make_flow(),), valid_time=T0, observed_at=T0
    )
    assert "csia:token:none" not in snapshot.model_dump_json()


def test_d4_no_fabricated_claim_refs() -> None:
    """D4: no claim ref appears that is not among supplied canonical inputs."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    flow = make_flow()
    snapshot = synthesis.compose_snapshot(
        "snap:flow-only", flows=(flow,), valid_time=T0, observed_at=T0
    )
    if snapshot.principal_components is not None:
        for c in snapshot.principal_components.components:
            for ref in c.book2_claim_refs:
                assert ref in flow.book2_claim_refs


def test_d5_observed_zero_distinct_from_no_observation() -> None:
    """D5: observed economic zero vs no principal observation."""

    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "exact-basis")
    claims.add_initial(
        make_claim("book5-claim-eth-exact", evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    )
    synthesis = CapitalFieldSynthesis(provenance, SynthesisWriteLedger())
    zero_position = make_position(
        "pos:zero",
        components=component_set(
            component(quantity="0", claim_ref="book5-claim-eth-exact")
        ),
    )
    zero_snapshot = synthesis.compose_snapshot(
        "snap:zero", positions=(zero_position,), valid_time=T0, observed_at=T0
    )
    assert zero_snapshot.principal_components is not None
    flow_only = synthesis.compose_snapshot(
        "snap:none", flows=(make_flow(),), valid_time=T0, observed_at=T0
    )
    assert flow_only.principal_components is None


def test_d6_no_fake_component_to_satisfy_pydantic() -> None:
    """D6: empty principal vector must not invent a fake component."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    snapshot = synthesis.compose_snapshot(
        "snap:flow-only", flows=(make_flow(),), valid_time=T0, observed_at=T0
    )
    assert snapshot.principal_components is None
    assert not hasattr(snapshot, "placeholder")


# ---------------------------------------------------------------------------
# R1-D4 / Phase 7 — typed fail-closed guards (E1–E6)
# ---------------------------------------------------------------------------


def _typed_error(exc: Exception) -> bool:

    return isinstance(exc, (LineageError, Book5ProvenanceError))


def test_e1_raw_dict_edge_typed_error_not_attribute_error() -> None:
    """E1: add_edge(raw dict) → typed LineageError, NOT AttributeError."""

    g = CapitalPrincipalLineageGraph()
    with pytest.raises(Exception) as exc_info:
        g.add_edge({"source_lineage_id": "l:x", "target_record_id": "r"})  # type: ignore[arg-type]
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


def test_e2_raw_dict_node_typed_error() -> None:
    """E2: add_node(raw dict) → typed error."""

    g = CapitalPrincipalLineageGraph()
    with pytest.raises(Exception) as exc_info:
        g.add_node({"lineage_id": "l:x"})  # type: ignore[arg-type]
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


def test_e3_raw_position_dict_typed_error() -> None:
    """E3: compose_snapshot(raw position dict) → typed error."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    with pytest.raises(Exception) as exc_info:
        synthesis.compose_snapshot(
            "snap:raw",
            positions=({"position_id": "pos:raw"},),  # type: ignore[list-item]
            valid_time=T0,
            observed_at=T0,
        )
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


def test_e4_nested_raw_component_typed_error() -> None:
    """E4: model_copy position with raw nested component → typed error."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    position = make_position()
    raw_components = position.principal_components.model_copy(
        update={"components": ({"asset_ref": "x"},)}  # type: ignore[dict-item]
    )
    tampered = position.model_copy(update={"principal_components": raw_components})
    with pytest.raises(Exception) as exc_info:
        synthesis.compose_snapshot(
            "snap:nested", positions=(tampered,), valid_time=T0, observed_at=T0
        )
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


def test_e5_liability_raw_dict_typed_error() -> None:
    """E5: raw liability dict at the synthesis boundary → typed error."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    with pytest.raises(Exception) as exc_info:
        synthesis.compose_snapshot(
            "snap:liab",
            liabilities=({"liability_id": "liability:raw"},),  # type: ignore[list-item]
            valid_time=T0,
            observed_at=T0,
        )
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


def test_e6_observed_value_raw_dict_typed_error() -> None:
    """E6: raw observed-value dict → typed error."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    with pytest.raises(Exception) as exc_info:
        synthesis.compose_snapshot(
            "snap:ovf",
            observed_value_facts=({"fact_id": "fact:raw"},),  # type: ignore[list-item]
            valid_time=T0,
            observed_at=T0,
        )
    assert _typed_error(exc_info.value), f"leaked {type(exc_info.value).__name__}"


# ---------------------------------------------------------------------------
# R1-D5 / Phases 8–9 — synthesis provenance set closure (F1–F5)
# ---------------------------------------------------------------------------


def test_f1_stripped_provenance_position_rejected_by_compose() -> None:
    """F1: valid position → model_copy(book2_claim_refs=()) → compose REJECT."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    position = make_position()
    stripped = position.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Exception):
        synthesis.compose_snapshot(
            "snap:stripped", positions=(stripped,), valid_time=T0, observed_at=T0
        )


def test_f2_swapped_unrelated_claim_rejected() -> None:
    """F2: claim refs swapped to an unrelated canonical claim → REJECT."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    position = make_position(
        components=component_set(component(claim_ref="book5-claim-usdc")),
    )
    swapped = position.model_copy(update={"book2_claim_refs": ("book5-claim-vault",)})
    with pytest.raises(Exception):
        synthesis.compose_snapshot(
            "snap:swapped", positions=(swapped,), valid_time=T0, observed_at=T0
        )


def test_f3_nested_component_refs_stripped_rejected() -> None:
    """F3: nested component claim refs stripped while position refs remain."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    position = make_position()
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
    with pytest.raises(Exception):
        synthesis.compose_snapshot(
            "snap:nested-stripped", positions=(tampered,), valid_time=T0, observed_at=T0
        )


def test_f4_position_refs_stripped_nested_remain_rejected() -> None:
    """F4: position refs stripped while nested component refs remain."""

    synthesis = CapitalFieldSynthesis(_live_provenance(), SynthesisWriteLedger())
    position = make_position()
    tampered = position.model_copy(update={"book2_claim_refs": ()})
    with pytest.raises(Exception):
        synthesis.compose_snapshot(
            "snap:pos-stripped", positions=(tampered,), valid_time=T0, observed_at=T0
        )


def test_f5_coherent_canonical_inputs_pass() -> None:
    """F5: all canonical and coherent → PASS."""

    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "exact-basis")
    claims.add_initial(
        make_claim("book5-claim-eth-exact", evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    )
    synthesis = CapitalFieldSynthesis(provenance, SynthesisWriteLedger())
    position = make_position(
        components=component_set(
            component(quantity="3", claim_ref="book5-claim-eth-exact")
        )
    )
    snapshot = synthesis.compose_snapshot(
        "snap:coherent", positions=(position,), valid_time=T0, observed_at=T0
    )
    assert snapshot.input_record_refs == ("pos:r1",)


# ---------------------------------------------------------------------------
# Phase 10 — lineage decision-point revalidation
# ---------------------------------------------------------------------------


def test_lineage_add_edge_tampered_state_rejected_at_collapse_with_provenance() -> None:
    claims, ev, provenance = kernel()
    edge = contribution("l:eth", "rec:x", quantity=None, unit=None).model_copy(
        update={"quantity": "3", "unit": "ETH"}
    )
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(edge)
    # collapse verifies live basis when provenance supplied
    with pytest.raises(Exception):
        g.collapse_same_unit("rec:x", unit="ETH", provenance=provenance)


def test_collapse_with_canonical_basis_passes() -> None:
    claims, ev, provenance = kernel()
    evidence_ref = make_evidence(ev, "exact-basis")
    claims.add_initial(
        make_claim("book5-claim-eth-exact", evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    )
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(
        contribution("l:eth", "rec:x", quantity="3", unit="ETH", claim_ref="book5-claim-eth-exact")
    )
    assert g.collapse_same_unit("rec:x", unit="ETH", provenance=provenance) == "3"


def test_collapse_refuses_quantity_unit_pairing_tamper() -> None:
    """Phase 10: a stripped unit on an attributable edge (quantity kept) is
    caught at the collapse boundary — the node's unit may not silently
    legitimize a tampered pairing."""

    edge = contribution("l:eth", "rec:x", quantity="3", unit="ETH").model_copy(
        update={"unit": None}
    )
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(edge)
    with pytest.raises(Exception):
        g.collapse_same_unit("rec:x", unit="ETH")


def test_components_for_validates_live_state_with_provenance() -> None:
    """Phase 10: components_for() with a provenance revalidates every
    materialized component — a model_copy unit tamper cannot flow through
    lineage into a component vector."""

    provenance = _live_provenance()
    from crypto_systems_intelligence_atlas.book5_provenance import ClaimContextBinding

    provenance.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-eth", asset_ref="csia:token:eth", unit="ETH")
    )
    edge = contribution("l:eth", "rec:x", quantity="3", unit="ETH").model_copy(
        update={"unit": "USDC"}
    )
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    g.add_edge(edge)
    with pytest.raises(Exception):
        g.components_for("rec:x", provenance=provenance)


def test_valuation_state_unchanged() -> None:
    assert VALUATION_NOT_AUTHORIZED == "NOT_AUTHORIZED"
