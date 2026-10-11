"""SENSOR-B5-I05 - RED-first canonical timestamp models and time vocabularies.

Authored BEFORE any I05 production code (the B5-I05A commit captures these
failing), so no time model can be shaped to fit a test written after it.

Frozen authority for every assertion here is bloc_05/02 sections 2-10, read
through the I05 readiness assessment section 2.  Compact citations are used
throughout (``bloc_05/02 s<n>`` for section <n>) so this file stays plain
ASCII, matching the I02/I03 authoring convention.

OFFLINE: no network, no provider adapter, no filesystem, no wall clock.  All
fixture times are UTC-aware literals; naive inputs get their own negative
cases because s18 invariant 1 forbids naive timestamps outright.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    IntervalTimeConvention,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.time import (
    TIMESTAMP_ROLE_FIELD,
    AvailabilityResolution,
    CanonicalTimestamp,
    RevisionMode,
    RevisionStatus,
    ReplayEligibility,
    TimestampRole,
)

UTC = timezone.utc

T = datetime(2023, 5, 1, hour=12, minute=30, tzinfo=UTC)
T_MS = datetime(2023, 5, 1, hour=12, minute=30, second=15, microsecond=123000, tzinfo=UTC)
T_S = datetime(2023, 5, 1, hour=12, minute=30, second=15, tzinfo=UTC)
T_DATE_ONLY = datetime(2023, 5, 1, tzinfo=UTC)

NINE_CLOCKS = (
    "source_event_at",
    "interval_start_at",
    "interval_end_at",
    "effective_at",
    "published_at",
    "market_available_at",
    "observed_at",
    "ingested_at",
    "normalized_at",
)


# ---------------------------------------------------------------------------
# s2/s3 - the frozen timestamp-role vocabulary and its field map
# ---------------------------------------------------------------------------


def test_timestamp_role_vocabulary_is_the_frozen_nine() -> None:
    """bloc_05/02 s2 lists exactly nine canonical timestamp fields."""
    assert [member.value for member in TimestampRole] == [c.upper() for c in NINE_CLOCKS]


def test_timestamp_role_field_map_is_total_and_matches_the_frozen_names() -> None:
    """Every role resolves to its frozen field name; no tenth meaning exists."""
    assert set(TIMESTAMP_ROLE_FIELD) == set(TimestampRole)
    for role in TimestampRole:
        assert TIMESTAMP_ROLE_FIELD[role] in NINE_CLOCKS, role
    assert len(set(TIMESTAMP_ROLE_FIELD.values())) == 9, "roles must not collapse"


def test_a_role_never_maps_to_another_roles_field() -> None:
    """s2: null means not-applicable, never "same as another timestamp"."""
    assert TIMESTAMP_ROLE_FIELD[TimestampRole.MARKET_AVAILABLE_AT] == "market_available_at"
    assert TIMESTAMP_ROLE_FIELD[TimestampRole.INGESTED_AT] == "ingested_at"
    assert (
        TIMESTAMP_ROLE_FIELD[TimestampRole.MARKET_AVAILABLE_AT]
        != TIMESTAMP_ROLE_FIELD[TimestampRole.INGESTED_AT]
    )


def test_revision_status_vocabulary_is_the_frozen_six() -> None:
    """bloc_05/02 s10 revision statuses, frozen order."""
    assert [m.value for m in RevisionStatus] == [
        "ORIGINAL",
        "PROVIDER_CORRECTED",
        "SOURCE_MUTATION_REPARSED",
        "NORMALIZATION_REBUILD",
        "IDENTITY_REBUILD",
        "SEMANTIC_REINTERPRETATION",
    ]


def test_revision_mode_vocabulary_is_the_frozen_six() -> None:
    """bloc_05/02 s11 research revision modes, frozen order."""
    assert [m.value for m in RevisionMode] == [
        "AS_KNOWN_THEN",
        "LATEST_VERIFIED",
        "FIRST_SEEN",
        "EXACT_REVISION",
        "ALL_REVISIONS",
        "ERROR_ON_AMBIGUITY",
    ]


def test_replay_eligibility_vocabulary_is_the_frozen_six() -> None:
    """bloc_05/02 s15 replay_eligibility values, frozen order."""
    assert [m.value for m in ReplayEligibility] == [
        "ELIGIBLE",
        "RETROSPECTIVE_ONLY",
        "BLOCKED_TIMESTAMP",
        "BLOCKED_REVISION",
        "BLOCKED_IDENTITY",
        "BLOCKED_LINEAGE",
    ]


def test_time_vocabularies_reuse_i01_enums_instead_of_redeclaring() -> None:
    """AvailabilityBasis/TimestampPrecision/IntervalTimeConvention are I01-owned."""
    from crypto_sensor_fabric.normalization.time import enums as time_enums

    for name in (
        "AvailabilityBasis",
        "TimestampPrecision",
        "IntervalTimeConvention",
        "NormalizationQualityFlag",
    ):
        assert not hasattr(time_enums, name), f"{name} must be imported, never redeclared"


# ---------------------------------------------------------------------------
# s8 - UTC and explicit precision
# ---------------------------------------------------------------------------


def test_naive_timestamp_is_refused() -> None:
    """s18 invariant 1: no naive timestamps."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(at=datetime(2023, 5, 1, hour=12), role=TimestampRole.SOURCE_EVENT_AT, precision=TimestampPrecision.MILLISECOND)


