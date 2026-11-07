"""SENSOR-B5-I09P2d - custody authority, scoped verdicts and PIT fail-closure.

Attacks the four defects the P2cR1 independent audit measured:

* F-R1-01 a custody-shaped object that holds no bytes could earn
  ``custody_verified`` by echoing the approval's public digest;
* F-R1-02 ``downstream_trusted`` was awarded while venue, instrument, revision
  and acquisition identity stayed unauthenticated, with nothing in the result
  saying so;
* F-R1-03 the result model accepted internally contradictory trust states;
* F-R1-04 an approval carrying no availability field was admissible at any
  earlier cutoff.

Every approval, registry and blob here is SYNTHETIC and labelled as such.  A
synthetic root demonstrates the mechanism; it certifies no venue and fabricates
no provider document.
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Iterator

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.contracts.enums import AggressorSide
from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_RELPATH,
    SemanticAuthorityRefusal,
    load_trusted_authority,
)
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.sensors.liquidation import (
    LiquidationAggregationScope,
    LiquidationPositionSide,
    T1LiquidationRecord,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.sensors.side_maps import SideEvidence
from crypto_sensor_fabric.normalization.sensors.trade import (
    T1TradeRecord,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.sensors.verification import (
    TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
    BlobStoreCustody,
    RecordVerification,
    RecordVerificationError,
    TrustedAuthorityContext,
    verify_liquidation_record,
    verify_trade_record,
)
from crypto_sensor_fabric.storage import (
    IntegrityState,
    LocalBlobStore,
    StorageEncoding,
)

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
PRODUCTION_MANIFEST = QUANT_LAB / TRUSTED_MANIFEST_RELPATH

DOC_BYTES = b"synthetic p2d venue document bytes (not a real provider document)"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2D_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ARTIFACT_ID = "registry-p2d.yaml"
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

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
    evidence_reference: SYNTHETIC_P2D_DOC_REF
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
    evidence_reference: SYNTHETIC_P2D_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
  - provider: BINANCE_USDM
    provider_field: side_exec
    canonical_sensor: MECHANICAL_LIQUIDATION
    canonical_field: execution_side
    semantic_equivalence_class: NORMALIZABLE_COMPARABLE
    native_definition: "provider string naming the execution side"
    transformation: "side -> execution side"
    methodology_id: LIQUIDATION_SIDE_BINANCE_V1
    blocking_assumptions: [venue documents side as the liquidated position side]
    known_limitations: ["single venue; no cross-venue polarity claim"]
    source_endpoint_or_archive: "wss futures forceOrder stream"
    data_type: "string"
    native_unit: "n/a"
    timestamp_meaning: "event time"
    interval_data_scope: INTERVAL_LOCAL
    direction_side_convention: "execution side"
    evidence_reference: SYNTHETIC_P2D_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p2d-1",
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
                },
            ],
        }
    )


def _synthetic_manifest(
    *,
    available_at: str | None = "2026-03-01",
    available_at_instant: str | None = None,
    evidence_blobs: dict[str, str] | None = None,
    approval_id: str = "APPROVAL-SYNTHETIC-P2D",
) -> bytes:
    entry: dict[str, object] = {
        "sha256": ARTIFACT_SHA,
        "approval_id": approval_id,
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": "2027-01-01",
        "allowed_methodologies": [METHOD_ID, LIQ_METHOD],
        "evidence": {
            "BINANCE_USDM": {
                "isBuyerMaker": [REF],
                "side": [REF],
                "side_exec": [REF],
            }
        },
        "declared_native_fields": {
            "BINANCE_USDM": ["isBuyerMaker", "side", "side_exec"]
        },
        "resolved_blocking_assumptions": [ASSUMPTION, LIQ_ASSUMPTION],
        "evidence_blobs": {REF: DOC_SHA} if evidence_blobs is None else evidence_blobs,
    }
    if available_at is not None:
        entry["available_at"] = available_at
    if available_at_instant is not None:
        entry["available_at_instant"] = available_at_instant
    return json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "PROBE_ROOT",
            "artifacts": {ARTIFACT_ID: entry},
            "revoked_approval_ids": [],
        }
    ).encode("utf-8")


def _pin(monkeypatch: pytest.MonkeyPatch, manifest: bytes) -> None:
    monkeypatch.setattr(
        authority_module,
        "TRUSTED_MANIFEST_SHA256",
        hashlib.sha256(manifest).hexdigest(),
    )


def _issue(manifest: bytes, *, evaluation_at: datetime = CUTOFF):
    return load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id=ARTIFACT_ID,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=evaluation_at,
    )


def _context(manifest: bytes) -> TrustedAuthorityContext:
    return TrustedAuthorityContext.from_reviewed_root(
        manifest_bytes=manifest, artifact_id=ARTIFACT_ID
    )


def _trade_payload(**overrides: object):
    from crypto_sensor_fabric.normalization.enums import TimestampPrecision
    from crypto_sensor_fabric.normalization.sensors.trade import TradeObservationInput
    from crypto_sensor_fabric.storage import CoverageState, RevisionState

    payload: dict[str, object] = {
        "provider": "BINANCE_USDM",
        "venue": "BINANCE",
        "native_instrument": "BTCUSDT",
        "contract_instance_id": "BINANCE_USDM:BTCUSDT:PERP:2024-01",
        "native_event_id": "500001",
        "price_native": "61234.50",
        "quantity_native": "0.25000000",
        "quantity_native_unit": "BTC",
        "side_evidence": SideEvidence.provider_boolean(
            "isBuyerMaker", True, provider="BINANCE_USDM"
        ),
        "event_at": datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        "source_precision": TimestampPrecision.MILLISECOND,
        "source_revision_id": "rev-p2d-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p2d-1",
        "raw_projection_refs": ("proj:p2d:1",),
        "acquisition_refs": ("acq:p2d:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p2d",
        "config_version": "cfg-p2d",
    }
    payload.update(overrides)
    return TradeObservationInput.model_validate(payload)


def _trade_record(monkeypatch: pytest.MonkeyPatch, **kwargs) -> T1TradeRecord:
    manifest = _synthetic_manifest(**kwargs)
    _pin(monkeypatch, manifest)
    return normalize_trade(_trade_payload(), registry=_issue(manifest))


def _liq_payload(**overrides: object):
    from crypto_sensor_fabric.normalization.enums import TimestampPrecision
    from crypto_sensor_fabric.normalization.sensors.liquidation import (
        LiquidationObservationInput,
    )
    from crypto_sensor_fabric.storage import CoverageState, RevisionState

    payload: dict[str, object] = {
        "provider": "BINANCE_USDM",
        "venue": "BINANCE",
        "native_instrument": "BTCUSDT",
        "liquidation_event_id": "liq-p2d-1",
        "position_side_liquidated": LiquidationPositionSide.LONG,
        "execution_side": AggressorSide.SELL,
        "native_position_side_field": "side",
        "native_position_side_value": "LONG",
        "native_execution_side_field": "side_exec",
        "native_execution_side_value": "SELL",
        "quantity_native": "2.5",
        "quantity_native_unit": "BTC",
        "aggregation_scope": LiquidationAggregationScope.EVENT_LEVEL,
        "source_precision": TimestampPrecision.MILLISECOND,
        "source_revision_id": "rev-p2d-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p2d-1",
        "raw_projection_refs": ("proj:p2d:1",),
        "acquisition_refs": ("acq:p2d:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p2d",
        "config_version": "cfg-p2d",
    }
    payload.update(overrides)
    return LiquidationObservationInput(**payload)  # type: ignore[arg-type]


def _liq_record(monkeypatch: pytest.MonkeyPatch, **kwargs) -> T1LiquidationRecord:
    manifest = _synthetic_manifest(**kwargs)
    _pin(monkeypatch, manifest)
    return normalize_liquidation(_liq_payload(), registry=_issue(manifest))


# ---------------------------------------------------------------------------
# Custody doubles.  Each one models a DIFFERENT attack, so the assertions name
# which claim the verifier actually established.
# ---------------------------------------------------------------------------


class ByteCustody:
    """Independently held BYTES: the shape the repaired boundary accepts."""

    def __init__(self, held: dict[str, bytes]) -> None:
        self._held = dict(held)

    def read_evidence(self, reference: str) -> bytes | None:
        return self._held.get(reference)


class DigestEchoCustody:
    """P2cR1 F-R1-01: holds no bytes, echoes the approval's public digest."""

    def __init__(self, held: dict[str, str]) -> None:
        self._held = dict(held)

    def held_digest(self, reference: str) -> str | None:
        return self._held.get(reference)


