"""G6 — constitutional-attack governance scenarios S20–S24 (deterministic).

G6 EXTERNAL-REVIEW HARDENED (G6-ER01..ER07). Supersedes, with evidence, the
first-draft G6 semantics where vocabulary was stronger than what was verified:

  ER01  a top-level MappingProxyType is NOT deep immutability — the entire
        criteria tree is deep-frozen into immutable structures; nested mutation
        is structurally impossible and caller-retained aliases are severed at
        freeze time (every container is rebuilt).
  ER02  FUTURE_VERSION_ADOPTED let a Governor change its own evaluation law by
        targeting a future window. A rule change is now a
        FUTURE_VERSION_CANDIDATE only; activation/ratification goes through the
        CANONICAL authority engine (propose -> ratify; no self-ratification).
  ER03  G6 no longer defines a second authority ontology. S21 uses
        engine/authority.py (AuthorityState / AuthorityRegistry / CapabilityGrant
        / risk classes / prior-proposal / self-ratification guards).
  ER04  GOVERNOR is not silently OPERATOR. Operator action authorization needs a
        governed mandate + an explicit constitutional permission record (a bare
        boolean cannot mint permission). Evidence grades change ONLY through a
        registered evidence ref; operator desire has no vote in either
        direction (weak evidence is not improved by desire; strong contradictory
        evidence is not suppressed by incumbent preference).
  ER05  S23 compares the ACTUAL requested action envelope (action, scope,
        surface, reversibility, canonical risk class, environment) against the
        GRANTED envelope — safe grant metadata cannot hide riskier actual
        actions — and proves the grant PRE-EXISTS the operator-unavailable
        decision (issued_seq < decision seq).
  ER06  S24 classification no longer treats raw_event keywords as governance
        truth. A channel is used only when structured, evidence-backed
        classification evidence supports exactly one channel; otherwise the
        event stays UNRESOLVED_GOVERNANCE_EVENT (raw token hits are recorded as
        observation only, never as decision input).
  ER07  CON-02 allocator provenance is observable: every consequential evidence
        path can record initiating actor / allocator / selected worker /
        source-retrieval path / exposure lineage, and the harness can detect
        ALLOCATOR_CONCENTRATION (all apparently independent paths through one
        allocator). Observability only — no constitutional rule changes.

Nothing here mutates production/cloud/capital, calls a model, or depends on
wall clock. All identifiers derive from content (deterministic_hex).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .authority import (
    AUTHORITY_BEARING_RISK_CLASSES,
    AuthorityState,
    AuthorityViolation,
    CapabilityGrant,
    RISK_CLASSES,
)
from .base import deterministic_hex
from .registry import EvidenceRegistry

# --------------------------------------------------------------------------- #
# ER01 — deep-freeze primitives (structural, not convention)
# --------------------------------------------------------------------------- #
class _FrozenMapping(Mapping):
    """An immutable mapping. Mutation raises; nested values are already frozen."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_data",
                           {str(k): _deep_freeze(v) for k, v in dict(data).items()})

    def __getitem__(self, key: Any) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError("FrozenMapping is immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("FrozenMapping is immutable")

    def __repr__(self) -> str:
        return f"FrozenMapping({self._data!r})"


class _FrozenSequence(Sequence):
    """An immutable sequence. No mutation methods exist; items are frozen."""

    __slots__ = ("_items",)

    def __init__(self, items: Iterable[Any]) -> None:
        object.__setattr__(self, "_items", tuple(_deep_freeze(v) for v in items))

    def __getitem__(self, index: Any) -> Any:
        return self._items[index]

    def __len__(self) -> int:
        return len(self._items)

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError("FrozenSequence is immutable")

    def __repr__(self) -> str:
        return f"FrozenSequence({self._items!r})"


_IMMUTABLE_SCALARS = (str, int, float, bool, type(None), frozenset)


def _deep_freeze(value: Any) -> Any:
    """Convert a plain structure into a fully immutable tree. Every container is
    REBUILT, so any alias the caller retained now points at the old mutable
    object and cannot reach into the frozen one. Unknown container types fail
    closed rather than being stored unfrozen."""
    if isinstance(value, _FrozenMapping) or isinstance(value, _FrozenSequence):
        return value
    if isinstance(value, dict):
        return _FrozenMapping(value)
    if isinstance(value, (list, tuple)):
        return _FrozenSequence(value)
    if isinstance(value, set):
        return frozenset(value)
    if isinstance(value, _IMMUTABLE_SCALARS):
        return value
    raise TypeError(
        f"cannot deep-freeze value of type {type(value).__name__!r}; "
        f"criteria trees must be JSON-like (dict/list/str/number/bool/None)")


def _thaw(value: Any) -> Any:
    """Convert a frozen tree back to plain structures (canonical form)."""
    if isinstance(value, _FrozenMapping):
        return {k: _thaw(v) for k, v in value._data.items()}
    if isinstance(value, _FrozenSequence):
        return [_thaw(v) for v in value._items]
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    if isinstance(value, list):
        return [_thaw(v) for v in value]
    if isinstance(value, dict):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, frozenset):
        return sorted(_thaw(v) for v in value)
    return value


