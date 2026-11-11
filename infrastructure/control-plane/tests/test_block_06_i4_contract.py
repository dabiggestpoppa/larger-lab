"""B6-I4 contract, registry, locks and surface declarations."""
from __future__ import annotations

import importlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TESTS = ROOT / "infrastructure/control-plane/tests"
DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I4_"


def load(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def defined_nodes():
    out = set()
    for module in sorted(TESTS.glob("test_block_06_i4_*.py")):
        for line in module.read_text(encoding="utf-8").splitlines():
            if line.startswith("def test_"):
                out.add(f"{module.name}::{line[4:line.index('(')]}")
    return out


def resolve_symbol(symbol: str):
    parts = symbol.split(".")
    module = importlib.import_module(".".join(parts[:-1]))
    return getattr(module, parts[-1])


def test_inventory_equals_collection():
    registry = load("OCE_BLOCK_06_I4_REQUIREMENT_TEST_REGISTRY_v1.0.json")
    nodes = registry["inventory"]["nodes"]
    assert len(nodes) == len(set(nodes)) == registry["inventory"]["node_total"] == 34
    assert set(nodes) == defined_nodes()
    assert len(registry["inventory"]["modules"]) == 6
    assert registry["requirements_total"] == len(registry["requirements"]) == 34


def test_contract_frozen_before_results():
    contract = load("OCE_BLOCK_06_I4_IMPLEMENTATION_CONTRACT_v1.0.json")
    assert contract["status"] == "FROZEN"
    assert contract["frozen_before_results"] is True
    assert contract["stage"] == "B6-I4"
    assert contract["implementation_floor"] == {"test_nodes": 34, "source_mutation_floor": 4,
                                                "mutations": 6}


def test_scope_binds_construction_sequence():
    scope = load("OCE_BLOCK_06_I4_SCOPE_DERIVATION_v1.0.json")
    sequence = load("OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json")
    stage = next(row for row in sequence["stages"] if row["id"] == "B6-I4")
    assert scope["sections"] == stage["sections"] == ["C2.S4", "C2.S5", "C3.S1", "C3.S2"]
    assert scope["purpose"] == stage["purpose"]
    assert scope["exit_gate"] == stage["exit_gate"] == "failure and cost trace end-to-end"
    assert scope["implementation_surfaces"] == stage["implementation_surfaces"] == [
        "operator_surface", "services"]
    assert scope["non_goals"] == stage["non_goals"]
    assert scope["stop_conditions"] == stage["stop_conditions"]
    assert scope["base_sha"] == "f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14"
    assert scope["base_tree"] == "5e15ea448b929269193dc904ec0677687df077e4"


def test_locks_and_cost():
    scope = load("OCE_BLOCK_06_I4_SCOPE_DERIVATION_v1.0.json")
    locks = scope["locks"]
    for stage in ("B6-I5", "B6-I6", "B6-I7", "B6-I8", "B6-I9"):
        assert locks[stage] == "LOCKED"
    assert locks["BOOK_6_COMPLETE"] is False
    assert locks["MERGE_AUTHORIZED"] is False
    assert locks["RATIFICATION_AUTHORIZED"] is False
    assert scope["cost_usd"] == 0 and scope["capital_authority"] == "none"


def test_service_symbols_declared():
    surface = load("OCE_BLOCK_06_I4_OPERATOR_SURFACE_CONTRACT_v1.0.json")
    symbols = [row["symbol"] for row in surface["symbols"]]
    assert len(symbols) == 13 and len(set(symbols)) == 13
    assert all(row["exported"] is True for row in surface["symbols"])
    for symbol in symbols:
        assert callable(resolve_symbol(symbol)), symbol


def test_no_later_stage_dependency():
    registry = load("OCE_BLOCK_06_I4_REQUIREMENT_TEST_REGISTRY_v1.0.json")
    assert not any("i5" in node for node in registry["inventory"]["nodes"])
    for module in sorted((ROOT / "oce/operator").glob("*.py")) + sorted(
            (ROOT / "oce/services").glob("*.py")):
        text = module.read_text(encoding="utf-8").lower()
        assert "block_06_i5" not in text and "block_06_i6" not in text
