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
  stop rules (2.1.9) — an unexplained "stop" is not representable;
- the artifact carries the canonical candidate set it counted, not only its ids
  (2.7.15), because canon 2.1.10 measures novelty against what was already known
  and the report is what a later pass has to hand over. Carrying ids alone made
  the durable handoff — feed the previous pass's metrics forward — re-count an
  already-known candidate as new, inflating the very rate the stop law reads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import AdapterStatus
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
    sha256_of,
)
from qcae.core.validation import (
    require_enum,
    require_enum_tuple,
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
    require_rfc3339_utc,
    require_str_list,
)
from qcae.core.vocabulary import EVIDENCE_STRENGTH_ORDER, EvidenceClass

__all__ = [
    "CandidateFamily",
    "DiscoveryReport",
    "EscalationEntry",
    "NegativeObservation",
    "NextAction",
    "PrefilterDecision",
    "PrefilterDecisionRecord",
    "Priority",
    "StopConditionAssessment",
    "StopRecommendation",
    "StopRecommendationState",
    "make_discovery_report",
]


@dataclass(frozen=True)
class NegativeObservation(SerializableRecord):
    """One identity-deduplicated negative result (P3-R4C4; canon 2.1.13).

    A repeated observation of the same condition is not new knowledge: the
    record's ``observation_id`` is derived from the safe applicable combination
    of query identity, atom/family, source class, adapter, provider revision,
    status and bounded query scope, so two identical observations share one id
    and a materially new state derives a different one. ``NO_RESULTS`` stays a
    distinct status from provider failure, and an observation never proves
    capability absence — it is negative knowledge, not evidence of nonexistence.
    """

    SCHEMA_VERSION = 1

    query_id: str
    atom_id: str
    family_id: str
    source_class: SourceClass
    adapter_id: str
    status: AdapterStatus
    discovery_plan_id: str
    #: Optional safe scope dimensions: two observations only share an identity
    #: when these also agree.
    provider_revision: str = ""
    bounded_query_scope: str = ""
    evidence_refs: Tuple[str, ...] = ()
    #: Derived last, from everything above (see ``identity_fields``).
    observation_id: str = ""
    first_seen_at: str = ""
    last_seen_at: str = ""
    observed_count: int = 1

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "status": lambda v: coerce_enum(v, AdapterStatus),
        "evidence_refs": tuple,
    }

    #: The fields the stable identity derives from. Prose (notes, rationale) is
    #: deliberately excluded: identity is what was observed, not what was said.
    @property
    def identity_fields(self) -> dict:
        return {
            "query_id": self.query_id,
            "atom_id": self.atom_id,
            "family_id": self.family_id,
            "source_class": self.source_class.value,
            "adapter_id": self.adapter_id,
            "provider_revision": self.provider_revision,
            "status": self.status.value,
            "bounded_query_scope": self.bounded_query_scope,
        }

    def __post_init__(self) -> None:
        if not self.observation_id:
            object.__setattr__(
                self, "observation_id", f"neg-{sha256_of(self.identity_fields)[:24]}"
            )

    def validate(self) -> None:
        require_identifier(self.observation_id, "observation_id")
        require_identifier(self.query_id, "query_id")
        require_identifier(self.atom_id, "atom_id")
        require_identifier(self.family_id, "family_id")
        require_enum(self.source_class, SourceClass, "source_class")
        require_non_empty_str(self.adapter_id, "adapter_id")
        require_enum(self.status, AdapterStatus, "status")
        require_identifier(self.discovery_plan_id, "discovery_plan_id")
        require_str_list(self.evidence_refs, "evidence_refs")
        if not isinstance(self.observed_count, int) or isinstance(
            self.observed_count, bool
        ) or self.observed_count < 1:
            raise QcaeValidationError(
                f"observed_count must be an integer >= 1, got {self.observed_count!r}"
            )
        if self.first_seen_at:
            require_rfc3339_utc(self.first_seen_at, "first_seen_at")
        if self.last_seen_at:
            require_rfc3339_utc(self.last_seen_at, "last_seen_at")
            if self.first_seen_at and self.last_seen_at < self.first_seen_at:
                raise QcaeValidationError(
                    "last_seen_at cannot precede first_seen_at"
                )
        # Identity integrity: the carried id must still derive from the fields.
        if self.observation_id != f"neg-{sha256_of(self.identity_fields)[:24]}":
            raise QcaeValidationError(
                f"observation_id {self.observation_id!r} does not derive from the "
                "observation's identity fields; negative knowledge with a foreign "
                "identity cannot be deduplicated"
            )


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
class StopConditionAssessment(SerializableRecord):
    """One attributable stop-condition judgement (P3-R4C3; canon 2.1.9).

    A STOP can no longer be created by a naked caller boolean: each satisfied
    condition is a typed record naming who evaluated it, under which policy,
    over exactly which subjects, derived how, and on what evidence. A
    recommendation grants no acquisition authority — it is what a human reads.
    """

    SCHEMA_VERSION = 1

    condition: StopCondition
    discovery_plan_id: str
    contract_id: str
    contract_version: int
    #: Who produced this assessment — an evaluator identity, never "the caller".
    evaluator_id: str
    #: The ranking/stop policy version the derivation ran under.
    policy_version: str
    assessed_at: str
    #: The exact subject set the condition was evaluated over — candidate ids
    #: for sufficiency, class/query ids for hard constraints, and so on.
    subject_ids: Tuple[str, ...] = ()
    #: How the assessment was derived from the subjects (re-derived under the
    #: current policy, counted from typed accounting, ...), not a conclusion.
    derivation_method: str = ""
    #: Durable evidence references backing the derivation (evidence ids,
    #: prefilter decision ids, proposal ids, accounting record ids).
    evidence_ids: Tuple[str, ...] = ()
    #: A proposal id is mandatory evidence for
    #: CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT (law 5).
    amendment_proposal_id: str = ""
    rationale: str = ""

    _COERCIONS = {
        "condition": lambda v: coerce_enum(v, StopCondition),
        "subject_ids": tuple,
        "evidence_ids": tuple,
    }

    def validate(self) -> None:
        require_enum(self.condition, StopCondition, "condition")
        require_identifier(self.discovery_plan_id, "discovery_plan_id")
        require_identifier(self.contract_id, "contract_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError("contract_version must be an integer >= 1")
        require_identifier(self.evaluator_id, "evaluator_id")
        require_non_empty_str(self.policy_version, "policy_version")
        require_rfc3339_utc(self.assessed_at, "assessed_at")
        require_str_list(self.subject_ids, "subject_ids")
        require_str_list(self.evidence_ids, "evidence_ids")
        require_non_empty_str(self.rationale, "rationale")
        # The subject set is the exact set the condition was evaluated over; a
        # sufficiency or elimination claim with no subjects asserts nothing.
        if not self.subject_ids:
            raise QcaeValidationError(
                f"stop assessment for {self.condition.value} must name the exact "
                "subject set it evaluated (P3-R4C3 law 2/4): an assessment over no "
                "subjects attributes nothing"
            )
        if not self.derivation_method.strip():
            raise QcaeValidationError(
                f"stop assessment for {self.condition.value} must state its "
                "derivation method (P3-R4C3 law 8): the derivation, not the "
                "assertion, is the evidence"
            )
        if self.condition == StopCondition.CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT:
            require_identifier(self.amendment_proposal_id, "amendment_proposal_id")
            if self.amendment_proposal_id not in self.evidence_ids:
                raise QcaeValidationError(
                    "CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT must cite its amendment "
                    "proposal among the evidence ids (P3-R4C3 law 5)"
                )


@dataclass(frozen=True)
class StopRecommendation(SerializableRecord):
    """Saturation-driven stop/continue recommendation (canon 2.1.9, 2.7.14)."""

    SCHEMA_VERSION = 2

    state: StopRecommendationState
    satisfied_conditions: Tuple[StopCondition, ...] = ()
    #: The attributable assessments behind every satisfied condition. A STOP is
    #: only representable when each satisfied condition carries its own typed
    #: assessment — there is no boolean path to a STOP anymore (P3-R4C3).
    assessments: Tuple[StopConditionAssessment, ...] = ()
    rationale: str = ""

    _COERCIONS = {
        "state": lambda v: coerce_enum(v, StopRecommendationState),
        "satisfied_conditions": lambda v: coerce_enum_tuple(v, StopCondition),
        "assessments": tuple,
    }

    _NESTED_RECORDS = {"assessments": StopConditionAssessment}

    def validate(self) -> None:
        require_enum(self.state, StopRecommendationState, "state")
        require_enum_tuple(self.satisfied_conditions, StopCondition, "satisfied_conditions")
        require_no_duplicates(self.satisfied_conditions, "satisfied_conditions")
        require_non_empty_str(self.rationale, "rationale")
        seen: set = set()
        for assessment in self.assessments:
            assessment.validate()
            if assessment.condition in seen:
                raise QcaeValidationError(
                    f"duplicate stop assessment for {assessment.condition.value}"
                )
            seen.add(assessment.condition)
            if assessment.condition not in self.satisfied_conditions:
                raise QcaeValidationError(
                    f"stop assessment for {assessment.condition.value} names a "
                    "condition the recommendation does not report as satisfied"
                )
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
        # P3-R4C3: every satisfied condition needs its attributable assessment.
        unassessed = sorted(
            c.value for c in self.satisfied_conditions if c not in seen
        )
        if unassessed:
            raise QcaeValidationError(
                f"satisfied stop conditions without an attributable assessment: "
                f"{unassessed} (P3-R4C3: no raw caller boolean may create a STOP)"
            )


@dataclass(frozen=True)
class DiscoveryReport(SerializableRecord):
    """Block 2 terminal artifact (canon 2.7.15)."""

    #: Bumped when the persisted shape gained the scope quadruple
    #: (``requested_/internally_covered_/external_target_/actually_executed_atom_ids``):
    #: the reader refuses an older payload with a version error rather than a
    #: missing-field one, so an artifact predating the change is distinguishable
    #: from a corrupted one.
    SCHEMA_VERSION = 3

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
    #: The scope quadruple (P3-R4C2). ``atom_ids`` states the plan's requested
    #: scope; the four fields below separate what was requested from what the
    #: internal baseline already covers, what the baseline authorizes for
    #: external search, and what external search actually executed — because
    #: internal reuse narrows external discovery, and a report that named the
    #: requested set as its external scope would claim searches it never
    #: needed to run (canon 2.6.8).
    requested_atom_ids: Tuple[str, ...] = ()
    internally_covered_atom_ids: Tuple[str, ...] = ()
    external_target_atom_ids: Tuple[str, ...] = ()
    actually_executed_atom_ids: Tuple[str, ...] = ()
    #: Every canonical candidate known as of this pass — 2.7.15's canonical
    #: candidate set, accumulated across passes because 2.1.10 measures novelty
    #: against everything already known. This is the field a later pass reads to
    #: keep its counters honest; the ranking's own set is ``canonical_candidate_ids``.
    known_candidates: Tuple[CanonicalCandidate, ...] = ()
    coverage_notes: Tuple[str, ...] = ()
    partial_search_notes: Tuple[str, ...] = ()
    prefilter_decisions: Tuple[PrefilterDecisionRecord, ...] = ()
    #: Identity-deduplicated negative knowledge (P3-R4C4): one typed record per
    #: distinct NO_RESULTS / failure condition, with repeat counts — the report
    #: carries the observations themselves, not only prose strings.
    negative_observations: Tuple[NegativeObservation, ...] = ()
    negative_findings: Tuple[str, ...] = ()
    remaining_uncertainties: Tuple[str, ...] = ()
    amendment_proposals: Tuple[ContractAmendmentProposal, ...] = ()
    created_at: str = ""
    created_by: str = ""
    policy_version: str = ""

    _COERCIONS = {
        "atom_ids": tuple,
        "requested_atom_ids": tuple,
        "internally_covered_atom_ids": tuple,
        "external_target_atom_ids": tuple,
        "actually_executed_atom_ids": tuple,
        "sources_searched": lambda v: coerce_enum_tuple(v, SourceClass),
        "query_families_executed": tuple,
        "canonical_candidate_ids": tuple,
        "known_candidates": tuple,
        "coverage_notes": tuple,
        "partial_search_notes": tuple,
        "negative_observations": tuple,
        "negative_findings": tuple,
        "remaining_uncertainties": tuple,
    }

    _NESTED_RECORDS = {
        "known_candidates": CanonicalCandidate,
        "saturation_metrics": SaturationMetrics,
        "stop_recommendation": StopRecommendation,
        "candidate_families": CandidateFamily,
        "escalation_queue": EscalationEntry,
        "negative_observations": NegativeObservation,
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
        # The scope quadruple must state one coherent scope (canon 2.6.8):
        # requested matches the stated scope, coverage stays inside it, the
        # external target is exactly the uncovered remainder, and execution
        # never left the requested scope.
        if tuple(self.requested_atom_ids) != tuple(self.atom_ids):
            raise QcaeValidationError(
                f"requested_atom_ids {list(self.requested_atom_ids)} must equal the "
                f"report's atom scope {list(self.atom_ids)} (P3-R4C2)"
            )
        for name in ("internally_covered_atom_ids", "external_target_atom_ids",
                     "actually_executed_atom_ids"):
            require_no_duplicates(getattr(self, name), name)
        outside = sorted(
            set(self.internally_covered_atom_ids) - set(self.requested_atom_ids))
        if outside:
            raise QcaeValidationError(
                f"internally_covered_atom_ids outside the requested scope: {outside}"
            )
        expected_targets = tuple(
            a for a in self.requested_atom_ids
            if a not in set(self.internally_covered_atom_ids)
        )
        if tuple(self.external_target_atom_ids) != expected_targets:
            raise QcaeValidationError(
                f"external_target_atom_ids must be the requested atoms minus the "
                f"internally covered ones (canon 2.6.8): expected {list(expected_targets)}, "
                f"got {list(self.external_target_atom_ids)}"
            )
        executed_outside = sorted(
            set(self.actually_executed_atom_ids) - set(self.requested_atom_ids))
        if executed_outside:
            raise QcaeValidationError(
                f"actually_executed_atom_ids outside the requested scope: "
                f"{executed_outside}"
            )
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
        for candidate in self.known_candidates:
            candidate.validate()
        require_no_duplicates(self.known_candidates_ids, "known_candidates canonical_id")
        unknown = sorted(set(self.canonical_candidate_ids) - set(self.known_candidates_ids))
        if unknown:
            raise QcaeValidationError(
                f"canonical candidates absent from known_candidates: {unknown} "
                "(canon 2.7.15/2.1.10: the artifact must carry the candidates it counted "
                "as known, or a later pass cannot measure novelty against them and "
                "re-counts them as new)"
            )
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

        negative_ids: set = set()
        for observation in self.negative_observations:
            observation.validate()
            if observation.observation_id in negative_ids:
                raise QcaeValidationError(
                    f"duplicate negative observation {observation.observation_id!r}"
                )
            negative_ids.add(observation.observation_id)
            if observation.discovery_plan_id != self.discovery_plan_id:
                raise QcaeValidationError(
                    f"negative observation {observation.observation_id!r} was made "
                    f"for plan {observation.discovery_plan_id!r}, not this report's "
                    f"{self.discovery_plan_id!r}"
                )

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
    def known_candidates_ids(self) -> Tuple[str, ...]:
        """Canonical ids of every candidate this report knows (canon 2.1.10)."""
        return tuple(candidate.canonical_id for candidate in self.known_candidates)

    @property
    def external_scope_atoms(self) -> Tuple[str, ...]:
        """The baseline-authorized external target scope (canon 2.6.8).

        Internal reuse narrows the external request, so the scope Block 3
        receives is what the baseline authorized for external search — not the
        requested set, which would claim a wider search than the baseline
        required (P3-R4C2).
        """
        return tuple(self.external_target_atom_ids)

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
