"""SENSOR-B5-I01A — RED N0 enum tests for the Bloc 5 normalization base layer.

These tests are committed BEFORE the implementation (checkpoint commit B5-I01A
is the type-scope audit plus a deliberately failing enum suite).  They are the
executable form of ``BLOC_05_I01_TYPE_SCOPE_MATRIX.json``: every exact member
set asserted here is copied from a frozen Bloc 5 planning document, and the
docstring of each assertion names that document so a later reviewer can check
the vocabulary against the plan without reading this file's history.

Nothing here is a resolver, a registry, a conversion or a sensor normalizer.
The suite is pure vocabularies: membership, exactness, deterministic string
values, and refusal to let a normalization-owned vocabulary shadow an accepted
Bloc 4 / Bloc 1 one.

OFFLINE.  ``network_calls = 0``: this module imports no provider adapter, no
HTTP client and no storage backend.
"""

from __future__ import annotations

import json

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization import (
    BLOCKED_STATUS_MISSINGNESS_REASON,
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    PayoffType,
    QuarantineReason,
    QualityDimensionState,
    TimestampPrecision,
)
from crypto_sensor_fabric.probes.enums import Granularity
from crypto_sensor_fabric.storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitState,
    SourceUnitVariability,
)

# ---------------------------------------------------------------------------
# Frozen member sets, copied from the plan.
# ---------------------------------------------------------------------------

#: bloc_05/03 §15 canonical observation status.
FROZEN_NORMALIZATION_STATUS = (
    "NORMALIZED",
    "PARTIALLY_NORMALIZED",
    "NATIVE_ONLY",
    "BLOCKED_IDENTITY",
    "BLOCKED_TIME",
    "BLOCKED_SEMANTICS",
    "BLOCKED_CONVERSION",
    "QUARANTINED",
)

#: bloc_05/05 §12 T1 missingness vocabulary (frozen superset of bloc_05/03 §14).
FROZEN_MISSINGNESS = (
    "NOT_REPORTED",
    "NOT_SUPPORTED",
    "NOT_YET_LISTED",
    "DELISTED",
    "HISTORY_UNAVAILABLE",
    "PROVIDER_EMPTY",
    "ACCESS_BLOCKED",
    "SOURCE_GAP",
    "IDENTITY_BLOCKED",
    "TIME_BLOCKED",
    "SEMANTICS_BLOCKED",
    "CONVERSION_BLOCKED",
    "QUARANTINED",
)

#: bloc_05/01 §14 identity flags.
FROZEN_IDENTITY_FLAGS = (
    "IDENTITY_ALIAS_USED",
    "IDENTITY_AMBIGUOUS",
    "IDENTITY_TERMS_UNVERIFIED",
    "IDENTITY_LIFECYCLE_BOUNDARY",
    "IDENTITY_SYMBOL_REUSED",
    "IDENTITY_RELISTED",
    "IDENTITY_CURRENT_METADATA_BACKCAST_RISK",
    "IDENTITY_PROVIDER_ID_MISSING",
    "IDENTITY_MANUAL_OVERRIDE",
    "IDENTITY_STABLECOIN_DISTINCT",
)

#: bloc_05/02 §16 time flags.
FROZEN_TIME_FLAGS = (
    "TIME_SEMANTICS_UNVERIFIED",
    "TIME_INTERVAL_BOUNDARY_UNVERIFIED",
    "TIME_MARKET_AVAILABILITY_UNKNOWN",
    "TIME_ARCHIVE_RECONSTRUCTION",
    "TIME_CLOCK_SKEW",
    "TIME_PRECISION_COARSE",
    "TIME_SEQUENCE_MISSING",
    "PIT_REVISION_UNCERTAIN",
    "PIT_LATE_CORRECTION",
    "PIT_PROVIDER_BACKFILL",
)

#: bloc_05/05 §11 semantics/units flags.
FROZEN_SEMANTIC_UNIT_FLAGS = (
    "SEMANTICS_UNVERIFIED",
    "UNIT_NATIVE_ONLY",
    "UNIT_CONVERSION_BLOCKED",
    "STABLECOIN_CONVERSION_UNAVAILABLE",
    "REFERENCE_PRICE_UNAVAILABLE",
)

