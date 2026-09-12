"""Coverage vector + redundancy tests (T2-COV-01..06, T2-SEM-03)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from crypto_sensor_fabric.contracts.enums import (
    SemanticEquivalence,
    SensorFamily,
)
from crypto_sensor_fabric.probes.coverage import (
    CoverageVector,
    VerifiedSource,
    compute_coverage_vector,
    compute_sensor_redundancy,
    synthesize_coverage,
)
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    CapabilityStatus,
    EvidenceSourceClass,
    FreeOnlyStatus,
    Granularity,
    ProbeFailureClass,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import CapabilityProbeAttempt

RECENT = "RECENT_CONTROL"


_ERA_YEARS = {"2021": 2021, "2022": 2022, "2024": 2024, "2026": 2026}


def make_attempt(
    *,
    era: str,
    status: ResponseStatusClass = ResponseStatusClass.VERIFIED_SAMPLE,
    error_class: ProbeFailureClass | None = None,
    timestamp_fields: list[str] | None = None,
    unit_summary: dict[str, str] | None = None,
    fingerprint: str | None = None,
    granularity: Granularity = Granularity.G1D,
    instrument: str = "PI_XBTUSD",
    pagination_detected: bool = False,
    pagination_complete: bool | None = None,
    index: int = 0,
) -> CapabilityProbeAttempt:
    start = datetime(_ERA_YEARS.get(era, 2026), 6, 15, tzinfo=UTC)
    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": f"p-{index}",
            "probe_run_id": "run_cov_001",
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
            "venue_market": "KRAKEN_FUTURES",
            "instrument_native": instrument,
            "canonical_asset_hint": "BTC",
            "requested_start": start,
            "requested_end": start,
            "requested_granularity": granularity,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "response_status_class": status,
            "error_class": error_class,
            "native_timestamp_fields": timestamp_fields or [],
            "native_units_summary": unit_summary or {},
            "request_fingerprint": fingerprint,
            "pagination_detected": pagination_detected,
            "pagination_complete": pagination_complete,
            "era_hint": era,
            "probe_version": "sensor-probe-v1",
        }
    )


def _full_matrix() -> list[CapabilityProbeAttempt]:
    """Verified sample at every era + recent control, full semantics."""
    return [
        make_attempt(era="2021", index=0, timestamp_fields=["t"], unit_summary={"q": "contracts"}, fingerprint="f"),
        make_attempt(era="2022", index=1, timestamp_fields=["t"], unit_summary={"q": "contracts"}, fingerprint="f"),
        make_attempt(era="2024", index=2, timestamp_fields=["t"], unit_summary={"q": "contracts"}, fingerprint="f"),
        make_attempt(era="2026", index=3, timestamp_fields=["t"], unit_summary={"q": "contracts"}, fingerprint="f"),
        make_attempt(era=RECENT, index=4, timestamp_fields=["t"], unit_summary={"q": "contracts"}, fingerprint="f"),
    ]


# ---------------------------------------------------------------------------
# T2-COV-01 — coverage vector
# ---------------------------------------------------------------------------


def test_coverage_vector_full_matrix_scores_1_historical():
    vector = compute_coverage_vector(
        _full_matrix(),
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        semantic_equivalence_class=SemanticEquivalence.EXACT_EQUIVALENT,
    )
    assert vector.H == 1.0
    assert vector.T == 0.75
    assert vector.N == 0.75
    assert vector.A == 1.0
    assert vector.R == 1.0
    assert vector.S == 1.0


def test_coverage_vector_recent_only_historical_quarter():
    vector = compute_coverage_vector(
        [make_attempt(era=RECENT, timestamp_fields=["t"])],
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
    )
    assert vector.H == 0.25


def test_coverage_vector_granularity_and_universe_fractions():
    attempts = [
        make_attempt(era=RECENT, granularity=Granularity.G5M, instrument="PI_XBTUSD", index=0),
        make_attempt(era=RECENT, granularity=Granularity.G1H, instrument="PI_ETHUSD", index=1),
    ]
    vector = compute_coverage_vector(
        attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        planned_granularities=(Granularity.G5M, Granularity.G1H, Granularity.G1D),
        planned_instruments=("PI_XBTUSD", "PI_ETHUSD", "PI_XRPUSD"),
    )
    assert vector.G == round(2 / 3, 4)
    assert vector.U == round(2 / 3, 4)


def test_coverage_vector_timestamp_unclear_zeroes_T():
    attempts = [
        make_attempt(
            era=RECENT,
            status=ResponseStatusClass.FAILED,
            error_class=ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
        )
    ]
    vector = compute_coverage_vector(
        attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
    )
    assert vector.T == 0.0


def test_coverage_vector_unit_unclear_zeroes_N():
    attempts = [
        make_attempt(
            era=RECENT,
            status=ResponseStatusClass.FAILED,
            error_class=ProbeFailureClass.F_UNIT_UNCLEAR,
        )
    ]
    vector = compute_coverage_vector(
        attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
    )
    assert vector.N == 0.0


def test_coverage_vector_paid_access_zeroes_A():
    vector = compute_coverage_vector(
        _full_matrix(),
        free_only_status=FreeOnlyStatus.PAID_BLOCKED,
    )
    assert vector.A == 0.0


def test_coverage_vector_pagination_failure_zeroes_P():
    attempts = [
        make_attempt(
            era=RECENT,
            status=ResponseStatusClass.FAILED,
            error_class=ProbeFailureClass.F_PAGINATION_LOOP,
        )
    ]
    vector = compute_coverage_vector(
        attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
    )
    assert vector.P == 0.0


def test_coverage_vector_unknown_access_is_never_promotable():
    vector = compute_coverage_vector(
        _full_matrix(),
        free_only_status=FreeOnlyStatus.UNVERIFIED,
    )
    assert vector.A == 0.5


# ---------------------------------------------------------------------------
# T2-COV-02 — hard blocker override is handled at scoring layer; coverage
# synthesis must carry the data needed to detect it
# ---------------------------------------------------------------------------


def test_synthesize_coverage_carries_unit_and_pit_and_era_status():
    attempts = _full_matrix()
    coverage = synthesize_coverage(
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="KRAKEN_FUTURES",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        semantic_equivalence_class=SemanticEquivalence.EXACT_EQUIVALENT,
        planned_granularities=(Granularity.G1D,),
        planned_instruments=("PI_XBTUSD",),
    )
    assert coverage.era_status["2021"] is CapabilityStatus.VERIFIED
    assert coverage.era_status[RECENT] is CapabilityStatus.VERIFIED
    assert coverage.earliest_verified_history == datetime(2021, 6, 15, tzinfo=UTC)
    assert coverage.unit_clarity == 0.75
    assert coverage.promotion_eligible is False  # fail-closed until scoring approves


def test_synthesize_coverage_pre_listing_era_stays_distinct():
    attempts = [
        make_attempt(
            era="2021",
            status=ResponseStatusClass.FAILED,
            error_class=ProbeFailureClass.F_PRE_LISTING,
            index=0,
        ),
        make_attempt(era=RECENT, index=1, timestamp_fields=["t"]),
    ]
    coverage = synthesize_coverage(
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="KRAKEN_FUTURES",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
    )
    assert coverage.era_status["2021"] is CapabilityStatus.UNVERIFIED  # PRE_LISTING
    assert coverage.era_status[RECENT] is CapabilityStatus.VERIFIED


# ---------------------------------------------------------------------------
# T2-COV-03/04/05 — redundancy counts independent venues only
# ---------------------------------------------------------------------------


def test_redundancy_r0_no_sources():
    summary = compute_sensor_redundancy(SensorFamily.MECHANICAL_LIQUIDATION, [])
    assert summary.redundancy_class is RedundancyClass.R0_NONE
    assert summary.gap_status == "UNVERIFIED"


def test_redundancy_r1_single_independent_venue():
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_LIQUIDATION,
        [
            VerifiedSource(
                provider_id="KRAKEN_FUTURES",
                venue_market="KRAKEN_FUTURES",
                evidence_class=EvidenceSourceClass.FIRST_PARTY_RUNTIME,
            )
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R1_SINGLE_INDEPENDENT
    assert summary.gap_status == "SINGLE_SOURCE"


def test_redundancy_r2_two_independent_venues():
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_LIQUIDATION,
        [
            VerifiedSource("K", "KRAKEN_FUTURES", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
            VerifiedSource("G", "GATE_FUTURES", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R2_TWO_INDEPENDENT
    assert summary.gap_status == "ADEQUATE"


def test_redundancy_two_aliases_of_one_venue_is_r1():
    # Binance REST + Binance archive are two acquisition paths, one venue
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_LIQUIDATION,
        [
            VerifiedSource("B-REST", "BINANCE_USDM", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
            VerifiedSource("B-ARCH", "BINANCE_USDM", EvidenceSourceClass.FIRST_PARTY_ARCHIVE),
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R1_SINGLE_INDEPENDENT
    assert summary.verified_venues == ["BINANCE_USDM"]


def test_redundancy_aggregator_never_counts_as_independent_venue():
    # Coinalyze reporting Binance does not add a venue alongside Binance itself
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_LIQUIDATION,
        [
            VerifiedSource("BINANCE_USDM", "BINANCE_USDM", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
            VerifiedSource(
                "COINALYZE",
                "COINALYZE",
                EvidenceSourceClass.THIRD_PARTY_AGGREGATOR,
            ),
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R1_SINGLE_INDEPENDENT
    assert summary.first_party_count == 1
    assert summary.aggregator_count == 1


def test_redundancy_community_archive_is_diversity_not_first_party():
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_LIQUIDATION,
        [
            VerifiedSource(
                "BITFINEX_COMMUNITY",
                "BITFINEX",
                EvidenceSourceClass.COMMUNITY_ARCHIVE,
            )
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R0_NONE
    assert summary.community_count == 1
    assert summary.first_party_count == 0
    assert summary.gap_status == "INSUFFICIENT"


def test_redundancy_r3_three_independent_venues():
    summary = compute_sensor_redundancy(
        SensorFamily.MECHANICAL_FUNDING,
        [
            VerifiedSource("K", "KRAKEN_FUTURES", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
            VerifiedSource("G", "GATE_FUTURES", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
            VerifiedSource("B", "BINANCE_USDM", EvidenceSourceClass.FIRST_PARTY_RUNTIME),
        ],
    )
    assert summary.redundancy_class is RedundancyClass.R3_THREE_PLUS_INDEPENDENT


def test_coverage_vector_model_bounds():
    with pytest.raises(ValueError):
        CoverageVector(
            H=1.5, G=0.0, U=0.0, P=0.0, T=0.0, N=0.0, A=0.0, R=0.0, S=0.0, Q=0.0
        )
