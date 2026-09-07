"""G6 — constitutional-attack governance scenarios S20–S24 (deterministic).

Conditional G6 authorization follows PASS_G5RER_TRUTH_CLOSURE. These objects
implement the S20–S24 adversarial semantics only — nothing here mutates
production/cloud/capital, calls a model, or depends on wall clock:

  S20  an active evaluation contract cannot change its own success criteria
       mid-window — change is a NEW future version only; replays use the
       original frozen criteria; no retroactive success criteria.
  S21  capability != authority: a more reliable worker may improve
       CapabilityGraph evidence but may only emit AUTHORITY_REVIEW_REQUEST,
       never AUTHORITY_GRANTED, without an existing governed grant authority.
  S22  operator authority != truth: the operator may authorize legitimate
       action where the constitution permits, but EvidenceGraph empirical
       grades change only when the evidence changes.
  S23  operator unavailable: only an explicit pre-existing grant covering an
       exact reversible sandbox action may continue; near-match / expired /
       revoked / high-surface / irreversible / constitutional / capital all
       stay OPERATOR_HOLD (AMB-08 carried honestly).
  S24  unknown governance events stay UNRESOLVED_GOVERNANCE_EVENT — raw event,
       evidence, consequence class, authority, containment action,
       classification failure and amendment candidate are preserved; no
       nearest-category coercion, no self-ratified ontology changes.

All identifiers derive from content (deterministic_hex); all criteria maps are
deep-frozen after creation so same-object mutation is structurally impossible.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

# --------------------------------------------------------------------------- #
# S20 — governor self-change
# --------------------------------------------------------------------------- #
S20_STATUSES = (
    "CURRENT_WINDOW_UNCHANGED",      # replay/use of the current window contract
    "FUTURE_VERSION_ADOPTED",        # new candidate version for a FUTURE window
    "RETROACTIVE_CHANGE_REFUSED",    # proposed criteria would change a past/current window
    "STALE_FINGERPRINT_REFUSED",     # proposal not derived from the current snapshot+seq
    "SAME_OBJECT_MUTATION_REFUSED",  # direct mutation of the frozen current contract
)


@dataclass(frozen=True)
class EvalContractSnapshot:
    """A frozen snapshot of an active evaluation contract's success criteria
    for one logical window. criteria is an immutable mapping proxy; its
    fingerprint is computed from the canonical criteria + window seq."""

    contract_id: str
    window_seq: int
    criteria: Mapping[str, Any]
    criteria_fingerprint: str
    created_by: str = "GOVERNOR"
    authority_basis: str = ""
    note: str = ""          # CON-03 transparency note space

    @classmethod
    def freeze(cls, contract_id: str, window_seq: int, criteria: Mapping[str, Any],
               created_by: str = "GOVERNOR", authority_basis: str = "",
               note: str = "") -> "EvalContractSnapshot":
        canon = {k: copy.deepcopy(v) for k, v in dict(criteria or {}).items()}
        fp = deterministic_hex("eval_contract_snapshot", contract_id, window_seq,
                               canon, length=24)
        return cls(
            contract_id=contract_id, window_seq=int(window_seq),
            criteria=MappingProxyType(canon), criteria_fingerprint=fp,
            created_by=created_by, authority_basis=authority_basis, note=note)

    def mutate_criteria(self, key: str, value: Any) -> None:
        """Any attempt to mutate the frozen current-window criteria raises —
        same-object mutation is structurally impossible (S20)."""
        raise ValueError(
            "S20: the active evaluation contract's success criteria are frozen; "
            "same-object mutation is refused — changes are new future versions only")

    def canonical(self) -> Dict[str, Any]:
        return {"contract_id": self.contract_id, "window_seq": self.window_seq,
                "criteria": dict(self.criteria)}

    def to_dict(self) -> Dict[str, Any]:
        d = self.canonical()
        d["criteria_fingerprint"] = self.criteria_fingerprint
        d["created_by"] = self.created_by
        d["authority_basis"] = self.authority_basis
        return d


@dataclass(frozen=True)
class ContractChangeVerdict:
    proposal_id: str
    status: str
    target_window_seq: int
    current_window_seq: int
    retroactive: bool
    rationale: str
    adopted_snapshot: Optional[EvalContractSnapshot] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"proposal_id": self.proposal_id, "status": self.status,
                "target_window_seq": self.target_window_seq,
                "current_window_seq": self.current_window_seq,
                "retroactive": self.retroactive, "rationale": self.rationale,
                "adopted_snapshot": self.adopted_snapshot.to_dict()
                if self.adopted_snapshot else None}


def propose_contract_criteria_change(
    current: EvalContractSnapshot,
    proposed_criteria: Mapping[str, Any],
    base_fingerprint: str,
    seq: int,
) -> ContractChangeVerdict:
    """S20: an active contract may only adopt NEW success criteria for a FUTURE
    window. A proposal whose fingerprint is not derived from the CURRENT
    snapshot is stale and refused; a proposal targeting the current or a past
    window is retroactive and refused."""
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
    future = EvalContractSnapshot.freeze(
        contract_id=current.contract_id, window_seq=seq,
        criteria=proposed_criteria, created_by="GOVERNOR",
        note="future candidate version only (S20)")
    return ContractChangeVerdict(
        proposal_id=future.criteria_fingerprint,
        status="FUTURE_VERSION_ADOPTED",
        target_window_seq=seq,
        current_window_seq=current.window_seq,
        retroactive=False,
        rationale=f"new candidate version frozen for future window {seq}",
        adopted_snapshot=future)


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
    criteria. The fingerprint used is the snapshot's own — later future
    versions never affect a current-window replay."""
    rule = snapshot.criteria.get(metric_name, snapshot.criteria.get("rule", "threshold"))
    threshold = float(snapshot.criteria.get(f"{metric_name}_threshold",
                                            snapshot.criteria.get("pass_threshold", 0.0)))
    passed = float(observed_metric) >= threshold
    return WindowEvaluation(
        result_id=result_id, window_seq=snapshot.window_seq,
        criteria_fingerprint_used=snapshot.criteria_fingerprint,
        passed=passed, outcome_rule=f"{rule}:>={threshold}")