#: bloc_05/05 §11 event/dedupe flags.
FROZEN_EVENT_FLAGS = (
    "DUPLICATE_CONFIRMED",
    "DUPLICATE_CANDIDATE",
    "REVISION_PRESENT",
    "SOURCE_DISAGREEMENT",
    "NO_SAFE_DEDUPE_KEY",
)

#: bloc_05/05 §11 book flags.
FROZEN_BOOK_FLAGS = (
    "BOOK_SEQUENCE_GAP",
    "BOOK_PARTIAL_ONLY",
    "BOOK_DEPTH_UNKNOWN",
)

#: bloc_05/05 §11 lineage flags, and the bloc_05/05 §23 invariant-7 state.
FROZEN_LINEAGE_FLAGS = (
    "LINEAGE_COMPLETE",
    "LINEAGE_PARTIAL",
    "LINEAGE_BROKEN",
)

#: Canonical declaration order: bloc_05/05 §11 first (the T1 authority), then the
#: additive bloc_05/01 §14 and bloc_05/02 §16 members in their document order.
#: Declaration order is the canonical serialization order, so it is asserted
#: exactly rather than as a set.
FROZEN_QUALITY_FLAGS = (
    "IDENTITY_ALIAS_USED",
    "IDENTITY_LIFECYCLE_BOUNDARY",
    "IDENTITY_AMBIGUOUS",
    "IDENTITY_TERMS_UNVERIFIED",
    "TIME_SEMANTICS_UNVERIFIED",
    "TIME_ARCHIVE_RECONSTRUCTION",
    "TIME_MARKET_AVAILABILITY_UNKNOWN",
    "PIT_REVISION_UNCERTAIN",
    "SEMANTICS_UNVERIFIED",
    "UNIT_NATIVE_ONLY",
    "UNIT_CONVERSION_BLOCKED",
    "STABLECOIN_CONVERSION_UNAVAILABLE",
    "REFERENCE_PRICE_UNAVAILABLE",
    "DUPLICATE_CONFIRMED",
    "DUPLICATE_CANDIDATE",
    "REVISION_PRESENT",
    "SOURCE_DISAGREEMENT",
    "NO_SAFE_DEDUPE_KEY",
    "BOOK_SEQUENCE_GAP",
    "BOOK_PARTIAL_ONLY",
    "BOOK_DEPTH_UNKNOWN",
    "LINEAGE_COMPLETE",
    "LINEAGE_PARTIAL",
    "LINEAGE_BROKEN",
    "IDENTITY_SYMBOL_REUSED",
    "IDENTITY_RELISTED",
    "IDENTITY_CURRENT_METADATA_BACKCAST_RISK",
    "IDENTITY_PROVIDER_ID_MISSING",
    "IDENTITY_MANUAL_OVERRIDE",
    "IDENTITY_STABLECOIN_DISTINCT",
    "TIME_INTERVAL_BOUNDARY_UNVERIFIED",
    "TIME_CLOCK_SKEW",
    "TIME_PRECISION_COARSE",
    "TIME_SEQUENCE_MISSING",
    "PIT_LATE_CORRECTION",
    "PIT_PROVIDER_BACKFILL",
)

#: bloc_05/01 §3 payoff types.
FROZEN_PAYOFF = ("LINEAR", "INVERSE", "QUANTO", "SPOT", "UNKNOWN")

#: bloc_05/05 §10 per-dimension quality states.
FROZEN_QUALITY_DIMENSION = (
    "VERIFIED",
    "ACCEPTABLE_WITH_FLAGS",
    "PARTIAL",
    "UNKNOWN",
    "BLOCKED",
    "QUARANTINED",
)

