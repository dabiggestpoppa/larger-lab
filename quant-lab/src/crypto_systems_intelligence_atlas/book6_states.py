"""Book 6 descriptive state — rule-gated states and the fundamental state vector.

The central ratified invariant (state-vector v0.2 §1):

    NO EMPIRICAL THRESHOLD != NO DERIVATION RULE

Every state requires an explicit, versioned, RATIFIED derivation rule. Some
states need no empirical cutoff; others need a threshold or benchmark rule. A
state name may never carry a rule that was never declared — that is how v0.1 was
found to hide six unratified rules inside descriptive labels.

State classes (state-vector v0.2 §3):

- **Class A** availability/observation states — emittable from structural
  conditions alone, with no directional rule: ``INSUFFICIENT_DATA``,
  ``NOT_APPLICABLE``, ``RULE_NOT_RATIFIED``, ``COVERAGE_SUFFICIENCY_UNKNOWN``.
- **Class B** specification-only states — require a ratified ``StateRule``:
  ``INCREASING``, ``DECREASING``, ``UNCHANGED``.
- **Class C** threshold/benchmark states — require a ratified ``StateRule``
  plus benchmark / tolerance / volatility / decision-rule identity: ``STABLE``,
  ``VOLATILE``, ``HIGHER_THAN_OWN_HISTORY``, ``LOWER_THAN_OWN_HISTORY``.

Generic ``EXPANDING`` / ``CONTRACTING`` remain DEFERRED: a label may not inherit
its meaning from English, so they are not emittable at all.

The accepted implementation ships with ``INDIVIDUAL_STATE_RULES_RATIFIED = 0``:
ratifying the governance model ratified NO rule, so no Class B or Class C state is
emittable. Ratification is an individual operator act recorded here; nothing in
this module may self-ratify, and there is no delegated authority (D6M-3 = A).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .book6_grammar import MissingnessState


class StateError(ValueError):
    """A state was requested or emitted in violation of the ratified doctrine."""


class StateClass(str, Enum):
    """The three ratified state classes (state-vector v0.2 §3)."""

    A_AVAILABILITY = "A_AVAILABILITY"
    B_SPECIFICATION_ONLY = "B_SPECIFICATION_ONLY"
    C_THRESHOLD_BENCHMARK = "C_THRESHOLD_BENCHMARK"
    DEFERRED_GENERIC = "DEFERRED_GENERIC"


class StateName(str, Enum):
    """The ratified state vocabulary.

    Membership here does not license emission: only Class A is emittable without
    a ratified rule, and Class B/C require one.
    """

    # Class A — availability / observation
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    RULE_NOT_RATIFIED = "RULE_NOT_RATIFIED"
    COVERAGE_SUFFICIENCY_UNKNOWN = "COVERAGE_SUFFICIENCY_UNKNOWN"
    # Class B — specification-only
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    UNCHANGED = "UNCHANGED"
    # Class C — threshold / benchmark
    STABLE = "STABLE"
    VOLATILE = "VOLATILE"
    HIGHER_THAN_OWN_HISTORY = "HIGHER_THAN_OWN_HISTORY"
    LOWER_THAN_OWN_HISTORY = "LOWER_THAN_OWN_HISTORY"
    # Generic shapes — DEFERRED, never emittable
    EXPANDING = "EXPANDING"
    CONTRACTING = "CONTRACTING"


#: Class assignment per state name. EXPANDING/CONTRACTING are deliberately
#: DEFERRED rather than Class C, because no generic predicate was ratified.
STATE_CLASS_BY_NAME: Final[dict[StateName, StateClass]] = {
    StateName.INSUFFICIENT_DATA: StateClass.A_AVAILABILITY,
    StateName.NOT_APPLICABLE: StateClass.A_AVAILABILITY,
    StateName.RULE_NOT_RATIFIED: StateClass.A_AVAILABILITY,
    StateName.COVERAGE_SUFFICIENCY_UNKNOWN: StateClass.A_AVAILABILITY,
    StateName.INCREASING: StateClass.B_SPECIFICATION_ONLY,
    StateName.DECREASING: StateClass.B_SPECIFICATION_ONLY,
    StateName.UNCHANGED: StateClass.B_SPECIFICATION_ONLY,
    StateName.STABLE: StateClass.C_THRESHOLD_BENCHMARK,
    StateName.VOLATILE: StateClass.C_THRESHOLD_BENCHMARK,
    StateName.HIGHER_THAN_OWN_HISTORY: StateClass.C_THRESHOLD_BENCHMARK,
    StateName.LOWER_THAN_OWN_HISTORY: StateClass.C_THRESHOLD_BENCHMARK,
    StateName.EXPANDING: StateClass.DEFERRED_GENERIC,
    StateName.CONTRACTING: StateClass.DEFERRED_GENERIC,
}

#: Prescriptive names that may never exist as a state (Constitution v0.2 §5.3a).
#: Recorded so an attempt to inject one is a refusal, not an unknown.
PROHIBITED_STATE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "ATTRACTIVE",
        "STRONG_BUY",
        "UNDERVALUED",
        "OVERVALUED",
        "TOP_TIER",
        "HIGH_QUALITY",
        "WINNER",
        "BEST",
        "BUY",
        "SELL",
        "HEALTHY",
        "STRONG",
        "ROBUST",
        "PROMISING",
        "INVESTABLE",
        "HEALTHY_USAGE",
        "ADOPTION_SUCCESS",
    }
)


class RuleRatificationStatus(str, Enum):
    """Per-rule ratification status (D6M-3 = A: individual operator act)."""

    UNRATIFIED = "UNRATIFIED"
    RATIFIED = "RATIFIED"
    SUPERSEDED = "SUPERSEDED"


class StateRule(BaseModel):
    """A derivation rule for a Class B or Class C state.

    The object can represent an UNRATIFIED rule, which is how the accepted
    implementation ships. ``target_state`` may not be a Class A state (those need
    no rule) nor a DEFERRED generic state (no predicate was ratified).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_rule_id: str = Field(min_length=1)
    target_state: StateName
    state_class: StateClass
    predicate_ref: str = Field(min_length=1)
    methodology_ref: str = Field(min_length=1)
    required_measurement_refs: tuple[str, ...] = ()
    window_class_constraint: str | None = None
    comparability_constraint: str | None = None
    precision_semantics: str | None = None
    benchmark_methodology_ref: str | None = None
    coverage_sufficiency_ref: str | None = None
    tolerance_ref: str | None = None
    volatility_measure_ref: str | None = None
    decision_rule_ref: str | None = None
    version: str = Field(min_length=1)
    status: RuleRatificationStatus = RuleRatificationStatus.UNRATIFIED
    ratified_by: str | None = None
    ratified_at: datetime | None = None

    @model_validator(mode="after")
    def _check_rule_shape(self) -> "StateRule":
        if self.state_class is StateClass.A_AVAILABILITY:
            raise StateError(
                "Class A availability states require no derivation rule and may "
                "not carry one"
            )
        if self.state_class is StateClass.DEFERRED_GENERIC:
            raise StateError(
                "generic EXPANDING/CONTRACTING remain DEFERRED: a label may not "
                "inherit its meaning from English"
            )
        if STATE_CLASS_BY_NAME[self.target_state] is not self.state_class:
            raise StateError(
                f"state rule declares class {self.state_class.value} for "
                f"{self.target_state.value}, which is "
                f"{STATE_CLASS_BY_NAME[self.target_state].value}"
            )
        if self.target_state is StateName.UNCHANGED and self.precision_semantics is None:
            raise StateError(
                "UNCHANGED requires explicit precision semantics: exact equality "
                "must be meaningful for the measurement class, and it is not "
                "STABLE"
            )
        if self.state_class is StateClass.C_THRESHOLD_BENCHMARK:
            if not (
                self.benchmark_methodology_ref
                or self.tolerance_ref
                or self.volatility_measure_ref
            ):
                raise StateError(
                    f"{self.target_state.value} is threshold/benchmark dependent "
                    f"and requires a benchmark, tolerance or volatility-measure "
                    f"identity"
                )
        if self.status is RuleRatificationStatus.RATIFIED:
            if not self.ratified_by or not self.ratified_at:
                raise StateError(
                    "a RATIFIED rule must record its ratifying authority and time"
                )
        return self

    def is_ratified(self) -> bool:
        """Whether this rule currently authorizes its target state's emission."""

        return self.status is RuleRatificationStatus.RATIFIED


