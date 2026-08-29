"""Shared test helpers for the crypto sensor fabric test tree.

All Bloc 1 tests are offline: they consume committed synthetic JSON fixtures
under `fixtures/` and never touch the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture_json(name: str) -> dict:
    """Load a committed synthetic fixture as a plain dict."""
    path = FIXTURE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture_model(model_cls: type, name: str):
    """Validate a fixture against a canonical model class."""
    return model_cls.model_validate(load_fixture_json(name))


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def load_fixture():
    return load_fixture_json


@pytest.fixture
def load_model():
    return load_fixture_model
