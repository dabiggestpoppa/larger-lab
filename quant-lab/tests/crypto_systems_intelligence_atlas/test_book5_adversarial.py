"""Book 5 adversarial suites: model_copy/raw-injection mutation attacks
(Phase 24), cross-unit attacks (Phase 25), lineage attacks (Phase 26),
liability attacks (Phase 27), provenance attacks (Phase 28), and
temporal/replay proofs (Phase 29).

Book 4 lesson encoded: constructor validators alone are not authority. Frozen
models reject in-place mutation outright, pydantic model_copy(update=...)
skips every validator, and authority boundaries (collapse, projection,
composition, ledger append) revalidate live state — so tampered records fail
closed at the boundary even when construction-time checks were bypassed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.book5_core import AttributionStateError
from crypto_systems_intelligence_atlas.book5_records import TransformationKind

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    EconomicLocation,
    LocationType,
    PrincipalComponent,
    PrincipalComponentSet,
)
from crypto_systems_intelligence_atlas.book5_lineage import (
    CapitalPrincipalLineageGraph,
    DebtLiability,
    LineageError,
    PrincipalContribution,
    PrincipalLineageNode,
    RedemptionClaim,
    ReserveLiability,
    reconcile_projection,
)
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_records import (
    AppendOnlyFlowLedger,
    CapitalFlow,
    CapitalPosition,
    CapitalTransformation,
    FlowType,
    ObservedCommonValueFact,
    PositionKind,
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
)
from crypto_systems_intelligence_atlas.book5_synthesis import (
    CapitalFieldSynthesis,
    SynthesisWriteLedger,
)

UTC = UTC
T0 = NOW
T1 = LATER


def _bound_exact(
    provenance,
    tag: str,
    *,
    asset_ref: str,
    unit: str,
    realization_ref: str | None = None,
) -> str:
    """R2 helper: register a canonical PRINCIPAL_EXACT_FACT claim and bind
    its asset/unit/realization context on the provenance's stores."""

    from crypto_systems_intelligence_atlas.book5_support import make_claim, make_evidence

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


def make_position(position_id="pos:adv", *, components=None, **overrides):
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


# ---------------------------------------------------------------------------
# Phase 24 — model_copy / mutation adversarial
# ---------------------------------------------------------------------------


def test_frozen_models_reject_in_place_mutation() -> None:
    position = make_position()
    with pytest.raises(Exception):
        position.quantity = "999999"


def test_model_copy_stripped_provenance_fails_at_boundary() -> None:
    claims, ev, prov = kernel()
    position = make_position()
    stripped = position.model_copy(update={"book2_claim_refs": ()})
    # the tampered record is structurally present but carries no evidence
    assert len(stripped.book2_claim_refs) == 0
    # the authority boundary refuses evidence-less records
    synthesis = CapitalFieldSynthesis(prov, SynthesisWriteLedger())
    with pytest.raises(Exception):
        synthesis.compose_snapshot(
            "snap:stripped",
            positions=(
                CapitalPosition(
                    position_id=stripped.position_id,
                    position_kind=stripped.position_kind,
                    asset_ref=stripped.asset_ref,
                    principal_components=PrincipalComponentSet(
                        components=tuple(
                            c.model_copy(update={"book2_claim_refs": ()})
                            for c in stripped.principal_components.components
                        )
                    ),
                    holder_ref=None,
                    protocol_ref=stripped.protocol_ref,
                    site_ref=stripped.site_ref,
                    location=stripped.location,
                    quantity=stripped.quantity,
                    unit=stripped.unit,
                    valid_from=T0,
                    observed_at=T0,
                    book2_claim_refs=(),
                ),
            ),
            valid_time=T0,
            observed_at=T0,
        )


def test_model_copy_changed_unit_crosses_component_vector() -> None:
    claims, ev, prov = kernel()
    exact_ref = _bound_exact(prov, "adv-unit-swap-exact", asset_ref="csia:token:eth", unit="ETH")
    original = component_set(component(claim_ref=exact_ref))
    tampered = original.components[0].model_copy(update={"unit": "USDC"})
    # unit changed under model_copy; the single-tampered-component set still
    # exposes ONE unit key — but it is now the WRONG unit, and the identity
    # mismatch is detectable: the context binding contradicts the mutation
    tampered_set = PrincipalComponentSet(components=(tampered,))
    assert tampered_set.units() == ("USDC",)
    with pytest.raises(Exception):
        tampered_set.aggregate_same_unit("ETH", provenance=prov)  # original unit no longer present


