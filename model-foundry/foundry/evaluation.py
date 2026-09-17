"""MF-B4 — Frozen Evaluation Institution.

Answers:

    What may be measured, under which protocol, with which subject credited, and
    what may never be seen by the builder?

Doctrine enforced here:

    BENCHMARK SCORE != CAPABILITY
    HIDDEN EVAL != DEVELOPMENT DATA
    NEGATIVE RESULT != FAILED PROJECT
    MODEL OUTPUT != INSTITUTIONAL TRUTH

The institution freezes criteria *before* candidate outcomes exist, keeps sealed
answer material out of the builder path, credits the subject actually evaluated,
and reports capability as a vector with no master scalar.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .boundary import assert_conclusion_allowed, assert_subject_credit
from .constitution import EVALUATION_TIER_CONTRACT, ReproducibilityClaim
from .core import (
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    Receipt,
    Unauthorized,
    fingerprint,
    utc_now_iso,
)
from .enums import (
    CLAIM_DEGRADING_CONTAMINATION,
    EXPOSURE_BUDGET_BY_TIER,
    CapabilityEvidenceState,
    ClaimClass,
    ContaminationClass,
    EvaluationTier,
    ExposureType,
    SubjectKind,
    TIER_RANK,
    TerminalConclusion,
    TrustClass,
)

EVAL_DOUBLE = OceTestDouble(
    fixture="FoundryLocalEvaluationFreeze",
    canonical_oce_target="OCE B6 Evaluation Service / CEREBUS-governed evaluator freeze (G6 lineage)",
    replacement_condition="replace when OCE owns evaluator freeze/ratification authority",
    retirement_evidence="protocol freeze receipts are issued by the canonical evaluator service",
)

NEGATIVE_KNOWLEDGE_DOUBLE = OceTestDouble(
    fixture="FoundryLocalNegativeKnowledge",
    canonical_oce_target="OCE NegativeKnowledge with governed reopen semantics (A-004/A-009 lineage)",
    replacement_condition="replace when canonical NegativeKnowledge service is consumable",
    retirement_evidence="reopen conditions evaluated by canonical lifecycle, not locally",
)

#: Roles allowed to touch sealed material at all.
SEALED_ACCESS_ROLES = frozenset({"SEALED_EVALUATOR"})

#: Roles that constitute the normal builder surface.
BUILDER_ROLES = frozenset(
    {"BUILDER_AGENT", "RESEARCHER", "TRAINING_OPERATOR", "REVIEWER_AGENT"}
)


# --------------------------------------------------------------------------
# Protocol
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkItem:
    item_id: str
    task_class: str
    expected_answer: str
    difficulty: str
    source_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "task_class": self.task_class,
            "expected_answer": self.expected_answer,
            "difficulty": self.difficulty,
            "source_id": self.source_id,
        }


@dataclass(frozen=True)
class BenchmarkSpec:
    """Benchmark identity and lifecycle. Relabeling is not an upgrade."""

    benchmark_id: str
    version: str
    task_class: str
    items: tuple[BenchmarkItem, ...]
    tier: EvaluationTier
    status: str = "DRAFT"
    contamination_grade: ContaminationClass = ContaminationClass.C0_NO_OBSERVED_OVERLAP
    exposure_count: int = 0

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "benchmark_id": self.benchmark_id,
                "version": self.version,
                "task_class": self.task_class,
                "tier": self.tier.value,
                "items": [i.to_dict() for i in self.items],
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "task_class": self.task_class,
            "item_count": len(self.items),
            "item_ids": [i.item_id for i in self.items],
            "tier": self.tier.value,
            "status": self.status,
            "contamination_grade": self.contamination_grade.value,
            "exposure_count": self.exposure_count,
            "fingerprint": self.fingerprint,
        }

    def degraded(self) -> bool:
        return self.contamination_grade in CLAIM_DEGRADING_CONTAMINATION or self.status in {
            "DEGRADED",
            "COMPROMISED",
            "STALE",
            "RETIRED",
        }


@dataclass(frozen=True)
class MetricSpec:
    """A single evaluation dimension. Deliberately not aggregated."""

    name: str
    description: str
    direction: str  # HIGHER_IS_BETTER / LOWER_IS_BETTER / TARGET
    #: fraction of total weight used only for readability, never for a master score
    reported_weight: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "direction": self.direction,
            "reported_weight": self.reported_weight,
        }


@dataclass(frozen=True)
class EvaluationProtocol:
    """Criteria that must exist before outcomes are known."""

    protocol_id: str
    version: str
    benchmark: BenchmarkSpec
    metrics: tuple[MetricSpec, ...]
    min_items_for_power: int
    required_seeds: int
    baseline_reference: str
    tolerance: float
    decision_rules: tuple[str, ...]
    tier: EvaluationTier
    author: str
    frozen_at_utc: str | None = None
    framework_lock: str | None = None

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "protocol_id": self.protocol_id,
                "version": self.version,
                "benchmark_fingerprint": self.benchmark.fingerprint,
                "metrics": [m.to_dict() for m in self.metrics],
                "min_items_for_power": self.min_items_for_power,
                "required_seeds": self.required_seeds,
                "baseline_reference": self.baseline_reference,
                "tolerance": self.tolerance,
                "decision_rules": list(self.decision_rules),
                "tier": self.tier.value,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        contract = next(t for t in EVALUATION_TIER_CONTRACT if t.tier == self.tier)
        return {
            "protocol_id": self.protocol_id,
            "version": self.version,
            "benchmark": self.benchmark.to_dict(),
            "metrics": [m.to_dict() for m in self.metrics],
            "min_items_for_power": self.min_items_for_power,
            "required_seeds": self.required_seeds,
            "baseline_reference": self.baseline_reference,
            "tolerance": self.tolerance,
            "decision_rules": list(self.decision_rules),
            "tier": self.tier.value,
            "tier_contract": contract.to_dict(),
            "author": self.author,
            "frozen_at_utc": self.frozen_at_utc,
            "framework_lock": self.framework_lock,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class FrozenEvaluationProtocol:
    """A protocol sealed for a tier. The freeze is the scientific commitment."""

    protocol: EvaluationProtocol
    frozen_utc: str
    freeze_reason: str
    exposure_at_freeze: int
    registrar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol.to_dict(),
            "protocol_fingerprint": self.protocol.fingerprint,
            "frozen_utc": self.frozen_utc,
            "freeze_reason": self.freeze_reason,
            "exposure_at_freeze": self.exposure_at_freeze,
            "registrar": self.registrar,
            "criteria_frozen_before_outcomes": True,
        }


def freeze_protocol(
    protocol: EvaluationProtocol,
    *,
    registrar: str,
    freeze_reason: str,
    candidate_outcomes_observed: bool,
    actor_is_builder: bool,
    now_iso: str | None = None,
) -> FrozenEvaluationProtocol:
    """Freeze criteria. A protocol cannot be frozen after peeking at outcomes.

    ``now_iso`` exists so a replay can freeze on a fixed clock and produce
    byte-identical receipts; the real clock is only used when a caller does not
    supply one.
    """

    if not str(freeze_reason).strip():
        raise PolicyBlocked("FREEZE_REASON_REQUIRED", "a freeze must record why it happens")
    if candidate_outcomes_observed:
        raise PolicyBlocked(
            "FREEZE_AFTER_OUTCOMES_REFUSED",
            "criteria must be frozen before candidate outcomes are observed",
        )
    if actor_is_builder and protocol.tier is EvaluationTier.SEALED_CONFIRMATION:
        raise Unauthorized(
            "SEALED_FREEZE_BUILDER_REFUSED",
            "a builder cannot author the sealed freeze that will judge it",
        )
    if not protocol.decision_rules:
        raise PolicyBlocked(
            "DECISION_RULES_REQUIRED",
            "a protocol without pre-declared decision rules cannot support a conclusion",
        )
    stamp = now_iso or utc_now_iso()
    frozen = replace(protocol, frozen_at_utc=stamp)
    return FrozenEvaluationProtocol(
        protocol=frozen,
        frozen_utc=frozen.frozen_at_utc or stamp,
        freeze_reason=freeze_reason,
        exposure_at_freeze=protocol.benchmark.exposure_count,
        registrar=registrar,
    )


def assert_protocol_unchanged(frozen: FrozenEvaluationProtocol, candidate: EvaluationProtocol) -> None:
    """Instruction-defining truth may change; evaluation-defining truth may not."""

    if candidate.fingerprint != frozen.protocol.fingerprint:
        raise Unauthorized(
            "PROTOCOL_MUTATION_REFUSED",
            "a frozen protocol cannot be edited; register a new version through the tier contract",
            frozen=frozen.protocol.fingerprint,
            candidate=candidate.fingerprint,
        )


# --------------------------------------------------------------------------
# Sealed store (builder boundary)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SealedPayload:
    payload_id: str
    benchmark_id: str
    tier: EvaluationTier
    answer_key_digest: str
    items: tuple[str, ...]
    doctrine_bearing: bool = False

    def to_dict_public(self) -> dict[str, Any]:
        """Existence and digest only: this is what the builder surface may see."""

        return {
            "payload_id": self.payload_id,
            "benchmark_id": self.benchmark_id,
            "tier": self.tier.value,
            "answer_key_digest": self.answer_key_digest,
            "item_count": len(self.items),
            "contents_available_to_builder": False,
            "doctrine_bearing": self.doctrine_bearing,
        }


@dataclass(frozen=True)
class ExposureEvent:
    exposure_type: ExposureType
    subject: str
    actor: str
    tier: EvaluationTier
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "exposure_type": self.exposure_type.value,
            "subject": self.subject,
            "actor": self.actor,
            "tier": self.tier.value,
            "detail": self.detail,
        }

    @property
    def compromising(self) -> bool:
        from .enums import COMPROMISING_EXPOSURES

        return self.exposure_type in COMPROMISING_EXPOSURES


@dataclass
class SealedEvaluationStore:
    """Answer material that the builder path cannot reach.

    Every successful or refused access is recorded. Refusals are evidence too:
    an attempt to reach sealed material is exactly what this boundary exists to
    reveal.
    """

    double: OceTestDouble = field(default=EVAL_DOUBLE)
    _payloads: dict[str, SealedPayload] = field(default_factory=dict, init=False)
    _exposures: list[ExposureEvent] = field(default_factory=list, init=False)
    _refusals: list[dict[str, Any]] = field(default_factory=list, init=False)
    _access_tokens: dict[str, str] = field(default_factory=dict, init=False)

    def register(self, payload: SealedPayload, *, registrar_role: str) -> None:
        if registrar_role not in SEALED_ACCESS_ROLES:
            raise Unauthorized(
                "SEALED_REGISTRATION_ROLE_REFUSED",
                f"{registrar_role!r} may not register sealed material",
            )
        if not payload.answer_key_digest.strip():
            raise PolicyBlocked(
                "SEALED_PAYLOAD_DIGEST_REQUIRED",
                f"{payload.payload_id}: sealed payload requires an answer-key digest",
            )
        if payload.payload_id in self._payloads:
            raise PolicyBlocked(
                "SEALED_PAYLOAD_IMMUTABLE",
                f"{payload.payload_id}: sealed payloads are immutable; register a new payload id",
            )
        self._payloads[payload.payload_id] = payload

    def issue_access_token(self, payload_id: str, *, operator_actor: str, purpose: str) -> str:
        """Only an operator issues sealed access, and only for a stated purpose."""

        if operator_actor != "OPERATOR":
            raise Unauthorized(
                "SEALED_ACCESS_OPERATOR_REQUIRED",
                "sealed access tokens are issued by the operator",
            )
        if not str(purpose).strip():
            raise PolicyBlocked("SEALED_PURPOSE_REQUIRED", "sealed access requires a stated purpose")
        token = fingerprint({"payload": payload_id, "purpose": purpose, "issuer": operator_actor})[:26]
        self._access_tokens[token] = payload_id
        return token

    def builder_view(self) -> tuple[dict[str, Any], ...]:
        """What the normal builder surface may see: existence and digests only."""

        return tuple(
            payload.to_dict_public() for payload in sorted(self._payloads.values(), key=lambda p: p.payload_id)
        )

    def read(
        self,
        payload_id: str,
        *,
        actor: str,
        role: str,
        purpose: str,
        access_token: str | None = None,
    ) -> tuple[str, ...]:
        """Read sealed items. Refusal is recorded, not silent."""

        payload = self._payloads.get(payload_id)
        if payload is None:
            raise PolicyBlocked("SEALED_PAYLOAD_UNRESOLVED", f"no sealed payload {payload_id!r}")

        if role in BUILDER_ROLES:
            self._refusals.append(
                {"actor": actor, "role": role, "payload_id": payload_id, "reason": "BUILDER_SURFACE"}
            )
            raise Unauthorized(
                "SEALED_ACCESS_BUILDER_REFUSED",
                "sealed confirmation material is never available through the builder surface",
                payload=payload_id,
            )
        if role not in SEALED_ACCESS_ROLES:
            self._refusals.append(
                {"actor": actor, "role": role, "payload_id": payload_id, "reason": "ROLE_NOT_SEALED"}
            )
            raise Unauthorized(
                "SEALED_ACCESS_ROLE_NOT_PERMITTED",
                f"role {role!r} may not read sealed material",
            )
        if not access_token or self._access_tokens.get(access_token) != payload_id:
            self._refusals.append(
                {"actor": actor, "role": role, "payload_id": payload_id, "reason": "NO_VALID_TOKEN"}
            )
            raise Unauthorized(
                "SEALED_ACCESS_TOKEN_REQUIRED",
                "sealed access requires an operator-issued token for this payload",
            )

        self._exposures.append(
            ExposureEvent(
                exposure_type=ExposureType.ACCESSED_SEALED_PAYLOAD,
                subject=payload_id,
                actor=actor,
                tier=payload.tier,
                detail=purpose,
            )
        )
        return payload.items

    # -- evidence surfaces ------------------------------------------------

    def exposures(self) -> tuple[ExposureEvent, ...]:
        return tuple(self._exposures)

    def refusals(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._refusals)

    def exposure_budget_ok(self, tier: EvaluationTier) -> bool:
        budget = EXPOSURE_BUDGET_BY_TIER[tier]
        count = sum(1 for e in self._exposures if e.tier == tier)
        return count <= budget

    def receipt(self) -> Receipt:
        return Receipt(
            kind="sealed_eval.store",
            subject="sealed_store",
            payload={
                "payloads": [p.to_dict_public() for p in self._payloads.values()],
                "exposures": [e.to_dict() for e in self._exposures],
                "refusals": list(self._refusals),
                "builder_surface_contains_contents": False,
            },
        )


# --------------------------------------------------------------------------
# Runs and capability vector
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationObservation:
    """One measured outcome for one metric on one subject."""

    metric: str
    value: float
    item_count: int
    seed: int
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "item_count": self.item_count,
            "seed": self.seed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class EvaluationRun:
    run_id: str
    frozen_protocol: FrozenEvaluationProtocol
    subject_kind: SubjectKind
    subject_id: str
    observations: tuple[EvaluationObservation, ...]
    framework: str
    framework_version: str
    runtime_identity: str
    contamination_grade: ContaminationClass
    started_utc: str
    completed_utc: str
    seeds_used: int
    failures: tuple[str, ...] = ()

    @property
    def protocol_fingerprint(self) -> str:
        return self.frozen_protocol.protocol.fingerprint

    def sample_size(self) -> int:
        return max((o.item_count for o in self.observations), default=0)

    def power_adequate(self) -> bool:
        protocol = self.frozen_protocol.protocol
        return (
            self.sample_size() >= protocol.min_items_for_power
            and self.seeds_used >= protocol.required_seeds
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "protocol_fingerprint": self.protocol_fingerprint,
            "tier": self.frozen_protocol.protocol.tier.value,
            "subject_kind": self.subject_kind.value,
            "subject_id": self.subject_id,
            "observations": [o.to_dict() for o in self.observations],
            "framework": self.framework,
            "framework_version": self.framework_version,
            "runtime_identity": self.runtime_identity,
            "contamination_grade": self.contamination_grade.value,
            "started_utc": self.started_utc,
            "completed_utc": self.completed_utc,
            "seeds_used": self.seeds_used,
            "failures": list(self.failures),
            "sample_size": self.sample_size(),
            "power_adequate": self.power_adequate(),
            "run_is_capability_truth": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True)
class ReproductionEvidence:
    """Evidence that a *different* runtime reproduced the measurement.

    A list of framework names is a claim; agreement within a declared tolerance
    is evidence. Without this object no result may claim cross-framework
    agreement, and no result may conclude PASS.
    """

    frameworks: tuple[str, ...]
    metric_agreement: FrozenMap
    max_delta: float
    tolerance: float
    evidence_ref: str
    simulated: bool = False

    def agrees_with(self, framework: str) -> bool:
        others = [f for f in self.frameworks if f != framework]
        return bool(others) and all(bool(v) for v in self.metric_agreement.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "frameworks": list(self.frameworks),
            "metric_agreement": dict(self.metric_agreement),
            "max_delta": self.max_delta,
            "tolerance": self.tolerance,
            "evidence_ref": self.evidence_ref,
            "simulated": self.simulated,
            "within_tolerance": self.max_delta <= self.tolerance,
        }


@dataclass(frozen=True)
class CapabilityAssessment:
    """Vector-valued capability evidence. There is no master score."""

    assessment_id: str
    run_id: str
    subject_kind: SubjectKind
    subject_id: str
    tier: EvaluationTier
    dimensions: FrozenMap
    evidence_state: CapabilityEvidenceState
    framework_dependence: str
    limitations: tuple[str, ...]
    baseline_reference: str
    baseline_delta: FrozenMap
    oce_review_ref: str | None
    terminal_conclusion: TerminalConclusion
    reproducibility: dict[str, Any]
    negative_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "run_id": self.run_id,
            "subject_kind": self.subject_kind.value,
            "subject_id": self.subject_id,
            "tier": self.tier.value,
            "dimensions": dict(self.dimensions),
            "evidence_state": self.evidence_state.value,
            "framework_dependence": self.framework_dependence,
            "limitations": list(self.limitations),
            "baseline_reference": self.baseline_reference,
            "baseline_delta": dict(self.baseline_delta),
            "oce_review_ref": self.oce_review_ref,
            "terminal_conclusion": self.terminal_conclusion.value,
            "reproducibility": self.reproducibility,
            "negative_result": self.negative_result,
            "master_score": None,
            "master_score_is_forbidden": True,
            "writes_global_capability_status": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


def assess_capability(
    run: EvaluationRun,
    *,
    baseline: dict[str, float],
    replication: ReproductionEvidence | None,
    limitations: tuple[str, ...],
    oce_review_ref: str | None,
    reproducibility: ReproducibilityClaim,
) -> CapabilityAssessment:
    """Derive a vector of dimension deltas plus a truthful terminal conclusion.

    PASS requires: a powered run, clean contamination, an intact benchmark, and
    *evidence* that an independent runtime reproduced the same measurements.
    Anything less terminates as INCONCLUSIVE / UNDERPOWERED / CONTAMINATED.
    """

    protocol = run.frozen_protocol.protocol
    dimensions: dict[str, Any] = {}
    for observation in run.observations:
        base = baseline.get(observation.metric)
        dimensions[observation.metric] = {
            "value": observation.value,
            "baseline": base,
            "delta": None if base is None else observation.value - base,
            "direction": next(
                (m.direction for m in protocol.metrics if m.name == observation.metric), "UNKNOWN"
            ),
            "item_count": observation.item_count,
            "seed": observation.seed,
        }

    if protocol.framework_lock:
        framework_dependence = "FRAMEWORK_LOCKED"
        independent_replication = False
    elif replication is None:
        framework_dependence = "FRAMEWORK_UNVERIFIED"
        independent_replication = False
    elif not [f for f in replication.frameworks if f != run.framework]:
        framework_dependence = "SINGLE_FRAMEWORK"
        independent_replication = False
    elif not (replication.agrees_with(run.framework) and replication.max_delta <= replication.tolerance):
        framework_dependence = "CROSS_FRAMEWORK_DISAGREEMENT"
        independent_replication = False
    elif replication.simulated:
        # Agreement obtained by simulation is not independent replication: it
        # strengthens confidence in the harness, never in the capability claim.
        framework_dependence = "CROSS_FRAMEWORK_AGREED_SIMULATED"
        independent_replication = False
    else:
        framework_dependence = "CROSS_FRAMEWORK_AGREED"
        independent_replication = True

    limitations = tuple(limitations) + (
        ("single framework: no independent runtime replication",)
        if framework_dependence != "CROSS_FRAMEWORK_AGREED"
        else ()
    )

    if run.contamination_grade in CLAIM_DEGRADING_CONTAMINATION:
        conclusion = TerminalConclusion.CONTAMINATED
    elif not run.power_adequate():
        conclusion = TerminalConclusion.UNDERPOWERED
    elif run.failures:
        conclusion = TerminalConclusion.INCONCLUSIVE
    elif protocol.benchmark.degraded():
        conclusion = TerminalConclusion.INCONCLUSIVE
    elif not independent_replication:
        conclusion = TerminalConclusion.INCONCLUSIVE
    else:
        conclusion = TerminalConclusion.PASS

    evidence_state = {
        TerminalConclusion.PASS: CapabilityEvidenceState.REPRODUCED
        if independent_replication
        else CapabilityEvidenceState.MEASURED,
        TerminalConclusion.INCONCLUSIVE: CapabilityEvidenceState.MEASURED,
    }.get(conclusion, CapabilityEvidenceState.UNASSESSED)

    # A capability result never awards itself institutional capability truth: the
    # Foundry records evidence and *proposes*; the OCE CapabilityGraph owns status.
    reproducibility.validate()

    return CapabilityAssessment(
        assessment_id=f"cap:{run.run_id}",
        run_id=run.run_id,
        subject_kind=run.subject_kind,
        subject_id=run.subject_id,
        tier=protocol.tier,
        dimensions=FrozenMap(dimensions),
        evidence_state=evidence_state,
        framework_dependence=framework_dependence,
        limitations=limitations,
        baseline_reference=protocol.baseline_reference,
        baseline_delta=FrozenMap(
            {k: v["delta"] for k, v in dimensions.items() if v["delta"] is not None}
        ),
        oce_review_ref=oce_review_ref,
        terminal_conclusion=conclusion,
        reproducibility={
            "claimed": reproducibility.claimed.value,
            "supported": reproducibility.supported_class().value,
            "environment_recorded": reproducibility.environment_recorded,
            "framework": reproducibility.framework,
            "container_digest": reproducibility.container_digest,
            "provider_details": reproducibility.provider_details,
            "replication_evidence": replication.to_dict() if replication else None,
        },
        negative_result=None,
    )


def credit_assessment(assessment: CapabilityAssessment, *, claimed_kind: SubjectKind, attribution_study: str | None = None) -> None:
    """A system result cannot become an artifact result by declaration."""

    assert_subject_credit(assessment.subject_kind, claimed_kind, attribution_study=attribution_study)


def submit_for_oce_review(assessment: CapabilityAssessment, *, oce_review_ref: str | None) -> CapabilityAssessment:
    """Capability evidence becomes a candidate only through OCE review."""

    if not oce_review_ref:
        raise Unauthorized(
            "CAPABILITY_SELF_PROMOTION_REFUSED",
            "Foundry capability evidence cannot become institutional capability truth without OCE review",
        )
    return replace(
        assessment,
        oce_review_ref=oce_review_ref,
        evidence_state=CapabilityEvidenceState.READY_FOR_OCE_CAPABILITY_REVIEW,
    )


def assert_no_master_score(payload: dict[str, Any]) -> None:
    """No universal master capability score may be written anywhere."""

    forbidden = {"master_score", "overall_score", "aggregate_capability", "intelligence_quotient"}
    present = forbidden & set(payload)
    if present and any(payload[key] is not None for key in present):
        raise PolicyBlocked(
            "MASTER_CAPABILITY_SCORE_FORBIDDEN",
            f"a universal capability score is not permitted: {sorted(present)}",
        )


# --------------------------------------------------------------------------
# Negative results + reopen
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class NegativeResult:
    """A negative finding with an explicit, honest reopen condition."""

    negative_id: str
    subject_kind: SubjectKind
    subject_id: str
    hypothesis: str
    outcome: str
    conclusion: TerminalConclusion
    evidence: dict[str, Any]
    reopen_conditions: tuple[str, ...]
    scope: str
    recorded_utc: str
    reopen_state: str = "OPEN_FOR_REOPEN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "negative_id": self.negative_id,
            "subject_kind": self.subject_kind.value,
            "subject_id": self.subject_id,
            "hypothesis": self.hypothesis,
            "outcome": self.outcome,
            "conclusion": self.conclusion.value,
            "evidence": self.evidence,
            "reopen_conditions": list(self.reopen_conditions),
            "scope": self.scope,
            "recorded_utc": self.recorded_utc,
            "reopen_state": self.reopen_state,
            "negative_result_is_project_failure": False,
        }

    def dogma_risk(self) -> str:
        """Narrow or impossible reopen conditions are a dogma risk."""

        if not self.reopen_conditions:
            return "CRITICAL_NO_REOPEN_PATH"
        if len(self.reopen_conditions) == 1 and "never" in self.reopen_conditions[0].lower():
            return "CRITICAL_UNREACHABLE"
        if all(len(c) < 12 for c in self.reopen_conditions):
            return "ELEVATED_VAGUE"
        return "ACCEPTABLE"

    def to_dict_with_dogma(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["dogma_risk"] = self.dogma_risk()
        return payload


@dataclass
class NegativeKnowledgeStore:
    """Local negative-knowledge registry (noncanonical, declared)."""

    double: OceTestDouble = field(default=NEGATIVE_KNOWLEDGE_DOUBLE)
    _results: dict[str, NegativeResult] = field(default_factory=dict, init=False)
    _reopens: list[dict[str, Any]] = field(default_factory=list, init=False)

    def record(self, result: NegativeResult) -> None:
        if result.negative_id in self._results:
            raise PolicyBlocked(
                "NEGATIVE_RESULT_IMMUTABLE",
                f"{result.negative_id}: negative results are appended, never overwritten",
            )
        self._results[result.negative_id] = result

    def get(self, negative_id: str) -> NegativeResult:
        if negative_id not in self._results:
            raise PolicyBlocked("NEGATIVE_RESULT_UNRESOLVED", f"no negative result {negative_id!r}")
        return self._results[negative_id]

    def reopen(
        self,
        negative_id: str,
        *,
        reason: str,
        new_evidence_ref: str | None,
        actor: str,
        operator_approval_ref: str | None = None,
        now_iso: str | None = None,
    ) -> dict[str, Any]:
        """Reopening requires new evidence; a bare wish is not a reopen condition."""

        result = self.get(negative_id)
        if not new_evidence_ref:
            raise PolicyBlocked(
                "REOPEN_REQUIRES_NEW_EVIDENCE",
                f"{negative_id} may not be reopened without new evidence",
            )
        record = {
            "negative_id": negative_id,
            "reason": reason,
            "new_evidence_ref": new_evidence_ref,
            "actor": actor,
            "operator_approval_ref": operator_approval_ref,
            "prior_conclusion": result.conclusion.value,
            "scope": result.scope,
            "provenance_preserved": True,
            "recorded_utc": now_iso or utc_now_iso(),
        }
        self._reopens.append(record)
        self._results[negative_id] = replace(result, reopen_state="REOPENED")
        return record

    def all_results(self) -> tuple[NegativeResult, ...]:
        return tuple(self._results.values())

    def dogma_risks(self) -> dict[str, str]:
        return {
            negative_id: result.dogma_risk()
            for negative_id, result in sorted(self._results.items())
        }

    def receipt(self) -> Receipt:
        return Receipt(
            kind="negative_knowledge.store",
            subject="negative_knowledge",
            payload={
                "results": [r.to_dict_with_dogma() for r in self.all_results()],
                "reopens": list(self._reopens),
            },
        )


# --------------------------------------------------------------------------
# Statistical power gate + conclusion guard
# --------------------------------------------------------------------------


def assert_conclusion_supported(
    conclusion: TerminalConclusion, *, run: EvaluationRun, contamination: ContaminationClass
) -> None:
    """Terminate truthfully: no forced PASS/FAIL from underpowered evidence."""

    assert_conclusion_allowed(
        conclusion, power_adequate=run.power_adequate(), sample_adequate=run.sample_size() > 0
    )
    if contamination in CLAIM_DEGRADING_CONTAMINATION and conclusion is TerminalConclusion.PASS:
        raise PolicyBlocked(
            "CONTAMINATED_PASS_REFUSED",
            "a contaminated benchmark cannot support a PASS conclusion",
        )


def tier_of(benchmark: BenchmarkSpec) -> EvaluationTier:
    return benchmark.tier


def elevate_tier(
    benchmark: BenchmarkSpec,
    requested: EvaluationTier,
    *,
    new_protected_task_set: bool,
    actor_is_builder: bool,
    authorizing_ref: str | None,
) -> BenchmarkSpec:
    """Tier changes follow the constitutional contract, not convenience."""

    from .boundary import assert_tier_change_allowed

    assert_tier_change_allowed(
        benchmark.tier,
        requested,
        new_protected_task_set=new_protected_task_set,
        actor_is_builder=actor_is_builder,
    )
    if TIER_RANK[requested] > TIER_RANK[benchmark.tier] and not authorizing_ref:
        raise Unauthorized(
            "TIER_ELEVATION_REQUIRES_AUTHORIZING_REF",
            "tier elevation requires an external authorizing reference",
        )
    return replace(benchmark, tier=requested)


def claim_class_for(run: EvaluationRun, *, doctrine_exposed: bool) -> ClaimClass:
    """Sealed/doctrine exposure collapses the strongest rediscovery claim."""

    if doctrine_exposed:
        return ClaimClass.POST_REVEAL_REPRODUCTION
    if run.contamination_grade in CLAIM_DEGRADING_CONTAMINATION:
        return ClaimClass.POST_REVEAL_REPRODUCTION
    return ClaimClass.BLIND_TASK_PERFORMANCE


def trust_class_admissible_for_remote(trust: TrustClass) -> bool:
    from .enums import REMOTE_INADMISSIBLE_TRUST

    return trust not in REMOTE_INADMISSIBLE_TRUST


__all__ = [
    "BUILDER_ROLES",
    "EVAL_DOUBLE",
    "NEGATIVE_KNOWLEDGE_DOUBLE",
    "SEALED_ACCESS_ROLES",
    "BenchmarkItem",
    "BenchmarkSpec",
    "CapabilityAssessment",
    "EvaluationObservation",
    "EvaluationProtocol",
    "EvaluationRun",
    "ExposureEvent",
    "FrozenEvaluationProtocol",
    "MetricSpec",
    "NegativeKnowledgeStore",
    "NegativeResult",
    "ReproductionEvidence",
    "SealedEvaluationStore",
    "SealedPayload",
    "assert_conclusion_supported",
    "assert_no_master_score",
    "assert_protocol_unchanged",
    "assess_capability",
    "claim_class_for",
    "credit_assessment",
    "elevate_tier",
    "freeze_protocol",
    "submit_for_oce_review",
    "tier_of",
    "trust_class_admissible_for_remote",
]
