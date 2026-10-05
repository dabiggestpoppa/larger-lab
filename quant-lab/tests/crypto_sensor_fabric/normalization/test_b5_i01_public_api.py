"""SENSOR-B5-I01C — public export surface of the Bloc 5 normalization base layer.

A base layer that exports everything exports nothing: every public name is a
promise to keep it.  This module pins the deliberate surface exactly, proves
that private helpers stay private, and proves that the names a consumer is most
likely to reach for -- the frozen ``T1ObservationEnvelope`` and the identity /
replay / conversion objects owned by later checkpoints -- are NOT importable
from this package at all.

OFFLINE.  ``network_calls = 0``.
"""

from __future__ import annotations

import importlib

import pytest

#: The complete, deliberate B5-I01 public contract.
DOCUMENTED_PUBLIC_API = frozenset(
    {
        # frozen vocabularies
        "AvailabilityBasis",
        "IntervalTimeConvention",
        "LineageState",
        "MissingnessReason",
        "NormalizationQualityFlag",
        "NormalizationStatus",
        "PayoffType",
        "QuarantineReason",
        "QualityDimensionState",
        "TimestampPrecision",
        # frozen read-only correspondences
        "BLOCKED_STATUS_MISSINGNESS_REASON",
        "BLOCKING_QUALITY_FLAGS",
        # validated opaque identifier types
        "ContractInstanceId",
        "OpaqueIdentifier",
        "RegistryVersion",
        "T1GenerationId",
        "T1RecordId",
        # base models
        "NativeQuantity",
        "ObservationTimeEnvelope",
        "T1BaseEnvelope",
        "T1LineageRef",
        "T1Quality",
        "T1VersionContext",
        # serialization
        "canonical_json_bytes",
    }
)


def test_all_is_exactly_the_documented_surface() -> None:
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    assert set(normalization.__all__) == set(DOCUMENTED_PUBLIC_API)
    assert len(normalization.__all__) == len(set(normalization.__all__)), "duplicate export"


@pytest.mark.parametrize("name", sorted(DOCUMENTED_PUBLIC_API))
def test_every_documented_symbol_imports_from_the_package(name: str) -> None:
    """The documented import path is the package, not a private submodule."""
    module = importlib.import_module("crypto_sensor_fabric.normalization")
    assert hasattr(module, name), f"{name} is exported but not importable"


def test_documented_types_are_the_real_objects() -> None:
    from crypto_sensor_fabric.normalization import (
        AvailabilityBasis,
        IntervalTimeConvention,
        LineageState,
        MissingnessReason,
        NativeQuantity,
        NormalizationQualityFlag,
        NormalizationStatus,
        ObservationTimeEnvelope,
        PayoffType,
        QuarantineReason,
        QualityDimensionState,
        T1BaseEnvelope,
        T1LineageRef,
        T1Quality,
        T1VersionContext,
        TimestampPrecision,
    )

    for enum_cls in (
        NormalizationStatus,
        MissingnessReason,
        NormalizationQualityFlag,
        PayoffType,
        QualityDimensionState,
        QuarantineReason,
        IntervalTimeConvention,
        AvailabilityBasis,
        TimestampPrecision,
        LineageState,
    ):
        assert issubclass(enum_cls, __import__("enum").Enum)

    from pydantic import BaseModel

    for model in (
        ObservationTimeEnvelope,
        NativeQuantity,
        T1Quality,
        T1LineageRef,
        T1VersionContext,
        T1BaseEnvelope,
    ):
        assert issubclass(model, BaseModel)
        assert model.model_config.get("extra") == "forbid"