def _canonical_json(value: Any) -> str:
    import json
    return json.dumps(_thaw(value), sort_keys=True, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# S20 — governor self-change (ER01 deep freeze + ER02 candidate semantics)
# --------------------------------------------------------------------------- #
S20_STATUSES = (
    "CURRENT_WINDOW_UNCHANGED",
    "FUTURE_VERSION_CANDIDATE",      # ER02: proposed, NOT activated
    "FUTURE_VERSION_RATIFIED",       # ER02: activated via canonical authority path
    "RETROACTIVE_CHANGE_REFUSED",
    "STALE_FINGERPRINT_REFUSED",
)


@dataclass(frozen=True)
class EvalContractSnapshot:
    """A frozen snapshot of an active evaluation contract's success criteria for
    one logical window (S20 / G6-ER01).

    The criteria tree is DEEP-FROZEN: every nested dict/list/set becomes an
    immutable structure at freeze time, aliases held by the caller are severed
    (containers are rebuilt, not wrapped in place), and any mutation attempt on
    any nesting level raises. The fingerprint is computed over the canonical
    (order-independent) form of the frozen tree."""

    contract_id: str
    window_seq: int
    criteria: Any                    # deep-frozen tree (FrozenMapping at top level)
    criteria_fingerprint: str
    created_by: str = "GOVERNOR"
    authority_basis: str = ""
    note: str = ""                   # CON-03 transparency note space

    @classmethod
    def freeze(cls, contract_id: str, window_seq: int, criteria: Mapping[str, Any],
               created_by: str = "GOVERNOR", authority_basis: str = "",
               note: str = "") -> "EvalContractSnapshot":
        frozen = _deep_freeze(dict(criteria or {}))
        fp = deterministic_hex("eval_contract_snapshot", contract_id, window_seq,
                               _canonical_json(frozen), length=24)
        return cls(
            contract_id=contract_id, window_seq=int(window_seq), criteria=frozen,
            criteria_fingerprint=fp, created_by=created_by,
            authority_basis=authority_basis, note=note)

    def mutate_criteria(self, key: str, value: Any) -> None:
        """Top-level mutation is refused (S20). Nested mutation is structurally
        impossible — see is_deeply_frozen()."""
        raise ValueError(
            "S20: the active evaluation contract's success criteria are frozen; "
            "same-object mutation is refused — changes are future candidates only")

    def is_deeply_frozen(self) -> bool:
        """ER01: verify EVERY node of the criteria tree is an immutable type."""
        def check(node: Any) -> bool:
            if isinstance(node, _FrozenMapping):
                return all(check(v) for v in node._data.values())
            if isinstance(node, _FrozenSequence):
                return all(check(v) for v in node._items)
            if isinstance(node, tuple):
                return all(check(v) for v in node)
            if isinstance(node, (dict, list, set)):
                return False
            if isinstance(node, _IMMUTABLE_SCALARS):
                return True
            return False
        return check(self.criteria)

    def canonical(self) -> Dict[str, Any]:
        return {"contract_id": self.contract_id, "window_seq": self.window_seq,
                "criteria": _thaw(self.criteria)}

    def to_dict(self) -> Dict[str, Any]:
        d = self.canonical()
        d["criteria_fingerprint"] = self.criteria_fingerprint
        d["created_by"] = self.created_by
        d["authority_basis"] = self.authority_basis
        return d


@dataclass(frozen=True)
class FutureEvaluationContractCandidate:
    """ER02: a PROPOSED future evaluation contract. Its existence does NOT
    change any active contract; activation requires the canonical governed
    authority path (prior proposal + non-self ratification)."""

    candidate_id: str
    contract_id: str
    base_window_seq: int
    target_window_seq: int
    snapshot: EvalContractSnapshot
    proposed_by: str
    proposal_evidence_ref: str
    status: str = "PROPOSED"          # PROPOSED | RATIFIED_ACTIVATED

    def to_dict(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id, "contract_id": self.contract_id,
                "base_window_seq": self.base_window_seq,
                "target_window_seq": self.target_window_seq,
                "snapshot": self.snapshot.to_dict(),
                "proposed_by": self.proposed_by,
                "proposal_evidence_ref": self.proposal_evidence_ref,
                "status": self.status}


@dataclass(frozen=True)
class ContractChangeVerdict:
    proposal_id: str
    status: str
    target_window_seq: int
    current_window_seq: int
    retroactive: bool
    rationale: str
    candidate: Optional[FutureEvaluationContractCandidate] = None
    activated_snapshot: Optional[EvalContractSnapshot] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"proposal_id": self.proposal_id, "status": self.status,
                "target_window_seq": self.target_window_seq,
                "current_window_seq": self.current_window_seq,
                "retroactive": self.retroactive, "rationale": self.rationale,
                "candidate": self.candidate.to_dict() if self.candidate else None,
                "activated_snapshot": self.activated_snapshot.to_dict()
                if self.activated_snapshot else None}


