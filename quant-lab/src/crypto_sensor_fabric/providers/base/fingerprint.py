"""Deterministic request fingerprinting + payload integrity hashing (01 §7).

Fingerprint inputs (01 §7):

    provider_id
    endpoint_or_archive_family
    sensor_family
    native_instrument
    start
    end
    granularity
    page/cursor inputs
    adapter_semantic_version

Guarantees:

- identical semantic request -> identical fingerprint
- material semantic change -> different fingerprint
- ordering/serialization noise never changes the fingerprint
  (keys sorted, timestamps normalized to UTC ISO, cursors serialized
   deterministically)

The payload hash is a deterministic integrity hash over the raw body bytes
or faithful textual form; it changes if and only if the raw content changes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from .models import FetchRequest


def _stable_json(value: Any) -> str:
    """Deterministic JSON text: sorted keys, compact separators, ISO datetimes."""
    if isinstance(value, datetime):
        return value.astimezone().isoformat()
    if isinstance(value, dict):
        return json.dumps(
            {str(k): _stable_json(v) for k, v in sorted(value.items())},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    if isinstance(value, (list, tuple)):
        return json.dumps(
            [_stable_json(v) for v in value],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    if isinstance(value, Enum):
        return str(value)
    if value is None:
        return "null"
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint_request(
    request: FetchRequest,
    endpoint_or_archive_family: str,
    page_or_cursor_inputs: dict[str, Any] | None = None,
    algorithm: str = "sha256",
) -> str:
    """Deterministic semantic fingerprint of one acquisition request.

    `endpoint_or_archive_family` is the provider-native endpoint/archive
    family (e.g. ``/api/charts/v1/analytics`` or ``data.binance.vision``),
    NOT the full URL with volatile query values — only semantic identity.
    """
    start = request.start_time.astimezone().isoformat()
    end = request.end_time.astimezone().isoformat()
    resume = (
        request.resume_token.model_dump_json() if request.resume_token else None
    )
    payload = {
        "provider_id": request.provider_id,
        "endpoint_or_archive_family": endpoint_or_archive_family,
        "sensor_family": str(request.sensor_family),
        "native_instrument": request.native_instrument_id,
        "start": start,
        "end": end,
        "granularity": str(request.granularity) if request.granularity else None,
        "page_size_hint": request.page_size_hint,
        "purpose": str(request.purpose),
        "page_or_cursor_inputs": _stable_json(page_or_cursor_inputs or {}),
        "resume_token": resume,
        "adapter_semantic_version": request.adapter_semantic_version,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.new(algorithm, canonical.encode("utf-8")).hexdigest()


def payload_hash(raw_body: bytes | str, algorithm: str = "sha256") -> str:
    """Deterministic integrity hash of a raw payload body.

    Bytes are hashed directly; strings are hashed as UTF-8.  Same content
    always yields the same hash regardless of container/ordering concerns.
    """
    data = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
    return hashlib.new(algorithm, data).hexdigest()