@pytest.mark.parametrize(
    "name",
    [
        # private helpers and bases must stay private
        "NormalizationModelBase",
        "_StrEnum",
        "_FLAG_ORDER",
        "_SHA256_HEX_RE",
        "_OpaqueString",
        # the frozen full-envelope name is not exported until the composite exists
        "T1ObservationEnvelope",
        "T1Lineage",
        "T1Generation",
        # later-checkpoint objects must not be importable from here
        "CanonicalAsset",
        "Venue",
        "VenueInstrument",
        "EconomicContract",
        "ContractInstance",
        "InstrumentAlias",
        "InstrumentLifecycleState",
        "IdentityResolution",
        "IdentityResolutionStatus",
        "AliasType",
        "UniverseMembership",
        "VenueScope",
        "AvailabilityConfidence",
        "AvailabilityResolution",
        "TimeSemantics",
        "ReplayEligibility",
        "T1RevisionStatus",
        "T1RevisionChain",
        "DedupeStrength",
        "DuplicateOutcomeClass",
        "CanonicalQuantity",
        "ConversionRateObservation",
        "ReferencePriceType",
        "SemanticConfidence",
        "ProviderSemanticMapping",
        "NormalizationMethodology",
        "FieldLineage",
        "ConversionLineage",
        "T1PartitionManifest",
        # behavior that does not exist at I01
        "resolve_instrument",
        "derive_market_available_at",
        "query_t1",
        "convert",
    ],
)
def test_absent_names_are_absent(name: str) -> None:
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    assert not hasattr(normalization, name), f"{name} must not exist at B5-I01"
    assert name not in normalization.__all__


def test_no_behaviour_functions_are_exported() -> None:
    """Only types, frozen data and one serialization helper may be public.

    A callable that does work would be behavior; the single callable here is
    ``canonical_json_bytes``, which only serializes and never interprets.
    """
    import inspect

    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    functions = []
    for name in normalization.__all__:
        member = getattr(normalization, name)
        if inspect.isfunction(member):
            functions.append(name)
    assert functions == ["canonical_json_bytes"]


def test_upstream_vocabularies_are_imported_from_their_accepted_homes() -> None:
    """§17: consumed where they already live, never re-exported as new contract."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.probes.enums import Granularity
    from crypto_sensor_fabric.storage import (
        CoverageState,
        RevisionState,
        SourceUnitContract,
        SourceUnitEvidence,
        SourceUnitState,
        SourceUnitVariability,
    )

    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    for upstream in (
        SensorFamily,
        Granularity,
        CoverageState,
        RevisionState,
        SourceUnitState,
        SourceUnitVariability,
        SourceUnitContract,
        SourceUnitEvidence,
    ):
        assert upstream.__name__ not in normalization.__all__


def test_package_docstring_states_what_is_absent() -> None:
    """The boundary must be readable from the package, not only from tests."""
    doc = importlib.import_module("crypto_sensor_fabric.normalization").__doc__ or ""
    for absent in (
        "registry",
        "resolver",
        "conversion",
        "normalizer",
        "canonical query",
        "network",
    ):
        assert absent in doc, f"package docstring must name the absent {absent}"
    assert "T1ObservationEnvelope" in doc


def test_models_module_also_declares_a_narrow_all() -> None:
    """``models.__all__`` must not become a wider accidental contract."""
    from crypto_sensor_fabric.normalization import models

    assert set(models.__all__) == {
        "ContractInstanceId",
        "NativeQuantity",
        "NormalizationModelBase",
        "ObservationTimeEnvelope",
        "OpaqueIdentifier",
        "RegistryVersion",
        "T1BaseEnvelope",
        "T1GenerationId",
        "T1LineageRef",
        "T1Quality",
        "T1RecordId",
        "T1VersionContext",
        "canonical_json_bytes",
    }


def test_enums_module_exports_exactly_its_public_vocabularies() -> None:
    from crypto_sensor_fabric.normalization import enums

    assert set(enums.__all__) == DOCUMENTED_PUBLIC_API & {
        "AvailabilityBasis",
        "IntervalTimeConvention",
        "LineageState",
        "MissingnessReason",
        "NormalizationQualityFlag",
        "NormalizationStatus",
        "PayoffType",
        "QuarantineReason",
        "QualityDimensionState",
        "TimestampPrecision",
        "BLOCKED_STATUS_MISSINGNESS_REASON",
        "BLOCKING_QUALITY_FLAGS",
    }
    # The private ordering table stays private even though the model uses it.
    assert "_FLAG_ORDER" not in enums.__all__