def test_non_utc_offset_is_normalized_to_utc() -> None:
    """Canonical timestamps are UTC (bloc_05/02 s8)."""
    stamp = CanonicalTimestamp(
        at=datetime(2023, 5, 1, hour=14, tzinfo=timezone(timedelta(hours=2))),
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.SECOND,
    )
    assert stamp.at == datetime(2023, 5, 1, hour=12, tzinfo=UTC)
    assert stamp.at.utcoffset() == timedelta(0)


def test_precision_is_required_and_has_no_default() -> None:
    """s8: precision is declared evidence, never inferred or defaulted."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(at=T, role=TimestampRole.SOURCE_EVENT_AT)  # type: ignore[call-arg]


def test_second_precision_refuses_subsecond_value() -> None:
    """s8: no fabricated sub-second ordering on second-precision input."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(at=T_MS, role=TimestampRole.SOURCE_EVENT_AT, precision=TimestampPrecision.SECOND)


def test_millisecond_precision_refuses_microsecond_value() -> None:
    """s8: "do not fabricate microsecond ordering from millisecond input"."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=datetime(2023, 5, 1, hour=12, minute=30, second=15, microsecond=123456, tzinfo=UTC),
            role=TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
        )


def test_millisecond_precision_accepts_a_whole_millisecond_value() -> None:
    stamp = CanonicalTimestamp(
        at=T_MS,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.MILLISECOND,
    )
    assert stamp.at.microsecond == 123000


def test_microsecond_precision_accepts_microsecond_value() -> None:
    stamp = CanonicalTimestamp(
        at=T_MS,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.MICROSECOND,
    )
    assert stamp.precision is TimestampPrecision.MICROSECOND


def test_date_only_precision_requires_midnight() -> None:
    """s8: DATE_ONLY rendered with a time component is still date-only truth."""
    ok = CanonicalTimestamp(
        at=T_DATE_ONLY,
        role=TimestampRole.EFFECTIVE_AT,
        precision=TimestampPrecision.DATE_ONLY,
    )
    assert ok.precision is TimestampPrecision.DATE_ONLY
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=T_S,
            role=TimestampRole.EFFECTIVE_AT,
            precision=TimestampPrecision.DATE_ONLY,
        )


def test_unknown_precision_is_still_declared_not_absent() -> None:
    stamp = CanonicalTimestamp(
        at=T_MS,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.UNKNOWN,
    )
    assert stamp.precision is TimestampPrecision.UNKNOWN


def test_precision_is_a_frozen_member_not_a_free_string() -> None:
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=T,
            role=TimestampRole.SOURCE_EVENT_AT,
            precision="MICROS",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# s9 - clock skew: flagged, never silently corrected, raw value preserved
# ---------------------------------------------------------------------------


def test_skew_methodology_without_a_measured_skew_is_refused() -> None:
    """s9: a methodology with no measured discrepancy is meaningless."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=T,
            role=TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
            clock_skew_methodology_id="SKEW_METHOD_V1",
        )


def test_measured_skew_is_accepted_without_a_correction() -> None:
    """s9: discrepancy is FLAGGED rather than silently corrected."""
    stamp = CanonicalTimestamp(
        at=T,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.MILLISECOND,
        clock_skew_ms=Decimal("-120.5"),
    )
    assert stamp.clock_skew_ms == Decimal("-120.5")
    assert stamp.at == T


