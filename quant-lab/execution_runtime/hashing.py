"""QL-EXEC-R1 — deterministic canonical config hashing.

Requirements: stable ordering, explicit schema/version, no secrets, no
dynamic state, no per-serialization timestamps.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any

from .types import SecretReference

_HASH_VERSION = "QH1"


def canonicalize(obj: Any) -> Any:
    """Deterministic JSON-safe representation.

    - dataclasses -> dicts with keys sorted alphabetically (field-order
      independent)
    - enums -> .value
    - SecretReference -> kind only (the reference identifier and any
      credential value are NEVER part of hash material)
    - tuples -> lists
    - dicts -> recursively sorted keys
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, SecretReference):
        return {"kind": obj.kind.value}
    if isinstance(obj, Path):
        return str(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            out[f.name] = canonicalize(getattr(obj, f.name))
        return dict(sorted(out.items()))
    if isinstance(obj, dict):
        return {str(k): canonicalize(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [canonicalize(x) for x in obj]
    if hasattr(obj, "to_dict"):
        return canonicalize(obj.to_dict())
    return str(obj)


def canonical_json(obj: Any) -> str:
    return json.dumps(
        canonicalize(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def config_hash(obj: Any) -> str:
    """Versioned, deterministic hash of a static contract.

    Includes the object type name so distinct schemas never collide.
    """
    type_name = type(obj).__name__
    payload = canonical_json(obj)
    digest = hashlib.sha256(f"{type_name}|{payload}".encode("utf-8")).hexdigest()
    return f"{_HASH_VERSION}:{digest}"
