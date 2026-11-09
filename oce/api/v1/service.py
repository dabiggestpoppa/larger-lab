"""Canonical in-process v1 API dispatcher.

There is exactly one place where a request becomes a result: this module. The SDK, the examples
and the tests all route through it, so no consumer can grow a second authority. Results are plain
canonical data; the private store is never returned, named or reachable through a payload key.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from . import contract as C

SUPPORTED = ("v1",)
KNOWN_UNSUPPORTED = ("v0",)
_FORBIDDEN_PAYLOAD_KEYS = ("authority", "store", "path", "secret", "token", "_internal")


class Refused(Exception):
    """A typed, deterministic refusal. Unknown is never treated as supported."""

    def __init__(self, code: str, reason: str, supported: list[str] | None = None,
                 requested: str | None = None) -> None:
        if code not in C.REFUSAL_CODES:
            raise ValueError(f"undeclared refusal code {code}")
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.supported = list(supported or [])
        self.requested = requested

    def to_dict(self) -> dict[str, Any]:
        return {"ok": False, "code": self.code, "reason": self.reason,
                "supported": self.supported, "requested": self.requested}


def _digest(obj) -> str:
    return hashlib.sha256(C.canonical_bytes(obj)).hexdigest()


def _scan(value) -> None:
    """Refuse any shape that would leak storage internals or authority."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_PAYLOAD_KEYS:
                raise Refused("REFUSED_STORAGE_INTERNAL",
                              f"forbidden field {key!r} is not part of the public contract")
            _scan(item)
    elif isinstance(value, list):
        for item in value:
            _scan(item)


