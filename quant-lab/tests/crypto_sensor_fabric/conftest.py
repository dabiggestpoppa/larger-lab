"""Shared test helpers for the crypto sensor fabric test tree.

All Bloc 1 tests are offline: they consume committed synthetic JSON fixtures
under `fixtures/` and never touch the network.  The loader lives in
`crypto_sensor_fabric.testing` so it is importable outside pytest contexts.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from crypto_sensor_fabric.testing import (
    FIXTURE_DIR,
    load_fixture_json,
    load_fixture_model,
)


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def load_fixture():
    return load_fixture_json


@pytest.fixture
def load_model():
    return load_fixture_model
