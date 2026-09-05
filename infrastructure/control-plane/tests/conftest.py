"""OCE Control Plane test configuration (B2).

Registers the `container` marker (container-backed tests are mandatory in
CI and skip truthfully without Docker), provides fixtures for the control
plane with test-controlled clocks. No wall-clock sleeps in authoritative
tests.
"""
import sys
from pathlib import Path

import pytest

# Add src to path
SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from oce_control.clocks import TestClock, set_test_clock, reset_clock
from oce_control.plane import ControlPlane


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "container: test requires a real Docker/Compose runtime (mandatory in CI)",
    )


def docker_available():
    import shutil
    import subprocess
    if shutil.which("docker") is None:
        return False
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def pytest_collection_modifyitems(session, config, items):
    """Autoskip container-marked tests when Docker is absent (truthful skip)."""
    if docker_available():
        return
    for item in items:
        if item.get_closest_marker("container") is not None:
            item.add_marker(pytest.mark.skip(reason="container runtime unavailable (Docker absent)"))


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
