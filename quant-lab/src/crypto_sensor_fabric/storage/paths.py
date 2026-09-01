"""SENSOR-B4-I02 — content-addressed object keys and safe reversible path encoding.

Two identities must never be conflated (I02 §16):

- CONTENT ID          = ``blob_sha256`` (the 64-char source SHA-256);
- STORAGE OBJECT KEY  = portable, backend-neutral, slash-separated relative
                        key under the storage root (``blobs/sha256/...`` or
                        ``projections/...``);
- RESOLVED LOCAL PATH = machine-specific root + object key (``resolve_under_root``).

Absolute workstation paths are NEVER canonical evidence identity; the data
root must remain movable.

Rules enforced here:

- T0A blob location depends ONLY on source content digest + wrapper encoding.
  Provider/sensor/instrument values NEVER enter the content-addressed key.
- Path segment escaping is deterministic, reversible, UTF-8 preserving, with
  NO Unicode normalization and NO OS-dependent behavior (narrow literal-safe
  alphabet ``A-Z a-z 0-9 _ -``; everything else percent-encoded as uppercase
  ``%HH`` of the UTF-8 bytes).
- Native identity is ESCAPED, never normalized: ``BTC/USDT``, ``BTC-USDT``,
  ``btc-usdt`` and ``BTC USDT`` remain distinct exact strings.
- Empty structural coordinates fail closed — empty never maps to
  ``unknown``/``none``/``_`` (that would invent identity).
- ``resolve_under_root`` is LEXICAL containment only: absolute keys, ``..``,
  empty segments, backslashes and NUL are rejected.  Symlink-escape hardening
  belongs to the later security/hardening checkpoint — no overclaim here.

This module performs NO filesystem mutation, NO directory creation, NO
compression and NO network.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .checksums import validate_sha256_hex
from .enums import StorageEncoding

# Backend-neutral object-key prefix for content-addressed T0A blobs.
BLOB_KEY_PREFIX = "blobs/sha256"

# Narrow literal-safe segment alphabet (uppercase %HH encodes everything else).
_SAFE_SEGMENT_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
)

_UPPERCASE_HEX = frozenset("0123456789ABCDEF")

# Default projection-schema-key prefix length is NOT identity; the full
# projection SHA-256 remains authoritative (I02 §27 — no schema-hash doctrine
# is invented here; I05 owns the projection schema registry).
DEFAULT_HASH_PREFIX_LENGTH = 8


def escape_path_segment(value: str) -> str:
    """Deterministic reversible UTF-8-preserving percent-encoding (uppercase %HH).

    Literal-safe alphabet is ``A-Z a-z 0-9 _ -``.  Everything else — ``.``,
    ``/``, ``\\``, ``%``, ``=``, space, Unicode bytes, control bytes — is
    encoded as uppercase ``%HH`` of its UTF-8 bytes.  No Unicode normalization:
    NFC/NFD and case variants remain distinct exact strings.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"escape_path_segment requires str, got {type(value).__name__}"
        )
    out: list[str] = []
    for byte in value.encode("utf-8"):
        char = chr(byte)
        if char in _SAFE_SEGMENT_CHARS:
            out.append(char)
        else:
            out.append(f"%{byte:02X}")
    return "".join(out)


def unescape_path_segment(encoded: str) -> str:
    """Reversible inverse of :func:`escape_path_segment`.

    Only the CANONICAL uppercase ``%HH`` form is accepted: lowercase/mixed
    percent escapes, raw non-safe characters, malformed ``%`` sequences and
    non-UTF-8 byte sequences are rejected (accepting variants would create
    multiple canonical encodings for one native identity).
    """
    if not isinstance(encoded, str):
        raise TypeError(
            f"unescape_path_segment requires str, got {type(encoded).__name__}"
        )
    out = bytearray()
    i = 0
    n = len(encoded)
    while i < n:
        char = encoded[i]
        if char == "%":
            if i + 3 > n:
                raise ValueError(
                    f"malformed percent encoding at offset {i} (truncated %HH)"
                )
            hi, lo = encoded[i + 1], encoded[i + 2]
            if hi not in _UPPERCASE_HEX or lo not in _UPPERCASE_HEX:
                raise ValueError(
                    f"malformed percent encoding at offset {i} "
                    f"({encoded[i:i + 3]!r}; only canonical uppercase %HH accepted)"
                )
            out.append(int(encoded[i + 1 : i + 3], 16))
            i += 3
        elif char in _SAFE_SEGMENT_CHARS:
            out.append(ord(char))
            i += 1
        else:
            raise ValueError(
                f"unescape_path_segment: {char!r} at offset {i} is not canonical "
                "(raw non-safe characters must be percent-encoded)"
            )
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"decoded segment bytes are not valid UTF-8: {exc}") from None


def blob_object_key(blob_sha256: str, storage_encoding: StorageEncoding) -> str:
    """Derive the backend-neutral T0A storage object key from content digest.

    Layout (I02 §15, partition doc §2.3):

    ``blobs/sha256/<h0h1>/<h2h3>/<full_sha256>.blob``
    ``blobs/sha256/<h0h1>/<h2h3>/<full_sha256>.blob.zst``

    No provider/sensor/date components.  The wrapper suffix is metadata only —
    the source content ID (``blob_sha256``) is identical for both encodings.
    Malformed SHA input fails closed (single shared validation rule).
    """
    if not isinstance(storage_encoding, StorageEncoding):
        raise TypeError(
            f"storage_encoding must be a StorageEncoding, got {type(storage_encoding).__name__}"
        )
    validate_sha256_hex(blob_sha256)
    suffix = ".blob" if storage_encoding is StorageEncoding.NONE else ".blob.zst"
    return (
        f"{BLOB_KEY_PREFIX}/{blob_sha256[0:2]}/{blob_sha256[2:4]}/{blob_sha256}{suffix}"
    )