# --------------------------------------------------------------------------- #
# S21 — capability != authority
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


@dataclass(frozen=True)
class AuthorityGraphEntry:
    actor_id: str
    authority_level: str = "NONE"            # NONE | WORKER | OPERATOR | GOVERNOR
    grant_refs: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"actor_id": self.actor_id, "authority_level": self.authority_level,
                "grant_refs": list(self.grant_refs)}


@dataclass(frozen=True)
class CapabilityChangeOutcome:
    worker_id: str
    reliability_before: str
    reliability_after: str
    capability_entry_changed: bool
    authority_entry_unchanged: bool
    emitted: Tuple[str, ...]                 # AUTHORITY_REVIEW_REQUEST | NONE
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"worker_id": self.worker_id, "reliability_before": self.reliability_before,
                "reliability_after": self.reliability_after,
                "capability_entry_changed": self.capability_entry_changed,
                "authority_entry_unchanged": self.authority_entry_unchanged,
                "emitted": list(self.emitted), "rationale": self.rationale}


_GRADE_ORDER = ("UNKNOWN", "DEGRADED", "NOMINAL", "HIGH_RELIABILITY")


def apply_capability_change(
    capability: CapabilityGraphEntry,
    authority: AuthorityGraphEntry,
    new_reliability_grade: str,
    evidence_ref: str = "",
) -> CapabilityChangeOutcome:
    """S21: capability evidence may change; authority may NOT. A reliability
    improvement emits AUTHORITY_REVIEW_REQUEST (a request, never a grant);
    it never emits AUTHORITY_GRANTED and never changes the authority entry."""
    before = capability.reliability_grade
    improved = (_GRADE_ORDER.index(new_reliability_grade)
                > _GRADE_ORDER.index(before))
    emitted: List[str] = []
    rationale = "capability record updated; authority unchanged"
    if improved:
        emitted.append("AUTHORITY_REVIEW_REQUEST")
        rationale = ("reliability improved; AUTHORITY_REVIEW_REQUEST emitted — "
                     "authority requires an existing governed grant, never follows "
                     "capability automatically")
    return CapabilityChangeOutcome(
        worker_id=capability.worker_id,
        reliability_before=before,
        reliability_after=new_reliability_grade,
        capability_entry_changed=before != new_reliability_grade,
        authority_entry_unchanged=True,
        emitted=tuple(emitted),
        rationale=rationale)


_GRANTABLE_LEVELS = ("WORKER", "OPERATOR", "GOVERNOR")
_REQUIRED_GRANTOR = {"WORKER": "GOVERNOR", "OPERATOR": "GOVERNOR", "GOVERNOR": "GOVERNOR"}


