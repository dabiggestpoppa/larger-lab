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
]