def projection_object_key(
    *,
    provider: str,
    venue: str,
    sensor_family: str,
    native_instrument: str,
    native_granularity: str,
    year: int,
    month: int,
    day: int,
    schema_key: str,
    shard_id: int,
    projection_sha256: str,
    hash_prefix_length: int = DEFAULT_HASH_PREFIX_LENGTH,
) -> str:
    """Derive the logical T0B projection object key (pure, deterministic).

    Layout (I02 §24, partition doc §6):

    ``projections/provider=<esc>/venue=<esc>/sensor=<esc>/instrument=<esc>/``
    ``granularity=<esc>/year=<YYYY>/month=<MM>/day=<DD>/schema=<esc>/``
    ``part-<shard:05d>-<projection_sha256_prefix>.parquet``

    - Date components come from an EXPLICIT caller-adjudicated logical date;
      no date-basis inference (no ``datetime.now()``, no ingested_at, no
      provider timestamp);
    - ``schema_key`` is a PREVALIDATED caller-supplied registry key (I05 owns
      schema-registry hashing doctrine — none is invented here); it is still
      escaped so it can never become a traversal component;
    - ``shard_id`` is deterministic caller input (nonnegative int, no UUID, no
      wall clock); zero-padding width is formatting only, not scientific;
    - ``projection_sha256`` is validated in full; the prefix is a documented
      shorthand, NOT identity.
    """
    coordinates = {
        "provider": provider,
        "venue": venue,
        "sensor_family": sensor_family,
        "native_instrument": native_instrument,
        "native_granularity": native_granularity,
        "schema_key": schema_key,
    }
    for name, value in coordinates.items():
        if not isinstance(value, str) or value == "":
            raise ValueError(
                f"{name} must be a nonempty string (empty coordinates fail closed), got {value!r}"
            )
    if not isinstance(shard_id, int) or isinstance(shard_id, bool) or shard_id < 0:
        raise ValueError(
            f"shard_id must be a nonnegative int, got {shard_id!r}"
        )
    if (
        not isinstance(hash_prefix_length, int)
        or isinstance(hash_prefix_length, bool)
        or not 1 <= hash_prefix_length <= 64
    ):
        raise ValueError(
            f"hash_prefix_length must be an int in 1..64, got {hash_prefix_length!r}"
        )
    validate_sha256_hex(projection_sha256)
    try:
        logical_date = date(year, month, day)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"invalid logical date year={year!r} month={month!r} day={day!r}: {exc}"
        ) from None
    prefix = projection_sha256[:hash_prefix_length]
    return "/".join(
        [
            "projections",
            f"provider={escape_path_segment(provider)}",
            f"venue={escape_path_segment(venue)}",
            f"sensor={escape_path_segment(sensor_family)}",
            f"instrument={escape_path_segment(native_instrument)}",
            f"granularity={escape_path_segment(native_granularity)}",
            f"year={logical_date.year:04d}",
            f"month={logical_date.month:02d}",
            f"day={logical_date.day:02d}",
            f"schema={escape_path_segment(schema_key)}",
            f"part-{shard_id:05d}-{prefix}.parquet",
        ]
    )


def resolve_under_root(root: str | Path, object_key: str) -> Path:
    """Resolve a canonical object key under ``root`` — LEXICAL containment only.

    Rejects: absolute keys, Windows drive prefixes, ``..`` / ``.`` / empty
    segments, backslashes, NUL and ``:`` inside segments.  Creates NOTHING on
    disk and performs no symlink resolution: this is not a security claim
    against symlink escape (later hardening checkpoint); it is the pure
    containment contract for movable data roots.
    """
    if not isinstance(object_key, str):
        raise TypeError(
            f"object_key must be str, got {type(object_key).__name__}"
        )
    if object_key == "":
        raise ValueError("object_key must be a nonempty relative key")
    if object_key.startswith("/") or re.match(r"^[A-Za-z]:", object_key):
        raise ValueError(f"object_key must be relative, got {object_key!r}")
    if "\\" in object_key or "\x00" in object_key:
        raise ValueError(
            f"object_key contains forbidden structural characters (backslash/NUL), got {object_key!r}"
        )
    segments = object_key.split("/")
    for segment in segments:
        if segment in ("", ".", ".."):
            raise ValueError(
                f"object_key contains unsafe segment {segment!r}: {object_key!r}"
            )
        if ":" in segment or "\\" in segment or "\x00" in segment:
            raise ValueError(
                f"object_key segment {segment!r} contains a structural character"
            )
    return Path(root).joinpath(*segments)


__all__ = [
    "BLOB_KEY_PREFIX",
    "DEFAULT_HASH_PREFIX_LENGTH",
    "blob_object_key",
    "escape_path_segment",
    "projection_object_key",
    "resolve_under_root",
    "unescape_path_segment",
]
