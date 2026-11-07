"""SENSOR-B5-I09P2b - trusted initialization, custody and record provenance.

The distinction this suite pins: ``load_semantic_authority`` believes whichever
manifest it is handed (the P2a residual), while ``load_trusted_authority``
accepts only the reviewed production manifest, whose digest is pinned in source
rather than inside the manifest it describes.

Every fixture here is labelled synthetic.  None of it certifies a venue, and a
synthetic approval proves only that the mechanism works under its test root.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import date

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_RELPATH,
    TRUSTED_MANIFEST_SHA256,
    MappingProvenance,
    SemanticAuthorityRefusal,
    load_semantic_authority,
    load_trusted_authority,
    parse_approval_manifest,
    verify_evidence_custody,
    verify_liquidation_admission_provenance,
    verify_mapping_provenance,
)
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.sensors.trade import T1TradeRecord

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
PRODUCTION_MANIFEST = QUANT_LAB / TRUSTED_MANIFEST_RELPATH

DOC_BYTES = b"synthetic venue document bytes (not a real provider document)"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2B_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"

REGISTRY_TEXT = """schema_version: "9.9.9"
mappings:
  - provider: BINANCE_USDM
    provider_field: isBuyerMaker
    canonical_sensor: MECHANICAL_TRADE
    canonical_field: aggressor_side
    semantic_equivalence_class: NORMALIZABLE_COMPARABLE
    native_definition: "provider boolean: true when the buyer is the maker"
    transformation: "isBuyerMaker=true -> SELL; false -> BUY"
    methodology_id: AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1
    blocking_assumptions: ["venue documents isBuyerMaker as the maker-side flag"]
    known_limitations: ["single venue; no cross-venue polarity claim"]
    source_endpoint_or_archive: "wss futures trade stream"
    data_type: "boolean"
    native_unit: "n/a"
    timestamp_meaning: "event time"
    interval_data_scope: INTERVAL_LOCAL
    direction_side_convention: "taker aggressor"
    evidence_reference: SYNTHETIC_P2B_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
  - provider: BINANCE_USDM
    provider_field: side
    canonical_sensor: MECHANICAL_LIQUIDATION
    canonical_field: position_side_liquidated
    semantic_equivalence_class: NORMALIZABLE_COMPARABLE
    native_definition: "provider string naming the liquidated position side"
    transformation: "side -> liquidated position side"
    methodology_id: LIQUIDATION_SIDE_BINANCE_V1
    blocking_assumptions: [venue documents side as the liquidated position side]
    known_limitations: ["single venue; no cross-venue polarity claim"]
    source_endpoint_or_archive: "wss futures forceOrder stream"
    data_type: "string"
    native_unit: "n/a"
    timestamp_meaning: "event time"
    interval_data_scope: INTERVAL_LOCAL
    direction_side_convention: "liquidated position side"
    evidence_reference: SYNTHETIC_P2B_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p2b-1",
            "methodologies": [
                {
                    "methodology_id": METHOD_ID,
                    "version": "1",
                    "sensor_family": "MECHANICAL_TRADE",
                    "description": "synthetic probe methodology",
                    "formula_or_algorithm": "isBuyerMaker -> side",
                    "required_inputs": ["isBuyerMaker"],
                    "output_units": ["AggressorSide"],
                    "PIT_requirements": "none beyond event time",
                    "known_limitations": ["synthetic"],
                    "introduced_at": "probe",
                },
                {
                    "methodology_id": LIQ_METHOD,
                    "version": "1",
                    "sensor_family": "MECHANICAL_LIQUIDATION",
                    "description": "synthetic liquidation probe methodology",
                    "formula_or_algorithm": "side -> liquidated position side",
                    "required_inputs": ["side"],
                    "output_units": ["LiquidationPositionSide"],
                    "PIT_requirements": "none beyond event time",
                    "known_limitations": ["synthetic"],
                    "introduced_at": "probe",
                }
            ],
        }
    )


def _synthetic_manifest(
    *,
    available_at: str | None = "2026-03-01",
    evidence_blobs: dict[str, str] | None = None,
    approval_id: str = "APPROVAL-SYNTHETIC-P2B",
    schema_version: str = "b5-i09p2a-1",
) -> bytes:
    entry = {
        "sha256": ARTIFACT_SHA,
        "approval_id": approval_id,
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": "2027-01-01",
        "allowed_methodologies": [METHOD_ID, LIQ_METHOD],
        "evidence": {"BINANCE_USDM": {"isBuyerMaker": [REF], "side": [REF]}},
        "declared_native_fields": {"BINANCE_USDM": ["isBuyerMaker", "side"]},
        "approved_transformations": {},
        "resolved_blocking_assumptions": [ASSUMPTION, LIQ_ASSUMPTION],
    }
    if available_at is not None:
        entry["available_at"] = available_at
    evidence_blobs = {REF: DOC_SHA} if evidence_blobs is None else evidence_blobs
    entry["evidence_blobs"] = evidence_blobs
    return json.dumps(
        {
            "schema_version": schema_version,
            "authority_id": "PROBE_ROOT",
            "artifacts": {"registry-probe.yaml": entry},
            "revoked_approval_ids": [],
        }
    ).encode("utf-8")


