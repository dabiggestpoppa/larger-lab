"""Approval + escalation workflow (P2-C05; Book V 12.8, directive §13-14, §30).

Approval law (directive §14, Book V 12.8 "No Approval Laundering"):

- an approval binds (principal, action, resource, scope, budget) exactly;
- an approval for action X / scope A / budget B never authorizes
  action Y / scope C / budget D;
- expired approvals cannot execute;
- an approval from the wrong approver/authority domain cannot execute;
- approval is a NEW durable record — the original request is never edited;
- no response is not approval.

Escalation law (Book V 12.8): durable, evidence-backed, option-oriented;
human decisions become durable artifacts; a job/step waits while escalation
is open and resumes or terminates per the decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import List, Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)

__all__ = [
    "ApprovalState",
    "EscalationState",
    "EscalationTrigger",
    "ApprovalRequest",
    "ApprovalDecision",
    "EscalationRecord",
    "EscalationDecision",
    "ApprovalRegistry",
    "APPROVAL_DDL",
]


class ApprovalState(StrEnum):
    PENDING = "PENDING"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"


class EscalationState(StrEnum):
    OPEN = "OPEN"
    RESOLVED_CONTINUE = "RESOLVED_CONTINUE"
    RESOLVED_TERMINATE = "RESOLVED_TERMINATE"
    RESOLVED_DEFER = "RESOLVED_DEFER"


class EscalationTrigger(StrEnum):
    """Canon-defined triggers (Book V 12.8)."""

    LEGAL_AMBIGUITY = "LEGAL_AMBIGUITY"
    SECURITY_AMBIGUITY = "SECURITY_AMBIGUITY"
    PRIVATE_DATA_EGRESS = "PRIVATE_DATA_EGRESS"
    PRODUCTION_CREDENTIAL_REQUEST = "PRODUCTION_CREDENTIAL_REQUEST"
    HARD_CONTRADICTION = "HARD_CONTRADICTION"
    MATERIAL_CONTRACT_CHANGE = "MATERIAL_CONTRACT_CHANGE"
    FORK_VENDOR_COMMITMENT = "FORK_VENDOR_COMMITMENT"
    PRODUCTION_AUTHORITY = "PRODUCTION_AUTHORITY"
    CAPITAL_AUTHORITY = "CAPITAL_AUTHORITY"
    IRREVERSIBLE_ACTION = "IRREVERSIBLE_ACTION"
    BUDGET_INCREASE = "BUDGET_INCREASE"


@dataclass(frozen=True)
class ApprovalRequest(SerializableRecord):
    """What is being asked, by whom, for exactly what scope."""

    SCHEMA_VERSION = 1

    request_id: str
    principal: str
    action: str
    resource: str
    scope: str
    budget_ref: str
    justification: str
    created_at: str

    # Approval windows are explicit; empty means "must be decided in-policy".
    expires_at: str = ""

    def validate(self) -> None:
        require_identifier(self.request_id, "request_id")
        require_non_empty_str(self.principal, "principal")
        require_non_empty_str_strict(self.action, "action")
        require_non_empty_str(self.resource, "resource")
        require_non_empty_str(self.scope, "scope")
        require_non_empty_str(self.budget_ref, "budget_ref")
        require_non_empty_str(self.justification, "justification")
        require_non_empty_str(self.created_at, "created_at")


@dataclass(frozen=True)
class ApprovalDecision(SerializableRecord):
    """The operator's answer — a separate artifact from the request."""

    SCHEMA_VERSION = 1

    decision_id: str
    request_ref: str
    state: ApprovalState

    decided_by: str
    decided_at: str
    # Exact binding the grant covers; must equal the request's binding.
    bound_action: str
    bound_resource: str
    bound_scope: str
    bound_budget_ref: str

    reason: str = ""
    constraints: Tuple[str, ...] = ()

    _COERCIONS = {"state": lambda v: coerce_enum(v, ApprovalState)}

    def validate(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        require_identifier(self.request_ref, "request_ref")
        if not isinstance(self.state, ApprovalState):
            raise QcaeValidationError(
                f"state must be an ApprovalState member, got {self.state!r}"
            )
        require_non_empty_str(self.decided_by, "decided_by")
        require_non_empty_str(self.decided_at, "decided_at")
        require_non_empty_str_strict(self.bound_action, "bound_action")
        require_non_empty_str(self.bound_resource, "bound_resource")
        require_non_empty_str(self.bound_scope, "bound_scope")
        require_non_empty_str(self.bound_budget_ref, "bound_budget_ref")
        if self.state is ApprovalState.GRANTED and not self.reason:
            raise QcaeValidationError("grants must record their reason")


def require_non_empty_str_strict(value, what):
    if not isinstance(value, str) or not value.strip():
        raise QcaeValidationError(f"{what} must be a non-empty string")


@dataclass(frozen=True)
class EscalationRecord(SerializableRecord):
    """Durable escalation packet (Book V 12.8 Escalation Packet)."""

    SCHEMA_VERSION = 1

    escalation_id: str
    trigger: EscalationTrigger
    job_id: str
    step_id: str
    decision_requested: str
    why_policy_cannot_decide: str
    options: Tuple[str, ...]
    supporting_evidence_refs: Tuple[str, ...]
    known_risks: Tuple[str, ...]
    reversibility: str
    consequence_of_no_decision: str
    created_at: str

    state: EscalationState = EscalationState.OPEN
    recommended_option: str = ""

    _COERCIONS = {
        "trigger": lambda v: coerce_enum(v, EscalationTrigger),
        "state": lambda v: coerce_enum(v, EscalationState),
    }

    def validate(self) -> None:
        require_identifier(self.escalation_id, "escalation_id")
        if not isinstance(self.trigger, EscalationTrigger):
            raise QcaeValidationError(
                f"trigger must be an EscalationTrigger member, got {self.trigger!r}"
            )
        require_identifier(self.job_id, "job_id")
        require_non_empty_str(self.step_id, "step_id")
        require_non_empty_str(self.decision_requested, "decision_requested")
        require_non_empty_str(self.why_policy_cannot_decide, "why_policy_cannot_decide")
        require_no_duplicates(self.options, "options")
        if not self.options:
            raise QcaeValidationError("escalation must present options")
        if not self.supporting_evidence_refs:
            raise QcaeValidationError("escalations are evidence-backed")
        require_non_empty_str(self.reversibility, "reversibility")
        require_non_empty_str(
            self.consequence_of_no_decision, "consequence_of_no_decision"
        )
        require_non_empty_str(self.created_at, "created_at")


@dataclass(frozen=True)
class EscalationDecision(SerializableRecord):
    SCHEMA_VERSION = 1

    decision_id: str
    escalation_ref: str
    state: EscalationState
    decided_by: str
    decided_at: str
    scope: str
    reason: str

    _COERCIONS = {"state": lambda v: coerce_enum(v, EscalationState)}

    def validate(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        require_identifier(self.escalation_ref, "escalation_ref")
        if self.state is EscalationState.OPEN:
            raise QcaeValidationError("a decision cannot leave an escalation OPEN")
        require_non_empty_str(self.decided_by, "decided_by")
        require_non_empty_str(self.decided_at, "decided_at")
        require_non_empty_str(self.scope, "scope")
        require_non_empty_str(self.reason, "reason")


__all__ = [
    "ApprovalState",
    "EscalationState",
    "EscalationTrigger",
    "ApprovalRequest",
    "ApprovalDecision",
    "EscalationRecord",
    "EscalationDecision",
]
