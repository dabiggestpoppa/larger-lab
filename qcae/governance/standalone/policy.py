"""Local policy engine (P2-C04; Book V 13.2, ADR-0009).

Policy-as-data: versioned, deterministic, auditable rule sets. The engine
evaluates (principal, action, resource, scope, classification, budget, risk)
against ordered rules and returns exactly one of:

    ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS

Fail-closed law (Book V 13.2 invariant 4): an unknown/ambiguous condition or
no matching rule produces DENY, never implicit permission. Workers cannot
modify policy (13.2 invariant 5) — the engine has no mutation API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List, Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = [
    "PolicyDecisionType",
    "PolicyEffect",
    "PolicyRule",
    "PolicySet",
    "PolicyRequest",
    "PolicyDecision",
    "LocalPolicyEngine",
]


class PolicyDecisionType(StrEnum):
    """Book V 13.2 decision vocabulary."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ALLOW_WITH_CONSTRAINTS = "ALLOW_WITH_CONSTRAINTS"


class PolicyEffect(StrEnum):
    """Rule-level effect; maps onto decision types."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ALLOW_WITH_CONSTRAINTS = "ALLOW_WITH_CONSTRAINTS"


@dataclass(frozen=True)
class PolicyRule(SerializableRecord):
    """One declarative rule. First-match-wins in declared order."""

    SCHEMA_VERSION = 1

    rule_id: str
    effect: PolicyEffect
    action: str  # PolicyAction value or future OCE action; open string at
    # this layer so P3+ can register domain actions through versioned policy.

    principal_match: str = "*"  # exact id or "*"
    resource_match: str = "*"  # exact id/prefix or "*"
    classification_match: str = "*"  # data/risk class or "*"

    constraints: Tuple[str, ...] = ()
    reason: str = ""

    _COERCIONS = {"effect": lambda v: coerce_enum(v, PolicyEffect)}

    def validate(self) -> None:
        require_identifier(self.rule_id, "rule_id")
        if not isinstance(self.effect, PolicyEffect):
            raise QcaeValidationError(
                f"effect must be a PolicyEffect member, got {self.effect!r}"
            )
        require_non_empty_str(self.action, "action")
        for m in (self.principal_match, self.resource_match, self.classification_match):
            if not isinstance(m, str) or not m:
                raise QcaeValidationError("rule matchers must be non-empty strings")
        if self.effect is not PolicyEffect.DENY and not self.reason:
            raise QcaeValidationError("non-deny rules must record their reason")
        for c in self.constraints:
            require_non_empty_str(c, "constraint")


@dataclass(frozen=True)
class PolicySet(SerializableRecord):
    """Versioned, ordered rule set (policy-as-data)."""

    SCHEMA_VERSION = 1

    policy_id: str
    policy_version: str
    rules: Tuple[PolicyRule, ...] = ()

    _NESTED_RECORDS = {"rules": PolicyRule}

    def validate(self) -> None:
        require_identifier(self.policy_id, "policy_id")
        require_non_empty_str(self.policy_version, "policy_version")
        ids = [r.rule_id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise QcaeValidationError("duplicate rule_id in policy set")
        for r in self.rules:
            r.validate()


@dataclass(frozen=True)
class PolicyRequest(SerializableRecord):
    """One bounded authority question (Book V 13.2 policy inputs)."""

    SCHEMA_VERSION = 1

    principal: str
    action: str
    resource: str = "*"
    scope: str = ""
    classification: str = ""
    environment: str = "local"
    budget_ref: str = ""
    risk_class: str = ""

    def validate(self) -> None:
        require_non_empty_str(self.principal, "principal")
        require_non_empty_str_strict(self.action, "action")
        if not isinstance(self.resource, str):
            raise QcaeValidationError("resource must be a string")


def require_non_empty_str_strict(value, what):
    if not isinstance(value, str) or not value.strip():
        raise QcaeValidationError(f"{what} must be a non-empty string")


@dataclass(frozen=True)
class PolicyDecision(SerializableRecord):
    """Structured decision record (P2 directive §10; Book V 13.2)."""

    SCHEMA_VERSION = 1

    decision_id: str
    decision: PolicyDecisionType
    principal: str
    action: str
    resource: str
    policy_id: str
    policy_version: str
    rule_ref: str  # matched rule id, or "FAIL_CLOSED" / "NO_MATCH"
    reason: str
    constraints: Tuple[str, ...] = ()
    scope: str = ""
    created_at: str = ""
    expires_at: str = ""
    evidence_refs: Tuple[str, ...] = ()

    _COERCIONS = {"decision": lambda v: coerce_enum(v, PolicyDecisionType)}

    def validate(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        if not isinstance(self.decision, PolicyDecisionType):
            raise QcaeValidationError(
                f"decision must be a PolicyDecisionType member, got {self.decision!r}"
            )
        require_non_empty_str(self.principal, "principal")
        require_non_empty_str_strict(self.action, "action")
        require_non_empty_str(self.resource, "resource")
        require_non_empty_str(self.policy_id, "policy_id")
        require_non_empty_str(self.policy_version, "policy_version")
        require_non_empty_str(self.rule_ref, "rule_ref")
        require_non_empty_str(self.created_at, "created_at")
        if self.decision is PolicyDecisionType.ALLOW_WITH_CONSTRAINTS and not self.constraints:
            raise QcaeValidationError(
                "ALLOW_WITH_CONSTRAINTS must carry at least one constraint"
            )
        if self.decision is PolicyDecisionType.DENY and self.constraints:
            raise QcaeValidationError("DENY cannot carry constraints")


def _matches(pattern: str, value: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("*") and value.startswith(pattern[:-1]):
        return True
    return pattern == value


class LocalPolicyEngine:
    """Deterministic first-match-wins evaluator; fail closed."""

    def __init__(self, policy_set: PolicySet) -> None:
        policy_set.validate()
        self._policy = policy_set

    @property
    def policy(self) -> PolicySet:
        return self._policy

    def evaluate(self, request: PolicyRequest, *, decision_id: str, created_at: str) -> PolicyDecision:
        request.validate()
        for rule in self._policy.rules:
            # Action matching uses the same discipline as the other matchers
            # (exact, prefix-star, or '*'). An earlier exact-only comparison
            # silently made action wildcards unusable; P2-R2-C01 derives
            # baseline actions (execute.<step_type>) that versioned policies
            # declare with prefix rules.
            if not _matches(rule.action, request.action):
                continue
            if not _matches(rule.principal_match, request.principal):
                continue
            if not _matches(rule.resource_match, request.resource):
                continue
            if not _matches(rule.classification_match, request.classification):
                continue
            return self._decision_from(rule, request, decision_id, created_at)
        # No matching rule -> fail closed (Book V 13.2 invariant 4).
        return PolicyDecision(
            decision_id=decision_id,
            decision=PolicyDecisionType.DENY,
            principal=request.principal,
            action=request.action,
            resource=request.resource,
            policy_id=self._policy.policy_id,
            policy_version=self._policy.policy_version,
            rule_ref="NO_MATCH",
            reason="no policy rule matched this request; failing closed",
            scope=request.scope,
            created_at=created_at,
        )

    def _decision_from(
        self, rule: PolicyRule, request: PolicyRequest, decision_id: str, created_at: str
    ) -> PolicyDecision:
        return PolicyDecision(
            decision_id=decision_id,
            decision=PolicyDecisionType(rule.effect.value),
            principal=request.principal,
            action=request.action,
            resource=request.resource,
            policy_id=self._policy.policy_id,
            policy_version=self._policy.policy_version,
            rule_ref=rule.rule_id,
            reason=rule.reason,
            constraints=rule.constraints,
            scope=request.scope,
            created_at=created_at,
        )
