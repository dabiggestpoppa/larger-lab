"""Frozen provider semantic contracts (repair SENSOR-B1-R01).

The Binance `isBuyerMaker` → `aggressor_side` direction is an economic
semantic contract, not a transformation implementation: the adapter
implementation belongs to Bloc 2/5.  Bloc 1 freezes and regression-tests the
declared direction so an inversion can never be re-introduced silently:

    isBuyerMaker = true  -> aggressor_side = SELL  (buyer is maker; seller is taker)
    isBuyerMaker = false -> aggressor_side = BUY   (buyer is taker)
"""

from __future__ import annotations

from crypto_sensor_fabric.registry.methodology_registry import load_methodology_registry
from crypto_sensor_fabric.registry.semantic_equivalence import load_semantic_equivalence
from crypto_sensor_fabric.testing import load_fixture_json

FROZEN_CASES = {
    True: "SELL",
    False: "BUY",
}


def test_r01_frozen_direction_true_maps_to_sell():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    cases = {case["isBuyerMaker"]: case["expected_aggressor_side"] for case in contract["cases"]}
    assert cases[True] == "SELL"


def test_r01_frozen_direction_false_maps_to_buy():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    cases = {case["isBuyerMaker"]: case["expected_aggressor_side"] for case in contract["cases"]}
    assert cases[False] == "BUY"


def test_r01_frozen_contract_covers_both_directions_exactly():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    cases = {case["isBuyerMaker"]: case["expected_aggressor_side"] for case in contract["cases"]}
    assert cases == FROZEN_CASES
    assert set(cases) == {True, False}


def test_r01_contract_references_registered_methodology():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    methodologies = load_methodology_registry()
    assert contract["methodology_id"] in methodologies.methodologies


def test_r01_equivalence_registry_mapping_consistent_with_contract():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    registry = load_semantic_equivalence()
    mappings = [
        m
        for m in registry.mappings
        if m.provider == contract["provider"] and m.source_metric == contract["source_metric"]
    ]
    assert len(mappings) == 1
    mapping = mappings[0]
    assert mapping.canonical_sensor.value == contract["canonical_sensor"]
    assert mapping.canonical_field == contract["canonical_field"]
    assert mapping.methodology_id == contract["methodology_id"]
    assert mapping.equivalence.value == "NORMALIZABLE_COMPARABLE"


def test_r01_contract_still_provisional():
    contract = load_fixture_json("binance_is_buyer_maker_semantics.json")
    assert contract["status"] == "PROVISIONAL"
