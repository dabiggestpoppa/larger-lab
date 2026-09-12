"""Secret redaction (T2-MODEL-04 / 04 §20).

Secrets and tokens are never written into probe evidence: not in headers, not
in query parameters, not in URLs, not in native error detail.  Tests use fake
credentials only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED = "***REDACTED***"

#: Header / parameter / field names treated as secret (case-insensitive).
SECRET_KEYS: frozenset[str] = frozenset(
    {
        "apikey",
        "api_key",
        "api-key",
        "key",
        "token",
        "secret",
        "authorization",
        "x-api-key",
        "x-apikey",
        "signature",
        "sig",
        "password",
        "passwd",
        "credential",
        "credentials",
        "cookie",
        "session",
        "access-token",
        "refresh-token",
    }
)

#: Common secret value shapes (API keys, JWTs, bearer tokens).
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|bearer)\s*[:=]\s*[A-Za-z0-9_\-\.]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),  # JWT
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
)


def _is_secret_key(key: str) -> bool:
    normalized = key.strip().lower().replace("_", "-").replace(" ", "-")
    return normalized in SECRET_KEYS


def redact_value(key: str, value: Any) -> Any:
    """Redact a single value when its key is secret."""
    if _is_secret_key(key):
        return REDACTED
    return value


def redact_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    """Redact secret keys in a flat or nested mapping (headers, params)."""
    if not mapping:
        return {}
    result: dict[str, Any] = {}
    for key, value in mapping.items():
        if _is_secret_key(str(key)):
            result[str(key)] = REDACTED
        elif isinstance(value, Mapping):
            result[str(key)] = redact_mapping(value)
        elif isinstance(value, list):
            result[str(key)] = [
                redact_mapping(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            result[str(key)] = value
    return result


def redact_url(url: str) -> str:
    """Redact query parameter values whose keys are secret, plus userinfo."""
    if "://" in url:
        scheme, _, rest = url.partition("://")
        if "@" in rest:
            userinfo, _, rest = rest.rpartition("@")
            redacted_userinfo = REDACTED if userinfo else userinfo
            rest = f"{redacted_userinfo}@{rest}"
        url = f"{scheme}://{rest}"
    if "?" not in url:
        return url
    base, _, query = url.partition("?")
    parts = []
    for pair in query.split("&"):
        if not pair:
            continue
        key, sep, _value = pair.partition("=")
        if _is_secret_key(key):
            parts.append(f"{key}={REDACTED}")
        else:
            parts.append(pair if sep else f"{key}={REDACTED}")
    return f"{base}?{'&'.join(parts)}"


def scrub_secrets(text: str | None) -> str | None:
    """Replace recognizable secret shapes inside free text (error messages)."""
    if text is None:
        return None
    scrubbed = text
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub(REDACTED, scrubbed)
    return scrubbed
