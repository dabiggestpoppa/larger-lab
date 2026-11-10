"""B6-I3 contract, registry, locks and surface declarations."""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TESTS = ROOT / "infrastructure/control-plane/tests"
DOCS = ROOT / "docs/oce-golden-system"


def load(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def defined_nodes():
    out = set()
    for module in sorted(TESTS.glob("test_block_06_i3_*.py")):
        for line in module.read_text(encoding="utf-8").splitlines():
            if line.startswith("def test_"):
                out.add(f"{module.name}::{line[4:line.index('(')]}")
    return out


def test_inventory_equals_collection():
    registry = load("OCE_BLOCK_06_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json")
    nodes = registry["inventory"]["nodes"]
    assert len(nodes) == len(set(nodes)) == registry["inventory"]["node_total"] == 28
    assert set(nodes) == defined_nodes()
    assert len(registry["inventory"]["modules"]) == 4


def test_contract_frozen_before_results():
    contract = load("OCE_BLOCK_06_I3_IMPLEMENTATION_CONTRACT_v1.0.json")
    assert contract["status"] == "FROZEN"
    assert contract["frozen_before_results"] is True
    assert contract["stage"] == "B6-I3"


def test_scope_binds_construction_sequence():
    scope = load("OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json")
    sequence = load("OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json")
    stage = next(row for row in sequence["stages"] if row["id"] == "B6-I3")
    assert scope["sections"] == stage["sections"] == ["C2.S1", "C2.S2", "C2.S3"]
    assert scope["purpose"] == stage["purpose"]
    assert scope["exit_gate"] == stage["exit_gate"] == "operator truth and authority tests pass"
    assert scope["implementation_surfaces"] == stage["implementation_surfaces"] == ["operator_surface"]
    assert scope["non_goals"] == stage["non_goals"]
    assert scope["stop_conditions"] == stage["stop_conditions"]
    assert scope["base_sha"] == "018b164f249bbf075334d5d03ad37e80dcbbede0"
    assert scope["base_tree"] == "65c3713ad70e527a6a5657347c53f8663a2ccb20"


def test_locks_and_cost():
    scope = load("OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json")
    locks = scope["locks"]
    for stage in ("B6-I4", "B6-I5", "B6-I6", "B6-I7", "B6-I8", "B6-I9"):
        assert locks[stage] == "LOCKED"
    assert locks["BOOK_6_COMPLETE"] is False
    assert locks["MERGE_AUTHORIZED"] is False
    assert locks["RATIFICATION_AUTHORIZED"] is False
    assert scope["cost_usd"] == 0 and scope["capital_authority"] == "none"


def test_operator_symbols_declared():
    import oce.operator as operator

    surface = load("OCE_BLOCK_06_I3_OPERATOR_SURFACE_CONTRACT_v1.0.json")
    symbols = {row["symbol"] for row in surface["symbols"]}
    assert symbols == {
        "oce.operator.capability_view",
        "oce.operator.approval_inbox",
        "oce.operator.decide",
        "oce.operator.reconcile_chain",
    }
    assert all(row["exported"] is True for row in surface["symbols"])
    assert all(callable(getattr(operator, symbol.rsplit(".", 1)[-1])) for symbol in symbols)


def test_no_later_stage_dependency():
    registry = load("OCE_BLOCK_06_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json")
    assert not any("i4" in node for node in registry["inventory"]["nodes"])
    for module in sorted((ROOT / "oce/operator").glob("*.py")):
        text = module.read_text(encoding="utf-8").lower()
        assert "block_06_i4" not in text and "oce.operator.i4" not in text
