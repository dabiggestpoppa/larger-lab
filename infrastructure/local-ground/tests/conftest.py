"""OCE Local Ground test configuration.

Registers the `container` marker (container-backed tests are mandatory in CI
and skip truthfully without Docker) and loads the OCE summary plugin that
writes a deterministic machine-readable test registry.
"""
import os
import shutil

import pytest

pytest_plugins = ["plugin_oce_summary"]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "container: test requires a real Docker/Compose runtime (mandatory in CI)",
    )


def docker_available():
    if shutil.which("docker") is None:
        return False
    import subprocess
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def pytest_collection_modifyitems(session, config, items):
    """Autoskip container-marked tests when Docker is absent (truthful skip)."""
    if docker_available():
        return
    for item in items:
        if item.get_closest_marker("container") is not None:
            item.add_marker(pytest.mark.skip(reason="container runtime unavailable (Docker absent)"))