def _pin(monkeypatch: pytest.MonkeyPatch, manifest: bytes) -> None:
    """Explicit test-only trust root: the reviewed constant, for these bytes."""
    monkeypatch.setattr(
        authority_module,
        "TRUSTED_MANIFEST_SHA256",
        hashlib.sha256(manifest).hexdigest(),
    )


def _trusted_load(monkeypatch: pytest.MonkeyPatch, *, evaluation_at: date, **manifest_kwargs):
    manifest = _synthetic_manifest(**manifest_kwargs)
    _pin(monkeypatch, manifest)
    return load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id="registry-probe.yaml",
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=evaluation_at,
    )


def _refusal(call) -> str:
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        call()
    return caught.value.refusal.value


# -- ROOT -------------------------------------------------------------------


def test_production_pin_matches_the_reviewed_manifest() -> None:
    """The pin in source must equal the shipped manifest, byte for byte."""
    payload = json.loads(PRODUCTION_MANIFEST.read_text(encoding="utf-8"))
    assert hashlib.sha256(PRODUCTION_MANIFEST.read_bytes()).hexdigest() == (
        TRUSTED_MANIFEST_SHA256
    )
    assert payload["artifacts"] == {}


def test_trusted_entry_refuses_an_actor_supplied_manifest() -> None:
    """Both sides of the pair coming from one actor is not an approval."""
    attacker = _synthetic_manifest(approval_id="ATTACKER-APPROVAL")
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        load_trusted_authority(
            manifest_bytes=attacker,
            artifact_id="registry-probe.yaml",
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
            evaluation_at=date(2026, 6, 1),
        )
    assert caught.value.refusal.value == "TRUSTED_ROOT_MISMATCH"


def test_untrusted_loader_remains_the_documented_residual() -> None:
    """P2b narrows the entry point; it does not rewrite the lower-level loader."""
    manifest = _synthetic_manifest()
    issued = load_semantic_authority(
        manifest_bytes=manifest,
        artifact_id="registry-probe.yaml",
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=date(2026, 6, 1),
    )
    assert issued.approval_id == "APPROVAL-SYNTHETIC-P2B"


def test_trusted_entry_pins_the_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _synthetic_manifest(schema_version="some-other-generation")
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        load_trusted_authority(
            manifest_bytes=manifest,
            artifact_id="registry-probe.yaml",
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
            evaluation_at=date(2026, 6, 1),
        )
    assert caught.value.refusal.value == "TRUSTED_ROOT_MISMATCH"


def test_trusted_entry_issues_under_the_pinned_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    assert authority.approval_id == "APPROVAL-SYNTHETIC-P2B"
    assert authority.evidence_blobs == {REF: DOC_SHA}


# -- PIT --------------------------------------------------------------------


def test_approval_used_before_it_became_available_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        load_trusted_authority(
            manifest_bytes=manifest,
            artifact_id="registry-probe.yaml",
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
            evaluation_at=date(2026, 2, 1),
        )
    assert caught.value.refusal.value == "APPROVAL_NOT_YET_AVAILABLE"


def test_availability_without_an_evaluation_instant_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        load_trusted_authority(
            manifest_bytes=manifest,
            artifact_id="registry-probe.yaml",
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
        )
    assert caught.value.refusal.value == "EVALUATION_TIME_REQUIRED"


def test_approval_applied_after_availability_is_admitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 3, 1))
    assert authority.available_at == "2026-03-01"


# -- CUSTODY ----------------------------------------------------------------


def test_custody_binds_the_reference_to_the_held_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    verify_evidence_custody(authority, {REF: DOC_SHA})


def test_custody_refuses_a_missing_blob(monkeypatch: pytest.MonkeyPatch) -> None:
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        verify_evidence_custody(authority, {})
    assert caught.value.refusal.value == "EVIDENCE_BLOB_UNVERIFIED"


def test_custody_refuses_a_swapped_blob(monkeypatch: pytest.MonkeyPatch) -> None:
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        verify_evidence_custody(
            authority, {REF: hashlib.sha256(b"another document").hexdigest()}
        )
    assert caught.value.refusal.value == "EVIDENCE_BLOB_UNVERIFIED"