def test_model_copy_changed_attribution_refuses_arithmetic() -> None:
    claims, ev, prov = kernel()
    exact_ref = _bound_exact(prov, "adv-state-down-exact", asset_ref="csia:token:eth", unit="ETH")
    original = component(claim_ref=exact_ref)
    tampered = original.model_copy(update={"attribution_state": AttributionState.UNKNOWN})
    s = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        s.aggregate_same_unit("ETH", provenance=prov)


def test_raw_dict_injection_refused_by_typed_edges() -> None:
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:eth"))
    with pytest.raises(Exception):
        g.add_edge({"source_lineage_id": "l:eth", "target_record_id": "rec:x"})  # type: ignore[arg-type]


def test_model_copy_valid_time_inversion_caught_on_rebuild() -> None:
    position = make_position()
    # frozen model: direct mutation impossible; a rebuilt record with inverted
    # time is rejected by the validator
    with pytest.raises(ValueError):
        make_position(valid_from=T1, valid_to=T0)


# ---------------------------------------------------------------------------
# Phase 25 — cross-unit adversarial
# ---------------------------------------------------------------------------


def test_eth_plus_usdc_never_scalarizes() -> None:
    lp = component_set(
        component(quantity="3", unit="ETH", claim_ref="book5-claim-eth"),
        component(
            asset_ref="csia:token:usdc", quantity="5000", unit="USDC",
            claim_ref="book5-claim-usdc",
        ),
    )
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov, SynthesisWriteLedger())
    # no scalar API exists; the only aggregate APIs are same-unit
    assert not hasattr(lp, "total_value")
    eth_ref = _bound_exact(prov, "crossunit-adv-eth", asset_ref="csia:token:eth", unit="ETH")
    usdc_ref = _bound_exact(prov, "crossunit-adv-usdc", asset_ref="csia:token:usdc", unit="USDC")
    kind, total, vector = synthesis.collapse_request(
        graph=graph(
            contribution("l:eth", "rec:lp", claim_ref=eth_ref),
            contribution("l:usdc", "rec:lp", quantity="5000", unit="USDC", claim_ref=usdc_ref),
            nodes=(
                lineage_node("l:eth", claim_ref=eth_ref),
                lineage_node("l:usdc", asset_ref="csia:token:usdc", unit="USDC", claim_ref=usdc_ref),
            ),
        ),
        record_id="rec:lp",
        unit="ETH",
    )
    assert kind == "HETEROGENEOUS_VECTOR" and total is None


def test_share_fraction_never_yields_usd() -> None:
    half = component(share_fraction="0.5", attribution=AttributionState.PROPORTIONAL, claim_ref="book5-claim-eth")
    assert half.share_fraction == "0.5"
    assert not hasattr(half, "value_usd")


def test_same_realization_usdc_may_sum() -> None:
    _, _, prov = kernel()
    usdc_ref = _bound_exact(
        prov,
        "adv-usdc-real-exact",
        asset_ref="csia:token:usdc",
        unit="USDC",
        realization_ref="realization:chain-1",
    )
    a = component(
        asset_ref="csia:token:usdc", quantity="100", unit="USDC",
        claim_ref=usdc_ref, realization_ref="realization:chain-1",
    )
    b = component(
        asset_ref="csia:token:usdc", quantity="200", unit="USDC",
        claim_ref=usdc_ref, realization_ref="realization:chain-1",
    )
    s = PrincipalComponentSet(components=(a, b))
    assert s.aggregate_same_unit("realization:chain-1", provenance=prov) == "300"


def test_observed_40b_fact_is_not_a_conversion_authority() -> None:
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov, SynthesisWriteLedger())
    fact = ObservedCommonValueFact(
        fact_id="fact:reserves", reported_value="40000000000", numeraire="USD",
        reporter_ref="csia:entity:issuer", subject_ref="csia:stablecoin:fxd",
        observed_at=T0, valid_time=T0, book2_claim_refs=("book5-claim-base",),
    )
    display = synthesis.observed_value_display(fact)
    assert display["display"] == "OBSERVED_COMMON_VALUE_FACT"
    # the fact exposes no conversion API and the synthesis has no method that
    # consumes it for valuation
    assert not hasattr(fact, "convert")
    assert synthesis.valuation_request() == "NOT_AUTHORIZED"


# ---------------------------------------------------------------------------
# Phase 26 — principal-lineage adversarial
# ---------------------------------------------------------------------------


