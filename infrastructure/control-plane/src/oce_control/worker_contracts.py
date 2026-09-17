"""Book 3 Worker Fabric — versioned worker contracts and identity (B3-C1).

Freezes the machine-checkable contract catalogue for the worker fabric:
protocol version, worker identity fields, capability manifest, supported
task types, OS class, runtime class, trust zone, sandbox profile, and the
resource envelope. Unknown capabilities and unsupported versions fail
closed by every consumer of these contracts.

This module is the single source of truth for contract constants; the
JSON schemas under ``contracts/`` are their human-auditable mirrors.
"""
from __future__ import annotations
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema_validator import validate as _validate_schema

# -- versioning ----------------------------------------------------------------

PROTOCOL_VERSION = "1.0"
SUPPORTED_PROTOCOLS = ("1.0",)

SCHEMA_VERSION = "1.0.0"
VALIDATOR_VERSION = "b3-worker-fabric-1.0"

# -- enumerated catalogues -----------------------------------------------------

KNOWN_OS_CLASSES = ("windows", "linux", "darwin")
KNOWN_RUNTIME_CLASSES = (
    "python",            # plain interpreter subprocess (default local)
    "container-docker",  # docker-based isolation (adapter, not configured B3)
    "isolated-subprocess",
)
KNOWN_TRUST_ZONES = ("worker-local", "quant-lab", "operator", "isolated")
KNOWN_SANDBOX_PROFILES = ("default", "readonly", "network-none", "compute-heavy")

# Operator-admitted capability catalogue. Representative Book 3 jobs map
# onto these; anything absent here is unknown and fails closed.
KNOWN_CAPABILITIES = (
    "hash",                 # deterministic hash job
    "compute-python",       # bounded python compute
    "repo-inventory",       # read-only repository inventory
    "backtest-synthetic",   # synthetic backtest fixture
    "analysis-artifact",    # artifact-producing analysis job
    "file-read",            # read files within a bounded workspace
    "report-html",          # build an HTML report artifact
    "stdout-transform",     # pure-transform job
)

SUPPORTED_TASK_TYPES = (
    "b3.deterministic-hash",
    "b3.bounded-compute",
    "b3.repo-inventory",
    "b3.synthetic-backtest",
    "b3.analysis-artifact",
    "b3.cancel-during-exec",
)

# -- time helpers --------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def utcnow_iso() -> str:
    return utcnow().isoformat()

def utcnow_iso_after(seconds: int) -> str:
    from datetime import timedelta
    return (utcnow() + timedelta(seconds=seconds)).isoformat()

def dt_pass(now_iso: str, past_iso: str, window_s: int) -> bool:
    """True when `past_iso` is older than `window_s` seconds versus `now_iso`."""
    try:
        now = datetime.fromisoformat(now_iso)
        past = datetime.fromisoformat(past_iso)
        return (now - past).total_seconds() > window_s
    except (TypeError, ValueError):
        return False

# -- contract catalogue --------------------------------------------------------

@dataclass(frozen=True)
class Contract:
    name: str
    version: str
    schema: dict

    def validate(self, instance: Any) -> tuple[bool, list[str]]:
        return _validate_schema(instance, self.schema)

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version,
                "schema": self.schema}


def validate(contract: Contract, instance: Any) -> tuple[bool, list[str]]:
    return contract.validate(instance)


_RESOURCE_ENVELOPE_SCHEMA = {
    "type": "object",
    "required": ["cpu_limit", "memory_bytes", "disk_bytes", "timeout_s"],
    "additionalProperties": True,
    "properties": {
        "cpu_limit": {"type": "number", "minimum": 0},
        "memory_bytes": {"type": "integer", "minimum": 0},
        "disk_bytes": {"type": "integer", "minimum": 0},
        "timeout_s": {"type": "integer", "minimum": 1},
    },
}

_IDENTITY_SCHEMA = {
    "type": "object",
    "required": ["worker_id", "protocol_version", "host_os_class",
                 "runtime_class", "trust_zone", "worker_version"],
    "additionalProperties": True,
    "properties": {
        "worker_id": {"type": "string", "minLength": 1},
        "protocol_version": {"type": "string", "enum": list(SUPPORTED_PROTOCOLS)},
        "host_os_class": {"type": "string", "enum": list(KNOWN_OS_CLASSES)},
        "runtime_class": {"type": "string", "enum": list(KNOWN_RUNTIME_CLASSES)},
        "trust_zone": {"type": "string", "enum": list(KNOWN_TRUST_ZONES)},
        "sandbox_profile": {"type": "string", "enum": list(KNOWN_SANDBOX_PROFILES)},
    },
}