def test_an_unbound_blob_cannot_be_declared() -> None:
    unbound = _synthetic_manifest(evidence_blobs={"NOT_BOUND_ANYWHERE": DOC_SHA})
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        parse_approval_manifest(unbound)
    assert caught.value.refusal.value == "MALFORMED_MANIFEST"


# -- PROVENANCE -------------------------------------------------------------


def _provenance(authority) -> MappingProvenance:
    return MappingProvenance(
        artifact_id=authority.artifact_id,
        approval_id=authority.approval_id,
        registry_digest=authority.registry_digest,
        provider="BINANCE_USDM",
        provider_field="isBuyerMaker",
        canonical_field="aggressor_side",
        canonical_sensor="MECHANICAL_TRADE",
        methodology_id=METHOD_ID,
        methodology_version="1",
        evidence_reference=REF,
        semantic_confidence="VERIFIED_SECONDARY",
        approved_at="2026-01-01",
        available_at="2026-03-01",
    )


def test_provenance_is_re_derived_against_the_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest()
    _pin(monkeypatch, manifest)
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    verify_mapping_provenance(
        _provenance(authority),
        manifest_bytes=manifest,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=date(2026, 6, 1),
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("approval_id", "ATTACKER-APPROVAL"),
        ("registry_digest", "0" * 64),
        ("canonical_field", "position_side_liquidated"),
        ("semantic_confidence", "VERIFIED_FIRST_PARTY"),
        ("methodology_id", "MINTED_BY_CALLER_V1"),
        ("evidence_reference", "SOME_OTHER_DOC"),
    ],
)
def test_a_mutated_provenance_claim_is_refused(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str
) -> None:
    manifest = _synthetic_manifest()
    _pin(monkeypatch, manifest)
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    payload = _provenance(authority).model_dump()
    payload[field] = value
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        verify_mapping_provenance(
            MappingProvenance.model_validate(payload),
            manifest_bytes=manifest,
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
            evaluation_at=date(2026, 6, 1),
        )
    assert caught.value.refusal.value == "PROVENANCE_MISMATCH"


def test_a_record_without_provenance_cannot_be_verified() -> None:
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        verify_mapping_provenance(
            None,
            manifest_bytes=_synthetic_manifest(),
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
        )
    assert caught.value.refusal.value == "PROVENANCE_MISSING"


def test_trade_record_carries_the_provenance_slot() -> None:
    assert "authority_provenance" in T1TradeRecord.model_fields


# -- LIQUIDATION PROVENANCE --------------------------------------------------


def _liquidation_admission(authority):
    from crypto_sensor_fabric.normalization.sensors.liquidation import (
        LiquidationSideAdmission,
    )

    return LiquidationSideAdmission(
        canonical_field="position_side_liquidated",
        provider_field="side",
        provisional_value="BUY",
        semantic_confidence="VERIFIED_SECONDARY",
        evidence_reference=REF,
        methodology_id=LIQ_METHOD,
        mapping_version="1",
        admitted=True,
        admission_approval_id=authority.approval_id,
        admission_registry_digest=authority.registry_digest,
    )


def _verify_liquidation(admission, manifest) -> None:
    verify_liquidation_admission_provenance(
        admission,
        artifact_id="registry-probe.yaml",
        manifest_bytes=manifest,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=date(2026, 6, 1),
    )


def test_liquidation_admission_is_re_derived(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _synthetic_manifest()
    _pin(monkeypatch, manifest)
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    provenance = verify_liquidation_admission_provenance(
        _liquidation_admission(authority),
        artifact_id="registry-probe.yaml",
        manifest_bytes=manifest,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=date(2026, 6, 1),
    )
    assert provenance.canonical_sensor == "MECHANICAL_LIQUIDATION"
    assert provenance.provider == "BINANCE_USDM"
    assert provenance.evidence_reference == REF


def test_liquidation_admission_without_approving_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest()
    _pin(monkeypatch, manifest)
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    admission = _liquidation_admission(authority).model_copy(
        update={"admission_approval_id": None}
    )
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _verify_liquidation(admission, manifest)
    assert caught.value.refusal.value == "PROVENANCE_MISSING"


def test_mutated_liquidation_digest_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest()
    _pin(monkeypatch, manifest)
    authority = _trusted_load(monkeypatch, evaluation_at=date(2026, 6, 1))
    admission = _liquidation_admission(authority).model_copy(
        update={"admission_registry_digest": "0" * 64}
    )
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _verify_liquidation(admission, manifest)
    assert caught.value.refusal.value == "PROVENANCE_MISMATCH"
