"""Book 5 bloc kernel tests (5A–5G) and the 45-row stress traceability corpus.

Every stress row from the ratified matrix is exercised with an assertion that
the dangerous behavior fails closed or the allowed behavior succeeds, mapped
by STRESS_ROW_TRACEABILITY at the bottom (plan v0.3; Phase 22).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    AttributionStateError,
    EconomicLocation,
    EconomicSite,
    LocationType,
    PrincipalComponent,
    PrincipalComponentSet,
    SiteType,
)
from crypto_systems_intelligence_atlas.book5_lineage import (
    CapitalPrincipalLineageGraph,
    DebtLiability,
    LineageError,
    PrincipalLineageNode,
    RedemptionClaim,
    ReserveLiability,
    VALUATION_NOT_AUTHORIZED,
    reconcile_projection,
)
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    AppendOnlyFlowLedger,
    CapitalFlow,
    CapitalPosition,
    CapitalTransformation,
    DerivativeExposure,
    EconomicClaim,
    Encumbrance,
    EncumbranceState,
    FlowType,
    ObservedCommonValueFact,
    PositionKind,
    SettlementBalance,
    TransformationKind,
)
from crypto_systems_intelligence_atlas.book5_support import (
    LATER,
    NOW,
    add_claim,
    claim_ref_for,
    component,
    component_set,
    contribution,
    debt_liability,
    graph,
    kernel,
    lineage_node,
    make_claim,
    make_evidence,
    site,
)
from crypto_systems_intelligence_atlas.book5_synthesis import (
    CapitalFieldSynthesis,
    SynthesisWriteLedger,
)

UTC = UTC
T0 = NOW
T1 = LATER


def _bound_exact(
    provenance: Book5Provenance,
    tag: str,
    *,
    asset_ref: str,
    unit: str,
    realization_ref: str | None = None,
) -> str:
    """R2 helper: register a canonical PRINCIPAL_EXACT_FACT claim on the
    provenance's stores AND bind its asset/unit/realization context, so
    authority aggregation exercises the full mandatory-authority seal."""

    evidence_ref = make_evidence(provenance.evidence_store, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    provenance.claim_store.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, qualifier="PRINCIPAL_EXACT_FACT")
    )
    provenance.bind_claim_context(
        ClaimContextBinding(
            claim_id=claim_id,
            asset_ref=asset_ref,
            realization_ref=realization_ref,
            unit=unit,
        )
    )
    return claim_id


def make_position(
    position_id="pos:1",
    *,
    components,
    site_ref="csia:site:pool-1",
    protocol_ref="csia:protocol:amm",
    kind=PositionKind.CLAIM_SIDE,
    quantity="1",
    unit="LP",
    holder=None,
    encumbrance=EncumbranceState.UNENCUMBERED,
    liability_refs=(),
):
    return CapitalPosition(
        position_id=position_id,
        position_kind=kind,
        asset_ref="csia:token:lp",
        principal_components=components,
        holder_ref=holder,
        protocol_ref=protocol_ref,
        site_ref=site_ref,
        location=EconomicLocation(location_type=LocationType.POOL, ref="loc:1"),
        quantity=quantity,
        unit=unit,
        valid_from=T0,
        observed_at=T0,
        book2_claim_refs=tuple(
            ref for c in components.components for ref in c.book2_claim_refs
        ),
        encumbrance_state=encumbrance,
        liability_refs=liability_refs,
    )


# ---------------------------------------------------------------------------
# BLOC 5A — stablecoin rails
# ---------------------------------------------------------------------------


def test_5a_canonical_plus_wrapped_supply_never_double_counts() -> None:
    _, _, prov = kernel()
    fxd = _bound_exact(prov, "fxd-exact", asset_ref="csia:stablecoin:fxd", unit="FXD")
    canonical = PrincipalComponentSet(
        components=(
            PrincipalComponent(
                asset_ref="csia:stablecoin:fxd",
                quantity="1000",
                unit="FXD",
                attribution_state=AttributionState.EXACT,
                book2_claim_refs=(fxd,),
                valid_time=T0,
            ),
        )
    )
    wrapped = PrincipalComponentSet(
        components=(
            PrincipalComponent(
                asset_ref="csia:stablecoin:fxd",
                realization_ref="realization:chain-b:0xwrapped",
                quantity="1000",
                unit="FXD",
                attribution_state=AttributionState.EXACT,
                book2_claim_refs=(fxd,),
                valid_time=T0,
            ),
        )
    )
    # linked, never summed: the wrapped side is a realization with an explicit
    # redemption liability, not additional principal
    assert canonical.aggregate_same_unit("FXD", provenance=prov) == "1000"
    assert wrapped.aggregate_same_unit("FXD", provenance=prov) == "1000"
    assert canonical.components[0].realization_ref is None
    assert wrapped.components[0].realization_ref is not None
    with pytest.raises(Exception):
        PrincipalComponentSet(
            components=canonical.components + wrapped.components
        ).aggregate_same_unit("TOTAL_SUPPLY", provenance=prov)  # no such unit: no summed supply


def test_5a_six_way_supply_separation_representable() -> None:
    _, _, prov = kernel()
    fxd = _bound_exact(prov, "fxd-six-exact", asset_ref="csia:stablecoin:fxd", unit="FXD")
    total_issuance = PrincipalComponent(
        asset_ref="csia:stablecoin:fxd", quantity="10000", unit="FXD",
        attribution_state=AttributionState.EXACT, book2_claim_refs=(fxd,),
        valid_time=T0,
    )
    canonical_circulating = component(
        asset_ref="csia:stablecoin:fxd", quantity="4000", unit="FXD", claim_ref=fxd
    )
    chain_local = PrincipalComponent(
        asset_ref="csia:stablecoin:fxd", realization_ref="realization:chain-2", quantity="3000",
        unit="FXD", attribution_state=AttributionState.EXACT, book2_claim_refs=(fxd,),
        valid_time=T0,
    )
    bridged = PrincipalComponent(
        asset_ref="csia:stablecoin:fxd", realization_ref="realization:chain-2:wrapped", quantity="3000",
        unit="FXD", attribution_state=AttributionState.EXACT, book2_claim_refs=(fxd,),
        valid_time=T0,
    )
    escrow = PrincipalComponent(
        asset_ref="csia:stablecoin:fxd", realization_ref="escrow:bridge-1", quantity="3000",
        unit="FXD", attribution_state=AttributionState.EXACT, book2_claim_refs=(fxd,),
        valid_time=T0,
    )
    redemption_liability = ReserveLiability(
        liability_id="liability:fxd-redemption", issuer_ref="csia:entity:issuer",
        claim_token_ref="csia:stablecoin:fxd",
        backing=component_set(escrow),
        book2_claim_refs=(fxd,), valid_time=T0,
    )
    assert total_issuance.quantity == "10000"
    assert canonical_circulating.quantity == "4000"
    assert chain_local.realization_ref != bridged.realization_ref
    assert redemption_liability.backing.aggregate_same_unit("FXD", provenance=prov) == "3000"


# ---------------------------------------------------------------------------
# BLOC 5B — DEX / liquidity
# ---------------------------------------------------------------------------


def test_5b_reserves_lp_range_flow_volume_route_separation() -> None:
    reserves = SettlementBalance(
        balance_id="bal:pool-1", venue_site_id="csia:site:amm-1",
        principal_components=component_set(
            component(claim_ref="book5-claim-eth"),
            component(asset_ref="csia:token:usdc", quantity="5000", unit="USDC", claim_ref="book5-claim-usdc"),
        ),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth", "book5-claim-usdc"),
    )
    lp_claim = make_position(
        "pos:lp", components=component_set(
            component(claim_ref="book5-claim-eth"),
            component(asset_ref="csia:token:usdc", quantity="5000", unit="USDC", claim_ref="book5-claim-usdc"),
        )
    )
    swap = CapitalFlow(
        flow_id="flow:swap-1", flow_type=FlowType.SWAP, asset_ref="csia:token:eth",
        quantity="1", unit="ETH", from_location=EconomicLocation(location_type=LocationType.POOL, ref="p"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        capability_route_ref="csia:edge:routed-through-1",
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    assert reserves.principal_components.is_heterogeneous()
    assert lp_claim.position_kind is PositionKind.CLAIM_SIDE
    assert swap.flow_type is FlowType.SWAP
    # route reference is a pointer; no volume field exists on the flow
    assert not hasattr(swap, "volume")
    # reserves are not ownership: custody-observation positions cannot claim holders
    with pytest.raises(ValueError):
        make_position(
            "pos:custody", components=component_set(component(claim_ref="book5-claim-eth")),
            kind=PositionKind.CUSTODY_OBSERVATION, holder="csia:entity:invented",
        )


def test_5b_append_only_flow_ledger() -> None:
    ledger = AppendOnlyFlowLedger()
    flow = CapitalFlow(
        flow_id="flow:1", flow_type=FlowType.SWAP, asset_ref="csia:token:eth",
        quantity="1", unit="ETH", from_location=EconomicLocation(location_type=LocationType.POOL, ref="p"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    ledger.append(flow)
    with pytest.raises(Book5ProvenanceError):
        ledger.append(flow)
    replacement = flow.model_copy(update={"flow_id": "flow:1r", "observed_at": T1})
    ledger.supersede("flow:1", replacement=replacement)
    assert ledger.active_flow_ids() == ("flow:1r",)
    assert len(ledger.flows()) == 2  # history remains queryable


# ---------------------------------------------------------------------------
# BLOC 5C — credit / lending
# ---------------------------------------------------------------------------


def test_5c_supplied_plus_borrowed_never_additive() -> None:
    _, _, prov = kernel()
    usdc = _bound_exact(prov, "supplied-usdc-exact", asset_ref="csia:token:usdc", unit="USDC")
    supplied = component_set(
        component(
            asset_ref="csia:token:usdc", quantity="1000", unit="USDC",
            claim_ref=usdc,
        )
    )
    borrowed = debt_liability(quantity="800")
    # 1000 supplied + 800 borrowed != 1800 principal: the debt is a canonical
    # liability record, not capital; there is no cross-record summation API
    assert supplied.aggregate_same_unit("USDC", provenance=prov) == "1000"
    assert borrowed.quantity == "800"
    assert not hasattr(supplied, "add_record")
    assert not hasattr(CapitalPrincipalLineageGraph, "sum_all")


def test_5c_collateral_eligibility_is_not_posted() -> None:
    posted = make_position(
        "pos:coll", components=component_set(component(claim_ref="book5-claim-eth")),
        kind=PositionKind.CLAIM_SIDE, encumbrance=EncumbranceState.PLEDGED,
    )
    encumbrance = Encumbrance(
        encumbrance_id="enc:1", encumbered_ref="pos:coll", state=EncumbranceState.PLEDGED,
        valid_time=T0, book2_claim_refs=("book5-claim-eth",),
    )
    assert posted.encumbrance_state is EncumbranceState.PLEDGED
    assert encumbrance.state is EncumbranceState.PLEDGED
    # eligibility (capability) is a Book 1 edge reference — a position field
    # never claims eligibility by existing
    assert not hasattr(posted, "collateral_enabled")


def test_5c_borrowed_redeposit_carries_pool_commingled_attribution() -> None:
    _, _, prov = kernel()
    prov.bind_claim_context(
        ClaimContextBinding(
            claim_id="book5-claim-pool", asset_ref="csia:token:usdc", unit="USDC"
        )
    )
    g = graph(
        contribution(
            "l:pool", "rec:borrow",
            attribution=AttributionState.COMMINGLED, quantity="800", unit="USDC",
            claim_ref="book5-claim-pool",
        ),
        nodes=(lineage_node("l:pool", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-pool"),),
    )
    # the borrowed USDC's attribution is COMMINGLED: no depositor-unit ancestry
    roots = g.roots_for("rec:borrow")
    assert len(roots) == 1
    # COMMINGLED refuses the exact total under the full authority seal: the
    # arithmetic law fires after basis/context validation, never instead of it
    with pytest.raises(AttributionStateError):
        g.collapse_same_unit("rec:borrow", unit="USDC", provenance=prov)


def test_5c_debt_position_projection_reconciles_with_liability() -> None:
    liability = debt_liability(quantity="800")
    debt_position = make_position(
        "pos:debt",
        components=component_set(
            component(
                asset_ref="csia:token:usdc", quantity="800", unit="USDC",
                attribution=AttributionState.COMMINGLED, claim_ref="book5-claim-pool",
            )
        ),
        kind=PositionKind.LIABILITY_SIDE, quantity="800", unit="USDC",
        site_ref="csia:site:market-1", protocol_ref="csia:protocol:lending",
        liability_refs=(liability.liability_id,),
    )
    assert debt_position.reference_liability(liability, observed_at=T0) == "800"
    drifting = debt_position.model_copy(update={"quantity": "700"})
    with pytest.raises(Book5ProvenanceError):
        drifting.reference_liability(liability, observed_at=T0)


def test_5c_collateral_lineage_never_merges_into_borrowed_lineage() -> None:
    # ETH collateral principal and USDC pool principal are distinct roots; a
    # DebtLiability relates them economically without merging lineages
    g = graph(
        contribution("l:eth-collateral", "rec:collateral"),
        contribution(
            "l:usdc-pool", "rec:borrowed",
            attribution=AttributionState.COMMINGLED, quantity="800", unit="USDC",
            claim_ref="book5-claim-pool",
        ),
        nodes=(
            lineage_node("l:eth-collateral"),
            lineage_node("l:usdc-pool", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-pool"),
        ),
    )
    eth_roots = g.roots_for("rec:collateral")
    usdc_roots = g.roots_for("rec:borrowed")
    assert [n.lineage_id for n in eth_roots] == ["l:eth-collateral"]
    assert [n.lineage_id for n in usdc_roots] == ["l:usdc-pool"]
    # no lineage path exists between the two roots
    assert "l:eth-collateral" not in [n.lineage_id for n in usdc_roots]


# ---------------------------------------------------------------------------
# BLOC 5D — staking / restaking / yield
# ---------------------------------------------------------------------------


def test_5d_eth_lst_restake_single_lineage_no_multiplication() -> None:
    _, _, prov = kernel()
    eth = _bound_exact(prov, "lst-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    g = graph(
        contribution("l:eth", "rec:staked", claim_ref=eth),
        contribution("l:eth", "rec:lst-claim", claim_ref=eth),
        contribution("l:eth", "rec:restaked", claim_ref=eth),
        nodes=(lineage_node("l:eth", claim_ref=eth),),
    )
    # three representations, ONE principal root; each record's collapse is the
    # same principal quantity — never 3x TVL
    for record in ("rec:staked", "rec:lst-claim", "rec:restaked"):
        assert [n.lineage_id for n in g.roots_for(record)] == ["l:eth"]
        assert g.collapse_same_unit(record, unit="ETH", provenance=prov) == "3"


def test_5d_yield_credit_is_a_flow_not_a_claim() -> None:
    yield_credit = CapitalFlow(
        flow_id="flow:yield", flow_type=FlowType.YIELD_CREDIT, asset_ref="csia:token:eth",
        quantity="0.1", unit="ETH", from_location=EconomicLocation(location_type=LocationType.VALIDATOR, ref="v"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    assert yield_credit.flow_type is FlowType.YIELD_CREDIT
    # the claim position and the realized yield are different records; no
    # yield-rate field exists anywhere in the kernel
    assert not hasattr(yield_credit, "apy")


# ---------------------------------------------------------------------------
# BLOC 5E — derivatives / leverage
# ---------------------------------------------------------------------------


def test_5e_notional_never_enters_principal_sums() -> None:
    _, _, prov = kernel()
    usdc = _bound_exact(prov, "margin-usdc-exact", asset_ref="csia:token:usdc", unit="USDC")
    exposure = DerivativeExposure(
        exposure_id="exp:1", instrument_ref="csia:market:perp-eth", site_ref="csia:site:perp-1",
        notional_quantity="1000", notional_unit="USD-NOTIONAL", direction="LONG",
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    collateral = make_position(
        "pos:margin", components=component_set(
            component(asset_ref="csia:token:usdc", quantity="100", unit="USDC", claim_ref=usdc)
        ),
        quantity="100", unit="USDC", encumbrance=EncumbranceState.PLEDGED,
        site_ref="csia:site:perp-1", protocol_ref="csia:protocol:perp",
    )
    # exposure quantities live on the exposure record; the position's
    # principal components remain asset-denominated; no API sums them
    assert exposure.notional_unit == "USD-NOTIONAL"
    assert collateral.principal_components.aggregate_same_unit("USDC", provenance=prov) == "100"
    assert not hasattr(exposure, "principal_components")
    assert not hasattr(collateral, "notional")


def test_5e_unrealized_pnl_is_not_a_position_field() -> None:
    exposure = DerivativeExposure(
        exposure_id="exp:2", instrument_ref="csia:market:perp-eth", site_ref="csia:site:perp-1",
        notional_quantity="1000", notional_unit="USD-NOTIONAL", direction="LONG",
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    assert not hasattr(exposure, "unrealized_pnl")


# ---------------------------------------------------------------------------
# BLOC 5F — RWA / payments
# ---------------------------------------------------------------------------


def test_5f_token_supply_never_equals_offchain_value_without_evidence() -> None:
    token = PrincipalComponent(
        asset_ref="csia:rwa:treasury-token", quantity="1000000", unit="TST",
        attribution_state=AttributionState.EXACT, book2_claim_refs=("book5-claim-base",),
        valid_time=T0,
    )
    claim = RedemptionClaim(
        claim_id="claim:rwa-1", liability_id="liability:spv-1", quantity="1000000",
        unit="TST", book2_claim_refs=("book5-claim-base",), valid_time=T0,
    )
    # the redemption claim is the evidence-backed equivalence; without it no
    # equivalence field exists anywhere on the token component
    assert not hasattr(token, "offchain_value")
    assert claim.quantity == "1000000"


def test_5f_payment_and_settlement_are_flows() -> None:
    for flow_type in (FlowType.PAYMENT, FlowType.SETTLEMENT, FlowType.REDEEM, FlowType.OFF_RAMP):
        flow = CapitalFlow(
            flow_id=f"flow:{flow_type.value}", flow_type=flow_type,
            asset_ref="csia:stablecoin:fxd", quantity="10", unit="FXD",
            from_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
            to_location=EconomicLocation(location_type=LocationType.PAYMENT_ENDPOINT, ref="pe:1")
            if flow_type is not FlowType.OFF_RAMP
            else EconomicLocation(location_type=LocationType.OUTSIDE_MODELED_SYSTEM, ref="boundary:modeled"),
            valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-base",),
        )
        assert flow.flow_type is flow_type


# ---------------------------------------------------------------------------
# BLOC 5G — synthesis (T-1..T-14 behaviors; canonical writes; valuation)
# ---------------------------------------------------------------------------


def test_5g_heterogeneous_vector_preserved_never_scalar() -> None:
    _, _, prov = kernel()
    ledger = SynthesisWriteLedger()
    synthesis = CapitalFieldSynthesis(prov, ledger)
    eth_ref = _bound_exact(prov, "t1-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    usdc_ref = _bound_exact(prov, "t1-usdc-exact", asset_ref="csia:token:usdc", unit="USDC")
    g = graph(
        contribution("l:eth", "rec:lp", claim_ref=eth_ref),
        contribution("l:usdc", "rec:lp", quantity="5000", unit="USDC", claim_ref=usdc_ref),
        nodes=(
            lineage_node("l:eth", claim_ref=eth_ref),
            lineage_node("l:usdc", asset_ref="csia:token:usdc", unit="USDC", claim_ref=usdc_ref),
        ),
    )
    kind, total, vector = synthesis.collapse_request(graph=g, record_id="rec:lp", unit="ETH")
    assert kind == "HETEROGENEOUS_VECTOR"
    assert total is None
    assert vector is not None and vector.is_heterogeneous()


def test_5g_same_unit_collapse_permitted() -> None:
    _, _, prov = kernel()
    ledger = SynthesisWriteLedger()
    synthesis = CapitalFieldSynthesis(prov, ledger)
    eth_ref = _bound_exact(prov, "t14-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    g = graph(
        contribution("l:eth", "rec:a", claim_ref=eth_ref),
        nodes=(lineage_node("l:eth", claim_ref=eth_ref),),
    )
    kind, total, vector = synthesis.collapse_request(graph=g, record_id="rec:a", unit="ETH")
    assert kind == "SAME_UNIT_COLLAPSE"
    assert total == "3"
    assert vector is None


def test_5g_valuation_request_not_authorized() -> None:
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov)
    assert synthesis.valuation_request() == "NOT_AUTHORIZED"
    assert synthesis.valuation_request() != "UNKNOWN"


def test_5g_snapshot_propagates_unknown_not_zero_fill() -> None:
    _, _, prov = kernel()
    prov.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-usdc", asset_ref="csia:token:usdc", unit="USDC")
    )
    synthesis = CapitalFieldSynthesis(prov)
    unknown_position = make_position(
        "pos:unknown",
        components=component_set(
            component(
                asset_ref="csia:token:usdc", quantity="0", unit="USDC",
                attribution=AttributionState.UNKNOWN, claim_ref="book5-claim-usdc",
            )
        ),
        quantity="0", unit="USDC", site_ref="csia:site:market-1",
        protocol_ref="csia:protocol:lending",
    )
    snapshot = synthesis.compose_snapshot(
        "snap:unknown", positions=(unknown_position,), valid_time=T0, observed_at=T0
    )
    assert snapshot.incomplete
    assert snapshot.gaps[0].missing_input_ref == "pos:unknown"


def test_5g_snapshot_carries_methodology_inputs_and_derived_mark() -> None:
    _, _, prov = kernel()
    eth_ref = _bound_exact(prov, "meta-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    synthesis = CapitalFieldSynthesis(prov)
    position = make_position("pos:x", components=component_set(component(claim_ref=eth_ref)))
    snapshot = synthesis.compose_snapshot("snap:x", positions=(position,), valid_time=T0, observed_at=T0)
    assert snapshot.derived is True
    assert snapshot.methodology_id == "5g-capital-field-composition"
    assert snapshot.methodology_version == "5g-compose-v1"
    assert "pos:x" in snapshot.input_record_refs
    assert snapshot.valid_time == T0


def test_5g_canonical_write_count_zero_by_construction() -> None:
    _, _, prov = kernel()
    eth_ref = _bound_exact(prov, "w-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    ledger = SynthesisWriteLedger()
    synthesis = CapitalFieldSynthesis(prov, ledger)
    position = make_position("pos:w", components=component_set(component(claim_ref=eth_ref)))
    synthesis.compose_snapshot("snap:w", positions=(position,), valid_time=T0, observed_at=T0)
    synthesis.lineage_view(
        "view:w", graph=graph(contribution("l:eth", "pos:w", claim_ref=eth_ref), nodes=(lineage_node("l:eth", claim_ref=eth_ref),)),
        target_record_id="pos:w", valid_time=T0, observed_at=T0,
    )
    synthesis.topology_view(
        "topo:w", node_record_refs=("pos:w",), valid_time=T0, observed_at=T0
    )
    assert ledger.canonical_write_count == 0
    assert ledger.composition_count == 3


def test_5g_observed_value_fact_display_never_conversion() -> None:
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov)
    fact = ObservedCommonValueFact(
        fact_id="fact:reserves", reported_value="40000000000", numeraire="USD",
        reporter_ref="csia:entity:issuer", subject_ref="csia:stablecoin:fxd",
        observed_at=T0, valid_time=T0, book2_claim_refs=("book5-claim-base",),
    )
    display = synthesis.observed_value_display(fact)
    assert display["display"] == "OBSERVED_COMMON_VALUE_FACT"
    assert display["reported_value"] == "40000000000"


def test_5g_snapshot_replay_consistency() -> None:
    _, _, prov = kernel()
    eth_ref = _bound_exact(prov, "replay-eth-exact", asset_ref="csia:token:eth", unit="ETH")
    synthesis_a = CapitalFieldSynthesis(prov)
    synthesis_b = CapitalFieldSynthesis(prov)
    position = make_position("pos:r", components=component_set(component(claim_ref=eth_ref)))
    snap_a = synthesis_a.compose_snapshot("snap:r", positions=(position,), valid_time=T0, observed_at=T0)
    snap_b = synthesis_b.compose_snapshot("snap:r", positions=(position,), valid_time=T0, observed_at=T0)
    assert snap_a == snap_b  # same inputs + methodology => identical output
    snap_t2 = synthesis_a.compose_snapshot(
        "snap:r-t2", positions=(position,), valid_time=T1, observed_at=T1
    )
    assert snap_t2.valid_time == T1 != snap_a.valid_time


def test_5g_composition_requires_canonical_inputs() -> None:
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov)
    with pytest.raises(Book5ProvenanceError):
        synthesis.compose_snapshot("snap:empty", valid_time=T0, observed_at=T0)


# ---------------------------------------------------------------------------
# 45-ROW STRESS TRACEABILITY (Phase 22)
# ---------------------------------------------------------------------------

STRESS_ROW_TRACEABILITY: dict[str, str] = {
    # rows 1-10: promoted D7 corpus
    "1": "test_5c_supplied_plus_borrowed_never_additive",
    "2": "test_5c_borrowed_redeposit_carries_pool_commingled_attribution",
    "3": "test_5d_eth_lst_restake_single_lineage_no_multiplication",
    "4": "test_5d_eth_lst_restake_single_lineage_no_multiplication",
    "5": "test_5c_collateral_eligibility_is_not_posted",
    "6": "test_5a_canonical_plus_wrapped_supply_never_double_counts",
    "7": "test_5d_eth_lst_restake_single_lineage_no_multiplication",
    "8": "test_5e_notional_never_enters_principal_sums",
    "9": "test_5f_token_supply_never_equals_offchain_value_without_evidence",
    "10": "test_5c_collateral_eligibility_is_not_posted",
    # rows 11-25: structural (11/12/17/19/20/21/23 covered in test_book5_core)
    "11": "book5_core::test_rehypothecation_chain_preserves_source_set",
    "12": "book5_core::test_lineage_fan_out_one_root_many_records",
    "13": "test_5d_eth_lst_restake_single_lineage_no_multiplication",
    "14": "test_5e_notional_never_enters_principal_sums",
    "15": "test_5b_append_only_flow_ledger",
    "16": "test_5c_supplied_plus_borrowed_never_additive",
    "17": "book5_core::test_attribution_arithmetic_law",
    "18": "test_5b_reserves_lp_range_flow_volume_route_separation",
    "19": "book5_core::test_unknown_location_never_carries_precision",
    "20": "book5_core::test_unknown_location_never_carries_precision",
    "21": "book5_core::test_unpromotable_claim_state_fails_closed",
    "22": "test_5f_token_supply_never_equals_offchain_value_without_evidence",
    "23": "book5_core::test_site_requires_book1_anchors_and_valid_time",
    "24": "test_5b_append_only_flow_ledger",
    "25": "test_5f_token_supply_never_equals_offchain_value_without_evidence",
    # rows 26-35: attribution
    "26": "test_5g_heterogeneous_vector_preserved_never_scalar",
    "27": "test_5g_heterogeneous_vector_preserved_never_scalar",
    "28": "test_5c_borrowed_redeposit_carries_pool_commingled_attribution",
    "29": "test_5c_collateral_lineage_never_merges_into_borrowed_lineage",
    "30": "test_5c_collateral_eligibility_is_not_posted",
    "31": "test_5a_six_way_supply_separation_representable",
    "32": "test_5g_observed_value_fact_display_never_conversion",
    "33": "test_5b_reserves_lp_range_flow_volume_route_separation",
    "34": "test_5g_snapshot_propagates_unknown_not_zero_fill",
    "35": "book5_core::test_derived_allocation_requires_methodology_fraction",
    # rows 36-45: unit-domain
    "36": "test_5g_heterogeneous_vector_preserved_never_scalar",
    "37": "test_5g_heterogeneous_vector_preserved_never_scalar",
    "38": "test_5c_collateral_eligibility_is_not_posted",
    "39": "test_5a_six_way_supply_separation_representable",
    "40": "test_5g_observed_value_fact_display_never_conversion",
    "41": "test_5f_token_supply_never_equals_offchain_value_without_evidence",
    "42": "book5_core::test_lp_multi_root_vector_is_heterogeneous",
    "43": "book5_core::test_lp_multi_root_vector_is_heterogeneous",
    "44": "test_5g_observed_value_fact_display_never_conversion",
    "45": "test_5g_valuation_request_not_authorized",
}


def test_stress_traceability_complete() -> None:
    """Every stress row maps to an existing test in this module or core module."""

    import sys
    from pathlib import Path

    module = sys.modules[__name__]
    assert sorted(STRESS_ROW_TRACEABILITY, key=int) == [str(i) for i in range(1, 46)]
    core_test_source = (Path(__file__).parent / "test_book5_core.py").read_text(
        encoding="utf-8"
    )
    for row, target in STRESS_ROW_TRACEABILITY.items():
        mod_name, _, test_name = target.partition("::")
        if mod_name == "book5_core":
            assert test_name in core_test_source, (
                f"row {row} maps to missing core test {target}"
            )
        else:
            assert hasattr(module, target), f"row {row} maps to missing test {target}"
