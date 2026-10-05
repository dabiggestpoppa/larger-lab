"""Book 6 baseline selection — RUNG 6 (``PRIOR_COMPARABLE_WINDOW`` + GAP-6).

``PRIOR_COMPARABLE_WINDOW`` is the only executable baseline selector. The other
four names in the closed inventory are refused at construction, in Rung 4, and
nothing here gives them behaviour.

The selector **selects**; it never **aggregates**. Its result is exactly one
``MeasurementObservation`` or ``BASELINE_UNAVAILABLE``. Repeated observations
of a window are already aggregated by ``MetricDefinition.aggregation``, so an
aggregator here would be inventing semantics the metric already owns.

Two ratified orderings are load-bearing, and they are opposite in direction.

**Eligibility strictly precedes ordering.** A candidate that fails any gate is
excluded before any ordering key is compared, so the lexical tie-break can only
ever see candidates that already passed everything. This is what stops a
superseded predecessor from winning a tie it was never eligible for.

**The record-state gate is currentness, not status.** Grammar v0.7 §1.5 writes
this gate as ``observation.status is ObservationStatus.OBSERVED``. That clause
predates two later ratifications which forbid it:

    B-STRICT (BOOK6-GAP7-v0.3)   OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
    TIME-11.1 (test spec v0.6)   REFUSAL_REASON_A = TERMINALITY
                                 STATUS_REFUSAL   = FALSE

TIME-11 is exactly the case that decides it: two candidates tied on everything,
one non-terminal, the non-terminal one given the lexically greater ref. A status
gate would let the v0.4 form of that case pass. So the gate here is the injected
currentness authority — the GAP-7 resolver — whose refusal for a superseded
predecessor is terminality. This is the same precedence rule applied to
CARR-21/TERM-6: the later ratified successor controls over the earlier clause.

Ordering keys are **derived and discarded**. ``effective_start`` and
``effective_end`` are module functions over the accepted record; they are never
written onto a ``MeasurementObservation``, no record field is added, no
interval is fabricated for an instantaneous observation, and there is no
one-day convention. An unrecognised window class is a fail-closed error rather
than a fall-through to a default.

Selection never reads ``coverage_observation_id``. Coverage is an
authorization gate applied *after* structural selection; using it to choose a
candidate would let the gate decide which observation is the baseline, which is
circular.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Final, Sequence

from .book6_comparison_contracts import ComparisonRule
from .book6_grammar import INTERVAL_WINDOW_CLASSES, WindowClass
from .book6_records import MeasurementObservation


class BaselineSelectorError(ValueError):
    """The baseline selector was asked to do something it may not do."""


class BaselineRefusal(str, Enum):
    """Why one candidate was excluded. Names the failing requirement.

    ``AGGREGATE_ONLY = REJECTED``: an exclusion reports *which* gate refused,
    never merely "not eligible", so a failing check can be diagnosed instead of
    guessed at.
    """

    SUBJECT_MISMATCH = "SUBJECT_MISMATCH"
    METRIC_DEFINITION_MISMATCH = "METRIC_DEFINITION_MISMATCH"
    SEMANTIC_FINGERPRINT_MISMATCH = "SEMANTIC_FINGERPRINT_MISMATCH"
    METHODOLOGY_NOT_PERMITTED = "METHODOLOGY_NOT_PERMITTED"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    DENOMINATOR_INCOMPATIBLE = "DENOMINATOR_INCOMPATIBLE"
    WINDOW_INCOMPATIBLE = "WINDOW_INCOMPATIBLE"
    NOT_STRICTLY_PRIOR = "NOT_STRICTLY_PRIOR"
    NOT_CURRENT = "NOT_CURRENT"
    MISSINGNESS_NOT_PERMITTED = "MISSINGNESS_NOT_PERMITTED"
    MISSING_SOURCE_AUTHORITY = "MISSING_SOURCE_AUTHORITY"
    NOT_VALUE_BEARING = "NOT_VALUE_BEARING"


class BaselineOutcome(str, Enum):
    """The selector's two first-class outcomes."""

    RESOLVED = "RESOLVED"
    BASELINE_UNAVAILABLE = "BASELINE_UNAVAILABLE"


