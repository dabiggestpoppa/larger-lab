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
class FrictionAction:
    """One executed friction action — G3R-05: methods/budgets actually govern
    execution, and every action is recorded explicitly."""

    method: str
    reviewer_id: str
    budget_unit: int
    exposure_mode: str
    result: str                          # conclusion id / NO_CONCLUSION / NO_FIXTURE_DATA
    evidence_produced: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"method": self.method, "reviewer_id": self.reviewer_id,
                "budget_unit": self.budget_unit, "exposure_mode": self.exposure_mode,
                "result": self.result, "evidence_produced": list(self.evidence_produced)}


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
    actions: Tuple[FrictionAction, ...] = ()           # G3R-05: executed actions, method-bound
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out = {k: getattr(self, k) for k in (
            "record_id", "triggered", "budget_used", "fresh_context_reviewers",
            "surfaced_alternatives", "information_gain", "evidence_gap",
            "cost_units", "rationale")}
        out["actions"] = [a.to_dict() for a in self.actions]
        return out

    def actions_dict(self) -> Dict[str, Any]:
        return {"actions": [a.to_dict() for a in self.actions]}

    def action_count(self) -> int:
        return len(self.actions)


@dataclass(frozen=True)
class FrictionContract:
    """PROVISIONAL trigger test-contract (per consequence class).

    G3R2-07: every method named by a consequence class must belong to the
    canonical FRICTION_METHODS vocabulary — an unknown method fails closed at
    contract construction (a contract can never make MAGIC_METHOD admissible).
    """

    contract_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    consequence_classes: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    # e.g. {"HIGH": {"trigger_on": ["correlation_risk", "premature_convergence"],
    #                "max_prior_exposure_ratio": 0.0, "budget": 4, "cost_per_reconstruction": 5}}

    def __post_init__(self) -> None:
        unknown: List[str] = []
        for cclass, cfg in self.consequence_classes.items():
            for m in cfg.get("methods", []):
                if m not in FRICTION_METHODS:
                    unknown.append(str(m))
        if unknown:
            raise ValueError(
                f"FrictionContract {self.contract_id!r}: unknown friction method(s) "
                f"{sorted(set(unknown))} — must be in canonical FRICTION_METHODS")

    def for_consequence(self, consequence_class: str) -> Mapping[str, Any]:
        return dict(self.consequence_classes.get(consequence_class, {}))

    def fingerprint(self) -> str:
        return deterministic_hex("friction_contract", self.contract_id, self.version_tag,
                                 self.consequence_classes, length=24)


