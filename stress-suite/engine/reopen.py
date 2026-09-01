"""G4-B — machine-readable reopen conditions + suppression decisions (S10/S11).

ReopenCondition is a PROVISIONAL test contract. Supported operators are a small
fixed vocabulary (EQ / NEQ / GTE / LTE / IN / EXISTS / BLOCKER_RESOLVED). No
eval(), no arbitrary executable expressions. Unknown condition type or operator
FAILS CLOSED at construction.

ReopenEvaluator decides ELIGIBILITY only: NO_REOPEN / REOPEN_CANDIDATE /
OPERATOR_REVIEW_REQUIRED / CONDITION_UNKNOWN. It never sets ACTIVE or PROMOTED —
reopening means eligible for renewed evaluation through the governed M4 path
(which itself forbids DORMANT->ACTIVE shortcuts).

NegativeKnowledgeSuppressionDecision: suppression influences search/retrieval
priority behavior; it never erases evidence, and it ends for the exact governed
scope when the reopen condition fires (unless the record is operator-permanent,
in which case the behavior stays OPERATOR_REVIEW_REQUIRED / explicit ambiguity).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

REOPEN_OPERATORS = ("EQ", "NEQ", "GTE", "LTE", "IN", "EXISTS", "BLOCKER_RESOLVED")
REOPEN_CONDITION_TYPES = ("FIELD_PREDICATE", "BLOCKER_RESOLVED", "EXISTS")
REOPEN_OUTCOMES = ("NO_REOPEN", "REOPEN_CANDIDATE", "OPERATOR_REVIEW_REQUIRED",
                   "CONDITION_UNKNOWN")

#: canonical blockers for BLOCKER_RESOLVED (a small PROVISIONAL vocabulary)
KNOWN_BLOCKERS = ("TIMESTAMP_LEAKAGE", "SURVIVORSHIP_BIAS", "LOOKAHEAD_LEAKAGE",
                  "SENSOR_UNAVAILABLE", "DATA_QUALITY", "GENERIC_BLOCKER")


class ReopenConditionError(ValueError):
    pass


@dataclass(frozen=True)
class ReopenCondition:
    condition_id: str
    condition_type: str = "FIELD_PREDICATE"
    subject_ref: str = ""
    field: str = ""
    operator: str = "EQ"
    expected_value: Any = None
    evidence_required: bool = False
    scope: str = ""
    created_under_contract: str = "G4_MEMORY_AND_REACTIVATION_POLICY:1.0.0"
    authority_basis_if_any: str = ""
    version_tag: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.condition_type not in REOPEN_CONDITION_TYPES:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: unknown condition_type "
                f"{self.condition_type!r}; canonical: {REOPEN_CONDITION_TYPES}")
        if self.operator not in REOPEN_OPERATORS:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: unknown operator "
                f"{self.operator!r}; canonical: {REOPEN_OPERATORS}")
        if self.condition_type == "BLOCKER_RESOLVED":
            if self.operator != "BLOCKER_RESOLVED":
                raise ReopenConditionError(
                    f"condition {self.condition_id!r}: BLOCKER_RESOLVED type "
                    f"requires operator BLOCKER_RESOLVED")
            if self.expected_value not in KNOWN_BLOCKERS:
                raise ReopenConditionError(
                    f"condition {self.condition_id!r}: unknown blocker "
                    f"{self.expected_value!r}; canonical: {KNOWN_BLOCKERS}")

    @classmethod
    def make(cls, seq, **kw) -> "ReopenCondition":
        cid = kw.pop("condition_id", None)
        return cls(condition_id=cid or deterministic_hex("reopen_cond", seq), **kw)

    # ------------------------------------------------------------------ #
    def evaluate(self, facts: Mapping[str, Any]) -> bool:
        """Deterministic evaluation against current observable facts. Unknown
        condition types/operators cannot exist (construction fails closed), so
        evaluation is always well-defined here."""
        if self.condition_type == "BLOCKER_RESOLVED":
            blocker = self.expected_value
            resolved = facts.get("resolved_blockers")
            if isinstance(resolved, (list, tuple, set)):
                return blocker in resolved
            # bool field form: {"resolved_blockers": {"BLOCKER": true}}
            if isinstance(resolved, dict):
                return bool(resolved.get(blocker, False))
            return False
        if self.condition_type == "EXISTS":
            return bool(facts.get(self.field) is not None and facts.get(self.field) != "")
        value = facts.get(self.field)
        if self.operator == "EQ":
            return value == self.expected_value
        if self.operator == "NEQ":
            return value != self.expected_value
        if self.operator == "GTE":
            return isinstance(value, (int, float)) and value >= self.expected_value
        if self.operator == "LTE":
            return isinstance(value, (int, float)) and value <= self.expected_value
        if self.operator == "IN":
            return value in (self.expected_value or [])
        if self.operator == "EXISTS":
            return value is not None and value != ""
        raise ReopenConditionError(f"unreachable: operator {self.operator!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {"condition_id": self.condition_id,
                "condition_type": self.condition_type,
                "subject_ref": self.subject_ref, "field": self.field,
                "operator": self.operator, "expected_value": self.expected_value,
                "evidence_required": self.evidence_required, "scope": self.scope,
                "created_under_contract": self.created_under_contract,
                "authority_basis_if_any": self.authority_basis_if_any,
                "version_tag": self.version_tag}


@dataclass(frozen=True)
class ReopenEvaluation:
    outcome: str
    condition_results: Tuple[Dict[str, Any], ...]
    rationale: str
    evidence_required_met: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"outcome": self.outcome, "condition_results": list(self.condition_results),
                "rationale": self.rationale,
                "evidence_required_met": self.evidence_required_met}


class ReopenEvaluator:
    """Eligibility-only reopen evaluation. Consumes knowledge object refs,
    NegativeKnowledge records, versioned reopen conditions, current observable
    facts and the current epoch. Returns NO_REOPEN / REOPEN_CANDIDATE /
    OPERATOR_REVIEW_REQUIRED / CONDITION_UNKNOWN. Never mutates M4 state."""

    def __init__(self, conditions: Optional[Sequence[ReopenCondition]] = None,
                 evidence_registry: Optional[Any] = None, current_epoch: str = ""):
        self.conditions = tuple(conditions or ())
        self.evidence_registry = evidence_registry
        self.current_epoch = current_epoch

    def evaluate(self, knowledge_id: str, facts: Mapping[str, Any],
                 conditions: Optional[Sequence[ReopenCondition]] = None,
                 negative_knowledge: Optional[Any] = None) -> ReopenEvaluation:
        conds = tuple(conditions or self.conditions)
        if not conds:
            return ReopenEvaluation(
                outcome="NO_REOPEN", condition_results=(), rationale="no reopen conditions supplied")
        results: List[Dict[str, Any]] = []
        any_true = False
        any_unknown = False
        evidence_available = bool(facts.get("evidence_refs")) or bool(facts.get("evidence"))
        for c in conds:
            try:
                ok = c.evaluate(facts)
            except ReopenConditionError:
                ok = False
                any_unknown = True
                results.append({"condition_id": c.condition_id, "evaluated": False,
                                "reason": "condition semantics unknown (version drift)"})
                continue
            if ok and c.evidence_required and not evidence_available:
                # S11 control 2: asserting a blocker is resolved WITHOUT evidence
                # must not reopen — the condition is not satisfied.
                results.append({"condition_id": c.condition_id, "evaluated": True,
                                "satisfied": False,
                                "reason": "condition satisfied but evidence_required and no evidence supplied",
                                "version_tag": c.version_tag})
                continue
            results.append({"condition_id": c.condition_id, "evaluated": True,
                            "satisfied": ok, "version_tag": c.version_tag})
            if ok:
                any_true = True
        evidence_required_met = evidence_available or not any(
            c.evidence_required for c in conds)
        # OPERATOR-permanent negative knowledge: ordinary reopen evidence must
        # NOT auto-reopen; revocation semantics are unspecified -> explicit
        # OPERATOR_REVIEW_REQUIRED (G4 §8 Control 3 / G4-P0-C ambiguity kept).
        if negative_knowledge is not None and getattr(negative_knowledge, "is_permanent", False):
            return ReopenEvaluation(
                outcome="OPERATOR_REVIEW_REQUIRED",
                condition_results=tuple(results),
                rationale="record is PERMANENT_BY_OPERATOR_AUTHORITY; ordinary reopen "
                          "evidence cannot auto-reopen; operator revocation is not "
                          "specified (ambiguity preserved)",
                evidence_required_met=evidence_required_met)
        if any_unknown and not any_true:
            return ReopenEvaluation(
                outcome="CONDITION_UNKNOWN",
                condition_results=tuple(results),
                rationale="at least one condition could not be evaluated under "
                          "current semantics; fail closed",
                evidence_required_met=False)
        if any_true:
            return ReopenEvaluation(
                outcome="REOPEN_CANDIDATE",
                condition_results=tuple(results),
                rationale="reopen condition satisfied: eligible for renewed "
                          "evaluation via the governed M4 path (not promotion)",
                evidence_required_met=evidence_required_met)
        return ReopenEvaluation(
            outcome="NO_REOPEN",
            condition_results=tuple(results),
            rationale="no reopen condition satisfied",
            evidence_required_met=False)


# --------------------------------------------------------------------------- #
# §9 — NegativeKnowledgeSuppressionDecision
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NegativeKnowledgeSuppressionDecision:
    record_id: str
    scope: str
    currently_suppressed: bool
    reason: str
    reopen_condition_status: str          # NOT_EVALUATED | SATISFIED | UNSATISFIED | OPERATOR_PERMANENT
    evidence_refs: Tuple[str, ...]
    permanent_operator_authority: Optional[str]
    next_action: str                      # CONTINUE_SUPPRESSION | STOP_SUPPRESSION | OPERATOR_REVIEW_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return {"record_id": self.record_id, "scope": self.scope,
                "currently_suppressed": self.currently_suppressed, "reason": self.reason,
                "reopen_condition_status": self.reopen_condition_status,
                "evidence_refs": list(self.evidence_refs),
                "permanent_operator_authority": self.permanent_operator_authority,
                "next_action": self.next_action}


def decide_suppression(
    negative_knowledge: Any,
    evaluator: ReopenEvaluator,
    facts: Mapping[str, Any],
    conditions: Optional[Sequence[ReopenCondition]] = None,
) -> NegativeKnowledgeSuppressionDecision:
    """Suppression is a retrieval/priority behavior, never deletion. Reopen
    stops suppression for the exact governed scope when the condition fires —
    unless the record is operator-permanent (then operator review is required
    and the ambiguity stays explicit)."""
    ev = evaluator.evaluate(negative_knowledge.record_id, facts,
                            conditions=conditions, negative_knowledge=negative_knowledge)
    permanent = getattr(negative_knowledge, "permanent_by_operator_authority", None)
    if permanent:
        return NegativeKnowledgeSuppressionDecision(
            record_id=negative_knowledge.record_id,
            scope=negative_knowledge.exact_scope,
            currently_suppressed=True,
            reason="PERMANENT_BY_OPERATOR_AUTHORITY; ordinary reopen evidence cannot "
                   "auto-reopen (revocation unspecified)",
            reopen_condition_status="OPERATOR_PERMANENT",
            evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
            permanent_operator_authority=permanent,
            next_action="OPERATOR_REVIEW_REQUIRED")
    if ev.outcome == "REOPEN_CANDIDATE":
        return NegativeKnowledgeSuppressionDecision(
            record_id=negative_knowledge.record_id,
            scope=negative_knowledge.exact_scope,
            currently_suppressed=False,
            reason="reopen condition satisfied for this exact scope; suppression "
                   "ceases, record retained",
            reopen_condition_status="SATISFIED",
            evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
            permanent_operator_authority=None,
            next_action="STOP_SUPPRESSION")
    if ev.outcome == "CONDITION_UNKNOWN":
        return NegativeKnowledgeSuppressionDecision(
            record_id=negative_knowledge.record_id,
            scope=negative_knowledge.exact_scope,
            currently_suppressed=True,
            reason="reopen condition semantics unknown; fail closed to suppression",
            reopen_condition_status="UNKNOWN",
            evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
            permanent_operator_authority=None,
            next_action="CONTINUE_SUPPRESSION")
    return NegativeKnowledgeSuppressionDecision(
        record_id=negative_knowledge.record_id,
        scope=negative_knowledge.exact_scope,
        currently_suppressed=True,
        reason="reopen condition not satisfied",
        reopen_condition_status="UNSATISFIED",
        evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
        permanent_operator_authority=None,
        next_action="CONTINUE_SUPPRESSION")