_CAPABILITY_MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["worker_id", "capabilities", "schema_version"],
    "additionalProperties": False,
    "properties": {
        "worker_id": {"type": "string", "minLength": 1},
        "capabilities": {"type": "array", "items": {"type": "string"}},
        "schema_version": {"type": "string", "const": SCHEMA_VERSION},
    },
}

_LEASE_SCHEMA = {
    "type": "object",
    "required": ["job_id", "lease_id", "fence", "worker_id", "expires_at"],
    "properties": {
        "job_id": {"type": "string"},
        "lease_id": {"type": "string", "minLength": 16},
        "fence": {"type": "integer", "minimum": 1},
        "worker_id": {"type": "string"},
        "expires_at": {"type": "string"},
    },
}

_RESULT_ENVELOPE_SCHEMA = {
    "type": "object",
    "required": ["job_id", "attempt", "success", "artifact_manifest_refs"],
    "properties": {
        "job_id": {"type": "string"},
        "attempt": {"type": "integer", "minimum": 1},
        "success": {"type": "boolean"},
        "artifact_manifest_refs": {"type": "array"},
    },
}

ARTIFACT_MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["job_id", "attempt", "producer_identity", "worker_id",
                 "artifacts"],
    "properties": {
        "job_id": {"type": "string"},
        "attempt": {"type": "integer", "minimum": 1},
        "producer_identity": {"type": "string"},
        "worker_id": {"type": "string"},
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "sha256", "size", "content_type"],
                "properties": {
                    "name": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "size": {"type": "integer", "minimum": 0},
                    "content_type": {"type": "string"},
                },
            },
        },
    },
}


def contract_catalogue() -> dict[str, Contract]:
    return {
        "worker-identity": Contract("worker-identity", SCHEMA_VERSION, _IDENTITY_SCHEMA),
        "capability-manifest": Contract("capability-manifest", SCHEMA_VERSION,
                                        _CAPABILITY_MANIFEST_SCHEMA),
        "resource-envelope": Contract("resource-envelope", SCHEMA_VERSION,
                                      _RESOURCE_ENVELOPE_SCHEMA),
        "lease": Contract("lease", SCHEMA_VERSION, _LEASE_SCHEMA),
        "result-envelope": Contract("result-envelope", SCHEMA_VERSION,
                                    _RESULT_ENVELOPE_SCHEMA),
        "artifact-manifest": Contract("artifact-manifest", SCHEMA_VERSION,
                                      ARTIFACT_MANIFEST_SCHEMA),
    }


_CONTRACTS = contract_catalogue()


def get_contract(name: str) -> Contract:
    if name not in _CONTRACTS:
        raise KeyError(f"unknown worker contract '{name}'")
    return _CONTRACTS[name]

# -- fail-closed validators ----------------------------------------------------

def ensure_supported_protocol(version: str, actor: str) -> None:
    if version not in SUPPORTED_PROTOCOLS:
        raise ValueError(
            f"{actor}: unsupported protocol version '{version}' "
            f"(supported: {list(SUPPORTED_PROTOCOLS)}) — fail closed")

def ensure_valid_os(os_class: str, actor: str) -> None:
    if os_class not in KNOWN_OS_CLASSES:
        raise ValueError(f"{actor}: unknown OS class '{os_class}' — fail closed")

def ensure_valid_runtime(runtime_class: str, actor: str) -> None:
    if runtime_class not in KNOWN_RUNTIME_CLASSES:
        raise ValueError(f"{actor}: unknown runtime class '{runtime_class}' — fail closed")

def ensure_valid_trust_zone(trust_zone: str, actor: str) -> None:
    if trust_zone not in KNOWN_TRUST_ZONES:
        raise ValueError(f"{actor}: unknown trust zone '{trust_zone}' — fail closed")

def ensure_valid_sandbox(profile: str, actor: str) -> None:
    if profile not in KNOWN_SANDBOX_PROFILES:
        raise ValueError(f"{actor}: unknown sandbox profile '{profile}' — fail closed")

def validate_identity_fields(identity: dict) -> tuple[bool, list[str]]:
    return get_contract("worker-identity").validate(identity)

def validate_capability_manifest(manifest: dict) -> tuple[bool, list[str]]:
    return get_contract("capability-manifest").validate(manifest)

# -- helpers -------------------------------------------------------------------

def new_worker_id() -> str:
    return "wkr-" + secrets.token_hex(12)


def schema_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "contracts"