def propose_contract_criteria_change(
    current: EvalContractSnapshot,
    proposed_criteria: Mapping[str, Any],
    base_fingerprint: str,
    seq: int,
    proposed_by: str = "GOVERNOR",
    proposal_evidence_ref: str = "",
) -> ContractChangeVerdict:
    """S20/ER02: a rule change becomes a FUTURE_VERSION_CANDIDATE — never a
    self-adopted FUTURE_VERSION_ADOPTED. A stale base fingerprint is refused; a
    proposal targeting the current or a past window is retroactive and refused.
    The candidate carries the frozen proposed snapshot for the FUTURE window."""
    if base_fingerprint != current.criteria_fingerprint:
        return ContractChangeVerdict(
            proposal_id=deterministic_hex("s20_change", seq, base_fingerprint),
            status="STALE_FINGERPRINT_REFUSED",
            target_window_seq=current.window_seq + 1,
            current_window_seq=current.window_seq,
            retroactive=False,
            rationale=("proposal fingerprint does not match the current snapshot; "
                       "the proposal was authored against a stale base"))
    if seq <= current.window_seq:
        return ContractChangeVerdict(
            proposal_id=deterministic_hex("s20_change", seq, base_fingerprint),
            status="RETROACTIVE_CHANGE_REFUSED",
            target_window_seq=seq,
            current_window_seq=current.window_seq,
            retroactive=True,
            rationale=(f"proposal would set success criteria for window {seq}, "
                       f"which is not in the future of current window "
                       f"{current.window_seq} — no retroactive success criteria"))
    snapshot = EvalContractSnapshot.freeze(
        contract_id=current.contract_id, window_seq=seq, criteria=proposed_criteria,
        created_by=proposed_by,
        note="future candidate version only (S20/ER02) — not active until governed activation")
    candidate = FutureEvaluationContractCandidate(
        candidate_id=snapshot.criteria_fingerprint,
        contract_id=current.contract_id,
        base_window_seq=current.window_seq,
        target_window_seq=seq,
        snapshot=snapshot,
        proposed_by=proposed_by,
        proposal_evidence_ref=proposal_evidence_ref,
        status="PROPOSED")
    return ContractChangeVerdict(
        proposal_id=candidate.candidate_id,
        status="FUTURE_VERSION_CANDIDATE",
        target_window_seq=seq,
        current_window_seq=current.window_seq,
        retroactive=False,
        rationale=(f"future evaluation-contract candidate frozen for window {seq}; "
                   f"PROPOSED only — activation requires governed ratification "
                   f"(prior proposal + non-self ratifier); CON-03 carried: this "
                   f"does NOT solve transparent-vs-gameable thresholds"),
        candidate=candidate)


_EVALUATION_CONTRACT_CHANGE_RISK_CLASS = "deployment"   # authority-bearing class


def activate_future_version(
    candidate: FutureEvaluationContractCandidate,
    authority: AuthorityState,
    ratifier: str,
    seq: int,
    risk_class: str = _EVALUATION_CONTRACT_CHANGE_RISK_CLASS,
) -> ContractChangeVerdict:
    """ER02: governed activation of a future evaluation-contract candidate via
    the CANONICAL authority engine. The Governor (proposer) may PROPOSE; only a
    ratifier holding OPERATOR authority (canonical rule for authority-bearing
    risk classes) may activate, and never the target actor itself. A
    ratification without a prior proposal is refused by the canonical engine.

    Raises AuthorityViolation on any attempted shortcut (self-ratification,
    missing prior proposal, non-operator ratifier)."""
    if candidate.status != "PROPOSED":
        raise AuthorityViolation(
            f"candidate {candidate.candidate_id!r} is {candidate.status!r}, not PROPOSED")
    grant = CapabilityGrant.make(
        seq=seq, actor=candidate.proposed_by,
        action="activate_evaluation_contract",
        target=f"{candidate.contract_id}@window{candidate.target_window_seq}",
        issued_by=ratifier, risk_class=risk_class,
        environment="local-test")
    # canonical prior-proposal step: the proposer proposes the authority change
    # that would let the candidate activate (a worker may propose, never self-ratify)
    authority.propose_authority_change(candidate.proposed_by, candidate.proposed_by, grant)
    # canonical ratification: refuses self-ratification, missing prior proposal,
    # and non-operator ratifiers for authority-bearing risk classes
    authority.ratify_authority_change(ratifier, candidate.proposed_by,
                                      candidate.proposed_by, grant)
    issued = [g for g in authority.registry.grants(candidate.proposed_by)
              if g.grant_id == grant.grant_id]
    if not issued:
        raise AuthorityViolation(
            "activation grant was not issued by the canonical registry — refusing to activate")
    activated = EvalContractSnapshot.freeze(
        contract_id=candidate.contract_id, window_seq=candidate.target_window_seq,
        criteria=_thaw(candidate.snapshot.criteria),
        created_by=candidate.proposed_by,
        authority_basis=f"ratified by {ratifier} via canonical authority engine "
                        f"(grant {grant.grant_id}, risk_class {risk_class})",
        note="RATIFIED_ACTIVATED future window contract")
    ratified_candidate = FutureEvaluationContractCandidate(
        candidate_id=candidate.candidate_id, contract_id=candidate.contract_id,
        base_window_seq=candidate.base_window_seq,
        target_window_seq=candidate.target_window_seq,
        snapshot=candidate.snapshot, proposed_by=candidate.proposed_by,
        proposal_evidence_ref=candidate.proposal_evidence_ref,
        status="RATIFIED_ACTIVATED")
    return ContractChangeVerdict(
        proposal_id=candidate.candidate_id,
        status="FUTURE_VERSION_RATIFIED",
        target_window_seq=candidate.target_window_seq,
        current_window_seq=candidate.base_window_seq,
        retroactive=False,
        rationale=(f"future contract for window {candidate.target_window_seq} "
                   f"activated through canonical authority ratification "
                   f"(grant {grant.grant_id}); the CURRENT window contract is "
                   f"unchanged"),
        candidate=ratified_candidate,
        activated_snapshot=activated)


@dataclass(frozen=True)
class WindowEvaluation:
    result_id: str
    window_seq: int
    criteria_fingerprint_used: str
    passed: bool
    outcome_rule: str

    def to_dict(self) -> Dict[str, Any]:
        return {"result_id": self.result_id, "window_seq": self.window_seq,
                "criteria_fingerprint_used": self.criteria_fingerprint_used,
                "passed": self.passed, "outcome_rule": self.outcome_rule}


