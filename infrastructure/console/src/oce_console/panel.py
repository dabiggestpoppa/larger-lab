"""Queue-depth observability panel (B5-I7 governed change; charter increment I-8).

THE ONE governed change of B5-I7 (contract ``B5I7-R02``): *add a queue-depth
observability panel* over **already declared** console reads. This module is a
PROJECTION of reads, never a state owner.

Authority and prohibition (contract sections 5-14):

- ``B5I7-R15`` — only surface ids declared in the frozen B5-I2 contract pack are
  requested. An undeclared, embedded or malformed surface is refused BEFORE any
  I/O (the ``read`` callable is never invoked for it).
- ``B5I7-R16`` — reads only (``GET`` semantics via the injected read path). This
  module imports no transport write verb, holds no store handle, and performs no
  canonical-state write, invoke, lease, requeue or reconciliation.
- ``B5I7-R17`` — an unreachable stack renders ``STACK_UNREACHABLE`` for the WHOLE
  document; no partial section, no cached value, never healthy/stale/green.
- ``B5I7-R18`` — unknown or unverifiable queue values render as JSON ``null``
  with an explicit ``unknown_reason`` (never ``0``, never green); governed
  denials are carried verbatim; there is no retry path at all.
- ``B5I7-R19`` — identical inputs render BYTE-IDENTICAL canonical JSON (sorted
  keys, ASCII, single trailing newline). No wall clock, no randomness, no locale,
  no dict-iteration order can reach the rendered bytes.
- ``B5I7-R21`` — no secret, token or authorization material in panel output;
  token-shaped rendered strings are explicitly replaced with ``[redacted]`` and
  flagged, never silently copied.
- ``B5I7-R22`` — inputs and outputs are bounded (per-string, per-document,
  per-collection); oversized or malformed input is refused with the frozen
  refusal vocabulary.

Derived-state law (charter section 9; "never fabricates progress, leaves unknown
or unverifiable gaps explicit"): ``OK`` / ``DENIED`` / ``UNVERIFIABLE`` /
``STACK_UNREACHABLE`` are PRESENTATION states of this process's own document,
derived deterministically from the returned governed envelopes. They are not
canonical backend state, are persisted nowhere, authorize no transition, and can
never be written back — this module has no write path by construction.

Import-closure law: the frozen B5-I4 ``stdlib-only`` proof pins the console
package's import set, so this module imports nothing outside it. The digest
algorithm required by the canonicalization law is therefore implemented here in
pure Python and is cross-checked against ``hashlib`` by the B5-I7 evidence-law
proof (``TestEL09``/``TestPanelDeterminism``). No model, no provider, no network.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from .kernel import DEFAULT_PACK_PATH, ConsoleRefusal, load_read_surfaces

PANEL_KIND = "oce-console-panel"
PANEL_VERSION = "1.0.0"
PANEL_SCHEMA = "oce-console-panel/1.0.0"

#: The only surfaces this change may read (contract 4.4 / 7). ``health.read``
#: already carries ``pending_jobs``/``active_jobs``/``failed_jobs``/
#: ``quarantined_jobs``; ``workers.list`` and ``jobs.schedules`` supply the
#: bounded collections. No sixth status-pack section is created.
PANEL_SURFACES = ("health.read", "workers.list", "jobs.schedules")

#: Panel field -> the governed source field inside ``health.read``'s data.
QUEUE_FIELDS = ("pending", "active", "failed", "quarantined")
QUEUE_SOURCE_FIELDS = {
    "pending": "pending_jobs",
    "active": "active_jobs",
    "failed": "failed_jobs",
    "quarantined": "quarantined_jobs",
}

STATE_OK = "OK"
STATE_UNREACHABLE = "STACK_UNREACHABLE"
STATE_DENIED = "DENIED"
STATE_UNVERIFIABLE = "UNVERIFIABLE"
PANEL_STATES = (STATE_OK, STATE_UNREACHABLE, STATE_DENIED, STATE_UNVERIFIABLE)

MAX_STRING_BYTES = 4096
MAX_DOCUMENT_BYTES = 65536
MAX_COLLECTION_ITEMS = 64
MAX_SURFACE_COUNT = 8

#: The frozen canonicalization law (contract section 22; mission section 8).
#: Rendered into the document itself so a reviewer can check the law the bytes
#: obey without reading this module.
CANONICALIZATION_LAW = {
    "schema": PANEL_SCHEMA,
    "field_set": (
        "closed and exhaustive: kind, version, schema, non_authoritative, state, "
        "queue, workers, schedules, reads, snapshot, provenance"
    ),
    "field_ordering": "JSON sort_keys=True (code-point ascending) at every level",
    "collection_ordering": "ids sorted ascending; queue fields in QUEUE_FIELDS order; "
                          "surfaces in PANEL_SURFACES order",
    "numeric_normalization": (
        "integral counts only; bool is never a count; a negative count is UNKNOWN "
        "and is never clamped to zero"
    ),
    "timestamp_treatment": (
        "only a caller-supplied governed observation time is rendered; no wall "
        "clock is read and none can reach the bytes"
    ),
    "unknown_representation": "{value: null, known: false, unknown_reason: <str>}",
    "partial_representation": (
        "reads[<surface>].partial = true plus a per-field unknown_reason; a partial "
        "read never summarizes as success"
    ),
    "omitted_vs_null": (
        "no field is ever omitted; absent governed data renders null + "
        "unknown_reason (omission is not a representation)"
    ),
    "encoding": "UTF-8 with ensure_ascii=True",
    "newline": "exactly one trailing newline",
    "digest": "sha256 over the rendered canonical bytes of this document",
}

#: Token-shaped material that must never reach the rendered document (R21).
_SECRET_MARKERS = (
    "bearer ",
    "authorization:",
    "x-oce-grant",
    "x-oce-actor",
    "private_key",
    "secret=",
)
REDACTED = "[redacted]"

# ── pure-Python sha256 (import-closure law; see module docstring) ────────────
_SHA256_K = (
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1,
    0x923F82A4, 0xAB1C5ED5, 0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
    0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174, 0xE49B69C1, 0xEFBE4786,
    0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147,
    0x06CA6351, 0x14292967, 0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
    0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85, 0xA2BFE8A1, 0xA81A664B,
    0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A,
    0x5B9CCA4F, 0x682E6FF3, 0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
    0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
)
_MASK32 = 0xFFFFFFFF


def _rotr(value: int, bits: int) -> int:
    return ((value >> bits) | (value << (32 - bits))) & _MASK32


def normalize_blob_bytes(data: bytes) -> bytes:
    """Normalize checkout line endings to the repository's stored form (LF).

    ``.gitattributes`` stores ``infrastructure/**/*.py`` as LF, so the same
    logical file has CRLF bytes in a Windows working tree and LF bytes in a
    Linux one. Hashing raw working-tree bytes would make the panel's own
    provenance platform-dependent, violating ``B5I7-R19`` (identical inputs
    render identical bytes) for the pack and source digests. Provenance is
    therefore hashed over the normalized blob, which is identical on every
    checkout and equal to the stored git blob.
    """
    # byte values, not escapes: CR=13, LF=10
    return data.replace(bytes((13, 10)), bytes((10,)))

def sha256_hex(data: bytes) -> str:
    """sha256 of ``data`` as lowercase hex (pure Python, import-closure safe)."""
    if not isinstance(data, (bytes, bytearray)):
        raise ConsoleRefusal("malformed_request", "sha256 input must be bytes")
    message = bytearray(data)
    bit_length = (len(message) * 8) & 0xFFFFFFFFFFFFFFFF
    message.append(0x80)
    while len(message) % 64 != 56:
        message.append(0x00)
    message.extend(bit_length.to_bytes(8, "big"))
    hash_words = [
        0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
        0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
    ]
    for offset in range(0, len(message), 64):
        block = message[offset:offset + 64]
        word = [int.from_bytes(block[i:i + 4], "big") for i in range(0, 64, 4)]
        for i in range(16, 64):
            s0 = _rotr(word[i - 15], 7) ^ _rotr(word[i - 15], 18) ^ (word[i - 15] >> 3)
            s1 = _rotr(word[i - 2], 17) ^ _rotr(word[i - 2], 19) ^ (word[i - 2] >> 10)
            word.append((word[i - 16] + s0 + word[i - 7] + s1) & _MASK32)
        a, b, c, d, e, f, g, h = hash_words
        for i in range(64):
            s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((~e & _MASK32) & g)
            temp1 = (h + s1 + ch + _SHA256_K[i] + word[i]) & _MASK32
            s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & _MASK32
            h, g, f, e = g, f, e, (d + temp1) & _MASK32
            d, c, b, a = c, b, a, (temp1 + temp2) & _MASK32
        hash_words = [
            (hash_words[0] + a) & _MASK32, (hash_words[1] + b) & _MASK32,
            (hash_words[2] + c) & _MASK32, (hash_words[3] + d) & _MASK32,
            (hash_words[4] + e) & _MASK32, (hash_words[5] + f) & _MASK32,
            (hash_words[6] + g) & _MASK32, (hash_words[7] + h) & _MASK32,
        ]
    return "".join(f"{part:08x}" for part in hash_words)


# ── bounded rendering helpers ───────────────────────────────────────────────

def _bounded_text(value: object, field: str) -> tuple[Optional[str], bool]:
    """Render one string field under the bound + redaction laws (R21/R22).

    Returns ``(rendered, redacted)``. A non-string renders ``None`` (the caller
    turns that into an explicit unknown). An over-bound string is REFUSED — a
    truncated identity would be a fabricated identity.
    """
    if not isinstance(value, str):
        return None, False
    if len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise ConsoleRefusal(
            "payload_too_large", f"{field} exceeds {MAX_STRING_BYTES} bytes"
        )
    lowered = value.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        return REDACTED, True
    return value, False


_MAX_SANITIZE_DEPTH = 8


def _sanitize(value: object, field: str, depth: int = 0) -> object:
    """Recursively apply the bound + redaction laws to a verbatim payload (R21).

    A governed denial is rendered verbatim (R18), but "verbatim" may not leak
    authorization material: every string in the carried payload — including
    nested request ids and denial details — passes the same bounded/redacted
    rendering as a top-level field. Depth and collection width are bounded so a
    hostile payload cannot drive unbounded work (R22).
    """
    if depth > _MAX_SANITIZE_DEPTH:
        return REDACTED
    if isinstance(value, str):
        text, _ = _bounded_text(value, field)
        return text
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        rendered: dict = {}
        for key, item in value.items():
            key_text, _ = _bounded_text(key, f"{field}.key")
            if key_text is None:
                raise ConsoleRefusal("malformed_request", f"{field}: non-string key")
            rendered[key_text] = _sanitize(item, f"{field}.{key_text}", depth + 1)
        return rendered
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise ConsoleRefusal(
                "payload_too_large", f"{field}: collection over {MAX_COLLECTION_ITEMS}"
            )
        return [_sanitize(item, f"{field}[]", depth + 1) for item in value]
    return REDACTED


def _unknown(reason: str) -> dict:
    """The frozen unknown representation: null + reason, NEVER zero."""
    return {"value": None, "known": False, "unknown_reason": reason}


def _known(value: int) -> dict:
    return {"value": int(value), "known": True, "unknown_reason": None}


def _queue_value(data: object, field: str) -> dict:
    """Extract one queue counter, or an explicit unknown — never a default."""
    if not isinstance(data, dict):
        return _unknown("data_not_an_object")
    source = QUEUE_SOURCE_FIELDS[field]
    if source not in data:
        return _unknown("not_reported")
    raw = data[source]
    if isinstance(raw, bool) or not isinstance(raw, int):
        return _unknown("not_an_integer")
    if raw < 0:
        return _unknown("negative_value")
    return _known(raw)


def _collection(data: object, keys: Sequence[str], field: str) -> dict:
    """Project one bounded id collection, deterministically ordered.

    Accepts a mapping of id -> record or a list of ids; anything else is an
    explicit unknown. Ordering is sorted ascending so the rendered bytes can
    never depend on dict insertion order (R19).
    """
    if not isinstance(data, dict):
        return {"known": False, "count": _unknown("data_not_an_object"),
                "ids": [], "truncated": False, "bound": MAX_COLLECTION_ITEMS,
                "redacted": False}
    value = None
    for key in keys:
        if key in data:
            value = data[key]
            break
    if value is None:
        return {"known": False, "count": _unknown("not_reported"),
                "ids": [], "truncated": False, "bound": MAX_COLLECTION_ITEMS,
                "redacted": False}
    if isinstance(value, dict):
        raw_ids = list(value.keys())
    elif isinstance(value, list):
        raw_ids = [item.get("id") if isinstance(item, dict) else item for item in value]
    else:
        return {"known": False, "count": _unknown("not_a_collection"),
                "ids": [], "truncated": False, "bound": MAX_COLLECTION_ITEMS,
                "redacted": False}
    rendered: list[str] = []
    redacted_any = False
    for item in raw_ids:
        text, was_redacted = _bounded_text(item, f"{field}.id")
        if text is None:
            return {"known": False, "count": _unknown("non_string_id"),
                    "ids": [], "truncated": False, "bound": MAX_COLLECTION_ITEMS,
                    "redacted": False}
        redacted_any = redacted_any or was_redacted
        rendered.append(text)
    rendered.sort()
    total = len(rendered)
    truncated = total > MAX_COLLECTION_ITEMS
    return {
        "known": True,
        "count": _known(total),
        "ids": rendered[:MAX_COLLECTION_ITEMS],
        "truncated": truncated,
        "bound": MAX_COLLECTION_ITEMS,
        "redacted": redacted_any,
    }


def _envelope_state(response: object) -> tuple[str, Optional[dict], str]:
    """Classify one governed response: (read state, verbatim envelope, reason)."""
    if not isinstance(response, dict):
        return STATE_UNVERIFIABLE, None, "response_not_an_envelope"
    if not all(key in response for key in ("ok", "status", "data")):
        return STATE_UNVERIFIABLE, None, "envelope_fields_missing"
    verbatim = {
        "ok": response.get("ok"),
        "status": response.get("status"),
        "data": response.get("data"),
        "error": response.get("error", ""),
        "request_id": response.get("request_id", ""),
    }
    if response.get("ok") is not True:
        if str(response.get("status", "")).lower() == "denied":
            return STATE_DENIED, verbatim, "governed_denial"
        return STATE_UNVERIFIABLE, verbatim, "governed_not_ok"
    return STATE_OK, verbatim, ""


def _validate_requested(
    surfaces: Mapping[str, str], requested: Optional[Sequence[str]]
) -> tuple[str, ...]:
    """Validate the requested surface set BEFORE any I/O (R15, F3/F4)."""
    if requested is None:
        return PANEL_SURFACES
    if isinstance(requested, (str, bytes)) or not isinstance(requested, Sequence):
        raise ConsoleRefusal("malformed_request", "requested surfaces not a sequence")
    if len(requested) > MAX_SURFACE_COUNT:
        raise ConsoleRefusal(
            "payload_too_large", f"{len(requested)} surfaces > {MAX_SURFACE_COUNT}"
        )
    seen: list[str] = []
    for entry in requested:
        if not isinstance(entry, str):
            raise ConsoleRefusal("malformed_request", f"non-string surface {entry!r}")
        if len(entry.encode("utf-8")) > MAX_STRING_BYTES:
            raise ConsoleRefusal("payload_too_large", "surface id over bound")
        if entry not in PANEL_SURFACES or entry not in surfaces:
            # Undeclared, embedded or unknown: refused before the read path
            # is ever called (matrix F3), never resolved by a fallback.
            raise ConsoleRefusal("unsupported_surface", entry)
        if entry in seen:
            # A duplicate identifier would double-count queue depth (F4).
            raise ConsoleRefusal("duplicate_surface", entry)
        seen.append(entry)
    return tuple(seen)


def _pack_sha256(pack_path: Optional[Path]) -> Optional[str]:
    """Digest the frozen contract pack; unknown when unreadable (never faked)."""
    path = Path(pack_path) if pack_path is not None else DEFAULT_PACK_PATH
    try:
        return sha256_hex(normalize_blob_bytes(path.read_bytes()))
    except (OSError, ConsoleRefusal):
        return None


def _source_identity() -> Optional[str]:
    """Digest this module's own bytes so the panel names its own source."""
    try:
        return sha256_hex(normalize_blob_bytes(Path(__file__).resolve().read_bytes()))
    except (OSError, ConsoleRefusal):
        return None


