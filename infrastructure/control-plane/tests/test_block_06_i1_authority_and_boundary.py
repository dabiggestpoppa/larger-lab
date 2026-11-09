"""B6-I1 authority and boundary proofs."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.api.v1 import contract as C  # noqa: E402
from oce.api.v1.service import CanonicalAPI, Refused  # noqa: E402

DOCS = ROOT / "docs/oce-golden-system"
FORBIDDEN_KEYS = {"authority", "store", "path", "secret", "token", "_internal",
                  "_actors", "_tasks", "_approvals", "_evidence"}


def walk(value, keys: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            walk(item, keys)
    elif isinstance(value, list):
        for item in value:
            walk(item, keys)


def test_no_private_store_or_path_in_any_result() -> None:
    api = CanonicalAPI()
    calls = [
        {"version": "v1", "operation": "oce.api.v1.identity.get", "actor": "actor-1",
         "scopes": ["read"], "payload": {"actor_id": "actor-1"}},
        {"version": "v1", "operation": "oce.api.v1.evidence.list", "actor": "actor-1",
         "scopes": ["read"], "payload": {}},
        {"version": "v1", "operation": "oce.api.v1.artifacts.get", "actor": "actor-1",
         "scopes": ["read"], "payload": {"artifact_id": "artifact-1"}},
    ]
    for call in calls:
        response = api.handle(call)
        keys: set[str] = set()
        walk(response, keys)
        assert not keys & FORBIDDEN_KEYS, keys & FORBIDDEN_KEYS
        lowered = {key.lower() for key in keys}
        assert not [k for k in lowered if "store" in k or k.endswith("path")], lowered
        assert "/srv/" not in json.dumps(response) and "store.db" not in json.dumps(response)


def test_receipt_binds_contract_hash_and_hashes() -> None:
    response = CanonicalAPI().handle({
        "version": "v1", "operation": "oce.api.v1.tasks.get", "actor": "actor-1",
        "scopes": ["read"], "payload": {"task_id": "task-1"}})
    receipt = response["receipt"]
    assert receipt["contract_hash"] == C.CONTRACT_HASH
    assert len(receipt["contract_hash"]) == 64
    expected = hashlib.sha256(C.canonical_bytes(response["result"])).hexdigest()
    assert receipt["result_sha256"] == expected
    assert receipt["version"] == "v1" and receipt["actor"] == "actor-1"


def test_capabilities_are_minimal() -> None:
    api = CanonicalAPI()
    assert api.capabilities_for("actor-3", "decide") == []
    assert api.capabilities_for("actor-2", "decide") == ["decide"]
    result = api.handle({"version": "v1", "operation": "oce.api.v1.capabilities.get",
                         "actor": "actor-3", "scopes": ["read"],
                         "payload": {"actor_id": "actor-3", "scope": "decide"}})
    assert result["result"]["capability_set"] == []


def test_self_approval_refused() -> None:
    with pytest.raises(Refused) as exc:
        CanonicalAPI().handle({
            "version": "v1", "operation": "oce.api.v1.approvals.decide", "actor": "actor-1",
            "scopes": ["decide"], "payload": {"approval_id": "approval-1",
                                              "decision": "approve"}})
    assert exc.value.code == "REFUSED_SELF_APPROVAL"


def test_approval_requires_decide_scope() -> None:
    with pytest.raises(Refused) as exc:
        CanonicalAPI().handle({
            "version": "v1", "operation": "oce.api.v1.approvals.decide", "actor": "actor-3",
            "scopes": ["decide"], "payload": {"approval_id": "approval-1",
                                              "decision": "approve"}})
    assert exc.value.code == "REFUSED_SCOPE"


def test_boundary_only_allowed_paths_changed() -> None:
    scope = json.loads((DOCS / "OCE_BLOCK_06_I1_SCOPE_DERIVATION_v1.0.json")
                       .read_text(encoding="utf-8"))
    allowed = tuple(scope["allowed_paths"])
    base = scope["base_sha"]
    changed = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", f"{base}..HEAD"],
                             capture_output=True, text=True, check=True).stdout.split()
    assert changed
    outside = [p for p in changed if not p.startswith(allowed)]
    assert outside == []
    forbidden = [p for p in changed if p.startswith(tuple(scope["forbidden_paths"]))]
    assert forbidden == []


def test_no_secret_or_external_provider_dependency() -> None:
    for path in list((ROOT / "oce/api").rglob("*.py")) + list((ROOT / "oce/sdk").rglob("*.py")) \
            + list((ROOT / "oce/compat").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for token in ("requests", "httpx", "urllib.request", "boto3", "openai", "os.environ"):
            assert token not in source, f"{path.name}: {token}"