def evaluate_against_window(snapshot: EvalContractSnapshot, result_id: str,
                            observed_metric: float, metric_name: str = "primary") -> WindowEvaluation:
    """Deterministic evaluation of one result against ONE frozen window's
    criteria. The fingerprint used is the snapshot's own — later candidates or
    even ratified future versions never affect a current-window replay."""
    rule = snapshot.criteria.get(metric_name, snapshot.criteria.get("rule", "threshold"))
    threshold = float(snapshot.criteria.get(f"{metric_name}_threshold",
                                            snapshot.criteria.get("pass_threshold", 0.0)))
    passed = float(observed_metric) >= threshold
    return WindowEvaluation(
        result_id=result_id, window_seq=snapshot.window_seq,
        criteria_fingerprint_used=snapshot.criteria_fingerprint,
        passed=passed, outcome_rule=f"{rule}:>={threshold}")


# --------------------------------------------------------------------------- #
# S21 — capability != authority (ER03: canonical authority engine only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CapabilityGraphEntry:
    worker_id: str
    reliability_grade: str = "UNKNOWN"      # UNKNOWN | DEGRADED | NOMINAL | HIGH_RELIABILITY
    capability_evidence_refs: Tuple[str, ...] = ()
    capability_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"worker_id": self.worker_id, "reliability_grade": self.reliability_grade,
                "capability_evidence_refs": list(self.capability_evidence_refs),
                "capability_note": self.capability_note}


_GRADE_ORDER = ("UNKNOWN", "DEGRADED", "NOMINAL", "HIGH_RELIABILITY")


@dataclass(frozen=True)
class CapabilityChangeOutcome:
    worker_id: str
    reliability_before: str
    reliability_after: str
    capability_entry_changed: bool
    emitted: Tuple[str, ...]                 # AUTHORITY_REVIEW_REQUEST | (empty)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"worker_id": self.worker_id, "reliability_before": self.reliability_before,
                "reliability_after": self.reliability_after,
                "capability_entry_changed": self.capability_entry_changed,
                "emitted": list(self.emitted), "rationale": self.rationale}


def apply_capability_change(
    capability: CapabilityGraphEntry,
    new_reliability_grade: str,
    evidence_ref: str = "",
) -> CapabilityChangeOutcome:
    """S21/ER03: capability evidence may change; authority is NOT an input here
    at all. A reliability improvement emits AUTHORITY_REVIEW_REQUEST — a request
    directed at the canonical authority engine, never a grant. Any authority
    change must go through AuthorityState propose+ratify (see
    attempt_capability_driven_grant, which always fails)."""
    if new_reliability_grade not in _GRADE_ORDER:
        raise ValueError(f"unknown reliability grade {new_reliability_grade!r}; "
                         f"canonical: {list(_GRADE_ORDER)}")
    before = capability.reliability_grade
    improved = (_GRADE_ORDER.index(new_reliability_grade)
                > _GRADE_ORDER.index(before))
    emitted: List[str] = ["AUTHORITY_REVIEW_REQUEST"] if improved else []
    rationale = "capability record updated; no authority object touched"
    if improved:
        rationale = ("reliability improved; AUTHORITY_REVIEW_REQUEST emitted — "
                     "authority changes require the canonical propose+ratify path "
                     "with an eligible ratifier; capability alone grants nothing")
    return CapabilityChangeOutcome(
        worker_id=capability.worker_id,
        reliability_before=before,
        reliability_after=new_reliability_grade,
        capability_entry_changed=before != new_reliability_grade,
        emitted=tuple(emitted),
        rationale=rationale)


def attempt_capability_driven_grant(
    authority: AuthorityState,
    requester: str,
    target_actor: str,
    requested_risk_class: str,
    seq: int,
) -> CapabilityGrant:
    """S21 adversarial probe: a capability improvement attempts to mint its own
    authority grant through the canonical engine. The canonical engine's guards
    (self-ratification, prior-proposal, operator-ratifier) decide the outcome;
    this helper raises AuthorityViolation whenever the canonical rules refuse.
    It exists so G6 tests exercise REAL canonical semantics instead of a local
    reimplementation (ER03: no second authority constitution)."""
    grant = CapabilityGrant.make(
        seq=seq, actor=target_actor, action="self_granted_capability_promotion",
        target=f"actor:{target_actor}", issued_by=requester,
        risk_class=requested_risk_class, environment="local-test")
    authority.propose_authority_change(requester, target_actor, grant)
    authority.ratify_authority_change(requester, requester, target_actor, grant)
    return grant


# --------------------------------------------------------------------------- #
# S22 — operator authority != truth (ER04)
# --------------------------------------------------------------------------- #
VALID_EMPIRICAL_GRADES = ("UNVERIFIED", "CONTESTED", "SUPPORTED", "REFUTED")


@dataclass(frozen=True)
class EmpiricalEvidenceGrade:
    evidence_id: str
    empirical_grade: str = "UNVERIFIED"
    grade_evidence_refs: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.empirical_grade not in VALID_EMPIRICAL_GRADES:
            raise ValueError(f"unknown empirical grade {self.empirical_grade!r}; "
                             f"canonical: {list(VALID_EMPIRICAL_GRADES)}")

    def to_dict(self) -> Dict[str, Any]:
        return {"evidence_id": self.evidence_id, "empirical_grade": self.empirical_grade,
                "grade_evidence_refs": list(self.grade_evidence_refs)}


