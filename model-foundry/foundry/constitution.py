"""MF-B0 — Program Constitution and Scientific Boundary (machine-legible form).

MF-B0 answers one question before any dataset/model/GPU work:

    What is the Model Foundry allowed to be?

This module carries the constitutional artifacts as data: mission contract,
ownership matrix, cognitive identity contract, OCE service dependency map, child
program boundary, truth grammar, evaluation tiers, authority ceiling, budget
semantics, reproducibility classes, supply-chain trust, lifecycle separation, and
the convergence map.

Enforcement lives in :mod:`foundry.boundary`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import (
    GENERIC_SERVICE_DOUBLES,
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    Unauthorized,
    fingerprint,
)
from .enums import (
    ArtifactLifecycleState,
    BenchmarkStatus,
    CapabilityEvidenceState,
    ClaimClass,
    EvaluationTier,
    IdentityDimension,
    ReproducibilityClass,
    RunState,
    SourceRole,
    SubjectKind,
    TerminalConclusion,
    TrustClass,
)

# --------------------------------------------------------------------------
# C1.S1 — Mission contract
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FoundryMissionContract:
    mission: str
    consumers: tuple[str, ...]
    supported_research_classes: tuple[str, ...]
    explicit_non_goals: tuple[str, ...]
    relationship_to_oce: str
    relationship_to_quant_lab: str
    relationship_to_runtime_dynamics: str
    relationship_to_compute_resource_intelligence: str

    # Invariants: the mission cannot imply ownership of any of these.
    NOT_OWNED: tuple[str, ...] = (
        "institutional truth",
        "OCE authority",
        "operator identity",
        "canonical project memory",
        "production deployment",
        "live capital",
        "constitutional amendment",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission": self.mission,
            "consumers": list(self.consumers),
            "supported_research_classes": list(self.supported_research_classes),
            "explicit_non_goals": list(self.explicit_non_goals),
            "relationship_to_oce": self.relationship_to_oce,
            "relationship_to_quant_lab": self.relationship_to_quant_lab,
            "relationship_to_runtime_dynamics": self.relationship_to_runtime_dynamics,
            "relationship_to_compute_resource_intelligence": self.relationship_to_compute_resource_intelligence,
            "not_owned": list(self.NOT_OWNED),
        }


MISSION_CONTRACT = FoundryMissionContract(
    mission=(
        "Create and study replaceable cognitive artifacts, runtimes, and systems for "
        "Larger Lab, producing evidence that remains interpretable when models, "
        "frameworks, providers, and eras of AI change."
    ),
    consumers=(
        "Larger Lab research operators",
        "OCE institutional review (as evidence submitter only)",
        "future Foundry research agents",
    ),
    supported_research_classes=(
        "corpus construction and data-rights governance",
        "provider-neutral experiment compute selection",
        "frozen evaluation and capability measurement",
        "scratch-model and learning-dynamics research (child programs)",
    ),
    explicit_non_goals=(
        "become institutional truth or OCE authority",
        "choose a permanent GPU provider",
        "train the final specialist model in this block",
        "certify its own consequence-bearing runtime",
        "place trades or connect live execution",
        "replace OCE identity, authority, evidence, workflow, or memory services",
    ),
    relationship_to_oce="domain institution beneath OCE; consumes and submits to canonical services",
    relationship_to_quant_lab="provides model-side capability evidence; cannot place or authorize capital",
    relationship_to_runtime_dynamics="parent scientific institution of the RLT/PC-ALM child programs",
    relationship_to_compute_resource_intelligence=(
        "consumer/feeder of B10 Resource Intelligence (COMPUTE.GPU.RENT); never the permanent provider platform"
    ),
)


# --------------------------------------------------------------------------
# C1.S2 — Ownership matrix
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OwnershipEntry:
    state: str
    canonical_owner: str
    foundry_role: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "canonical_owner": self.canonical_owner,
            "foundry_role": self.foundry_role,
        }


OWNERSHIP_MATRIX: tuple[OwnershipEntry, ...] = (
    OwnershipEntry("Operator authority", "OCE", "consume projection only"),
    OwnershipEntry("Institutional truth", "OCE", "submit evidence/candidates"),
    OwnershipEntry("Model identity", "Foundry domain", "own"),
    OwnershipEntry(
        "Dataset lineage", "Foundry domain under OCE provenance envelope", "own payload"
    ),
    OwnershipEntry("Benchmark content", "Foundry domain", "own"),
    OwnershipEntry(
        "Evaluator activation authority",
        "OCE / governed fixture pre-convergence",
        "consume",
    ),
    OwnershipEntry(
        "Compute provider history", "OCE Resource Intelligence target", "contribute observations"
    ),
    OwnershipEntry("Training run", "Foundry domain", "own"),
    OwnershipEntry(
        "Model checkpoint",
        "Foundry domain artifact under OCE artifact envelope",
        "own payload",
    ),
    OwnershipEntry("Capability assessment", "Foundry domain evidence", "produce"),
    OwnershipEntry(
        "Global capability status",
        "OCE CapabilityGraph",
        "propose/update candidate only",
    ),
    OwnershipEntry("OCE runtime authority", "OCE", "none"),
)


def ownership_conflicts() -> tuple[str, ...]:
    """No object may have two authoritative owners."""

    counts: dict[str, int] = {}
    for entry in OWNERSHIP_MATRIX:
        counts[entry.state] = counts.get(entry.state, 0) + 1
    return tuple(sorted(state for state, n in counts.items() if n > 1))


# --------------------------------------------------------------------------
# C1.S3 — Cognitive identity contract
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CognitiveArtifactSpec:
    """Decided weights / learned artifact identity. No prompt, tool, or retrieval."""

    artifact_id: str
    base_artifact: str | None
    weights_digest: str
    input_encoder_digest: str | None
    quantization: str | None
    recipe_fingerprint: str
    lifecycle_state: str = "REGISTERED"
    kind: SubjectKind = SubjectKind.COGNITIVE_ARTIFACT

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_kind": self.kind.value,
            "artifact_id": self.artifact_id,
            "base_artifact": self.base_artifact,
            "weights_digest": self.weights_digest,
            "input_encoder_digest": self.input_encoder_digest,
            "quantization": self.quantization,
            "recipe_fingerprint": self.recipe_fingerprint,
            "lifecycle_state": self.lifecycle_state,
        }


@dataclass(frozen=True)
class CognitiveRuntimeSpec:
    """Artifact + inference engine / quantization / state semantics."""

    runtime_id: str
    artifact: CognitiveArtifactSpec
    inference_engine: str
    engine_version: str
    quantization: str | None
    state_semantics: str
    kind: SubjectKind = SubjectKind.COGNITIVE_RUNTIME

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_kind": self.kind.value,
            "runtime_id": self.runtime_id,
            "artifact": self.artifact.to_dict(),
            "inference_engine": self.inference_engine,
            "engine_version": self.engine_version,
            "quantization": self.quantization,
            "state_semantics": self.state_semantics,
        }

    @property
    def identity_fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True)
class CognitiveSystemSpec:
    """Runtime + prompts/context + retrieval + tools + scaffold."""

    system_id: str
    runtime: CognitiveRuntimeSpec
    prompt_scaffold_digest: str | None
    retrieval_corpus_fingerprint: str | None
    tool_scaffold: tuple[str, ...] = ()
    kind: SubjectKind = SubjectKind.COGNITIVE_SYSTEM

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_kind": self.kind.value,
            "system_id": self.system_id,
            "runtime": self.runtime.to_dict(),
            "prompt_scaffold_digest": self.prompt_scaffold_digest,
            "retrieval_corpus_fingerprint": self.retrieval_corpus_fingerprint,
            "tool_scaffold": list(self.tool_scaffold),
        }

    @property
    def identity_fingerprint(self) -> str:
        return fingerprint(self.to_dict())


IDENTITY_DIMENSIONS: tuple[IdentityDimension, ...] = tuple(IdentityDimension)

# A subject may only be credited at the level actually evaluated. Moving a
# system result down to artifact-only credit requires an explicit attribution
# study; there is no implicit collapse.
SUBJECT_CREDIT_RULES: dict[SubjectKind, tuple[SubjectKind, ...]] = {
    SubjectKind.COGNITIVE_ARTIFACT: (SubjectKind.COGNITIVE_ARTIFACT,),
    SubjectKind.COGNITIVE_RUNTIME: (
        SubjectKind.COGNITIVE_RUNTIME,
        SubjectKind.COGNITIVE_ARTIFACT,
    ),
    SubjectKind.COGNITIVE_SYSTEM: (
        SubjectKind.COGNITIVE_SYSTEM,
        SubjectKind.COGNITIVE_RUNTIME,
        SubjectKind.COGNITIVE_ARTIFACT,
    ),
}


def permit_credit(
    observed: SubjectKind, claimed: SubjectKind, *, attribution_study: str | None = None
) -> bool:
    """Crediting a narrower subject from a broader result requires attribution."""

    if claimed == observed:
        return True
    if claimed not in SUBJECT_CREDIT_RULES[observed]:
        return False
    return bool(attribution_study and attribution_study.strip())


# --------------------------------------------------------------------------
# C1.S4 / C10.S1 — OCE service dependency + retirement map
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceDependency:
    service: str
    currently_available: bool
    temporary_fixture: str | None
    convergence_target: str
    replacement_condition: str
    retirement_evidence: str
    double: OceTestDouble | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "currently_available_on_this_branch": self.currently_available,
            "temporary_foundry_fixture": self.temporary_fixture,
            "convergence_target": self.convergence_target,
            "replacement_condition": self.replacement_condition,
            "retirement_evidence": self.retirement_evidence,
            "noncanonical_declaration": self.double.to_dict() if self.double else None,
        }


OCE_SERVICE_DEPENDENCY_MAP: tuple[ServiceDependency, ...] = tuple(
    ServiceDependency(
        service=name,
        currently_available=False,
        temporary_fixture=double.fixture,
        convergence_target=double.canonical_oce_target,
        replacement_condition=double.replacement_condition,
        retirement_evidence=double.retirement_evidence,
        double=double,
    )
    for name, double in sorted(GENERIC_SERVICE_DOUBLES.items())
) + (
    ServiceDependency(
        service="incident_handling",
        currently_available=False,
        temporary_fixture=None,
        convergence_target="OCE incident handling",
        replacement_condition="consumed only when Foundry reaches operational deployment",
        retirement_evidence="no Foundry-local incident authority exists at any point",
        double=None,
    ),
    ServiceDependency(
        service="approvals",
        currently_available=False,
        temporary_fixture=None,
        convergence_target="OCE approval/ratification path",
        replacement_condition="consumed at first consequence-bearing promotion request",
        retirement_evidence="MF-B5+ promotion requests route through OCE approval",
        double=None,
    ),
)


def undeclared_generic_services() -> tuple[str, ...]:
    """Generic services without a retirement path are a permanent-duplicate risk."""

    missing = []
    for dep in OCE_SERVICE_DEPENDENCY_MAP:
        if dep.temporary_fixture and not (
            dep.convergence_target and dep.replacement_condition and dep.retirement_evidence
        ):
            missing.append(dep.service)
    return tuple(sorted(missing))


# --------------------------------------------------------------------------
# C1.S5 — Child program boundary
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChildProgram:
    program: str
    relation: str
    independent_branch_allowed: bool
    promotion_terminus: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "program": self.program,
            "relation": self.relation,
            "independent_branch_allowed": self.independent_branch_allowed,
            "promotion_terminus": self.promotion_terminus,
        }


CHILD_PROGRAM_BOUNDARY_MAP: tuple[ChildProgram, ...] = (
    ChildProgram(
        "useful specialist-model track",
        "Foundry child track",
        True,
        "Foundry -> OCE evidence review",
    ),
    ChildProgram("scratch-model laboratory", "Foundry child track", True, "Foundry -> OCE evidence review"),
    ChildProgram(
        "Runtime Dynamics Program / RLT",
        "separately versioned child research program consumed by MF-B10; never rebuilt inside it",
        True,
        "Runtime Dynamics evidence registered back into Foundry, then OCE review",
    ),
    ChildProgram(
        "learning-dynamics track / PC-ALM",
        "Foundry child track",
        True,
        "Foundry -> OCE evidence review",
    ),
)


def self_promotion_blocked(program: str, terminus: str) -> bool:
    """Every child-program promotion route must terminate outside the program."""

    node = next((c for c in CHILD_PROGRAM_BOUNDARY_MAP if c.program == program), None)
    if node is None:
        raise PolicyBlocked("CHILD_PROGRAM_UNKNOWN", f"unknown child program {program!r}")
    return terminus != node.promotion_terminus


# --------------------------------------------------------------------------
# C2.S1 — Truth grammar
# --------------------------------------------------------------------------


TRUTH_GRAMMAR: tuple[str, ...] = (
    "OUTPUT_OR_MEASUREMENT",
    "OBSERVATION",
    "EVIDENCE",
    "CLAIM_ASSESSMENT",
    "DOMAIN_CAPABILITY_CANDIDATE",
    "OCE_REVIEW",
)

FORBIDDEN_SHORTCUTS: tuple[str, ...] = (
    "score -> capability truth",
    "model prose -> evidence",
    "benchmark win -> production readiness",
    "paper claim -> architecture fact",
    "PnL -> scientific validity",
)


# --------------------------------------------------------------------------
# C2.S2 — Evaluation tier contract
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TierRule:
    tier: EvaluationTier
    visible_to_builder: str
    may_influence_training: bool
    exposure_counted: bool
    answer_key_access: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value,
            "visible_to_builder": self.visible_to_builder,
            "may_influence_training": self.may_influence_training,
            "exposure_counted": self.exposure_counted,
            "answer_key_access": self.answer_key_access,
        }


EVALUATION_TIER_CONTRACT: tuple[TierRule, ...] = (
    TierRule(
        EvaluationTier.DEVELOPMENT,
        "tasks and answers may be visible",
        True,
        True,
        "open",
    ),
    TierRule(
        EvaluationTier.PROMOTION,
        "dimensions and high-level rules visible; unrestricted answer keys not visible",
        False,
        True,
        "restricted",
    ),
    TierRule(
        EvaluationTier.SEALED_CONFIRMATION,
        "existence and outcome only",
        False,
        True,
        "isolated",
    ),
)


# --------------------------------------------------------------------------
# C5.S1 — Authority ceiling
# --------------------------------------------------------------------------


FOUNDRY_FORBIDDEN_AUTHORITIES: tuple[str, ...] = (
    "deploy_production_oce_runtime",
    "self_grant_oce_tools",
    "change_oce_constitution",
    "place_trade",
    "connect_live_broker_or_exchange",
    "approve_own_evaluator_change",
    "certify_own_consequence_bearing_runtime",
    "launch_paid_compute_without_operator_authorization",
    "write_global_capability_status",
    "amend_doctrine",
)


def assert_within_authority_ceiling(action: str) -> None:
    if action in FOUNDRY_FORBIDDEN_AUTHORITIES:
        raise Unauthorized(
            "AUTHORITY_CEILING_EXCEEDED",
            f"Model Foundry may never perform {action!r}",
            action=action,
        )


# --------------------------------------------------------------------------
# C5.S2 — Resource budget contract (configurable, not architectural law)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourceBudget:
    """Live configuration. The $10-30/week operator envelope is a value, not law."""

    name: str
    dollars_per_week: float | None = None
    accelerator_hours: float | None = None
    storage_gb: float | None = None
    egress_gb: float | None = None
    wall_clock_hours: float | None = None
    model_api_units: float | None = None
    operator_interruptions: int | None = None
    requires_operator_authorization_above: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dollars_per_week": self.dollars_per_week,
            "accelerator_hours": self.accelerator_hours,
            "storage_gb": self.storage_gb,
            "egress_gb": self.egress_gb,
            "wall_clock_hours": self.wall_clock_hours,
            "model_api_units": self.model_api_units,
            "operator_interruptions": self.operator_interruptions,
            "requires_operator_authorization_above": self.requires_operator_authorization_above,
        }

    def check(self, *, dollars: float = 0.0, accelerator_hours: float = 0.0) -> None:
        """Budget exhaustion produces hold/underpowered state, never spend."""

        if self.dollars_per_week is not None and dollars > self.dollars_per_week:
            raise PolicyBlocked(
                "BUDGET_BLOCKED",
                "projected dollars exceed configured weekly envelope; hold for operator",
                projected=dollars,
                envelope=self.dollars_per_week,
            )
        if self.accelerator_hours is not None and accelerator_hours > self.accelerator_hours:
            raise PolicyBlocked(
                "BUDGET_BLOCKED",
                "projected accelerator hours exceed configured envelope; hold for operator",
                projected=accelerator_hours,
                envelope=self.accelerator_hours,
            )


DEFAULT_BUDGET = ResourceBudget(
    name="operator default research envelope",
    dollars_per_week=30.0,
    accelerator_hours=4.0,
    storage_gb=200.0,
    egress_gb=50.0,
    wall_clock_hours=12.0,
    operator_interruptions=20,
    requires_operator_authorization_above=0.0,
)


# --------------------------------------------------------------------------
# C6.S1 — Reproducibility classes
# --------------------------------------------------------------------------


REPRODUCIBILITY_CLASSES: tuple[ReproducibilityClass, ...] = tuple(ReproducibilityClass)


@dataclass(frozen=True)
class ReproducibilityClaim:
    """A claim may only name the strongest class actually supported."""

    claimed: ReproducibilityClass
    environment_recorded: bool
    independent_implementation: bool
    external_replication: bool
    framework: str | None = None
    dependency_lock_digest: str | None = None
    container_digest: str | None = None
    accelerator_identity: str | None = None
    driver_stack: str | None = None
    provider_details: str | None = None

    def supported_class(self) -> ReproducibilityClass:
        if not self.environment_recorded or not all(
            (self.framework, self.dependency_lock_digest, self.accelerator_identity, self.driver_stack)
        ):
            return ReproducibilityClass.R0_EXACT_REPLAY if self.environment_recorded else ReproducibilityClass.R0_EXACT_REPLAY
        if self.external_replication:
            return ReproducibilityClass.R3_EXTERNAL_DOMAIN_REPLICATION
        if self.independent_implementation:
            return ReproducibilityClass.R2_INDEPENDENT_IMPLEMENTATION
        if self.container_digest or self.dependency_lock_digest:
            return ReproducibilityClass.R1_FRESH_ENVIRONMENT_REPLAY
        return ReproducibilityClass.R0_EXACT_REPLAY

    def validate(self) -> None:
        if self.claimed != self.supported_class():
            raise PolicyBlocked(
                "REPRODUCIBILITY_OVERCLAIM",
                "claim names a stronger reproducibility class than the evidence supports",
                claimed=self.claimed.value,
                supported=self.supported_class().value,
            )


# --------------------------------------------------------------------------
# C7.S1 / C7.S5 — Supply-chain trust
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TrustClassification:
    subject: str
    trust_class: TrustClass
    requires_remote_code: bool
    unsafe_serialization: bool
    pinned_digest: str | None
    human_version: str | None

    def admit_to_trusted_runtime(self) -> None:
        if self.unsafe_serialization or self.requires_remote_code:
            raise PolicyBlocked(
                "SUPPLY_CHAIN_UNSAFE_RUNTIME_ENTRY",
                f"{self.subject!r} cannot silently enter the trusted runtime class",
                subject=self.subject,
            )
        if self.trust_class in {
            TrustClass.SECRET_BEARING_PROHIBITED_REMOTE,
            TrustClass.PRIVATE_OPERATOR,
        }:
            raise PolicyBlocked(
                "SUPPLY_CHAIN_TRUST_CLASS_BLOCKED",
                f"{self.subject!r} is not admissible to the trusted runtime class",
                subject=self.subject,
            )


@dataclass(frozen=True)
class DependencyPin:
    name: str
    human_version: str
    pinned_digest: str
    observed_digest: str

    def verify(self) -> None:
        if self.pinned_digest != self.observed_digest:
            raise PolicyBlocked(
                "PROVENANCE_MISMATCH",
                "same human-readable version resolved to different upstream bytes",
                dependency=self.name,
                version=self.human_version,
            )


# --------------------------------------------------------------------------
# C9 — Lifecycle separation
# --------------------------------------------------------------------------


def _states(enum: Any) -> tuple[str, ...]:
    """One machine per declared vocabulary: the enum is the only owner."""

    return tuple(member.value for member in enum)


LIFECYCLE_MACHINES: dict[str, tuple[str, ...]] = {
    "source_role": _states(SourceRole),
    "experiment_run": _states(RunState),
    "cognitive_artifact": _states(ArtifactLifecycleState),
    "benchmark": _states(BenchmarkStatus),
    "capability_evidence": _states(CapabilityEvidenceState),
    "oce_authority": ("NONE",),  # owned outside the Foundry lifecycle
}


@dataclass(frozen=True)
class LifecycleSnapshot:
    """Divergent legitimate state must be representable without one overall status."""

    source_role: str
    experiment_run: str
    cognitive_artifact: str
    benchmark: str
    capability_evidence: str
    oce_authority: str = "NONE"

    def validate(self) -> None:
        for machine, state in self.to_dict().items():
            if state not in LIFECYCLE_MACHINES[machine]:
                raise PolicyBlocked(
                    "LIFECYCLE_STATE_INVALID",
                    f"{machine}={state!r} is not a valid state of that machine",
                    machine=machine,
                    state=state,
                )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_role": self.source_role,
            "experiment_run": self.experiment_run,
            "cognitive_artifact": self.cognitive_artifact,
            "benchmark": self.benchmark,
            "capability_evidence": self.capability_evidence,
            "oce_authority": self.oce_authority,
        }

    def collapse_to_single_status(self) -> None:
        raise PolicyBlocked(
            "LIFECYCLE_COLLAPSE_REFUSED",
            "Foundry state machines are separate by constitution and cannot be merged",
            state=self.to_dict(),
        )


# --------------------------------------------------------------------------
# C10 — Convergence map
# --------------------------------------------------------------------------


CONVERGENCE_MAP: dict[str, Any] = {
    "authority": {"duplicated": False, "owner": "OCE"},
    "truth": {"duplicated": False, "owner": "OCE"},
    "memory": {"duplicated": False, "owner": "OCE"},
    "generic_workflow": {"duplicated": False, "owner": "OCE WorkGraph target"},
    "generic_evidence_lifecycle": {"duplicated": False, "owner": "OCE EvidenceGraph target"},
    "provider_specific_infrastructure": {"duplicated": False, "owner": "OCE B10 Resource Intelligence"},
}


# --------------------------------------------------------------------------
# Doctrine strings (the Foundry's own inequality set)
# --------------------------------------------------------------------------


FOUNDRY_DOCTRINE: tuple[str, ...] = (
    "MODEL OUTPUT != INSTITUTIONAL TRUTH",
    "WEIGHTS != CANONICAL MEMORY",
    "CAPABILITY != AUTHORITY",
    "ACCESS != RIGHTS",
    "AVAILABLE DATA != TRAINABLE DATA",
    "BENCHMARK SCORE != CAPABILITY",
    "PROVIDER OFFER != GUARANTEE",
    "HOURLY PRICE != COST-TO-CLOSE",
    "REGISTERED SOURCE != CLEAN SOURCE",
    "HIDDEN EVAL != DEVELOPMENT DATA",
    "NEGATIVE RESULT != FAILED PROJECT",
    "UNKNOWN != FAVORABLE",
)


@dataclass(frozen=True)
class ConstitutionalArtifacts:
    """The MF-B0 artifact set as one object, fingerprintable as a whole."""

    mission_contract: FoundryMissionContract = MISSION_CONTRACT
    ownership_matrix: tuple[OwnershipEntry, ...] = OWNERSHIP_MATRIX
    identity_dimensions: tuple[IdentityDimension, ...] = IDENTITY_DIMENSIONS
    service_dependencies: tuple[ServiceDependency, ...] = OCE_SERVICE_DEPENDENCY_MAP
    child_programs: tuple[ChildProgram, ...] = CHILD_PROGRAM_BOUNDARY_MAP
    truth_grammar: tuple[str, ...] = TRUTH_GRAMMAR
    forbidden_shortcuts: tuple[str, ...] = FORBIDDEN_SHORTCUTS
    evaluation_tiers: tuple[TierRule, ...] = EVALUATION_TIER_CONTRACT
    forbidden_authorities: tuple[str, ...] = FOUNDRY_FORBIDDEN_AUTHORITIES
    reproducibility_classes: tuple[ReproducibilityClass, ...] = REPRODUCIBILITY_CLASSES
    lifecycle_machines: FrozenMap = field(default_factory=lambda: FrozenMap(
        {k: list(v) for k, v in LIFECYCLE_MACHINES.items()}
    ))
    convergence_map: FrozenMap = field(default_factory=lambda: FrozenMap(CONVERGENCE_MAP))
    doctrine: tuple[str, ...] = FOUNDRY_DOCTRINE
    claim_classes: tuple[ClaimClass, ...] = tuple(ClaimClass)
    terminal_conclusions: tuple[TerminalConclusion, ...] = tuple(TerminalConclusion)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_contract": self.mission_contract.to_dict(),
            "ownership_matrix": [e.to_dict() for e in self.ownership_matrix],
            "identity_dimensions": [d.value for d in self.identity_dimensions],
            "service_dependencies": [d.to_dict() for d in self.service_dependencies],
            "child_programs": [c.to_dict() for c in self.child_programs],
            "truth_grammar": list(self.truth_grammar),
            "forbidden_shortcuts": list(self.forbidden_shortcuts),
            "evaluation_tiers": [t.to_dict() for t in self.evaluation_tiers],
            "forbidden_authorities": list(self.forbidden_authorities),
            "reproducibility_classes": [r.value for r in self.reproducibility_classes],
            "lifecycle_machines": self.lifecycle_machines.to_dict(),
            "convergence_map": self.convergence_map.to_dict(),
            "doctrine": list(self.doctrine),
            "claim_classes": [c.value for c in self.claim_classes],
            "terminal_conclusions": [t.value for t in self.terminal_conclusions],
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


CONSTITUTION = ConstitutionalArtifacts()
