"""Deterministic harness evidence (B6-I2, section C1.S4).

Evidence is a canonical JSON document plus a digest over exactly that document. Capturing the same
record twice yields identical bytes, so a fingerprint can be compared across runs without a clock,
a hostname or a process id.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "oce.harness.evidence.v1"


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def fingerprint(record: object) -> str:
    return hashlib.sha256(canonical(record)).hexdigest()


def capture(kind: str, record: object) -> dict:
    body = {"kind": kind, "record": record}
    return {"schema": SCHEMA, "kind": kind, "record": record,
            "digest": fingerprint(body), "network": False}


def verify(document: object) -> bool:
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        return False
    body = {"kind": document.get("kind"), "record": document.get("record")}
    return document.get("digest") == fingerprint(body)


__all__ = ["SCHEMA", "canonical", "capture", "fingerprint", "verify"]