class EncodedDigestCustody:
    """The digest STRING offered as if it were the evidence bytes."""

    def __init__(self, held: dict[str, str]) -> None:
        self._held = dict(held)

    def read_evidence(self, reference: str) -> bytes | None:
        value = self._held.get(reference)
        return None if value is None else value.encode("utf-8")


class LyingStore:
    """A store that claims integrity for bytes it will not match."""

    def __init__(self, blob: bytes, claimed_digest: str) -> None:
        self._blob = blob
        self._claimed = claimed_digest

    def verify_blob(self, digest: str, encoding: StorageEncoding) -> SimpleNamespace:
        return SimpleNamespace(
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            observed_hash=self._claimed,
        )

    @contextmanager
    def open_blob(self, digest: str, encoding: StorageEncoding) -> Iterator[io.BytesIO]:
        yield io.BytesIO(self._blob)


def _refusal(call) -> str:
    with pytest.raises(RecordVerificationError) as caught:
        call()
    return caught.value.refusal.value


def _verify_trade(
    record: T1TradeRecord, *, context: TrustedAuthorityContext, custody=None, cutoff=CUTOFF
) -> RecordVerification:
    return verify_trade_record(
        record,
        trusted_context=context,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        knowledge_cutoff=cutoff,
        custody=custody,
    )


