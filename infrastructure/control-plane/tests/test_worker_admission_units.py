"""B2-R4: worker admission unit tests (run anywhere, no container).

Covers the pure admission logic: token hashing (only the hash is ever
persisted), capability matching at claim time, and capability-manifest
validation against the frozen contract schema. The PostgreSQL-backed
admission/claim/fencing behavior is proven in test_pg_worker_integration.py
(container-backed, mandatory in CI).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

from oce_control.pg_worker import (
    capabilities_satisfied,
    hash_admission_token,
    validate_capability_manifest,
)


def test_admission_token_hash_is_deterministic():
    assert hash_admission_token("tok-alpha") == hash_admission_token("tok-alpha")
    assert hash_admission_token("tok-alpha") != hash_admission_token("tok-beta")
    assert len(hash_admission_token("anything")) == 64  # sha256 hexdigest


def test_capabilities_satisfied():
    assert capabilities_satisfied(["gpu"], ["gpu", "cpu"]) is True
    assert capabilities_satisfied(["gpu", "cpu"], ["gpu", "cpu"]) is True
    assert capabilities_satisfied(["gpu"], ["cpu"]) is False
    # no required capabilities -> any worker qualifies
    assert capabilities_satisfied([], ["cpu"]) is True
    assert capabilities_satisfied(None, ["cpu"]) is True
    assert capabilities_satisfied(["gpu"], None) is False


def test_valid_capability_manifest_passes():
    manifest = {
        "worker_id": "worker-local01",
        "capabilities": ["gpu", "batch"],
        "trust_zone": "worker-local",
        "connected_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "1.0.0",
    }
    ok, errors = validate_capability_manifest(manifest)
    assert ok is True, errors


def test_invalid_capability_manifest_rejected():
    # missing required fields
    ok, errors = validate_capability_manifest({"worker_id": "x"})
    assert ok is False
    assert any("required" in e for e in errors)

    # wrong schema version
    manifest = {
        "worker_id": "worker-local01",
        "capabilities": ["gpu"],
        "connected_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "9.9.9",
    }
    ok, errors = validate_capability_manifest(manifest)
    assert ok is False
    assert any("schema_version" in e for e in errors)

    # empty capabilities (minItems 1)
    manifest = {
        "worker_id": "worker-local01",
        "capabilities": [],
        "connected_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "1.0.0",
    }
    ok, errors = validate_capability_manifest(manifest)
    assert ok is False

    # unknown properties rejected (additionalProperties false)
    manifest = {
        "worker_id": "worker-local01",
        "capabilities": ["gpu"],
        "connected_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "1.0.0",
        "sneaky": True,
    }
    ok, errors = validate_capability_manifest(manifest)
    assert ok is False