@dataclass(frozen=True)
class EvidenceGraph:
    grades: Tuple[EmpiricalEvidenceGrade, ...] = ()

    def grade_of(self, evidence_id: str) -> str:
        for g in self.grades:
            if g.evidence_id == evidence_id:
                return g.empirical_grade
        return "UNVERIFIED"

    def with_grade(self, evidence_id: str, new_grade: str, ref: str,
                   registry: EvidenceRegistry) -> "EvidenceGraph":
        """ER04: a grade changes ONLY when the evidence changes — `ref` must
        RESOLVE in the governed evidence registry (an arbitrary non-empty string
        is not evidence), and the new grade must be in the canonical vocabulary.
        This is the only path that moves an EmpiricalEvidenceGrade."""
        if new_grade not in VALID_EMPIRICAL_GRADES:
            raise ValueError(f"unknown empirical grade {new_grade!r}; "
                             f"canonical: {list(VALID_EMPIRICAL_GRADES)}")
        if not ref or not registry.has(ref):
            raise ValueError(
                f"evidence grade change requires a REGISTERED evidence ref; "
                f"{ref!r} does not resolve in the governed registry")
        updated = []
        for g in self.grades:
            if g.evidence_id == evidence_id:
                updated.append(EmpiricalEvidenceGrade(
                    evidence_id=g.evidence_id, empirical_grade=new_grade,
                    grade_evidence_refs=g.grade_evidence_refs + (ref,)))
            else:
                updated.append(g)
        return EvidenceGraph(grades=tuple(updated))


@dataclass(frozen=True)
class OperatorMandate:
    """ER04: a Governor is not automatically an Operator. Operator-level action
    authorization requires a specifically granted mandate (issued by someone
    other than the holder — no self-mandate)."""

    actor: str
    scope: str
    issued_by: str
    grant_ref: str
    seq: int
    mandate_id: str = ""

    def __post_init__(self) -> None:
        if not self.mandate_id:
            object.__setattr__(self, "mandate_id", deterministic_hex(
                "operator_mandate", self.seq, self.actor, self.scope, self.issued_by))
        if self.issued_by == self.actor:
            raise AuthorityViolation("an actor may not issue its own operator mandate")

    def to_dict(self) -> Dict[str, Any]:
        return {"mandate_id": self.mandate_id, "actor": self.actor,
                "scope": self.scope, "issued_by": self.issued_by,
                "grant_ref": self.grant_ref, "seq": self.seq}


@dataclass(frozen=True)
class ConstitutionPermissionRecord:
    """ER04: constitutional permission is represented by a governed record, not
    a fixture boolean. `rule_ref` must name the constitutional rule and `basis`
    must say why the action class is permitted."""

    rule_ref: str
    permitted_action_class: str
    basis: str
    seq: int = 0

    def __post_init__(self) -> None:
        if not self.rule_ref or not self.basis:
            raise ValueError(
                "a constitutional permission record requires a rule_ref and a basis; "
                "a bare boolean cannot mint constitutional permission")

    def to_dict(self) -> Dict[str, Any]:
        return {"rule_ref": self.rule_ref,
                "permitted_action_class": self.permitted_action_class,
                "basis": self.basis, "seq": self.seq}


@dataclass(frozen=True)
class OperatorDirectiveOutcome:
    directive_id: str
    operator_action_authorized: bool
    authorization_basis: str
    evidence_grade_unchanged: bool
    evidence_grade_before: str
    evidence_grade_after: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {"directive_id": self.directive_id,
                "operator_action_authorized": self.operator_action_authorized,
                "authorization_basis": self.authorization_basis,
                "evidence_grade_unchanged": self.evidence_grade_unchanged,
                "evidence_grade_before": self.evidence_grade_before,
                "evidence_grade_after": self.evidence_grade_after,
                "rationale": self.rationale}


def apply_operator_directive(
    directive_id: str,
    authority_level: str,
    graph: EvidenceGraph,
    permission: ConstitutionPermissionRecord,
    evidence_id: str = "",
    mandate: Optional[OperatorMandate] = None,
    operator_preference: str = "",
) -> OperatorDirectiveOutcome:
    """S22/ER04: authority != truth, in BOTH directions.

    Authority side: the action is authorized only when the actor holds OPERATOR
    authority, or holds GOVERNOR authority WITH a specifically granted operator
    mandate, AND a governed ConstitutionPermissionRecord covers the action
    class. A bare boolean cannot mint permission; GOVERNOR alone is not
    OPERATOR.

    Truth side: the empirical evidence grade is never read or written here.
    Operator preference is recorded for the receipt but has NO vote: desire
    cannot improve weak evidence (directional test A) and desire cannot prevent
    a strong contradictory evidence transition (directional test B — the grade
    moves only via EvidenceGraph.with_grade with a registered evidence ref).
    """
    if permission.permitted_action_class not in ("RESEARCH", "EXPERIMENT", "POLICY"):
        raise ValueError(f"unknown permitted action class "
                         f"{permission.permitted_action_class!r}")
    authorized = False
    basis = ""
    if authority_level == "OPERATOR":
        authorized = True
        basis = "operator authority + governed constitutional permission record"
    elif authority_level == "GOVERNOR":
        if mandate is not None and mandate.actor and mandate.grant_ref:
            authorized = True
            basis = (f"GOVERNOR with specifically granted operator mandate "
                     f"{mandate.mandate_id} (issued_by={mandate.issued_by}) + "
                     f"governed constitutional permission record")
        else:
            basis = ("GOVERNOR authority alone is NOT operator authority; "
                     "no mandate granted — action not authorized")
    else:
        basis = (f"authority level {authority_level!r} cannot authorize operator "
                 f"actions")
    if authorized:
        basis += f" [{permission.rule_ref}: {permission.permitted_action_class}]"
    before = graph.grade_of(evidence_id) if evidence_id else "UNVERIFIED"
    preference_note = (f"; operator_preference={operator_preference!r} recorded "
                       f"with no vote over evidence") if operator_preference else ""
    rationale = (f"directive recorded; action_authorized={authorized} (authority "
                 f"axis); empirical evidence grade untouched (truth axis) — "
                 f"grades move only via registered evidence refs{preference_note}")
    return OperatorDirectiveOutcome(
        directive_id=directive_id,
        operator_action_authorized=authorized,
        authorization_basis=basis,
        evidence_grade_unchanged=True,
        evidence_grade_before=before,
        evidence_grade_after=before,
        rationale=rationale)