def _verify_liq(
    record: T1LiquidationRecord,
    *,
    context: TrustedAuthorityContext,
    custody=None,
    cutoff=CUTOFF,
) -> RecordVerification:
    return verify_liquidation_record(
        record,
        trusted_context=context,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        knowledge_cutoff=cutoff,
        custody=custody,
    )


def _result_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "record_kind": "TRADE",
        "artifact_id": ARTIFACT_ID,
        "approval_id": "APPROVAL-SYNTHETIC-P2D",
        "registry_digest": ARTIFACT_SHA,
        "provider": "BINANCE_USDM",
        "semantic_mapping_approved": True,
        "record_transformation_verified": True,
        "custody_verified": True,
        "source_lineage_verified": False,
        "pit_admissible": True,
        "instrument_authenticated": False,
        "source_revision_authenticated": False,
        "downstream_trusted": True,
        "trust_scope": TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
        "unverified_dimensions": ("SOURCE_LINEAGE",),
        "fields_verified": ("aggressor_side",),
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# SEC-D01 .. SEC-D10 -- custody is bytes, not a self-report
# ---------------------------------------------------------------------------


def test_sec_d01_a_digest_echoing_object_is_not_a_custody_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P2cR1 F-R1-01, verbatim: the counterfeit must now fail loudly."""
    record = _trade_record(monkeypatch)
    with pytest.raises(TypeError):
        _verify_trade(
            record,
            context=_context(_synthetic_manifest()),
            custody=DigestEchoCustody({REF: DOC_SHA}),
        )


def test_sec_d02_a_plain_dictionary_is_not_custody(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    with pytest.raises(TypeError):
        _verify_trade(
            record,
            context=_context(_synthetic_manifest()),
            custody={REF: DOC_SHA},  # type: ignore[arg-type]
        )


def test_sec_d03_the_digest_string_offered_as_bytes_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=EncodedDigestCustody({REF: DOC_SHA}),
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d04_a_store_that_lies_about_integrity_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A store may claim LOCAL_HASH_VERIFIED; the verifier hashes anyway."""
    custody = BlobStoreCustody(LyingStore(b"attacker bytes", DOC_SHA), {REF: DOC_SHA})
    assert custody.held_digest(REF) == hashlib.sha256(b"attacker bytes").hexdigest()
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=custody
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


class RaisingStore:
    """A store whose verify_blob raises instead of reporting integrity."""

    def verify_blob(self, digest: str, encoding: StorageEncoding) -> SimpleNamespace:
        raise OSError("the store is not readable")

    def open_blob(self, digest: str, encoding: StorageEncoding):
        raise OSError("the store is not readable")


