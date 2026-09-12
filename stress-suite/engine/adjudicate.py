"""EvidenceAdjudicator — generic test-policy layer (G2 §3-§6, G2R-01/G2R-06).

The G1 harness validated phase TOPOLOGY but deliberately did not decide WHY a
transition should occur. This module adds a PROVISIONAL_SCENARIO_TEST_POLICY
layer that proposes a next phase (or HOLD) from evidence.

Hard rules of this layer:

  * The adjudicator NEVER mutates the phase machine. It returns a PhaseProposal;
    application is exclusively the GovernedTransitionExecutor's job (G2 §3).
  * No scenario-ID branches and no expected-trace knowledge exist here. The
    policy is declarative predicates keyed on evidence-channel grades,
    persistence, dependency centrality, patch pressure, structural level,
    derived causal-signature recurrence, lineage diversity, data-quality
    blockers, prior review history, and explicit resolution conditions. A rule
    fires purely from observable evidence.
  * G2R-01: the SHARED core policy must be expressible without scenario
    literals — literal signatures/scopes/mechanism names may live in evidence
    provenance but never in transition predicates.
  * Non-scalar: proposals are driven by gates (all_of / any_of / persistence /
    dependency / patch / lineage). No aggregated numeric score carries authority.
  * Frozen contract: the PhaseEvaluationContract must already be frozen when the
    adjudicator runs; rules may not change mid evaluation. Mid-run modification
    fails closed.
  * G2R-06: the evaluation contract is FULLY semantic. Structured
    hysteresis_rules participate (minimum-persistence floors per phase family;
    `stronger_than_watch` and `recovery.independent_exit_predicate` are
    VALIDATED, not decorative prose); a non-empty admissible_phase_transitions
    list is enforceable: an M5-legal edge outside the contract is never
    proposed (CONTRACT_INADMISSIBLE hold, recorded).
  * Fail-closed grades: only LOW / MEDIUM / HIGH are canonical here. An unknown
    grade raises PolicyError.

Grades: LOW < MEDIUM < HIGH. Any other grade in a rule or observation raises.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import PROVISIONAL, deterministic_hex
from .evalcontract import PhaseEvaluationContract

CANONICAL_GRADES = ("LOW", "MEDIUM", "HIGH")
GRADE_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# review depth per phase, used for generic hysteresis: once the institution is at
# review depth D, proposals to phases SHALLOWER than D are skipped unless the
# target is a recovery outcome (STABLE / NO_CHANGE / HOMEOSTATIC_REPAIR). This
# is topology-adjacent but evidence-agnostic.
PHASE_DEPTH = {
    "STABLE": 0,
    "WATCH": 1,
    "DATA_BLOCKED": 1,
    "ESCALATION_REVIEW": 2,
    "HOMEOSTATIC_REPAIR": 2,
    "NO_CHANGE": 2,
    "OPERATOR_HOLD": 2,
    "AUTHORITY_BLOCKED": 2,
    "TRANSFORMATION_CANDIDATE": 3,
    "TRANSFORMATION_WINDOW": 4,
    "RECONSOLIDATION": 5,
    "NEW_STABLE": 6,
    "ROLLBACK": 6,
    "PLURAL_MODEL_STATE": 6,
    "UNRESOLVED": 6,
}
RECOVERY_TARGETS = ("STABLE", "NO_CHANGE", "HOMEOSTATIC_REPAIR")

# structural level ordering for patch escalation (L1 impl < ... < L6 architecture)
STRUCTURAL_LEVEL_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6}

# phase family -> evaluation-contract hysteresis key (G2R-06 wiring)
HYSTERESIS_FAMILY = {
    "WATCH": "watch",
    "ESCALATION_REVIEW": "escalation",
    "HOMEOSTATIC_REPAIR": "escalation",
    "TRANSFORMATION_CANDIDATE": "transformation",
    "TRANSFORMATION_WINDOW": "transformation",
    "RECONSOLIDATION": "transformation",
}
#: targets treated as recovery outcomes for the independent_exit_predicate rule
#: (HOMEOSTATIC_REPAIR is an escalation-family ACTION, not an exit predicate)
HYSTERESIS_RECOVERY_TARGETS = ("STABLE", "NO_CHANGE",
                               "NEW_STABLE", "PLURAL_MODEL_STATE", "ROLLBACK", "UNRESOLVED")

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

_VALID_HYSTERESIS_KEYS = {  # per family
    "watch": {"minimum_persistence", "entry_bar_below_escalation"},
    "escalation": {"minimum_persistence"},
    "transformation": {"minimum_persistence", "stronger_than_watch"},
    "recovery": {"independent_exit_predicate"},
}


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


def _grade_or_raise(grade, where, what="grade") -> str:
    if grade is None:
        raise PolicyError(f"{where}: {what} is required here")
    return _check_grade(grade, where)


@dataclass(frozen=True)
class PredicateGate:
    """One channel predicate. `grade` may be None to inherit the threshold of the
    FROZEN evaluation contract (G2 §7 wiring); `op` is gte (>=) or eq (==).
    Grades are canonical LOW/MEDIUM/HIGH only; unknown grades fail closed."""

    channel: str
    grade: Optional[str] = None    # None => inherit frozen-contract threshold
    op: str = "gte"               # gte | eq

    @classmethod
    def from_data(cls, data: Mapping[str, Any], where: str) -> "PredicateGate":
        raw = dict(data)
        if "channel" not in raw:
            nonop = {k: v for k, v in raw.items() if k != "op"}
            if len(nonop) != 1:
                raise PolicyError(f"{where}: gate must name exactly one channel")
            (channel, grade), = nonop.items()
            op = raw.get("op", "gte")
        else:
            channel = raw.get("channel", "")
            grade = raw.get("grade")
            op = raw.get("op", "gte")
        gate = cls(
            channel=_check_channel(channel, where),
            grade=_check_grade(grade, where) if grade is not None else None,
            op=op,
        )
        if gate.op not in ("gte", "eq"):
            raise PolicyError(f"{where}: unknown op {gate.op!r}; use gte or eq")
        return gate


@dataclass(frozen=True)
class AdjudicatorRule:
    """One declarative transition/hold predicate.

    A rule matches when ALL all_of gates meet, ANY any_of gate meets (empty = no
    requirement), the persistence window holds, dependency/patch/affected
    modifiers pass, lineage/resolution/current-depth gates pass, and none of
    `hold_when` labels appear in the latest observation.
    """

    rule_id: str
    to_state: str = ""
    hold: bool = False
    hold_when: Tuple[str, ...] = ()
    all_of: Tuple[PredicateGate, ...] = ()
    any_of: Tuple[PredicateGate, ...] = ()
    persistence: Optional[Mapping[str, Any]] = None      # {channel, grade, minimum_observations}
    prior: Optional[Mapping[str, Any]] = None            # {channel, grade, within, count, clean_labels?}
    dependency: Optional[Mapping[str, Any]] = None       # {min_centrality, requires_stronger_review}
    patch: Optional[Mapping[str, Any]] = None            # {structural_level|max_structural_level, causal_signature, min_recurrence}
    affected: Optional[Mapping[str, Any]] = None         # {max_level, scope} for leaf-vs-structural gating
    lineage_min_distinct: int = 0                        # G2R §5 — ≥N distinct source lineages
    resolution_required: str = ""                        # G2R-10/AMB-13 — explicit resolution condition kind
    min_current_depth: int = 0                           # generic depth bounds (0 = no bound)
    max_current_depth: int = 0
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
            prior=_freeze_map(data.get("prior"), where),
            dependency=_freeze_map(data.get("dependency"), where),
            patch=_freeze_map(data.get("patch"), where),
            affected=_freeze_map(data.get("affected"), where),
            lineage_min_distinct=int(data.get("lineage_min_distinct", 0)),
            resolution_required=str(data.get("resolution_required", "")),
            min_current_depth=int(data.get("min_current_depth", 0)),
            max_current_depth=int(data.get("max_current_depth", 0)),
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
    for key in ("structural_level", "max_structural_level"):
        if key in out and out[key] is not None and out[key] not in STRUCTURAL_LEVEL_RANK:
            raise PolicyError(f"{where}: unknown structural level {out[key]!r}")
    if "max_level" in out:
        if out["max_level"] not in STRUCTURAL_LEVEL_RANK:
            raise PolicyError(f"{where}: unknown affected max_level {out['max_level']!r}")
    if "channel" in out:
        out["channel"] = _check_channel(out["channel"], where)
    if "clean_labels" in out:
        out["clean_labels"] = [str(x) for x in out["clean_labels"]]
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
                    "all_of": [{"channel": g.channel, "grade": g.grade, "op": g.op} for g in r.all_of],
                    "any_of": [{"channel": g.channel, "grade": g.grade, "op": g.op} for g in r.any_of],
                    "persistence": dict(r.persistence) if r.persistence else None,
                    "prior": dict(r.prior) if r.prior else None,
                    "dependency": dict(r.dependency) if r.dependency else None,
                    "patch": dict(r.patch) if r.patch else None,
                    "affected": dict(r.affected) if r.affected else None,
                    "lineage_min_distinct": r.lineage_min_distinct,
                    "resolution_required": r.resolution_required,
                    "min_current_depth": r.min_current_depth,
                    "max_current_depth": r.max_current_depth,
                    "mutation_class": r.mutation_class,
                    "review_authority": r.review_authority,
                    "rationale": r.rationale,
                }
                for r in self.rules
            ],
        }

    def fingerprint(self) -> str:
        """Deterministic policy fingerprint (G2R-11: recorded per transition)."""
        return deterministic_hex("policy", self.policy_id, self.version_tag,
                                 self.authority_basis, self.to_dict(), length=24)


@dataclass(frozen=True)
class EvidenceObservation:
    """One period's observable evidence. Holds no hidden ground truth and no
    scenario expectations — only what a decision role could observe."""

    seq: int
    vector: Mapping[str, str]
    evidence_refs: Tuple[str, ...] = ()
    lineage_labels: Tuple[str, ...] = ()
    lineage: Optional[Mapping[str, Any]] = None   # registry-derived NON-SCALAR support (G2R §5)
    resolution_kinds: Tuple[str, ...] = ()        # explicit resolution conditions from the registry (AMB-13)
    patch: Optional[Mapping[str, Any]] = None     # structural_level / causal_signature / DERIVED recurrence
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
    admissible: bool = True                      # evaluation-contract admissibility (G2R-06)
    contract_inadmissible_reason: str = ""


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
        _validate_contract_semantics(contract, policy)
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
                rationale = rule.rationale or f"hold: blocker observed for {rule.rule_id}"
                if latest.lineage:
                    rationale += f" [lineage={_lineage_dict(latest.lineage)}]"
                return PhaseProposal(
                    rule_id=rule.rule_id, action="HOLD", rationale=rationale,
                )
        # pass 2: transition rules in policy order. hold_when-only rules are
        # NOT re-evaluated here (their sole trigger is pass 1).
        for rule in self.policy.rules:
            if rule.hold_when:
                continue
            # hysteresis guards: (1) never propose the phase we are ALREADY in
            # (no topology self-loops); (2) never propose regressing below the
            # current review depth, except to a recovery outcome; (3) current
            # depth bounds (e.g. NO_CHANGE is an ESCALATION_REVIEW-depth outcome).
            if not rule.hold and rule.to_state:
                if rule.to_state == current_phase:
                    continue
                target_depth = PHASE_DEPTH.get(rule.to_state, 2)
                current_depth = PHASE_DEPTH.get(current_phase, 2)
                if target_depth < current_depth and rule.to_state not in RECOVERY_TARGETS:
                    continue
                if rule.min_current_depth and current_depth < rule.min_current_depth:
                    continue
                if rule.max_current_depth and current_depth > rule.max_current_depth:
                    continue
            if self._matches(rule):
                if rule.hold:
                    return PhaseProposal(
                        rule_id=rule.rule_id, action="HOLD",
                        rationale=rule.rationale or "hold under " + rule.rule_id,
                    )
                refs = self._latest_refs()
                admissible, inadmissible_reason = self._admissible(current_phase, rule.to_state)
                if not admissible:
                    # G2R-06: an M5-legal edge outside the frozen contract is
                    # never proposed for application; recorded as a hold so the
                    # trace explains exactly why.
                    return PhaseProposal(
                        rule_id="CONTRACT_INADMISSIBLE", action="HOLD",
                        rationale=inadmissible_reason,
                        evidence_refs=refs,
                    )
                return PhaseProposal(
                    rule_id=rule.rule_id, action="TRANSITION", to_state=rule.to_state,
                    rationale=rule.rationale or f"evidence satisfied {rule.rule_id}",
                    evidence_refs=refs,
                    mutation_class=rule.mutation_class,
                    review_authority=rule.review_authority,
                    admissible=True,
                )
        # nothing fires: stay put (hysteresis: absence of sufficient evidence is not
        # a reason to escalate; staying on the current phase is the default)
        return PhaseProposal(rule_id="NO_MATCH", action="HOLD", rationale="no rule fired; hold phase")

    # ------------------------------------------------------------------ #
    def _admissible(self, current_phase: str, to_state: str) -> Tuple[bool, str]:
        allowed = self.contract.admissible_phase_transitions  # frozen tuple of pairs
        if not allowed:
            return True, ""
        for frm, to in allowed:
            if frm == current_phase and to == to_state:
                return True, ""
        return False, (
            f"contract inadmissible: {current_phase} -> {to_state} is outside "
            f"the frozen evaluation contract's admissible_phase_transitions"
        )

    def _latest_refs(self) -> Tuple[str, ...]:
        return self._observations[-1].evidence_refs

    def _matches(self, rule: AdjudicatorRule) -> bool:
        latest = self._observations[-1]
        vec = latest.vector

        for gate in rule.all_of:
            if not self._gate_ok(gate, vec, rule.rule_id):
                return False
        if rule.any_of:
            if not any(self._gate_ok(g, vec, rule.rule_id) for g in rule.any_of):
                return False

        if rule.persistence:
            if not self._persistence_ok(rule):
                return False
        else:
            floor = self._contract_persistence_floor(rule.to_state)
            if floor and len(self._observations) < floor:
                return False

        if rule.prior:
            if not self._prior_ok(rule):
                return False

        if rule.dependency and not self._dependency_ok(rule, vec, latest):
            return False

        if rule.patch and not self._patch_ok(rule, latest):
            return False

        if rule.affected and not self._affected_ok(rule, latest):
            return False

        if rule.lineage_min_distinct and not self._lineage_ok(rule, latest):
            return False

        if rule.resolution_required:
            if rule.resolution_required not in latest.resolution_kinds:
                return False

        return True

    # ------------------------------------------------------------------ #
    def _gate_ok(self, gate: PredicateGate, vec: Mapping[str, str], rule_id: str) -> bool:
        """Satisfy a gate, inheriting the grade from the frozen evaluation
        contract when the gate carries none (G2 §7 wiring)."""
        if gate.channel not in vec:
            return False
        observed = _check_grade(vec[gate.channel], rule_id)
        required = gate.grade
        if required is None:
            required = self._contract_threshold(gate.channel, rule_id)
        required = _check_grade(required, rule_id)
        if gate.op == "eq":
            return observed == required
        return GRADE_RANK[observed] >= GRADE_RANK[required]

    def _contract_threshold(self, channel: str, rule_id: str) -> str:
        rules = self.contract.channel_rules   # frozen mapping; safe to read
        if channel not in rules or "threshold" not in rules[channel]:
            raise PolicyError(
                f"{rule_id}: gate {channel!r} has no grade and the evaluation "
                f"contract defines no threshold for it"
            )
        return rules[channel]["threshold"]

    def _contract_persistence_floor(self, to_state: str) -> int:
        """G2R-06: structured hysteresis minimum_persistence for the target's
        phase family participates in every rule that lacks an explicit
        persistence block (history-length floor — the institution must have
        observed the episode for at least that many periods)."""
        family = HYSTERESIS_FAMILY.get(to_state, "")
        if not family:
            return 0
        rules = self.contract.hysteresis_rules or {}
        entry = rules.get(family) or {}
        if not isinstance(entry, dict):
            raise PolicyError(f"hysteresis entry for {family!r} must be a structured dict")
        return int(entry.get("minimum_persistence", 0) or 0)

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
            return False
        for obs in self._observations[-minimum:]:
            if channel not in obs.vector or not meets(obs.vector[channel], grade, rule.rule_id):
                return False
        return True

    def _prior_ok(self, rule: AdjudicatorRule) -> bool:
        """History evidence: within the last `within` observations (including the
        latest), at least `count` observations must show channel >= grade -- and
        (G2R-01/S02) none of those qualifying observations may carry a hold label
        listed in `clean_labels`: a resolution cannot ride on a defunct episode
        (e.g. data-quality-defective contradiction)."""
        pr = rule.prior or {}
        channel = _check_channel(str(pr["channel"]), rule.rule_id)
        grade = _grade_or_raise(pr.get("grade"), rule.rule_id, "prior.grade")
        within = int(pr.get("within", 1))
        count = int(pr.get("count", 1))
        clean_labels = list(pr.get("clean_labels", []) or [])
        if within < 1 or count < 1:
            raise PolicyError(f"{rule.rule_id}: prior within/count must be >= 1")
        window = self._observations[-within:]
        hits = 0
        for obs in window:
            if channel in obs.vector and meets(obs.vector[channel], grade, rule.rule_id):
                if clean_labels and any(h in obs.holds for h in clean_labels):
                    return False       # qualifying episode was sullied by a blocker
                hits += 1
        return hits >= count

    def _dependency_ok(self, rule: AdjudicatorRule, vec: Mapping[str, str], _latest) -> bool:
        d = rule.dependency or {}
        min_centrality = d.get("min_centrality", "HIGH")
        requires_stronger_review = bool(d.get("requires_stronger_review", False))
        # G2R-01: centrality is a rigor MODULATOR. When the observation carries no
        # centrality claim at all, there is nothing to modulate and the gate is
        # satisfied. A PRESENT-but-low centrality still denies (rigour).
        if "dependency_centrality" not in vec:
            return True
        central = vec["dependency_centrality"]
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
        min_level = pr.get("structural_level")
        max_level = pr.get("max_structural_level")
        min_recurrence = int(pr.get("min_recurrence", 1))
        signature = pr.get("causal_signature")
        patch = latest.patch
        if not patch:
            return False
        if signature is not None and patch.get("causal_signature") != signature:
            return False
        # G2R-03: recurrence is always the DERIVED value (the runner overwrites
        # caller-supplied recurrence from the exact-signature event history).
        if int(patch.get("recurrence", 0)) < min_recurrence:
            return False
        actual = patch.get("structural_level")
        if actual not in STRUCTURAL_LEVEL_RANK and (min_level or max_level):
            return False  # no structural claim -> cannot satisfy a structural gate
        if min_level is not None and STRUCTURAL_LEVEL_RANK[actual] < STRUCTURAL_LEVEL_RANK[min_level]:
            return False
        if max_level is not None and STRUCTURAL_LEVEL_RANK[actual] > STRUCTURAL_LEVEL_RANK[max_level]:
            return False
        return True

    def _affected_ok(self, rule: AdjudicatorRule, latest: EvidenceObservation) -> bool:
        af = rule.affected or {}
        max_level = af.get("max_level")
        scope = af.get("scope")
        obs_af = latest.affected
        if not obs_af:
            return False
        # scope is provenance-only; a predicate may never test a literal scope
        if scope is not None and obs_af.get("scope") != scope:
            return False
        if max_level is not None:
            lvl = obs_af.get("level")
            if lvl not in STRUCTURAL_LEVEL_RANK:
                return False
            if STRUCTURAL_LEVEL_RANK[lvl] > STRUCTURAL_LEVEL_RANK[max_level]:
                return False
        return True

    def _lineage_ok(self, rule: AdjudicatorRule, latest: EvidenceObservation) -> bool:
        """G2R §5: independent confirmation must expose MULTIPLE DISTINCT
        lineages. The registry-derived lineage summary is authoritative when
        present; a raw label count is the fallback for unbound unit tests."""
        if latest.lineage is not None:
            distinct = int(latest.lineage.get("distinct_source_lineages", 0))
            raw = int(latest.lineage.get("raw_evidence_count", 0))
        else:
            distinct = len({l for l in latest.lineage_labels})
            raw = len(latest.evidence_refs)
        if distinct < max(rule.lineage_min_distinct, 1):
            return False
        if raw < 1:
            return False
        return True

    def _hold_rationale_for(self, rule: AdjudicatorRule, latest: EvidenceObservation) -> str:
        parts = [rule.rationale or f"hold under {rule.rule_id}"]
        if latest.lineage:
            parts.append(f"lineage={_lineage_dict(latest.lineage)}")
        return "; ".join(str(p) for p in parts if p)


def _lineage_dict(lineage: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "raw": int(lineage.get("raw_evidence_count", 0)),
        "sources": int(lineage.get("distinct_source_lineages", 0)),
        "models": int(lineage.get("distinct_model_lineages", 0)),
    }


def _validate_contract_semantics(contract: PhaseEvaluationContract, policy: AdjudicatorPolicy) -> None:
    """G2R-06: hysteresis_rules must be STRUCTURED and participate; prose as an
    allegedly-executable rule fails closed; recovery targets must have an
    independent (equality) exit predicate; transformation must be stronger than
    watch. A non-empty admissible list is enforced at propose() time."""
    hyst = contract.hysteresis_rules
    if hyst:
        if not isinstance(hyst, Mapping):
            raise PolicyError("evaluation contract hysteresis_rules must be a dict")
        for family, entry in hyst.items():
            if family not in _VALID_HYSTERESIS_KEYS:
                raise PolicyError(
                    f"hysteresis family {family!r} unknown; structured keys: {sorted(_VALID_HYSTERESIS_KEYS)}"
                )
            if not isinstance(entry, dict):
                raise PolicyError(
                    f"hysteresis {family!r} must be a STRUCTURED dict, not prose "
                    f"({entry!r}) — human prose cannot be an executable rule"
                )
            unknown = set(entry) - _VALID_HYSTERESIS_KEYS[family]
            if unknown:
                raise PolicyError(f"hysteresis {family!r} carries unknown keys {sorted(unknown)}")
        recovery_cfg = hyst.get("recovery") or {}
        if recovery_cfg.get("independent_exit_predicate"):
            for rule in policy.rules:
                if rule.hold:
                    continue
                if rule.to_state in HYSTERESIS_RECOVERY_TARGETS:
                    has_eq = any(g.op == "eq" for g in rule.all_of) or any(
                        g.op == "eq" for g in rule.any_of
                    )
                    if not has_eq:
                        raise PolicyError(
                            f"{rule.rule_id}: recovery target {rule.to_state!r} requires an "
                            f"equality (independent) exit predicate under the evaluation contract"
                        )
        trans_cfg = hyst.get("transformation") or {}
        if trans_cfg.get("stronger_than_watch"):
            floor_t = int(trans_cfg.get("minimum_persistence", 0) or 0)
            floor_e = int((hyst.get("escalation") or {}).get("minimum_persistence", 0) or 0)
            if floor_t and floor_e and floor_t < floor_e:
                raise PolicyError(
                    "transformation persistence floor must not be below the escalation floor "
                    "(stronger_than_watch)"
                )


def _check_observation(obs: EvidenceObservation) -> None:
    for ch, grade in obs.vector.items():
        _check_channel(ch, f"observation {obs.seq}")
        _check_grade(grade, f"observation {obs.seq}")
    if obs.patch:
        level = obs.patch.get("structural_level")
        if level is not None and level not in STRUCTURAL_LEVEL_RANK:
            raise PolicyError(f"observation {obs.seq}: unknown structural_level {level!r}")