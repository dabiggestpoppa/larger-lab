"""Planner tests (T2-HIST-01..05, T2-PLAN-01..05)."""

from __future__ import annotations

from datetime import UTC, datetime

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import AccessMode, Granularity, QueryMode
from crypto_sensor_fabric.probes.models import CapabilityProbeRequest
from crypto_sensor_fabric.probes.planner import (
    RECENT_CONTROL_ERA,
    ProbePlan,
    ProbeTarget,
    build_probe_request,
    load_historical_checkpoints,
    plan_earliest_history_search,
    plan_probe_matrix,
    recent_control_date,
)

CONFIG = load_historical_checkpoints()
RUN_ID = "run_test_001"

DEFAULT_TARGET = ProbeTarget(
    provider_id="KRAKEN_FUTURES",
    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
    venue_market="KRAKEN_FUTURES",
    instruments=("PI_XBTUSD",),
    asset_hints=("BTC",),
    granularities=(Granularity.G5M,),
    access_mode=AccessMode.PUBLIC_REST,
    query_mode=QueryMode.TIME_RANGE,
)


# ---------------------------------------------------------------------------
# T2-HIST-01 — checkpoint config completeness
# ---------------------------------------------------------------------------


def test_t2_hist_01_checkpoint_config_contains_mandatory_eras():
    names = CONFIG.era_names()
    assert "2021" in names
    assert "2022" in names
    assert "2024" in names
    assert "2026" in names
    assert RECENT_CONTROL_ERA in names


def test_t2_hist_01_checkpoint_dates_frozen():
    by_name = {era.name: era.checkpoint_date for era in CONFIG.eras}
    assert by_name["2021"] == datetime(2021, 6, 15, tzinfo=UTC)
    assert by_name["2022"] == datetime(2022, 6, 15, tzinfo=UTC)
    assert by_name["2024"] == datetime(2024, 6, 15, tzinfo=UTC)
    assert by_name["2026"] == datetime(2026, 6, 15, tzinfo=UTC)


# ---------------------------------------------------------------------------
# T2-PLAN-01 — recent control first
# ---------------------------------------------------------------------------


def test_t2_plan_01_recent_control_first():
    plan = plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG)
    assert plan.steps[0].era == RECENT_CONTROL_ERA
    recent = plan.recent_control_steps()
    historical = plan.historical_steps()
    assert recent and historical
    # every recent step precedes every historical step
    for recent_step in recent:
        for hist_step in historical:
            assert recent_step.order < hist_step.order


def test_t2_plan_01_recent_control_is_today():
    plan = plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG)
    fixed_now = datetime(2026, 8, 29, tzinfo=UTC)
    assert recent_control_date(fixed_now) == datetime(2026, 8, 29, tzinfo=UTC)
    windowed = plan.steps[0].request
    assert windowed.requested_start.date() <= recent_control_date().date()
    assert windowed.era_hint == RECENT_CONTROL_ERA
    # each historical era stamps its own label
    assert {s.era for s in plan.historical_steps()} == {"2021", "2022", "2024", "2026"}
    assert {s.request.era_hint for s in plan.historical_steps()} == {
        "2021",
        "2022",
        "2024",
        "2026",
    }


# ---------------------------------------------------------------------------
# T2-PLAN-04 — unsupported granularity never generates requests
# ---------------------------------------------------------------------------


def test_t2_plan_04_unsupported_granularity_suppressed():
    target = ProbeTarget(
        provider_id="DERIBIT",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="DERIBIT",
        instruments=("BTC-PERPETUAL",),
        asset_hints=("BTC",),
        granularities=(Granularity.G5M, Granularity.G1H),
        access_mode=AccessMode.PUBLIC_REST,
        query_mode=QueryMode.SEQUENCE,
        supported_granularities=frozenset({Granularity.G1H}),
    )
    plan = plan_probe_matrix(target, RUN_ID, CONFIG)
    granularities = {step.request.requested_granularity for step in plan.steps}
    assert granularities == {Granularity.G1H}


# ---------------------------------------------------------------------------
# T2-PLAN-05 — deterministic planning
# ---------------------------------------------------------------------------


def test_t2_plan_05_plan_is_deterministic():
    first = plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG)
    second = plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG)
    assert [
        (s.era, s.request.instrument_native, s.request.requested_granularity.value)
        for s in first.steps
    ] == [
        (s.era, s.request.instrument_native, s.request.requested_granularity.value)
        for s in second.steps
    ]


