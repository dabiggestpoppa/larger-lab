"""Hashing utilities for the OCE control plane.

Uses hashlib for SHA-256 and MD5 (for fingerprints only, not security).
"""
from __future__ import annotations
import hashlib
import json
from typing import Any


def sha256_hex(data: bytes | str) -> str:
    """Compute SHA-256 hex digest of data."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def payload_hash(payload: Any) -> str:
    """Hash a JSON-serializable payload deterministically."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_hex(canonical)


def fingerprint_rows(rows: list[dict]) -> str:
    """Compute MD5 fingerprint over sorted canonical row-JSON.

    Matches B1's protected-inventory fingerprint pattern.
    """
    canonical = json.dumps(sorted(rows, key=json.dumps), sort_keys=True, separators=(",", ":"))
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()


def generate_id() -> str:
    """Generate a 32-char hex ID (128 bits of entropy)."""
    import secrets
    return secrets.token_hex(16)


def generate_idempotency_key() -> str:
    """Generate a 64-char hex idempotency key (256 bits)."""
    import secrets
    return secrets.token_hex(32)


def generate_correlation_id() -> str:
    """Generate a 32-char hex correlation ID."""
    return generate_id()
