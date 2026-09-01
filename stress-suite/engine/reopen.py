"""G4-B/G4R — machine-readable reopen conditions + suppression decisions (S10/S11).

ReopenCondition is a PROVISIONAL test contract. Supported operators are a small
fixed vocabulary (EQ / NEQ / GTE / LTE / IN / EXISTS / BLOCKER_RESOLVED). No
eval(), no arbitrary executable expressions. Unknown condition type / operator /
group operator / scope-match mode FAILS CLOSED at construction.

G4R-02/03/04 — binding semantics:
  * SUBJECT binding: an OBJECT_SPECIFIC condition (the default) applies ONLY to
    the knowledge object whose id equals condition.subject_ref. A condition
    targeting KNOWLEDGE_A can never reopen KNOWLEDGE_B. A blank subject_ref in
    an object-specific condition fails closed (subject_unbound). A condition
    that should apply broadly must declare subject_scope="GLOBAL" explicitly.
  * SCOPE binding: when the evaluated record carries a scope (negative
    knowledge exact_scope), a condition with a non-empty scope must match it
    under the condition's declared scope_match_mode (EXACT by default; PREFIX /
    WILDCARD only when explicitly requested and versioned). Cross-domain scope
    fails closed.
  * COMBINATION semantics: conditions sharing a group_id are combined with the
    group's explicit operator (ANY | ALL). Conditions without a group are
    independent (any satisfied condition reopens). Unknown combination
    operators fail closed. Order of conditions never changes the result.

G4R-05/06 — evidence-backed reopen:
  * A condition with evidence_required=true must cite SPECIFIC evidence ids
    (condition.evidence_refs). Each required ref must exist and resolve in the
    governed evidence registry; phantom refs FAIL CLOSED. Evidence that
    supports another condition cannot satisfy this one. Empty evidence_refs on
    an evidence_required condition fails closed (no generic "any evidence").
  * BLOCKER_RESOLVED with evidence_required=true additionally requires a
    BlockerResolutionRecord in the current facts whose evidence refs resolve;
    a bare resolved_blockers claim (or an unsupported agent assertion) cannot
    reopen negative knowledge.

ReopenEvaluator decides ELIGIBILITY only: NO_REOPEN / REOPEN_CANDIDATE /
OPERATOR_REVIEW_REQUIRED / CONDITION_UNKNOWN. It never sets ACTIVE or PROMOTED —
reopening means eligible for renewed evaluation through the governed M4 path
(which itself forbids DORMANT->ACTIVE shortcuts).

The shared G4_MEMORY_AND_REACTIVATION_POLICY decides the institutional
disposition from the evaluator's factual condition state (see g4_runner).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

REOPEN_OPERATORS = ("EQ", "NEQ", "GTE", "LTE", "IN", "EXISTS", "BLOCKER_RESOLVED")
REOPEN_CONDITION_TYPES = ("FIELD_PREDICATE", "BLOCKER_RESOLVED", "EXISTS")
REOPEN_OUTCOMES = ("NO_REOPEN", "REOPEN_CANDIDATE", "OPERATOR_REVIEW_REQUIRED",
                   "CONDITION_UNKNOWN")
REOPEN_GROUP_OPERATORS = ("ANY", "ALL")
SCOPE_MATCH_MODES = ("EXACT", "PREFIX", "WILDCARD")
SUBJECT_SCOPES = ("OBJECT_SPECIFIC", "GLOBAL")

#: canonical blockers for BLOCKER_RESOLVED (a small PROVISIONAL vocabulary)
KNOWN_BLOCKERS = ("TIMESTAMP_LEAKAGE", "SURVIVORSHIP_BIAS", "LOOKAHEAD_LEAKAGE",
                  "SENSOR_UNAVAILABLE", "DATA_QUALITY", "GENERIC_BLOCKER")


class ReopenConditionError(ValueError):
    pass


def _norm_tuples(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


@dataclass(frozen=True)
class BlockerResolutionRecord:
    """G4R-06 — an attributable, evidence-backed blocker resolution. A caller
    asserting `resolved_blockers = [...]` without a record + admissible
    evidence cannot reopen negative knowledge."""

    resolution_id: str
    blocker: str
    subject: str = ""
    scope: str = ""
    evidence_refs: Tuple[str, ...] = ()
    resolution_method: str = ""
    provenance: str = ""
    contract_version: str = "1.0.0"

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "BlockerResolutionRecord":
        return cls(
            resolution_id=str(data.get("resolution_id", "")),
            blocker=str(data.get("blocker", "")),
            subject=str(data.get("subject", "")),
            scope=str(data.get("scope", "")),
            evidence_refs=_norm_tuples(data.get("evidence_refs")),
            resolution_method=str(data.get("resolution_method", "")),
            provenance=str(data.get("provenance", "")),
            contract_version=str(data.get("contract_version", "1.0.0")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"resolution_id": self.resolution_id, "blocker": self.blocker,
                "subject": self.subject, "scope": self.scope,
                "evidence_refs": list(self.evidence_refs),
                "resolution_method": self.resolution_method,
                "provenance": self.provenance, "contract_version": self.contract_version}


@dataclass(frozen=True)
class ReopenCondition:
    condition_id: str
    condition_type: str = "FIELD_PREDICATE"
    subject_ref: str = ""
    field: str = ""
    operator: str = "EQ"
    expected_value: Any = None
    evidence_required: bool = False
    evidence_refs: Tuple[str, ...] = ()            # G4R-05: SPECIFIC evidence ids
    scope: str = ""
    scope_match_mode: str = "EXACT"                # G4R-03
    subject_scope: str = "OBJECT_SPECIFIC"         # G4R-02 explicit marker
    group_id: str = ""                             # G4R-04
    group_operator: str = ""                       # G4R-04: "" | ANY | ALL
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
        if self.subject_scope not in SUBJECT_SCOPES:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: unknown subject_scope "
                f"{self.subject_scope!r}; canonical: {SUBJECT_SCOPES}")
        if self.scope_match_mode not in SCOPE_MATCH_MODES:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: unknown scope_match_mode "
                f"{self.scope_match_mode!r}; canonical: {SCOPE_MATCH_MODES}")
        if self.group_operator and self.group_operator not in REOPEN_GROUP_OPERATORS:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: unknown group_operator "
                f"{self.group_operator!r}; canonical: {REOPEN_GROUP_OPERATORS}")
        if self.group_id and not self.group_operator:
            raise ReopenConditionError(
                f"condition {self.condition_id!r}: group_id requires an explicit "
                f"group_operator (ANY|ALL)")
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
        evidence_refs = kw.pop("evidence_refs", None)
        return cls(condition_id=cid or deterministic_hex("reopen_cond", seq),
                   evidence_refs=_norm_tuples(evidence_refs), **kw)

    # ------------------------------------------------------------------ #
    def evaluate(self, facts: Mapping[str, Any]) -> bool:
        """Deterministic evaluation of the PREDICATE against current observable
        facts. Unknown condition types/operators cannot exist (construction
        fails closed), so evaluation is always well-defined here."""
        if self.condition_type == "BLOCKER_RESOLVED":
            blocker = self.expected_value
            resolved = facts.get("resolved_blockers")
            if isinstance(resolved, (list, tuple, set)):
                return blocker in resolved
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

    # ------------------------------------------------------------------ #
    # G4R-02/03 binding
    # ------------------------------------------------------------------ #
    def applies_to(self, knowledge_id: str) -> Tuple[bool, Optional[str]]:
        """Exact subject binding. OBJECT_SPECIFIC conditions apply only to the
        object named by subject_ref; blank subject_ref fails closed. GLOBAL
        requires the explicit subject_scope marker."""
        if self.subject_scope == "GLOBAL":
            return True, None
        if self.subject_ref == knowledge_id:
            return True, None
        if not self.subject_ref:
            return False, "subject_unbound"
        return False, "subject_mismatch"

    def scope_ok(self, record_scope: str) -> Tuple[bool, Optional[str]]:
        """Exact scope binding (G4R-03). A condition without a declared scope is
        scope-unbound for scoped records: fail closed (the condition must state
        the governed scope it covers). Unscoped evaluations skip this check."""
        if not record_scope:
            return True, None
        if not self.scope:
            return False, "scope_unbound"
        if self.scope_match_mode == "EXACT":
            ok = self.scope == record_scope
            return ok, (None if ok else "scope_mismatch")
        if self.scope_match_mode == "PREFIX":
            ok = record_scope == self.scope or record_scope.startswith(self.scope.rstrip("/") + "/")
            return ok, None
        if self.scope_match_mode == "WILDCARD":
            if self.scope.endswith("*"):
                return record_scope.startswith(self.scope[:-1]), None
            return self.scope == record_scope, None
        return False, "unknown_scope_mode"

    def to_dict(self) -> Dict[str, Any]:
        return {"condition_id": self.condition_id,
                "condition_type": self.condition_type,
                "subject_ref": self.subject_ref, "field": self.field,
                "operator": self.operator, "expected_value": self.expected_value,
                "evidence_required": self.evidence_required,
                "evidence_refs": list(self.evidence_refs), "scope": self.scope,
                "scope_match_mode": self.scope_match_mode,
                "subject_scope": self.subject_scope,
                "group_id": self.group_id, "group_operator": self.group_operator,
                "created_under_contract": self.created_under_contract,
                "authority_basis_if_any": self.authority_basis_if_any,
                "version_tag": self.version_tag}


@dataclass(frozen=True)
class ReopenEvaluation:
    outcome: str
    condition_results: Tuple[Dict[str, Any], ...]
    rationale: str
    evidence_required_met: bool = False
    conflicts: Tuple[Dict[str, Any], ...] = ()     # G4R-21: binding/evidence conflicts

    def to_dict(self) -> Dict[str, Any]:
        return {"outcome": self.outcome, "condition_results": list(self.condition_results),
                "rationale": self.rationale,
                "evidence_required_met": self.evidence_required_met,
                "conflicts": list(self.conflicts)}


class ReopenEvaluator:
    """Eligibility-only reopen evaluation. Consumes knowledge object refs,
    NegativeKnowledge records, versioned reopen conditions, current observable
    facts, a governed evidence registry and the current epoch. Returns
    NO_REOPEN / REOPEN_CANDIDATE / OPERATOR_REVIEW_REQUIRED / CONDITION_UNKNOWN.
    Never mutates M4 state."""

    def __init__(self, conditions: Optional[Sequence[ReopenCondition]] = None,
                 evidence_registry: Optional[Any] = None, current_epoch: str = ""):
        self.conditions = tuple(conditions or ())
        self.evidence_registry = evidence_registry
        self.current_epoch = current_epoch

    # ------------------------------------------------------------------ #
    def _evidence_ok(self, c: ReopenCondition, facts: Mapping[str, Any],
                     record_scope: str) -> Tuple[bool, Optional[str], List[str]]:
        """G4R-05: an evidence_required condition must cite SPECIFIC evidence
        ids; each must resolve in the governed registry (phantom -> fail
        closed) and be admissible for the condition type. Returns
        (ok, failure_reason, conflict_refs)."""
        if not c.evidence_required:
            return True, None, []
        if not c.evidence_refs:
            return False, "evidence_refs_empty", []
        supplied = {str(r) for r in (facts.get("evidence_refs") or [])}
        missing = [r for r in c.evidence_refs if r not in supplied]
        if missing:
            return False, "evidence_missing", missing
        phantom: List[str] = []
        inadmissible: List[str] = []
        for ref in c.evidence_refs:
            if self.evidence_registry is None:
                continue
            if not self.evidence_registry.has(ref):
                phantom.append(ref)
                continue
            obj = self.evidence_registry.resolve(ref)
            kind = getattr(obj, "kind", "")
            # a bare agent self-assertion can never prove blocker resolution
            if c.condition_type == "BLOCKER_RESOLVED" and kind == "AGENT_CLAIM":
                inadmissible.append(ref)
        if phantom:
            return False, "evidence_phantom", phantom
        if inadmissible:
            return False, "evidence_not_admissible", inadmissible
        return True, None, []

    def _blocker_ok(self, c: ReopenCondition, facts: Mapping[str, Any],
                    record_scope: str) -> Tuple[bool, Optional[str], List[str]]:
        """G4R-06: BLOCKER_RESOLVED with evidence_required must be backed by a
        BlockerResolutionRecord whose evidence refs resolve; a bare claim or an
        unsupported agent assertion cannot reopen."""
        if c.condition_type != "BLOCKER_RESOLVED" or not c.evidence_required:
            return True, None, []
        recs = facts.get("blocker_resolutions") or []
        rec = next((r for r in recs if r.get("blocker") == c.expected_value), None)
        if rec is None:
            return False, "blocker_resolution_record_missing", []
        if rec.get("subject") and c.subject_ref and rec["subject"] != c.subject_ref:
            return False, "blocker_resolution_subject_mismatch", []
        if rec.get("scope") and record_scope and rec["scope"] != record_scope:
            return False, "blocker_resolution_scope_mismatch", []
        phantom: List[str] = []
        for ref in rec.get("evidence_refs") or []:
            if self.evidence_registry is not None and not self.evidence_registry.has(ref):
                phantom.append(ref)
        if phantom:
            return False, "blocker_resolution_evidence_phantom", phantom
        return True, None, []

    # ------------------------------------------------------------------ #
    def evaluate(self, knowledge_id: str, facts: Mapping[str, Any],
                 conditions: Optional[Sequence[ReopenCondition]] = None,
                 negative_knowledge: Optional[Any] = None,
                 record_scope: str = "") -> ReopenEvaluation:
        conds = tuple(conditions or self.conditions)
        conflicts: List[Dict[str, Any]] = []
        if not conds:
            return ReopenEvaluation(
                outcome="NO_REOPEN", condition_results=(), rationale="no reopen conditions supplied",
                conflicts=())
        results: List[Dict[str, Any]] = []
        any_true = False
        any_unknown = False
        evidence_available = bool(facts.get("evidence_refs")) or bool(facts.get("evidence"))
        evidence_ok_flags: List[bool] = []
        for c in conds:
            applied, reason = c.applies_to(knowledge_id)
            if not applied:
                conflicts.append({"axis": "subject_ref", "claimed": c.subject_ref,
                                  "registered": knowledge_id if reason == "subject_mismatch" else "<unbound>",
                                  "disposition": reason})
                results.append({"condition_id": c.condition_id, "applied": False,
                                "satisfied": False, "reason": reason,
                                "version_tag": c.version_tag})
                evidence_ok_flags.append(False)
                continue
            if record_scope:
                scope_ok, scope_reason = c.scope_ok(record_scope)
                if not scope_ok:
                    conflicts.append({"axis": "scope", "claimed": c.scope or "<unbound>",
                                      "registered": record_scope, "disposition": scope_reason})
                    results.append({"condition_id": c.condition_id, "applied": True,
                                    "satisfied": False, "reason": scope_reason,
                                    "version_tag": c.version_tag})
                    evidence_ok_flags.append(False)
                    continue
            try:
                ok = c.evaluate(facts)
            except ReopenConditionError:
                ok = False
                any_unknown = True
                results.append({"condition_id": c.condition_id, "evaluated": False,
                                "satisfied": False,
                                "reason": "condition semantics unknown (version drift)"})
                evidence_ok_flags.append(False)
                continue
            evidence_ok, ev_failure, ev_conflicts = self._evidence_ok(c, facts, record_scope)
            blocker_ok, bl_failure, bl_conflicts = self._blocker_ok(c, facts, record_scope)
            for axis, refs in (("evidence_ref", ev_conflicts), ("blocker_evidence_ref", bl_conflicts)):
                for ref in refs:
                    conflicts.append({"axis": axis, "claimed": ref,
                                      "registered": "<not registered>", "disposition": "phantom"})
            ev_ok = evidence_ok and blocker_ok
            if ok and c.evidence_required and not ev_ok:
                # evidence-backed conditions that evaluate true but lack bound
                # evidence do NOT satisfy (S11 control 2).
                fail = ev_failure or bl_failure or "evidence"
                conflicts.append({"axis": "evidence_binding", "claimed": "evidence claimed",
                                  "registered": f"<{fail}>", "disposition": fail})
                results.append({"condition_id": c.condition_id, "applied": True,
                                "evaluated": True, "satisfied": False,
                                "reason": f"condition satisfied but evidence not bound: {fail}",
                                "version_tag": c.version_tag,
                                "evidence_refs": list(c.evidence_refs)})
                evidence_ok_flags.append(False)
                continue
            results.append({"condition_id": c.condition_id, "applied": True,
                            "evaluated": True, "satisfied": ok,
                            "scope_match": c.scope, "version_tag": c.version_tag,
                            "evidence_refs": list(c.evidence_refs)})
            evidence_ok_flags.append(True)
            if ok:
                any_true = True

        # G4R-04 — ANY/ALL group combination (order independent)
        group_results: Dict[str, List[Dict[str, Any]]] = {}
        group_ops: Dict[str, str] = {}
        for c, r in zip(conds, results):
            if c.group_id:
                group_results.setdefault(c.group_id, []).append(r)
                group_ops.setdefault(c.group_id, c.group_operator)
        group_ok: Dict[str, bool] = {}
        for gid, rs in group_results.items():
            op = group_ops[gid]
            if op == "ALL":
                group_ok[gid] = bool(rs) and all(r.get("satisfied") is True for r in rs)
            elif op == "ANY":
                group_ok[gid] = any(r.get("satisfied") is True for r in rs)
            else:
                group_ok[gid] = False
        satisfied_group = any(group_ok.values())
        satisfied_standalone = any(
            r.get("satisfied") is True for c, r in zip(conds, results) if not c.group_id)
        any_true = satisfied_group or satisfied_standalone

        evidence_required_met = evidence_available or not any(
            c.evidence_required for c in conds)
        if negative_knowledge is not None and getattr(negative_knowledge, "is_permanent", False):
            return ReopenEvaluation(
                outcome="OPERATOR_REVIEW_REQUIRED",
                condition_results=tuple(results),
                rationale="record is PERMANENT_BY_OPERATOR_AUTHORITY; ordinary reopen "
                          "evidence cannot auto-reopen; operator revocation is not "
                          "specified (ambiguity preserved)",
                evidence_required_met=evidence_required_met,
                conflicts=tuple(conflicts))
        if any_unknown and not any_true:
            return ReopenEvaluation(
                outcome="CONDITION_UNKNOWN",
                condition_results=tuple(results),
                rationale="at least one condition could not be evaluated under "
                          "current semantics; fail closed",
                evidence_required_met=False, conflicts=tuple(conflicts))
        if any_true:
            return ReopenEvaluation(
                outcome="REOPEN_CANDIDATE",
                condition_results=tuple(results),
                rationale="reopen condition satisfied: eligible for renewed "
                          "evaluation via the governed M4 path (not promotion)",
                evidence_required_met=evidence_required_met,
                conflicts=tuple(conflicts))
        return ReopenEvaluation(
            outcome="NO_REOPEN",
            condition_results=tuple(results),
            rationale="no reopen condition satisfied",
            evidence_required_met=False, conflicts=tuple(conflicts))


def reopen_condition_state(ev: ReopenEvaluation) -> str:
    """Factual condition state for the shared memory policy: SATISFIED /
    UNSATISFIED / UNKNOWN / OPERATOR_PERMANENT."""
    if ev.outcome == "REOPEN_CANDIDATE":
        return "SATISFIED"
    if ev.outcome == "CONDITION_UNKNOWN":
        return "UNKNOWN"
    if ev.outcome == "OPERATOR_REVIEW_REQUIRED":
        return "OPERATOR_PERMANENT"
    return "UNSATISFIED"


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


def _policy_next_action(policy, facts: Mapping[str, Any]) -> Optional[str]:
    """Resolve the shared memory policy's suppression disposition; None when no
    rule applies (the caller then keeps the fail-closed default)."""
    if policy is None:
        return None
    rule = policy.evaluate(facts, "suppression")
    if rule is None:
        return None
    return rule.then.get("next_action")


def decide_suppression(
    negative_knowledge: Any,
    evaluator: ReopenEvaluator,
    facts: Mapping[str, Any],
    conditions: Optional[Sequence[ReopenCondition]] = None,
    policy: Optional[Any] = None,
) -> NegativeKnowledgeSuppressionDecision:
    """Suppression is a retrieval/priority behavior, never deletion. Reopen
    stops suppression for the exact governed scope when the condition fires —
    unless the record is operator-permanent (then operator review is required
    and the ambiguity stays explicit). When a shared memory policy is supplied
    its suppression rule decides next_action (G4R-01)."""
    ev = evaluator.evaluate(negative_knowledge.record_id, facts,
                            conditions=conditions, negative_knowledge=negative_knowledge,
                            record_scope=negative_knowledge.exact_scope)
    permanent = negative_knowledge.is_permanent if hasattr(negative_knowledge, "is_permanent") \
        else bool(getattr(negative_knowledge, "permanent_by_operator_authority", None))
    facts_for_policy = {
        "reopen_condition_state": reopen_condition_state(ev),
        "suppression_state": "SUPPRESSED",
        "permanent_operator_authority": bool(permanent),
        "lifecycle_state": getattr(negative_knowledge, "current_lifecycle_state", "DEMOTED"),
    }
    policy_action = _policy_next_action(policy, facts_for_policy)
    if permanent:
        return NegativeKnowledgeSuppressionDecision(
            record_id=negative_knowledge.record_id,
            scope=negative_knowledge.exact_scope,
            currently_suppressed=True,
            reason="PERMANENT_BY_OPERATOR_AUTHORITY; ordinary reopen evidence cannot "
                   "auto-reopen (revocation unspecified)",
            reopen_condition_status="OPERATOR_PERMANENT",
            evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
            permanent_operator_authority=getattr(negative_knowledge,
                                                 "permanent_by_operator_authority", None),
            next_action="OPERATOR_REVIEW_REQUIRED")
    if ev.outcome == "REOPEN_CANDIDATE":
        action = policy_action or "STOP_SUPPRESSION"
        return NegativeKnowledgeSuppressionDecision(
            record_id=negative_knowledge.record_id,
            scope=negative_knowledge.exact_scope,
            currently_suppressed=action != "STOP_SUPPRESSION",
            reason="reopen condition satisfied for this exact scope; suppression "
                   "ceases, record retained",
            reopen_condition_status="SATISFIED",
            evidence_refs=tuple(negative_knowledge.evidence_refs or ()),
            permanent_operator_authority=None,
            next_action=action)
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