#: bloc_05/05 §20 quarantine reasons.
FROZEN_QUARANTINE_REASON = (
    "SCHEMA_FAILURE",
    "IDENTITY_AMBIGUOUS",
    "LINEAGE_BREAK",
    "IMPOSSIBLE_UNITS",
    "INVALID_SIDE_MAPPING",
    "BOOK_SEQUENCE_CORRUPTION",
    "SOURCE_REVISION_CONFLICT",
)

#: bloc_05/02 §7 interval boundary conventions.
FROZEN_INTERVAL_CONVENTION = (
    "LEFT_CLOSED_RIGHT_OPEN",
    "LEFT_OPEN_RIGHT_CLOSED",
    "PROVIDER_NATIVE_UNKNOWN",
    "POINT_SAMPLE",
)

#: bloc_05/02 §5 availability basis.
FROZEN_AVAILABILITY_BASIS = (
    "REALTIME_PUBLIC_EVENT",
    "REALTIME_PUBLIC_SNAPSHOT",
    "PUBLIC_INTERVAL_CLOSE",
    "DELAYED_PUBLICATION",
    "HISTORICAL_ARCHIVE_RECONSTRUCTION",
    "PROVIDER_DECLARED_PUBLIC_TIME",
    "SYSTEM_ONLY_OBSERVED",
    "UNKNOWN",
)

#: bloc_05/02 §8 source timestamp precision.
FROZEN_TIMESTAMP_PRECISION = (
    "SECOND",
    "MILLISECOND",
    "MICROSECOND",
    "NANOSECOND",
    "DATE_ONLY",
    "UNKNOWN",
)


def _names(enum_cls) -> tuple[str, ...]:
    """Member names in DECLARATION order (not sorted, not a set)."""
    return tuple(member.name for member in enum_cls)


# ---------------------------------------------------------------------------
# Exact membership
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("enum_cls", "expected"),
    [
        (NormalizationStatus, FROZEN_NORMALIZATION_STATUS),
        (MissingnessReason, FROZEN_MISSINGNESS),
        (NormalizationQualityFlag, FROZEN_QUALITY_FLAGS),
        (PayoffType, FROZEN_PAYOFF),
        (QualityDimensionState, FROZEN_QUALITY_DIMENSION),
        (QuarantineReason, FROZEN_QUARANTINE_REASON),
        (IntervalTimeConvention, FROZEN_INTERVAL_CONVENTION),
        (AvailabilityBasis, FROZEN_AVAILABILITY_BASIS),
        (TimestampPrecision, FROZEN_TIMESTAMP_PRECISION),
        (LineageState, FROZEN_LINEAGE_FLAGS),
    ],
)
def test_enum_membership_is_exact_and_ordered(enum_cls, expected) -> None:
    """Every frozen member exists, in frozen order, and NOTHING else exists.

    Asserting the exact ordered tuple (not a set) means an added member fails:
    a new vocabulary value is a plan change, not a convenience.
    """
    assert _names(enum_cls) == expected


def test_quality_flag_union_equals_the_three_frozen_documents() -> None:
    """The flag enum is exactly the union of the three frozen Bloc 5 lists."""
    identity = {name for name in FROZEN_IDENTITY_FLAGS}
    time = {name for name in FROZEN_TIME_FLAGS}
    tail = (
        set(FROZEN_SEMANTIC_UNIT_FLAGS)
        | set(FROZEN_EVENT_FLAGS)
        | set(FROZEN_BOOK_FLAGS)
        | set(FROZEN_LINEAGE_FLAGS)
    )
    assert set(_names(NormalizationQualityFlag)) == identity | time | tail
    assert len(_names(NormalizationQualityFlag)) == 36


