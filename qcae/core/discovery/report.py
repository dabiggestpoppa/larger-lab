"""DiscoveryReport, families and escalation queue — canon 2.7.9, 2.7.14, 2.7.15.

Block 2's terminal artifact is a report, not a verdict. Canon 2.7.4 is explicit
that a top-ranked candidate means "inspect this first" and not "acquire this",
and 2.7.16 invariant 1 repeats it for the whole ranking layer. The report's laws
encode that boundary:

- the escalation queue may only reference canonical candidates listed in the same
  report, with an explicit next action and wave (2.7.9, 2.7.14);
- a hard rejection is only representable together with a prefilter decision that
  itself required sufficient evidence strength (2.7.3);
- a stop recommendation is either CONTINUE with no satisfied stop condition, or
  STOP with at least one satisfied condition drawn from the plan's own declared
  stop rules (2.1.9) — an unexplained "stop" is not representable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, Tuple

from qcae.core.discovery.plan import (
    ContractAmendmentProposal,
    SaturationMetrics,
    StopCondition,
)
from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import (
    SerializableRecord,
    coerce_enum,
    coerce_enum_tuple,
)
from qcae.core.validation import (
    require_enum,
    require_enum_tuple,
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
    require_str_list,
)
from qcae.core.vocabulary import EVIDENCE_STRENGTH_ORDER, EvidenceClass

__all__ = [
    "CandidateFamily",
    "DiscoveryReport",
    "EscalationEntry",
    "NextAction",
    "PrefilterDecision",
    "PrefilterDecisionRecord",
    "Priority",
    "StopRecommendation",
    "StopRecommendationState",
    "make_discovery_report",
]

#: Investigation waves (canon 2.7.14): 1 = cheap/high-information, 2 = promising
#: and diverse, 3 = expensive/uncertain only if still needed.
WAVES: frozenset = frozenset({1, 2, 3})


class PrefilterDecision(StrEnum):
    """Outcome of a cheap hard prefilter (canon 2.7.3)."""

    ACCEPT = "ACCEPT"
    DEFER = "DEFER"
    REJECT = "REJECT"


class NextAction(StrEnum):
    """The next cheapest investigation step for a candidate (canon 2.7.9).

    Ranking operates on next action, not only candidate identity (2.7.8), which
    is why the queue carries an action rather than a bare score.
    """

    REPOSITORY_METADATA = "REPOSITORY_METADATA"
    SOURCE_TREE_MAP = "SOURCE_TREE_MAP"
    LICENSE_VERIFY = "LICENSE_VERIFY"
    ARTIFACT_VERIFY = "ARTIFACT_VERIFY"
    SPECIFICATION_LOOKUP = "SPECIFICATION_LOOKUP"
    DEEP_INTELLIGENCE = "DEEP_INTELLIGENCE"
    DEFER_PENDING_FAMILY = "DEFER_PENDING_FAMILY"
    REJECT_HARD_CONSTRAINT = "REJECT_HARD_CONSTRAINT"


class Priority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class StopRecommendationState(StrEnum):
    CONTINUE = "CONTINUE"
    STOP = "STOP"


@dataclass(frozen=True)
class PrefilterDecisionRecord(SerializableRecord):
    """One prefilter judgement with its evidence standing (canon 2.7.3)."""

    SCHEMA_VERSION = 1

    candidate_id: str
    prefilter_id: str
    decision: PrefilterDecision
    evidence_class: EvidenceClass
    rationale: str

    _COERCIONS = {
        "decision": lambda v: coerce_enum(v, PrefilterDecision),
        "evidence_class": lambda v: coerce_enum(v, EvidenceClass),
    }

    def validate(self) -> None:
        require_identifier(self.candidate_id, "candidate_id")
        require_identifier(self.prefilter_id, "prefilter_id")
        require_enum(self.decision, PrefilterDecision, "decision")
        require_enum(self.evidence_class, EvidenceClass, "evidence_class")
        require_non_empty_str(self.rationale, "rationale")
        # Canon 2.7.16 invariant 6: hard rejection needs strong evidence, and
        # 2.7.3 forbids acting on weak metadata. The floor for acting at all is
        # E1_DOCUMENTATION; a hard REJECT additionally needs source-grade
        # evidence (an actual LICENSE file, a manifest, a platform declaration),
        # never a README claim or a star count.
        strength = EVIDENCE_STRENGTH_ORDER.index(self.evidence_class)
        if self.decision == PrefilterDecision.REJECT and strength < EVIDENCE_STRENGTH_ORDER.index(
            EvidenceClass.E2_SOURCE
        ):
            raise QcaeValidationError(
                f"a candidate cannot be hard-rejected on {self.evidence_class.value} "
                "evidence; rejection requires source-grade evidence (canon 2.7.3, "
                "2.7.16 invariant 6)"
            )
        if strength < EVIDENCE_STRENGTH_ORDER.index(EvidenceClass.E1_DOCUMENTATION):
            raise QcaeValidationError(
                f"prefilter decisions cannot act on {self.evidence_class.value} "
                "evidence (canon 2.7.3: weak metadata cannot justify a decision)"
            )


@dataclass(frozen=True)
class CandidateFamily(SerializableRecord):
    """A cluster of lineage-related candidates (canon 2.7.6).

    Forks, thin wrappers, bindings, ports and reimplementations are grouped so
    QCAE can inspect a representative first. Membership is *not* independent
    evidence: canon 2.7.16 invariant 4 forbids treating a fork family as fully
    independent corroboration.
    """

    SCHEMA_VERSION = 1

    family_id: str
    representative_candidate_id: str
    member_candidate_ids: Tuple[str, ...]
    shared_lineage: str
    independent_family: bool = False

    _COERCIONS = {"member_candidate_ids": tuple}

    def validate(self) -> None:
        require_identifier(self.family_id, "family_id")
        require_identifier(self.representative_candidate_id, "representative_candidate_id")
        require_str_list(self.member_candidate_ids, "member_candidate_ids")
        if not self.member_candidate_ids:
            raise QcaeValidationError("a candidate family must contain at least one member")
        require_no_duplicates(self.member_candidate_ids, "member_candidate_ids")
        if self.representative_candidate_id not in self.member_candidate_ids:
            raise QcaeValidationError(
                "the family representative must be one of its members"
            )
        require_non_empty_str(self.shared_lineage, "shared_lineage")
        if not isinstance(self.independent_family, bool):
            raise QcaeValidationError("independent_family must be a bool")


@dataclass(frozen=True)
class EscalationEntry(SerializableRecord):
    """One ranked escalation-queue row (canon 2.7.9, 2.7.14)."""

    SCHEMA_VERSION = 1

    candidate_id: str
    family_id: str
    next_action: NextAction
    priority: Priority
    wave: int
    rationale: str
    score: float = 0.0
    expected_information_gain: float = 0.0
    expected_cost_units: float = 0.0
    prefilter_decision: PrefilterDecision = PrefilterDecision.ACCEPT
    deferred_pending: str = ""
    #: Per-dimension score inputs, kept so a ranking decision is auditable
    #: (canon 2.7.16 invariant 7: ranking policy is versioned and auditable).
    dimension_scores: Dict[str, float] = field(default_factory=dict)

    _COERCIONS = {
        "next_action": lambda v: coerce_enum(v, NextAction),
        "priority": lambda v: coerce_enum(v, Priority),
        "prefilter_decision": lambda v: coerce_enum(v, PrefilterDecision),
    }

    def validate(self) -> None:
        require_identifier(self.candidate_id, "candidate_id")
        require_identifier(self.family_id, "family_id")
        require_enum(self.next_action, NextAction, "next_action")
        require_enum(self.priority, Priority, "priority")
        require_enum(self.prefilter_decision, PrefilterDecision, "prefilter_decision")
        if self.wave not in WAVES:
            raise QcaeValidationError(
                f"wave must be one of {sorted(WAVES)}, got {self.wave!r} (canon 2.7.14)"
            )
        require_non_empty_str(self.rationale, "rationale")
        for name in ("expected_information_gain", "score"):
            value = getattr(self, name)
            if not (0.0 <= float(value) <= 1.0):
                raise QcaeValidationError(f"{name} must be within [0, 1], got {value!r}")
        if float(self.expected_cost_units) < 0:
            raise QcaeValidationError("expected_cost_units must be >= 0")
        if not isinstance(self.dimension_scores, dict):
            raise QcaeValidationError("dimension_scores must be a mapping")
        for name, value in self.dimension_scores.items():
            require_non_empty_str(name, "dimension_scores key")
            if not (0.0 <= float(value) <= 1.0):
                raise QcaeValidationError(
                    f"dimension_scores[{name!r}] must be within [0, 1], got {value!r}"
                )
        if self.next_action == NextAction.REJECT_HARD_CONSTRAINT:
            if self.prefilter_decision != PrefilterDecision.REJECT:
                raise QcaeValidationError(
                    "REJECT_HARD_CONSTRAINT requires a REJECT prefilter decision; a "
                    "hard rejection carries its evidence with it (canon 2.7.3)"
                )
        if self.next_action == NextAction.DEFER_PENDING_FAMILY:
            if not self.deferred_pending.strip():
                raise QcaeValidationError(
                    "DEFER_PENDING_FAMILY requires the candidate it is deferred behind"
                )
        if self.prefilter_decision == PrefilterDecision.REJECT and self.wave != 3:
            raise QcaeValidationError(
                "rejected candidates are parked in wave 3 (canon 2.7.14): they are "
                "not investigation work"
            )


@dataclass(frozen=True)
class StopRecommendation(SerializableRecord):
    """Saturation-driven stop/continue recommendation (canon 2.1.9, 2.7.14)."""

    SCHEMA_VERSION = 1

    state: StopRecommendationState
    satisfied_conditions: Tuple[StopCondition, ...] = ()
    rationale: str = ""

    _COERCIONS = {
        "state": lambda v: coerce_enum(v, StopRecommendationState),
        "satisfied_conditions": lambda v: coerce_enum_tuple(v, StopCondition),
    }

    def validate(self) -> None:
        require_enum(self.state, StopRecommendationState, "state")
        require_enum_tuple(self.satisfied_conditions, StopCondition, "satisfied_conditions")
        require_no_duplicates(self.satisfied_conditions, "satisfied_conditions")
        require_non_empty_str(self.rationale, "rationale")
        if self.state == StopRecommendationState.STOP and not self.satisfied_conditions:
            raise QcaeValidationError(
                "STOP requires at least one satisfied declared stop condition "
                "(canon 2.1.9): searching does not stop by inertia"
            )
        if self.state == StopRecommendationState.CONTINUE and self.satisfied_conditions:
            raise QcaeValidationError(
                "CONTINUE cannot report satisfied stop conditions; revise the "
                "declared rules or stop (canon 2.1.9)"
            )


@dataclass(frozen=True)
class DiscoveryReport(SerializableRecord):
    """Block 2 terminal artifact (canon 2.7.15)."""

    SCHEMA_VERSION = 1

    report_id: str
    discovery_plan_id: str
    contract_id: str
    contract_version: int
    atom_ids: Tuple[str, ...]
    internal_baseline_ref: str
    sources_searched: Tuple[SourceClass, ...]
    query_families_executed: Tuple[str, ...]
    canonical_candidate_ids: Tuple[str, ...]
    candidate_families: Tuple[CandidateFamily, ...]
    escalation_queue: Tuple[EscalationEntry, ...]
    saturation_metrics: SaturationMetrics
    stop_recommendation: StopRecommendation
    coverage_notes: Tuple[str, ...] = ()
    partial_search_notes: Tuple[str, ...] = ()
    prefilter_decisions: Tuple[PrefilterDecisionRecord, ...] = ()
    negative_findings: Tuple[str, ...] = ()
    remaining_uncertainties: Tuple[str, ...] = ()
    amendment_proposals: Tuple[ContractAmendmentProposal, ...] = ()
    created_at: str = ""
    created_by: str = ""
    policy_version: str = ""

    _COERCIONS = {
        "atom_ids": tuple,
        "sources_searched": lambda v: coerce_enum_tuple(v, SourceClass),
        "query_families_executed": tuple,
        "canonical_candidate_ids": tuple,
        "coverage_notes": tuple,
        "partial_search_notes": tuple,
        "negative_findings": tuple,
        "remaining_uncertainties": tuple,
    }

    _NESTED_RECORDS = {
        "saturation_metrics": SaturationMetrics,
        "stop_recommendation": StopRecommendation,
        "candidate_families": CandidateFamily,
        "escalation_queue": EscalationEntry,
        "prefilter_decisions": PrefilterDecisionRecord,
        "amendment_proposals": ContractAmendmentProposal,
    }

    def validate(self) -> None:
        require_identifier(self.report_id, "report_id")
        require_identifier(self.discovery_plan_id, "discovery_plan_id")
        require_identifier(self.contract_id, "contract_id")
        require_non_empty_str(self.created_at, "created_at")
        require_non_empty_str(self.created_by, "created_by")
        require_non_empty_str(self.policy_version, "policy_version")
        require_str_list(self.atom_ids, "atom_ids")
        if not self.atom_ids:
            raise QcaeValidationError("a discovery report must state its atom scope")
        require_str_list(self.query_families_executed, "query_families_executed")
        require_enum_tuple(self.sources_searched, SourceClass, "sources_searched")
        require_str_list(self.coverage_notes, "coverage_notes")
        require_str_list(self.partial_search_notes, "partial_search_notes")
        require_str_list(self.negative_findings, "negative_findings")
        require_str_list(self.remaining_uncertainties, "remaining_uncertainties")

        self.saturation_metrics.validate()
        self.stop_recommendation.validate()

        # Canon 2.1.6: every external comparison has an explicit baseline.
        require_non_empty_str(self.internal_baseline_ref, "internal_baseline_ref")

        require_str_list(self.canonical_candidate_ids, "canonical_candidate_ids")
        require_no_duplicates(self.canonical_candidate_ids, "canonical_candidate_ids")
        known = set(self.canonical_candidate_ids)

        family_ids: set = set()
        for family in self.candidate_families:
            family.validate()
            if family.family_id in family_ids:
                raise QcaeValidationError(f"duplicate family_id {family.family_id!r}")
            family_ids.add(family.family_id)
            unknown = [c for c in family.member_candidate_ids if c not in known]
            if unknown:
                raise QcaeValidationError(
                    f"family {family.family_id!r} references candidates absent from "
                    f"the report's canonical set: {unknown}"
                )

        for entry in self.escalation_queue:
            entry.validate()
            if entry.candidate_id not in known:
                raise QcaeValidationError(
                    f"escalation entry references candidate {entry.candidate_id!r} "
                    "outside the report's canonical candidate set"
                )
            if entry.family_id and entry.family_id not in family_ids:
                raise QcaeValidationError(
                    f"escalation entry references unknown family {entry.family_id!r}"
                )
        seen_candidates = [entry.candidate_id for entry in self.escalation_queue]
        require_no_duplicates(seen_candidates, "escalation_queue candidate_id")

        for decision in self.prefilter_decisions:
            decision.validate()
            if decision.candidate_id not in known:
                raise QcaeValidationError(
                    f"prefilter decision references candidate "
                    f"{decision.candidate_id!r} outside the canonical set"
                )

        for proposal in self.amendment_proposals:
            proposal.validate()
            if proposal.plan_id != self.discovery_plan_id:
                raise QcaeValidationError(
                    "amendment proposals must reference this report's discovery plan"
                )

    @property
    def external_scope_atoms(self) -> Tuple[str, ...]:
        """Atoms this report is still searching for (canon 2.6.8 partial reuse).

        The narrowing law lives with the internal baseline; the report simply
        states the scope it actually searched, which is what Block 3 receives.
        """
        return tuple(self.atom_ids)

    @property
    def rejected_candidate_ids(self) -> Tuple[str, ...]:
        """Candidates parked as hard rejections (canon 2.7.9 ``Candidate D``)."""
        return tuple(
            entry.candidate_id
            for entry in self.escalation_queue
            if entry.prefilter_decision == PrefilterDecision.REJECT
        )


def make_discovery_report(**kwargs) -> DiscoveryReport:
    """Build and validate a discovery report in one call."""
    report = DiscoveryReport(**kwargs)
    report.validate()
    return report
