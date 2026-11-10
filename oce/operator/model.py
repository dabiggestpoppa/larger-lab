"""Canonical encoding and refusal primitives for the operator surface."""
from __future__ import annotations

import hashlib
import json


class OperatorRefusal(Exception):
    """A governed refusal: the caller learns the code and nothing is silently coerced."""

    def __init__(self, code: str, detail=None) -> None:
        super().__init__(code if detail is None else f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical(obj) -> bytes:
    """Canonical JSON bytes: sorted keys, two-space indent, trailing LF, UTF-8."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def digest(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def object_digest(obj) -> str:
    return digest(canonical(obj))


def require(condition, code: str, detail=None) -> None:
    if not condition:
        raise OperatorRefusal(code, detail)
