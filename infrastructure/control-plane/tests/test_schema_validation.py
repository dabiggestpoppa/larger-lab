"""B2-C1: Schema validation tests — all contract schemas validate correctly."""
import json
from pathlib import Path

import pytest
from oce_control.schema_validator import validate, load_schema, validate_file

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts"


def test_schema_registry_validates():
    schema = load_schema(CONTRACTS / "schema-registry.json")
    instance = {
        "registry_id": "OCE-CP-SCHEMA-REGISTRY-v2",
        "schemas": [
            {
                "schema_id": "job-envelope",
                "name": "Job Envelope",
                "version": "2.0.0",
                "owner": "control-plane",
                "compatibility_class": "backward",
                "status": "active"
            }
        ]
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Schema validation errors: {errors}"


def test_schema_registry_rejects_unknown():
    schema = load_schema(CONTRACTS / "schema-registry.json")
    instance = {"registry_id": "WRONG", "schemas": []}
    ok, errors = validate(instance, schema)
    assert not ok


def test_agent_identity_validates():
    schema = load_schema(CONTRACTS / "agent-identity.schema.json")
    instance = {
        "agent_id": "operator-local01",
        "agent_type": "operator",
        "trust_zone": "operator",
        "created_at": "2026-08-30T00:00:00Z",
        "expires_at": "2026-08-31T00:00:00Z",
        "schema_version": "1.0.0"
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Errors: {errors}"


def test_agent_identity_rejects_wrong_type():
    schema = load_schema(CONTRACTS / "agent-identity.schema.json")
    instance = {
        "agent_id": "operator-local01",
        "agent_type": "invalid_type",
        "trust_zone": "operator",
        "created_at": "2026-08-30T00:00:00Z",
        "expires_at": "2026-08-31T00:00:00Z",
        "schema_version": "1.0.0"
    }
    ok, _ = validate(instance, schema)
    assert not ok


def test_job_envelope_validates():
    schema = load_schema(CONTRACTS / "job-envelope.schema.json")
    instance = {
        "job_id": "a" * 32,
        "job_type": "test_job",
        "schema_version": "2.0.0",
        "submitting_actor": "po-test01",
        "authority_context": {
            "grant_id": "b" * 32,
            "actor_id": "po-test01",
            "action": "submit_job",
            "target": "default",
            "environment": "local",
            "expires_at": "2026-08-31T00:00:00Z"
        },
        "resource_scope": "default",
        "environment": "local",
        "priority": "normal",
        "idempotency_key": "c" * 64,
        "payload_hash": "d" * 64,
        "created_at": "2026-08-30T00:00:00Z",
        "scheduled_at": "2026-08-30T00:00:00Z",
        "attempt_number": 0,
        "retry_policy": {"max_attempts": 3, "backoff_strategy": "exponential"},
        "timeout": 300,
        "lease": {},
        "correlation_id": "e" * 32,
        "status": "pending"
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Errors: {errors}"


def test_capability_grant_validates():
    schema = load_schema(CONTRACTS / "capability-grant.schema.json")
    instance = {
        "grant_id": "a" * 32,
        "actor_id": "po-test01",
        "action": "submit_job",
        "target": "default",
        "environment": "local",
        "risk_class": "local-write",
        "limits": {"max_concurrent": 5},
        "issued_at": "2026-08-30T00:00:00Z",
        "expires_at": "2026-08-31T00:00:00Z",
        "status": "active"
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Errors: {errors}"


def test_event_envelope_validates():
    schema = load_schema(CONTRACTS / "event-envelope.schema.json")
    instance = {
        "event_id": "a" * 32,
        "event_type": "job_submitted",
        "schema_version": "2.0.0",
        "actor_id": "po-test01",
        "authority_grant_id": "b" * 32,
        "causality": {
            "root_id": "c" * 32,
            "parent_id": "",
            "sequence": 1
        },
        "target": "default",
        "payload_hash": "d" * 64,
        "environment": "local",
        "timestamp": "2026-08-30T00:00:00Z"
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Errors: {errors}"


def test_denial_envelope_validates():
    schema = load_schema(CONTRACTS / "denial-envelope.schema.json")
    instance = {
        "denial_id": "a" * 32,
        "reason_code": "missing_authority",
        "actor_id": "unknown-actor",
        "requested_action": "submit_job",
        "requested_target": "default",
        "policy_version": "2.0.0",
        "denied_at": "2026-08-30T00:00:00Z"
    }
    ok, errors = validate(instance, schema)
    assert ok, f"Errors: {errors}"


def test_denial_envelope_rejects_invalid_reason():
    schema = load_schema(CONTRACTS / "denial-envelope.schema.json")
    instance = {
        "denial_id": "a" * 32,
        "reason_code": "made_up_reason",
        "actor_id": "unknown-actor",
        "requested_action": "submit_job",
        "requested_target": "default",
        "policy_version": "2.0.0",
        "denied_at": "2026-08-30T00:00:00Z"
    }
    ok, _ = validate(instance, schema)
    assert not ok


# ── B4-CXR7U9R12: the pattern-input bound is real, not decorative ────────
def test_pattern_is_never_run_on_over_bound_input(monkeypatch):
    """An instance longer than the bound is refused BEFORE the regex runs.

    The rule that flags this sink (a schema-supplied pattern matched against
    caller-supplied text) cannot see the length guard from outside, so the
    guard is proven here instead: the module's own `re.match` is replaced by
    a recorder that fails the test if it is ever reached.
    """
    import oce_control.schema_validator as sv

    reached = []

    def recorder(pattern, string, *a, **kw):
        reached.append((pattern, len(string)))
        raise AssertionError("the pattern must not run on over-bound input")

    monkeypatch.setattr(sv.re, "match", recorder)
    over = "x" * (sv._MAX_PATTERN_INPUT + 1)
    errors = sv._validate_string(over, {"pattern": "^(a|aa)+$"}, "$.field")
    assert reached == [], reached
    assert any("exceeds pattern-input bound" in e for e in errors), errors


def test_pattern_still_runs_and_decides_within_the_bound(monkeypatch):
    """Positive control: at or under the bound the pattern is evaluated and
    still decides the outcome, so the guard bounds work without weakening it."""
    import oce_control.schema_validator as sv

    seen = []
    real_match = sv.re.match

    def recorder(pattern, string, *a, **kw):
        seen.append((pattern, string))
        return real_match(pattern, string, *a, **kw)

    monkeypatch.setattr(sv.re, "match", recorder)
    at_bound = "a" * sv._MAX_PATTERN_INPUT
    assert sv._validate_string(at_bound, {"pattern": "^a+$"}, "$.field") == []
    assert seen, "the pattern must be evaluated within the bound"
    bad = sv._validate_string("b", {"pattern": "^a+$"}, "$.field")
    assert any("does not match pattern" in e for e in bad), bad
