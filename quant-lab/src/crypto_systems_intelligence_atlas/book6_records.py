"""Book 6 measurement observations — Book 6-local derived records.

A ``MeasurementObservation`` is NOT a Book 2 claim (ratified D6M-1 = A). It is an
immutable, append-preserving derived record that CITES Book 2 authority through
``source_claim_refs``; its authority is resolved live by ``Book6Provenance`` at
every use, never remembered from construction.

Mandatory fields are resolved BY METRIC CATEGORY, not blanket (grammar v0.1
§2.1): a windowed rate must declare its window, an instantaneous stock must not,
and a ratio must carry its denominator as a measured subject with its own
missingness.

The value/missingness contract is fail-closed in both directions: a
value-bearing state may not omit its value, and a value-forbidding state may
not carry one. ``ZERO_OBSERVED`` is a measured zero; every other missingness
state is an absence. No state may launder an absence into a numeric 0.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .book6_definitions import DenominatorRule, MetricDefinition
from .book6_grammar import (
    DENOMINATOR_REQUIRED_CATEGORIES,
    INTERVAL_WINDOW_CLASSES,
    MeasurementCategory,
    MissingnessState,
    ObservationStatus,
    QualityFlag,
    RestatementReason,
    VALUE_BEARING_MISSINGNESS,
    VALUE_FORBIDDEN_MISSINGNESS,
    WindowClass,
)


class MeasurementRecordError(ValueError):
    """A measurement record is structurally invalid."""


class DenominatorRef(BaseModel):
    """The denominator as a first-class measured subject (grammar v0.1 §4).

    ``denominator_measurement_id`` identifies an observation; ``state`` is the
    denominator's OWN missingness/multiplicity state and is never inherited from
    the numerator. A denominator identity change breaks comparability of a series
    even when each individual observation is valid (grammar v0.1 §4.2 rule 3).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    denominator_measurement_id: str = Field(min_length=1)
    denominator_identity: str = Field(min_length=1)
    state: str = Field(min_length=1)
    value: float | None = None

    @model_validator(mode="after")
    def _check_state_value_agreement(self) -> "DenominatorRef":
        from .book6_grammar import DenominatorState

        state = DenominatorState(self.state)
        if state is DenominatorState.PRESENT:
            if self.value is None:
                raise MeasurementRecordError(
                    "a PRESENT denominator must carry its observed value"
                )
            if self.value == 0.0:
                raise MeasurementRecordError(
                    "an observed zero denominator is ZERO, not PRESENT"
                )
        elif state is DenominatorState.ZERO:
            if self.value not in (None, 0.0):
                raise MeasurementRecordError(
                    "a ZERO denominator must carry an observed 0.0, not a "
                    "fabricated non-zero value"
                )
        elif self.value is not None:
            raise MeasurementRecordError(
                f"a {state.value} denominator may not carry a numeric value"
            )
        return self

    @property
    def is_divisible(self) -> bool:
        """Whether a quotient may be computed against this denominator."""

        from .book6_grammar import DIVISIBLE_DENOMINATOR_STATES, DenominatorState

        return DenominatorState(self.state) in DIVISIBLE_DENOMINATOR_STATES


