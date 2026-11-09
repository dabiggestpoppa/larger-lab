"""Compatibility matrix check.

Three outcomes only: SUPPORTED, UNSUPPORTED, UNKNOWN. Unknown is never treated as supported and no
version is ever coerced to the newest one.
"""
from __future__ import annotations

SUPPORTED = ("v1",)
KNOWN_UNSUPPORTED = ("v0",)
WINDOW = {"min": "v1", "max": "v1", "policy": "additive_minor"}


def check(consumer_version: str) -> dict:
    if not isinstance(consumer_version, str) or not consumer_version:
        return {"verdict": "UNKNOWN", "requested": consumer_version, "supported": list(SUPPORTED),
                "reason": "version is empty or not a string; no latest is selected"}
    if consumer_version in SUPPORTED:
        return {"verdict": "SUPPORTED", "requested": consumer_version,
                "supported": list(SUPPORTED), "reason": "inside the supported window"}
    if consumer_version in KNOWN_UNSUPPORTED:
        return {"verdict": "UNSUPPORTED", "requested": consumer_version,
                "supported": list(SUPPORTED),
                "reason": "outside the supported window v1..v1"}
    return {"verdict": "UNKNOWN", "requested": consumer_version, "supported": list(SUPPORTED),
            "reason": "version cannot be resolved; no latest is selected"}