def test_directive_quality_flag_minimum_is_covered() -> None:
    """Every flag named by the B5-I01 directive §10 is present.

    The directive list is the bloc_05/05 §11 minimum; the enum additionally
    carries the additive doc 01 §14 / doc 02 §16 members, which is additive
    only -- it can never remove a directive-named flag.
    """
    directive_minimum = (
        "IDENTITY_ALIAS_USED",
        "IDENTITY_LIFECYCLE_BOUNDARY",
        "IDENTITY_AMBIGUOUS",
        "IDENTITY_TERMS_UNVERIFIED",
        "TIME_SEMANTICS_UNVERIFIED",
        "TIME_ARCHIVE_RECONSTRUCTION",
        "TIME_MARKET_AVAILABILITY_UNKNOWN",
        "PIT_REVISION_UNCERTAIN",
        "SEMANTICS_UNVERIFIED",
        "UNIT_NATIVE_ONLY",
        "UNIT_CONVERSION_BLOCKED",
        "STABLECOIN_CONVERSION_UNAVAILABLE",
        "REFERENCE_PRICE_UNAVAILABLE",
        "DUPLICATE_CONFIRMED",
        "DUPLICATE_CANDIDATE",
        "REVISION_PRESENT",
        "SOURCE_DISAGREEMENT",
        "NO_SAFE_DEDUPE_KEY",
        "BOOK_SEQUENCE_GAP",
        "BOOK_PARTIAL_ONLY",
        "BOOK_DEPTH_UNKNOWN",
        "LINEAGE_COMPLETE",
        "LINEAGE_PARTIAL",
        "LINEAGE_BROKEN",
    )
    names = set(_names(NormalizationQualityFlag))
    assert set(directive_minimum) <= names


def test_directive_normalization_states_are_covered() -> None:
    """bloc_05/03 §15 keeps the frozen blocked-class spelling, not the §12 one."""
    names = set(_names(NormalizationStatus))
    assert {
        "NORMALIZED",
        "PARTIALLY_NORMALIZED",
        "NATIVE_ONLY",
        "QUARANTINED",
        "BLOCKED_IDENTITY",
        "BLOCKED_TIME",
        "BLOCKED_SEMANTICS",
        "BLOCKED_CONVERSION",
    } == names
    # The §12 spelling belongs to missingness.  A frozen distinction, not a
    # duplicate: collapsing the two would make the correspondence unmeasurable.
    assert "IDENTITY_BLOCKED" in set(_names(MissingnessReason))
    assert "IDENTITY_BLOCKED" not in names


def test_directive_missingness_minimum_is_covered() -> None:
    directive_minimum = (
        "NOT_REPORTED",
        "NOT_SUPPORTED",
        "NOT_YET_LISTED",
        "DELISTED",
        "HISTORY_UNAVAILABLE",
        "PROVIDER_EMPTY",
        "ACCESS_BLOCKED",
        "SOURCE_GAP",
        "IDENTITY_BLOCKED",
        "TIME_BLOCKED",
        "SEMANTICS_BLOCKED",
        "CONVERSION_BLOCKED",
        "QUARANTINED",
    )
    assert _names(MissingnessReason) == directive_minimum


def test_quality_dimension_states_cover_the_directive_four() -> None:
    """bloc_05/05 §10 supersets the directive §9 four; the four are preserved."""
    names = set(_names(QualityDimensionState))
    assert {"VERIFIED", "PARTIAL", "BLOCKED", "QUARANTINED"} <= names
    # UNKNOWN is the lawful "not yet determined" state and ACCEPTABLE_WITH_FLAGS
    # is the frozen middle state; neither is invented by this checkpoint.
    assert "UNKNOWN" in names
    assert "ACCEPTABLE_WITH_FLAGS" in names


# ---------------------------------------------------------------------------
# Deterministic string values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "enum_cls",
    [
        NormalizationStatus,
        MissingnessReason,
        NormalizationQualityFlag,
        PayoffType,
        QualityDimensionState,
        QuarantineReason,
        IntervalTimeConvention,
        AvailabilityBasis,
        TimestampPrecision,
        LineageState,
    ],
)
def test_enum_value_equals_member_name(enum_cls) -> None:
    """Stable string values: ``member.value == member.name``, ``str`` too.

    Deterministic serialization depends on this: a canonical JSON dump must not
    depend on a repr or a memory address.
    """
    for member in enum_cls:
        assert member.value == member.name
        assert str(member) == member.name


