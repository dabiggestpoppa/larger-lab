"""Book 6 comparison / change contracts — RUNG 4 (types and contracts).

This module introduces exactly **two** new public authority-bearing classes:

    ComparisonRule        how a comparison is permitted to be made
    ChangeObservation     the record a permitted comparison produces

plus closed supporting types and value objects. The count is load-bearing:
``NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2`` and
``HIDDEN_THIRD_CONTRACT = NONE`` (plan v0.6 §5, plan v0.7 §1). ``BaselineSelectorSpec``
is deliberately NOT a third contract class — it is nested rule content, so it
has no registry, no ratification ledger, no independent lifecycle, and no
authority of its own. See the class docstring for how that is enforced.

Scope of this rung is **types and contracts only**. The twenty authority-replay
checks, the fingerprint, the executable ``PRIOR_COMPARABLE_WINDOW`` selector,
the coverage and temporal-comparability derivations, and the delta arithmetic
are later rungs. What lands here is the closed vocabulary those rungs are
written against, plus the invariants that are decidable from a record's own
shape.

The doctrine this encodes is ratified; the five repairs it encodes are:

    GAP-1  1A-STRICT   stored binary64, exact stored-value equality, finite
                       input, no epsilon and no migration
    GAP-2  2D          same-metric exact-unit identity, no conversion
    GAP-3  3C          coverage applicability from rule presence
    GAP-4  4D          TemporalComparabilityStatus with a producing check;
                       UNRESOLVED never maps to NOT_COMPARABLE
    GAP-5  5E          ComparisonRule-owned BaselineSelectorSpec

Two firewalls are structurally enforced rather than merely documented, because
a closed schema is the only way to actually forbid a field:

*Materiality.* There is no epsilon field, no tolerance field, no materiality
field, and no significance field, so no threshold below which a difference
stops being a change can be expressed through a rule parameter at all.
``NO_CHANGE`` means exact canonical equality and nothing else.

*Anti-score.* ``display_metadata`` exists and is carried, but it is excluded
from equality-relevant derivation by construction: it is a separate field that
no derivation in this module reads. The Rung 5 fingerprint excludes it too.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Final

from pydantic import Field, model_validator

from .book6_frozen import Book6FrozenModel
from .book6_grammar import WindowClass


class ComparisonContractError(ValueError):
    """A comparison or change record violates its ratified contract."""


# ---------------------------------------------------------------------------
# Closed vocabularies
# ---------------------------------------------------------------------------


class DeltaOperator(str, Enum):
    """The complete, closed set of delta operators (grammar v0.4 §1.1).

    There is no free-form formula, no expression language, and no
    caller-supplied formula. A new operator requires a contract version, not
    a string.
    """

    ABSOLUTE_DELTA = "ABSOLUTE_DELTA"
    RELATIVE_DELTA = "RELATIVE_DELTA"


class ChangeAxis(str, Enum):
    """The single ratified axis for a change record (grammar v0.4 §4)."""

    MEASUREMENT_CHANGE = "MEASUREMENT_CHANGE"


class ChangeKind(str, Enum):
    """The complete, closed set of change outcomes (grammar v0.4 §3).

    Derived from the sign of the canonical **unrounded** absolute delta, never
    from display, precision, tolerance, or relative magnitude.
    """

    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    NO_CHANGE = "NO_CHANGE"
    CHANGE_UNDEFINED = "CHANGE_UNDEFINED"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TemporalComparabilityStatus(str, Enum):
    """The closed domain of ``comparability_status`` (grammar v0.5 §3.1).

    This closes the GAP-4 defect: v0.4 listed ``comparability_status`` as
    required but gave it no value domain and no producing check, so
    ``change_kind = NOT_COMPARABLE`` existed with nothing able to produce it.

    It is deliberately NOT ``CorpusVerdict``, NOT ``ComparabilityClass``, NOT
    ``StateName``, and NOT ``ClaimState``. It applies only to the single-metric
    temporal comparison/change engine.

    The three members are not interchangeable:

        COMPARABLE       all applicable structural gates passed
        NOT_COMPARABLE   an explicit structural requirement FAILED
        UNRESOLVED       insufficient authoritative basis to decide

    ``UNRESOLVED`` is **never** mapped to ``NOT_COMPARABLE``. A structural
    failure is a decision; absence of basis is not a failure.
    """

    COMPARABLE = "COMPARABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    UNRESOLVED = "UNRESOLVED"


class CoverageRequirementStatus(str, Enum):
    """The derived tri-state coverage requirement (grammar v0.4 §1, R-2)."""

    REQUIRED = "REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNRESOLVED = "UNRESOLVED"


class CoverageObservationState(str, Enum):
    """The R-3 discriminator splitting coverage into three real states.

    The pre-split ``coverage_observation`` was a ref-or-``None`` that meant
    both "no coverage needed" and "coverage needed but not available". Those
    are different facts with different downstream consequences, so they are
    now separate members.
    """

    PRESENT = "PRESENT"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CoverageVerdict(str, Enum):
    """A coverage verdict, always replayed from a ratified rule.

    Never self-declared. No numeric sufficiency threshold may live on a
    comparison rule; sufficiency is what ratified coverage-sufficiency rules
    decide (see ``book6_coverage_rules``).
    """

    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class BaselineSelectorKind(str, Enum):
    """The closed baseline-selector inventory (grammar v0.6 §2.2.3).

    Exactly one member is executable. The four reserved names are **not**
    accepted runtime methods and carry no placeholder behaviour: constructing a
    ``ComparisonRule`` with any of them is rejected here, before any resolution
    work. They may become executable only via separate successor governance
    specifying inputs, parameters, window semantics, aggregation semantics,
    missingness, fingerprint content, and tests.
    """

    PRIOR_COMPARABLE_WINDOW = "PRIOR_COMPARABLE_WINDOW"
    ROLLING_MEAN = "ROLLING_MEAN"
    ROLLING_MEDIAN = "ROLLING_MEDIAN"
    HISTORICAL_DISTRIBUTION = "HISTORICAL_DISTRIBUTION"
    BASELINE_EPOCH = "BASELINE_EPOCH"


EXECUTABLE_BASELINE_SELECTOR: Final[BaselineSelectorKind] = (
    BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW
)

RESERVED_NOT_EXECUTABLE_SELECTORS: Final[frozenset[BaselineSelectorKind]] = frozenset(
    kind for kind in BaselineSelectorKind if kind is not EXECUTABLE_BASELINE_SELECTOR
)


class BaselineOrderingPolicy(str, Enum):
    """The only permitted ordering policy (grammar v0.6 §2.2.4).

    No caller ordering, no ``observed_at`` economic-time ordering, no
    ingestion time, no randomness, no insertion order. The lexical tie-break
    exists only so that a tie resolves to exactly one observation rather than
    to implementation-defined behaviour.
    """

    LATEST_PRIOR_VALID_TIME_END_THEN_START_THEN_LEXICAL_REF = (
        "LATEST_PRIOR_VALID_TIME_END_THEN_START_THEN_LEXICAL_REF"
    )


# ---------------------------------------------------------------------------
# Nested value object — NOT an authority-bearing class
# ---------------------------------------------------------------------------


class BaselineSelectorSpec(Book6FrozenModel):
    """Nested rule content describing how a baseline is selected.

    This is **not** a third authority-bearing contract class. It has no
    registry, no ratification ledger, no independent lifecycle, and no version
    of its own; it cannot be ratified, cannot be looked up, and carries no
    authority outside the ``ComparisonRule`` that owns it. Its semantic content
    is fingerprinted as part of that rule's own content in Rung 5.

    It is a frozen value object precisely so that the bound is structural: the
    only way to hold one is as a field of a rule.
    """

    selector_kind: BaselineSelectorKind
    window_compatibility: tuple[WindowClass, ...] = Field(min_length=1)
    methodology_compatibility: tuple[str, ...] = Field(min_length=1)
    denominator_requirements: tuple[str, ...] = ()
    cohort_requirements: tuple[str, ...] = ()
    ordering_policy: BaselineOrderingPolicy = (
        BaselineOrderingPolicy.LATEST_PRIOR_VALID_TIME_END_THEN_START_THEN_LEXICAL_REF
    )

    @model_validator(mode="after")
    def _check_executable(self) -> "BaselineSelectorSpec":
        """Reject reserved selector names at construction.

        Reserved names are refused here rather than at resolution time so that
        a rule naming one can never exist, let alone be ratified. There is no
        placeholder behaviour to fall into.
        """

        if self.selector_kind in RESERVED_NOT_EXECUTABLE_SELECTORS:
            raise ComparisonContractError(
                f"{self.selector_kind.value} is RESERVED_NOT_EXECUTABLE; the only "
                f"executable baseline selector is "
                f"{EXECUTABLE_BASELINE_SELECTOR.value}. Reserved names carry no "
                f"placeholder behaviour and become executable only via separate "
                f"successor governance."
            )
        return self


# ---------------------------------------------------------------------------
# Authority-bearing class 1 of 2
# ---------------------------------------------------------------------------


class ComparisonRule(Book6FrozenModel):
    """How a comparison is permitted to be made. Authority-bearing class 1 of 2.

    A rule is versioned and superseded, never mutated. Its identity, its
    operator-ratification binding, and its canonical content fingerprint are
    the subject of replay checks 1-3; the baseline selector it owns is the
    subject of checks 4-6.

    Deliberately absent, because each was a policy surface a rule author could
    otherwise influence and none is a genuine choice:

        direction_derivation      direction is the sign of the canonical
                                 UNROUNDED absolute delta
        zero_baseline_policy      relative delta is UNDEFINED at baseline 0;
                                 never 0, inf, NaN, capped, or percentage
        unit_divisibility_policy  derived from the accepted typed unit
                                 contract; a rule may cite requirements and
                                 never redefine mathematics
        rounding_precision_policy presentation only, lives in
                                 ``display_metadata``, outside every
                                 derivation and fingerprint

    ``compatible_methodology_refs`` is an explicit allow-list. There is no
    wildcard.
    """

    comparison_rule_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    supersedes_ref: str | None = None

    metric_definition_ref: str = Field(min_length=1)
    metric_definition_semantic_fingerprint: str = Field(min_length=1)

    baseline_selector: BaselineSelectorSpec
    delta_operator: DeltaOperator

    compatible_methodology_refs: tuple[str, ...] = Field(min_length=1)
    unit_requirements: str = Field(min_length=1)
    denominator_requirements: tuple[str, ...] = ()
    cohort_requirements: tuple[str, ...] = ()
    window_compatibility: tuple[WindowClass, ...] = Field(min_length=1)
    missingness_requirements: tuple[str, ...] = Field(min_length=1)
    output_semantics: str = Field(min_length=1)

    coverage_requirement_status: CoverageRequirementStatus
    coverage_applicability_source_ref: str | None = None
    coverage_sufficiency_rule_ref: str | None = None

    display_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_supersession(self) -> "ComparisonRule":
        """R-5: absence of ``supersedes_ref`` means exactly one thing.

        ``version == 1`` -> absent. ``version > 1`` -> required, and rejected
        if absent. Silence about a known supersession is not a first-version
        claim; it is an omission.
        """

        if self.version == 1:
            if self.supersedes_ref is not None:
                raise ComparisonContractError(
                    "a first-version ComparisonRule (version == 1) must not "
                    "carry supersedes_ref; absence is the only spelling of "
                    "'this is the first version'"
                )
        elif self.supersedes_ref is None:
            raise ComparisonContractError(
                f"ComparisonRule version {self.version} must declare "
                f"supersedes_ref; a later version may not be silently "
                f"unlinked from the version it replaces"
            )
        return self

    @model_validator(mode="after")
    def _check_coverage_applicability(self) -> "ComparisonRule":
        """R-2: ``coverage_applicability_source_ref`` has a single meaning.

        Absent means ``NO_UPSTREAM_DETERMINATION_EXISTS`` and nothing else.
        It is required whenever the status is ``REQUIRED`` or
        ``NOT_APPLICABLE``, because in both of those an upstream determination
        demonstrably exists — claiming none did is a contradiction rather than
        an absence.
        """

        if self.coverage_requirement_status in (
            CoverageRequirementStatus.REQUIRED,
            CoverageRequirementStatus.NOT_APPLICABLE,
        ) and self.coverage_applicability_source_ref is None:
            raise ComparisonContractError(
                f"coverage_applicability_source_ref is required when "
                f"coverage_requirement_status is "
                f"{self.coverage_requirement_status.value}; absence means "
                f"NO_UPSTREAM_DETERMINATION_EXISTS, and no determination "
                f"exists for a status that asserts one was made"
            )
        if self.coverage_requirement_status is CoverageRequirementStatus.REQUIRED:
            if self.coverage_sufficiency_rule_ref is None:
                raise ComparisonContractError(
                    "coverage_sufficiency_rule_ref is required when coverage is "
                    "REQUIRED; coverage sufficiency is decided by a ratified "
                    "rule, never by the comparison rule asserting it"
                )
        elif self.coverage_sufficiency_rule_ref is not None:
            raise ComparisonContractError(
                f"coverage_sufficiency_rule_ref must be absent when coverage is "
                f"{self.coverage_requirement_status.value}; naming a "
                f"sufficiency rule where none is required would let a rule "
                f"manufacture its own coverage verdict"
            )
        return self


# ---------------------------------------------------------------------------
# Authority-bearing class 2 of 2
# ---------------------------------------------------------------------------


class ChangeObservation(Book6FrozenModel):
    """The record a permitted comparison produces. Authority-bearing class 2 of 2.

    This is a derived record, Book 6-local, and carries no D6M authority of
    its own (plan v0.4 §9, D6M-1).

    Presence and absence are each single-meaning here, which is the whole point
    of the ``AC-17`` repair:

        ``absolute_delta`` absent   -> NOT COMPUTABLE, never "0"
        ``relative_delta`` absent   -> UNDEFINED, never 0 / inf / NaN / capped
        ``selected_baseline_measurement_ref`` absent -> BASELINE_UNAVAILABLE,
                                     and nothing else
        ``coverage_observation_ref`` absent -> only when the state is
                                     UNAVAILABLE or NOT_APPLICABLE

    ``NOT_APPLICABLE`` is never used as an absence encoding. It is a real
    member of a real closed enum, and the states that mean "not needed" and
    "needed but not obtained" are separate members rather than one ``None``.
    """

    change_observation_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    axis: ChangeAxis = ChangeAxis.MEASUREMENT_CHANGE
    valid_time: datetime

    metric_definition_ref: str = Field(min_length=1)
    metric_definition_semantic_fingerprint: str = Field(min_length=1)

    comparison_rule_ref: str = Field(min_length=1)
    comparison_rule_version: int = Field(ge=1)
    comparison_rule_fingerprint: str = Field(min_length=1)
    derivation_binding_ref: str = Field(min_length=1)

    baseline_selector_spec_fingerprint: str = Field(min_length=1)
    baseline_measurement_refs: tuple[str, ...] = Field(min_length=1)
    comparison_measurement_refs: tuple[str, ...] = Field(min_length=1)
    selected_baseline_measurement_ref: str | None = None

    absolute_delta: float | None = None
    relative_delta: float | None = None
    delta_operator: DeltaOperator

    change_kind: ChangeKind
    unit: str = Field(min_length=1)
    source_measurement_refs: tuple[str, ...] = Field(min_length=1)
    measurement_methodology_refs: tuple[str, ...] = Field(min_length=1)

    coverage_requirement_status: CoverageRequirementStatus
    coverage_applicability_source_ref: str | None = None
    coverage_observation_state: CoverageObservationState
    coverage_observation_ref: str | None = None
    coverage_verdict: CoverageVerdict

    missingness: str = Field(min_length=1)
    comparability_status: TemporalComparabilityStatus
    comparability_refusal_reasons: tuple[tuple[str, str], ...] = ()

    display_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_finite_stored_values(self) -> "ChangeObservation":
        """GAP-1: stored binary64, finite input required, exact equality.

        No epsilon, no ``isclose``, no tolerance. A non-finite stored value is
        refused at construction rather than being carried as a sentinel,
        because a sentinel here would be indistinguishable from a real result.
        """

        for name in ("absolute_delta", "relative_delta"):
            value = getattr(self, name)
            if value is not None and (value != value or value in (float("inf"), float("-inf"))):
                raise ComparisonContractError(
                    f"{name} must be a finite stored binary64 value; a "
                    f"non-finite delta is refused rather than carried as a "
                    f"sentinel that a reader could mistake for a result"
                )
        return self

    @model_validator(mode="after")
    def _check_coverage_observation(self) -> "ChangeObservation":
        """R-3: the discriminator and the ref are one fact, not two."""

        if self.coverage_observation_state is CoverageObservationState.PRESENT:
            if self.coverage_observation_ref is None:
                raise ComparisonContractError(
                    "coverage_observation_ref is required when "
                    "coverage_observation_state is PRESENT"
                )
        elif self.coverage_observation_ref is not None:
            raise ComparisonContractError(
                f"coverage_observation_ref must be absent when "
                f"coverage_observation_state is "
                f"{self.coverage_observation_state.value}; silence about known "
                f"coverage is INVALID"
            )
        return self

    @model_validator(mode="after")
    def _check_comparability_mapping(self) -> "ChangeObservation":
        """The ``comparability_status`` -> ``change_kind`` law (grammar v0.5 §3.4).

        The direction of the mapping matters. ``UNRESOLVED`` means there was
        not enough authoritative basis to decide, which is a different fact
        from a structural incompatibility, so it maps to ``INSUFFICIENT_DATA``
        and never to ``NOT_COMPARABLE``. Collapsing the two would report a
        decision the engine never made.
        """

        expected = {
            TemporalComparabilityStatus.NOT_COMPARABLE: ChangeKind.NOT_COMPARABLE,
            TemporalComparabilityStatus.UNRESOLVED: ChangeKind.INSUFFICIENT_DATA,
        }.get(self.comparability_status)

        if expected is not None and self.change_kind is not expected:
            raise ComparisonContractError(
                f"comparability_status {self.comparability_status.value} implies "
                f"change_kind {expected.value}, not {self.change_kind.value}; "
                f"UNRESOLVED is never mapped to NOT_COMPARABLE"
            )

        if self.comparability_status is TemporalComparabilityStatus.COMPARABLE:
            if self.change_kind in (
                ChangeKind.NOT_COMPARABLE,
                ChangeKind.INSUFFICIENT_DATA,
            ):
                raise ComparisonContractError(
                    f"comparability_status COMPARABLE cannot carry change_kind "
                    f"{self.change_kind.value}; the two are contradictory"
                )
        return self

    @model_validator(mode="after")
    def _check_baseline_presence(self) -> "ChangeObservation":
        """A resolved baseline and an unresolved one are different facts.

        A baseline is selected only when arithmetic actually ran. Both
        ``NOT_COMPARABLE`` and ``INSUFFICIENT_DATA`` mean no comparison
        reached the arithmetic stage — the first because a structural gate
        failed, the second because there was not enough authoritative basis —
        so in both cases a selected baseline would assert a resolution that
        did not happen.
        """

        resolved_kinds = (
            ChangeKind.INCREASE,
            ChangeKind.DECREASE,
            ChangeKind.NO_CHANGE,
            ChangeKind.CHANGE_UNDEFINED,
        )
        baseline_resolved = self.change_kind in resolved_kinds
        if baseline_resolved and self.selected_baseline_measurement_ref is None:
            raise ComparisonContractError(
                f"selected_baseline_measurement_ref is required when "
                f"change_kind is {self.change_kind.value}; its absence means "
                f"BASELINE_UNAVAILABLE and only that"
            )
        if not baseline_resolved and self.selected_baseline_measurement_ref is not None:
            raise ComparisonContractError(
                f"selected_baseline_measurement_ref must be absent when "
                f"change_kind is {self.change_kind.value}; presence of a "
                f"selected baseline asserts a resolution that did not happen"
            )
        return self

    @model_validator(mode="after")
    def _check_temporal_comparability_has_a_producer(self) -> "ChangeObservation":
        """GAP-4: ``NOT_COMPARABLE`` and ``UNRESOLVED`` require a recorded cause.

        Either status is a decision, and a decision has to say which gate
        produced it. This is what stops the field from being a free-standing
        assertion with no producer — the v0.4 defect.
        """

        if self.comparability_status in (
            TemporalComparabilityStatus.NOT_COMPARABLE,
            TemporalComparabilityStatus.UNRESOLVED,
        ):
            if not self.comparability_refusal_reasons:
                raise ComparisonContractError(
                    f"comparability_status {self.comparability_status.value} "
                    f"requires at least one recorded producing gate; a status "
                    f"with no producer is an assertion, not a decision"
                )
        return self


__all__ = [
    "BaselineOrderingPolicy",
    "BaselineSelectorKind",
    "BaselineSelectorSpec",
    "ChangeAxis",
    "ChangeKind",
    "ChangeObservation",
    "ComparisonContractError",
    "ComparisonRule",
    "CoverageObservationState",
    "CoverageRequirementStatus",
    "CoverageVerdict",
    "DeltaOperator",
    "EXECUTABLE_BASELINE_SELECTOR",
    "RESERVED_NOT_EXECUTABLE_SELECTORS",
    "TemporalComparabilityStatus",
]
