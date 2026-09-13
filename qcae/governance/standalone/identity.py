"""Local identity (P2-C04; Book V 13.1 runtime identity, directive §15).

Minimum standalone identities: operator, runtime, worker/service. Stable
enough for authority decisions, audit events, job ownership, and approval
decisions. OCE replaces/adapts this at P12 through the same Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = ["IdentityKind", "LocalIdentity", "LocalIdentityProvider"]


class IdentityKind(StrEnum):
    OPERATOR = "OPERATOR"
    RUNTIME = "RUNTIME"
    WORKER = "WORKER"
    SERVICE = "SERVICE"


@dataclass(frozen=True)
class LocalIdentity(SerializableRecord):
    SCHEMA_VERSION = 1

    identity_id: str
    kind: IdentityKind
    display_name: str = ""

    def validate(self) -> None:
        require_identifier(self.identity_id, "identity_id")
        if not isinstance(self.kind, IdentityKind):
            raise QcaeValidationError(
                f"kind must be an IdentityKind member, got {self.kind!r}"
            )
        if self.display_name:
            require_non_empty_str(self.display_name, "display_name")


class LocalIdentityProvider:
    """Static local identity registry implementing the P0 Protocol."""

    def __init__(self) -> None:
        self._identities: Dict[str, LocalIdentity] = {}
        self._current: Optional[str] = None
        # Boot identity: the runtime itself.
        runtime = LocalIdentity(identity_id="id-runtime-local", kind=IdentityKind.RUNTIME,
                                display_name="local runtime")
        self._identities[runtime.identity_id] = runtime
        self._current = runtime.identity_id

    def register(self, identity: LocalIdentity) -> None:
        identity.validate()
        if identity.identity_id in self._identities:
            raise QcaeValidationError(
                f"identity {identity.identity_id!r} already registered"
            )
        self._identities[identity.identity_id] = identity

    def get(self, identity_id: str) -> Optional[LocalIdentity]:
        return self._identities.get(identity_id)

    def require(self, identity_id: str) -> LocalIdentity:
        identity = self._identities.get(identity_id)
        if identity is None:
            raise QcaeValidationError(f"unknown identity {identity_id!r}")
        return identity

    def set_current(self, identity_id: str) -> None:
        self.require(identity_id)
        self._current = identity_id

    def current_identity(self) -> str:
        """P0 IdentityProvider Protocol."""
        return self._current

    def known_ids(self):
        return sorted(self._identities)
