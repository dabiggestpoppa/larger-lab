"""Discovery domain records (canon Book II Block 2).

Provider-neutral, stdlib-only domain objects for the Discovery Vertical Slice:

- :mod:`qcae.core.discovery.plan` — DiscoveryPlan and its parts (canon 2.1.15).
- :mod:`qcae.core.discovery.lead` — normalized candidate leads + query lineage
  (canon 2.1.11/2.1.4, Book V 15.3).
- :mod:`qcae.core.discovery.report` — DiscoveryReport and escalation entries
  (canon 2.7.9/2.7.15).
- :mod:`qcae.core.discovery.candidate` — the canonical merged candidate identity
  that preserves every discovery path (canon 2.1.12).

These records live at the dependency center (core) for the same reason evidence
and knowledge records do (P1): every higher layer consumes one canonical
vocabulary, and no adapter can invent its own (Book V 15.1 invariant 5, 15.2
invariant 4).
"""

from qcae.core.discovery.candidate import (
    CanonicalCandidate,
    make_canonical_candidate,
)
from qcae.core.discovery.lead import (
    AdapterStatus,
    CandidateKind,
    CandidateLead,
    QueryLineage,
    SearchCompleteness,
    make_candidate_lead,
)
from qcae.core.discovery.plan import (
    BLOCK_2_MAX_TIER,
    DIVERSITY_FAMILY_KINDS,
    REQUIRED_STOP_CONDITIONS,
    AmendmentProposalStatus,
    ContractAmendmentProposal,
    DiscoveryBudget,
    DiscoveryPlan,
    DiversityRequirement,
    HardPrefilter,
    QueryFamilyKind,
    QueryFamilyRecord,
    SaturationMetrics,
    SearchHypothesis,
    SearchHypothesisKind,
    SourceAllocation,
    StopCondition,
    StopRule,
    make_discovery_plan,
)
from qcae.core.discovery.report import (
    EscalationEntry,
    NextAction,
    PrefilterDecision,
    Priority,
    StopRecommendation,
)
from qcae.core.discovery.vocabulary import CostTier, SourceClass

__all__ = [
    "BLOCK_2_MAX_TIER",
    "DIVERSITY_FAMILY_KINDS",
    "REQUIRED_STOP_CONDITIONS",
    "AmendmentProposalStatus",
    "ContractAmendmentProposal",
    "CostTier",
    "DiscoveryBudget",
    "DiscoveryPlan",
    "DiversityRequirement",
    "EscalationEntry",
    "HardPrefilter",
    "NextAction",
    "PrefilterDecision",
    "Priority",
    "QueryFamilyKind",
    "QueryFamilyRecord",
    "SaturationMetrics",
    "SearchHypothesis",
    "SearchHypothesisKind",
    "SourceAllocation",
    "SourceClass",
    "StopCondition",
    "StopRecommendation",
    "StopRule",
    "make_discovery_plan",
    "CanonicalCandidate",
    "make_canonical_candidate",
    "AdapterStatus",
    "CandidateKind",
    "CandidateLead",
    "QueryLineage",
    "SearchCompleteness",
    "make_candidate_lead",
]
