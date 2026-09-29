"""Book 5 core kernel tests: provenance adapter, sites/locations, attribution
laws, unit-domain vectors, and the many-to-many lineage graph (plan v0.3;
D5CAP-2 A-REVISED; stress rows 1–25, 26–35, 36–45 core behaviors)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.book5_core import (
    ARITHMETIC_STATES,
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
    LineageError,
    PrincipalContribution,
    PrincipalLineageNode,
    VALUATION_NOT_AUTHORIZED,
    reconcile_projection,
)
from crypto_systems_intelligence_atlas.book5_provenance import (
    Book5Provenance,
    Book5ProvenanceError,
    ClaimContextBinding,
)
from crypto_systems_intelligence_atlas.book5_support import (
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
from crypto_systems_intelligence_atlas.claims import ClaimState

UTC = UTC


def test_kernel_resolves_through_book2() -> None:
    claims, evidence, provenance = kernel()
    claim = provenance.resolve_claim("book5-claim-base")
    assert claim.claim_state is ClaimState.OBSERVED
    assert claim.proposition.qualifier == "ECONOMIC_FACT"


def test_unknown_claim_ref_fails_closed() -> None:
    _, _, provenance = kernel()
    with pytest.raises(Book5ProvenanceError):
        provenance.resolve_claim("book5-claim-never-seeded")


def test_unpromotable_claim_state_fails_closed() -> None:
    claims, evidence, provenance = kernel()
    add_claim(provenance, "stale", state=ClaimState.DECLARED)
    with pytest.raises(Book5ProvenanceError):
        provenance.resolve_claim("book5-claim-stale")


def test_detached_evidence_fails_closed() -> None:
    claims, evidence, provenance = kernel()
    claim_id = "book5-claim-detached"
    claims.add_initial(
        __import__(
            "crypto_systems_intelligence_atlas.book5_support",
            fromlist=["make_claim"],
        ).make_claim(claim_id, evidence_ref="book5-never-captured")
    )
    with pytest.raises(Book5ProvenanceError):
        provenance.resolve_claim(claim_id)


def test_empty_claim_refs_refused() -> None:
    _, _, provenance = kernel()
    with pytest.raises(Book5ProvenanceError):
        provenance.resolve_claim_refs(())


def test_string_claim_refs_refused() -> None:
    _, _, provenance = kernel()
    with pytest.raises(Book5ProvenanceError):
        provenance.resolve_claim_refs("book5-claim-base")


def test_site_requires_book1_anchors_and_valid_time() -> None:
    s = site()
    assert s.protocol_ref.startswith("csia:protocol:")
    assert s.deployment_ref is not None
    with pytest.raises(ValueError):
        EconomicSite(
            site_id="csia:site:bad",
            site_type=SiteType.VAULT,
            protocol_ref="csia:protocol:x",
            location=EconomicLocation(location_type=LocationType.VAULT, ref="l"),
            valid_from=NOW,
            valid_to=datetime(2026, 9, 1, tzinfo=UTC),
        )


def test_unknown_location_never_carries_precision() -> None:
    assert EconomicLocation(location_type=LocationType.UNKNOWN).ref is None
    with pytest.raises(ValueError):
        EconomicLocation(location_type=LocationType.UNKNOWN, ref="invented")


def test_typed_location_requires_ref() -> None:
    with pytest.raises(ValueError):
        EconomicLocation(location_type=LocationType.CEX)


def _exact_bound_kernel(tag: str, *, asset_ref: str = "csia:token:eth", unit: str = "ETH", realization_ref: str | None = None):
    """R2 helper: kernel + canonical exact-basis claim with a coherent
    context binding, so authority aggregation exercises the full seal."""

    claims, evidence, provenance = kernel()
    evidence_ref = make_evidence(evidence, f"{tag}-ev")
    claim_id = f"book5-claim-{tag}"
    claims.add_initial(
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
    return provenance, claim_id


def test_attribution_arithmetic_law() -> None:
    for state in (AttributionState.EXACT, AttributionState.PROPORTIONAL):
        assert state in ARITHMETIC_STATES
    # non-attributed components are constructible but never arithmetic
    for state in (
        AttributionState.COMMINGLED,
        AttributionState.UNKNOWN,
        AttributionState.UNRESOLVED,
    ):
        c = component(quantity="2", attribution=state, claim_ref="book5-claim-pool")
        assert c.share_fraction is None
    # same-unit aggregation refuses non-attributed components (the EXACT
    # participant carries a proper R2 basis + binding so the COMMINGLED
    # arithmetic refusal is what fires, not a basis rejection)
    provenance, exact_ref = _exact_bound_kernel("law-exact")
    s = component_set(
        component(quantity="1", attribution=AttributionState.EXACT, claim_ref=exact_ref),
        component(quantity="2", attribution=AttributionState.COMMINGLED, claim_ref="book5-claim-pool"),
    )
    with pytest.raises(AttributionStateError):
        s.aggregate_same_unit("ETH", provenance=provenance)


def test_derived_allocation_requires_methodology_fraction() -> None:
    with pytest.raises(ValueError):
        PrincipalComponent(
            asset_ref="csia:token:eth",
            quantity="1",
            unit="ETH",
            attribution_state=AttributionState.DERIVED_ALLOCATION,
            book2_claim_refs=("book5-claim-eth",),
            valid_time=NOW,
        )


def test_share_fraction_illegal_for_exact() -> None:
    with pytest.raises(ValueError):
        component(share_fraction="0.5")


def test_lp_multi_root_vector_is_heterogeneous() -> None:
    prov_eth, eth_ref = _exact_bound_kernel("lp-eth-exact")
    prov_usdc, usdc_ref = _exact_bound_kernel(
        "lp-usdc-exact", asset_ref="csia:token:usdc", unit="USDC"
    )
    lp = component_set(
        component(quantity="3", unit="ETH", claim_ref=eth_ref),
        component(
            asset_ref="csia:token:usdc",
            quantity="5000",
            unit="USDC",
            claim_ref=usdc_ref,
        ),
    )
    assert lp.is_heterogeneous()
    assert lp.units() == ("ETH", "USDC")
    # same-unit aggregation still works per unit under the R2 authority seal
    assert lp.aggregate_same_unit("ETH", provenance=prov_eth) == "3"
    assert lp.aggregate_same_unit("USDC", provenance=prov_usdc) == "5000"


def test_no_cross_unit_aggregation_exists() -> None:
    prov_eth, eth_ref = _exact_bound_kernel("crossunit-eth")
    _, usdc_ref = _exact_bound_kernel(
        "crossunit-usdc", asset_ref="csia:token:usdc", unit="USDC"
    )
    lp = component_set(
        component(quantity="3", unit="ETH", claim_ref=eth_ref),
        component(
            asset_ref="csia:token:usdc",
            quantity="5000",
            unit="USDC",
            claim_ref=usdc_ref,
        ),
    )
    assert not hasattr(lp, "aggregate_total")
    assert not hasattr(lp, "value")
    with pytest.raises(Book5ProvenanceError):
        lp.aggregate_same_unit("USD", provenance=prov_eth)  # no such unit in the set


def test_lineage_many_roots_for_one_record() -> None:
    g = graph(
        contribution("l:eth", "rec:lp"),
        contribution(
            "l:usdc", "rec:lp", quantity="5000", unit="USDC", claim_ref="book5-claim-usdc"
        ),
        nodes=(
            lineage_node("l:eth"),
            lineage_node("l:usdc", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-usdc"),
        ),
    )
    roots = g.roots_for("rec:lp")
    assert len(roots) == 2  # N:1 — no single-root forcing


def test_lineage_fan_out_one_root_many_records() -> None:
    prov, ref = _exact_bound_kernel("fanout-exact")
    g = graph(
        contribution("l:eth", "rec:a", claim_ref=ref),
        contribution("l:eth", "rec:b", claim_ref=ref),
        nodes=(lineage_node("l:eth", claim_ref=ref),),
    )
    assert len(g.roots_for("rec:a")) == 1
    assert len(g.roots_for("rec:b")) == 1
    # fan-out did not multiply the principal: each record still sees one root
    # with the same unit, and collapse of each is independent
    assert g.collapse_same_unit("rec:a", unit="ETH", provenance=prov) == "3"


def test_collapse_refuses_non_attributed_edge() -> None:
    g = graph(
        contribution(
            "l:pool",
            "rec:borrow",
            attribution=AttributionState.COMMINGLED,
            quantity="800",
            unit="USDC",
            claim_ref="book5-claim-pool",
        ),
        nodes=(
            lineage_node(
                "l:pool", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-pool"
            ),
        ),
    )
    with pytest.raises(AttributionStateError):
        g.collapse_same_unit("rec:borrow", unit="USDC", provenance=kernel()[2])


def test_collapse_refuses_missing_quantity() -> None:
    prov, ref = _exact_bound_kernel("missingqty-exact")
    g = graph(
        contribution("l:eth", "rec:x", quantity=None, unit=None, claim_ref=ref),
        nodes=(lineage_node("l:eth", claim_ref=ref),),
    )
    with pytest.raises(LineageError):
        g.collapse_same_unit("rec:x", unit="ETH", provenance=prov)


def test_cycle_detection_and_collapse_refusal() -> None:
    g = CapitalPrincipalLineageGraph()
    g.add_node(lineage_node("l:a"))
    g.add_node(lineage_node("l:b", asset_ref="csia:token:usdc", unit="USDC", claim_ref="book5-claim-usdc"))
    g.add_edge(contribution("l:a", "l:b", quantity="3", unit="ETH"))
    g.add_edge(
        contribution(
            "l:b", "l:a", quantity="800", unit="USDC", claim_ref="book5-claim-usdc"
        )
    )
    assert set(g.detect_cycles()) == {"l:a", "l:b"}
    with pytest.raises(LineageError):
        g.collapse_same_unit("l:b", unit="USDC", provenance=kernel()[2])


def test_rehypothecation_chain_preserves_source_set() -> None:
    prov, ref = _exact_bound_kernel("rehyp-exact")
    g = graph(
        contribution("l:eth", "rec:pledge1", claim_ref=ref),
        contribution("l:eth", "rec:pledge2", quantity="3", unit="ETH", claim_ref=ref),
        nodes=(lineage_node("l:eth", claim_ref=ref),),
    )
    # same principal feeds two encumbrance legs (rehypothecation): the source
    # set for each record is preserved and the lineage root is one — the
    # principal was NOT multiplied
    assert len(g.roots_for("rec:pledge1")) == 1
    assert len(g.roots_for("rec:pledge2")) == 1
    assert g.collapse_same_unit("rec:pledge1", unit="ETH", provenance=prov) == "3"
    assert g.collapse_same_unit("rec:pledge2", unit="ETH", provenance=prov) == "3"


def test_liability_projection_reconciles_or_fails() -> None:
    liability = debt_liability(quantity="800")
    assert (
        reconcile_projection(
            canonical_quantity="800",
            projected_quantity="800",
            same_observation_parameters=True,
        )
        == "800"
    )
    with pytest.raises(Exception):
        reconcile_projection(
            canonical_quantity="800",
            projected_quantity="700",
            same_observation_parameters=True,
        )
    with pytest.raises(Exception):
        reconcile_projection(
            canonical_quantity="800",
            projected_quantity="800",
            same_observation_parameters=False,
        )


def test_valuation_state_is_not_authorized_not_unknown() -> None:
    assert VALUATION_NOT_AUTHORIZED == "NOT_AUTHORIZED"
    assert VALUATION_NOT_AUTHORIZED != "UNKNOWN"