def test_skew_never_mutates_the_raw_source_timestamp() -> None:
    """s9: raw source timestamps remain preserved."""
    stamp = CanonicalTimestamp(
        at=T,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.MILLISECOND,
        clock_skew_ms=Decimal("250"),
        clock_skew_methodology_id="SKEW_METHOD_V1",
    )
    assert stamp.at == T, "the stored timestamp must be the raw source value"


def test_negative_and_zero_skew_are_both_representable() -> None:
    for value in (Decimal("-1"), Decimal("0"), Decimal("1.5")):
        stamp = CanonicalTimestamp(
            at=T,
            role=TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
            clock_skew_ms=value,
        )
        assert stamp.clock_skew_ms == value


# ---------------------------------------------------------------------------
# Immutable temporal evidence + the availability resolution contract
# ---------------------------------------------------------------------------


def test_canonical_timestamp_is_immutable() -> None:
    """Phase B: immutable temporal evidence."""
    stamp = CanonicalTimestamp(
        at=T,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.MILLISECOND,
    )
    with pytest.raises(Exception):
        stamp.at = T + timedelta(seconds=1)  # type: ignore[misc]


def test_role_is_required_and_must_be_a_frozen_member() -> None:
    with pytest.raises(ValueError):
        CanonicalTimestamp(at=T, precision=TimestampPrecision.MILLISECOND)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=T,
            role="EVENT_TIME",  # type: ignore[arg-type]
            precision=TimestampPrecision.MILLISECOND,
        )


def test_availability_resolution_never_carries_an_unknown_time() -> None:
    """bloc_05/02 s5: UNKNOWN cannot be placed in market time."""
    with pytest.raises(ValueError):
        AvailabilityResolution(
            market_available_at=T,
            availability_basis=AvailabilityBasis.UNKNOWN,
            sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
        )


def test_availability_resolution_unknown_basis_carries_no_time() -> None:
    resolution = AvailabilityResolution(
        market_available_at=None,
        availability_basis=AvailabilityBasis.UNKNOWN,
        sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
    )
    assert resolution.market_available_at is None


def test_system_only_basis_never_carries_a_market_time() -> None:
    """bloc_05/02 s4/s18.3: ingestion is not market availability."""
    with pytest.raises(ValueError):
        AvailabilityResolution(
            market_available_at=T,
            availability_basis=AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
            sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
        )
    resolution = AvailabilityResolution(
        market_available_at=None,
        availability_basis=AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
        sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
    )
    assert resolution.market_available_at is None


def test_availability_resolution_basis_is_required() -> None:
    with pytest.raises(ValueError):
        AvailabilityResolution(market_available_at=None)  # type: ignore[call-arg]


def test_availability_resolution_quality_flags_use_the_frozen_vocabulary() -> None:
    resolution = AvailabilityResolution(
        market_available_at=None,
        availability_basis=AvailabilityBasis.UNKNOWN,
        sensor_family="MECHANICAL_OPEN_INTEREST",  # type: ignore[arg-type]
        quality_flags=(NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,),
    )
    assert resolution.quality_flags == (
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
    )
    with pytest.raises(ValueError):
        AvailabilityResolution(
            market_available_at=None,
            availability_basis=AvailabilityBasis.UNKNOWN,
            sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
            quality_flags=("TIME_SOMETHING_NEW",),  # type: ignore[arg-type]
        )


def test_availability_resolution_is_immutable() -> None:
    resolution = AvailabilityResolution(
        market_available_at=None,
        availability_basis=AvailabilityBasis.UNKNOWN,
        sensor_family="MECHANICAL_TRADE",  # type: ignore[arg-type]
    )
    with pytest.raises(Exception):
        resolution.availability_basis = AvailabilityBasis.REALTIME_PUBLIC_EVENT  # type: ignore[misc]


def test_declared_interval_convention_is_not_guessed_by_the_models() -> None:
    """bloc_05/02 s7: the convention is declared, never inferred here."""
    assert [m.value for m in IntervalTimeConvention] == [
        "LEFT_CLOSED_RIGHT_OPEN",
        "LEFT_OPEN_RIGHT_CLOSED",
        "PROVIDER_NATIVE_UNKNOWN",
        "POINT_SAMPLE",
    ]
