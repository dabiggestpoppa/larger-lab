"""Shared domain validation primitives for QCAE core records.

Small, dependency-free helpers so every record enforces identifiers, strings,
and tuples identically (Book V 15.2: malformed core objects fail before
provider execution).
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Sequence

from qcae.core.errors import QcaeValidationError

#: Stable internal identifier shape (canon 1.3.16: identity is not display name).
#: Examples: CAP-REPLAY-001, atom-changepoint-detection, repo:owner/name@sha.
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")

#: Validated UTC/RFC3339 timestamps: ``YYYY-MM-DDTHH:MM:SS(.ffffff)?Z``. The
#: shape is fixed so record digests stay stable across producers (P3-R4C3/C5).
_RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$"
)


def require_identifier(value: Any, what: str) -> None:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise QcaeValidationError(
            f"{what} must match {_ID_RE.pattern!r} (short stable identifier), got {value!r}"
        )


def require_rfc3339_utc(value: Any, what: str) -> None:
    """A validated UTC timestamp in RFC3339 form, not free prose (canon 1.3.14)."""
    if not isinstance(value, str) or not _RFC3339_UTC_RE.match(value):
        raise QcaeValidationError(
            f"{what} must be an RFC3339 UTC timestamp 'YYYY-MM-DDTHH:MM:SS(.ffffff)?Z', "
            f"got {value!r}"
        )
    try:
        datetime.strptime(
            value[:-1] + (".000000" if "." not in value else ""),
            "%Y-%m-%dT%H:%M:%S.%f",
        )
    except ValueError as exc:
        raise QcaeValidationError(
            f"{what} is not a real UTC instant: {value!r} ({exc})"
        ) from exc


def require_non_empty_str(value: Any, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QcaeValidationError(f"{what} must be a non-empty string")


def require_str_list(value: Any, what: str) -> None:
    if not isinstance(value, (list, tuple)):
        raise QcaeValidationError(f"{what} must be a list of strings")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise QcaeValidationError(f"{what} entries must be non-empty strings, got {item!r}")


def require_hex_hash(value: Any, what: str, min_length: int = 8) -> None:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{min_length},}}", value):
        raise QcaeValidationError(
            f"{what} must be a lowercase hex digest of at least {min_length} chars, got {value!r}"
        )


def require_enum(value: Any, enum_cls: type, what: str) -> None:
    if not isinstance(value, enum_cls):
        raise QcaeValidationError(
            f"{what} must be a {enum_cls.__name__} member, got {value!r}"
        )


def require_enum_tuple(value: Any, enum_cls: type, what: str) -> None:
    if not isinstance(value, (list, tuple)):
        raise QcaeValidationError(f"{what} must be a list of {enum_cls.__name__} members")
    for item in value:
        require_enum(item, enum_cls, f"{what} entry")


def require_no_duplicates(values: Sequence[Any], what: str) -> None:
    seen: set = set()
    for item in values:
        key = item.value if isinstance(item, Enum) else item
        if key in seen:
            raise QcaeValidationError(f"{what} contains duplicate entry {key!r}")
        seen.add(key)
