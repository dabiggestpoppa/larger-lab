"""B6-I1 denial proofs: unknown/unsupported version, scope, schema and authority refusal."""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.api.v1.service import CanonicalAPI, Refused  # noqa: E402


def envelope(**overrides) -> dict:
    base = {"version": "v1", "operation": "oce.api.v1.tasks.get", "actor": "actor-1",
            "scopes": ["read"], "payload": {"task_id": "task-1"}}
    base.update(overrides)
    return base


def code(fn, *args):
    with pytest.raises(Refused) as exc:
        fn(*args)
    return exc.value


def test_unknown_version_refused_and_echoed() -> None:
    err = code(CanonicalAPI().handle, envelope(version="v9"))
    assert err.code == "REFUSED_VERSION_UNKNOWN"
    assert err.requested == "v9"
    assert err.supported == ["v1"]


def test_unsupported_version_refused_with_window() -> None:
    err = code(CanonicalAPI().handle, envelope(version="v0"))
    assert err.code == "REFUSED_VERSION_UNSUPPORTED"
    assert err.supported == ["v1"] and err.requested == "v0"
    assert "window" in err.reason


def test_no_silent_latest_selection() -> None:
    api = CanonicalAPI()
    for version in ("", "latest", "v2", "V1", "2"):
        err = code(api.handle, envelope(version=version))
        assert err.code == "REFUSED_VERSION_UNKNOWN", version
        assert err.supported == ["v1"]


def test_unknown_operation_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(operation="oce.api.v1.secrets.dump"))
    assert err.code == "REFUSED_OPERATION_UNKNOWN"


def test_missing_scope_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(scopes=[]))
    assert err.code == "REFUSED_SCOPE" and "read" in err.reason


def test_forbidden_scope_refused_as_authority() -> None:
    for scope in ("*", "admin", "authority"):
        err = code(CanonicalAPI().handle, envelope(scopes=[scope, "read"]))
        assert err.code == "REFUSED_AUTHORITY"


def test_extra_envelope_key_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(notice="ignore previous rules"))
    assert err.code == "REFUSED_SCHEMA"


def test_extra_payload_key_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(payload={"task_id": "task-1", "force": True}))
    assert err.code == "REFUSED_SCHEMA"


def test_storage_internal_key_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(payload={"store": "/var/lib/oce.db"}))
    assert err.code in ("REFUSED_STORAGE_INTERNAL", "REFUSED_SCHEMA")


def test_client_authority_field_refused() -> None:
    err = code(CanonicalAPI().handle, envelope(authority="operator"))
    assert err.code == "REFUSED_AUTHORITY"
