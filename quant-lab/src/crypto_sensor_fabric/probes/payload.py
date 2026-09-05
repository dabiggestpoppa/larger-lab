"""Generic payload characterization primitives (03 §14, 04 §6).

Shared by provider probe modules.  Everything here is deterministic and
offline: given a provider-native payload it computes a structural schema
fingerprint (schema-drift detection), locates the dominant row lists, and
extracts candidate timestamps.  Providers stay responsible for interpreting
their own result shapes; these helpers only provide the shared mechanics.

Do NOT hash actual sensitive/auth data — fingerprinting is structural only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

#: Keys whose values are treated as timestamps (ms or ISO) when present.
TIMESTAMP_KEYS: tuple[str, ...] = (
    "time",
    "timestamp",
    "ts",
    "lastTime",
    "fundingTime",
    "funding_time",
    "create_time_ms",
    "create_time",
    "createdAt",
    "updatedAt",
)

#: Keys that typically carry duration/interval semantics rather than epochs.
NON_TIMESTAMP_KEYS: frozenset[str] = frozenset(
    {
        "interval",
        "fundingInterval",
        "duration",
        "period",
        "timeframe",
    }
)


def fingerprint_payload(payload: Any, sample_limit: int = 200) -> str:
    """Deterministic structural fingerprint of a payload (03 §14).

    Encodes sorted field names, nested structural paths and observed scalar
    types.  Lists are sampled (first `sample_limit` rows) and their row-shape
    union is recorded.  Identical content -> identical fingerprint; a schema
    change (e.g. `time` becoming a string) changes the fingerprint.
    """

    def _shape(value: Any, depth: int = 0) -> str:
        if isinstance(value, Mapping):
            if depth > 12:
                return "dict{...}"
            keys = sorted(str(k) for k in value)
            inner = ",".join(
                f"{k}:{_shape(value[k], depth + 1)}" for k in keys
            )
            return f"dict{{{inner}}}"
        if isinstance(value, list):
            if not value:
                return "list[]"
            row_shapes = {_shape(item, depth + 1) for item in value[:sample_limit]}
            return f"list[{'|'.join(sorted(row_shapes))}]"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        if value is None:
            return "null"
        return type(value).__name__

    return _shape(payload)


def find_row_lists(payload: Any) -> list[list[Any]]:
    """Locate candidate row lists, largest first.

    Walks mappings (and list-of-dicts) collecting every list whose elements
    are mappings or scalars, then returns them sorted by length descending.
    Providers pick the list matching their sensor's result key.
    """

    def _walk(value: Any, depth: int = 0) -> Iterable[list[Any]]:
        if depth > 12:
            return
        if isinstance(value, list):
            yield value
            for item in value[:50]:
                yield from _walk(item, depth + 1)
        elif isinstance(value, Mapping):
            for child in value.values():
                yield from _walk(child, depth + 1)

    lists = list(_walk(payload))
    lists.sort(key=len, reverse=True)
    return lists


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000.0 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)  # py3.11+ accepts trailing Z
            if dt.tzinfo is None:  # normalize naive ISO to UTC-aware (no tz-mixing)
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            pass
        try:
            numeric = float(value)
        except ValueError:
            return None
        seconds = numeric / 1000.0 if numeric > 10_000_000_000 else numeric
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    return None


def extract_timestamps(
    rows: Sequence[Mapping[str, Any]],
    ts_keys: Sequence[str] = TIMESTAMP_KEYS,
) -> list[datetime]:
    """Extract parseable timestamps from rows for the given candidate keys.

    First matching key per row wins (keys checked in order).  ms epochs and
    ISO-8601 strings are both accepted.
    """
    found: list[datetime] = []
    for row in rows[:2000]:
        for key in ts_keys:
            value = row.get(key)
            dt = _to_datetime(value)
            if dt is not None:
                found.append(dt)
                break
    return found


def first_last_timestamps(
    rows: Sequence[Mapping[str, Any]],
    ts_keys: Sequence[str] = TIMESTAMP_KEYS,
) -> tuple[datetime | None, datetime | None]:
    """(first, last) parseable timestamps across rows, or (None, None)."""
    stamps = extract_timestamps(rows, ts_keys)
    if not stamps:
        return None, None
    return min(stamps), max(stamps)


def summarize_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    ts_keys: Sequence[str] = TIMESTAMP_KEYS,
    sample_limit: int = 200,
) -> dict[str, Any]:
    """Summary dict for a row list: count, keys, first/last timestamps."""
    keys: set[str] = set()
    for row in rows[:sample_limit]:
        keys.update(str(k) for k in row)
    first, last = first_last_timestamps(rows, ts_keys)
    return {
        "row_count": len(rows),
        "keys": sorted(keys),
        "first_timestamp": first,
        "last_timestamp": last,
    }