# --------------------------------------------------------------------------- #
# S23 — operator unavailable (ER05: actual envelope vs granted envelope)
# --------------------------------------------------------------------------- #
HOLD_SURFACES = ("CONSTITUTIONAL", "CAPITAL", "IRREVERSIBLE", "HIGH_AFFECTED_SURFACE")


@dataclass(frozen=True)
class ActionRequest:
    """ER05: the ACTUAL action being requested, structured so its risk cannot
    hide behind grant metadata. risk_class uses the CANONICAL vocabulary from
    engine/authority.py (unknown classes fail closed at construction)."""

    action: str
    target_scope: str
    affected_surface: str = "REVERSIBLE_SANDBOX"
    reversible: bool = True
    risk_class: str = "local-write"
    environment: str = "local-test"

    def __post_init__(self) -> None:
        if self.risk_class not in RISK_CLASSES:
            raise AuthorityViolation(
                f"unknown risk_class {self.risk_class!r}; canonical vocabulary: "
                f"{sorted(RISK_CLASSES)}")
        if not self.action or not self.target_scope:
            raise ValueError("an action request requires action and target_scope")

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "target_scope": self.target_scope,
                "affected_surface": self.affected_surface,
                "reversible": self.reversible, "risk_class": self.risk_class,
                "environment": self.environment}


@dataclass(frozen=True)
class ActionGrantEnvelope:
    """ER05: the GRANTED action envelope (pre-existing grant). The grant covers
    exactly what it was issued for — a request must fit this envelope on EVERY
    axis; neither side may claim lower risk than the other."""

    grant_id: str
    grantee: str
    action: str
    target_scope: str
    affected_surface: str = "REVERSIBLE_SANDBOX"
    reversible: bool = True
    risk_class: str = "local-write"
    environment: str = "local-test"
    issued_seq: int = 0
    expiry_seq: int = 0              # 0 = never expires
    status: str = "ACTIVE"           # ACTIVE | EXPIRED | REVOKED
    authority_basis: str = ""

    def __post_init__(self) -> None:
        if self.risk_class not in RISK_CLASSES:
            raise AuthorityViolation(
                f"unknown risk_class {self.risk_class!r}; canonical vocabulary: "
                f"{sorted(RISK_CLASSES)}")

    def to_dict(self) -> Dict[str, Any]:
        return {"grant_id": self.grant_id, "grantee": self.grantee,
                "action": self.action, "target_scope": self.target_scope,
                "affected_surface": self.affected_surface,
                "reversible": self.reversible, "risk_class": self.risk_class,
                "environment": self.environment, "issued_seq": self.issued_seq,
                "expiry_seq": self.expiry_seq, "status": self.status,
                "authority_basis": self.authority_basis}


@dataclass(frozen=True)
class OperatorHoldVerdict:
    action_id: str
    verdict: str                     # MAY_CONTINUE | OPERATOR_HOLD
    grant_used: str = ""
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"action_id": self.action_id, "verdict": self.verdict,
                "grant_used": self.grant_used, "rationale": self.rationale}


