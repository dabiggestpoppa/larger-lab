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