class CanonicalAPI:
    """One deterministic dispatcher over a private, in-memory store."""

    version = C.API_VERSION
    contract_hash = C.CONTRACT_HASH

    def __init__(self, actors: dict | None = None) -> None:
        self._actors = actors or {
            "actor-1": {"capabilities": ["read", "propose", "decide"]},
            "actor-2": {"capabilities": ["read", "propose", "decide"]},
            "actor-3": {"capabilities": ["read"]},
        }
        self._intents: dict[str, dict] = {}
        self._tasks = {"task-1": {"id": "task-1", "state": "pending", "owner": "actor-1"}}
        self._events: list[dict] = []
        self._artifacts = {"artifact-1": {"id": "artifact-1", "kind": "report", "bytes": 12}}
        self._evidence = [{"id": "evidence-1", "state": "OPEN", "owner": "B5I8-DF05"}]
        self._approvals = {"approval-1": {"id": "approval-1", "requester": "actor-1",
                                          "effect": "read", "state": "PENDING"}}
        self._receipts: set[str] = set()

    # ---- public surface -----------------------------------------------------------------
    def handle(self, envelope: dict) -> dict:
        if not isinstance(envelope, dict):
            raise Refused("REFUSED_SCHEMA", "request must be an object")
        keys = set(envelope)
        if keys & set(C.ENVELOPE_FORBIDDEN):
            raise Refused("REFUSED_AUTHORITY", "authority is never supplied by a caller")
        if keys != set(C.ENVELOPE_REQUIRED):
            missing = sorted(set(C.ENVELOPE_REQUIRED) - keys)
            extra = sorted(keys - set(C.ENVELOPE_REQUIRED))
            raise Refused("REFUSED_SCHEMA", f"envelope mismatch missing={missing} extra={extra}")

        version = envelope["version"]
        if version != C.API_VERSION:
            if version in KNOWN_UNSUPPORTED:
                raise Refused("REFUSED_VERSION_UNSUPPORTED",
                              "requested version is outside the supported window",
                              supported=list(SUPPORTED), requested=version)
            raise Refused("REFUSED_VERSION_UNKNOWN",
                          "requested version cannot be resolved; no latest is selected",
                          supported=list(SUPPORTED), requested=version)

        operation = envelope["operation"]
        spec = C.OPERATIONS.get(operation) if isinstance(operation, str) else None
        if spec is None:
            raise Refused("REFUSED_OPERATION_UNKNOWN", "operation is not in the frozen table")

        actor = envelope["actor"]
        if not isinstance(actor, str) or not actor or len(actor) > 128:
            raise Refused("REFUSED_SCHEMA", "actor must be a non-empty opaque string")
        _scan({"actor": actor})

        scopes = envelope["scopes"]
        if not isinstance(scopes, list) or not all(isinstance(s, str) for s in scopes):
            raise Refused("REFUSED_SCHEMA", "scopes must be a list of strings")
        if set(scopes) & set(C.FORBIDDEN_SCOPES):
            raise Refused("REFUSED_AUTHORITY", "wildcard or authority scopes are forbidden")
        required = spec["scope_required"]
        if required not in scopes:
            raise Refused("REFUSED_SCOPE", f"scope {required!r} is required")
        if required not in self._actors.get(actor, {}).get("capabilities", []):
            raise Refused("REFUSED_SCOPE", f"actor does not hold {required!r}")

        payload = envelope["payload"]
        if not isinstance(payload, dict):
            raise Refused("REFUSED_SCHEMA", "payload must be an object")
        _scan(payload)
        if set(payload) != set(spec["typed_inputs"]):
            missing = sorted(set(spec["typed_inputs"]) - set(payload))
            extra = sorted(set(payload) - set(spec["typed_inputs"]))
            raise Refused("REFUSED_SCHEMA", f"payload mismatch missing={missing} extra={extra}")

        result = self._dispatch(operation, actor, payload)
        _scan(result)
        receipt = self._receipt(operation, actor, payload, result)
        return {"ok": True, "version": C.API_VERSION, "operation": operation,
                "result": result, "receipt": receipt}

    def capabilities_for(self, actor: str, scope: str) -> list[str]:
        held = self._actors.get(actor, {}).get("capabilities", [])
        return [scope] if scope in held else []

    # ---- dispatch -----------------------------------------------------------------------
    def _dispatch(self, operation: str, actor: str, payload: dict) -> dict:
        if operation == "oce.api.v1.identity.get":
            if payload["actor_id"] not in self._actors:
                raise Refused("REFUSED_SCHEMA", "unknown actor")
            return {"actor_id": payload["actor_id"],
                    "capabilities": list(self._actors[payload["actor_id"]]["capabilities"])}
        if operation == "oce.api.v1.capabilities.get":
            return {"capability_set": self.capabilities_for(payload["actor_id"],
                                                            payload["scope"])}
        if operation == "oce.sdk.intents.submit":
            intent = payload["intent"]
            if not isinstance(intent, str) or len(intent) > 512:
                raise Refused("REFUSED_SCHEMA", "intent must be a bounded string")
            intent_id = "intent-" + _digest({"actor": payload["actor"], "intent": intent})[:12]
            self._intents.setdefault(intent_id, {"id": intent_id, "state": "submitted",
                                                 "body": intent})
            return {"receipt": {"intent_id": intent_id, "state": "submitted"}}
        if operation == "oce.api.v1.intents.get":
            row = self._intents.get(payload["intent_id"])
            if row is None:
                raise Refused("REFUSED_SCHEMA", "unknown intent")
            return {"intent": dict(row)}
        if operation == "oce.api.v1.tasks.get":
            row = self._tasks.get(payload["task_id"])
            if row is None:
                raise Refused("REFUSED_SCHEMA", "unknown task")
            return {"task": dict(row)}
        if operation == "oce.api.v1.events.append":
            if payload["task_id"] not in self._tasks:
                raise Refused("REFUSED_SCHEMA", "unknown task")
            event = {"task_id": payload["task_id"], "event": payload["event"],
                     "index": len(self._events)}
            self._events.append(event)
            return {"receipt": {"event_index": event["index"], "task_id": event["task_id"]}}
        if operation == "oce.api.v1.artifacts.get":
            row = self._artifacts.get(payload["artifact_id"])
            if row is None:
                raise Refused("REFUSED_SCHEMA", "unknown artifact")
            return {"artifact": dict(row)}
        if operation == "oce.api.v1.evidence.list":
            return {"evidence": [dict(r) for r in self._evidence]}
        if operation == "oce.api.v1.approvals.decide":
            row = self._approvals.get(payload["approval_id"])
            if row is None:
                raise Refused("REFUSED_SCHEMA", "unknown approval")
            if payload["decision"] not in ("approve", "deny"):
                raise Refused("REFUSED_SCHEMA", "decision must be approve or deny")
            if actor == row["requester"]:
                raise Refused("REFUSED_SELF_APPROVAL", "requester cannot approve their own request")
            row = dict(row)
            row["state"] = "APPROVED" if payload["decision"] == "approve" else "DENIED"
            self._approvals[payload["approval_id"]] = row
            return {"approval": dict(row)}
        if operation == "oce.compat.matrix.check":
            from ...compat import matrix  # local import keeps the API free of compat coupling
            return {"verdict": matrix.check(payload["consumer_version"])}
        raise Refused("REFUSED_OPERATION_UNKNOWN", "operation is not implemented")

    def _receipt(self, operation: str, actor: str, payload: dict, result: dict) -> dict:
        request_sha = _digest({"operation": operation, "actor": actor, "payload": payload})
        result_sha = _digest(result)
        receipt_id = _digest({"contract": C.CONTRACT_HASH, "request": request_sha,
                              "result": result_sha})
        if receipt_id in self._receipts:
            raise Refused("REFUSED_DUPLICATE_RECEIPT", "receipt already exists")
        self._receipts.add(receipt_id)
        return {"contract_hash": C.CONTRACT_HASH, "request_sha256": request_sha,
                "result_sha256": result_sha, "version": C.API_VERSION,
                "operation": operation, "actor": actor, "receipt_id": receipt_id}
