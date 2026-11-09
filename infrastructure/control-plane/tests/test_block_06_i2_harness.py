"""B6-I2 harness proofs: endpoint sets, profile/service refusal, network refusal, evidence."""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.harness import evidence, local  # noqa: E402
from oce.templates import refusals  # noqa: E402


def code(fn, *args, **kwargs):
    with pytest.raises(refusals.Refused) as exc:
        fn(*args, **kwargs)
    return exc.value


def test_up_returns_endpoint_set() -> None:
    result = local.up("local")
    assert result["transport"] == "in-process"
    assert result["network"] is False
    assert result["services"] == ["app", "db", "evidence", "queue"]
    assert [row["service"] for row in result["endpoints"]] == result["services"]
    for row in result["endpoints"]:
        assert row["address"] == f"local://{row['service']}"
        assert row["transport"] == "in-process"
    assert local.up("minimal")["services"] == ["app"]
    assert local.profiles() == {"local": ["app", "db", "evidence", "queue"],
                                "minimal": ["app"]}


def test_missing_service_refused() -> None:
    assert code(local.up, "local", services=("app", "ghost")).code == "REFUSED_MISSING_SERVICE"
    assert code(local.up, "minimal", services=("db",)).code == "REFUSED_MISSING_SERVICE"
    assert code(local.up, "local", services=()).code == "REFUSED_MISSING_SERVICE"


def test_unknown_profile_refused() -> None:
    for profile in ("cloud", "production", ""):
        err = code(local.up, profile)
        assert err.code == "REFUSED_UNKNOWN_PROFILE"
        assert err.detail == profile


def test_undeclared_network_call_refused() -> None:
    for module in ("socket", "urllib.request", "http.client", "requests"):
        assert code(local.up, "local", imports=(module,)).code == "REFUSED_NETWORK"
    assert code(local.up, "local", imports=("os",)).code == "REFUSED_INVALID_MANIFEST"
    assert local.up("local", imports=("json", "hashlib"))["network"] is False


def test_evidence_capture_deterministic() -> None:
    record = {"profile": "local", "services": ["app"], "status": "PASS"}
    first = evidence.capture("harness.profile", record)
    second = evidence.capture("harness.profile", record)
    assert evidence.canonical(first) == evidence.canonical(second)
    assert evidence.verify(first) is True
    tampered = dict(first, digest="0" * 64)
    assert evidence.verify(tampered) is False
    assert b"\r\n" not in evidence.canonical(first)


def test_environment_fingerprint_stable() -> None:
    base = {"profile": "local", "services": local.profiles()["local"], "network": False}
    assert evidence.fingerprint(base) == evidence.fingerprint(dict(base))
    changed = dict(base, services=["app"])
    assert evidence.fingerprint(base) != evidence.fingerprint(changed)
    assert len(evidence.fingerprint(base)) == 64
