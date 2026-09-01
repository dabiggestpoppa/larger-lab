"""OCE Institutional Stress Suite — generic harness (G1).

Deterministic, local-first, model-free. The engine contains NO S01-S24 scenario
logic; scenarios live in stress-suite/scenarios + fixtures.
"""
from .base import HARNESS_VERSION
from .phase import PhaseStateMachine, PhaseEdgeTable, PhaseDecisionRecord
from .lifecycle import KnowledgeRecord, LifecycleEngine, LifecycleEdgeTable, TransitionRecord
from .authority import AuthorityState, CapabilityGrant, AuthorityRegistry
from .independence import IndependenceRecord, INDEPENDENCE_DIMENSIONS
from .evidence import EvidenceRecord, ContradictionRecord, EvidenceGap, EvidenceChannelVector
from .negative import NegativeKnowledgeRecord
from .unresolved import UnresolvedPatternRecord, UnresolvedGovernanceEvent
from .patch import PatchPressureRecord, PatchPressureGroup
from .affected import AffectedSurface
from .constraint import ConstraintField
from .evalcontract import PhaseEvaluationContract
from .window import TransformationWindowSpec
from .epoch import EpochManifest
from .outcome import OutcomePacket, ResumeCapsule
from .truth import CapabilityStatus, TruthRegistry
from .forbidden import ForbiddenTransitionValidator
from .governed import GovernedTransitionExecutor, TraceEntry
from .replay import DeterministicReplay, ReplayEvent, ReplayResult
from .fixtures import StressScenarioSpec, spec_to_replay_events, load_spec
from .adjudicate import (
    EvidenceAdjudicator, AdjudicatorPolicy, AdjudicatorRule, PredicateGate,
    EvidenceObservation, PhaseProposal, PolicyError,
)
from .scenario import run_scenario, evaluate_expectation, decision_view, explain_transition, ScenarioRunResult
from .registry import EvidenceRegistry, LineageSummary, UnknownEvidenceRef, DuplicateEvidenceError
from .scenariolib import ScenarioPack, load_scenario_pack, load_all_packs, SCENARIO_DIRS
from .cognitive_ecology import (
    ReviewerIndependenceProfile, DependencyGraph, ConsensusRecord, EcologyFacts,
    CognitiveEcologyHealthRecord, CorrelatedFailureRecord, AllocationProvenance,
    RegisteredReviewerProvenance, ProvenanceConflict, ReviewerProvenanceRegistry,
    SyntheticFixtureAuthority, EpistemicPathRecord, ReplicationPathRecord,
    ProvenanceConflictLedger, collect_epistemic_paths,
    PROVENANCE_MODES, DEFAULT_PROVENANCE_MODE, CAPABILITY_SOURCES, UNKNOWN,
    SAME, DIFFERENT,
    independent_confirmation_satisfied, receipt_lineage, EXPOSURE_MODES, PAIRWISE_AXES,
)
from .ecology_policy import EcologyPolicy, EcologyRule, EcologyPolicyError
from .review_topology import (
    ReviewTopology, ReviewTopologyDecision, TopologyConstraintContract,
    route_review_topology,
)
from .friction import (
    EpistemicFrictionProtocol, FrictionContract, FrictionResult, FrictionTrigger,
    FrictionAction, CounterAttractorReview, CounterAttractorSpec,
)
from .g3_runner import G3ScenarioPack, G3RunResult, load_g3_pack, run_g3_scenario, evaluate_g3_expectation
from .memory import (
    MEMORY_TIERS, KnowledgeActivationState, MemoryObject, MemoryIndex,
    MemoryCompactionRecord, MemoryRetriever, ContextBundle, RetrievalTraceEntry,
    run_metabolism_pipeline, MetabolismReport,
)
from .reopen import (
    REOPEN_OPERATORS, ReopenCondition, ReopenEvaluator, ReopenEvaluation,
    NegativeKnowledgeSuppressionDecision, decide_suppression, ReopenConditionError,
)
from .reconstruction import (
    PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT, EpochReconstructionBundle,
    EpochReconstructionReport, reconstruct_epoch, verify_epoch_chain,
)
from .memory_policy import MemoryPolicy, MemoryRule, MemoryPolicyError
from .g4_runner import G4ScenarioPack, G4RunResult, load_g4_pack, run_g4_scenario, evaluate_g4_expectation

