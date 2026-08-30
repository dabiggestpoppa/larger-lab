"""OCE Control Plane test configuration.

Provides fixtures for the control plane with test-controlled clocks.
No wall-clock sleeps in authoritative tests.
"""
import sys
from pathlib import Path

import pytest

# Add src to path
SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from oce_control.clocks import TestClock, set_test_clock, reset_clock
from oce_control.plane import ControlPlane


@pytest.fixture
def clock():
    """Fresh test clock for each test."""
    c = TestClock()
    set_test_clock(c)
    yield c
    reset_clock()


@pytest.fixture
def plane(clock):
    """Fresh control plane with test clock."""
    return ControlPlane(test_clock=clock)
