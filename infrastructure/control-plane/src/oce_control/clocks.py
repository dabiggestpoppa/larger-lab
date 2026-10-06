"""Test-controlled clock for deterministic time in the OCE control plane.

No authoritative test relies on wall-clock sleeps. All time-dependent logic
uses this clock so tests can advance time deterministically.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional


class TestClock:
    """A controllable clock for deterministic testing."""

    def __init__(self, initial: Optional[datetime] = None):
        self._now = initial or datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)

    def set(self, dt: datetime) -> None:
        self._now = dt

    def isoformat(self) -> str:
        return self._now.isoformat()


class WallClock:
    """The real wall clock. Used in production, never in authoritative tests."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def advance(self, seconds: float) -> None:
        raise NotImplementedError("WallClock cannot be advanced")

    def set(self, dt: datetime) -> None:
        raise NotImplementedError("WallClock cannot be set")

    def isoformat(self) -> str:
        return self.now().isoformat()


# Default clock for the process (tests override this)
_default_clock: Optional[TestClock] = None


def get_clock() -> TestClock:
    global _default_clock
    if _default_clock is None:
        _default_clock = TestClock()
    return _default_clock


def set_test_clock(clock: TestClock) -> None:
    global _default_clock
    _default_clock = clock


def reset_clock() -> None:
    global _default_clock
    _default_clock = None