# ---------------------------------------------------------------------------
# T2-PLAN-03 — bounded earliest-history search
# ---------------------------------------------------------------------------


def test_t2_plan_03_boundary_search_bounded_and_month_precise():
    probes = plan_earliest_history_search(
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="KRAKEN_FUTURES",
        instrument_native="PI_XBTUSD",
        canonical_asset_hint="BTC",
        granularity=Granularity.G1D,
        access_mode=AccessMode.PUBLIC_REST,
        query_mode=QueryMode.TIME_RANGE,
        probe_run_id=RUN_ID,
        config=CONFIG,
        era_successes={"2021": True, "2022": True, "2024": False, "2026": False},
    )
    assert len(probes) <= CONFIG.boundary_max_probes()
    # probes step by ~month between the newest success (2022) and oldest fail (2024)
    if probes:
        for request in probes:
            assert request.requested_start >= datetime(2022, 6, 15, tzinfo=UTC)
            assert request.requested_start <= datetime(2024, 6, 15, tzinfo=UTC)


def test_t2_plan_03_no_success_means_no_search():
    probes = plan_earliest_history_search(
        provider_id="X",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="X",
        instrument_native="X",
        canonical_asset_hint=None,
        granularity=Granularity.G1D,
        access_mode=AccessMode.PUBLIC_REST,
        query_mode=QueryMode.TIME_RANGE,
        probe_run_id=RUN_ID,
        config=CONFIG,
        era_successes={"2021": False, "2022": False, "2024": False, "2026": False},
    )
    assert probes == []


# ---------------------------------------------------------------------------
# T2-HIST-02 .. T2-HIST-05 — pre-listing / current-only / boundary separation
# ---------------------------------------------------------------------------


def test_t2_hist_02_pre_listing_is_distinct_state():
    # PRE_LISTING is an instrument state, never a provider failure:
    # proven at the failure-taxonomy level and preserved in probe plans as a
    # legitimate era outcome (see test_failures).
    from crypto_sensor_fabric.probes.enums import (
        CapabilityMissingness,
        ProbeFailureClass,
    )
    from crypto_sensor_fabric.probes.failures import failure_to_missingness

    assert failure_to_missingness(ProbeFailureClass.F_PRE_LISTING) is (
        CapabilityMissingness.PRE_LISTING
    )


def test_t2_hist_03_current_only_never_unsupported():
    # Covered in depth by claim-synthesis tests (I03); the planner itself never
    # labels a failed era UNSUPPORTED — that decision belongs to evidence
    # synthesis.  Here we assert the planner emits plain attempts.
    plan = plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG)
    assert len(plan.historical_steps()) == 4 * len(DEFAULT_TARGET.instruments)


def test_t2_hist_04_05_claimed_vs_verified_separation():
    from crypto_sensor_fabric.probes.models import CapabilityClaim

    claim = CapabilityClaim.model_validate(
        {
            "claim_id": "c1",
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": "MECHANICAL_OPEN_INTEREST",
            "venue_market": "KRAKEN_FUTURES",
            "access_mode": "PUBLIC_REST",
            "earliest_claimed_history": "2019-01-01T00:00:00Z",
            "earliest_verified_history": "2021-06-15T00:00:00Z",
            "latest_verified_history": "2026-06-15T00:00:00Z",
        }
    )
    # claimed and verified are separate fields; verified never exceeds evidence
    assert claim.earliest_claimed_history == datetime(2019, 1, 1, tzinfo=UTC)
    assert claim.earliest_verified_history == datetime(2021, 6, 15, tzinfo=UTC)
    assert claim.earliest_claimed_history < claim.earliest_verified_history


def test_probe_request_window_by_granularity():
    request = build_probe_request(
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        venue_market="K",
        instrument_native="I",
        canonical_asset_hint="BTC",
        checkpoint_date=datetime(2022, 6, 15, tzinfo=UTC),
        granularity=Granularity.G1D,
        access_mode=AccessMode.PUBLIC_REST,
        query_mode=QueryMode.TIME_RANGE,
        probe_run_id=RUN_ID,
        config=CONFIG,
        era="2022",
    )
    assert (request.requested_end - request.requested_start).days == 30
    assert request.era_hint == "2022"
    assert isinstance(request, CapabilityProbeRequest)
    assert isinstance(plan_probe_matrix(DEFAULT_TARGET, RUN_ID, CONFIG), ProbePlan)