def test_sec_d04a_a_store_that_raises_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PA-R1-06 raised-exception arm: a raising store never yields a verdict."""
    custody = BlobStoreCustody(RaisingStore(), {REF: DOC_SHA})
    assert custody.read_evidence(REF) is None
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=custody
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d05_a_missing_blob_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    store = LocalBlobStore(tmp_path)
    record = _trade_record(monkeypatch)
    custody = BlobStoreCustody(store, {REF: DOC_SHA})
    assert custody.read_evidence(REF) is None
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=custody
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d06_a_mutated_blob_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    store = LocalBlobStore(tmp_path)
    put = store.put_bytes(
        DOC_BYTES, storage_encoding=StorageEncoding.NONE, source_media_type="text/plain"
    )
    record = _trade_record(monkeypatch)
    intact = BlobStoreCustody(store, {REF: put.blob.blob_sha256})
    assert _verify_trade(
        record, context=_context(_synthetic_manifest()), custody=intact
    ).custody_verified is True
    (tmp_path / put.object_key).write_bytes(b"tampered bytes")
    tampered = BlobStoreCustody(store, {REF: put.blob.blob_sha256})
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=tampered
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d07_an_index_pointing_at_another_blob_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    store = LocalBlobStore(tmp_path)
    other = store.put_bytes(
        b"another document",
        storage_encoding=StorageEncoding.NONE,
        source_media_type="text/plain",
    )
    record = _trade_record(monkeypatch)
    custody = BlobStoreCustody(store, {REF: other.blob.blob_sha256})
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=custody
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d08_bytes_from_another_provider_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=ByteCustody({REF: b"a different venue's document"}),
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_sec_d09_an_approval_cannot_cite_an_unbound_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(
        evidence_blobs={REF: DOC_SHA, "UNBOUND_REF": hashlib.sha256(b"x").hexdigest()}
    )
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _issue(manifest)
    assert caught.value.refusal.value == "MALFORMED_MANIFEST"


def test_sec_d10_the_approved_bytes_earn_integrity_but_not_source_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
    )
    assert result.custody_verified is True
    assert result.custody_source_authorized is False
    assert result.downstream_trusted is True
    assert "CUSTODY_SOURCE_AUTHORITY" in result.unverified_dimensions
    assert result.trust_scope == TRUST_SCOPE_ECONOMIC_FIELD_BINDING


# ---------------------------------------------------------------------------
# SEC-D11 .. SEC-D14 -- the result model refuses contradiction
# ---------------------------------------------------------------------------


def test_sec_d11_contradictory_direct_construction_is_refused() -> None:
    with pytest.raises(ValueError):
        RecordVerification.model_validate(
            _result_payload(custody_verified=False, downstream_trusted=True)
        )
    with pytest.raises(ValueError):
        RecordVerification.model_validate(
            _result_payload(semantic_mapping_approved=False)
        )


def test_sec_d12_contradictory_json_reconstruction_is_refused() -> None:
    payload = _result_payload(record_transformation_verified=False)
    text = json.dumps(payload)
    with pytest.raises(ValueError):
        RecordVerification.model_validate_json(text)


def test_sec_d13_model_copy_bypass_is_detectable() -> None:
    valid = RecordVerification.model_validate(_result_payload())
    copied = valid.model_copy(update={"custody_verified": False})
    # Documented Pydantic behaviour: the copy is NOT revalidated ...
    assert copied.downstream_trusted is True and copied.custody_verified is False
    # ... so the consumer-facing guard must catch it.
    assert (
        _refusal(copied.assert_trustworthy) == "CONTRADICTORY_VERIFICATION"
    )
    valid.assert_trustworthy()  # verifier-produced results pass unchanged


def test_sec_d14_a_verdict_cannot_exceed_its_proven_dimensions() -> None:
    with pytest.raises(ValueError):
        RecordVerification.model_validate(_result_payload(fields_verified=()))
    with pytest.raises(ValueError):
        RecordVerification.model_validate(_result_payload(unverified_dimensions=()))
    with pytest.raises(ValueError):
        RecordVerification.model_validate(
            _result_payload(pit_admissible=False, custody_verified=False)
        )
    with pytest.raises(ValueError):
        RecordVerification.model_validate(_result_payload(trust_scope="FULL_RECORD"))


# ---------------------------------------------------------------------------
# SEC-D15 .. SEC-D18 -- unauthenticated dimensions stay named
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("venue", "COINBASE"),
        ("native_instrument", "ETHUSDT"),
        ("contract_instance_id", "BINANCE_USDM:ETHUSDT:PERP:2024-01"),
        ("source_revision_id", "rev-attacker"),
        ("acquisition_refs", ("acq:attacker",)),
    ],
)
def test_sec_d15_to_d18_record_dimension_substitution_stays_unverified(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={field: value})
    result = _verify_trade(
        forged,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
    )
    assert result.instrument_authenticated is False
    assert result.source_revision_authenticated is False
    assert result.source_lineage_verified is False
    for dimension in (
        "VENUE_IDENTITY",
        "INSTRUMENT_IDENTITY",
        "SOURCE_REVISION",
        "ACQUISITION_LINEAGE",
        "SOURCE_LINEAGE",
    ):
        assert dimension in result.unverified_dimensions


# ---------------------------------------------------------------------------
# SEC-D19 .. SEC-D20 -- liquidation keeps honest uncertainty
# ---------------------------------------------------------------------------


def test_sec_d19_a_coordinated_liquidation_rewrite_stays_economically_unverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    admissions = tuple(
        admission.model_copy(
            update={
                "provisional_value": (
                    "SHORT"
                    if admission.provisional_value == "LONG"
                    else "BUY"
                    if admission.provisional_value == "SELL"
                    else admission.provisional_value
                )
            }
        )
        for admission in record.side_admissions
    )
    forged = record.model_copy(
        update={
            "position_side_liquidated": LiquidationPositionSide.SHORT,
            "execution_side": AggressorSide.BUY,
            "native_position_side_value": "SHORT",
            "native_execution_side_value": "BUY",
            "side_admissions": admissions,
        }
    )
    result = _verify_liq(
        forged,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
    )
    assert result.semantic_mapping_approved is True
    assert result.record_transformation_verified is False
    assert result.downstream_trusted is False


def test_sec_d20_mapping_approval_is_not_economic_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    result = _verify_liq(
        record,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
    )
    assert result.semantic_mapping_approved is True
    assert result.downstream_trusted is False
    assert any("executable" in note for note in result.notes)


# ---------------------------------------------------------------------------
# SEC-D21 .. SEC-D32 -- PIT availability and the timezone matrix
# ---------------------------------------------------------------------------


def test_sec_d21_an_approval_with_no_availability_is_admissible_at_no_instant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P2cR1 F-R1-04: this used to verify."""
    manifest = _synthetic_manifest(available_at=None)
    record = _trade_record(monkeypatch, available_at=None)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(manifest),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=CUTOFF,
            )
        )
        == "PIT_AVAILABILITY_MISSING"
    )