@pytest.mark.parametrize(
    "enum_cls",
    [
        NormalizationStatus,
        MissingnessReason,
        NormalizationQualityFlag,
        PayoffType,
        QualityDimensionState,
        QuarantineReason,
        IntervalTimeConvention,
        AvailabilityBasis,
        TimestampPrecision,
        LineageState,
    ],
)
def test_enum_round_trips_through_its_string_value(enum_cls) -> None:
    """enum -> value -> enum is exact, and JSON uses the string value."""
    for member in enum_cls:
        assert enum_cls(member.value) is member
        dumped = json.dumps({"v": member})
        assert json.loads(dumped)["v"] == member.value


def test_unknown_enum_value_fails_explicitly() -> None:
    """bloc_05/06 §3 N0 law: unknown enum handling fails explicitly."""
    with pytest.raises(ValueError):
        NormalizationStatus("NORMALISED")
    with pytest.raises(ValueError):
        MissingnessReason("MISSING")
    with pytest.raises(ValueError):
        NormalizationQualityFlag("SOME_NEW_FLAG")
    with pytest.raises(ValueError):
        PayoffType("OTHER")


# ---------------------------------------------------------------------------
# Frozen correspondence tables
# ---------------------------------------------------------------------------


def test_blocked_status_maps_to_its_typed_missingness_cause() -> None:
    """doc 03 §15 status <-> doc 05 §12 cause, for all four blocked classes."""
    assert dict(BLOCKED_STATUS_MISSINGNESS_REASON) == {
        NormalizationStatus.BLOCKED_IDENTITY: MissingnessReason.IDENTITY_BLOCKED,
        NormalizationStatus.BLOCKED_TIME: MissingnessReason.TIME_BLOCKED,
        NormalizationStatus.BLOCKED_SEMANTICS: MissingnessReason.SEMANTICS_BLOCKED,
        NormalizationStatus.BLOCKED_CONVERSION: MissingnessReason.CONVERSION_BLOCKED,
    }
    # Non-blocked statuses have no blocked-cause correspondence: NORMALIZED and
    # NATIVE_ONLY are not the absence of a cause.
    for status in (
        NormalizationStatus.NORMALIZED,
        NormalizationStatus.PARTIALLY_NORMALIZED,
        NormalizationStatus.NATIVE_ONLY,
        NormalizationStatus.QUARANTINED,
    ):
        assert status not in BLOCKED_STATUS_MISSINGNESS_REASON


def test_blocked_status_correspondence_is_read_only() -> None:
    """The correspondence is frozen data, not a mutable per-run dict."""
    with pytest.raises(TypeError):
        BLOCKED_STATUS_MISSINGNESS_REASON[NormalizationStatus.NORMALIZED] = (  # type: ignore[index]
            MissingnessReason.SOURCE_GAP
        )


def test_blocking_flag_set_is_read_only_and_minimal() -> None:
    """Every blocking flag has an explicit frozen fail-closed citation."""
    expected = {
        NormalizationQualityFlag.IDENTITY_AMBIGUOUS,
        NormalizationQualityFlag.IDENTITY_TERMS_UNVERIFIED,
        NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
        NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
        NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE,
        NormalizationQualityFlag.LINEAGE_BROKEN,
    }
    assert set(BLOCKING_QUALITY_FLAGS) == expected
    with pytest.raises(AttributeError):
        BLOCKING_QUALITY_FLAGS.add(NormalizationQualityFlag.UNIT_NATIVE_ONLY)  # type: ignore[attr-defined]


def test_non_blocking_flags_are_not_in_the_blocking_set() -> None:
    """Label-only flags stay non-blocking.

    TIME_ARCHIVE_RECONSTRUCTION labels archive evidence (doc 02 F10) and
    NO_SAFE_DEDUPE_KEY is a soft-dedupe warning (doc 05 §6/§23); neither makes
    a row unverifiable, so neither may sit in the blocking set.
    """
    for flag in (
        NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,
        NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY,
        NormalizationQualityFlag.DUPLICATE_CANDIDATE,
        NormalizationQualityFlag.SOURCE_DISAGREEMENT,
        NormalizationQualityFlag.UNIT_NATIVE_ONLY,
        NormalizationQualityFlag.IDENTITY_ALIAS_USED,
    ):
        assert flag not in BLOCKING_QUALITY_FLAGS


