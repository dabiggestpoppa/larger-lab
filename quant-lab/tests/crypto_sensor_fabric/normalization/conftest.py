"""Per-directory pytest anchor for normalization tests.

Also hosts the Wave 1 (I12-I15) shared test support: a synthetic approval root and
the PIT terms/price factories the new sensor suites need.

**Every registry built here is SYNTHETIC TEST AUTHORITY.**  It exercises the
admission MECHANISM and certifies no provider: every row carries the label twice,
and no production registry row may be derived from it.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from crypto_sensor_fabric.contracts.enums import SemanticEquivalence, SensorFamily
from crypto_sensor_fabric.normalization.authority import load_semantic_authority
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodology,
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.common.semantic_registry import (
    IntervalDataScope,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    serialize_provider_semantic_registry_yaml,
)
from crypto_sensor_fabric.normalization.enums import IntervalTimeConvention, PayoffType
from crypto_sensor_fabric.normalization.terms.conversion import (
    ReferencePriceEvidence,
    ReferencePriceType,
)
from crypto_sensor_fabric.normalization.terms.snapshot import ContractTermsSnapshot

#: Marker repeated on every synthetic row so a fixture cannot be mistaken for
#: documentary evidence about a venue.
SYNTH = "SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION"

AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 3, 1, 13, 0, tzinfo=timezone.utc)
DIGEST = "a" * 64


def sint_row(
    provider_field: str,
    canonical_field: str,
    *,
    family: SensorFamily,
    provider: str = "BINANCE_USDM",
    confidence: SemanticConfidence = SemanticConfidence.VERIFIED_FIRST_PARTY,
    evidence: str | None = f"{SYNTH}:evidence",
    methodology: str | None = f"{SYNTH}_METHOD_V1",
    equivalence: SemanticEquivalence = SemanticEquivalence.EXACT_EQUIVALENT,
) -> ProviderSemanticMapping:
    """One synthetic registry row: it certifies the MECHANISM, not the venue."""
    return ProviderSemanticMapping(
        provider=provider,
        provider_field=provider_field,
        canonical_sensor=family,
        canonical_field=canonical_field,
        semantic_equivalence_class=equivalence,
        native_definition=f"{SYNTH}:{provider_field}",
        transformation=f"{SYNTH}:{provider_field}->{canonical_field}",
        methodology_id=methodology,
        blocking_assumptions=(f"{SYNTH}:certifies-nothing-in-production",),
        known_limitations=(f"{SYNTH}:fixture-only-authority",),
        source_endpoint_or_archive="synthetic://test-authority",
        data_type="SNAPSHOT",
        native_unit="ENUM",
        timestamp_meaning="OBSERVED_AT",
        interval_data_scope=IntervalDataScope.INTERVAL_LOCAL,
        direction_side_convention=f"{SYNTH}:{canonical_field}",
        evidence_reference=evidence,
        semantic_confidence=confidence,
        version="1",
    )


def sint_registry(
    rows: tuple[ProviderSemanticMapping, ...],
    *,
    version: str = "SYNTHETIC_TEST_REGISTRY_V1",
) -> ProviderSemanticRegistry:
    return ProviderSemanticRegistry(schema_version=version, mappings=tuple(rows))


def sint_authority(registry: ProviderSemanticRegistry):
    """A synthetic P2a approval root covering THIS registry."""
    artifact = serialize_provider_semantic_registry_yaml(registry).encode("utf-8")
    fields: dict[str, dict[str, list[str]]] = {}
    declared: dict[str, list[str]] = {}
    methods: list[str] = []
    assumptions: list[str] = []
    rows_by_identity: dict[tuple[str, str], ProviderSemanticMapping] = {}
    for row in registry.mappings:
        ref = row.evidence_reference or ""
        fields.setdefault(row.provider, {}).setdefault(row.provider_field, []).append(ref)
        declared.setdefault(row.provider, []).append(row.provider_field)
        if row.methodology_id is not None:
            if row.methodology_id not in methods:
                methods.append(row.methodology_id)
            rows_by_identity[(row.methodology_id, row.version)] = row
        for assumption in row.blocking_assumptions:
            if assumption not in assumptions:
                assumptions.append(assumption)
    manifest = json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "SYNTHETIC_TEST_TRUST_ROOT",
            "artifacts": {
                "synthetic-test-registry": {
                    "sha256": hashlib.sha256(artifact).hexdigest(),
                    "approval_id": "SYNTHETIC-TEST-APPROVAL-P2A",
                    "registry_schema_version": registry.schema_version,
                    "approved_at": "2026-11-06",
                    "valid_until": None,
                    "allowed_methodologies": methods,
                    "evidence": fields,
                    "declared_native_fields": declared,
                    "approved_transformations": {},
                    "resolved_blocking_assumptions": assumptions,
                }
            },
            "revoked_approval_ids": [],
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    methodologies = NormalizationMethodologyRegistry(
        schema_version="1",
        methodologies=tuple(
            NormalizationMethodology(
                methodology_id=row.methodology_id,
                version=row.version,
                sensor_family=row.canonical_sensor,
                description=f"{SYNTH}:synthetic methodology",
                formula_or_algorithm="preserve the declared native field",
                required_inputs=("native_field",),
                output_units=("ENUM",),
                PIT_requirements="no derivation; the field is read as declared",
                known_limitations=(f"{SYNTH}:fixture-only",),
                introduced_at="e2df7109b4ae336c2ed71f1cb8b56e2b4360874e",
            )
            for row in rows_by_identity.values()
        ),
    )
    return load_semantic_authority(
        manifest_bytes=manifest,
        artifact_id="synthetic-test-registry",
        artifact_bytes=artifact,
        methodology_registry=methodologies,
    )


def terms(
    *,
    payoff: PayoffType = PayoffType.LINEAR,
    multiplier: str = "0.001",
    inverse: bool = False,
    quantity_unit: str = "BTC",
    price_unit: str = "USDT",
    quote_asset: str = "USDT",
) -> ContractTermsSnapshot:
    return ContractTermsSnapshot(
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        economic_contract_id="ECON:BTCUSDT:PERP",
        contract_terms_version="terms-v1",
        contract_multiplier=Decimal(multiplier),
        multiplier_unit="CONTRACTS",
        price_unit=price_unit,
        quantity_unit=quantity_unit,
        payoff_type=payoff,
        inverse_flag=inverse,
        quanto_flag=False,
        quote_asset_id=quote_asset,
        settlement_asset_id=quote_asset,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.001"),
        source_evidence_refs=(f"{SYNTH}:terms",),
    )


def price(*, value: str = "61222", kind: ReferencePriceType = ReferencePriceType.PROVIDER_INDEX) -> ReferencePriceEvidence:
    return ReferencePriceEvidence(
        reference_price=Decimal(value),
        reference_price_type=kind,
        reference_price_time=AT,
        reference_price_source=f"{SYNTH}:price",
        market_available_at=AT,
        reference_price_unit="USDT",
        reference_price_base_unit="BTC",
        source_evidence_refs=(f"{SYNTH}:price-evidence",),
    )


@pytest.fixture()
def wave1():
    """The Wave 1 test support surface, as one namespace."""
    return SimpleNamespace(
        SYNTH=SYNTH,
        AT=AT,
        CUTOFF=CUTOFF,
        DIGEST=DIGEST,
        SensorFamily=SensorFamily,
        SemanticEquivalence=SemanticEquivalence,
        SemanticConfidence=SemanticConfidence,
        row=sint_row,
        registry=sint_registry,
        authority=sint_authority,
        terms=terms,
        price=price,
        PayoffType=PayoffType,
        ReferencePriceType=ReferencePriceType,
        interval_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    )