def render_panel(document: Mapping[str, object]) -> str:
    """Render the canonical panel text (R19): sorted, ASCII, one trailing LF."""
    text = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ConsoleRefusal(
            "payload_too_large", f"panel document exceeds {MAX_DOCUMENT_BYTES} bytes"
        )
    return text


def canonical_digest(document: Mapping[str, object]) -> str:
    """The panel's digest law: sha256 over the rendered canonical bytes."""
    return sha256_hex(render_panel(document).encode("utf-8"))


def build_panel_document(
    read: Callable[[str], object],
    surfaces: Optional[Mapping[str, str]] = None,
    *,
    pack_path: Optional[Path] = None,
    surfaces_requested: Optional[Sequence[str]] = None,
    observed_at: Optional[str] = None,
    prior_snapshot_id: Optional[str] = None,
) -> dict:
    """Build the read-only queue-depth panel (the single governed change).

    ``read(surface)`` is the same injected read callable the status kernel uses;
    it is called exactly once per surface, in ``PANEL_SURFACES`` order, and never
    for a refused surface. There is no retry, no cache, and no write path.
    """
    if surfaces is None:
        surfaces = load_read_surfaces(pack_path)
    else:
        surfaces = dict(surfaces)

    # (1) Refusal ordering: every surface is validated BEFORE any I/O.
    for surface in PANEL_SURFACES:
        if surface not in surfaces:
            raise ConsoleRefusal("unsupported_surface", surface)
    selected = _validate_requested(surfaces, surfaces_requested)

    # (2) One read per surface, fixed order, no retry (R16, R18).
    reads: dict[str, dict] = {}
    responses: dict[str, object] = {}
    unreachable = False
    interrupted_at = ""
    for surface in selected:
        try:
            response = read(surface)
        except Exception as exc:  # fail closed, whole document (R17 / F-1)
            unreachable = True
            interrupted_at = f"{surface}: {type(exc).__name__}"
            break
        responses[surface] = response

    if unreachable:
        return _unreachable_document(surfaces, selected, interrupted_at, pack_path)

    for surface in selected:
        response = responses[surface]
        state, verbatim, reason = _envelope_state(response)
        entry = {
            "state": state,
            "available": state == STATE_OK,
            "reason": reason,
            "partial": False,
        }
        if verbatim is not None:
            entry["response"] = _sanitize(verbatim, surface)
            request_id, redacted = _bounded_text(
                verbatim.get("request_id", ""), f"{surface}.request_id"
            )
            entry["request_id"] = request_id
            entry["redacted"] = redacted
        reads[surface] = entry

    health_state = reads.get("health.read", {}).get("state", STATE_UNVERIFIABLE)
    health_data = (
        responses.get("health.read", {})
        if isinstance(responses.get("health.read"), dict)
        else {}
    )
    health_data = health_data.get("data") if isinstance(health_data, dict) else None

    queue: dict[str, object] = {"surfaces_used": list(selected)}
    known_count = 0
    for field in QUEUE_FIELDS:
        if health_state == STATE_OK:
            entry = _queue_value(health_data, field)
        elif health_state == STATE_DENIED:
            entry = _unknown("read_denied")
        else:
            entry = _unknown("read_unverifiable")
        if entry["known"]:
            known_count += 1
        queue[field] = entry

    # Bounded depth: derived ONLY when both of its inputs are known, otherwise
    # an explicit unknown — a partial sum is never presented as a depth.
    pending, active = queue["pending"], queue["active"]
    if pending["known"] and active["known"]:
        queue["depth"] = _known(pending["value"] + active["value"])
        queue["depth"]["basis"] = "pending+active"
    else:
        reason = (
            "pending_unknown" if not pending["known"] else "active_unknown"
        )
        queue["depth"] = _unknown(reason)
        queue["depth"]["basis"] = "pending+active"

    # "Partial is not success" (contract section 7; matrix F-12): a read that
    # returns an intact envelope but does not yield EVERY counter is PARTIAL,
    # and a partial read never summarizes as OK. Unknown is never silently
    # green, and a fully-unreported queue is not an empty queue.
    if health_state == STATE_OK and known_count < len(QUEUE_FIELDS):
        reads["health.read"]["partial"] = True

    workers = _collection(
        responses.get("workers.list", {}).get("data")
        if isinstance(responses.get("workers.list"), dict) else None,
        ("workers", "items"),
        "workers",
    )
    schedules = _collection(
        responses.get("jobs.schedules", {}).get("data")
        if isinstance(responses.get("jobs.schedules"), dict) else None,
        ("schedules", "items"),
        "schedules",
    )

    # A collection surface whose envelope is intact but whose collection is
    # absent/unusable is a PARTIAL read, never a validated empty collection.
    if "workers.list" in reads and not workers["known"]:
        reads["workers.list"]["partial"] = True
    if "jobs.schedules" in reads and not schedules["known"]:
        reads["jobs.schedules"]["partial"] = True

    # (3) Summary state, derived deterministically from the read states.
    read_states = [entry["state"] for entry in reads.values()]
    partial_any = any(entry.get("partial") for entry in reads.values())
    if STATE_DENIED in read_states:
        state = STATE_DENIED
    elif any(item != STATE_OK for item in read_states) or partial_any:
        state = STATE_UNVERIFIABLE
    else:
        state = STATE_OK

    unavailable = sorted(
        surface for surface, entry in reads.items() if entry["state"] != STATE_OK
    )
    consistent = not unavailable
    snapshot_id = sha256_hex(
        json.dumps(
            {"reads": reads, "queue": queue, "workers": workers,
             "schedules": schedules},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
    )

    observed_text, observed_redacted = _bounded_text(observed_at, "observed_at")
    if observed_text is None:
        currency, currency_reason = "UNKNOWN", "no_governed_observation_time"
    else:
        currency, currency_reason = "CURRENT", None

    return {
        "kind": PANEL_KIND,
        "version": PANEL_VERSION,
        "schema": PANEL_SCHEMA,
        # The panel never claims canonical authority (charter section 5 rule 9).
        "non_authoritative": True,
        "state": state,
        "queue": queue,
        "workers": workers,
        "schedules": schedules,
        "reads": reads,
        "snapshot": {
            "id": snapshot_id,
            "surface_ids": list(selected),
            "consistent": consistent,
            "inconsistent_reason": (
                None if consistent else "surface_unavailable:" + ",".join(unavailable)
            ),
            "currency": currency,
            "currency_reason": currency_reason,
            "observed_at": observed_text,
            "observed_at_redacted": observed_redacted,
            "replay": bool(prior_snapshot_id is not None
                           and prior_snapshot_id == snapshot_id),
            "prior_snapshot_id": prior_snapshot_id,
        },
        "provenance": {
            "source_identity": _source_identity(),
            "contract_pack_sha256": _pack_sha256(pack_path),
            "panel_version": PANEL_VERSION,
            "canonicalization": dict(CANONICALIZATION_LAW),
        },
    }


def _unreachable_document(
    surfaces: Mapping[str, str],
    selected: Sequence[str],
    interrupted_at: str,
    pack_path: Optional[Path],
) -> dict:
    """Fail-closed whole-document render (R17): no section survives as green."""
    queue: dict[str, object] = {"surfaces_used": list(selected)}
    for field in QUEUE_FIELDS:
        queue[field] = _unknown("stack_unreachable")
    queue["depth"] = _unknown("stack_unreachable")
    queue["depth"]["basis"] = "pending+active"
    return {
        "kind": PANEL_KIND,
        "version": PANEL_VERSION,
        "schema": PANEL_SCHEMA,
        "non_authoritative": True,
        "state": STATE_UNREACHABLE,
        "queue": queue,
        "workers": {"known": False, "count": _unknown("stack_unreachable"),
                    "ids": [], "truncated": False,
                    "bound": MAX_COLLECTION_ITEMS, "redacted": False},
        "schedules": {"known": False, "count": _unknown("stack_unreachable"),
                      "ids": [], "truncated": False,
                      "bound": MAX_COLLECTION_ITEMS, "redacted": False},
        "reads": {},
        "snapshot": {
            "id": None,
            "surface_ids": list(selected),
            "consistent": False,
            "inconsistent_reason": "stack_unreachable",
            "currency": "UNKNOWN",
            "currency_reason": "stack_unreachable",
            "observed_at": None,
            "observed_at_redacted": False,
            "replay": False,
            "prior_snapshot_id": None,
            "interrupted_at": interrupted_at,
        },
        "provenance": {
            "source_identity": _source_identity(),
            "contract_pack_sha256": _pack_sha256(pack_path),
            "panel_version": PANEL_VERSION,
            "canonicalization": dict(CANONICALIZATION_LAW),
        },
    }
