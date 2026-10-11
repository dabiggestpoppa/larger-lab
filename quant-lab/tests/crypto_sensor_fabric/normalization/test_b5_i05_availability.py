"""SENSOR-B5-I05 - RED-first conservative market-availability derivation.

Frozen authority: bloc_05/02 s4 (two availability clocks), s5 (availability
basis), s6 (conservative derivation, function signature quoted verbatim),
s13 (sensor-family anchors), s14 (archive two-layer time), s18 invariants
2/3/6/7.  Scenarios F05-01, F05-02, F05-05 and F05-06 get their core assertion
here; the full six-scenario battery lives in the frozen-scenario suite.

The single law this suite exists to defend: ``ingested_at`` is never an input
to ``market_available_at``.  It is asserted two ways -- by value (the ingestion
instant is never returned) and by construction (changing the ingestion instant
while holding every other input fixed never changes the answer).

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    IntervalTimeConvention,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.time import (
    AcquisitionMetadata,
    ProviderTimeSemantics,
    TimestampRole,
    derive_market_available_at,
)

UTC = timezone.utc

BAR_START = datetime(2024, 6, 1, hour=12, minute=0, tzinfo=UTC)
BAR_END = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
EVENT_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
PUBLISHED = datetime(2024, 6, 1, hour=12, minute=0, second=2, tzinfo=UTC)
INGESTED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=5, tzinfo=UTC)
OBSERVED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=6, tzinfo=UTC)


def _semantics(
    *,
    convention: IntervalTimeConvention = IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    contemporaneous_public: bool = False,
    refs: tuple[str, ...] = (),
) -> ProviderTimeSemantics:
    return ProviderTimeSemantics(
        provider="SYNTHETIC_EXCHANGE_A",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        timestamp_field_roles={TimestampRole.SOURCE_EVENT_AT: "timestamp"},
        interval_time_convention=convention,
        precision=TimestampPrecision.MILLISECOND,
        contemporaneous_public=contemporaneous_public,
        source_evidence_refs=refs,
    )


def _acquisition(
    *,
    observed_at: datetime | None = None,
    ingested_at: datetime | None = None,
    contemporaneous_public_evidence_refs: tuple[str, ...] = (),
) -> AcquisitionMetadata:
    return AcquisitionMetadata(
        observed_at=observed_at,
        ingested_at=ingested_at,
        contemporaneous_public_evidence_refs=contemporaneous_public_evidence_refs,
    )


def _derive(**kwargs: object) -> object:
    return derive_market_available_at(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# F05-01 core -- a completed interval is never available before its close
# ---------------------------------------------------------------------------


def test_start_stamped_interval_is_not_available_at_its_start() -> None:
    """F05-01 core: market_available_at >= interval_end_at, never the start."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_acquisition(),
    )
    assert resolution.market_available_at == BAR_END
    assert resolution.market_available_at > BAR_START
    assert resolution.availability_basis is AvailabilityBasis.PUBLIC_INTERVAL_CLOSE


def test_later_publication_pushes_availability_later_still() -> None:
    """s6: publication after the close proves an even later public time."""
    later = BAR_END + timedelta(seconds=3)
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=later,
        acquisition_metadata=_acquisition(),
    )
    assert resolution.market_available_at == later
    assert resolution.market_available_at >= BAR_END


def test_interval_availability_is_never_before_the_close_for_each_convention() -> None:
    for convention in (
        IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED,
    ):
        resolution = derive_market_available_at(
            sensor_family=SensorFamily.MECHANICAL_LIQUIDATION,
            provider_semantics=_semantics(convention=convention),
            event_time=BAR_START,
            interval_start=BAR_START,
            interval_end=BAR_END,
            published_at=None,
            acquisition_metadata=_acquisition(),
        )
        assert resolution.market_available_at is not None
        assert resolution.market_available_at >= BAR_END, convention
        assert resolution.market_available_at != BAR_START, convention


# ---------------------------------------------------------------------------
# Fail-closed paths: unknown semantics, undeclared bounds, no invention
# ---------------------------------------------------------------------------


def test_unknown_interval_convention_blocks_availability() -> None:
    """bloc_05/02 s7/s18.7: never guess whether 12:00 starts or ends a window."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(
            convention=IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN
        ),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN
    assert (
        NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED
        in resolution.quality_flags
    )
    assert (
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN
        in resolution.quality_flags
    )


def test_interval_without_provider_semantics_fails_closed() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=None,
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN


def test_half_declared_interval_bounds_fail_closed() -> None:
    """s7: a half-declared window is an unknown window, not a usable one."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=None,
        interval_start=BAR_START,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN
    assert (
        NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED
        in resolution.quality_flags
    )


def test_classified_point_sample_is_anchored_at_the_sample_instant() -> None:
    """A snapshot is public at capture ONLY when the provider says so (s5/s6)."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        provider_semantics=_semantics(
            convention=IntervalTimeConvention.POINT_SAMPLE,
            contemporaneous_public=True,
            refs=("provider-docs:synth-a-book",),
        ),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_START,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=BAR_START),
    )
    assert resolution.market_available_at == BAR_START
    assert resolution.availability_basis is AvailabilityBasis.REALTIME_PUBLIC_SNAPSHOT


def test_unclassified_point_sample_fails_closed() -> None:
    """s18.7: an unproven snapshot cannot be placed in market time."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        provider_semantics=_semantics(convention=IntervalTimeConvention.POINT_SAMPLE),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_START,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=BAR_START),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN


def test_publish_time_anchors_availability_when_no_interval_is_declared() -> None:
    """Funding-like case: the rate is knowable before it is applied (s6)."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        provider_semantics=_semantics(),
        event_time=BAR_END,
        interval_start=None,
        interval_end=None,
        published_at=PUBLISHED,
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
    )
    assert resolution.market_available_at == PUBLISHED
    assert resolution.availability_basis is AvailabilityBasis.DELAYED_PUBLICATION


def test_provider_declared_public_field_is_distinguished_from_delayed_publication() -> None:
    """s5: PROVIDER_DECLARED_PUBLIC_TIME is the provider's own declared field."""
    declared = ProviderTimeSemantics(
        provider="SYNTHETIC_EXCHANGE_A",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        timestamp_field_roles={TimestampRole.PUBLISHED_AT: "funding_publish_time"},
        interval_time_convention=IntervalTimeConvention.POINT_SAMPLE,
        precision=TimestampPrecision.SECOND,
        contemporaneous_public=False,
        source_evidence_refs=(),
    )
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        provider_semantics=declared,
        event_time=BAR_END,
        interval_start=None,
        interval_end=None,
        published_at=PUBLISHED,
        acquisition_metadata=_acquisition(ingested_at=PUBLISHED),
    )
    assert resolution.availability_basis is AvailabilityBasis.PROVIDER_DECLARED_PUBLIC_TIME
    assert resolution.market_available_at == PUBLISHED


# ---------------------------------------------------------------------------
# F05-02 -- archive rows are labeled, and only with contemporaneous evidence
# ---------------------------------------------------------------------------


def test_archive_row_with_contemporaneous_public_evidence_is_labeled() -> None:
    """F05-02: obtained in 2026, proven public in 2022 -> ARCHIVE_RECONSTRUCTION."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026,
            ingested_at=INGESTED_2026,
            contemporaneous_public_evidence_refs=("archive-docs:oi-2022-public",),
        ),
    )
    assert resolution.availability_basis is AvailabilityBasis.HISTORICAL_ARCHIVE_RECONSTRUCTION
    assert resolution.market_available_at == EVENT_2022
    assert NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION in resolution.quality_flags


def test_archive_row_without_contemporaneous_evidence_is_not_reconstructed() -> None:
    """s6: archive download time never becomes market availability."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026,
            ingested_at=INGESTED_2026,
        ),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.SYSTEM_ONLY_OBSERVED
    assert resolution.market_available_at != INGESTED_2026


def test_realtime_public_classification_needs_registered_provider_semantics() -> None:
    semantics = _semantics(
        contemporaneous_public=True, refs=("provider-docs:synth-a-trades",)
    )
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=semantics,
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(ingested_at=EVENT_2022),
    )
    assert resolution.availability_basis is AvailabilityBasis.REALTIME_PUBLIC_EVENT
    assert resolution.market_available_at == EVENT_2022


def test_unclassified_provider_source_never_becomes_a_market_time() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(contemporaneous_public=False),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
        ),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.SYSTEM_ONLY_OBSERVED


# ---------------------------------------------------------------------------
# F05-06 -- ingestion is never substituted for market availability
# ---------------------------------------------------------------------------


def test_ingestion_alone_yields_system_only_with_no_market_time() -> None:
    """F05-06 core: we know when WE stored it; that is not market time."""
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(),
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
        ),
    )
    assert resolution.availability_basis is AvailabilityBasis.SYSTEM_ONLY_OBSERVED
    assert resolution.market_available_at is None
    assert NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN in (
        resolution.quality_flags
    )


def test_changing_ingestion_time_never_changes_market_availability() -> None:
    """Construction-level proof: ingested_at is not an input to the derivation."""
    base = dict(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(
            contemporaneous_public=True, refs=("provider-docs:synth-a-trades",)
        ),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
    )
    with_ingest = derive_market_available_at(
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026), **base  # type: ignore[arg-type]
    )
    without_ingest = derive_market_available_at(
        acquisition_metadata=_acquisition(), **base  # type: ignore[arg-type]
    )
    assert with_ingest.market_available_at == without_ingest.market_available_at
    assert with_ingest.availability_basis == without_ingest.availability_basis


def test_no_evidence_at_all_is_unknown_not_invented() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(),
    )
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN
    assert resolution.market_available_at is None
    assert resolution.quality_flags == (
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
    )


# ---------------------------------------------------------------------------
# Model laws for the acquisition evidence and the resolution itself
# ---------------------------------------------------------------------------


def test_acquisition_metadata_is_immutable_and_utc_only() -> None:
    metadata = _acquisition(ingested_at=INGESTED_2026)
    with pytest.raises(Exception):
        metadata.ingested_at = None  # type: ignore[misc]
    with pytest.raises(ValueError):
        AcquisitionMetadata(ingested_at=datetime(2026, 1, 2))  # type: ignore[call-arg]


def test_acquisition_evidence_references_are_validated() -> None:
    with pytest.raises(ValueError):
        AcquisitionMetadata(
            contemporaneous_public_evidence_refs=("docs/archive/file.json",)
        )
    with pytest.raises(ValueError):
        AcquisitionMetadata(
            contemporaneous_public_evidence_refs=("ref:one", "ref:one")
        )


def test_derived_resolution_is_immutable_and_carries_its_family() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        provider_semantics=_semantics(),
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=PUBLISHED,
        acquisition_metadata=_acquisition(),
    )
    assert resolution.sensor_family is SensorFamily.MECHANICAL_FUNDING
    with pytest.raises(Exception):
        resolution.availability_basis = AvailabilityBasis.UNKNOWN  # type: ignore[misc]


def test_derivation_is_pure_and_repeatable() -> None:
    kwargs: dict[str, object] = dict(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_acquisition(),
    )
    first = derive_market_available_at(**kwargs)  # type: ignore[arg-type]
    second = derive_market_available_at(**kwargs)  # type: ignore[arg-type]
    assert first == second
    assert kwargs["interval_start"] == BAR_START
    assert kwargs["event_time"] == BAR_START