#: The one window class that is not an interval. The effective-key projection
#: is total over the closed enum: intervals use their own bounds, this member
#: uses its ``valid_time``, and nothing else is permitted.
NON_INTERVAL_WINDOW_CLASS: Final[WindowClass] = WindowClass.INSTANTANEOUS


def effective_end(observation: MeasurementObservation) -> datetime:
    """The candidate's effective END, derived and never stored.

    For an interval window class this is the observation's own ``window_end``;
    for ``INSTANTANEOUS`` it is ``valid_time``. The accepted record model
    already guarantees the interval fields are present and the instantaneous
    ones absent, so no field is fabricated here.
    """

    if observation.window_class in INTERVAL_WINDOW_CLASSES:
        if observation.window_end is None:  # pragma: no cover - record invariant
            raise BaselineSelectorError(
                f"interval observation {observation.measurement_id} has no "
                f"window_end; the accepted record model forbids this and the "
                f"selector will not default it"
            )
        return observation.window_end
    if observation.window_class is NON_INTERVAL_WINDOW_CLASS:
        return observation.valid_time
    raise BaselineSelectorError(  # pragma: no cover - closed enum
        f"unrecognised window class {observation.window_class!r}; effective-key "
        f"derivation is total over the closed enum and must never fall through "
        f"to a default"
    )


def effective_start(observation: MeasurementObservation) -> datetime:
    """The candidate's effective START, derived and never stored."""

    if observation.window_class in INTERVAL_WINDOW_CLASSES:
        if observation.window_start is None:  # pragma: no cover - record invariant
            raise BaselineSelectorError(
                f"interval observation {observation.measurement_id} has no "
                f"window_start; the accepted record model forbids this and the "
                f"selector will not default it"
            )
        return observation.window_start
    if observation.window_class is NON_INTERVAL_WINDOW_CLASS:
        return observation.valid_time
    raise BaselineSelectorError(  # pragma: no cover - closed enum
        f"unrecognised window class {observation.window_class!r}; effective-key "
        f"derivation is total over the closed enum and must never fall through "
        f"to a default"
    )


@dataclass(frozen=True)
class BaselineResolution:
    """The selector's result: one selected ref, or a first-class refusal.

    A value object, not an authority-bearing contract. It carries no
    ratification, no version, and no lifecycle — it is what the selector
    computed, and it names every exclusion so the refusal is auditable.
    """

    outcome: BaselineOutcome
    selected_measurement_ref: str | None
    eligible_refs: tuple[str, ...]
    exclusions: tuple[tuple[str, BaselineRefusal], ...]

    @property
    def is_resolved(self) -> bool:
        return self.outcome is BaselineOutcome.RESOLVED


