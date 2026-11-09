"""Frozen B6-I1 v1 operation contract.

The table is the single source of truth for the API surface, the SDK and the compatibility check.
It is intentionally static: no discovery, no plugin registration, no environment-driven symbols,
so an unknown operation can never appear by accident.
"""
from __future__ import annotations

import hashlib
import json

API_VERSION = "v1"
CONTRACT_ID = "OCE-B6-I1-API-001"
SCOPES = ("read", "propose", "decide")
FORBIDDEN_SCOPES = ("*", "admin", "authority", "write", "root")
ENVELOPE_REQUIRED = ("version", "operation", "actor", "scopes", "payload")
ENVELOPE_FORBIDDEN = ("authority", "store", "path", "token", "secret")

# symbol -> (section, scope, typed inputs, typed outputs)
_TABLE = (
    ("oce.api.v1.identity.get", "C1.S1", "read", ("actor_id",), ("actor_id", "capabilities")),
    ("oce.api.v1.capabilities.get", "C1.S1", "read", ("actor_id", "scope"),
     ("capability_set",)),
    ("oce.sdk.intents.submit", "C1.S2", "propose", ("intent", "actor"), ("receipt",)),
    ("oce.api.v1.intents.get", "C1.S2", "read", ("intent_id",), ("intent",)),
    ("oce.api.v1.tasks.get", "C1.S2", "read", ("task_id",), ("task",)),
    ("oce.api.v1.events.append", "C1.S2", "propose", ("task_id", "event"), ("receipt",)),
    ("oce.api.v1.artifacts.get", "C1.S2", "read", ("artifact_id",), ("artifact",)),
    ("oce.api.v1.evidence.list", "C1.S2", "read", (), ("evidence",)),
    ("oce.api.v1.approvals.decide", "C1.S2", "decide", ("approval_id", "decision"),
     ("approval",)),
    ("oce.compat.matrix.check", "C1.S5", "read", ("consumer_version",), ("verdict",)),
)

OPERATIONS = {
    symbol: {
        "symbol": symbol,
        "section": section,
        "version": API_VERSION,
        "scope_required": scope,
        "typed_inputs": list(inputs),
        "typed_outputs": list(outputs),
        "classification": "public_experimental",
        "compatibility_promise": "additive_minor",
        "deterministic": True,
        "authority_class": scope,
    }
    for symbol, section, scope, inputs, outputs in _TABLE
}

REFUSAL_CODES = (
    "REFUSED_VERSION_UNKNOWN",
    "REFUSED_VERSION_UNSUPPORTED",
    "REFUSED_OPERATION_UNKNOWN",
    "REFUSED_SCOPE",
    "REFUSED_SCHEMA",
    "REFUSED_AUTHORITY",
    "REFUSED_STORAGE_INTERNAL",
    "REFUSED_SELF_APPROVAL",
    "REFUSED_DUPLICATE_RECEIPT",
)


def canonical_bytes(obj) -> bytes:
    """Canonical JSON used for every hash, receipt and comparison."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


CONTRACT_HASH = hashlib.sha256(
    canonical_bytes({"id": CONTRACT_ID, "version": API_VERSION,
                     "operations": [OPERATIONS[s] for s in sorted(OPERATIONS)]})
).hexdigest()