@pytest.mark.parametrize("hour", [0, 9, 15, 23])
def test_sec_d22_d23_same_day_date_only_availability_is_refused(
    monkeypatch: pytest.MonkeyPatch, hour: int
) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 3, 1, hour, 0, tzinfo=UTC),
            )
        )
        == "INTRADAY_PIT_AMBIGUOUS"
    )


def test_sec_d24_a_later_day_is_admissible(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
        cutoff=datetime(2026, 3, 2, 0, 0, tzinfo=UTC),
    )
    assert result.pit_admissible is True


def _instant_manifest(**kwargs) -> bytes:
    return _synthetic_manifest(**{"available_at_instant": "2026-03-01T15:00:00+00:00", **kwargs})


@pytest.mark.parametrize(
    "cutoff,expected",
    [
        (datetime(2026, 3, 1, 14, 59, tzinfo=UTC), "APPROVAL_NOT_YET_AVAILABLE"),
        (datetime(2026, 3, 1, 15, 0, tzinfo=UTC), None),
        (datetime(2026, 3, 1, 15, 1, tzinfo=UTC), None),
    ],
)
def test_sec_d25_to_d27_exact_instant_boundaries(
    monkeypatch: pytest.MonkeyPatch, cutoff: datetime, expected: str | None
) -> None:
    manifest = _instant_manifest()
    record = _trade_record(monkeypatch, available_at_instant="2026-03-01T15:00:00+00:00")
    if expected is None:
        assert _verify_trade(
            record,
            context=_context(manifest),
            custody=ByteCustody({REF: DOC_BYTES}),
            cutoff=cutoff,
        ).pit_admissible is True
    else:
        assert (
            _refusal(
                lambda: _verify_trade(
                    record,
                    context=_context(manifest),
                    custody=ByteCustody({REF: DOC_BYTES}),
                    cutoff=cutoff,
                )
            )
            == expected
        )