def _first_refusal(
    comparison: MeasurementObservation,
    candidate: MeasurementObservation,
    rule: ComparisonRule,
    *,
    semantic_fingerprint_of: Callable[[str], str],
    is_current: Callable[[str], bool],
) -> BaselineRefusal | None:
    """Every eligibility gate for one candidate, in a fixed order.

    Returns the first failing gate, or ``None`` when the candidate is eligible.
    The order is fixed so that a candidate failing several gates always reports
    the same reason, which keeps the audit trail stable across runs.
    """

    # 1. same subject
    if candidate.subject_ref != comparison.subject_ref:
        return BaselineRefusal.SUBJECT_MISMATCH

    # 2. same metric definition
    if candidate.metric_definition_ref != comparison.metric_definition_ref:
        return BaselineRefusal.METRIC_DEFINITION_MISMATCH

    # 3. same metric-definition semantic fingerprint, resolved live
    try:
        fingerprint = semantic_fingerprint_of(candidate.metric_definition_ref)
    except Exception as exc:  # noqa: BLE001
        raise BaselineSelectorError(
            f"metric definition {candidate.metric_definition_ref} did not resolve "
            f"for its semantic fingerprint"
        ) from exc
    if fingerprint != rule.metric_definition_semantic_fingerprint:
        return BaselineRefusal.SEMANTIC_FINGERPRINT_MISMATCH

    # 4. methodology identity/version must be on the explicit allow-list
    if candidate.methodology_identity not in rule.compatible_methodology_refs:
        return BaselineRefusal.METHODOLOGY_NOT_PERMITTED

    # 5. same-metric exact-unit identity: no conversion, ever
    if candidate.unit != comparison.unit or comparison.unit is None:
        return BaselineRefusal.UNIT_MISMATCH

    # 6. compatible denominator semantics
    if candidate.denominator != comparison.denominator:
        return BaselineRefusal.DENOMINATOR_INCOMPATIBLE

    # 8. window compatibility, including shape agreement with the comparison.
    # Mixed temporal shapes are rejected here, BEFORE any ordering runs, so
    # no key is ever compared across shapes and no coercion is attempted.
    if candidate.window_class not in rule.window_compatibility:
        return BaselineRefusal.WINDOW_INCOMPATIBLE
    if candidate.window_class is not comparison.window_class:
        return BaselineRefusal.WINDOW_INCOMPATIBLE

    # 9. strictly precedes. The precedence relation is strict `<`, never `<=`;
    #    a candidate sharing the comparison's own start instant is ineligible.
    if not effective_end(candidate) < effective_start(comparison):
        return BaselineRefusal.NOT_STRICTLY_PRIOR

    # 11. missingness requirements
    if candidate.missingness_state.value not in rule.missingness_requirements:
        return BaselineRefusal.MISSINGNESS_NOT_PERMITTED

    # currentness authority (terminality), NOT status
    if not is_current(candidate.measurement_id):
        return BaselineRefusal.NOT_CURRENT

    # a baseline must be able to carry a value at all: a record that forbids a
    # value can never become one, whatever its missingness state permits
    if not candidate.is_value_bearing:
        return BaselineRefusal.NOT_VALUE_BEARING

    # 10. input Book 2 authority must be cited. The accepted record model
    # already requires this of every value-bearing record, so this gate is the
    # defence against a record built outside that model -- it is deliberately
    # last, so a candidate that failed a more specific gate is reported
    # against that gate rather than this one.
    if not candidate.source_claim_refs:
        return BaselineRefusal.MISSING_SOURCE_AUTHORITY

    return None


def select_baseline(
    *,
    comparison: MeasurementObservation,
    candidates: Sequence[MeasurementObservation],
    rule: ComparisonRule,
    semantic_fingerprint_of: Callable[[str], str],
    is_current: Callable[[str], bool],
) -> BaselineResolution:
    """Select the one prior comparable window, or report BASELINE_UNAVAILABLE.

    ``is_current`` is the injected currentness authority — in production the
    GAP-7 resolver's ``is_authoritative_now``. It is a required parameter with
    no default on purpose: a permissive default would silently reintroduce
    component-wide trust, which is the defect this whole rung is downstream of.

    Determinism: the result is ``max`` over a total key of
    ``(effective_end, effective_start, measurement_ref)``. A total key makes
    the answer independent of ``candidates`` order, and ``observed_at`` and
    ingestion order are never read.

    Coverage is not an input. ``coverage_observation_id`` is not consulted
    anywhere in this module, by design.
    """

    eligible: list[MeasurementObservation] = []
    exclusions: list[tuple[str, BaselineRefusal]] = []

    # Eligibility completes for EVERY candidate before any key is compared.
    for candidate in candidates:
        refusal = _first_refusal(
            comparison,
            candidate,
            rule,
            semantic_fingerprint_of=semantic_fingerprint_of,
            is_current=is_current,
        )
        if refusal is None:
            eligible.append(candidate)
        else:
            exclusions.append((candidate.measurement_id, refusal))

    if not eligible:
        return BaselineResolution(
            outcome=BaselineOutcome.BASELINE_UNAVAILABLE,
            selected_measurement_ref=None,
            eligible_refs=(),
            exclusions=tuple(exclusions),
        )

    selected = max(
        eligible,
        key=lambda o: (effective_end(o), effective_start(o), o.measurement_id),
    )
    return BaselineResolution(
        outcome=BaselineOutcome.RESOLVED,
        selected_measurement_ref=selected.measurement_id,
        eligible_refs=tuple(sorted(o.measurement_id for o in eligible)),
        exclusions=tuple(exclusions),
    )


__all__ = [
    "NON_INTERVAL_WINDOW_CLASS",
    "BaselineOutcome",
    "BaselineRefusal",
    "BaselineResolution",
    "BaselineSelectorError",
    "effective_end",
    "effective_start",
    "select_baseline",
]