class MeasurementObservation(BaseModel):
    """One measured value for one subject under one methodology (grammar v0.1 §2).

    Immutable. Revision creates a NEW observation that supersedes the prior one;
    the prior value is retained with ``status = SUPERSEDED`` and stays queryable
    (grammar v0.1 §8).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    measurement_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    metric_definition_ref: str = Field(min_length=1)
    category: MeasurementCategory
    missingness_state: MissingnessState
    value: float | None = None
    unit: str | None = None
    numerator_measurement_id: str | None = None
    denominator: DenominatorRef | None = None
    valid_time: datetime
    observed_at: datetime
    window_class: WindowClass
    window_start: datetime | None = None
    window_end: datetime | None = None
    methodology_ref: str = Field(min_length=1)
    methodology_version: str = Field(min_length=1)
    source_claim_refs: tuple[str, ...] = ()
    coverage_observation_id: str | None = None
    quality_flags: tuple[QualityFlag, ...] = ()
    native_scope: str = Field(min_length=1)
    architecture_family: str | None = None
    status: ObservationStatus = ObservationStatus.OBSERVED
    supersedes_measurement_id: str | None = None
    restatement_reason: RestatementReason | None = None

    @model_validator(mode="after")
    def _check_value_and_missingness(self) -> "MeasurementObservation":
        if self.missingness_state in VALUE_FORBIDDEN_MISSINGNESS and self.value is not None:
            raise MeasurementRecordError(
                f"missingness {self.missingness_state.value} forbids a value; a "
                f"fabricated numeric value (including 0) may not be carried "
                f"(MISSING != ZERO)"
            )
        if self.missingness_state in VALUE_BEARING_MISSINGNESS:
            if self.value is None:
                raise MeasurementRecordError(
                    f"missingness {self.missingness_state.value} must carry its "
                    f"observed value"
                )
            if not self.unit:
                raise MeasurementRecordError(
                    "a value-bearing measurement must declare its unit; a value "
                    "never carries an implicit unit"
                )
            if not self.source_claim_refs:
                raise MeasurementRecordError(
                    "a value-bearing measurement must cite Book 2 source authority"
                )
        return self

    @model_validator(mode="after")
    def _check_window_discipline(self) -> "MeasurementObservation":
        if self.window_class in INTERVAL_WINDOW_CLASSES:
            if self.window_start is None or self.window_end is None:
                raise MeasurementRecordError(
                    f"window class {self.window_class.value} requires an explicit "
                    f"[start, end) interval"
                )
            if self.window_start >= self.window_end:
                raise MeasurementRecordError(
                    "window_start must precede window_end"
                )
        else:
            if self.window_start is not None or self.window_end is not None:
                raise MeasurementRecordError(
                    f"window class {self.window_class.value} is instantaneous and "
                    f"may not declare an interval"
                )
        if self.window_end is not None and self.window_end < self.valid_time:
            raise MeasurementRecordError(
                "valid_time may not fall after its own window end"
            )
        return self

    @model_validator(mode="after")
    def _check_denominator_discipline(self) -> "MeasurementObservation":
        if self.category in DENOMINATOR_REQUIRED_CATEGORIES:
            if self.denominator is None:
                raise MeasurementRecordError(
                    "a ratio measurement must carry its denominator as a measured "
                    "subject; a ratio has no implicit divisor"
                )
            # A non-divisible denominator (observed zero, unknown, unavailable,
            # unstable) is NOT a construction error: the record is legitimate and
            # the DENOMINATOR state is explicit. Division is what must fail
            # closed, and it does so in the engine's typed quotient, which
            # returns is_undefined rather than infinity, zero, or a drop.
        elif self.denominator is not None:
            raise MeasurementRecordError(
                f"a {self.category.value} measurement may not declare a denominator"
            )
        return self

    @model_validator(mode="after")
    def _check_supersession_discipline(self) -> "MeasurementObservation":
        if self.status is ObservationStatus.SUPERSEDED and not self.supersedes_measurement_id:
            raise MeasurementRecordError(
                "a SUPERSEDED observation must name the observation it superseded"
            )
        if self.supersedes_measurement_id and not self.restatement_reason:
            raise MeasurementRecordError(
                "a superseding observation must declare its restatement reason; "
                "history is never rewritten without one"
            )
        if self.supersedes_measurement_id == self.measurement_id:
            raise MeasurementRecordError(
                "an observation may not supersede itself"
            )
        return self

    @property
    def is_value_bearing(self) -> bool:
        """Whether this observation asserts a measured value."""

        return self.missingness_state in VALUE_BEARING_MISSINGNESS

    @property
    def methodology_identity(self) -> str:
        """Fully-qualified methodology identity of the producing method."""

        return f"{self.methodology_ref}@{self.methodology_version}"


def validate_against_definition(
    observation: MeasurementObservation, definition: MetricDefinition
) -> None:
    """Fail closed when an observation drifts from its metric definition.

    Checked at use, not only at construction: a forged ``model_copy`` must not be
    able to assert a unit, category or denominator role the definition forbids.
    """

    if observation.metric_definition_ref != definition.metric_id:
        raise MeasurementRecordError(
            f"observation {observation.measurement_id} does not reference its "
            f"declared definition {definition.metric_id}"
        )
    if observation.category is not definition.category:
        raise MeasurementRecordError(
            f"observation {observation.measurement_id} category "
            f"{observation.category.value} contradicts definition category "
            f"{definition.category.value}"
        )
    if observation.window_class is not definition.window_class:
        raise MeasurementRecordError(
            f"observation {observation.measurement_id} window class "
            f"{observation.window_class.value} contradicts definition window "
            f"class {definition.window_class.value}"
        )
    if observation.is_value_bearing and observation.unit != definition.unit:
        raise MeasurementRecordError(
            f"observation {observation.measurement_id} unit {observation.unit!r} "
            f"contradicts definition unit {definition.unit!r}"
        )
    if observation.methodology_ref != definition.methodology.methodology_ref:
        raise MeasurementRecordError(
            f"observation {observation.measurement_id} methodology "
            f"{observation.methodology_ref!r} is not the definition's methodology"
        )
    if definition.denominator_rule is DenominatorRule.OBSERVED_MEASUREMENT:
        if observation.denominator is None:
            raise MeasurementRecordError(
                f"definition {definition.metric_id} requires an observed-measurement "
                f"denominator"
            )
    if definition.applies_to_architectures:
        family = observation.architecture_family
        if family is None:
            raise MeasurementRecordError(
                f"definition {definition.metric_id} is scoped to architectures "
                f"{definition.applies_to_architectures}; the observation declares "
                f"no architecture family"
            )
        if not definition.applies_to(family):
            raise MeasurementRecordError(
                f"metric {definition.metric_id} is NOT_SUPPORTED for architecture "
                f"family {family}; absence is not zero"
            )


#: Canonical invariant: no value may be produced from a missingness state that
#: forbids one.
MISSING_NEVER_BECOMES_ZERO: Final[bool] = True


__all__ = [
    "DenominatorRef",
    "MeasurementObservation",
    "MeasurementRecordError",
    "MISSING_NEVER_BECOMES_ZERO",
    "validate_against_definition",
]