def test_sec_d28_offsets_compare_as_instants(monkeypatch: pytest.MonkeyPatch) -> None:
    instant = "2026-03-01T10:00:00-05:00"  # 15:00Z
    manifest = _instant_manifest(available_at_instant=instant)
    record = _trade_record(monkeypatch, available_at_instant=instant)
    before = datetime(2026, 3, 1, 14, 59, tzinfo=UTC)
    after = datetime(2026, 3, 1, 15, 0, tzinfo=UTC)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(manifest),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=before,
            )
        )
        == "APPROVAL_NOT_YET_AVAILABLE"
    )
    assert _verify_trade(
        record, context=_context(manifest), custody=ByteCustody({REF: DOC_BYTES}), cutoff=after
    ).pit_admissible is True


def test_sec_d29_dst_fall_back_orders_real_instants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """01:30-04:00 == 05:30Z; the repeated hour must not be flattened."""
    instant = "2026-11-01T01:30:00-04:00"
    manifest = _instant_manifest(available_at_instant=instant)
    _pin(monkeypatch, manifest)
    record = normalize_trade(
        _trade_payload(),
        registry=_issue(manifest, evaluation_at=datetime(2026, 11, 2, tzinfo=UTC)),
    )
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(manifest),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 11, 1, 5, 15, tzinfo=UTC),
            )
        )
        == "APPROVAL_NOT_YET_AVAILABLE"
    )
    assert _verify_trade(
        record,
        context=_context(manifest),
        custody=ByteCustody({REF: DOC_BYTES}),
        cutoff=datetime(2026, 11, 1, 5, 45, tzinfo=UTC),
    ).pit_admissible is True


def test_sec_d30_naive_inputs_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 6, 1, 12, 0),
            )
        )
        == "PIT_CUTOFF_REQUIRED"
    )
    manifest = _synthetic_manifest(available_at_instant="2026-03-01T15:00:00")
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _issue(manifest)
    assert caught.value.refusal.value == "MALFORMED_MANIFEST"


def test_sec_d31_an_approval_available_after_the_cutoff_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(available_at="2026-07-01")
    record = _trade_record(monkeypatch)  # normalised under the earlier root
    _pin(monkeypatch, manifest)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(manifest),
                custody=ByteCustody({REF: DOC_BYTES}),
                cutoff=CUTOFF,
            )
        )
        in {"APPROVAL_NOT_YET_AVAILABLE", "INTRADAY_PIT_AMBIGUOUS"}
    )


def test_sec_d32_evidence_acquisition_availability_is_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No acquisition instant exists in the record, so no claim is made."""
    record = _trade_record(monkeypatch)
    assert not hasattr(record, "acquisition_available_at_instant")
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=ByteCustody({REF: DOC_BYTES}),
    )
    assert "ACQUISITION_LINEAGE" in result.unverified_dimensions


# ---------------------------------------------------------------------------
# SEC-D33 .. SEC-D36 -- root, determinism and module hygiene
# ---------------------------------------------------------------------------


def test_sec_d33_the_shipped_root_still_admits_nothing() -> None:
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _issue(PRODUCTION_MANIFEST.read_bytes())
    assert caught.value.refusal.value in {"NO_APPROVAL", "ARTIFACT_NOT_APPROVED"}


def test_sec_d34_no_real_provider_approval_was_added() -> None:
    manifest = json.loads(PRODUCTION_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["artifacts"] == {}
    assert manifest["revoked_approval_ids"] == []


def test_sec_d35_verification_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    context = _context(_synthetic_manifest())
    first = _verify_trade(record, context=context, custody=ByteCustody({REF: DOC_BYTES}))
    second = _verify_trade(record, context=context, custody=ByteCustody({REF: DOC_BYTES}))
    assert first.model_dump() == second.model_dump()
    assert first.model_dump_json() == second.model_dump_json()


def test_sec_d36_the_sensor_layer_still_hashes_nothing() -> None:
    import inspect

    import crypto_sensor_fabric.normalization.sensors.verification as verification

    source = inspect.getsource(verification)
    assert "hashlib" not in source
    assert "crypto_sensor_fabric.providers" not in source
    assert "manifest_bytes=h" not in source
