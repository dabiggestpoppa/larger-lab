"""Book 6 measurement grammar — typed categories that must not collapse.

Book 6 owns measurement DEFINITIONS and descriptive measured state. It owns no
epistemic state machine and defines no claim state (ratified D6M-1 = A:
``MeasurementObservation`` is a Book 6-LOCAL DERIVED RECORD that cites Book 2
authority; it is NOT a Book 2 claim).

This module holds the ratified grammar as distinct Python types. The categories
below are separate enums, not one ``Any``-typed slot: a RATE is not a STOCK, a
COUNT is not a SUM, an OBSERVATION is not a MEASUREMENT, and MISSINGNESS is not
a value. Collapsing them would let a missing input silently become a zero or a
label inherit semantics it never declared.

Canonical sources: ratified Book 6 plan v0.2 §2, measurement grammar v0.1 §1,
state-rule reconciliation v0.1 §3, state-vector design v0.2 §3.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


class GrammarCategory(str, Enum):
    """The twenty ratified grammar terms, as a closed categorical axis.

    The enum keeps the categories *distinct in type* even where several of them
    would share a numeric scalar at runtime. ``MeasurementCategory.RATE`` and
    ``MeasurementCategory.STOCK`` both carry floats, but they are not
    interchangeable and no field may accept one where the other is required.
    """

    RAW_OBSERVATION = "RAW_OBSERVATION"
    MEASUREMENT = "MEASUREMENT"
    METRIC = "METRIC"
    DERIVED_METRIC = "DERIVED_METRIC"
    NORMALIZED_METRIC = "NORMALIZED_METRIC"
    RATE = "RATE"
    RATIO = "RATIO"
    COUNT = "COUNT"
    STOCK = "STOCK"
    FLOW = "FLOW"
    DISTRIBUTION = "DISTRIBUTION"
    INDEX = "INDEX"
    STATE_DIMENSION = "STATE_DIMENSION"
    STATE_VECTOR = "STATE_VECTOR"
    BENCHMARK = "BENCHMARK"
    COHORT = "COHORT"
    METHODOLOGY = "METHODOLOGY"
    DENOMINATOR = "DENOMINATOR"
    COVERAGE = "COVERAGE"
    MISSINGNESS = "MISSINGNESS"
    UNCERTAINTY = "UNCERTAINTY"


class MeasurementCategory(str, Enum):
    """Value-bearing categories (grammar v0.1 §1.1)."""

    RATE = "RATE"
    RATIO = "RATIO"
    COUNT = "COUNT"
    STOCK = "STOCK"
    FLOW = "FLOW"
    DISTRIBUTION = "DISTRIBUTION"
    SCALAR_QUANTITY = "SCALAR_QUANTITY"


#: Categories that require an explicit denominator observation. Dividing through
#: an absent, unknown, or unavailable denominator is a structural failure
#: (grammar v0.1 §4).
DENOMINATOR_REQUIRED_CATEGORIES: Final[frozenset[MeasurementCategory]] = (
    frozenset({MeasurementCategory.RATIO})
)


#: Categories whose value is accumulated over a window rather than held at an
#: instant (grammar v0.1 §1.1). A window is mandatory for these.
WINDOWED_CATEGORIES: Final[frozenset[MeasurementCategory]] = frozenset(
    {MeasurementCategory.RATE, MeasurementCategory.FLOW}
)

#: Categories held at a valid instant.
INSTANTANEOUS_CATEGORIES: Final[frozenset[MeasurementCategory]] = frozenset(
    {MeasurementCategory.STOCK, MeasurementCategory.COUNT}
)


class MeasurementRole(str, Enum):
    """Whether a definition/observation is native or derived (Axiom 1)."""

    NATIVE = "NATIVE"
    DERIVED = "DERIVED"
    #: Normalized values are a distinct role produced ONLY through the ratified
    #: separate ``NormalizationRule`` contract (D6M-2 = B). It is not a flag on
    #: the definition and not an untyped transformation embedded in a methodology.
    NORMALIZED = "NORMALIZED"


class SubjectDomain(str, Enum):
    """What may be a subject of a metric (plan v0.2 §3 MetricDefinition)."""

    CHAIN = "CHAIN"
    PROTOCOL = "PROTOCOL"
    TOKEN = "TOKEN"
    CAPITAL = "CAPITAL"
    DEVELOPER = "DEVELOPER"


class MissingnessState(str, Enum):
    """Ratified missingness states (grammar v0.1 §6).

    Ten distinct states. None collapses into another, and none collapses into a
    numeric value: ``ZERO_OBSERVED`` (a measured zero) is not missingness, and
    ``NOT_COLLECTED`` is not ``ZERO_OBSERVED``.
    """

    OBSERVED = "OBSERVED"
    ZERO_OBSERVED = "ZERO_OBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_COLLECTED = "NOT_COLLECTED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    STALE = "STALE"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    UNKNOWN = "UNKNOWN"


#: States under which a numeric ``value`` may legally be present.
VALUE_BEARING_MISSINGNESS: Final[frozenset[MissingnessState]] = frozenset(
    {MissingnessState.OBSERVED, MissingnessState.ZERO_OBSERVED}
)

#: States that forbid carrying a value. A measurement in one of these states MUST
#: NOT carry a fabricated numeric zero (plan v0.2 §4).
VALUE_FORBIDDEN_MISSINGNESS: Final[frozenset[MissingnessState]] = frozenset(
    set(MissingnessState) - VALUE_BEARING_MISSINGNESS
)


class DenominatorState(str, Enum):
    """Ratified denominator states (grammar v0.1 §4.1).

    The denominator is a first-class measured subject with its own
    missingness. ``ZERO`` is an observed zero and produces an UNDEFINED_RATIO —
    never infinity, never a fabricated zero, never a dropped observation.
    """

    PRESENT = "PRESENT"
    ZERO = "ZERO"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSTABLE = "UNSTABLE"


#: Denominator states under which a quotient may be computed.
DIVISIBLE_DENOMINATOR_STATES: Final[frozenset[DenominatorState]] = frozenset(
    {DenominatorState.PRESENT}
)


class WindowClass(str, Enum):
    """Ratified measurement window classes (grammar v0.1 §5.1).

    "Monthly activity" is not a metric until the window class, the
    calendar/timezone convention, the late-data behaviour and the revision
    behaviour are declared.
    """

    INSTANTANEOUS = "INSTANTANEOUS"
    BLOCK_EPOCH = "BLOCK_EPOCH"
    DAILY = "DAILY"
    ROLLING = "ROLLING"
    CALENDAR_WEEK = "CALENDAR_WEEK"
    CALENDAR_MONTH = "CALENDAR_MONTH"
    QUARTER = "QUARTER"
    LIFETIME = "LIFETIME"
    EVENT_BOUNDED = "EVENT_BOUNDED"
    CUSTOM = "CUSTOM"


#: Window classes that accumulate over an interval and therefore require an
#: explicit closed-open ``[start, end)`` interval.
INTERVAL_WINDOW_CLASSES: Final[frozenset[WindowClass]] = frozenset(
    {
        WindowClass.BLOCK_EPOCH,
        WindowClass.DAILY,
        WindowClass.ROLLING,
        WindowClass.CALENDAR_WEEK,
        WindowClass.CALENDAR_MONTH,
        WindowClass.QUARTER,
        WindowClass.LIFETIME,
        WindowClass.EVENT_BOUNDED,
        WindowClass.CUSTOM,
    }
)


#: Windows in the same class may be compared; different classes may not be
#: compared without an explicit rule (grammar v0.1 §4.2, state-vector v0.2 §4.1
#: "window compatibility").
def windows_are_comparable(left: WindowClass, right: WindowClass) -> bool:
    """Return whether two window classes may be compared as-is.

    Same-class comparison is permitted. Cross-class comparison is NOT permitted
    without a ratified rule, so it reports ``False`` rather than raising: the
    caller decides whether a refusal is a hard error or a deferred state.
    """

    return left is right


class NormalizationType(str, Enum):
    """Ratified-for-planning normalization operations (comparability v0.1 §4).

    ``PERCENTILE_WITHIN_COHORT`` is deliberately ABSENT: it is a ranking surface
    in disguise and was REJECTED (comparability v0.1 §4; Constitution v0.2
    §5.3a). It must not be added merely because a planning corpus mentions it.
    """

    PER_TIME = "PER_TIME"
    PER_USER = "PER_USER"
    PER_TRANSACTION = "PER_TRANSACTION"
    PER_CAPITAL = "PER_CAPITAL"
    PER_VALIDATOR = "PER_VALIDATOR"
    PER_BLOCK = "PER_BLOCK"
    PER_UNIT_SECURITY = "PER_UNIT_SECURITY"
    SHARE_OF_TOTAL = "SHARE_OF_TOTAL"
    GROWTH_RATE = "GROWTH_RATE"
    INDEX_TO_BASE = "INDEX_TO_BASE"


#: Normalization operations that are structurally invalid for a metric category.
#: Validity is scoped to (metric × cohort × methodology), never global
#: (comparability v0.1 §4).
NORMALIZATION_INVALID_FOR: Final[dict[MeasurementCategory, frozenset[NormalizationType]]] = {
    MeasurementCategory.RATIO: frozenset(
        {
            NormalizationType.PER_USER,
            NormalizationType.PER_TRANSACTION,
            NormalizationType.PER_CAPITAL,
            NormalizationType.PER_VALIDATOR,
            NormalizationType.PER_BLOCK,
            NormalizationType.PER_TIME,
        }
    ),
    MeasurementCategory.COUNT: frozenset(
        {NormalizationType.PER_USER, NormalizationType.PER_VALIDATOR, NormalizationType.PER_BLOCK}
    ),
}


class QualityFlag(str, Enum):
    """Typed observation quality flags (grammar v0.1 §2.1)."""

    LATE_DATA = "LATE_DATA"
    PARTIAL_POPULATION = "PARTIAL_POPULATION"
    ESTIMATED_METHOD = "ESTIMATED_METHOD"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    RESTATED = "RESTATED"


class ObservationStatus(str, Enum):
    """Append-preserving measurement lifecycle.

    A revision never overwrites: the prior observation is retained with
    ``SUPERSEDED`` and stays queryable (grammar v0.1 §8).
    """

    OBSERVED = "OBSERVED"
    SUPERSEDED = "SUPERSEDED"


class RestatementReason(str, Enum):
    """Closed set of legitimate measurement restatement causes (grammar v0.1 §8)."""

    LATE_BLOCKS = "LATE_BLOCKS"
    INDEXER_CORRECTION = "INDEXER_CORRECTION"
    SOURCE_BACKFILL = "SOURCE_BACKFILL"
    METHODOLOGY_CHANGE = "METHODOLOGY_CHANGE"
    CHAIN_REORG = "CHAIN_REORG"
    PROTOCOL_ACCOUNTING_CORRECTION = "PROTOCOL_ACCOUNTING_CORRECTION"


#: Restatement causes that are bounded to a specific window rather than the
#: whole history. A chain reorg must not rewrite measurements outside the
#: reorged interval (grammar v0.1 §8 rule 4).
WINDOW_BOUNDED_RESTATEMENT_REASONS: Final[frozenset[RestatementReason]] = frozenset(
    {RestatementReason.CHAIN_REORG}
)


class ArchitectureFamily(str, Enum):
    """Book 3 native architecture families relevant to metric applicability.

    Book 6 never forces a family onto another family's vocabulary: a metric that
    does not exist natively for a subject is ``NOT_SUPPORTED``, never zero
    (Axiom 1; plan v0.2 §6).
    """

    UTXO = "UTXO"
    ACCOUNT_EVM = "ACCOUNT_EVM"
    ACCOUNT_INSTRUCTION = "ACCOUNT_INSTRUCTION"
    DAG = "DAG"
    POS = "POS"
    BFT_FEDERATION = "BFT_FEDERATION"
    PERMISSIONED = "PERMISSIONED"
    POW = "POW"
    MODULAR_ROLLUP = "MODULAR_ROLLUP"


__all__ = [
    "ArchitectureFamily",
    "DENOMINATOR_REQUIRED_CATEGORIES",
    "DenominatorState",
    "DIVISIBLE_DENOMINATOR_STATES",
    "GrammarCategory",
    "INSTANTANEOUS_CATEGORIES",
    "INTERVAL_WINDOW_CLASSES",
    "MeasurementCategory",
    "MeasurementRole",
    "MissingnessState",
    "NORMALIZATION_INVALID_FOR",
    "NormalizationType",
    "ObservationStatus",
    "QualityFlag",
    "RestatementReason",
    "SubjectDomain",
    "VALUE_BEARING_MISSINGNESS",
    "VALUE_FORBIDDEN_MISSINGNESS",
    "WINDOWED_CATEGORIES",
    "WINDOW_BOUNDED_RESTATEMENT_REASONS",
    "WindowClass",
    "windows_are_comparable",
]