class StateRuleRegistry:
    """Deterministic, offline, in-memory registry of state rules.

    No automatic ratification, no delegated authority, no delegation register
    (D6M-3 = A). ``register`` accepts UNRATIFIED rules; ``ratify`` records an
    individual operator decision and is the ONLY path to authorization.
    """

    def __init__(self) -> None:
        self._rules: dict[str, StateRule] = {}

    def register(self, rule: StateRule) -> StateRule:
        """Register a rule. Registration proves nothing about current authority."""

        if rule.state_rule_id in self._rules:
            raise StateError(f"state rule {rule.state_rule_id} already registered")
        self._rules[rule.state_rule_id] = rule
        return rule

    def ratified_count(self) -> int:
        """Number of currently-ratified rules."""

        return sum(1 for rule in self._rules.values() if rule.is_ratified())

    def rules_for(self, target: StateName) -> tuple[StateRule, ...]:
        """All registered rules targeting a state (deterministically ordered)."""

        return tuple(
            sorted(
                (r for r in self._rules.values() if r.target_state is target),
                key=lambda r: r.state_rule_id,
            )
        )

    def authorize(self, target: StateName, *, rule_ref: str) -> StateRule:
        """Return a ratified rule for a state, or refuse.

        This is the single chokepoint that makes "governance ratified != rule
        ratified" mechanical: a Class B/C state cannot be emitted without naming
        a rule that is individually RATIFIED here.
        """

        rule = self._rules.get(rule_ref)
        if rule is None:
            raise StateError(
                f"state rule {rule_ref} is not registered; {target.value} may not "
                f"be emitted without a ratified rule"
            )
        if rule.target_state is not target:
            raise StateError(
                f"state rule {rule_ref} targets {rule.target_state.value}, not "
                f"{target.value}"
            )
        if not rule.is_ratified():
            raise StateError(
                f"state rule {rule_ref} for {target.value} is "
                f"{rule.status.value}; ratification is an individual operator "
                f"decision and may not be inferred"
            )
        return rule

    def ratify(self, rule_ref: str, *, operator: str, at: datetime) -> StateRule:
        """Record an individual operator ratification of one rule.

        Supersedes any earlier version of the same rule id; the prior version is
        replaced in the registry but its state emission history is unaffected
        because historical states are never rewritten.
        """

        rule = self._rules.get(rule_ref)
        if rule is None:
            raise StateError(f"state rule {rule_ref} is not registered")
        if rule.status is RuleRatificationStatus.RATIFIED:
            raise StateError(
                f"state rule {rule_ref} is already ratified; a rule is ratified "
                f"by an individual decision, not re-ratified implicitly"
            )
        ratified = rule.model_copy(
            update={
                "status": RuleRatificationStatus.RATIFIED,
                "ratified_by": operator,
                "ratified_at": at,
            }
        )
        self._rules[rule_ref] = ratified
        return ratified


