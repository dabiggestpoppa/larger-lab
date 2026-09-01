"""G3-C epistemic friction protocol + counter-attractor review (S08/S09).

EpistemicFrictionProtocol — semi-permeable cognition and staged reveal.
Friction is NOT triggered by disagreement. It is triggered by a TEST CONTRACT
based on consequence, correlation risk (concentration/exposure), premature
convergence and uncertainty. Friction has cost; budgets are bounded.

CounterAttractorReview — a bounded adversarial check against a strong incumbent
consensus. It may return CHALLENGE_SUPPORTED, NO_CHANGE or UNRESOLVED. An honest
NO_CHANGE is a SUCCESS: nobody is rewarded for manufacturing dissent, and
exhausting the challenge budget never reduces confidence/evidence status
arbitrarily.

All deterministic, local, model-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .cognitive_ecology import (
    ConsensusRecord,
    EcologyFacts,
    ReviewerIndependenceProfile,
    UNKNOWN,
)

# §9 friction methods (staged reveal / reconstruction)
FRICTION_METHODS = (
    "fresh_context_reconstruction",
    "staged_reveal",
    "alternate_source_bundle",
    "alternate_model_or_runtime_lineage",
    "raw_evidence_reconstruction",
    "reverse_premise_analysis",
    "independent_experiment_design",
)

# §15 counter-attractor methods
COUNTER_ATTRACTOR_METHODS = (
    "fresh_context",
    "reverse_premise",
    "alternate_source_search",
    "raw_evidence_reconstruction",
)

CHALLENGE_TERMINALS = ("CHALLENGE_SUPPORTED", "NO_CHANGE", "UNRESOLVED")


# --------------------------------------------------------------------------- #
# §9 EpistemicFrictionProtocol
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FrictionTrigger:
    triggered: bool
    rationale: str
    budget: int = 0
    methods: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"triggered": self.triggered, "rationale": self.rationale,
                "budget": self.budget, "methods": list(self.methods)}


@dataclass(frozen=True)
class FrictionResult:
    record_id: str
    triggered: bool
    budget_used: int
    fresh_context_reviewers: Tuple[str, ...]           # reviewer ids on blind/evidence-only paths
    surfaced_alternatives: Tuple[str, ...]             # conclusions surfaced only on the fresh path
    information_gain: bool
    evidence_gap: Optional[Mapping[str, Any]]          # discriminating test gap, if any
    cost_units: int
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "record_id", "triggered", "budget_used", "fresh_context_reviewers",
            "surfaced_alternatives", "information_gain", "evidence_gap",
            "cost_units", "rationale")}


@dataclass(frozen=True)
class FrictionContract:
    """PROVISIONAL trigger test-contract (per consequence class)."""

    contract_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    consequence_classes: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    # e.g. {"HIGH": {"trigger_on": ["correlation_risk", "premature_convergence"],
    #                "max_prior_exposure_ratio": 0.0, "budget": 4, "cost_per_reconstruction": 5}}

    def for_consequence(self, consequence_class: str) -> Mapping[str, Any]:
        return dict(self.consequence_classes.get(consequence_class, {}))

    def fingerprint(self) -> str:
        return deterministic_hex("friction_contract", self.contract_id, self.version_tag,
                                 self.consequence_classes, length=24)


def friction_trigger(facts: EcologyFacts, contract: FrictionContract) -> FrictionTrigger:
    """Test-contract trigger — NOT disagreement-driven. High consequence with
    correlation risk (source/model/retrieval concentration, prior-conclusion
    exposure) or premature convergence demands a bounded fresh-context check."""
    cfg = contract.for_consequence(facts.consequence_class)
    triggers = set(cfg.get("trigger_on", []))
    budget = int(cfg.get("budget", 0))
    max_exposure = float(cfg.get("max_prior_exposure_ratio", 1.0))
    if not cfg:
        return FrictionTrigger(False, "no friction contract for this consequence class", 0, ())
    reasons: List[str] = []
    if "correlation_risk" in triggers:
        if facts.source_concentration is not None and facts.source_concentration >= 0.5:
            reasons.append("high source concentration")
        if facts.model_family_concentration is not None and facts.model_family_concentration >= 0.5:
            reasons.append("high model-family concentration")
        if facts.retrieval_concentration is not None and facts.retrieval_concentration >= 0.5:
            reasons.append("high retrieval concentration")
        if facts.prior_conclusion_exposure_ratio > max_exposure:
            reasons.append("prior-conclusion exposure above contract ratio")
    if "premature_convergence" in triggers:
        if facts.raw_reviewer_count >= 3 and facts.disagreement_count <= 1 and \
                facts.fresh_context_count == 0 and facts.prior_conclusion_exposure_ratio > max_exposure:
            reasons.append("rapid convergence under shared context with no fresh path")
    if reasons:
        methods = cfg.get("methods", ["fresh_context_reconstruction"])
        return FrictionTrigger(True, "; ".join(reasons), budget, tuple(methods))
    return FrictionTrigger(False, "no correlation-risk or convergence trigger", budget, ())


def run_friction(
    trigger: FrictionTrigger,
    reviewers: Sequence[ReviewerIndependenceProfile],
    conclusions_by_exposure: Mapping[str, Mapping[str, str]],
    incumbent_conclusion: str,
    budget: int,
    cost_per_reconstruction: int = 5,
) -> FrictionResult:
    """Bounded fresh-context reconstruction. `conclusions_by_exposure` maps
    reviewer_id -> {exposure_mode: conclusion} (fixture behavior, decision-grade).
    A reviewer whose exposure changed to BLIND/EVIDENCE_ONLY may surface an
    alternative; the alternative is recorded, never forced to be correct."""
    if not trigger.triggered:
        return FrictionResult(
            record_id=deterministic_hex("friction", "not_triggered", incumbent_conclusion),
            triggered=False, budget_used=0, fresh_context_reviewers=(),
            surfaced_alternatives=(), information_gain=False, evidence_gap=None,
            cost_units=0, rationale="friction not triggered",
        )
    fresh: List[str] = []
    alternatives: List[str] = []
    used = 0
    for p in reviewers:
        if used >= budget:
            break
        if p.exposure_mode in ("BLIND", "EVIDENCE_ONLY"):
            fresh.append(p.reviewer_id)
            used += 1
            conclusion = (conclusions_by_exposure.get(p.reviewer_id) or {}).get(p.exposure_mode)
            if conclusion and conclusion != incumbent_conclusion:
                alternatives.append(conclusion)
    information_gain = len(alternatives) > 0
    evidence_gap = None
    if information_gain:
        evidence_gap = {
            "question": f"discriminating test between incumbent and {len(alternatives)} alternative(s)",
            "missing": "bounded discriminating observation that separates the hypotheses",
            "reopen_if": "a discriminating observation is produced under a fresh membrane",
        }
    return FrictionResult(
        record_id=deterministic_hex("friction", tuple(p.reviewer_id for p in reviewers),
                                    sorted(alternatives), used),
        triggered=True,
        budget_used=used,
        fresh_context_reviewers=tuple(sorted(fresh)),
        surfaced_alternatives=tuple(sorted(set(alternatives))),
        information_gain=information_gain,
        evidence_gap=evidence_gap,
        cost_units=used * cost_per_reconstruction,
        rationale="bounded fresh-context reconstruction completed",
    )


# --------------------------------------------------------------------------- #
# §15 CounterAttractorReview
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CounterAttractorReview:
    record_id: str
    trigger_reason: str
    incumbent_claim: str
    review_budget: int
    budget_used: int
    allowed_methods: Tuple[str, ...]
    fresh_context_requirements: str
    source_exclusion_rules: Tuple[str, ...]
    stop_condition: str
    evidence_produced: Tuple[str, ...]
    discriminating_contradiction_found: bool
    terminal_result: str                  # CHALLENGE_SUPPORTED | NO_CHANGE | UNRESOLVED
    cost_units: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "record_id", "trigger_reason", "incumbent_claim", "review_budget",
            "budget_used", "allowed_methods", "fresh_context_requirements",
            "source_exclusion_rules", "stop_condition", "evidence_produced",
            "discriminating_contradiction_found", "terminal_result", "cost_units")}


@dataclass(frozen=True)
class CounterAttractorSpec:
    """PROVISIONAL trigger + budget test-contract."""

    spec_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    trigger_on_strong_consensus: bool = True
    min_source_lineages_for_trigger: int = 2
    min_model_or_runtime_lineages_for_trigger: int = 2
    max_prior_exposure_ratio_for_trigger: float = 0.0
    budget: int = 4
    cost_per_method: int = 3

    def fingerprint(self) -> str:
        return deterministic_hex("counter_attractor_spec", self.spec_id, self.version_tag,
                                 self.budget, length=24)


def counter_attractor_trigger(facts: EcologyFacts, spec: CounterAttractorSpec) -> bool:
    """A STRONG, well-supported consensus may trigger a bounded challenge. The
    meta-observer does not need dissent to justify the check."""
    if not spec.trigger_on_strong_consensus:
        return False
    if facts.distinct_source_lineages < spec.min_source_lineages_for_trigger:
        return False
    model_or_runtime = max(facts.distinct_model_family_count, facts.distinct_runtime_lineage_count)
    if model_or_runtime < spec.min_model_or_runtime_lineages_for_trigger:
        return False
    if facts.prior_conclusion_exposure_ratio > spec.max_prior_exposure_ratio_for_trigger:
        return False
    if facts.independent_replication_count < 1:
        return False
    return True


def run_counter_attractor(
    spec: CounterAttractorSpec,
    incumbent_claim: str,
    findings: Sequence[Mapping[str, Any]],
) -> CounterAttractorReview:
    """Bounded challenge. `findings` are the fixture's decision-grade results for
    the allowed methods (e.g. alternate-source search yields nothing). Terminal:
    CHALLENGE_SUPPORTED if a discriminating contradiction was found, NO_CHANGE if
    none was, UNRESOLVED if budget ran out without a verdict. Honest NO_CHANGE is
    success; budget exhaustion does NOT lower evidence/confidence status."""
    contradiction_found = any(f.get("discriminating_contradiction") for f in findings)
    budget_used = min(spec.budget, max(len(findings), 1))
    if contradiction_found:
        terminal = "CHALLENGE_SUPPORTED"
    elif budget_used >= spec.budget:
        terminal = "NO_CHANGE"
    else:
        terminal = "UNRESOLVED"
    produced = tuple(sorted({str(f.get("evidence_id", "")) for f in findings if f.get("evidence_id")}))
    return CounterAttractorReview(
        record_id=deterministic_hex("counter_attractor", incumbent_claim, terminal, budget_used),
        trigger_reason="strong independent consensus warrants a bounded adversarial check",
        incumbent_claim=incumbent_claim,
        review_budget=spec.budget,
        budget_used=budget_used,
        allowed_methods=COUNTER_ATTRACTOR_METHODS,
        fresh_context_requirements="fresh context, no prior conclusion exposure",
        source_exclusion_rules=("exclude incumbent source bundle",),
        stop_condition="discriminating contradiction found OR budget exhausted",
        evidence_produced=produced,
        discriminating_contradiction_found=contradiction_found,
        terminal_result=terminal,
        cost_units=budget_used * spec.cost_per_method,
    )
