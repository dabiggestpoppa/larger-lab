"""SENSOR-B5-I05 - the six frozen acceptance scenarios F05-01..F05-06.

Frozen authority: I05 directive section 05 (scenario text), bloc_05/06 s13
(the six required timestamp/replay tests), bloc_05/02 s4-s15, s18.

Each scenario is composed from the REAL production functions -- interval
topology, availability derivation, revision selection and the replay gate --
never from a test double, so a scenario passing here is evidence about the
shipped code.  The expected outcome of every scenario is a literal written
from the frozen contract BEFORE the implementation, and is asserted directly.

Adversarial axes covered alongside them: UTC/naive-DST refusal, declared
precision, provider uncertainty (fail-closed registry lookup), interval
boundaries, revision leakage, false availability claims, and source
non-mutation of every upstream object consumed.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.models import ObservationTimeEnvelope
from crypto_sensor_fabric.normalization.time import (
    AcquisitionMetadata,
    CanonicalTimestamp,
    IntervalWindow,
    ProviderTimeSemantics,
    ReplayEligibility,
    ReplayEvidence,
    RevisionMode,
    RevisionRecord,
    RevisionStatus,
    TimestampRole,
    UnknownProviderTimeSemantics,
    assess_replay_eligibility,
    derive_market_available_at,
    parse_provider_time_semantics_yaml,
    select_revisions,
)

UTC = timezone.utc
_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
SEMANTICS_CONFIG = (
    _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_time_semantics.yaml"
)
REVISION_CONFIG = (
    _QUANT_LAB / "config" / "crypto_sensor_fabric" / "revision_policies.yaml"
)

BAR_START = datetime(2024, 6, 1, hour=12, minute=0, tzinfo=UTC)
BAR_END = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
EVENT_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
INGESTED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=5, tzinfo=UTC)
KNOWN_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2025 = datetime(2025, 3, 3, hour=10, tzinfo=UTC)
CUTOFF_2022 = EVENT_2022


def _semantics(
    *,
    convention: IntervalTimeConvention = IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    contemporaneous_public: bool = False,
    refs: tuple[str, ...] = (),
    family: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST,
) -> ProviderTimeSemantics:
    return ProviderTimeSemantics(
        provider="SYNTHETIC_EXCHANGE_A",
        sensor_family=family,
        timestamp_field_roles={TimestampRole.SOURCE_EVENT_AT: "timestamp"},
        interval_time_convention=convention,
        precision=TimestampPrecision.MILLISECOND,
        contemporaneous_public=contemporaneous_public,
        source_evidence_refs=refs,
    )


def _revisions():
    original = RevisionRecord(
        source_revision_id="rev-oi-original",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=KNOWN_2022,
        known_to=None,
    )
    correction = RevisionRecord(
        source_revision_id="rev-oi-corrected-2025",
        normalization_generation=2,
        supersedes_t1_record_id="rev-oi-original",
        revision_status=RevisionStatus.PROVIDER_CORRECTED,
        known_from=KNOWN_2025,
        known_to=None,
    )
    return original, correction


def _policy(mode: RevisionMode):
    from crypto_sensor_fabric.normalization.time import (
        parse_revision_policies_yaml,
    )

    return parse_revision_policies_yaml(
        REVISION_CONFIG.read_text(encoding="utf-8")
    ).policy_for(mode)


def _evidence(**overrides: object) -> ReplayEvidence:
    payload: dict[str, object] = {
        "identity_pit_resolved": True,
        "timestamp_semantics_verified": True,
        "source_evidence_refs": ("provider-docs:synth-a-public-feed",),
        "availability_basis": AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        "availability_confidence": "EVIDENCE_BACKED_DECLARATION",
        "market_available_at": BAR_END,
        "interval_complete": True,
        "revision": select_revisions(_revisions(), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022),
        "lineage": LineageState.LINEAGE_COMPLETE,
        "quality_flags": (NormalizationQualityFlag.LINEAGE_COMPLETE,),
    }
    payload.update(overrides)
    return ReplayEvidence(**payload)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# F05-01
# ---------------------------------------------------------------------------


def test_f05_01_start_stamped_interval_is_not_fully_available_at_its_start() -> None:
    """A 5m bar stamped at 12:00 must not be available at 12:00."""
    window = IntervalWindow(
        interval_start_at=BAR_START,
        interval_end_at=BAR_END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    )
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=BAR_START, ingested_at=BAR_END
        ),
    )
    assert resolution.market_available_at == BAR_END  # expected from bloc_05/02 s6
    assert resolution.market_available_at > BAR_START
    assert resolution.market_available_at >= window.earliest_justified_availability()


# ---------------------------------------------------------------------------
# F05-02
# ---------------------------------------------------------------------------


def test_f05_02_contemporaneously_public_archive_row_is_labeled_historical() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=INGESTED_2026,
            ingested_at=INGESTED_2026,
            contemporaneous_public_evidence_refs=("archive-docs:oi-2022-public",),
        ),
    )
    assert (
        resolution.availability_basis
        is AvailabilityBasis.HISTORICAL_ARCHIVE_RECONSTRUCTION
    )
    assert resolution.market_available_at == EVENT_2022
    assert NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION in (
        resolution.quality_flags
    )
    # And such a row is still admissible: the label is disclosure, not a block.
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=AvailabilityBasis.HISTORICAL_ARCHIVE_RECONSTRUCTION,
            market_available_at=EVENT_2022,
            quality_flags=(NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,),
        )
    )
    assert evaluation.eligibility is ReplayEligibility.ELIGIBLE


# ---------------------------------------------------------------------------
# F05-03 / F05-04
# ---------------------------------------------------------------------------


def test_f05_03_future_correction_never_enters_as_known_then() -> None:
    original, correction = _revisions()
    selection = select_revisions(
        (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert correction not in selection.selected
    assert all(record.known_from <= CUTOFF_2022 for record in selection.selected)
    evaluation = assess_replay_eligibility(_evidence(revision=selection))
    assert evaluation.eligibility is ReplayEligibility.ELIGIBLE


def test_f05_04_retrospective_correction_is_eligible_only_in_retrospective_mode() -> None:
    original, correction = _revisions()
    retrospective = select_revisions(
        (original, correction), _policy(RevisionMode.LATEST_VERIFIED), CUTOFF_2022
    )
    assert retrospective.selected == (correction,)
    evaluation = assess_replay_eligibility(_evidence(revision=retrospective))
    assert evaluation.eligibility is ReplayEligibility.RETROSPECTIVE_ONLY


# ---------------------------------------------------------------------------
# F05-05 / F05-06
# ---------------------------------------------------------------------------


def test_f05_05_unknown_market_availability_blocks_strict_replay() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(family=SensorFamily.MECHANICAL_TRADE),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=INGESTED_2026, ingested_at=INGESTED_2026
        ),
    )
    assert resolution.availability_basis is AvailabilityBasis.SYSTEM_ONLY_OBSERVED
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=resolution.availability_basis,
            market_available_at=resolution.market_available_at,
        )
    )
    assert evaluation.eligibility is ReplayEligibility.BLOCKED_TIMESTAMP


def test_f05_05_unregistered_provider_semantics_blocks_the_row_too() -> None:
    """Unknown provider timestamp semantics fail closed (s18.7, G2)."""
    registry = parse_provider_time_semantics_yaml(
        SEMANTICS_CONFIG.read_text(encoding="utf-8")
    )
    assert registry.resolve("KRAKEN_FUTURES", SensorFamily.MECHANICAL_TRADE) is None
    with pytest.raises(UnknownProviderTimeSemantics):
        registry.require("KRAKEN_FUTURES", SensorFamily.MECHANICAL_TRADE)
    evaluation = assess_replay_eligibility(
        _evidence(timestamp_semantics_verified=False, source_evidence_refs=())
    )
    assert evaluation.eligibility is ReplayEligibility.BLOCKED_TIMESTAMP


def test_f05_06_ingestion_time_cannot_silently_replace_market_availability() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(family=SensorFamily.MECHANICAL_TRADE),
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=INGESTED_2026, ingested_at=INGESTED_2026
        ),
    )
    assert resolution.market_available_at is None
    assert resolution.market_available_at != INGESTED_2026
    # Presenting that system-only claim as a market time is refused outright.
    with pytest.raises(Exception):
        from crypto_sensor_fabric.normalization.time import AvailabilityResolution

        AvailabilityResolution(
            market_available_at=INGESTED_2026,
            availability_basis=AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
            sensor_family=SensorFamily.MECHANICAL_TRADE,
        )


def test_f05_06_ingestion_instant_is_not_an_input_to_the_derivation() -> None:
    base = dict(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        provider_semantics=_semantics(
            family=SensorFamily.MECHANICAL_FUNDING, contemporaneous_public=True,
            refs=("provider-docs:synth-a-funding",),
        ),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
    )
    with_ingest = derive_market_available_at(
        acquisition_metadata=AcquisitionMetadata(ingested_at=INGESTED_2026), **base  # type: ignore[arg-type]
    )
    without_ingest = derive_market_available_at(
        acquisition_metadata=AcquisitionMetadata(), **base  # type: ignore[arg-type]
    )
    assert with_ingest.market_available_at == without_ingest.market_available_at
    assert with_ingest.market_available_at == EVENT_2022


# ---------------------------------------------------------------------------
# Adversarial axes
# ---------------------------------------------------------------------------


def test_adversarial_naive_local_time_in_a_dst_gap_is_refused() -> None:
    """2023-03-12 02:30 local does not exist; naive input can never claim it."""
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=datetime(2023, 3, 12, hour=2, minute=30),
            role=TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
        )
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(source_event_at=datetime(2023, 3, 12, hour=2, minute=30))


def test_adversarial_aware_non_utc_input_normalizes_to_a_single_utc_instant() -> None:
    aware = datetime(2023, 7, 1, hour=14, tzinfo=timezone(timedelta(hours=2)))
    stamp = CanonicalTimestamp(
        at=aware,
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.SECOND,
    )
    assert stamp.at == datetime(2023, 7, 1, hour=12, tzinfo=UTC)
    assert stamp.at.utcoffset() == timedelta(0)


def test_adversarial_precision_is_declared_evidence_not_inferred_from_value() -> None:
    with pytest.raises(ValueError):
        CanonicalTimestamp(
            at=datetime(2024, 6, 1, hour=12, minute=0, second=0, microsecond=500, tzinfo=UTC),
            role=TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.SECOND,
        )
    ok = CanonicalTimestamp(
        at=datetime(2024, 6, 1, hour=12, tzinfo=UTC),
        role=TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.SECOND,
    )
    assert ok.precision is TimestampPrecision.SECOND


def test_adversarial_provider_uncertainty_never_produces_an_availability_time() -> None:
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=None,
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(ingested_at=BAR_END),
    )
    assert resolution.market_available_at is None
    assert resolution.availability_basis is AvailabilityBasis.UNKNOWN


def test_adversarial_all_declared_conventions_hold_their_boundaries() -> None:
    cases = {
        IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN: (True, False),
        IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED: (False, True),
    }
    for convention, (at_start, at_end) in cases.items():
        window = IntervalWindow(
            interval_start_at=BAR_START,
            interval_end_at=BAR_END,
            interval_closed=True,
            interval_time_convention=convention,
        )
        assert window.contains(BAR_START) is at_start, convention
        assert window.contains(BAR_END) is at_end, convention
        assert window.earliest_justified_availability() == BAR_END, convention


def test_adversarial_revision_leakage_is_absent_from_every_selected_record() -> None:
    original, correction = _revisions()
    for cutoff in (CUTOFF_2022, CUTOFF_2022 + timedelta(days=1), KNOWN_2025):
        selection = select_revisions(
            (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), cutoff
        )
        for record in selection.selected:
            assert record.known_from <= cutoff
            if record.known_to is not None:
                assert record.known_to > cutoff
    future = select_revisions(
        (original, correction),
        _policy(RevisionMode.AS_KNOWN_THEN),
        CUTOFF_2022 - timedelta(days=1),
    )
    assert future.selected == ()


def test_adversarial_false_availability_claims_are_refused_at_construction() -> None:
    from crypto_sensor_fabric.normalization.time import AvailabilityResolution

    for basis in (AvailabilityBasis.UNKNOWN, AvailabilityBasis.SYSTEM_ONLY_OBSERVED):
        with pytest.raises(Exception):
            AvailabilityResolution(
                market_available_at=BAR_END,
                availability_basis=basis,
                sensor_family=SensorFamily.MECHANICAL_TRADE,
            )


def test_adversarial_source_objects_are_never_mutated_by_the_pipeline() -> None:
    envelope = ObservationTimeEnvelope(
        interval_start_at=BAR_START,
        interval_end_at=BAR_END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        ingested_at=INGESTED_2026,
        market_available_at=None,
    )
    original, correction = _revisions()
    snapshots = (
        envelope.model_dump(),
        original.model_dump(),
        correction.model_dump(),
    )
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=envelope.interval_start_at,
        interval_end=envelope.interval_end_at,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(ingested_at=envelope.ingested_at),
    )
    selection = select_revisions(
        (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assessment = assess_replay_eligibility(
        _evidence(
            availability_basis=resolution.availability_basis,
            market_available_at=resolution.market_available_at,
            revision=selection,
        )
    )
    assert assessment.eligibility is ReplayEligibility.ELIGIBLE
    assert envelope.model_dump() == snapshots[0]
    assert original.model_dump() == snapshots[1]
    assert correction.model_dump() == snapshots[2]
    assert envelope.ingested_at == INGESTED_2026
    assert envelope.market_available_at is None