@dataclass(frozen=True)
class EpistemicFrictionProtocol:
    """§9 protocol surface — semi-permeable cognition and staged reveal.

    Bundles a FrictionContract with its trigger/run semantics. Friction is
    triggered ONLY by a test contract (consequence class, correlation risk,
    premature convergence), never by disagreement alone, and always within a
    bounded budget. This is the named surface the module docstring promises.
    """

    contract: FrictionContract

    def trigger(self, facts: EcologyFacts) -> FrictionTrigger:
        return friction_trigger(facts, self.contract)

    def run(
        self,
        trigger: FrictionTrigger,
        reviewers: Sequence[ReviewerIndependenceProfile],
        conclusions_by_exposure: Mapping[str, Mapping[str, str]],
        incumbent_conclusion: str,
        cost_per_reconstruction: int = 5,
    ) -> FrictionResult:
        return run_friction(
            trigger, reviewers, conclusions_by_exposure, incumbent_conclusion,
            trigger.budget, cost_per_reconstruction,
        )


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
        # G3R2-04: a single common source shared across otherwise-different
        # bundles is still a shared dependency (partial-bundle overlap).
        if facts.max_single_source_lineage_prevalence is not None \
                and facts.max_single_source_lineage_prevalence >= 0.5:
            reasons.append("high single-source prevalence across bundles")
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
    method_results: Optional[Mapping[str, Mapping[str, str]]] = None,
) -> FrictionResult:
    """Bounded friction execution — G3R-05: ONLY the methods authorized on the
    trigger may execute, and every executed action consumes one budget unit.

    * `fresh_context_reconstruction` acts on BLIND/EVIDENCE_ONLY reviewers using
      `conclusions_by_exposure` (reviewer_id -> {exposure_mode: conclusion}).
    * any other authorized method executes from `method_results`
      (method -> {reviewer_id: result}) when the fixture supplies data;
      authorized-but-unprovisioned methods are recorded as not executed and
      consume nothing.
    * An alternative is surfaced only from an EXECUTED action; it is recorded,
      never forced to be correct.
    """
    if not trigger.triggered:
        return FrictionResult(
            record_id=deterministic_hex("friction", "not_triggered", incumbent_conclusion),
            triggered=False, budget_used=0, fresh_context_reviewers=(),
            surfaced_alternatives=(), information_gain=False, evidence_gap=None,
            cost_units=0, actions=(), rationale="friction not triggered",
        )
    fresh: List[str] = []
    alternatives: List[str] = []
    actions: List[FrictionAction] = []
    used = 0
    authorized = set(trigger.methods) if trigger.methods else {"fresh_context_reconstruction"}

    # --- fresh-context reconstruction -------------------------------------- #
    if "fresh_context_reconstruction" in authorized:
        for p in reviewers:
            if used >= budget:
                break
            if p.exposure_mode not in ("BLIND", "EVIDENCE_ONLY"):
                continue
            used += 1
            fresh.append(p.reviewer_id)
            conclusion = (conclusions_by_exposure.get(p.reviewer_id) or {}).get(p.exposure_mode, "")
            actions.append(FrictionAction(
                method="fresh_context_reconstruction", reviewer_id=p.reviewer_id,
                budget_unit=used, exposure_mode=p.exposure_mode,
                result=str(conclusion) if conclusion else "NO_CONCLUSION",
                evidence_produced=(str(conclusion),) if conclusion else (),
            ))
            if conclusion and conclusion != incumbent_conclusion:
                alternatives.append(conclusion)

    # --- other authorized methods (fixture-supplied results only) ---------- #
    for method in sorted(authorized - {"fresh_context_reconstruction"}):
        if used >= budget:
            break
        results = (method_results or {}).get(method) or {}
        for reviewer_id, result in sorted(results.items()):
            if used >= budget:
                break
            used += 1
            actions.append(FrictionAction(
                method=method, reviewer_id=str(reviewer_id), budget_unit=used,
                exposure_mode="METHOD_EXECUTION",
                result=str(result) if result else "NO_RESULT",
                evidence_produced=(str(result),) if result else (),
            ))
            if result and str(result) != incumbent_conclusion:
                alternatives.append(str(result))

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
                                    sorted(alternatives), used,
                                    tuple(sorted(a.method for a in actions))),
        triggered=True,
        budget_used=used,
        fresh_context_reviewers=tuple(sorted(fresh)),
        surfaced_alternatives=tuple(sorted(set(alternatives))),
        information_gain=information_gain,
        evidence_gap=evidence_gap,
        cost_units=used * cost_per_reconstruction,
        actions=tuple(actions),
        rationale="bounded friction execution completed under authorized methods",
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
    non_admissible_findings: Tuple[Mapping[str, Any], ...] = ()   # G3R-02: never affect verdict

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "record_id", "trigger_reason", "incumbent_claim", "review_budget",
            "budget_used", "allowed_methods", "fresh_context_requirements",
            "source_exclusion_rules", "stop_condition", "evidence_produced",
            "discriminating_contradiction_found", "terminal_result", "cost_units",
            "non_admissible_findings")}


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
    min_dominant_vote_ratio_for_trigger: float = 0.6   # G3R-03: strong consensus = actual concentration
    allowed_methods: Tuple[str, ...] = ()              # G3R-02: empty = canonical contract
    budget: int = 4
    cost_per_method: int = 3

    def __post_init__(self) -> None:
        # G3R2-07: unknown challenge methods fail closed at construction.
        unknown = [m for m in self.allowed_methods if m not in COUNTER_ATTRACTOR_METHODS]
        if unknown:
            raise ValueError(
                f"CounterAttractorSpec {self.spec_id!r}: unknown method(s) "
                f"{sorted(set(unknown))} — must be in canonical COUNTER_ATTRACTOR_METHODS")

    def fingerprint(self) -> str:
        return deterministic_hex("counter_attractor_spec", self.spec_id, self.version_tag,
                                 self.budget, self.min_dominant_vote_ratio_for_trigger,
                                 self.allowed_methods, length=24)


