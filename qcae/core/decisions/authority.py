"""Authority request/decision primitives and provider interfaces.

Canon Book I 0.3.5–0.3.6 and master prompt §21:

- Standalone QCAE enforces a deliberately narrow local policy layer ("shim").
- The shim consumes machine-readable policy and emits machine-readable decisions.
- Intelligence is separate from authority: QCAE analysis never self-authorizes.
- The interfaces here are the stable contract that OCE will later implement
  (governance/oce adapters) without rewriting QCAE core (canon 0.3.6, Book V 14).

Actions in canon 0.3.3 always require higher authority; 0.3.4 defines the human
approval boundary. Policy actions below mirror the shim's decision set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Protocol, runtime_checkable

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str


class PolicyAction(StrEnum):
    """Local shim decision vocabulary (canon 0.3.5)."""

    MAY_DISCOVER = "may_discover"
    MAY_CLONE_TO_SANDBOX = "may_clone_to_sandbox"
    MAY_EXECUTE_IN_SANDBOX = "may_execute_in_sandbox"
    MAY_ACCESS_DATASET_CLASS = "may_access_dataset_class"
    MAY_GENERATE_ADAPTER = "may_generate_adapter"
    MAY_PERSIST_REGISTRY_RECORD = "may_persist_registry_record"
    REQUIRES_HUMAN_APPROVAL_FOR_INTEGRATION = "requires_human_approval_for_integration"


class AuthorityOutcome(StrEnum):
    """GRANT / DENY / REQUEST_MORE_EVIDENCE (canon 0.3.6)."""

    GRANT = "GRANT"
    DENY = "DENY"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"


@dataclass(frozen=True)
class AuthorityRequest(SerializableRecord):
    """A machine-readable request for authority over one policy action."""

    SCHEMA_VERSION = 1

    request_id: str
    action: PolicyAction
    subject_id: str
    justification: str
    requested_by: str

    # Free-form machine-readable context (job ref, candidate ref, dataset
    # class...). Values must be JSON-native.
    context: dict = field(default_factory=dict)

    _COERCIONS = {"action": lambda v: coerce_enum(v, PolicyAction)}

    def validate(self) -> None:
        require_identifier(self.request_id, "request_id")
        if not isinstance(self.action, PolicyAction):
            raise QcaeValidationError(
                f"action must be a PolicyAction member, got {self.action!r}"
            )
        require_identifier(self.subject_id, "subject_id")
        require_non_empty_str(self.justification, "justification")
        require_non_empty_str(self.requested_by, "requested_by")
        if not isinstance(self.context, dict):
            raise QcaeValidationError("context must be a dict")


@dataclass(frozen=True)
class AuthorityDecision(SerializableRecord):
    """A machine-readable authority result for one request."""

    SCHEMA_VERSION = 1

    decision_id: str
    request_ref: str
    action: PolicyAction
    outcome: AuthorityOutcome

    decided_by: str
    decided_at: str
    reason: str = ""

    _COERCIONS = {
        "action": lambda v: coerce_enum(v, PolicyAction),
        "outcome": lambda v: coerce_enum(v, AuthorityOutcome),
    }

    def validate(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        require_identifier(self.request_ref, "request_ref")
        if not isinstance(self.action, PolicyAction):
            raise QcaeValidationError(
                f"action must be a PolicyAction member, got {self.action!r}"
            )
        if not isinstance(self.outcome, AuthorityOutcome):
            raise QcaeValidationError(
                f"outcome must be an AuthorityOutcome member, got {self.outcome!r}"
            )
        require_non_empty_str(self.decided_by, "decided_by")
        require_non_empty_str(self.decided_at, "decided_at")


@runtime_checkable
class AuthorityProvider(Protocol):
    """Port for authority decisions (canon 0.3.5 shim now, OCE at P12).

    Implementations: governance/standalone (P2) and governance/oce (P12).
    QCAE core depends only on this Protocol.
    """

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        """Return an authority decision for the request; must not raise for denials."""
        ...


@runtime_checkable
class IdentityProvider(Protocol):
    """Port for governed identity (Book V 14.4); local shim at P2."""

    def current_identity(self) -> str:
        """Return the acting identity id for the current context."""
        ...
