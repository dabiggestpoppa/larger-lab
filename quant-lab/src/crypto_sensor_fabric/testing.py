"""Offline test-support helpers (fixture loading).

Bloc 1 unit tests are network-free by contract: they consume committed
synthetic fixtures under `quant-lab/tests/crypto_sensor_fabric/fixtures/`.
This module keeps that loader importable from anywhere in the repo (including
from within the package itself, e.g. versioning tests).

This module is test-support code, not part of the runtime contract surface.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from ._paths import QUANT_LAB_ROOT

FIXTURE_DIR = QUANT_LAB_ROOT / "tests" / "crypto_sensor_fabric" / "fixtures"


def load_fixture_json(name: str) -> dict:
    """Load a committed synthetic fixture as a plain dict."""
    path = FIXTURE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture_model(model_cls: type[BaseModel], name: str) -> BaseModel:
    """Validate a fixture against a canonical model class."""
    return model_cls.model_validate(load_fixture_json(name))
