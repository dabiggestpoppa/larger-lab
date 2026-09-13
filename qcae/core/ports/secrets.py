"""SecretProvider port (P2-C09; Book V 13.4, directive §16).

Jobs store SECRET REFERENCES, never secret values. Workers request secret
handles through the provider by class/purpose/scope — never raw paths.
The local implementation lives in infrastructure/secrets; production trading
credentials remain outside ordinary QCAE proving authority (canon 13.4
invariant 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = ["SecretDecision", "SecretHandle", "SecretProvider"]


@dataclass(frozen=True)
class SecretHandle(SerializableRecord):
    """A revocable reference to a secret — never the value itself."""

    SCHEMA_VERSION = 1

    handle_id: str
    secret_class: str
    purpose: str
    scope: str
    expires_at: str = ""

    def validate(self) -> None:
        require_identifier(self.handle_id, "handle_id")
        require_non_empty_str(self.secret_class, "secret_class")
        require_non_empty_str(self.purpose, "purpose")
        require_non_empty_str(self.scope, "scope")


@dataclass(frozen=True)
class SecretDecision(SerializableRecord):
    """Provider's answer to a secret request (DENY / REQUIRE_APPROVAL / grant)."""

    SCHEMA_VERSION = 1

    request_id: str
    secret_class: str
    granted: bool
    reason: str
    handle_id: str = ""  # set only when granted

    def validate(self) -> None:
        require_identifier(self.request_id, "request_id")
        require_non_empty_str(self.secret_class, "secret_class")
        require_non_empty_str(self.reason, "reason")
        if self.granted and not self.handle_id:
            raise ValueError("granted secret decisions must carry a handle_id")


@runtime_checkable
class SecretProvider(Protocol):
    """Boundary every secret access must pass through (canon 13.4)."""

    def request_secret(
        self, secret_class: str, purpose: str, scope: str,
        worker_id: str, *, ttl_seconds: int = 300,
    ) -> SecretDecision:
        """Grant a handle, deny, or require approval; never return raw values."""
        ...

    def resolve(self, handle: SecretHandle) -> str:
        """Resolve a handle for the current worker context only."""
        ...

    def revoke(self, handle_id: str) -> None:
        """Revoke immediately (failed/suspicious runs; canon 13.4 rotation)."""
        ...

    def audit_log(self) -> tuple:
        """Record who requested which class/purpose/scope/decision — no values."""
        ...
