"""B6-I4 C3.S1 identity registry, raw-secret refusal, isolation and revocation."""
from __future__ import annotations

import pytest

from oce.operator.model import OperatorRefusal
from oce.services.identity import identity_registry, resolve_identity


def record(**overrides):
    row = {"id": "id:agent", "kind": "service", "app": "app-a",
           "credential_reference": {"id": "cr-1", "kind": "token", "rotated_at": 0,
                                    "revoked": False}}
    row.update(overrides)
    return row


def registry(**overrides):
    return identity_registry([record(**overrides)])


def test_identity_registry_canonical():
    doc = registry()
    assert doc["total"] == 1 and doc["digest"]
    assert doc["identities"]["id:agent"]["app"] == "app-a"
    assert doc["identities"]["id:agent"]["credential_reference"]["id"] == "cr-1"


def test_raw_secret_refused():
    with pytest.raises(OperatorRefusal) as exc:
        identity_registry([record(credential_reference={
            "id": "cr-1", "kind": "token", "rotated_at": 0, "revoked": False,
            "secret": "sk-live"})])
    assert exc.value.code == "REFUSED_RAW_SECRET"


def test_duplicate_identity_refused():
    with pytest.raises(OperatorRefusal) as exc:
        identity_registry([record(), record()])
    assert exc.value.code == "REFUSED_DUPLICATE_IDENTITY"


def test_cross_app_isolation_refused():
    with pytest.raises(OperatorRefusal) as exc:
        resolve_identity(registry(), "id:agent", "app-b", 5)
    assert exc.value.code == "REFUSED_CROSS_APP"


def test_revoked_identity_refused():
    with pytest.raises(OperatorRefusal) as exc:
        resolve_identity(registry(credential_reference={
            "id": "cr-1", "kind": "token", "rotated_at": 0, "revoked": True}),
            "id:agent", "app-a", 5)
    assert exc.value.code == "REFUSED_REVOKED"


def test_resolution_deterministic():
    reg = identity_registry([record(), record(id="id:other", app="app-a")])
    first = resolve_identity(reg, "id:agent", "app-a", 5)
    second = resolve_identity(reg, "id:agent", "app-a", 5)
    assert first["digest"] == second["digest"]
    assert first["credential_reference_id"] == "cr-1"


def test_nested_map_secret_refused():
    credential = {"id": "cr-1", "kind": "token", "rotated_at": 0, "revoked": False,
                  "meta": {"auth": {"token": "sk-live"}}}
    with pytest.raises(OperatorRefusal) as exc:
        identity_registry([record(credential_reference=credential)])
    assert exc.value.code == "REFUSED_RAW_SECRET"


def test_nested_sequence_secret_refused():
    credential = {"id": "cr-1", "kind": "token", "rotated_at": 0, "revoked": False,
                  "headers": [{"name": "ok"}, {"password": "sk-live"}]}
    with pytest.raises(OperatorRefusal) as exc:
        identity_registry([record(credential_reference=credential)])
    assert exc.value.code == "REFUSED_RAW_SECRET"
