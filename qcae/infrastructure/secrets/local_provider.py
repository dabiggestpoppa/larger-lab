"""Local SecretProvider + centralized redaction (P2-C09; Book V 13.4).

The local implementation is environment-backed: a secret class maps to an
environment variable name via an explicit, policy-supplied mapping. Workers
receive short-lived handles; resolution requires the handle and returns the
value only within the provider boundary. Raw values never enter:

- job/step stores
- event payloads
- checkpoints
- error messages (the redactor scrubs them)
- the audit log (records who/what/decision, never values)
"""

from __future__ import annotations

import os
import re
import secrets as _secrets
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.ports.secrets import SecretDecision, SecretHandle

__all__ = ["LocalSecretProvider", "Redactor"]


class _AuditEntry:
    __slots__ = ("request_id", "secret_class", "purpose", "scope", "worker_id", "granted", "reason")

    def __init__(self, request_id, secret_class, purpose, scope, worker_id, granted, reason):
        self.request_id = request_id
        self.secret_class = secret_class
        self.purpose = purpose
        self.scope = scope
        self.worker_id = worker_id
        self.granted = granted
        self.reason = reason


class LocalSecretProvider:
    """Environment-backed handles; no raw value ever leaves resolve()."""

    def __init__(
        self,
        class_to_env: Dict[str, str],
        *,
        denied_classes: Tuple[str, ...] = ("production-trading",),
        now_fn=None,
    ) -> None:
        self._class_to_env = dict(class_to_env)
        self._denied = tuple(denied_classes)
        self._now = now_fn or (lambda: "2026-09-13T12:00:00Z")
        self._handles: Dict[str, Tuple[str, SecretHandle]] = {}
        self._audit: List[_AuditEntry] = []
        self._counter = 0

    def request_secret(
        self, secret_class: str, purpose: str, scope: str,
        worker_id: str, *, ttl_seconds: int = 300,
    ) -> SecretDecision:
        self._counter += 1
        request_id = f"secreq-{self._counter:08d}"
        if secret_class in self._denied:
            self._audit.append(_AuditEntry(
                request_id, secret_class, purpose, scope, worker_id, False,
                "class denied by policy (outside proving authority)",
            ))
            return SecretDecision(
                request_id=request_id, secret_class=secret_class, granted=False,
                reason="secret class is outside standalone proving authority",
            )
        env_name = self._class_to_env.get(secret_class)
        if env_name is None or env_name not in os.environ:
            self._audit.append(_AuditEntry(
                request_id, secret_class, purpose, scope, worker_id, False,
                "no binding for class in local provider",
            ))
            return SecretDecision(
                request_id=request_id, secret_class=secret_class, granted=False,
                reason="secret class not configured locally",
            )
        handle_id = f"sechdl-{_secrets.token_hex(8)}"
        from datetime import datetime, timedelta, timezone

        expires = (
            datetime.strptime(self._now(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            + timedelta(seconds=ttl_seconds)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        handle = SecretHandle(
            handle_id=handle_id, secret_class=secret_class, purpose=purpose,
            scope=scope, expires_at=expires,
        )
        handle.validate()
        self._handles[handle_id] = (env_name, handle)
        self._audit.append(_AuditEntry(
            request_id, secret_class, purpose, scope, worker_id, True, "granted",
        ))
        return SecretDecision(
            request_id=request_id, secret_class=secret_class, granted=True,
            reason="granted", handle_id=handle_id,
        )

    def resolve(self, handle: SecretHandle) -> str:
        if not isinstance(handle, SecretHandle):
            raise QcaeValidationError("resolve requires a SecretHandle")
        entry = self._handles.get(handle.handle_id)
        if entry is None:
            raise QcaeValidationError(f"unknown or revoked handle {handle.handle_id!r}")
        env_name, stored = entry
        if stored.expires_at and self._now() > stored.expires_at:
            del self._handles[handle.handle_id]
            raise QcaeValidationError(f"handle {handle.handle_id!r} expired")
        return os.environ[env_name]

    def revoke(self, handle_id: str) -> None:
        self._handles.pop(handle_id, None)

    def audit_log(self) -> tuple:
        return tuple(
            {
                "request_id": e.request_id,
                "secret_class": e.secret_class,
                "purpose": e.purpose,
                "scope": e.scope,
                "worker_id": e.worker_id,
                "granted": e.granted,
                "reason": e.reason,
            }
            for e in self._audit
        )

    def active_handle_ids(self) -> Tuple[str, ...]:
        return tuple(self._handles)


class Redactor:
    """Centralized defensive scrubbing of secret-bearing text.

    Patterns: explicit registered values plus common credential key shapes
    (api_key=..., token=..., password=...). This is defense-in-depth — it is
    never a substitute for correct secret handling (directive §17).
    """

    _KEY_PATTERNS = re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|passwd|authorization"
        r"|private[_-]?key|credential[s]?)\b\s*([=:])\s*"
        r"(\"[^\"]*\"|'[^']*'|[^\s,;)}\]]+)"
    )

    def __init__(self) -> None:
        self._values: List[str] = []

    def register(self, value: str) -> None:
        if value:
            self._values.append(value)

    def redact(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        out = text
        for value in self._values:
            if value in out:
                out = out.replace(value, "[REDACTED]")
        out = self._KEY_PATTERNS.sub(
            lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", out
        )
        return out

    def redact_mapping(self, mapping: Dict[str, str]) -> Dict[str, str]:
        return {k: self.redact(str(v)) for k, v in mapping.items()}
