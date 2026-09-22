"""DiscoveryPlan and its parts — canon Book II 2.1.

The Discovery Planner's output is a **plan**, never a repository (2.1). This
module is that plan's domain contract: hypotheses, query families, the source
portfolio, diversity requirements, hard prefilters, stop rules, cost tiers,
saturation metrics, budget, and contract-amendment proposals.

Why the laws live here rather than in a service: canon 2.1.16 lists the planner
failure modes that must be *prevented* (one-query discovery, product-name
capture, dominant-vocabulary capture, star-count selection, searching externally
before checking internal capability, repeated rediscovery of rejected
candidates, silently changing the contract). A malformed plan is therefore
refused at construction time instead of being discovered halfway through an
expensive search.

Boundaries this module deliberately does not cross:

- It contains no provider, no ranking, and no transport: it is stdlib-only core
  (ADR-0001) and provider-neutral (Book V 15.1 invariant 1).
- It cannot enact a contract change. Canon 2.1.14 permits discovery to *emit*
  a ``CONTRACT_AMENDMENT_PROPOSAL`` with evidence and forbids it from silently
  adding the requirement and continuing; :class:`ContractAmendmentProposal` is
  therefore proposal-only (no accepted/enacted state exists).
- It cannot approve acquisition. Ranking allocates investigation budget only
  (canon 2.7.4, 2.7.16 invariant 1); nothing here can promote a candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.discovery.vocabulary import CostTier, SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import (
    SerializableRecord,
    coerce_enum,
    coerce_enum_tuple,
    coerce_int_enum,
)
from qcae.core.validation import (
    require_enum,
    require_enum_tuple,
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
    require_str_list,
)
from qcae.core.vocabulary import EvidenceClass

__all__ = [
    "BLOCK_2_MAX_TIER",
    "DIVERSITY_FAMILY_KINDS",
    "REQUIRED_STOP_CONDITIONS",
    "AmendmentProposalStatus",
    "ContractAmendmentProposal",
    "DiscoveryBudget",
    "DiscoveryPlan",
    "DiversityRequirement",
    "HardPrefilter",
    "QueryFamilyKind",
    "QueryFamilyRecord",
    "SaturationMetrics",
    "SearchHypothesis",
    "SearchHypothesisKind",
    "SourceAllocation",
    "StopCondition",
    "StopRule",
    "make_discovery_plan",
]


class SearchHypothesisKind(StrEnum):
    """Where the capability may exist (canon 2.1.2). A route, not a belief."""

    FOCUSED_LIBRARY = "FOCUSED_LIBRARY"
    FRAMEWORK_COMPONENT = "FRAMEWORK_COMPONENT"
    PROTOCOL_SPECIFICATION = "PROTOCOL_SPECIFICATION"
    PAPER_REFERENCE_IMPLEMENTATION = "PAPER_REFERENCE_IMPLEMENTATION"
    EXTRACTABLE_SUBSYSTEM = "EXTRACTABLE_SUBSYSTEM"
    SERVICE_API = "SERVICE_API"
    INTERNAL_IMPLEMENTATION = "INTERNAL_IMPLEMENTATION"
    ADJACENT_DOMAIN = "ADJACENT_DOMAIN"


class QueryFamilyKind(StrEnum):
    """Query families (canon 2.1.3) — families, not single prompts."""

    BEHAVIORAL = "BEHAVIORAL"
    DOMAIN_TERM = "DOMAIN_TERM"
    SYNONYM = "SYNONYM"
    INTERFACE = "INTERFACE"
    IMPLEMENTATION_PATTERN = "IMPLEMENTATION_PATTERN"
    FAILURE_EDGE_CASE = "FAILURE_EDGE_CASE"
    SPECIFICATION_PAPER = "SPECIFICATION_PAPER"
    NEGATIVE_SPACE = "NEGATIVE_SPACE"


class StopCondition(StrEnum):
    """Rational termination conditions (canon 2.1.9)."""

    NON_DOMINATED_SET_SUFFICIENT = "NON_DOMINATED_SET_SUFFICIENT"
    NEGLIGIBLE_NOVELTY = "NEGLIGIBLE_NOVELTY"
    DEEPER_INVESTIGATION_OUTVALUES_SOURCES = "DEEPER_INVESTIGATION_OUTVALUES_SOURCES"
    HARD_CONSTRAINTS_ELIMINATE_CLASS = "HARD_CONSTRAINTS_ELIMINATE_CLASS"
    INTERNAL_CAPABILITY_DOMINATES = "INTERNAL_CAPABILITY_DOMINATES"
    BUDGET_CEILING_REACHED = "BUDGET_CEILING_REACHED"
    CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT = "CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT"


#: Stop rules a plan must declare before any expensive investigation (canon
#: 2.1.17 invariant 7: stop rules exist before expensive investigation). A plan
#: that can only stop by running out of budget is not a plan.
REQUIRED_STOP_CONDITIONS: frozenset = frozenset(
    {
        StopCondition.BUDGET_CEILING_REACHED,
        StopCondition.NON_DOMINATED_SET_SUFFICIENT,
    }
)


#: Block 2 controls tiers 0–3 and decides what merits Block 3/4 escalation
#: (canon 2.1.8). A DiscoveryPlan whose ceiling is above tier 3 has silently
#: absorbed repository intelligence or forensics work.
BLOCK_2_MAX_TIER = CostTier.TIER_3_SOURCE_TREE


#: Family kinds that counter dominant-vocabulary capture (canon 2.1.16). A
#: multi-hypothesis plan must include at least one of these.
DIVERSITY_FAMILY_KINDS: frozenset = frozenset(
    {
        QueryFamilyKind.SYNONYM,
        QueryFamilyKind.NEGATIVE_SPACE,
        QueryFamilyKind.SPECIFICATION_PAPER,
        QueryFamilyKind.IMPLEMENTATION_PATTERN,
        QueryFamilyKind.FAILURE_EDGE_CASE,
    }
)

#: Family kinds that anchor queries to capability semantics (canon 2.1.1: the
#: plan begins from frozen capability semantics).
SEMANTIC_FAMILY_KINDS: frozenset = frozenset(
    {QueryFamilyKind.BEHAVIORAL, QueryFamilyKind.DOMAIN_TERM}
)


@dataclass(frozen=True)
class SearchHypothesis(SerializableRecord):
    """One search route for one or more atoms (canon 2.1.2)."""

    SCHEMA_VERSION = 1

    hypothesis_id: str
    atom_ids: Tuple[str, ...]
    kind: SearchHypothesisKind
    statement: str
    rationale: str = ""
    expected_source_classes: Tuple[SourceClass, ...] = ()

    _COERCIONS = {
        "kind": lambda v: coerce_enum(v, SearchHypothesisKind),
        "expected_source_classes": lambda v: coerce_enum_tuple(v, SourceClass),
    }

    def validate(self) -> None:
        require_identifier(self.hypothesis_id, "hypothesis_id")
        require_str_list(self.atom_ids, "atom_ids")
        if not self.atom_ids:
            raise QcaeValidationError("a hypothesis must target at least one atom")
        require_no_duplicates(self.atom_ids, "atom_ids")
        for atom_id in self.atom_ids:
            require_identifier(atom_id, "atom_ids entry")
        require_enum(self.kind, SearchHypothesisKind, "kind")
        require_non_empty_str(self.statement, "statement")
        require_enum_tuple(self.expected_source_classes, SourceClass, "expected_source_classes")


@dataclass(frozen=True)
class QueryFamilyRecord(SerializableRecord):
    """A family of concrete queries serving one or more hypotheses (2.1.3)."""

    SCHEMA_VERSION = 1

    family_id: str
    kind: QueryFamilyKind
    hypothesis_ids: Tuple[str, ...]
    terms: Tuple[str, ...]
    source_classes: Tuple[SourceClass, ...]
    notes: str = ""

    _COERCIONS = {
        "kind": lambda v: coerce_enum(v, QueryFamilyKind),
        "source_classes": lambda v: coerce_enum_tuple(v, SourceClass),
    }

    def validate(self) -> None:
        require_identifier(self.family_id, "family_id")
        require_enum(self.kind, QueryFamilyKind, "kind")
        require_str_list(self.hypothesis_ids, "hypothesis_ids")
        if not self.hypothesis_ids:
            raise QcaeValidationError(
                "every query family must serve at least one hypothesis (canon 2.1.4 lineage)"
            )
        require_str_list(self.terms, "terms")
        if not self.terms:
            raise QcaeValidationError("a query family must carry at least one concrete term")
        require_enum_tuple(self.source_classes, SourceClass, "source_classes")
        if not self.source_classes:
            raise QcaeValidationError("a query family must name at least one source class")


@dataclass(frozen=True)
class SourceAllocation(SerializableRecord):
    """Budget share for one source class (canon 2.1.5, 2.1.7)."""

    SCHEMA_VERSION = 1

    source_class: SourceClass
    budget_share: float
    max_tier: CostTier = CostTier.TIER_1_METADATA_SNIPPETS
    rationale: str = ""
    enabled: bool = True

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "max_tier": lambda v: coerce_int_enum(v, CostTier),
    }

    def validate(self) -> None:
        require_enum(self.source_class, SourceClass, "source_class")
        if not isinstance(self.budget_share, (int, float)) or isinstance(self.budget_share, bool):
            raise QcaeValidationError(
                f"budget_share must be a number in [0, 1], got {self.budget_share!r}"
            )
        if not (0.0 <= float(self.budget_share) <= 1.0):
            raise QcaeValidationError(
                f"budget_share must be within [0, 1], got {self.budget_share!r}"
            )
        require_enum(self.max_tier, CostTier, "max_tier")
        if not isinstance(self.enabled, bool):
            raise QcaeValidationError(f"enabled must be a bool, got {self.enabled!r}")


@dataclass(frozen=True)
class DiversityRequirement(SerializableRecord):
    """Deliberate diversity allocation (canon 2.1.7, 2.1.17 invariant 5).

    The canon invariant is not the example percentages (50/20/10/10/10 are
    policy examples) but that *the top-ranked ecosystem must not consume the
    entire discovery budget by default*. That is enforced as a hard cap on the
    largest single source share.
    """

    SCHEMA_VERSION = 1

    max_single_source_share: float = 0.5
    min_distinct_source_classes: int = 2
    notes: str = ""

    def validate(self) -> None:
        if not isinstance(self.max_single_source_share, (int, float)) or isinstance(
            self.max_single_source_share, bool
        ):
            raise QcaeValidationError("max_single_source_share must be a number")
        if not (0.0 < float(self.max_single_source_share) < 1.0):
            raise QcaeValidationError(
                "max_single_source_share must be strictly between 0 and 1: a cap "
                "of 1.0 permits single-source capture and a cap of 0 permits no plan"
            )
        if not isinstance(self.min_distinct_source_classes, int) or isinstance(
            self.min_distinct_source_classes, bool
        ):
            raise QcaeValidationError("min_distinct_source_classes must be an integer")
        if self.min_distinct_source_classes < 2:
            raise QcaeValidationError(
                "min_distinct_source_classes must be at least 2 (canon 2.1.5: a "
                "Discovery Plan allocates work across source classes rather than "
                "relying on one index)"
            )


@dataclass(frozen=True)
class HardPrefilter(SerializableRecord):
    """A cheap hard prefilter with an evidence floor (canon 2.2.14, 2.7.3).

    Canon 2.7.16 invariant 6: hard rejection requires sufficiently strong
    evidence, and weak metadata cannot justify it. ``min_evidence_class`` is the
    weakest evidence that may act on this prefilter; E0_CLAIM therefore cannot
    justify rejection (a README claim is not an incompatible license).
    """

    SCHEMA_VERSION = 1

    prefilter_id: str
    rule: str
    min_evidence_class: EvidenceClass
    rationale: str = ""

    _COERCIONS = {"min_evidence_class": lambda v: coerce_enum(v, EvidenceClass)}

    def validate(self) -> None:
        require_identifier(self.prefilter_id, "prefilter_id")
        require_non_empty_str(self.rule, "rule")
        require_enum(self.min_evidence_class, EvidenceClass, "min_evidence_class")
        if self.min_evidence_class == EvidenceClass.E0_CLAIM:
            raise QcaeValidationError(
                "hard prefilters cannot act on E0_CLAIM evidence: weak metadata "
                "must not justify hard rejection (canon 2.7.3, 2.7.16 invariant 6)"
            )


@dataclass(frozen=True)
class StopRule(SerializableRecord):
    """One declared termination condition (canon 2.1.9)."""

    SCHEMA_VERSION = 1

    condition: StopCondition
    detail: str = ""
    threshold: Optional[float] = None

    _COERCIONS = {"condition": lambda v: coerce_enum(v, StopCondition)}

    def validate(self) -> None:
        require_enum(self.condition, StopCondition, "condition")
        if self.threshold is not None and self.threshold < 0:
            raise QcaeValidationError(
                f"stop-rule threshold must be >= 0, got {self.threshold!r}"
            )
        if self.condition == StopCondition.NEGLIGIBLE_NOVELTY and self.threshold is None:
            raise QcaeValidationError(
                "NEGLIGIBLE_NOVELTY requires an explicit threshold; otherwise "
                "'negligible' is unfalsifiable prose"
            )


@dataclass(frozen=True)
class SaturationMetrics(SerializableRecord):
    """Marginal-novelty tracking (canon 2.1.10, 2.7.15).

    Saturation is a measurement, not an opinion: the counters are inputs and
    ``marginal_novelty_rate`` is derived here. Declaring ``saturated`` requires a
    recorded reason so a search cannot be silently stopped by omission.
    """

    SCHEMA_VERSION = 1

    queries_executed: int = 0
    results_inspected: int = 0
    new_candidates: int = 0
    new_implementation_families: int = 0
    new_specifications: int = 0
    new_atoms_covered: int = 0
    new_acquisition_forms: int = 0
    new_failure_information: int = 0
    saturated: bool = False
    saturation_reason: str = ""

    def validate(self) -> None:
        for name in (
            "queries_executed",
            "results_inspected",
            "new_candidates",
            "new_implementation_families",
            "new_specifications",
            "new_atoms_covered",
            "new_acquisition_forms",
            "new_failure_information",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise QcaeValidationError(f"{name} must be a non-negative integer, got {value!r}")
        if not isinstance(self.saturated, bool):
            raise QcaeValidationError(f"saturated must be a bool, got {self.saturated!r}")
        if self.saturated and not self.saturation_reason.strip():
            raise QcaeValidationError(
                "declaring saturation requires a recorded reason (canon 2.7.16 "
                "invariant 8: saturation is reevaluated, not asserted)"
            )

    @property
    def marginal_novelty_rate(self) -> float:
        """Novel items per inspected result, or 0.0 before anything is inspected."""
        if self.results_inspected <= 0:
            return 0.0
        novel = (
            self.new_candidates
            + self.new_implementation_families
            + self.new_specifications
            + self.new_atoms_covered
            + self.new_failure_information
        )
        return novel / self.results_inspected


@dataclass(frozen=True)
class DiscoveryBudget(SerializableRecord):
    """Bounded discovery spend envelope (canon 2.1.15 ``budget``)."""

    SCHEMA_VERSION = 1

    max_queries: int
    max_results_inspected: int
    max_source_calls: int
    max_wall_clock_seconds: int
    max_cost_usd: Optional[float] = None

    def validate(self) -> None:
        for name in ("max_queries", "max_results_inspected", "max_source_calls",
                     "max_wall_clock_seconds"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise QcaeValidationError(
                    f"{name} must be an integer >= 1 (a plan with no spend envelope "
                    f"cannot be stopped), got {value!r}"
                )
        if self.max_cost_usd is not None:
            if not isinstance(self.max_cost_usd, (int, float)) or isinstance(
                self.max_cost_usd, bool
            ):
                raise QcaeValidationError("max_cost_usd must be a number or None")
            if self.max_cost_usd < 0:
                raise QcaeValidationError(
                    f"max_cost_usd must be >= 0, got {self.max_cost_usd!r}"
                )


class AmendmentProposalStatus(StrEnum):
    """Contract-amendment proposal state (canon 2.1.14).

    Only ``PROPOSED`` and ``WITHDRAWN`` exist: discovery may propose a contract
    change but may never enact one, so no accepted/applied state is reachable
    from the discovery layer.
    """

    PROPOSED = "PROPOSED"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True)
class ContractAmendmentProposal(SerializableRecord):
    """``CONTRACT_AMENDMENT_PROPOSAL`` record (canon 2.1.14)."""

    SCHEMA_VERSION = 1

    proposal_id: str
    contract_id: str
    contract_version: int
    plan_id: str
    discovered_need: str
    proposed_change: str
    evidence_ids: Tuple[str, ...]
    status: AmendmentProposalStatus = AmendmentProposalStatus.PROPOSED

    _COERCIONS = {
        "status": lambda v: coerce_enum(v, AmendmentProposalStatus),
        "evidence_ids": tuple,
    }

    def validate(self) -> None:
        require_identifier(self.proposal_id, "proposal_id")
        require_identifier(self.contract_id, "contract_id")
        require_identifier(self.plan_id, "plan_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError("contract_version must be an integer >= 1")
        require_enum(self.status, AmendmentProposalStatus, "status")
        require_non_empty_str(self.discovered_need, "discovered_need")
        require_non_empty_str(self.proposed_change, "proposed_change")
        require_str_list(self.evidence_ids, "evidence_ids")
        if not self.evidence_ids:
            raise QcaeValidationError(
                "a contract-amendment proposal must cite evidence (canon 2.1.14: "
                "the planner may emit the proposal *with evidence*)"
            )


@dataclass(frozen=True)
class DiscoveryPlan(SerializableRecord):
    """The frozen schema of canon 2.1.15, with its anti-capture laws."""

    SCHEMA_VERSION = 1

    discovery_plan_id: str
    contract_id: str
    contract_version: int
    atom_ids: Tuple[str, ...]

    internal_baseline_queries: Tuple[str, ...]
    search_hypotheses: Tuple[SearchHypothesis, ...]
    query_families: Tuple[QueryFamilyRecord, ...]
    source_allocations: Tuple[SourceAllocation, ...]
    budget: DiscoveryBudget
    cost_tier_ceiling: CostTier
    diversity_requirements: DiversityRequirement
    hard_prefilters: Tuple[HardPrefilter, ...] = ()
    stop_rules: Tuple[StopRule, ...] = ()
    saturation_metrics: SaturationMetrics = field(default_factory=SaturationMetrics)
    created_by: str = ""
    policy_version: str = ""
    operating_context: str = ""
    security_data_constraints: Tuple[str, ...] = ()
    accepted_acquisition_forms: Tuple[str, ...] = ()
    known_prior_evaluation_ids: Tuple[str, ...] = ()
    amendment_proposals: Tuple[ContractAmendmentProposal, ...] = ()
    single_route_justification: str = ""

    _COERCIONS = {
        "atom_ids": tuple,
        "internal_baseline_queries": tuple,
        "security_data_constraints": tuple,
        "accepted_acquisition_forms": tuple,
        "known_prior_evaluation_ids": tuple,
        "cost_tier_ceiling": lambda v: coerce_int_enum(v, CostTier),
    }

    _NESTED_RECORDS = {
        "budget": DiscoveryBudget,
        "diversity_requirements": DiversityRequirement,
        "saturation_metrics": SaturationMetrics,
        "search_hypotheses": SearchHypothesis,
        "query_families": QueryFamilyRecord,
        "source_allocations": SourceAllocation,
        "hard_prefilters": HardPrefilter,
        "stop_rules": StopRule,
        "amendment_proposals": ContractAmendmentProposal,
    }

    # -- validation ---------------------------------------------------------

    def validate(self) -> None:
        require_identifier(self.discovery_plan_id, "discovery_plan_id")
        require_identifier(self.contract_id, "contract_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError("contract_version must be an integer >= 1")
        require_non_empty_str(self.created_by, "created_by")
        require_non_empty_str(self.policy_version, "policy_version")

        # 2.1.1 / 2.1.17 invariant 1: discovery begins from frozen capability
        # semantics, so a plan with no atom scope is not a plan.
        require_str_list(self.atom_ids, "atom_ids")
        if not self.atom_ids:
            raise QcaeValidationError(
                "a DiscoveryPlan must target at least one atom (canon 2.1.1)"
            )
        require_no_duplicates(self.atom_ids, "atom_ids")
        for atom_id in self.atom_ids:
            require_identifier(atom_id, "atom_ids entry")

        # 2.1.6 / 2.1.17 invariant 3: internal capability is part of the search
        # universe, so internal-baseline queries are mandatory before external
        # search — not merely allowed.
        require_str_list(self.internal_baseline_queries, "internal_baseline_queries")
        if not self.internal_baseline_queries:
            raise QcaeValidationError(
                "internal_baseline_queries must be non-empty: external search "
                "before checking internal capability is a canon 2.1.16 failure mode"
            )

        # Allocation first: the source portfolio is the funding envelope, and
        # query families are validated against the classes it enables. Reporting
        # an unfunded family before an unbalanced portfolio would hide the
        # primary defect behind its own consequence.
        self._validate_allocations()
        self._validate_hypotheses()
        self._validate_query_families()
        self._validate_stop_rules()
        self._validate_prefilters()
        self._validate_proposals()
        self.budget.validate()
        self.diversity_requirements.validate()
        self.saturation_metrics.validate()

        require_enum(self.cost_tier_ceiling, CostTier, "cost_tier_ceiling")
        if self.cost_tier_ceiling > BLOCK_2_MAX_TIER:
            raise QcaeValidationError(
                f"cost_tier_ceiling {self.cost_tier_ceiling.name} exceeds the Block 2 "
                f"ceiling {BLOCK_2_MAX_TIER.name}: repository intelligence, forensics "
                "and proving are Block 3/4 escalation decisions, not discovery work "
                "(canon 2.1.8)"
            )
        for allocation in self.source_allocations:
            if allocation.max_tier > self.cost_tier_ceiling:
                raise QcaeValidationError(
                    f"source allocation {allocation.source_class.value} declares "
                    f"max_tier {allocation.max_tier.name} above the plan ceiling "
                    f"{self.cost_tier_ceiling.name}"
                )

        require_str_list(self.security_data_constraints, "security_data_constraints")
        require_str_list(self.accepted_acquisition_forms, "accepted_acquisition_forms")
        require_str_list(self.known_prior_evaluation_ids, "known_prior_evaluation_ids")

    def _validate_hypotheses(self) -> None:
        if not self.search_hypotheses:
            raise QcaeValidationError(
                "a DiscoveryPlan requires at least one search hypothesis (canon 2.1.2)"
            )
        seen: set = set()
        for hypothesis in self.search_hypotheses:
            hypothesis.validate()
            if hypothesis.hypothesis_id in seen:
                raise QcaeValidationError(
                    f"duplicate hypothesis_id {hypothesis.hypothesis_id!r}"
                )
            seen.add(hypothesis.hypothesis_id)
            unknown = [a for a in hypothesis.atom_ids if a not in self.atom_ids]
            if unknown:
                raise QcaeValidationError(
                    f"hypothesis {hypothesis.hypothesis_id!r} targets atoms outside "
                    f"the plan scope: {unknown}"
                )

        # 2.1.17 invariant 2: multiple search hypotheses are mandatory for
        # nontrivial capabilities. Every requested atom must be routed, and a
        # single-route atom needs an explicit recorded justification instead of
        # a silent shortcut.
        per_atom: dict = {atom_id: 0 for atom_id in self.atom_ids}
        for hypothesis in self.search_hypotheses:
            for atom_id in hypothesis.atom_ids:
                per_atom[atom_id] += 1
        unrouted = sorted(atom_id for atom_id, count in per_atom.items() if count == 0)
        if unrouted:
            raise QcaeValidationError(
                f"atoms without any search hypothesis: {unrouted} (canon 2.1.17 "
                "invariant 2)"
            )
        single_route = sorted(atom_id for atom_id, count in per_atom.items() if count == 1)
        if single_route and not self.single_route_justification.strip():
            raise QcaeValidationError(
                f"atoms {single_route} have a single search route; a deliberate "
                "narrow route requires a recorded single_route_justification "
                "(canon 2.1.17 invariant 2, 2.1.16 one-query discovery)"
            )

    def _validate_query_families(self) -> None:
        if not self.query_families:
            raise QcaeValidationError(
                "a DiscoveryPlan requires query families, not one query (canon 2.1.3)"
            )
        hypothesis_ids = {h.hypothesis_id for h in self.search_hypotheses}
        enabled_sources = {a.source_class for a in self.source_allocations if a.enabled}
        family_ids: set = set()
        served_hypotheses: set = set()
        for family in self.query_families:
            family.validate()
            if family.family_id in family_ids:
                raise QcaeValidationError(f"duplicate family_id {family.family_id!r}")
            family_ids.add(family.family_id)
            unknown = [h for h in family.hypothesis_ids if h not in hypothesis_ids]
            if unknown:
                raise QcaeValidationError(
                    f"query family {family.family_id!r} references unknown "
                    f"hypotheses: {unknown} (canon 2.1.4 lineage)"
                )
            served_hypotheses.update(family.hypothesis_ids)
            unallocated = sorted(
                sc.value for sc in family.source_classes if sc not in enabled_sources
            )
            if unallocated:
                raise QcaeValidationError(
                    f"query family {family.family_id!r} targets source classes with "
                    f"no enabled allocation: {unallocated}"
                )

        unserved = sorted(hypothesis_ids - served_hypotheses)
        if unserved:
            raise QcaeValidationError(
                f"hypotheses with no query family: {unserved} (canon 2.1.4: the "
                "lineage runs hypothesis -> query family -> concrete query -> source)"
            )

        # No dead budget: every enabled class must be reachable from a family.
        # This is a portfolio-coverage law, so it is checked here (after the
        # per-family allocation checks) rather than with the portfolio
        # arithmetic in _validate_allocations.
        referenced = {sc for family in self.query_families for sc in family.source_classes}
        dead = sorted(
            a.source_class.value
            for a in self.source_allocations
            if a.enabled and a.source_class not in referenced
        )
        if dead:
            raise QcaeValidationError(
                f"enabled source classes funded but never queried: {dead}"
            )

        kinds = {family.kind for family in self.query_families}
        if not (kinds & SEMANTIC_FAMILY_KINDS):
            raise QcaeValidationError(
                "query families must include at least one behavioral or domain-term "
                "family anchored to capability semantics (canon 2.1.3, 2.1.17 "
                "invariant 1)"
            )
        # 2.1.16 dominant-vocabulary capture: a plan with more than one route
        # must reserve budget for terminology outside the dominant vocabulary.
        if len(self.search_hypotheses) > 1 and not (kinds & DIVERSITY_FAMILY_KINDS):
            raise QcaeValidationError(
                "a multi-hypothesis plan must include a diversity family (synonym, "
                "negative-space, specification/paper, implementation-pattern or "
                "failure/edge-case) to counter dominant-vocabulary capture "
                "(canon 2.1.16, 2.7.16 invariant 3)"
            )

    def _validate_allocations(self) -> None:
        if not self.source_allocations:
            raise QcaeValidationError(
                "a DiscoveryPlan must allocate a source portfolio (canon 2.1.5)"
            )
        classes: set = set()
        for allocation in self.source_allocations:
            allocation.validate()
            if allocation.source_class in classes:
                raise QcaeValidationError(
                    f"duplicate source allocation for {allocation.source_class.value}"
                )
            classes.add(allocation.source_class)

        enabled = [a for a in self.source_allocations if a.enabled]
        if len(enabled) < self.diversity_requirements.min_distinct_source_classes:
            raise QcaeValidationError(
                f"enabled source classes ({len(enabled)}) fall below the diversity "
                f"requirement ({self.diversity_requirements.min_distinct_source_classes})"
            )
        total = sum(float(a.budget_share) for a in enabled)
        if abs(total - 1.0) > 1e-6:
            raise QcaeValidationError(
                f"enabled source budget shares must sum to 1.0, got {total!r}"
            )
        largest = max(enabled, key=lambda a: float(a.budget_share))
        if float(largest.budget_share) > self.diversity_requirements.max_single_source_share + 1e-9:
            raise QcaeValidationError(
                f"source {largest.source_class.value} would consume "
                f"{largest.budget_share!r} of discovery budget, above the diversity "
                f"cap {self.diversity_requirements.max_single_source_share!r} "
                "(canon 2.1.7: the top-ranked ecosystem must not consume the entire "
                "discovery budget by default)"
            )

    def _validate_stop_rules(self) -> None:
        if not self.stop_rules:
            raise QcaeValidationError(
                "stop rules must exist before expensive investigation begins "
                "(canon 2.1.9, 2.1.17 invariant 7)"
            )
        conditions = [rule.condition for rule in self.stop_rules]
        require_no_duplicates(conditions, "stop_rules conditions")
        for rule in self.stop_rules:
            rule.validate()
        missing = sorted(c.value for c in REQUIRED_STOP_CONDITIONS if c not in set(conditions))
        if missing:
            raise QcaeValidationError(
                f"stop rule conditions missing: {missing} (canon 2.1.9: a bounded "
                "search states both when it has enough and when it has spent enough)"
            )

    def _validate_prefilters(self) -> None:
        seen: set = set()
        for prefilter in self.hard_prefilters:
            prefilter.validate()
            if prefilter.prefilter_id in seen:
                raise QcaeValidationError(
                    f"duplicate prefilter_id {prefilter.prefilter_id!r}"
                )
            seen.add(prefilter.prefilter_id)

    def _validate_proposals(self) -> None:
        seen: set = set()
        for proposal in self.amendment_proposals:
            proposal.validate()
            if proposal.plan_id != self.discovery_plan_id:
                raise QcaeValidationError(
                    f"amendment proposal {proposal.proposal_id!r} names plan "
                    f"{proposal.plan_id!r} but is attached to {self.discovery_plan_id!r}"
                )
            if proposal.contract_id != self.contract_id:
                raise QcaeValidationError(
                    f"amendment proposal {proposal.proposal_id!r} targets contract "
                    f"{proposal.contract_id!r}, not the plan's {self.contract_id!r}"
                )

    # -- queries ------------------------------------------------------------

    def hypotheses_for_atom(self, atom_id: str) -> Tuple[SearchHypothesis, ...]:
        """Search routes covering one atom (canon 2.1.2)."""
        return tuple(h for h in self.search_hypotheses if atom_id in h.atom_ids)

    def enabled_source_classes(self) -> Tuple[SourceClass, ...]:
        """Enabled source classes in declared order (canon 2.1.5)."""
        return tuple(a.source_class for a in self.source_allocations if a.enabled)


def make_discovery_plan(**kwargs) -> DiscoveryPlan:
    """Build and validate a DiscoveryPlan in one call."""
    plan = DiscoveryPlan(**kwargs)
    plan.validate()
    return plan