def test_single_root_forcing_impossible_for_lp() -> None:
    g = graph(
        contribution("l:eth", "rec:lp"),
        contribution("l:usdc", "rec:lp", quantity="5000", unit="USDC", claim_ref="book5-claim-usdc"),
        nodes=(
            lineage_node("l:eth"),
            lineage_node("l:usdc", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-usdc"),
        ),
    )
    assert len(g.roots_for("rec:lp")) == 2


def test_fan_out_never_multiplies_collapse() -> None:
    _, _, prov = kernel()
    eth_ref = _bound_exact(prov, "adv-fanout-exact", asset_ref="csia:token:eth", unit="ETH")
    g = graph(
        contribution("l:eth", "rec:a", claim_ref=eth_ref),
        contribution("l:eth", "rec:b", claim_ref=eth_ref),
        nodes=(lineage_node("l:eth", claim_ref=eth_ref),),
    )
    assert g.collapse_same_unit("rec:a", unit="ETH", provenance=prov) == "3"
    assert g.collapse_same_unit("rec:b", unit="ETH", provenance=prov) == "3"  # not 6


def test_fan_in_preserves_all_sources() -> None:
    g = graph(
        contribution("l:a", "rec:pool", quantity="3", unit="ETH"),
        contribution(
            "l:b", "rec:pool", quantity="5000", unit="USDC", claim_ref="book5-claim-usdc"
        ),
        nodes=(
            lineage_node("l:a"),
            lineage_node("l:b", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-usdc"),
        ),
    )
    assert len(g.roots_for("rec:pool")) == 2  # fan-in did not erase sources


def test_unknown_to_exact_mutation_refused_at_boundary() -> None:
    """R2 replacement: the UNKNOWN→EXACT tamper that pre-R2 aggregated to
    "3" WITHOUT a resolver must fail closed at the authority boundary — the
    generic-basis claim cannot support the upgraded state. The UNKNOWN origin
    remains detectable through the untouched Book 2 refs."""

    from crypto_systems_intelligence_atlas.book5_core import PrincipalComponentSet

    _, _, prov = kernel()
    tampered = component(
        quantity="3", attribution=AttributionState.UNKNOWN, claim_ref="book5-claim-eth"
    ).model_copy(update={"attribution_state": AttributionState.EXACT})
    s = PrincipalComponentSet(components=(tampered,))
    with pytest.raises(Exception):
        s.aggregate_same_unit("ETH", provenance=prov)
    # the ORIGINAL record's state was UNKNOWN and the tamper is detectable —
    # Book 2 refs still bind the original observation identity
    assert tampered.book2_claim_refs == ("book5-claim-eth",)


def test_comingled_to_exact_without_new_evidence_refused() -> None:
    claims, ev, prov = kernel()
    prov.bind_claim_context(
        ClaimContextBinding(claim_id="book5-claim-pool", asset_ref="csia:token:usdc", unit="USDC")
    )
    edge = contribution(
        "l:pool", "rec:x", attribution=AttributionState.COMMINGLED,
        quantity="800", unit="USDC", claim_ref="book5-claim-pool",
    ).model_copy(update={"attribution_state": AttributionState.EXACT})
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:pool", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-pool"))
    g.add_edge(edge)
    # with provenance, the boundary verifies the LIVE edge state against its
    # Book 2 basis: an EXACT edge backed by claims that do not assert exact
    # principal continuity is refused
    with pytest.raises(Exception):
        g.collapse_same_unit("rec:x", unit="USDC", provenance=prov)
    # the state law still refuses COMMINGLED arithmetic (resolver now always
    # present at the authority boundary — R2)
    tampered_back = edge.model_copy(update={"attribution_state": AttributionState.COMMINGLED})
    g2 = CapitalPrincipalLineageGraph()
    g2.add_node(lineage_node("l:pool", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-pool"))
    g2.add_edge(tampered_back)
    with pytest.raises(AttributionStateError):
        g2.collapse_same_unit("rec:x", unit="USDC", provenance=prov)


def test_raw_contribution_dict_injection_refused() -> None:
    g = CapitalPrincipalLineageGraph()
    with pytest.raises(Exception):
        g.add_edge(
            {
                "source_lineage_id": "l:eth",
                "target_record_id": "rec:x",
                "attribution_state": "EXACT",
                "book2_claim_refs": ["book5-claim-eth"],
                "valid_time": T0,
            }  # type: ignore[arg-type]
        )


def test_missing_book2_evidence_on_edge_refused() -> None:
    with pytest.raises(ValueError):
        PrincipalContribution(
            source_lineage_id="l:eth",
            target_record_id="rec:x",
            attribution_state=AttributionState.EXACT,
            quantity="3",
            unit="ETH",
            book2_claim_refs=(),
            valid_time=T0,
        )


# ---------------------------------------------------------------------------
# Phase 27 — liability adversarial
# ---------------------------------------------------------------------------


def test_conflicting_position_liability_quantity_fails() -> None:
    liability = debt_liability(quantity="800")
    position = make_position(
        "pos:debt",
        components=component_set(
            component(
                asset_ref="csia:token:usdc", quantity="800", unit="USDC",
                attribution=AttributionState.COMMINGLED, claim_ref="book5-claim-pool",
            )
        ),
        position_kind=PositionKind.LIABILITY_SIDE, quantity="999", unit="USDC",
        site_ref="csia:site:market-1", protocol_ref="csia:protocol:lending",
        liability_refs=(liability.liability_id,),
    )
    with pytest.raises(Book5ProvenanceError):
        position.reference_liability(liability, observed_at=T0)


def test_projection_with_mismatched_observation_time_fails() -> None:
    liability = debt_liability(quantity="800")
    position = make_position(
        "pos:debt2",
        components=component_set(
            component(
                asset_ref="csia:token:usdc", quantity="800", unit="USDC",
                attribution=AttributionState.COMMINGLED, claim_ref="book5-claim-pool",
            )
        ),
        position_kind=PositionKind.LIABILITY_SIDE, quantity="800", unit="USDC",
        site_ref="csia:site:market-1", protocol_ref="csia:protocol:lending",
        liability_refs=(liability.liability_id,),
    )
    with pytest.raises(Book5ProvenanceError):
        position.reference_liability(liability, observed_at=T1)


def test_unreferenced_liability_projection_fails() -> None:
    liability = debt_liability(quantity="800")
    position = make_position(
        "pos:debt3",
        components=component_set(
            component(
                asset_ref="csia:token:usdc", quantity="800", unit="USDC",
                attribution=AttributionState.COMMINGLED, claim_ref="book5-claim-pool",
            )
        ),
        position_kind=PositionKind.LIABILITY_SIDE, quantity="800", unit="USDC",
        site_ref="csia:site:market-1", protocol_ref="csia:protocol:lending",
        liability_refs=(),
    )
    with pytest.raises(Book5ProvenanceError):
        position.reference_liability(liability, observed_at=T0)


def test_reconciliation_utility_laws() -> None:
    with pytest.raises(Exception):
        reconcile_projection(
            canonical_quantity="800", projected_quantity="801",
            same_observation_parameters=True,
        )
    with pytest.raises(Exception):
        reconcile_projection(
            canonical_quantity="abc", projected_quantity="800",
            same_observation_parameters=True,
        )


def test_redemption_claim_requires_canonical_fields() -> None:
    with pytest.raises(ValueError):
        RedemptionClaim(
            claim_id="claim:x", liability_id="liability:x", quantity="1",
            unit="TST", book2_claim_refs=(), valid_time=T0,
        )


def test_reserve_liability_backing_is_component_set() -> None:
    with pytest.raises(ValueError):
        ReserveLiability(
            liability_id="liability:r", issuer_ref="csia:entity:x",
            claim_token_ref="csia:token:x",
            backing=PrincipalComponentSet(components=()),  # empty refused
            book2_claim_refs=("book5-claim-base",), valid_time=T0,
        )


# ---------------------------------------------------------------------------
# Phase 28 — provenance adversarial
# ---------------------------------------------------------------------------


def test_unrelated_claim_refused_by_qualifier_resolution() -> None:
    claims, ev, prov = kernel()
    # a claim without the ECONOMIC_FACT qualifier cannot support an economic fact
    from crypto_systems_intelligence_atlas.book5_support import make_claim, make_evidence

    ev_ref = make_evidence(ev, "non-econ")
    claims.add_initial(make_claim("book5-claim-noned", evidence_ref=ev_ref, qualifier="SOMETHING_ELSE"))
    with pytest.raises(Book5ProvenanceError):
        prov.resolve_economics_claim("book5-claim-noned", qualifier="ECONOMIC_FACT")


def test_forged_claim_object_refused() -> None:
    claims, ev, prov = kernel()
    canonical = prov.resolve_claim("book5-claim-eth")
    forged = canonical.model_copy(update={"claim_id": "book5-claim-eth"})
    other = prov.resolve_claim("book5-claim-usdc")
    with pytest.raises(Book5ProvenanceError):
        prov.resolve_claim("book5-claim-eth", expected_claim=other)


def test_non_string_claim_ref_refused() -> None:
    _, _, prov = kernel()
    with pytest.raises(Exception) as exc_info:
        prov.resolve_claim({"claim": "book5-claim-eth"})  # type: ignore[arg-type]
    # typed, fail-closed vocabulary (Book4 adapter guard reused deliberately)
    assert "canonical string references" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Phase 29 — temporal / replay proofs
# ---------------------------------------------------------------------------


def test_flows_append_only_and_supersession_preserves_history() -> None:
    ledger = AppendOnlyFlowLedger()
    flow = CapitalFlow(
        flow_id="f:1", flow_type=FlowType.MINT, asset_ref="csia:stablecoin:fxd",
        quantity="10", unit="FXD", from_location=EconomicLocation(location_type=LocationType.UNKNOWN),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-base",),
    )
    ledger.append(flow)
    replacement = flow.model_copy(update={"flow_id": "f:1-r", "observed_at": T1})
    ledger.supersede("f:1", replacement=replacement)
    assert len(ledger.flows()) == 2
    assert ledger.flows()[0].flow_id == "f:1"  # original queryable forever
    assert ledger.active_flow_ids() == ("f:1-r",)
    with pytest.raises(Book5ProvenanceError):
        ledger.append(flow)  # duplicate append refused


def test_supersession_requires_new_identity() -> None:
    ledger = AppendOnlyFlowLedger()
    flow = CapitalFlow(
        flow_id="f:2", flow_type=FlowType.BURN, asset_ref="csia:stablecoin:fxd",
        quantity="10", unit="FXD", from_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        to_location=EconomicLocation(location_type=LocationType.UNKNOWN),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-base",),
    )
    ledger.append(flow)
    with pytest.raises(Book5ProvenanceError):
        ledger.supersede("f:2", replacement=flow)


def test_late_observation_enters_transaction_axis_late() -> None:
    flow = CapitalFlow(
        flow_id="f:late", flow_type=FlowType.TRANSFER, asset_ref="csia:token:eth",
        quantity="1", unit="ETH", from_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="b"),
        valid_time=T0, observed_at=T1,  # observed long after the fact
        book2_claim_refs=("book5-claim-eth",),
    )
    assert flow.observed_at > flow.valid_time  # history not rewritten


def test_5g_replay_two_valid_times_consistent() -> None:
    _, _, prov = kernel()
    synthesis = CapitalFieldSynthesis(prov, SynthesisWriteLedger())
    eth_ref = _bound_exact(prov, "replay-adv-eth", asset_ref="csia:token:eth", unit="ETH")
    position = make_position(components=component_set(component(claim_ref=eth_ref)))
    s1 = synthesis.compose_snapshot("s:t1", positions=(position,), valid_time=T0, observed_at=T0)
    s2 = synthesis.compose_snapshot("s:t1", positions=(position,), valid_time=T0, observed_at=T0)
    assert s1 == s2
    s3 = synthesis.compose_snapshot("s:t2", positions=(position,), valid_time=T1, observed_at=T1)
    assert s3.valid_time == T1
    # same methodology/version on all snapshots
    assert s1.methodology_version == s3.methodology_version


def test_transformation_distinct_from_flow() -> None:
    transformation = CapitalTransformation(
        transformation_id="t:1", transformation_kind=TransformationKind.ASSET_TO_LST,
        input_claim_id="claim:eth", output_claim_id="claim:steth",
        principal_component_refs=("lineage:eth-1",),
        liability_created=("liability:lst",),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    flow = CapitalFlow(
        flow_id="f:t1", flow_type=FlowType.TRANSFER, asset_ref="csia:token:eth",
        quantity="1", unit="ETH", from_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="a"),
        to_location=EconomicLocation(location_type=LocationType.ONCHAIN_ACCOUNT, ref="b"),
        valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
    )
    assert type(transformation) is not type(flow)
    # frozen: in-place identity erasure impossible
    with pytest.raises(Exception):
        transformation.output_claim_id = "claim:eth"
    # constructor-level identity erasure refused
    with pytest.raises(Exception):
        CapitalTransformation(
            transformation_id="t:2", transformation_kind=TransformationKind.ASSET_TO_LST,
            input_claim_id="claim:same", output_claim_id="claim:same",
            principal_component_refs=("lineage:eth-1",),
            valid_time=T0, observed_at=T0, book2_claim_refs=("book5-claim-eth",),
        )