def execute_under_operator_hold(
    action_id: str,
    actor: str,
    request: ActionRequest,
    grant: Optional[ActionGrantEnvelope],
    current_seq: int,
) -> OperatorHoldVerdict:
    """S23/ER05: while the operator is unavailable, continuation requires an
    ACTIVE pre-existing grant whose envelope covers the ACTUAL requested action
    on every axis — action, target scope, affected surface, reversibility,
    canonical risk class, environment — AND the grant must PRE-DATE the
    operator-unavailable decision (issued_seq < current_seq). Neither side's
    claim of lower risk is trusted alone:

      * an actual CAPITAL/authority-bearing risk class holds even when grant
        metadata says REVERSIBLE_SANDBOX;
      * an actual irreversible action holds even when the grant says reversible;
      * a grant whose own envelope is authority-bearing or irreversible can
        never authorize operator-unavailable continuation;
      * near-match actions/scopes, expired/revoked grants, wrong grantees and
        post-hoc grants all hold.

    AMB-08 is carried honestly: a hold is a hold, not a resolution."""
    def _hold(reason: str) -> OperatorHoldVerdict:
        return OperatorHoldVerdict(action_id=action_id, verdict="OPERATOR_HOLD",
                                   rationale=reason)

    if grant is None:
        return _hold("no pre-existing grant covers this action")
    if grant.status != "ACTIVE":
        return _hold(f"grant {grant.grant_id} is {grant.status} — does not count")
    if grant.issued_seq >= current_seq:
        return _hold(f"grant {grant.grant_id} was issued at seq {grant.issued_seq}, "
                     f"not before the operator-unavailable decision seq {current_seq} "
                     f"— a post-hoc grant cannot retroactively authorize work")
    if grant.expiry_seq and current_seq >= grant.expiry_seq:
        return _hold(f"grant {grant.grant_id} expired at seq {grant.expiry_seq}")
    if grant.grantee != actor:
        return _hold(f"grant {grant.grant_id} is held by {grant.grantee}, not {actor}")
    # ---- actual-vs-granted envelope comparison (BOTH sides matter) ---- #
    if request.risk_class in AUTHORITY_BEARING_RISK_CLASSES:
        return _hold(f"ACTUAL action risk class {request.risk_class!r} is "
                     f"authority-bearing; safe grant metadata "
                     f"({grant.risk_class!r}) cannot hide it — OPERATOR_HOLD")
    if grant.risk_class in AUTHORITY_BEARING_RISK_CLASSES:
        return _hold(f"grant {grant.grant_id} envelope carries authority-bearing "
                     f"risk class {grant.risk_class!r}; it cannot authorize "
                     f"operator-unavailable continuation")
    if request.risk_class != grant.risk_class:
        return _hold(f"risk class mismatch: actual {request.risk_class!r} vs "
                     f"granted {grant.risk_class!r}")
    if request.action != grant.action:
        return _hold(f"near-match only: grant covers action {grant.action!r}, "
                     f"requested {request.action!r} — near-match does not count")
    if request.target_scope != grant.target_scope:
        return _hold(f"scope mismatch: grant covers {grant.target_scope!r}, "
                     f"requested {request.target_scope!r}")
    if not request.reversible:
        return _hold(f"ACTUAL action is irreversible; grant reversibility "
                     f"({grant.reversible}) cannot make it reversible")
    if not grant.reversible:
        return _hold(f"grant {grant.grant_id} envelope is non-reversible; it "
                     f"cannot authorize operator-unavailable continuation")
    if request.affected_surface in HOLD_SURFACES:
        return _hold(f"ACTUAL affected surface {request.affected_surface!r} "
                     f"exceeds the pre-authorized reversible sandbox — OPERATOR_HOLD")
    if grant.affected_surface in HOLD_SURFACES:
        return _hold(f"grant envelope surface {grant.affected_surface!r} exceeds "
                     f"the pre-authorized reversible sandbox")
    if request.affected_surface != grant.affected_surface:
        return _hold(f"surface mismatch: actual {request.affected_surface!r} vs "
                     f"granted {grant.affected_surface!r}")
    if request.environment != grant.environment:
        return _hold(f"environment mismatch: actual {request.environment!r} vs "
                     f"granted {grant.environment!r}")
    return OperatorHoldVerdict(action_id=action_id, verdict="MAY_CONTINUE",
                               grant_used=grant.grant_id,
                               rationale="actual action envelope fully covered by an "
                                         "ACTIVE pre-existing grant envelope "
                                         "(action/scope/surface/reversibility/risk/"
                                         "environment) issued before the hold")


# --------------------------------------------------------------------------- #
# S24 — unknown governance event (ER06: evidence-bound classification)
# --------------------------------------------------------------------------- #
GOVERNANCE_CHANNELS = ("EVALUATION", "AMENDMENT", "EVIDENCE", "AUTHORITY",
                       "SENSOR", "CAPABILITY")


@dataclass(frozen=True)
class GovernanceEvent:
    event_id: str
    raw_event: str
    evidence_refs: Tuple[str, ...] = ()
    consequence_class: str = ""
    authority_context: str = ""
    containment_action: str = "SAFE_HOLD"
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "raw_event": self.raw_event,
                "evidence_refs": list(self.evidence_refs),
                "consequence_class": self.consequence_class,
                "authority_context": self.authority_context,
                "containment_action": self.containment_action, "seq": self.seq}


@dataclass(frozen=True)
class GovernanceClassificationEvidence:
    """ER06: structured classification signal. A channel may be used ONLY when
    supported by such evidence (with resolving evidence refs); raw_event prose
    tokens are never a decision authority."""

    proposed_channel: str
    evidence_refs: Tuple[str, ...] = ()
    classifier_version: str = "g6-classifier-1"
    status: str = "SUPPORTED"        # SUPPORTED | CONTESTED | UNVERIFIED
    unresolved_conflicts: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in ("SUPPORTED", "CONTESTED", "UNVERIFIED"):
            raise ValueError(f"unknown classification-evidence status "
                             f"{self.status!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {"proposed_channel": self.proposed_channel,
                "evidence_refs": list(self.evidence_refs),
                "classifier_version": self.classifier_version,
                "status": self.status,
                "unresolved_conflicts": list(self.unresolved_conflicts)}


@dataclass(frozen=True)
class GovernanceEventDisposition:
    event_id: str
    channel: str                     # GOVERNANCE_CHANNELS entry | "UNRESOLVED_GOVERNANCE_EVENT"
    classification_failure: str
    preserved: Dict[str, Any]        # raw event / evidence / consequence / authority /
                                     # containment / raw token hits / classification evidence
    amendment_candidate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "channel": self.channel,
                "classification_failure": self.classification_failure,
                "preserved": self.preserved, "amendment_candidate": self.amendment_candidate}