def counter_attractor_trigger(facts: EcologyFacts, spec: CounterAttractorSpec) -> bool:
    """A STRONG, well-supported consensus may trigger a bounded challenge. The
    meta-observer does not need dissent to justify the check. G3R-03: strong
    means actual vote concentration >= the provisional ratio threshold — raw
    reviewer count alone can never trigger (duplicates and splits do not count
    as strong consensus)."""
    if not spec.trigger_on_strong_consensus:
        return False
    # strict: a 3/2 split (ratio == threshold) is NOT strong consensus
    if facts.dominant_vote_ratio <= spec.min_dominant_vote_ratio_for_trigger:
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
    """Bounded challenge — G3R-01/02:

    * ONLY findings actually CONSUMED within the authorized budget affect
      discriminating_contradiction_found, terminal_result, evidence_produced
      and cost_units. A contradiction beyond the budget is IGNORED.
    * Each finding must carry a `method` in the authorized method set
      (spec.allowed_methods or the canonical CounterAttractor contract);
      unknown/disallowed methods are recorded as non-admissible evidence that
      can NEVER affect the verdict and consume no budget.
    * Honest NO_CHANGE is success; budget exhaustion does NOT lower
      evidence/confidence status; zero findings never fake budget consumption.
    """
    allowed = set(spec.allowed_methods) if spec.allowed_methods else set(COUNTER_ATTRACTOR_METHODS)
    consumed: List[Mapping[str, Any]] = []
    non_admissible: List[Mapping[str, Any]] = []
    budget_used = 0
    contradiction_found = False
    for f in findings:
        if budget_used >= spec.budget:
            break
        method = str(f.get("method") or "")
        if method not in allowed:
            non_admissible.append({**dict(f), "reason": "method_not_authorized"})
            continue
        consumed.append(dict(f))
        budget_used += 1
        # G3R2-08: stop on the FIRST consumed discriminating contradiction —
        # additional findings are not consumed and cannot affect the verdict.
        if bool(f.get("discriminating_contradiction")):
            contradiction_found = True
            break
    if contradiction_found:
        terminal = "CHALLENGE_SUPPORTED"
    elif budget_used >= spec.budget and budget_used > 0:
        terminal = "NO_CHANGE"
    else:
        terminal = "UNRESOLVED"
    produced = tuple(sorted({str(f.get("evidence_id", "")) for f in consumed if f.get("evidence_id")}))
    return CounterAttractorReview(
        record_id=deterministic_hex("counter_attractor", incumbent_claim, terminal, budget_used,
                                    tuple(sorted(f.get("evidence_id", "") for f in consumed))),
        trigger_reason="strong independent consensus warrants a bounded adversarial check",
        incumbent_claim=incumbent_claim,
        review_budget=spec.budget,
        budget_used=budget_used,
        allowed_methods=tuple(sorted(allowed)),
        fresh_context_requirements="fresh context, no prior conclusion exposure",
        source_exclusion_rules=("exclude incumbent source bundle",),
        stop_condition="stop at FIRST consumed discriminating contradiction OR budget exhausted; later findings are never consumed",
        evidence_produced=produced,
        discriminating_contradiction_found=contradiction_found,
        terminal_result=terminal,
        cost_units=budget_used * spec.cost_per_method,
        non_admissible_findings=tuple(non_admissible),
    )
