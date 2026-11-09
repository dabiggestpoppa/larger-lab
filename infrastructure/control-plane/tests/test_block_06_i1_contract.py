"""B6-I1 contract proofs: identity, operation table, scopes, canonical artifacts, manifest."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.api.v1 import contract as C  # noqa: E402

DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I1_"


def load(name: str) -> dict:
    return json.loads((DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def test_scope_derivation_is_frozen_and_sourced() -> None:
    scope = load("SCOPE_DERIVATION_v1.0.json")
    assert scope["status"] == "FROZEN"
    assert scope["identity"]["stage_name"] == "C1 API and SDK"
    assert scope["identity"]["sections"] == ["C1.S1", "C1.S2"]
    assert scope["identity"]["surfaces"] == ["api", "sdk"]
    assert scope["identity"]["authorizes_source_extraction"] is False
    assert scope["identity"]["authorizes_packaging"] is False
    assert len(scope["authority_sources"]) >= 6


def test_operation_table_matches_firewall_symbols() -> None:
    firewall = json.loads((DOCS / "OCE_BLOCK_06_P0_PUBLIC_PRIVATE_API_FIREWALL_v1.0.json")
                          .read_text(encoding="utf-8"))
    reserved = {row["symbol"] for row in firewall["symbols"]
                if row.get("version_introduced") == "B6-I1"}
    assert reserved == {"oce.api.v1.capabilities.get", "oce.sdk.intents.submit",
                        "oce.compat.matrix.check"}
    assert reserved <= set(C.OPERATIONS)


def test_every_operation_declares_one_scope_and_typed_schema() -> None:
    assert len(C.OPERATIONS) == 10
    for symbol, spec in C.OPERATIONS.items():
        assert spec["scope_required"] in C.SCOPES
        assert isinstance(spec["typed_inputs"], list)
        assert isinstance(spec["typed_outputs"], list) and spec["typed_outputs"]
        assert spec["version"] == "v1" and spec["deterministic"] is True
        assert spec["classification"] == "public_experimental"


def test_no_wildcard_or_authority_scope() -> None:
    assert not set(C.FORBIDDEN_SCOPES) & set(C.SCOPES)
    declared = {spec["scope_required"] for spec in C.OPERATIONS.values()}
    assert declared == set(C.SCOPES)
    api = load("API_AND_SDK_CONTRACT_v1.0.json")
    assert api["deny_by_default"] is True
    assert "no client authority" in api["prohibitions"]


def test_refusal_taxonomy_is_complete() -> None:
    contract = load("IMPLEMENTATION_CONTRACT_v1.0.json")
    declared = {row["code"] for row in contract["refusals"]}
    assert declared == set(C.REFUSAL_CODES)
    classes = {row["class"] for row in contract["refusals"]}
    assert {"F09", "F10", "F07", "F05"} <= classes


def test_contract_artifacts_are_canonical_json() -> None:
    for path in sorted(DOCS.glob(f"{PREFIX}*.json")):
        raw = path.read_bytes()
        assert raw == canonical(json.loads(raw)), path.name
        assert raw.endswith(b"\n") and b"\r\n" not in raw


def test_registry_covers_every_section() -> None:
    registry = load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    assert registry["requirements_total"] == len(registry["requirements"]) == 12
    sections = {row["section"] for row in registry["requirements"]}
    assert sections == {"C1.S1", "C1.S2", "C1.S5"}
    assert registry["mutation_floor"] == {"source": 3, "stage": 6}


def test_manifest_lists_every_artifact() -> None:
    manifest = load("MANIFEST_v1.0.json")
    listed = {row["path"].split("/")[-1] for row in manifest["artifacts"]}
    present = {p.name for p in DOCS.glob(f"{PREFIX}*.json")} - {"OCE_BLOCK_06_I1_MANIFEST_v1.0.json"}
    assert listed == present
    for row in manifest["artifacts"]:
        data = (ROOT / row["path"]).read_bytes()
        assert row["sha256"] == hashlib.sha256(data).hexdigest()
        assert row["bytes"] == len(data)