class VectorStatus(str, Enum):
    """Two distinct NON-EVALUATIVE structural statuses (state-vector v0.2 §6).

    "Complete" names slot resolution only. It never means good, healthy, high
    quality or strong: no quality reading is permitted on these fields.
    """

    SCHEMA_COMPLETE = "SCHEMA_COMPLETE"
    SCHEMA_INCOMPLETE = "SCHEMA_INCOMPLETE"
    DATA_COMPLETE = "DATA_COMPLETE"
    DATA_INCOMPLETE = "DATA_INCOMPLETE"


class StateDimension(BaseModel):
    """One descriptive dimension of a subject's state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension_id: str = Field(min_length=1)
    state: StateName
    state_class: StateClass
    measurement_refs: tuple[str, ...] = ()
    state_rule_ref: str | None = None
    methodology_ref: str = Field(min_length=1)
    valid_time: datetime
    observed_at: datetime
    missingness: MissingnessState
    coverage_observation_id: str | None = None
    sensitivity_note: str | None = None

    @model_validator(mode="after")
    def _check_rule_reference(self) -> "StateDimension":
        if self.state_class in (
            StateClass.B_SPECIFICATION_ONLY,
            StateClass.C_THRESHOLD_BENCHMARK,
        ) and not self.state_rule_ref:
            raise StateError(
                f"dimension {self.dimension_id} emits a {self.state_class.value} "
                f"state and must name its state_rule_ref"
            )
        return self


class FundamentalStateVector(BaseModel):
    """A descriptive vector of state dimensions — never a score.

    No ``total``, ``score``, ``rating``, ``grade``, ``rank`` or weighted field
    exists on this type; ``extra="forbid"`` makes injecting one fail closed
    (Constitution v0.2 §5.3a; plan v0.2 §24).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_ref: str = Field(min_length=1)
    schema_ref: str = Field(min_length=1)
    as_of_valid_time: datetime
    dimensions: tuple[StateDimension, ...] = Field(min_length=1)

    def _resolve_status(self) -> tuple[VectorStatus, VectorStatus]:
        """Compute schema and data status structurally (no score, no judgement)."""

        schema_complete = all(
            dim.state_class is not StateClass.DEFERRED_GENERIC
            and STATE_CLASS_BY_NAME.get(dim.state) is not None
            for dim in self.dimensions
        )
        data_complete = all(
            dim.missingness in (MissingnessState.OBSERVED, MissingnessState.ZERO_OBSERVED)
            and dim.state_class is not StateClass.DEFERRED_GENERIC
            for dim in self.dimensions
        )
        return (
            VectorStatus.SCHEMA_COMPLETE if schema_complete else VectorStatus.SCHEMA_INCOMPLETE,
            VectorStatus.DATA_COMPLETE if data_complete else VectorStatus.DATA_INCOMPLETE,
        )

    @property
    def schema_status(self) -> VectorStatus:
        """``NOT_APPLICABLE`` satisfies the schema: it is a resolved slot."""

        return self._resolve_status()[0]

    @property
    def data_status(self) -> VectorStatus:
        """Data completeness requires an observed derivation for every dimension.

        Because no coverage-sufficiency rule is ratified, no dimension can assert
        sufficiency on coverage alone; this status reflects observed derivation
        only and fails closed when anything is unresolved.
        """

        return self._resolve_status()[1]


