"""B6-I2 contract proofs: frozen identity, floors, source binding, locks, path authority."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I2_"
BASE_SHA = "4496d548078660efd7ad4f93e7fff461d34ea538"
BASE_TREE = "c6638bde3e9c8f71482f4d96fde42d0484d9a624"
TESTS = ROOT / "infrastructure/control-plane/tests"


def load(name: str) -> dict:
    return json.loads((DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def test_inventory_equals_collection() -> None:
    registry = load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    declared = registry["inventory"]["nodes"]
    modules = sorted(TESTS.glob("test_block_06_i2_*.py"))
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *map(str, modules), "--collect-only", "-q",
         "-p", "no:cacheprovider", "-o", "addopts="],
        cwd=str(ROOT), capture_output=True, text=True)
    collected = [line.strip().split("/")[-1] for line in proc.stdout.splitlines()
                 if line.startswith("infrastructure/") and "::" in line]
    assert len(modules) == 6
    assert len(collected) == 30 and len(set(collected)) == 30
    assert sorted(collected) == sorted(declared)


def test_contract_frozen_before_results() -> None:
    contract = load("IMPLEMENTATION_CONTRACT_v1.0.json")
    assert contract["status"] == "FROZEN"
    assert contract["frozen_before_results"] is True
    floors = contract["implementation_floor"]
    assert floors == {"mutations": 6, "source_mutation_floor": 3, "test_nodes": 30}
    assert contract["base_sha"] == BASE_SHA and contract["base_tree"] == BASE_TREE
    assert contract["adjacent_floors"]["common_regression_nodes"] == 208
    assert contract["paired_comparison"] == {
        "base_only_expected": 0,
        "base_sha": BASE_SHA,
        "common_floor": 208,
        "head_only_expected": 30,
    }


def test_scope_binds_construction_sequence() -> None:
    scope = load("SCOPE_DERIVATION_v1.0.json")
    assert scope["purpose"] == "C1 templates and local harness"
    assert scope["sections"] == ["C1.S3", "C1.S4"]
    assert scope["implementation_surfaces"] == ["templates", "harness"]
    assert scope["outputs"] == ["template", "harness"]
    assert scope["non_goals"] == ["cloud dependency"]
    assert scope["exit_gate"] == "fresh generated app starts locally"
    assert scope["stop_conditions"] == ["stop if cloud is required"]
    assert scope["requirements"] == ["B6-P0-SEC-03", "B6-P0-SEC-04"]
    assert scope["base_sha"] == BASE_SHA
    sequence = DOCS / "OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json"
    assert sequence.exists()
    sources = scope["authority_sources"]
    assert len(sources) >= 6
    for source in sources:
        assert (ROOT / source.split("#")[0]).exists(), source


def test_locks_and_cost() -> None:
    scope = load("SCOPE_DERIVATION_v1.0.json")
    contract = load("IMPLEMENTATION_CONTRACT_v1.0.json")
    locks = scope["locks"]
    for stage in ("B6-I3", "B6-I4", "B6-I5", "B6-I6", "B6-I7", "B6-I8", "B6-I9"):
        assert locks[stage] == "LOCKED"
    assert locks["BOOK_6_COMPLETE"] is False
    assert locks["G16"] == "OPEN" and locks["G16_OWNER"] == "B5I8-DF05"
    assert locks["MERGE_AUTHORIZED"] is False and locks["RATIFICATION_AUTHORIZED"] is False
    assert locks["evaluation_system"] == "RESERVED_NOT_AUTHORIZED"
    assert locks["cloud_hosting"] == "NOT_AUTHORIZED"
    assert scope["cost_usd"] == 0 and scope["capital_authority"] == "none"
    assert contract["locks"]["MERGE_AUTHORIZED"] is False
    assert contract["locks"]["B6-I3_through_I9"] == "LOCKED"
    assert contract["cost_usd"] == 0 and contract["capital_authority"] == "none"


def test_allowed_and_forbidden_paths_declared() -> None:
    registration = load("STAGE_SCOPE_REGISTRATION_v1.0.json")
    prefixes = registration["this_stage"]["allowed_prefixes"]
    assert f"{PREFIX}" not in prefixes
    for required in ("docs/oce-golden-system/OCE_BLOCK_06_I2_",
                     "infrastructure/control-plane/scripts/block_06_i2_",
                     "infrastructure/control-plane/tests/test_block_06_i2_",
                     "oce/templates/", "oce/harness/"):
        assert required in prefixes
    for forbidden in ("packages/", "dist/", "build/", "oce/api/", "oce/sdk/"):
        assert not any(p.startswith(forbidden) for p in prefixes)
    assert registration["status"] == "FROZEN"
    assert registration["frozen_before_results"] is True
    assert registration["this_stage"]["base"] == BASE_SHA
    assert "stage/branch_spoof" in registration["refusals"]
    assert "stage/contract_absent" in registration["refusals"]
