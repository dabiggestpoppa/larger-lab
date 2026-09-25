"""Book 4 deterministic pilot and accepted-primitive reuse tests."""

from __future__ import annotations

from crypto_systems_intelligence_atlas.book4 import OFFLINE_PILOTS
from crypto_systems_intelligence_atlas.dependency_paths import DependencyPathBook
from crypto_systems_intelligence_atlas.dependency_relations import OracleDeliveryHyperedgeFactory
from crypto_systems_intelligence_atlas.relationships import (
    Hyperedge,
    HyperedgeClass,
    RouteAttributes,
    RouteMechanism,
)


def test_at_least_eighteen_offline_pilots_exist() -> None:
    assert len(OFFLINE_PILOTS) >= 18
    assert len({item.pilot_id for item in OFFLINE_PILOTS}) == len(OFFLINE_PILOTS)


def test_every_pilot_is_explicitly_fixture_only() -> None:
    assert all(item.is_deterministic_offline_fixture for item in OFFLINE_PILOTS)
    assert all(item.live_current_claim is False for item in OFFLINE_PILOTS)


def test_oracle_delivery_reuses_book1_hyperedge() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import NOW, kernel

    claims, _, provenance = kernel()
    factory = OracleDeliveryHyperedgeFactory(claims)
    item = factory.build(
        hyperedge_id="fixture:oracle-delivery",
        oracle_ref="fixture:oracle-network",
        consumer_ref="fixture:liquidation-contract",
        chain_ref="fixture:chain",
        route_attributes=RouteAttributes(
            route_spec="fixture feed delivery",
            mechanism=RouteMechanism.OTHER,
            mechanism_defining_string="deterministic oracle feed delivery",
        ),
        claim_ref="book4-claim-current",
        observed_at=NOW,
        valid_from=NOW,
    )
    assert isinstance(item, Hyperedge)
    assert item.hyperedge_class is HyperedgeClass.HE_ORACLE_DELIVERY
    assert item.pairwise_projection()


def test_composite_route_uses_ordered_path_not_new_hypergraph() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import kernel, path

    _, _, provenance = kernel()
    item = DependencyPathBook(provenance).add(path("rollup-composite"))
    assert item.ordered_nodes == ("A", "B", "C")
    assert not hasattr(item, "hyperedge_class")