def classify_governance_event(
    event: GovernanceEvent,
    classification_evidence: Sequence[GovernanceClassificationEvidence] = (),
    channels: Sequence[str] = GOVERNANCE_CHANNELS,
    registry: Optional[EvidenceRegistry] = None,
) -> GovernanceEventDisposition:
    """S24/ER06: route a governance event ONLY on structured, evidence-backed
    classification signals.

      * exactly one unique SUPPORTED channel (with evidence refs that resolve
        when a registry is supplied) -> that channel;
      * zero supported channels -> UNRESOLVED_GOVERNANCE_EVENT
        (NO_EVIDENCE_SUPPORTED_CHANNEL) — even if the raw text contains a
        familiar keyword;
      * more than one supported channel -> UNRESOLVED_GOVERNANCE_EVENT
        (AMBIGUOUS_EVIDENCE_SUPPORTED_CHANNELS);
      * an unresolved event preserves raw event, evidence refs, consequence
        class, authority context, containment action, the raw token hits
        (recorded as OBSERVATION ONLY) and the classification evidence, plus a
        non-self-ratified amendment candidate.

    No nearest-category coercion; no automatic ontology mutation."""
    ch = tuple(channels or GOVERNANCE_CHANNELS)
    raw_hits = [c for c in ch if c.lower() in (event.raw_event or "").lower()]
    supported: List[str] = []
    for ce in classification_evidence or ():
        if ce.status != "SUPPORTED" or ce.proposed_channel not in ch:
            continue
        if not ce.evidence_refs:
            continue
        if registry is not None:
            if not all(registry.has(r) for r in ce.evidence_refs):
                continue
        supported.append(ce.proposed_channel)
    unique = sorted(set(supported))
    preserved = event.to_dict()
    preserved["raw_text_token_hits"] = raw_hits          # observation only
    preserved["classification_evidence"] = [ce.to_dict() for ce in (classification_evidence or ())]
    if len(unique) == 1:
        return GovernanceEventDisposition(
            event_id=event.event_id, channel=unique[0],
            classification_failure="", preserved=preserved)
    if len(unique) > 1:
        preserved["matching_channels"] = unique
        return GovernanceEventDisposition(
            event_id=event.event_id, channel="UNRESOLVED_GOVERNANCE_EVENT",
            classification_failure="AMBIGUOUS_EVIDENCE_SUPPORTED_CHANNELS",
            preserved=preserved,
            amendment_candidate="channel ontology candidate — not self-ratified")
    return GovernanceEventDisposition(
        event_id=event.event_id, channel="UNRESOLVED_GOVERNANCE_EVENT",
        classification_failure="NO_EVIDENCE_SUPPORTED_CHANNEL",
        preserved=preserved,
        amendment_candidate=("ontology/amendment candidate — requires a governed "
                             "amendment path; not self-ratified"))


# --------------------------------------------------------------------------- #
# ER07 — CON-02 allocator provenance observability (NOT a constitutional rule)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AllocatorProvenanceRecord:
    """CON-02 observability: who initiated an evidence path, who allocated the
    worker/reviewer, what source/retrieval path was used, and which evidence ref
    resulted. Pure observation — never a disqualifier by itself."""

    evidence_ref: str
    initiating_actor: str
    allocator_actor: str
    worker_selected: str = ""
    source_path: str = ""
    retrieval_lineage: str = ""
    exposure_lineage: str = ""
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"evidence_ref": self.evidence_ref,
                "initiating_actor": self.initiating_actor,
                "allocator_actor": self.allocator_actor,
                "worker_selected": self.worker_selected,
                "source_path": self.source_path,
                "retrieval_lineage": self.retrieval_lineage,
                "exposure_lineage": self.exposure_lineage, "seq": self.seq}


@dataclass
class AllocatorProvenanceLedger:
    """Bounded observational ledger over evidence paths. Detects when ALL
    apparently independent evidence paths were allocated through one allocator
    (PO agenda-power concern, CON-02). Detection does NOT reject the evidence
    and does NOT amend A-009/A-010 — it surfaces ALLOCATOR_CONCENTRATION for
    G7 sensitivity testing and later analysis."""

    records: List[AllocatorProvenanceRecord] = field(default_factory=list)

    def record(self, rec: AllocatorProvenanceRecord) -> None:
        if not rec.evidence_ref:
            raise ValueError("allocator provenance requires an evidence_ref")
        self.records.append(rec)

    def allocator_concentration(self) -> Dict[str, Any]:
        if not self.records:
            return {"paths": 0, "distinct_allocators": 0, "distinct_initiators": 0,
                    "concentration": "NO_PATHS", "allocators": []}
        allocators = sorted({r.allocator_actor for r in self.records})
        initiators = sorted({r.initiating_actor for r in self.records})
        concentrated = len(allocators) == 1 and len(self.records) >= 2
        return {
            "paths": len(self.records),
            "distinct_allocators": len(allocators),
            "distinct_initiators": len(initiators),
            "allocators": allocators,
            "initiators": initiators,
            "concentration": ("CONCENTRATED_SINGLE_ALLOCATOR" if concentrated
                              else "DIVERSE"),
            "note": ("all apparently independent evidence paths were allocated "
                     "through one allocator (CON-02 observability surface; "
                     "observability only — no constitutional rule applied)"
                     if concentrated else
                     "allocator topology observed; no concentration detected"),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"records": [r.to_dict() for r in self.records],
                "allocator_concentration": self.allocator_concentration()}
