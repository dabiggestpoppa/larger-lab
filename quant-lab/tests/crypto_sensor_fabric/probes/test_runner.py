"""Runner lifecycle tests (T2-PLAN-02, T2-PAGE-01..03)."""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    Granularity,
    ProbeFailureClass,
    ProbeRunStatus,
    QueryMode,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import (
    CapabilityProbeAttempt,
    CapabilityProbeRequest,
)
from crypto_sensor_fabric.probes.planner import (
    ProbePlan,
    ProbePlanStep,
    ProbeTarget,
    load_historical_checkpoints,
    plan_probe_matrix,
)
from crypto_sensor_fabric.probes.runner import (
    analyze_cursor_sequence,
    run_plan,
)

CONFIG = load_historical_checkpoints()
RUN_ID = "run_test_runner"

TARGET = ProbeTarget(
    provider_id="KRAKEN_FUTURES",
    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
    venue_market="KRAKEN_FUTURES",
    instruments=("PI_XBTUSD",),
    asset_hints=("BTC",),
    granularities=(Granularity.G5M,),
    access_mode=AccessMode.PUBLIC_REST,
    query_mode=QueryMode.TIME_RANGE,
)


def _attempt_for(
    request: CapabilityProbeRequest,
    *,
    status: ResponseStatusClass = ResponseStatusClass.VERIFIED_SAMPLE,
    error_class: ProbeFailureClass | None = None,
) -> CapabilityProbeAttempt:
    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": "probe-1",
            "probe_run_id": RUN_ID,
            "provider_id": request.provider_id,
            "sensor_family": request.sensor_family,
            "venue_market": request.venue_market,
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": request.access_mode,
            "query_mode": request.query_mode,
            "response_status_class": status,
            "error_class": error_class,
            "probe_version": "sensor-probe-v1",
        }
    )


class ScriptedExecutor:
    """Executor driven by a per-(era) script for deterministic tests."""

    def __init__(self, script: dict[str, tuple[ResponseStatusClass, ProbeFailureClass | None]]):
        self.script = script
        self.calls: list[CapabilityProbeRequest] = []

    def execute(self, request: CapabilityProbeRequest) -> list[CapabilityProbeAttempt]:
        self.calls.append(request)
        status, error = self.script.get(request.era_hint, (ResponseStatusClass.VERIFIED_SAMPLE, None))
        return [_attempt_for(request, status=status, error_class=error)]


def test_t2_plan_02_recent_control_hard_block_suppresses_history():
    plan = plan_probe_matrix(TARGET, RUN_ID, CONFIG)
    # hard-block the recent control; historical steps must be skipped
    executor = ScriptedExecutor(
        {"RECENT_CONTROL": (ResponseStatusClass.FAILED, ProbeFailureClass.F_ACCESS_PAYMENT)}
    )
    result = run_plan(plan, executor, RUN_ID, "sensor-probe-v1")
    assert result.run_status == ProbeRunStatus.ABORTED_HARD_BLOCK
    assert len(result.planned_but_skipped) == len(plan.historical_steps())
    # every executed request was a recent control
    executed_eras = {req.era_hint for req in executor.calls}
    assert executed_eras == {"RECENT_CONTROL"}


def test_t2_plan_02_recent_control_success_proceeds_to_history():
    plan = plan_probe_matrix(TARGET, RUN_ID, CONFIG)
    executor = ScriptedExecutor(
        {"RECENT_CONTROL": (ResponseStatusClass.VERIFIED_SAMPLE, None)}
    )
    result = run_plan(plan, executor, RUN_ID, "sensor-probe-v1")
    assert result.run_status == ProbeRunStatus.COMPLETE
    assert len(result.attempts) == len(plan.steps)
    assert result.planned_but_skipped == []


def test_retryable_failure_is_retried_once():
    request = plan_probe_matrix(TARGET, RUN_ID, CONFIG).steps[0].request

    class RetryExecutor:
        def __init__(self):
            self.calls = 0

        def execute(self, req):
            self.calls += 1
            if self.calls == 1:
                return [
                    _attempt_for(
                        req,
                        status=ResponseStatusClass.FAILED,
                        error_class=ProbeFailureClass.F_NETWORK_TIMEOUT,
                    )
                ]
            return [_attempt_for(req)]

    executor = RetryExecutor()
    result = run_plan(
        ProbePlan(steps=[ProbePlanStep(era="RECENT_CONTROL", order=0, request=request)]),
        executor,
        RUN_ID,
        "sensor-probe-v1",
        retry_count=1,
    )
    assert executor.calls == 2
    assert result.run_status == ProbeRunStatus.COMPLETE


def test_hard_block_never_retried():
    request = plan_probe_matrix(TARGET, RUN_ID, CONFIG).steps[0].request

    class NoRetryExecutor:
        def __init__(self):
            self.calls = 0

        def execute(self, req):
            self.calls += 1
            return [
                _attempt_for(
                    req,
                    status=ResponseStatusClass.FAILED,
                    error_class=ProbeFailureClass.F_ACCESS_PAYMENT,
                )
            ]

    executor = NoRetryExecutor()
    result = run_plan(
        ProbePlan(steps=[ProbePlanStep(era="RECENT_CONTROL", order=0, request=request)]),
        executor,
        RUN_ID,
        "sensor-probe-v1",
        retry_count=3,
    )
    assert executor.calls == 1
    assert result.run_status == ProbeRunStatus.ABORTED_HARD_BLOCK


# ---------------------------------------------------------------------------
# T2-PAGE-01..03 — cursor pagination analysis
# ---------------------------------------------------------------------------


def test_t2_page_01_cursor_pagination_terminates():
    complete, terminated = analyze_cursor_sequence(["c1", "c2", None])
    assert not complete
    assert terminated is True


def test_t2_page_02_repeated_cursor_is_loop():
    complete, terminated = analyze_cursor_sequence(["c1", "c2", "c1", "c2"])
    assert complete is True  # loop detected
    assert terminated is False


def test_t2_page_02_loop_detected_with_duplicate():
    complete, _ = analyze_cursor_sequence(["a", "b", "b"])
    assert complete is True


def test_t2_page_03_truncated_history_detected():
    complete, terminated = analyze_cursor_sequence(["c1", "c2", "c3"])
    assert complete is False
    assert terminated is False  # non-null trailing cursor: more pages exist


def test_t2_page_03_empty_sequence_unknown():
    complete, terminated = analyze_cursor_sequence([])
    assert complete is False
    assert terminated is None
