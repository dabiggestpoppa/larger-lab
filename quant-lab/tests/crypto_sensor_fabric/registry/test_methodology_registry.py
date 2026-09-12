"""Methodology registry tests (02 §16, versioning doctrine)."""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.registry.methodology_registry import (
    load_methodology_registry,
    require_methodology_id,
)

DEFAULT_METHODOLOGIES = load_methodology_registry()


def test_methodology_registry_loads():
    assert len(DEFAULT_METHODOLOGIES.methodologies) >= 5


def test_methodology_ids_unique_and_versioned():
    ids = list(DEFAULT_METHODOLOGIES.methodologies)
    assert len(ids) == len(set(ids))
    for entry in DEFAULT_METHODOLOGIES.methodologies.values():
        assert entry.description
        assert entry.version


def test_fixture_referenced_methodologies_registered():
    for methodology_id in (
        "OI_CONTRACTS_TO_USD_V1",
        "OI_USD_NATIVE_PASSTHROUGH_V1",
        "FUNDING_NATIVE_TO_8H_EQUIV_V1",
        "PROVIDER_ANALYTICS_PASSTHROUGH_V1",
        "DEPTH_BPS_RECONSTRUCTION_V1",
    ):
        assert methodology_id in DEFAULT_METHODOLOGIES.methodologies


def test_require_methodology_id_fails_closed():
    with pytest.raises(KeyError):
        require_methodology_id(DEFAULT_METHODOLOGIES, "NOT_A_REAL_METHOD_V99")


def test_require_methodology_id_ok():
    require_methodology_id(DEFAULT_METHODOLOGIES, "CVD_SIGNED_NOTIONAL_V1")


def test_all_methodologies_are_provisional():
    # Nothing may claim verified methodology semantics before Bloc 2/5 probes.
    for entry in DEFAULT_METHODOLOGIES.methodologies.values():
        assert entry.status == "PROVISIONAL"