def resolve_availability_state(
    *,
    has_measurements: bool,
    metric_applies: bool,
    rule_ratified: bool,
    coverage_sufficiency_rule_ratified: bool,
) -> StateName:
    """Resolve a Class A availability state from structural conditions alone.

    Class A states are decidable without any directional predicate, threshold or
    benchmark. The precedence order is fixed so that absence is never reported
    as a value: applicability first, then data, then rule, then coverage.
    """

    if not metric_applies:
        return StateName.NOT_APPLICABLE
    if not rule_ratified:
        return StateName.RULE_NOT_RATIFIED
    if not has_measurements:
        return StateName.INSUFFICIENT_DATA
    if not coverage_sufficiency_rule_ratified:
        return StateName.COVERAGE_SUFFICIENCY_UNKNOWN
    return StateName.INSUFFICIENT_DATA


#: Canonical invariants asserted by the accepted implementation.
INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP: Final[int] = 0
CLASS_B_AND_C_ARE_RULE_GATED: Final[bool] = True
GENERIC_EXPANDING_CONTRACTING_DEFERRED: Final[bool] = True
NO_COMPLETENESS_SCORE: Final[bool] = True


__all__ = [
    "CLASS_B_AND_C_ARE_RULE_GATED",
    "FundamentalStateVector",
    "GENERIC_EXPANDING_CONTRACTING_DEFERRED",
    "INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP",
    "NO_COMPLETENESS_SCORE",
    "PROHIBITED_STATE_NAMES",
    "RuleRatificationStatus",
    "STATE_CLASS_BY_NAME",
    "StateClass",
    "StateDimension",
    "StateError",
    "StateName",
    "StateRule",
    "StateRuleRegistry",
    "VectorStatus",
    "resolve_availability_state",
]