__all__ = [
    "HARNESS_VERSION",
    "PhaseStateMachine", "PhaseEdgeTable", "PhaseDecisionRecord",
    "KnowledgeRecord", "LifecycleEngine", "LifecycleEdgeTable", "TransitionRecord",
    "AuthorityState", "CapabilityGrant", "AuthorityRegistry",
    "IndependenceRecord", "INDEPENDENCE_DIMENSIONS",
    "EvidenceRecord", "ContradictionRecord", "EvidenceGap", "EvidenceChannelVector",
    "NegativeKnowledgeRecord",
    "UnresolvedPatternRecord", "UnresolvedGovernanceEvent",
    "PatchPressureRecord", "PatchPressureGroup",
    "AffectedSurface", "ConstraintField", "PhaseEvaluationContract",
    "TransformationWindowSpec", "EpochManifest", "OutcomePacket", "ResumeCapsule",
    "CapabilityStatus", "TruthRegistry", "ForbiddenTransitionValidator",
    "GovernedTransitionExecutor", "TraceEntry",
    "DeterministicReplay", "ReplayEvent", "ReplayResult",
    "StressScenarioSpec", "spec_to_replay_events", "load_spec",
    "ReviewerIndependenceProfile", "DependencyGraph", "ConsensusRecord", "EcologyFacts",
    "CognitiveEcologyHealthRecord", "CorrelatedFailureRecord", "AllocationProvenance",
    "RegisteredReviewerProvenance", "ProvenanceConflict", "ReviewerProvenanceRegistry",
    "SyntheticFixtureAuthority", "EpistemicPathRecord", "ReplicationPathRecord",
    "ProvenanceConflictLedger", "collect_epistemic_paths",
    "PROVENANCE_MODES", "DEFAULT_PROVENANCE_MODE", "CAPABILITY_SOURCES", "UNKNOWN",
    "SAME", "DIFFERENT",
    "independent_confirmation_satisfied", "receipt_lineage", "EXPOSURE_MODES", "PAIRWISE_AXES",
    "EcologyPolicy", "EcologyRule", "EcologyPolicyError",
    "ReviewTopology", "ReviewTopologyDecision", "TopologyConstraintContract",
    "route_review_topology",
    "EpistemicFrictionProtocol", "FrictionContract", "FrictionResult", "FrictionTrigger",
    "FrictionAction", "CounterAttractorReview", "CounterAttractorSpec",
    "G3ScenarioPack", "G3RunResult", "load_g3_pack", "run_g3_scenario",
    "evaluate_g3_expectation",
    "MEMORY_TIERS", "KnowledgeActivationState", "MemoryObject", "MemoryIndex",
    "MemoryCompactionRecord", "MemoryRetriever", "ContextBundle", "RetrievalTraceEntry",
    "run_metabolism_pipeline", "MetabolismReport",
    "REOPEN_OPERATORS", "ReopenCondition", "ReopenEvaluator", "ReopenEvaluation",
    "NegativeKnowledgeSuppressionDecision", "decide_suppression", "ReopenConditionError",
    "PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT", "EpochReconstructionBundle",
    "EpochReconstructionReport", "reconstruct_epoch", "verify_epoch_chain",
    "MemoryPolicy", "MemoryRule", "MemoryPolicyError",
    "G4ScenarioPack", "G4RunResult", "load_g4_pack", "run_g4_scenario",
    "evaluate_g4_expectation",
]