"""SENSOR-B5-I05 - RED-first interval topology and completion law.

Frozen authority: bloc_05/02 s7 (declared boundary conventions), s6
(``market_available_at >= interval_end_at``, never the start), s18 invariant 2
(no completed interval available before its close), bloc_05/06 s1 G2, and the
F05-01 acceptance scenario.

Both boundary conventions are exercised at their exact edges -- equality,
one tick inside, one tick outside -- because the whole point of s7 is that
``12:00`` cannot be assumed to start or end a window.  ``PROVIDER_NATIVE_UNKNOWN``
must make membership UNDECIDABLE rather than defaulting to either side.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from crypto_sensor_fabric.normalization.enums import IntervalTimeConvention
from crypto_sensor_fabric.normalization.models import ObservationTimeEnvelope
from crypto_sensor_fabric.normalization.time import (
    IntervalWindow,
    UndecidableIntervalBoundary,
    earliest_justified_availability_from,
)

UTC = timezone.utc

START = datetime(2024, 6, 1, hour=12, minute=0, tzinfo=UTC)
END = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
TICK = timedelta(microseconds=1)


def _window(
    convention: IntervalTimeConvention = IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    *,
    start: datetime = START,
    end: datetime = END,
    closed: bool = True,
) -> IntervalWindow:
    return IntervalWindow(
        interval_start_at=start,
        interval_end_at=end,
        interval_closed=closed,
        interval_time_convention=convention,
    )


# ---------------------------------------------------------------------------
# Boundary membership, exactly at the edges
# ---------------------------------------------------------------------------


def test_left_closed_right_open_membership() -> None:
    window = _window()
    assert window.contains(START) is True
    assert window.contains(START - TICK) is False
    assert window.contains(END - TICK) is True
    assert window.contains(END) is False
    assert window.contains(END + TICK) is False


def test_left_open_right_closed_membership() -> None:
    window = _window(IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED)
    assert window.contains(START) is False
    assert window.contains(START - TICK) is False
    assert window.contains(START + TICK) is True
    assert window.contains(END) is True
    assert window.contains(END + TICK) is False


def test_point_sample_membership_is_a_single_instant() -> None:
    window = _window(
        IntervalTimeConvention.POINT_SAMPLE, end=START
    )
    assert window.contains(START) is True
    assert window.contains(START - TICK) is False
    assert window.contains(START + TICK) is False


def test_provider_native_unknown_is_undecidable_not_guessed() -> None:
    """bloc_05/02 s7: never guess which side a boundary lies on."""
    window = _window(IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN)
    with pytest.raises(UndecidableIntervalBoundary):
        window.contains(START)


def test_point_sample_with_a_real_span_is_refused() -> None:
    """A point sample that is secretly a window is a semantic contradiction."""
    with pytest.raises(ValueError):
        _window(IntervalTimeConvention.POINT_SAMPLE, end=END)


def test_inverted_interval_is_refused() -> None:
    with pytest.raises(ValueError):
        _window(start=END, end=START)


def test_zero_length_interval_is_legal_only_for_point_samples() -> None:
    zero = _window(IntervalTimeConvention.POINT_SAMPLE, end=START)
    assert zero.interval_start_at == zero.interval_end_at
    with pytest.raises(ValueError):
        _window(IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN, end=START)


# ---------------------------------------------------------------------------
# The completion law
# ---------------------------------------------------------------------------


def test_completed_interval_is_available_at_its_close_not_its_start() -> None:
    """F05-01: a start-stamped 5m bar is not fully available at its start."""
    window = _window()
    earliest = window.earliest_justified_availability()
    assert earliest == END
    assert earliest > START
    assert earliest >= window.interval_end_at


def test_completion_law_holds_for_both_ordered_conventions() -> None:
    for convention in (
        IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED,
    ):
        earliest = _window(convention).earliest_justified_availability()
        assert earliest == END, convention


def test_point_sample_is_available_at_its_instant() -> None:
    window = _window(IntervalTimeConvention.POINT_SAMPLE, end=START)
    assert window.earliest_justified_availability() == START


def test_unclosed_interval_cannot_claim_completion() -> None:
    """An open/live window has no justified close (s18.2)."""
    window = _window(closed=False)
    with pytest.raises(ValueError):
        window.earliest_justified_availability()


def test_unknown_convention_cannot_claim_completion() -> None:
    window = _window(IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN)
    with pytest.raises(UndecidableIntervalBoundary):
        window.earliest_justified_availability()


def test_completion_never_uses_the_start_for_any_declared_convention() -> None:
    for convention in (
        IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED,
    ):
        window = _window(convention)
        assert window.earliest_justified_availability() != START, convention


# ---------------------------------------------------------------------------
# Integration with the ratified B5-I01 envelope (consumed, never modified)
# ---------------------------------------------------------------------------


def test_envelope_derivation_reuses_the_declared_declaration() -> None:
    envelope = ObservationTimeEnvelope(
        interval_start_at=START,
        interval_end_at=END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    )
    assert earliest_justified_availability_from(envelope) == END


def test_envelope_without_a_declared_convention_is_refused_upstream() -> None:
    """s7 is enforced at the I01 envelope itself: such an object cannot exist.

    The I05 reader repeats the guard defensively, but the ratifiable path is
    that construction already fails -- an envelope with bounds and no declared
    convention is never representable, so no consumer can be handed one.
    """
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(interval_start_at=START, interval_end_at=END)


def test_envelope_without_an_explicit_closure_flag_is_refused_upstream() -> None:
    """s7: ``interval_closed`` is a declaration, and None is not one."""
    with pytest.raises(ValueError):
        ObservationTimeEnvelope(
            interval_start_at=START,
            interval_end_at=END,
            interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        )


def test_an_envelope_without_bounds_cannot_claim_a_completion_time() -> None:
    with pytest.raises(ValueError):
        earliest_justified_availability_from(ObservationTimeEnvelope())


def test_derivation_does_not_mutate_the_source_envelope() -> None:
    """Source non-mutation: the I01 envelope is consumed, never written."""
    envelope = ObservationTimeEnvelope(
        interval_start_at=START,
        interval_end_at=END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        ingested_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    before = envelope.model_dump()
    earliest_justified_availability_from(envelope)
    assert envelope.model_dump() == before
    assert envelope.interval_start_at == START
    assert envelope.ingested_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_interval_window_is_immutable() -> None:
    window = _window()
    with pytest.raises(Exception):
        window.interval_end_at = END + timedelta(minutes=1)  # type: ignore[misc]


def test_interval_declaration_fields_are_explicit_never_defaulted() -> None:
    with pytest.raises(ValueError):
        IntervalWindow(
            interval_start_at=START,
            interval_end_at=END,
            interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        )  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        IntervalWindow(
            interval_start_at=START,
            interval_end_at=END,
            interval_closed=True,
        )  # type: ignore[call-arg]
