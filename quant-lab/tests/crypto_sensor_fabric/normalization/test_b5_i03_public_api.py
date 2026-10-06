"""SENSOR-B5-I03 - RED public-surface proof for the identity subpackage.

The identity package must expose exactly the 12 authorized symbols after
B5-I03 (the I02 ten + AliasType + InstrumentAlias), lose nothing, and leave
the ratified B5-I01 top-level surface untouched at exactly 24 symbols
(I03 directive 29; I02 ratification section 6).

RED protocol: the two I03A-era tests below are wired to fail while
AliasType/InstrumentAlias are absent; after B5-I03C the file becomes the
standing surface contract.  OFFLINE throughout.
"""

from __future__ import annotations

import importlib
import socket
import sys

import pytest

EXPECTED_IDENTITY = [
    "AliasType",
    "CanonicalAsset",
    "ContractInstance",
    "EconomicContract",
    "IdentityRegistrySnapshot",
    "IdentityResolution",
    "IdentityResolutionStatus",
    "InstrumentAlias",
    "InstrumentLifecycle",
    "LifecycleState",
    "SemanticToken",
    "Venue",
    "VenueInstrument",
    "parse_identity_registry_yaml",
    "resolve_instrument",
    "serialize_identity_registry_yaml",
    "validate_registry_succession",
]

EXPECTED_TOP_LEVEL_COUNT = 24


def test_identity_exports_exactly_the_authorized_symbols() -> None:
    """RED until B5-I03B/C lands the six new symbols."""
    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    assert sorted(identity.__all__) == EXPECTED_IDENTITY
    assert len(identity.__all__) == len(EXPECTED_IDENTITY)


def test_every_export_is_importable_and_real() -> None:
    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    for name in identity.__all__:
        assert getattr(identity, name) is not None, name


def test_private_helpers_do_not_leak() -> None:
    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    assert not [name for name in identity.__all__ if name.startswith("_")]
    for private in (
        "_reject_blank",
        "_require_unpadded",
        "_reject_path_shaped",
        "_EvidenceRef",
        "_SHA256_HEX_RE",
        "IdentityModelBase",
    ):
        assert not hasattr(identity, private), private


def test_b5_i04_plus_symbols_are_absent() -> None:
    """I03 directive 1/39/40/41 firewalls: conversion, time semantics,
    availability, revision policy, writer, canonical query, universe,
    fuzzy machinery - all must not exist at B5-I03."""
    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    for absent in (
        "ContractTermsSnapshot",
        "CanonicalObservation",
        "T1Writer",
        "T1WriterRegistry",
        "write_t1",
        "query_t1",
        "UniverseMembership",
        "convert_contract_value",
        "apply_multiplier",
        "AvailabilityPolicy",
        "ReplayEligibility",
        "RevisionPolicy",
        "TimeSemanticsRegistry",
        "MethodologyRegistry",
        "fuzzy_candidates",
        "fuzzy_match",
    ):
        assert not hasattr(identity, absent), absent


def test_top_level_normalization_surface_unchanged() -> None:
    """The ratified 24-symbol B5-I01 surface gains nothing from B5-I03
    (no top-level re-export, directive 29)."""
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    assert len(normalization.__all__) == EXPECTED_TOP_LEVEL_COUNT
    for name in ("resolve_instrument", "IdentityResolution", "InstrumentAlias"):
        assert name not in normalization.__all__


def test_importing_identity_makes_no_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero network at import time (I02 precedent, directive 1)."""
    calls: list[object] = []

    def _refuse(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("network access attempted during import")

    monkeypatch.setattr(socket, "socket", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)
    for module_name in list(sys.modules):
        if module_name.startswith("crypto_sensor_fabric.normalization"):
            monkeypatch.delitem(sys.modules, module_name, raising=False)
    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    assert identity.IdentityRegistrySnapshot is not None
    assert calls == []
