from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence_identity(source: str, source_id: str, title: str) -> str:
    basis = f"{source.strip().lower()}|{source_id.strip()}|{title.strip()}".encode("utf-8")
    return "ev_" + hashlib.sha256(basis).hexdigest()[:24]