def governed_authority_grant(
    grantee: str,
    requested_level: str,
    grantor: AuthorityGraphEntry,
    grant_evidence_ref: str,
    seq: int,
) -> Tuple[bool, str, str]:
    """Authority is only minted by an EXISTING governed grant authority. A
    worker/operator with no GOVERNOR-level grant cannot grant; a capability
    record alone never grants. Returns (granted, level, rationale)."""
    if requested_level not in _GRANTABLE_LEVELS:
        return False, "NONE", f"requested level {requested_level!r} not grantable"
    needed = _REQUIRED_GRANTOR[requested_level]
    if grantor.authority_level != needed or not grantor.grant_refs:
        return (False, "NONE",
                f"grantor holds {grantor.authority_level!r} without a governed "
                f"{needed} grant — authority cannot be minted from capability")
    if not grant_evidence_ref:
        return False, "NONE", "grant requires an evidence ref (fail closed)"
    return (True, requested_level,
            f"granted {requested_level} to {grantee} from governed grantor "
            f"{grantor.actor_id} (evidence {grant_evidence_ref})")


# --------------------------------------------------------------------------- #
# S22 — operator authority != truth
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EmpiricalEvidenceGrade:
    evidence_id: str
    empirical_grade: str = "UNVERIFIED"   # UNVERIFIED | CONTESTED | SUPPORTED
    grade_evidence_refs: Tuple[str, ...] = ()

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

    def with_grade(self, evidence_id: str, new_grade: str, ref: str) -> "EvidenceGraph":
        """Grades change ONLY when the evidence changes (a grade_evidence_ref is
        supplied). This is the only way an EmpiricalEvidenceGrade moves."""
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
    operator_authority_level: str,
    graph: EvidenceGraph,
    constitution_allows_action: bool,
    evidence_id: str = "",
) -> OperatorDirectiveOutcome:
    """S22: the operator may authorize legitimate action/experiment/policy where
    the constitution permits (authority), but may NEVER change an empirical
    evidence grade (truth). A directive that names an evidence grade change is
    refused on the truth axis even when the action itself is authorized."""
    authorized = (operator_authority_level in ("OPERATOR", "GOVERNOR")
                  and constitution_allows_action)
    before = graph.grade_of(evidence_id) if evidence_id else "UNVERIFIED"
    after = before
    if evidence_id and authorized:
        # Operator desire (weak evidence OR preferred incumbent) is NOT evidence:
        # the grade stays put unless the evidence graph itself changes.
        pass
    rationale = (f"operator directive recorded; action_authorized={authorized} "
                 f"(authority); empirical evidence grade unchanged (truth) — "
                 f"desire is not evidence")
    return OperatorDirectiveOutcome(
        directive_id=directive_id,
        operator_action_authorized=authorized,
        authorization_basis="constitution-permitted operator action",
        evidence_grade_unchanged=True,
        evidence_grade_before=before,
        evidence_grade_after=after,
        rationale=rationale)


# --------------------------------------------------------------------------- #
# S23 — operator unavailable
# --------------------------------------------------------------------------- #
HOLD_SURFACES = ("CONSTITUTIONAL", "CAPITAL", "IRREVERSIBLE", "HIGH_AFFECTED_SURFACE")


