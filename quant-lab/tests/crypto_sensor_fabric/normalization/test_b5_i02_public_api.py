"""SENSOR-B5-I02 — public-surface proof for the identity subpackage.

The identity package exposes exactly its 10 authorized symbols, leaks no
private helper, and leaves the ratified B5-I01 top-level surface untouched at
exactly 24 symbols (directive §29).  OFFLINE: importing must not touch the
network.
"""

from __future__ import annotations

import importlib
import socket
import sys

import pytest

EXPECTED_IDENTITY = [
    # B5-I02 sealed ten, PLUS the six B5-I03 symbols reconciled in B5-I03C
    # (public-surface reconciliation is the authorized I02D-pattern edit;
    # the achievable-surface law lives in test_b5_i03_public_api.py now).
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
    import crypto_sensor_fabric.normalization.identity as identity

    assert sorted(identity.__all__) == EXPECTED_IDENTITY
    assert len(identity.__all__) == 17


def test_every_export_is_importable_and_real() -> None:
    import crypto_sensor_fabric.normalization.identity as identity

    for name in identity.__all__:
        assert getattr(identity, name) is not None, name


def test_private_helpers_do_not_leak() -> None:
    import crypto_sensor_fabric.normalization.identity as identity

    assert not [name for name in identity.__all__ if name.startswith("_")]
    for private in ("_reject_blank", "_require_unpadded", "_reject_path_shaped",
                    "_EvidenceRef", "_SHA256_HEX_RE", "IdentityModelBase"):
        assert not hasattr(identity, private), private


def test_b5_i04_plus_symbols_are_absent() -> None:
    """RECONCILED in B5-I03C: the six I03 symbols are now implemented and
    guarded by test_b5_i03_public_api.py.  This I02-era firewall keeps the
    B5-I04+ machinery (universe/terms/writer/query plus any lifecycle-state
    rename) absent from the package surface."""
    import crypto_sensor_fabric.normalization.identity as identity

    for absent in (
        "InstrumentLifecycleState",  # never renamed; LifecycleState is the frozen name
        "UniverseMembership",
        "ContractTermsSnapshot",
        "T1Writer",
        "T1WriterRegistry",
        "write_t1",
        "query_t1",
        "ScopeState",  # VenueScope remains deferred (I02 matrix decision)
        "VenueScope",
    ):
        assert not hasattr(identity, absent), absent


def test_top_level_normalization_surface_unchanged() -> None:
    """The ratified 24-symbol B5-I01 surface must not have gained or lost a
    symbol because of B5-I02 (no top-level re-export, directive §29)."""
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    assert len(normalization.__all__) == EXPECTED_TOP_LEVEL_COUNT
    for name in EXPECTED_IDENTITY:
        assert name not in normalization.__all__


def test_importing_identity_makes_no_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero network at import time (directive §24/§42)."""
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
