"""EvidenceAdjudicator — generic test-policy layer (G2 §3-§6).

The G1 harness validated phase TOPOLOGY but deliberately did not decide WHY a
transition should occur. This module adds a PROVISIONAL_SCENARIO_TEST_POLICY
layer that proposes a next phase (or HOLD) from evidence.

Hard rules of this layer:

  * The adjudicator NEVER mutates the phase machine. It returns a PhaseProposal;
    application is exclusively the GovernedTransitionExecutor's job (G2 §3).
  * No scenario-ID branches and no expected-trace knowledge exist here. The
    policy is declarative predicates keyed on evidence-channel grades,
    persistence, dependency centrality, and patch pressure. A rule fires purely
    from observable evidence.
  * Non-scalar: proposals are driven by gates (all_of / any_of / persistence /
    dependency / patch). No aggregated numeric score carries authority.
  * Frozen contract: the PhaseEvaluationContract must already be frozen when the
    adjudicator runs; rules may not change mid evaluation. Mid-run modification
    fails closed.
  * Fail-closed grades: only LOW / MEDIUM / HIGH are canonical here (consistent
    with EvidenceChannelVector). An unknown grade raises PolicyError instead of
    guessing, so a scenario cannot smuggle a novel grade past the gates.

Grades: LOW < MEDIUM < HIGH. Any other grade in a rule or observation raises.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import PROVISIONAL
from .evalcontract import PhaseEvaluationContract

CANONICAL_GRADES = ("LOW", "MEDIUM", "HIGH")
GRADE_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# structural level ordering for patch escalation (L1 impl < ... < L6 architecture)
STRUCTURAL_LEVEL_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6}

# dependency-centrality vocabulary used by rules (vector grades reuse canonical)
CENTRALITY_LEVELS = ("LOW", "MEDIUM", "HIGH")

# canonical evidence channel names (must match EvidenceChannel values)
CHANNELS = (
    "reliability_degradation",
    "exception_burden",
    "independent_contradiction",
    "unresolved_pattern_density",
    "dependency_centrality",
    "external_environment_shift",
    "opportunity_cost_of_stability",
    "cost_and_reversibility",
)


class PolicyError(ValueError):
    pass


def _check_grade(grade: str, where: str) -> str:
    if grade not in CANONICAL_GRADES:
        raise PolicyError(
            f"{where}: unknown grade {grade!r}; canonical grades are {CANONICAL_GRADES}"
        )
    return grade


def _check_channel(channel: str, where: str) -> str:
    if channel not in CHANNELS:
        raise PolicyError(f"{where}: unknown evidence channel {channel!r}")
    return channel


def meets(observed: str, required: str, where: str) -> bool:
    """observed >= required under canonical ordering; unknown grades fail closed."""
    return GRADE_RANK[_check_grade(observed, where)] >= GRADE_RANK[_check_grade(required, where)]


@dataclass(frozen=True)
class PredicateGate:
    channel: str
    grade: str

    @classmethod
    def from_data(cls, data: Mapping[str, Any], where: str) -> "PredicateGate":
        raw = dict(data)
        if "channel" not in raw and len(raw) == 1:
            # shorthand: {"reliability_degradation": "HIGH"}
            (channel, grade), = raw.items()
        else:
            channel = raw.get("channel", "")
            grade = raw.get("grade", "")
        return cls(
            channel=_check_channel(channel, where),
            grade=_check_grade(grade, where),
        )


@dataclass(frozen=True)
class AdjudicatorRule:
    """One declarative transition/hold predicate.

    A rule matches when ALL all_of gates meet, ANY any_of gate meets (empty = no
    requirement), the persistence window holds, dependency/patch modifiers pass,
    and none of `hold_when` labels appear in the latest observation.
    """

    rule_id: str
    to_state: str = ""
    hold: bool = False
    hold_when: Tuple[str, ...] = ()
    all_of: Tuple[PredicateGate, ...] = ()
    any_of: Tuple[PredicateGate, ...] = ()
    persistence: Optional[Mapping[str, Any]] = None      # {channel, grade, minimum_observations}
    dependency: Optional[Mapping[str, Any]] = None       # {min_centrality, requires_stronger_review}
    patch: Optional[Mapping[str, Any]] = None            # {structural_level, causal_signature, min_recurrence}
    mutation_class: str = "READ_ONLY"
    review_authority: str = ""
    rationale: str = ""

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "AdjudicatorRule":
        where = f"rule {data.get('rule_id', '?')}"
        return cls(
            rule_id=str(data["rule_id"]),
            to_state=str(data.get("to_state", "")),
            hold=bool(data.get("hold", False)),
            hold_when=tuple(str(h) for h in data.get("hold_when", [])),
            all_of=tuple(PredicateGate.from_data(g, where) for g in data.get("all_of", [])),
            any_of=tuple(PredicateGate.from_data(g, where) for g in data.get("any_of", [])),
            persistence=_freeze_map(data.get("persistence"), where),
            dependency=_freeze_map(data.get("dependency"), where),
            patch=_freeze_map(data.get("patch"), where),
            mutation_class=str(data.get("mutation_class", "READ_ONLY")),
            review_authority=str(data.get("review_authority", "")),
            rationale=str(data.get("rationale", "")),
        )


def _freeze_map(value, where):
    if value is None:
        return None
    out = dict(value)
    if "grade" in out:
        out["grade"] = _check_grade(out["grade"], where)
    if "min_centrality" in out:
        out["min_centrality"] = _check_grade(out["min_centrality"], where)
    if "structural_level" in out:
        out["structural_level"] = out["structural_level"]
    if "channel" in out:
        out["channel"] = _check_channel(out["channel"], where)
    return out


@dataclass(frozen=True)
class AdjudicatorPolicy:
    """Versioned rule set. Explicitly a PROVISIONAL_SCENARIO_TEST_POLICY, not
    constitutional truth (A-010 defines no universal thresholds)."""

    policy_id: str
    version_tag: str = "V1"
    status: str = PROVISIONAL
    authority_basis: str = ""
    rules: Tuple[AdjudicatorRule, ...] = ()

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "AdjudicatorPolicy":
        return cls(
            policy_id=str(data["policy_id"]),
            version_tag=str(data.get("version_tag", "V1")),
            status=str(data.get("status", PROVISIONAL)),
            authority_basis=str(data.get("authority_basis", "")),
            rules=tuple(AdjudicatorRule.from_data(r) for r in data.get("rules", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version_tag": self.version_tag,
            "status": self.status,
            "authority_basis": self.authority_basis,
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "to_state": r.to_state,
                    "hold": r.hold,
                    "hold_when": list(r.hold_when),
                    "all_of": [{"channel": g.channel, "grade": g.grade} for g in r.all_of],
                    "any_of": [{"channel": g.channel, "grade": g.grade} for g in r.any_of],
                    "persistence": dict(r.persistence) if r.persistence else None,
                    "dependency": dict(r.dependency) if r.dependency else None,
                    "patch": dict(r.patch) if r.patch else None,
                    "mutation_class": r.mutation_class,
                    "review_authority": r.review_authority,
                    "rationale": r.rationale,
                }
                for r in self.rules
            ],
        }


@dataclass(frozen=True)
class EvidenceObservation:
    """One period's observable evidence. Holds no hidden ground truth and no
    scenario expectations — only what a decision role could observe."""

    seq: int
    vector: Mapping[str, str]
    evidence_refs: Tuple[str, ...] = ()
    lineage_labels: Tuple[str, ...] = ()
    patch: Optional[Mapping[str, Any]] = None     # structural_level / causal_signature / recurrence
    affected: Optional[Mapping[str, Any]] = None  # scope / level
    holds: Tuple[str, ...] = ()                   # observable blockers (e.g. data-quality defect)


@dataclass(frozen=True)
class PhaseProposal:
    rule_id: str
    action: str            # TRANSITION | HOLD
    to_state: str = ""     # target only for TRANSITION
    rationale: str = ""
    evidence_refs: Tuple[str, ...] = ()
    mutation_class: str = "READ_ONLY"
    review_authority: str = ""


class EvidenceAdjudicator:
    """Pure evidence -> proposal function. Holds observation history; proposes a
    next phase (or HOLD) by evaluating the frozen policy; never mutates the
    phase machine (application belongs to the governed executor)."""

    def __init__(self, policy: AdjudicatorPolicy, contract: PhaseEvaluationContract):
        if not contract.is_frozen():
            raise PolicyError(
                "evaluation contract must be FROZEN before adjudication begins; "
                "mid-run modification must fail"
            )
        self.policy = policy
        self.contract = contract
        self._observations: List[EvidenceObservation] = []

    @property
    def observation_count(self) -> int:
        return len(self._observations)

    def observe(self, obs: EvidenceObservation) -> None:
        _check_observation(obs)
        self._observations.append(obs)

    def propose(self, current_phase: str = "") -> PhaseProposal:
        if not self._observations:
            return PhaseProposal(rule_id="NO_EVIDENCE", action="HOLD", rationale="no observations yet")
        latest = self._observations[-1]
        # pass 1: hold_when blockers override every transition (e.g. a
        # data-quality defect parks escalation regardless of other channels)
        for rule in self.policy.rules:
            if rule.hold_when and any(h in latest.holds for h in rule.hold_when):
                return PhaseProposal(
                    rule_id=rule.rule_id, action="HOLD",
                    rationale=rule.rationale or f"hold: blocker observed for {rule.rule_id}",
                )
        # pass 2: transition rules in policy order
        for rule in self.policy.rules:
            # hysteresis guard: never propose a transition to the phase the
            # institution is ALREADY in (topology has no self-loops; firing
            # one would only produce a forbidden attempt). Pure hold rules are
            # phase-agnostic and still apply.
            if not rule.hold and rule.to_state and rule.to_state == current_phase:
                continue
            if self._matches(rule):
                if rule.hold:
                    return PhaseProposal(
                        rule_id=rule.rule_id, action="HOLD",
                        rationale=rule.rationale or "hold under " + rule.rule_id,
                    )
                refs = self._latest_refs()
                return PhaseProposal(
                    rule_id=rule.rule_id, action="TRANSITION", to_state=rule.to_state,
                    rationale=rule.rationale or f"evidence satisfied {rule.rule_id}",
                    evidence_refs=refs,
                    mutation_class=rule.mutation_class,
                    review_authority=rule.review_authority,
                )
        # nothing fires: stay put (hysteresis: absence of sufficient evidence is not
        # a reason to escalate; staying on the current phase is the default)
        return PhaseProposal(rule_id="NO_MATCH", action="HOLD", rationale="no rule fired; hold phase")

    # ------------------------------------------------------------------ #
    def _latest_refs(self) -> Tuple[str, ...]:
        return self._observations[-1].evidence_refs

    def _matches(self, rule: AdjudicatorRule) -> bool:
        latest = self._observations[-1]
        vec = latest.vector

        for gate in rule.all_of:
            if gate.channel not in vec:
                return False
            if not meets(vec[gate.channel], gate.grade, rule.rule_id):
                return False
        if rule.any_of:
            hit = False
            for gate in rule.any_of:
                if gate.channel in vec and meets(vec[gate.channel], gate.grade, rule.rule_id):
                    hit = True
                    break
            if not hit:
                return False

        if rule.persistence:
            if not self._persistence_ok(rule):
                return False

        if rule.dependency:
            if not self._dependency_ok(rule, vec, latest):
                return False

        if rule.patch:
            if not self._patch_ok(rule, latest):
                return False

        return True

    def _persistence_ok(self, rule: AdjudicatorRule) -> bool:
        p = rule.persistence or {}
        channel = p.get("channel")
        grade = p.get("grade")
        minimum = int(p.get("minimum_observations", 1))
        if channel is None or grade is None:
            raise PolicyError(f"{rule.rule_id}: persistence requires channel+grade")
        if minimum < 1:
            raise PolicyError(f"{rule.rule_id}: minimum_observations must be >= 1")
        if len(self._observations) < minimum:
            # not enough history yet: persistence cannot be satisfied (never
            # shrink the window to make a rule fire early)
            return False
        for obs in self._observations[-minimum:]:
            if channel not in obs.vector or not meets(obs.vector[channel], grade, rule.rule_id):
                return False
        return True

    def _dependency_ok(self, rule: AdjudicatorRule, vec: Mapping[str, str], _latest) -> bool:
        d = rule.dependency or {}
        min_centrality = d.get("min_centrality", "HIGH")
        requires_stronger_review = bool(d.get("requires_stronger_review", False))
        central = vec.get("dependency_centrality", "LOW")
        if not meets(central, min_centrality, rule.rule_id):
            return False
        # centrality raises rigor, never grants immunity: a stronger-review
        # dependency simply demands an extra independent-contradiction gate.
        if requires_stronger_review:
            ic = vec.get("independent_contradiction", "LOW")
            if not meets(ic, "HIGH", rule.rule_id):
                return False
        return True

    def _patch_ok(self, rule: AdjudicatorRule, latest: EvidenceObservation) -> bool:
        pr = rule.patch or {}
        required_level = pr.get("structural_level")
        min_recurrence = int(pr.get("min_recurrence", 1))
        signature = pr.get("causal_signature")
        patch = latest.patch
        if not patch:
            return False
        if signature is not None and patch.get("causal_signature") != signature:
            return False
        if int(patch.get("recurrence", 0)) < min_recurrence:
            return False
        if required_level is not None:
            if required_level not in STRUCTURAL_LEVEL_RANK:
                raise PolicyError(f"{rule.rule_id}: unknown structural_level {required_level!r}")
            actual = patch.get("structural_level")
            if actual not in STRUCTURAL_LEVEL_RANK:
                return False  # no structural claim -> cannot satisfy a structural gate
            if STRUCTURAL_LEVEL_RANK[actual] < STRUCTURAL_LEVEL_RANK[required_level]:
                return False
        return True


def _check_observation(obs: EvidenceObservation) -> None:
    for ch, grade in obs.vector.items():
        _check_channel(ch, f"observation {obs.seq}")
        _check_grade(grade, f"observation {obs.seq}")
    if obs.patch:
        level = obs.patch.get("structural_level")
        if level is not None and level not in STRUCTURAL_LEVEL_RANK:
            raise PolicyError(f"observation {obs.seq}: unknown structural_level {level!r}")