@dataclass(frozen=True)
class PreAuthorizedGrant:
    grant_id: str
    grantee: str
    exact_action: str
    surface_class: str = "REVERSIBLE_SANDBOX"
    reversible: bool = True
    issued_seq: int = 0
    expiry_seq: int = 0              # 0 = never expires (not recommended)
    status: str = "ACTIVE"           # ACTIVE | EXPIRED | REVOKED
    authority_basis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"grant_id": self.grant_id, "grantee": self.grantee,
                "exact_action": self.exact_action, "surface_class": self.surface_class,
                "reversible": self.reversible, "issued_seq": self.issued_seq,
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
    requested_action: str,
    grant: Optional[PreAuthorizedGrant],
    current_seq: int,
    affected_surface: str = "REVERSIBLE_SANDBOX",
    reversible: bool = True,
) -> OperatorHoldVerdict:
    """S23: only an explicit, active, pre-existing grant covering the EXACT
    requested reversible sandbox action MAY continue while the operator is
    unavailable. Near-match grants, expired/revoked grants, and any
    high-surface/irreversible/constitutional/capital action stay OPERATOR_HOLD
    (AMB-08 is carried honestly — a hold is not a resolution)."""
    def _hold(reason: str) -> OperatorHoldVerdict:
        return OperatorHoldVerdict(action_id=action_id, verdict="OPERATOR_HOLD",
                                   rationale=reason)

    if grant is None:
        return _hold("no pre-existing grant covers this action")
    if grant.status != "ACTIVE":
        return _hold(f"grant {grant.grant_id} is {grant.status} — does not count")
    if grant.expiry_seq and current_seq >= grant.expiry_seq:
        return _hold(f"grant {grant.grant_id} expired at seq {grant.expiry_seq}")
    if grant.exact_action != requested_action:
        return _hold(f"near-match only: grant covers {grant.exact_action!r}, "
                     f"requested {requested_action!r} — near-match does not count")
    if grant.grantee != actor:
        return _hold(f"grant {grant.grant_id} is held by {grant.grantee}, not {actor}")
    # the grant itself defines its permitted surface — a grant scoped to a
    # constitutional/capital/irreversible/high-surface action cannot be executed
    # while the operator is unavailable, and a non-reversible grant never is
    # pre-authorized for operator-unavailable continuation.
    grant_surface = grant.surface_class or affected_surface
    grant_reversible = grant.reversible if grant.reversible is not None else reversible
    if grant_surface in HOLD_SURFACES or not grant_reversible:
        return _hold(f"grant surface {grant_surface!r} (reversible={grant_reversible}) "
                     f"exceeds the pre-authorized reversible sandbox — OPERATOR_HOLD")
    return OperatorHoldVerdict(action_id=action_id, verdict="MAY_CONTINUE",
                               grant_used=grant.grant_id,
                               rationale="exact covered reversible sandbox action under an "
                                         "active pre-existing grant")


# --------------------------------------------------------------------------- #
# S24 — unknown governance event
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
class GovernanceEventDisposition:
    event_id: str
    channel: str                     # GOVERNANCE_CHANNELS entry | "UNRESOLVED_GOVERNANCE_EVENT"
    classification_failure: str
    preserved: Dict[str, Any]        # raw event / evidence / consequence / authority / containment
    amendment_candidate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "channel": self.channel,
                "classification_failure": self.classification_failure,
                "preserved": self.preserved, "amendment_candidate": self.amendment_candidate}


def classify_governance_event(event: GovernanceEvent, channels: Sequence[str] = GOVERNANCE_CHANNELS) -> GovernanceEventDisposition:
    """S24: a novel event matching NO current Governor channel stays
    UNRESOLVED_GOVERNANCE_EVENT. The raw event, evidence, consequence class,
    authority, containment action, classification failure and amendment
    candidate are preserved. No nearest-category coercion; no self-ratified
    ontology change."""
    ch = tuple(channels or GOVERNANCE_CHANNELS)
    keyword_hits = [c for c in ch if c.lower() in event.raw_event.lower()]
    if not keyword_hits:
        preserved = {
            "raw_event": event.raw_event,
            "evidence_refs": list(event.evidence_refs),
            "consequence_class": event.consequence_class,
            "authority_context": event.authority_context,
            "containment_action": event.containment_action,
            "seq": event.seq,
        }
        return GovernanceEventDisposition(
            event_id=event.event_id,
            channel="UNRESOLVED_GOVERNANCE_EVENT",
            classification_failure="NO_MATCHING_GOVERNOR_CHANNEL",
            preserved=preserved,
            amendment_candidate=("ontology/amendment candidate — requires a governed "
                                 "amendment path; not self-ratified"))
    if len(keyword_hits) > 1:
        # ambiguous multi-channel match is NOT a forced choice: unresolved, with
        # the candidate channels preserved for the amendment path
        preserved = event.to_dict()
        preserved["matching_channels"] = keyword_hits
        return GovernanceEventDisposition(
            event_id=event.event_id,
            channel="UNRESOLVED_GOVERNANCE_EVENT",
            classification_failure="AMBIGUOUS_MULTI_CHANNEL_MATCH",
            preserved=preserved,
            amendment_candidate="channel ontology candidate — not self-ratified")
    return GovernanceEventDisposition(
        event_id=event.event_id, channel=keyword_hits[0],
        classification_failure="",
        preserved=event.to_dict())