def test_lineage_broken_is_blocking() -> None:
    """bloc_05/05 §11: ``LINEAGE_BROKEN`` is blocking."""
    assert NormalizationQualityFlag.LINEAGE_BROKEN in BLOCKING_QUALITY_FLAGS
    assert LineageState.LINEAGE_BROKEN.value == "LINEAGE_BROKEN"
    assert LineageState.LINEAGE_COMPLETE.value == "LINEAGE_COMPLETE"
    assert LineageState.LINEAGE_PARTIAL.value == "LINEAGE_PARTIAL"


# ---------------------------------------------------------------------------
# No parallel vocabularies for accepted upstream types
# ---------------------------------------------------------------------------


def test_sensor_family_is_reused_not_duplicated() -> None:
    """The envelope reuses the accepted Bloc 1 SensorFamily (directive §16)."""
    assert {member.value for member in SensorFamily} == {
        "MECHANICAL_TRADE",
        "MECHANICAL_LIQUIDATION",
        "MECHANICAL_OPEN_INTEREST",
        "MECHANICAL_FUNDING",
        "MECHANICAL_BOOK_SNAPSHOT",
        "MECHANICAL_BOOK_METRIC",
        "MECHANICAL_POSITIONING",
        "MECHANICAL_BASIS",
    }
    # No normalization-local SensorFamily exists in the public surface.
    import crypto_sensor_fabric.normalization as normalization

    assert not any(
        name in normalization.__all__ for name in ("SensorFamily", "NormalizationSensorFamily")
    )


def test_granularity_is_reused_not_duplicated() -> None:
    assert {member.value for member in Granularity} == {
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
        "RAW_EVENT",
        "BOOK_SNAPSHOT",
    }
    import crypto_sensor_fabric.normalization as normalization

    assert "Granularity" not in normalization.__all__


def test_bloc4_coverage_revision_and_unit_vocabularies_are_not_redeclared() -> None:
    """CoverageState / RevisionState / SourceUnit* stay exactly where they are."""
    assert "CoverageState" not in _normalization_exports()
    assert "RevisionState" not in _normalization_exports()
    assert "RevisionPolicy" not in _normalization_exports()
    for name in ("SourceUnitState", "SourceUnitVariability", "SourceUnitContract"):
        assert name not in _normalization_exports()
        assert name not in _normalization_module_members()
    # They remain reachable and unchanged where Bloc 4 put them.
    assert SourceUnitState.VERIFIED_NATIVE.value == "VERIFIED_NATIVE"
    assert SourceUnitVariability.ROW_NATIVE.value == "ROW_NATIVE"
    assert SourceUnitContract.NO_UNIT_FIELDS.value == "NO_UNIT_FIELDS"
    assert CoverageState.EMPTY_CONFIRMED.value == "EMPTY_CONFIRMED"
    assert RevisionState.SOURCE_MUTATION.value == "SOURCE_MUTATION"


def test_normalization_package_does_not_shadow_a_bloc4_name() -> None:
    """No public normalization symbol may duplicate an accepted Bloc 4 name.

    Parallel vocabularies are how frozen distinctions get lost, so this is
    checked against the accepted 200-symbol public handoff surface itself.
    """
    import crypto_sensor_fabric.storage as storage

    exported = set(storage.__all__)
    assert exported, "storage public surface unexpectedly empty"
    collisions = exported & set(_normalization_exports())
    assert collisions == set()


def _normalization_exports() -> frozenset[str]:
    import crypto_sensor_fabric.normalization as normalization

    return frozenset(normalization.__all__)


def _normalization_module_members() -> set[str]:
    from crypto_sensor_fabric.normalization import enums as normalization_enums

    return {
        name
        for name in vars(normalization_enums)
        if not name.startswith("_") and isinstance(vars(normalization_enums)[name], type)
    }