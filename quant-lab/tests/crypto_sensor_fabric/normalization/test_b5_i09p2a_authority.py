"""SENSOR-B5-I09P2A - trusted semantic-authority suite (fail-closed boundary).

Implements the twenty mandatory probes of
``BLOC_05_I09P1_ADVERSARIAL_TEST_CONTRACT.md`` plus the seven G1-G7
reproductions, against the REAL production surface -- not a simulation.

**Every approval built here is SYNTHETIC TEST AUTHORITY.**  The manifest below is
a *test* trust root: it lives in this file, never in the shipping manifest, and
no production registry row may be derived from it.  The tests prove the MECHANISM
(approved bytes admit; everything else refuses) and certify no venue.

Two actors are kept apart in the fixtures, because the whole finding was that one
actor could be both:

* :func:`_artifact_bytes` -- the untrusted author's bytes;
* :func:`_manifest_bytes` -- the trusted approver's decision about them.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_sensor_fabric.contracts.enums import (
    AggressorSide,
    SemanticEquivalence,
    SensorFamily,
)
from crypto_sensor_fabric.normalization.authority import (
    AuthorityRefusal,
    SemanticAuthority,
    SemanticAuthorityRefusal,
    load_semantic_authority,
)
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodology,
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.common.semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    IntervalDataScope,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    parse_provider_semantic_registry_yaml,
    serialize_provider_semantic_registry_yaml,
)
from crypto_sensor_fabric.normalization.enums import NormalizationStatus
from crypto_sensor_fabric.normalization.sensors import (
    LiquidationAdmissionRefusal,
    LiquidationAggregationScope,
    LiquidationCanonicalField,
    LiquidationObservationInput,
    LiquidationPositionSide,
    LiquidationSideAdmission,
    T1LiquidationRecord,
    SideEvidence,
    T1TradeRecord,
    TradeObservationInput,
    normalize_liquidation,
    normalize_trade,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_QUANT_LAB = Path(__file__).resolve().parents[3]
_PROVIDER = "BINANCE_USDM"
_LABEL = "SYNTHETIC_P2A_TRUST_ROOT_NOT_PROVIDER_DOCUMENTATION"
_METHOD = "SYNTHETIC_P2A_METHOD_V1"
_SCHEMA = "SYNTHETIC_P2A_REGISTRY_V1"
_ARTIFACT_ID = "synthetic-registry-1"
_APPROVAL_ID = "SYNTHETIC-P2A-APPROVAL-1"
_DIGEST = "a" * 64
_FIELDS = ("side", "orderSide", "aggressor", "role", "isBuyerMaker")


# ---------------------------------------------------------------------------
# Untrusted author side
# ---------------------------------------------------------------------------


def _mapping(
    provider_field: str,
    canonical_field: str,
    *,
    family: SensorFamily = SensorFamily.MECHANICAL_LIQUIDATION,
    confidence: SemanticConfidence = SemanticConfidence.VERIFIED_FIRST_PARTY,
    evidence: str | None = f"{_LABEL}:evidence",
    methodology: str | None = _METHOD,
    transformation: str | None = None,
    assumption: str = f"{_LABEL}:resolved",
    version: str = "1",
) -> ProviderSemanticMapping:
    return ProviderSemanticMapping(
        provider=_PROVIDER,
        provider_field=provider_field,
        canonical_sensor=family,
        canonical_field=canonical_field,
        semantic_equivalence_class=SemanticEquivalence.EXACT_EQUIVALENT,
        native_definition=f"{_LABEL}:{provider_field}",
        transformation=transformation or f"{_LABEL}:{provider_field}->{canonical_field}",
        methodology_id=methodology,
        blocking_assumptions=(assumption,),
        known_limitations=(f"{_LABEL}:fixture-only-authority",),
        source_endpoint_or_archive="synthetic://p2a-authority",
        data_type="EVENT",
        native_unit="ENUM",
        timestamp_meaning="EVENT_TIME",
        interval_data_scope=IntervalDataScope.INTERVAL_LOCAL,
        direction_side_convention=f"{_LABEL}:{canonical_field}",
        evidence_reference=evidence,
        semantic_confidence=confidence,
        last_verified_date=None,
        version=version,
    )


def _registry(*rows: ProviderSemanticMapping) -> ProviderSemanticRegistry:
    return ProviderSemanticRegistry(schema_version=_SCHEMA, mappings=rows)


def _synthetic_rows() -> tuple[ProviderSemanticMapping, ...]:
    return (
        _mapping("side", "position_side_liquidated"),
        _mapping("orderSide", "execution_side"),
        _mapping("aggressor", "aggressor_side"),
        _mapping("role", "maker_taker_role"),
    )


def _full_registry() -> ProviderSemanticRegistry:
    return _registry(*_synthetic_rows())


def _artifact_bytes(*rows: ProviderSemanticMapping, comment: str | None = None) -> bytes:
    registry = _registry(*(rows or _synthetic_rows()))
    text = serialize_provider_semantic_registry_yaml(registry)
    if comment is not None:
        text = f"# {comment}\n{text}"
    return text.encode("utf-8")


# ---------------------------------------------------------------------------
# Trusted approver side
# ---------------------------------------------------------------------------


def _manifest_bytes(
    artifact: bytes,
    *,
    sha256: str | None = None,
    approval_id: str = _APPROVAL_ID,
    revoked: tuple[str, ...] = (),
    valid_until: str | None = None,
    approved_at: str = "2026-11-06",
    methodologies: tuple[str, ...] = (_METHOD,),
    evidence: dict[str, dict[str, list[str]]] | None = None,
    declared_fields: dict[str, list[str]] | None = None,
    transformations: dict[str, str] | None = None,
    assumptions: tuple[str, ...] = (f"{_LABEL}:resolved",),
    registry_schema_version: str = _SCHEMA,
) -> bytes:
    entry = {
        "sha256": sha256 or hashlib.sha256(artifact).hexdigest(),
        "approval_id": approval_id,
        "registry_schema_version": registry_schema_version,
        "approved_at": approved_at,
        "valid_until": valid_until,
        "allowed_methodologies": list(methodologies),
        "evidence": evidence
        or {_PROVIDER: {field: [f"{_LABEL}:evidence"] for field in _FIELDS}},
        "declared_native_fields": declared_fields or {_PROVIDER: list(_FIELDS)},
        "approved_transformations": transformations or {},
        "resolved_blocking_assumptions": list(assumptions),
    }
    payload = {
        "schema_version": "b5-i09p2a-1",
        "authority_id": "SYNTH_P2A_TRUST_ROOT",
        "artifacts": {_ARTIFACT_ID: entry},
        "revoked_approval_ids": list(revoked),
    }
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _methodology_registry(
    methodology_id: str = _METHOD, version: str = "1"
) -> NormalizationMethodologyRegistry:
    row = NormalizationMethodology(
        methodology_id=methodology_id,
        version=version,
        sensor_family=SensorFamily.MECHANICAL_LIQUIDATION,
        description=f"{_LABEL}: synthetic methodology, certifies nothing",
        formula_or_algorithm="preserve native field; map one enum member",
        required_inputs=("native_field",),
        output_units=("ENUM",),
        PIT_requirements="no derivation; the field is read as declared",
        known_limitations=(f"{_LABEL}:fixture-only",),
        introduced_at="e2df7109b4ae336c2ed71f1cb8b56e2b4360874e",
    )
    return NormalizationMethodologyRegistry(schema_version="1", methodologies=(row,))


def _load(
    artifact: bytes | None = None,
    manifest: bytes | None = None,
    *,
    methodology_registry: NormalizationMethodologyRegistry | None = None,
    evaluation_at: datetime | None = None,
) -> SemanticAuthority:
    artifact = artifact if artifact is not None else _artifact_bytes()
    manifest = manifest if manifest is not None else _manifest_bytes(artifact)
    return load_semantic_authority(
        manifest_bytes=manifest,
        artifact_id=_ARTIFACT_ID,
        artifact_bytes=artifact,
        methodology_registry=methodology_registry or _methodology_registry(),
        evaluation_at=evaluation_at,
    )


def _authority() -> SemanticAuthority:
    return _load()


# ---------------------------------------------------------------------------
# Consumers' fixtures
# ---------------------------------------------------------------------------


def _payload(**overrides: object) -> LiquidationObservationInput:
    base: dict[str, object] = dict(
        provider=_PROVIDER,
        venue="BINANCE",
        native_instrument="BTCUSD_PERP",
        liquidation_event_id="liq-1",
        position_side_liquidated=LiquidationPositionSide.LONG,
        execution_side=AggressorSide.SELL,
        native_position_side_field="side",
        native_position_side_value="LONG",
        native_execution_side_field="orderSide",
        native_execution_side_value="SELL",
        quantity_native=Decimal("250"),
        quantity_native_unit="CONTRACTS",
        aggregation_scope=LiquidationAggregationScope.EVENT_LEVEL,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
    )
    base.update(overrides)
    return LiquidationObservationInput(**base)  # type: ignore[arg-type]


def _trade_payload(**overrides: object) -> TradeObservationInput:
    base: dict[str, object] = dict(
        provider=_PROVIDER,
        venue="BINANCE",
        native_instrument="BTCUSDT",
        price_native=Decimal("60000"),
        quantity_native=Decimal("0.5"),
        quantity_native_unit="BTC",
        side_evidence=SideEvidence.provider_boolean(
            "isBuyerMaker", True, provider=_PROVIDER
        ),
        event_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
    )
    base.update(overrides)
    return TradeObservationInput(**base)  # type: ignore[arg-type]


def _refusal(callable_) -> AuthorityRefusal:
    with pytest.raises(SemanticAuthorityRefusal) as excinfo:
        callable_()
    return excinfo.value.refusal


# ---------------------------------------------------------------------------
# 1-4: the approval source, not the artifact, decides
# ---------------------------------------------------------------------------


def test_01_absent_manifest_entry_is_refused() -> None:
    """A manifest that approves nothing cannot be talked into approving by shape."""
    empty = json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "EMPTY",
            "artifacts": {},
            "revoked_approval_ids": [],
        }
    ).encode()
    assert _refusal(lambda: _load(manifest=empty)) is AuthorityRefusal.NO_APPROVAL
    other = _manifest_bytes(_artifact_bytes()).replace(
        _ARTIFACT_ID.encode(), b"some-other-artifact"
    )
    assert (
        _refusal(lambda: _load(manifest=other))
        is AuthorityRefusal.ARTIFACT_NOT_APPROVED
    )


def test_02_self_declared_digest_is_ignored() -> None:
    """A digest travelling with the artifact is not evidence about the artifact."""
    approved = _artifact_bytes()
    manifest = _manifest_bytes(approved)
    # The author now ships DIFFERENT bytes that merely CLAIM the approved digest.
    claimed = _artifact_bytes(
        comment=f"authoritative_sha256: {hashlib.sha256(approved).hexdigest()}"
    )
    assert (
        _refusal(lambda: _load(artifact=claimed, manifest=manifest))
        is AuthorityRefusal.DIGEST_MISMATCH
    )


def test_03_single_byte_mutation_is_detected() -> None:
    approved = _artifact_bytes()
    manifest = _manifest_bytes(approved)
    mutated = bytearray(approved)
    mutated[0] = mutated[0] ^ 0x01
    assert (
        _refusal(lambda: _load(artifact=bytes(mutated), manifest=manifest))
        is AuthorityRefusal.DIGEST_MISMATCH
    )


def test_04_confidence_edit_after_approval_is_detected() -> None:
    """A rung nobody approved cannot be reached by editing the row afterwards."""
    approved = _artifact_bytes(
        *(row for row in _synthetic_rows() if row.provider_field != "side"),
        _mapping(
            "side",
            "position_side_liquidated",
            confidence=SemanticConfidence.COMMUNITY_DOCUMENTED,
        ),
    )
    manifest = _manifest_bytes(approved)
    upgraded = _artifact_bytes(
        *(row for row in _synthetic_rows() if row.provider_field != "side"),
        _mapping(
            "side",
            "position_side_liquidated",
            confidence=SemanticConfidence.VERIFIED_FIRST_PARTY,
        ),
    )
    assert (
        _refusal(lambda: _load(artifact=upgraded, manifest=manifest))
        is AuthorityRefusal.DIGEST_MISMATCH
    )


# ---------------------------------------------------------------------------
# 5-9: per-row evidence chain, measured at the loader
# ---------------------------------------------------------------------------


def test_05_unregistered_methodology_is_refused() -> None:
    artifact = _artifact_bytes(
        _mapping("side", "position_side_liquidated", methodology="NOT_REGISTERED_V9"),
        *[row for row in _synthetic_rows() if row.provider_field != "side"],
    )
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=_manifest_bytes(artifact)))
        is AuthorityRefusal.UNREGISTERED_METHODOLOGY
    )


def test_06_foreign_evidence_is_refused() -> None:
    artifact = _artifact_bytes(
        _mapping(
            "side",
            "position_side_liquidated",
            evidence="KRAKEN_FUTURES_PUBLIC_API_DOCS_v4.pdf",
        ),
        *[row for row in _synthetic_rows() if row.provider_field != "side"],
    )
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=_manifest_bytes(artifact)))
        is AuthorityRefusal.EVIDENCE_NOT_BOUND_TO_PROVIDER
    )


def test_07_undeclared_native_field_is_refused() -> None:
    artifact = _artifact_bytes(
        _mapping("invented_field", "position_side_liquidated"),
        *[row for row in _synthetic_rows() if row.provider_field != "side"],
    )
    manifest = _manifest_bytes(
        artifact,
        evidence={
            _PROVIDER: {
                **{field: [f"{_LABEL}:evidence"] for field in _FIELDS},
                "invented_field": [f"{_LABEL}:evidence"],
            }
        },
    )
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.NATIVE_FIELD_NOT_DECLARED
    )


def test_08_unapproved_transformation_is_refused() -> None:
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(
        artifact,
        transformations={"side": f"{_LABEL}:something-else-entirely"},
    )
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.TRANSFORMATION_NOT_APPROVED
    )


def test_09_unresolved_blocking_assumption_is_refused() -> None:
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(artifact, assumptions=())
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.BLOCKING_ASSUMPTION_UNRESOLVED
    )


# ---------------------------------------------------------------------------
# 10-13: who may hold authority, and who may act on it
# ---------------------------------------------------------------------------


def test_10_authority_cannot_be_constructed_by_a_caller() -> None:
    with pytest.raises(ValueError):
        SemanticAuthority(
            artifact_id=_ARTIFACT_ID,
            approval_id=_APPROVAL_ID,
            registry_digest=hashlib.sha256(_artifact_bytes()).hexdigest(),
            manifest_authority_id="FORGED",
            registry=_full_registry(),
            allowed_methodologies=(_METHOD,),
            evidence={_PROVIDER: {field: (f"{_LABEL}:evidence",) for field in _FIELDS}},
            declared_native_fields={_PROVIDER: _FIELDS},
        )


def test_11_trade_consumer_refuses_a_bare_registry() -> None:
    """The ladder may run; the canonical field may not move (I10 gate)."""
    row = _mapping(
        "isBuyerMaker",
        "aggressor_side",
        family=SensorFamily.MECHANICAL_TRADE,
        methodology="AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1",
    )
    record = normalize_trade(_trade_payload(), registry=_registry(row))
    assert isinstance(record, T1TradeRecord)
    assert record.provisional_side is not None
    assert record.provisional_side.mapped_side is AggressorSide.SELL
    # the ladder itself would have admitted it...
    assert record.provisional_side.canonical_admitted is True
    # ...and the canonical field still does not move: shape is not authority.
    assert record.aggressor_side is AggressorSide.UNKNOWN


def test_12_liquidation_consumer_refuses_a_bare_registry() -> None:
    record = normalize_liquidation(_payload(), registry=_full_registry())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN
    refusal = {
        admission.refusal for admission in record.side_admissions
    }
    assert LiquidationAdmissionRefusal.UNTRUSTED_AUTHORITY in refusal


def test_13_missing_authority_is_a_stated_refusal_not_a_default() -> None:
    record = normalize_liquidation(_payload())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert all(
        admission.refusal is not None for admission in record.side_admissions
    )
    assert record.normalization_status is NormalizationStatus.NATIVE_ONLY


# ---------------------------------------------------------------------------
# 14-17: lifecycle, versioning, determinism
# ---------------------------------------------------------------------------


def test_14_revoked_approval_is_refused() -> None:
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(artifact, revoked=(_APPROVAL_ID,))
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.APPROVAL_REVOKED
    )


def test_15_expired_approval_is_refused() -> None:
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(
        artifact, approved_at="2025-01-01", valid_until="2026-01-01"
    )
    assert (
        _refusal(
            lambda: _load(
                artifact=artifact,
                manifest=manifest,
                evaluation_at=datetime(2026, 11, 6, tzinfo=timezone.utc),
            )
        )
        is AuthorityRefusal.AUTHORITY_EXPIRED
    )
    # and a window with no stated instant is refused rather than assumed current
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.EVALUATION_TIME_REQUIRED
    )


def test_16_version_mismatch_is_refused() -> None:
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(artifact, registry_schema_version="SOME_OTHER_SCHEMA")
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=manifest))
        is AuthorityRefusal.VERSION_MISMATCH
    )


def test_17_same_bytes_yield_the_same_authority() -> None:
    first, second = _load(), _load()
    assert first.registry_digest == second.registry_digest
    assert first.approval_id == second.approval_id
    assert first.registry.model_dump_json() == second.registry.model_dump_json()


# ---------------------------------------------------------------------------
# 18-20: the gate is not a blanket refusal
# ---------------------------------------------------------------------------


def test_18_approved_synthetic_authority_admits() -> None:
    record = normalize_liquidation(_payload(), registry=_authority())
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.execution_side is AggressorSide.SELL
    admitted = [
        admission for admission in record.side_admissions if admission.admitted
    ]
    assert admitted
    for admission in admitted:
        assert admission.admission_approval_id == _APPROVAL_ID
        assert admission.admission_registry_digest == _authority().registry_digest


def test_19_two_actor_self_approval_is_impossible() -> None:
    """The author cannot certify its own bytes, even with a digest in hand."""
    original = _artifact_bytes()
    manifest = _manifest_bytes(original)
    attacker = _artifact_bytes(
        _mapping("side", "position_side_liquidated", evidence=f"{_LABEL}:self-signed"),
        *[row for row in _synthetic_rows() if row.provider_field != "side"],
        comment=f"approved_sha256: {hashlib.sha256(original).hexdigest()}",
    )
    assert (
        _refusal(lambda: _load(artifact=attacker, manifest=manifest))
        is AuthorityRefusal.DIGEST_MISMATCH
    )
    # Approving the attacker's bytes requires the APPROVER to sign different
    # bytes; the author cannot produce that on its own.
    assert _load(artifact=_artifact_bytes(), manifest=_manifest_bytes(_artifact_bytes()))


def test_20_the_shipping_manifest_admits_nothing() -> None:
    shipping = (
        _QUANT_LAB
        / "config"
        / "crypto_sensor_fabric"
        / "provider_semantics"
        / "approval_manifest.json"
    ).read_bytes()
    payload = json.loads(shipping)
    assert payload["artifacts"] == {}, "P2a authorizes no provider semantics"
    assert payload["revoked_approval_ids"] == []
    assert (
        _refusal(lambda: _load(artifact=_artifact_bytes(), manifest=shipping))
        is AuthorityRefusal.NO_APPROVAL
    )


# ---------------------------------------------------------------------------
# G1-G7: the original defects, re-run against PRODUCTION
# ---------------------------------------------------------------------------


def test_g1_a_caller_minted_registry_cannot_promote() -> None:
    record = normalize_liquidation(_payload(), registry=_full_registry())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN


def test_g2_an_unregistered_methodology_cannot_promote() -> None:
    row = _mapping("side", "position_side_liquidated", methodology="GHOST_METHOD_V1")
    record = normalize_liquidation(
        _payload(
            native_execution_side_field=None,
            native_execution_side_value=None,
            execution_side=AggressorSide.UNKNOWN,
        ),
        registry=_registry(row),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_g3_foreign_evidence_cannot_promote() -> None:
    row = _mapping(
        "side", "position_side_liquidated", evidence="KRAKEN_DOCS_v4.pdf"
    )
    record = normalize_liquidation(
        _payload(
            native_execution_side_field=None,
            native_execution_side_value=None,
            execution_side=AggressorSide.UNKNOWN,
        ),
        registry=_registry(row),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_g4_an_undeclared_native_field_cannot_promote() -> None:
    row = _mapping("invented_field", "position_side_liquidated")
    record = normalize_liquidation(
        _payload(
            native_position_side_field="invented_field",
            native_execution_side_field=None,
            native_execution_side_value=None,
            execution_side=AggressorSide.UNKNOWN,
        ),
        registry=_registry(row),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_g5_an_unsupported_transformation_cannot_promote() -> None:
    row = _mapping(
        "side",
        "position_side_liquidated",
        transformation="do_whatever_looks_right",
    )
    record = normalize_liquidation(
        _payload(
            native_execution_side_field=None,
            native_execution_side_value=None,
            execution_side=AggressorSide.UNKNOWN,
        ),
        registry=_registry(row),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_g6_a_contradicting_assumption_cannot_promote() -> None:
    row = _mapping(
        "side",
        "position_side_liquidated",
        assumption="execution side IS the position side",
    )
    record = normalize_liquidation(
        _payload(
            native_execution_side_field=None,
            native_execution_side_value=None,
            execution_side=AggressorSide.UNKNOWN,
        ),
        registry=_registry(row),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_g7_an_admission_without_approval_provenance_is_unrepresentable() -> None:
    """The record law refuses a hand-minted "admitted" decision with no authority.

    RESIDUAL, stated rather than hidden: a caller who fabricates BOTH the decision
    and plausible provenance constants produces a record that validates, because a
    pydantic validator cannot authenticate an external approval root.  That is why
    the record-level provenance gate stays PARTIAL until an ingestion boundary
    exists (I09P2A evidence, section on direct construction).
    """
    with pytest.raises(ValueError, match="must name the approving authority"):
        LiquidationSideAdmission(
            canonical_field=LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED,
            provider_field="side",
            provisional_value="LONG",
            semantic_confidence=SemanticConfidence.VERIFIED_FIRST_PARTY,
            evidence_reference=f"{_LABEL}:evidence",
            methodology_id=_METHOD,
            mapping_version="1",
            admitted=True,
        )

    forged = LiquidationSideAdmission(
        canonical_field=LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED,
        provider_field="side",
        provisional_value="LONG",
        semantic_confidence=SemanticConfidence.VERIFIED_FIRST_PARTY,
        evidence_reference=f"{_LABEL}:evidence",
        methodology_id=_METHOD,
        mapping_version="1",
        admitted=True,
        admission_approval_id="FORGED-APPROVAL",
        admission_registry_digest=hashlib.sha256(b"forged").hexdigest(),
    )
    assert forged.admitted is True
    record = normalize_liquidation(_payload())
    with pytest.raises(ValueError, match="no admitted registry mapping"):
        T1LiquidationRecord.model_validate(
            {
                **record.model_dump(),
                "position_side_liquidated": LiquidationPositionSide.LONG,
                "side_admissions": (),
            }
        )


# ---------------------------------------------------------------------------
# Manifest hygiene
# ---------------------------------------------------------------------------


def test_a_manifest_with_duplicate_keys_has_no_authority() -> None:
    artifact = _artifact_bytes()
    duplicated = (
        '{"schema_version": "b5-i09p2a-1", "authority_id": "A", '
        '"authority_id": "B", "artifacts": {}, "revoked_approval_ids": []}'
    ).encode()
    assert (
        _refusal(lambda: _load(artifact=artifact, manifest=duplicated))
        is AuthorityRefusal.MALFORMED_MANIFEST
    )


def test_a_pending_evidence_approval_is_unrepresentable() -> None:
    artifact = _artifact_bytes()
    with pytest.raises(SemanticAuthorityRefusal) as excinfo:
        _load(
            artifact=artifact,
            manifest=_manifest_bytes(
                artifact,
                evidence={_PROVIDER: {"side": [PENDING_EVIDENCE_REFERENCE]}},
            ),
        )
    assert excinfo.value.refusal is AuthorityRefusal.MALFORMED_MANIFEST


def test_the_loader_is_pure_and_never_reads_a_clock() -> None:
    """Two loads at two implied "times" agree unless a window was declared."""
    artifact = _artifact_bytes()
    manifest = _manifest_bytes(artifact)
    first = _load(artifact=artifact, manifest=manifest)
    second = _load(artifact=artifact, manifest=manifest)
    assert first.valid_until is None and second.valid_until is None
    assert first.registry_digest == second.registry_digest


def test_liquidation_arithmetic_is_untouched_by_the_gate() -> None:
    """Authority changes WHO may promote, never the numbers."""
    record = normalize_liquidation(_payload(), registry=_authority())
    assert record.quantity_native == Decimal("250")
    assert record.liquidation_usd is not None
    assert record.liquidation_usd.blocked is True
    assert record.liquidation_usd.unresolved_citation == "B5_I08_UNITS_V1"
    assert record.provisional_position_side is LiquidationPositionSide.LONG
    assert record.native_position_side_value == "LONG"


def test_the_registry_type_is_still_parseable_as_a_diagnostic_value() -> None:
    text = serialize_provider_semantic_registry_yaml(_full_registry())
    reparsed = parse_provider_semantic_registry_yaml(text)
    assert reparsed.resolve(
        _PROVIDER, "side", SensorFamily.MECHANICAL_LIQUIDATION
    ) is not None
