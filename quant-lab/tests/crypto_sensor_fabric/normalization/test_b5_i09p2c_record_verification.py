"""SENSOR-B5-I09P2c - full-record trusted verification (RED->REPAIR suite).

The R1 audit measured three holes this suite attacks directly:

* ``verify_mapping_provenance`` accepts only a ``MappingProvenance``, so a record
  whose canonical side was replaced verified clean (P2B-18/P2B-19 FAIL);
* ``verify_evidence_custody`` trusts a caller-authored ``{reference: digest}``
  map and reads no bytes (P2B-11 PARTIAL);
* the PIT gate truncates a ``datetime`` to ``.date()``, so an approval available
  on 2026-03-01 was admitted at 09:00 and 15:00 that day (P2B-12 PARTIAL).

Every fixture is labelled synthetic.  A synthetic approval proves the MECHANISM
under a test root; it certifies no venue and fabricates no provider document.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import UTC, datetime

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.contracts.enums import AggressorSide, SensorFamily
from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_RELPATH,
    MappingProvenance,
    SemanticAuthorityRefusal,
    load_trusted_authority,
)
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.sensors.liquidation import (
    LiquidationAggregationScope,
    LiquidationPositionSide,
    LiquidationRole,
    T1LiquidationRecord,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.sensors.side_maps import (
    apply_declared_side_transformation,
)
from crypto_sensor_fabric.normalization.sensors.trade import (
    T1TradeRecord,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.sensors.verification import (
    INTEGRATION_STATE,
    BlobStoreCustody,
    RecordVerification,
    RecordVerificationError,
    RecordVerificationRefusal,
    TrustedAuthorityContext,
    verify_liquidation_record,
    verify_trade_record,
)
from crypto_sensor_fabric.registry.provider_registry import PROVIDER_IDS
from crypto_sensor_fabric.storage import IntegrityState, LocalBlobStore, StorageEncoding

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
PRODUCTION_MANIFEST = QUANT_LAB / TRUSTED_MANIFEST_RELPATH

DOC_BYTES = b"synthetic venue document bytes (not a real provider document)"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2C_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ARTIFACT_ID = "registry-probe.yaml"
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

REGISTRY_TEXT = """schema_version: "9.9.9"
mappings:
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
    evidence_reference: SYNTHETIC_P2C_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
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
    evidence_reference: SYNTHETIC_P2C_DOC_REF
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
    evidence_reference: SYNTHETIC_P2C_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p2c-1",
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
    approval_id: str = "APPROVAL-SYNTHETIC-P2C",
    approved_transformations: dict[str, str] | None = None,
) -> bytes:
    entry = {
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
        "approved_transformations": approved_transformations or {},
        "resolved_blocking_assumptions": [ASSUMPTION, LIQ_ASSUMPTION],
    }
    if available_at is not None:
        entry["available_at"] = available_at
    if available_at_instant is not None:
        entry["available_at_instant"] = available_at_instant
    entry["evidence_blobs"] = (
        {REF: DOC_SHA} if evidence_blobs is None else evidence_blobs
    )
    return json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "PROBE_ROOT",
            "artifacts": {ARTIFACT_ID: entry},
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
    from crypto_sensor_fabric.normalization.sensors.side_maps import SideEvidence
    from crypto_sensor_fabric.normalization.sensors.trade import TradeObservationInput
    from crypto_sensor_fabric.storage import CoverageState, RevisionState

    payload: dict[str, object] = {
        "provider": "BINANCE_USDM",
        "venue": "BINANCE",
        "native_instrument": "BTCUSDT",
        "contract_instance_id": "BINANCE_USDM:BTCUSDT:PERP:2024-01",
        "native_event_id": "400001",
        "price_native": "61234.50",
        "quantity_native": "0.25000000",
        "quantity_native_unit": "BTC",
        "side_evidence": SideEvidence.provider_boolean(
            "isBuyerMaker", True, provider="BINANCE_USDM"
        ),
        "event_at": datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        "source_precision": TimestampPrecision.MILLISECOND,
        "source_revision_id": "rev-p2c-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p2c-1",
        "raw_projection_refs": ("proj:p2c:1",),
        "acquisition_refs": ("acq:p2c:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p2c",
        "config_version": "cfg-p2c",
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
        "liquidation_event_id": "liq-p2c-1",
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
        "source_revision_id": "rev-p2c-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p2c-1",
        "raw_projection_refs": ("proj:p2c:1",),
        "acquisition_refs": ("acq:p2c:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p2c",
        "config_version": "cfg-p2c",
    }
    payload.update(overrides)
    return LiquidationObservationInput(**payload)  # type: ignore[arg-type]


def _liq_record(monkeypatch: pytest.MonkeyPatch, **kwargs) -> T1LiquidationRecord:
    manifest = _synthetic_manifest(**kwargs)
    _pin(monkeypatch, manifest)
    return normalize_liquidation(_liq_payload(), registry=_issue(manifest))


class FakeCustody:
    """Test-only custody provider: an independently held BYTE store.

    SENSOR-B5-I09P2d: the fixture now holds bytes because the verifier hashes
    them; a fixture that held digests would be re-testing the defect.
    """

    def __init__(self, held: dict[str, bytes]) -> None:
        self._held = dict(held)

    def read_evidence(self, reference: str) -> bytes | None:
        return self._held.get(reference)


def _refusal(call) -> str:
    with pytest.raises(RecordVerificationError) as caught:
        call()
    return caught.value.refusal.value


def _verify_trade(record, *, context, custody=None, cutoff=CUTOFF):
    return verify_trade_record(
        record,
        trusted_context=context,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        knowledge_cutoff=cutoff,
        custody=custody,
    )


def _verify_liq(record, *, context, custody=None, cutoff=CUTOFF):
    return verify_liquidation_record(
        record,
        trusted_context=context,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        knowledge_cutoff=cutoff,
        custody=custody,
    )


# ---------------------------------------------------------------------------
# REC-01 / REC-24 -- authorized record, trusted context, no initializer
# ---------------------------------------------------------------------------


def test_rec_01_authorized_trade_record_verifies(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    assert record.aggressor_side is AggressorSide.SELL  # isBuyerMaker=true -> SELL
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
    )
    assert isinstance(result, RecordVerification)
    assert result.semantic_mapping_approved is True
    assert result.record_transformation_verified is True
    assert result.pit_admissible is True
    assert result.custody_verified is True
    assert result.downstream_trusted is True
    # Never a claim about provider authorship.
    assert result.source_lineage_verified is False
    assert "raw observation bytes are not reconstructible" in " ".join(result.notes)


def test_rec_24_trusted_context_refuses_an_actor_supplied_manifest() -> None:
    attacker = _synthetic_manifest(approval_id="ATTACKER-APPROVAL")
    assert _refusal(lambda: _context(attacker)) == "TRUSTED_CONTEXT_MISMATCH"
    assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"


def test_rec_24_the_reviewed_production_root_initializes_a_context() -> None:
    """The shipped manifest is the pinned root; it still approves nothing."""
    context = _context(PRODUCTION_MANIFEST.read_bytes())
    assert context.artifact_id == ARTIFACT_ID
    assert context.manifest_sha256 == authority_module.TRUSTED_MANIFEST_SHA256


# ---------------------------------------------------------------------------
# REC-02 .. REC-06 -- the record's own values are now in scope
# ---------------------------------------------------------------------------


def test_rec_02_flipped_canonical_side_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={"aggressor_side": AggressorSide.BUY})
    assert forged.authority_provenance == record.authority_provenance
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "CANONICAL_VALUE_MISMATCH"
    )


def test_rec_03_provider_substitution_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    other = next(p for p in sorted(PROVIDER_IDS) if p != "BINANCE_USDM")
    forged = record.model_copy(update={"provider": other})
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "PROVIDER_MISMATCH"
    )


def test_rec_04_instrument_substitution_is_outside_mapping_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The approval names no instrument, so the result must SAY it is unauthenticated."""
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={"native_instrument": "ETHUSDT"})
    result = _verify_trade(
        forged,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
    )
    assert result.instrument_authenticated is False
    assert any("instrument" in note for note in result.notes)


def test_rec_05_native_field_substitution_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={"native_side_field": "side"})
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "NATIVE_FIELD_MISMATCH"
    )


def test_rec_06_native_value_substitution_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={"native_side_boolean": False})
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "CANONICAL_VALUE_MISMATCH"
    )


# ---------------------------------------------------------------------------
# REC-07 .. REC-12 -- authority identity and out-of-scope facts
# ---------------------------------------------------------------------------


def test_rec_07_unapproved_transformation_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(
        approved_transformations={"isBuyerMaker": "SOME_OTHER_TRANSFORMATION"}
    )
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _issue(manifest)
    assert caught.value.refusal.value == "TRANSFORMATION_NOT_APPROVED"


def test_rec_07_no_executable_transformation_for_liquidation_fields() -> None:
    """A textual transformation is not executable proof: refuse, do not guess."""
    from crypto_sensor_fabric.normalization.common.semantic_registry import (
        parse_provider_semantic_registry_yaml,
    )

    registry = parse_provider_semantic_registry_yaml(ARTIFACT.decode("utf-8"))
    liquidation_row = registry.resolve("BINANCE_USDM", "side", SensorFamily.MECHANICAL_LIQUIDATION)
    assert liquidation_row is not None
    assert apply_declared_side_transformation(liquidation_row, "LONG") is None
    trade_row = registry.resolve("BINANCE_USDM", "isBuyerMaker", SensorFamily.MECHANICAL_TRADE)
    assert trade_row is not None
    assert apply_declared_side_transformation(trade_row, True) is AggressorSide.SELL
    assert apply_declared_side_transformation(trade_row, False) is AggressorSide.BUY


@pytest.mark.parametrize(
    "field,value",
    [
        ("approval_id", "ATTACKER-APPROVAL"),
        ("registry_digest", "0" * 64),
        ("methodology_id", "MINTED_BY_CALLER_V1"),
        ("evidence_reference", "SOME_OTHER_DOC"),
        ("semantic_confidence", "VERIFIED_FIRST_PARTY"),
    ],
)
def test_rec_08_to_11_mutated_provenance_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str
) -> None:
    record = _trade_record(monkeypatch)
    payload = record.authority_provenance.model_dump()
    payload[field] = value
    forged = record.model_copy(
        update={"authority_provenance": MappingProvenance.model_validate(payload)}
    )
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "PROVENANCE_MISMATCH"
    )


def test_rec_12_source_revision_is_preserved_not_authenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The approval binds provider/field/evidence, not the acquisition revision."""
    record = _trade_record(monkeypatch)
    forged = record.model_copy(update={"source_revision_id": "rev-attacker"})
    result = _verify_trade(
        forged,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
    )
    assert result.source_revision_authenticated is False


# ---------------------------------------------------------------------------
# REC-13 / REC-22 / REC-23 -- intraday PIT
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hour", [9, 12, 15, 23])
def test_rec_13_rec_22_same_day_intraday_cutoff_is_refused(
    monkeypatch: pytest.MonkeyPatch, hour: int
) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 3, 1, hour, 0, tzinfo=UTC),
            )
        )
        == "INTRADAY_PIT_AMBIGUOUS"
    )


def test_rec_13_a_later_day_is_admissible(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
        cutoff=datetime(2026, 3, 2, 0, 0, tzinfo=UTC),
    )
    assert result.pit_admissible is True


def test_rec_22_missing_or_naive_cutoff_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    context = _context(_synthetic_manifest())
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=context, custody=FakeCustody({REF: DOC_BYTES}), cutoff=None
            )
        )
        == "PIT_CUTOFF_REQUIRED"
    )
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=context,
                custody=FakeCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 6, 1, 12, 0),
            )
        )
        == "PIT_CUTOFF_REQUIRED"
    )


def test_rec_23_an_instant_precise_availability_is_honoured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kwargs = {"available_at_instant": "2026-03-01T15:00:00+00:00"}
    manifest = _synthetic_manifest(**kwargs)
    record = _trade_record(monkeypatch, **kwargs)
    okay = _verify_trade(
        record,
        context=_context(manifest),
        custody=FakeCustody({REF: DOC_BYTES}),
        cutoff=datetime(2026, 3, 1, 15, 5, tzinfo=UTC),
    )
    assert okay.pit_admissible is True
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(manifest),
                custody=FakeCustody({REF: DOC_BYTES}),
                cutoff=datetime(2026, 3, 1, 14, 55, tzinfo=UTC),
            )
        )
        == "APPROVAL_NOT_YET_AVAILABLE"
    )


def test_rec_23_an_instant_without_an_offset_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _synthetic_manifest(available_at_instant="2026-03-01T15:00:00")
    _pin(monkeypatch, manifest)
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        _issue(manifest)
    assert caught.value.refusal.value == "MALFORMED_MANIFEST"


# ---------------------------------------------------------------------------
# REC-14 .. REC-18 -- liquidation record verification
# ---------------------------------------------------------------------------


def test_rec_14_position_side_substitution_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    forged = record.model_copy(
        update={"position_side_liquidated": LiquidationPositionSide.SHORT}
    )
    assert (
        _refusal(
            lambda: _verify_liq(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "CANONICAL_VALUE_MISMATCH"
    )


def test_rec_15_execution_side_substitution_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    assert record.execution_side is AggressorSide.SELL
    forged = record.model_copy(update={"execution_side": AggressorSide.BUY})
    assert (
        _refusal(
            lambda: _verify_liq(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "CANONICAL_VALUE_MISMATCH"
    )


def test_rec_16_aggressor_side_without_an_admission_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    forged = record.model_copy(update={"aggressor_side": AggressorSide.BUY})
    assert (
        _refusal(
            lambda: _verify_liq(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "ADMISSION_MISSING"
    )


def test_rec_17_maker_taker_role_substitution_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    forged = record.model_copy(update={"maker_taker_role": LiquidationRole.MAKER})
    assert (
        _refusal(
            lambda: _verify_liq(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "ADMISSION_MISSING"
    )


def test_rec_18_wrong_provider_liquidation_record_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    other = next(p for p in sorted(PROVIDER_IDS) if p != "BINANCE_USDM")
    forged = record.model_copy(update={"provider": other})
    assert (
        _refusal(
            lambda: _verify_liq(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "PROVIDER_MISMATCH"
    )


def test_liquidation_reports_transformation_not_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    result = _verify_liq(
        record,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
    )
    assert result.semantic_mapping_approved is True
    assert result.record_transformation_verified is False
    assert result.downstream_trusted is False
    assert any("executable" in note for note in result.notes)


# ---------------------------------------------------------------------------
# REC-19 .. REC-21 -- trusted custody
# ---------------------------------------------------------------------------


def test_rec_19_missing_blob_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=FakeCustody({})
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_rec_20_a_caller_dictionary_is_not_a_custody_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    with pytest.raises(TypeError):
        _verify_trade(
            record,
            context=_context(_synthetic_manifest()),
            custody={REF: DOC_SHA},  # type: ignore[arg-type]
        )


def test_verification_without_custody_is_never_downstream_trusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    result = _verify_trade(record, context=_context(_synthetic_manifest()))
    assert result.custody_verified is False
    assert result.downstream_trusted is False


def test_rec_21_a_mutated_source_blob_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    store = LocalBlobStore(tmp_path)
    put = store.put_bytes(
        DOC_BYTES, storage_encoding=StorageEncoding.NONE, source_media_type="text/plain"
    )
    record = _trade_record(monkeypatch)
    intact = BlobStoreCustody(store, {REF: put.blob.blob_sha256})
    assert intact.held_digest(REF) == put.blob.blob_sha256
    okay = _verify_trade(
        record, context=_context(_synthetic_manifest()), custody=intact
    )
    assert okay.custody_verified is True
    # Mutate the stored object in place: the index still names the original hash.
    (tmp_path / put.object_key).write_bytes(b"tampered bytes")
    tampered = BlobStoreCustody(store, {REF: put.blob.blob_sha256})
    assert tampered.held_digest(REF) is None
    assert (
        _refusal(
            lambda: _verify_trade(
                record, context=_context(_synthetic_manifest()), custody=tampered
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_custody_binds_the_reference_the_approval_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    result = _verify_trade(
        record,
        context=_context(_synthetic_manifest()),
        custody=FakeCustody({REF: DOC_BYTES}),
    )
    assert result.custody_verified is True
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: b"other"}),
            )
        )
        == "CUSTODY_UNVERIFIED"
    )


def test_blob_store_custody_refuses_an_object_it_cannot_read(
    tmp_path: pathlib.Path,
) -> None:
    custody = BlobStoreCustody(LocalBlobStore(tmp_path), {REF: "0" * 64})
    assert custody.held_digest(REF) is None
    assert custody.held_digest("UNKNOWN_REF") is None
    assert IntegrityState.LOCAL_HASH_VERIFIED.value  # vocabulary sanity


# ---------------------------------------------------------------------------
# Forged construction, determinism, module hygiene
# ---------------------------------------------------------------------------


def test_forged_direct_construction_cannot_reach_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A caller-assembled record carrying a real approval id is still refused."""
    record = _trade_record(monkeypatch)
    forged = T1TradeRecord.model_validate(
        {
            **record.model_dump(),
            "aggressor_side": "BUY",
            "provisional_side": None,
        }
    )
    assert forged.aggressor_side is AggressorSide.BUY
    assert (
        _refusal(
            lambda: _verify_trade(
                forged,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "CANONICAL_VALUE_MISMATCH"
    )


def test_a_record_without_provenance_cannot_be_verified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin(monkeypatch, _synthetic_manifest())
    record = normalize_trade(_trade_payload())  # no authority: canonical UNKNOWN
    assert record.authority_provenance is None
    assert (
        _refusal(
            lambda: _verify_trade(
                record,
                context=_context(_synthetic_manifest()),
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "PROVENANCE_MISSING"
    )


def test_verification_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    context = _context(_synthetic_manifest())
    first = _verify_trade(record, context=context, custody=FakeCustody({REF: DOC_BYTES}))
    second = _verify_trade(record, context=context, custody=FakeCustody({REF: DOC_BYTES}))
    assert first.model_dump() == second.model_dump()


def test_verification_module_imports_no_provider_package() -> None:
    import inspect

    import crypto_sensor_fabric.normalization.sensors.verification as verification

    source = inspect.getsource(verification)
    assert "crypto_sensor_fabric.providers" not in source
    assert "providers/" not in source


def test_unknown_record_kind_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    assert (
        _refusal(
            lambda: verify_liquidation_record(
                record,  # type: ignore[arg-type]
                trusted_context=_context(_synthetic_manifest()),
                artifact_bytes=ARTIFACT,
                methodology_registry=_methodologies(),
                knowledge_cutoff=CUTOFF,
                custody=FakeCustody({REF: DOC_BYTES}),
            )
        )
        == "RECORD_KIND_MISMATCH"
    )


def test_the_verifier_takes_the_record_not_only_the_mapping() -> None:
    """Guard against reintroducing a record-blind verifier as the blessed API."""
    import inspect

    import crypto_sensor_fabric.normalization.sensors.verification as verification

    parameters = tuple(inspect.signature(verification.verify_trade_record).parameters)
    assert parameters[0] == "record"
    assert "trusted_context" in parameters
    assert "knowledge_cutoff" in parameters


def test_refusal_vocabulary_covers_the_measured_holes() -> None:
    members = {member.value for member in RecordVerificationRefusal}
    for required in (
        "CANONICAL_VALUE_MISMATCH",
        "NATIVE_FIELD_MISMATCH",
        "PROVIDER_MISMATCH",
        "INTRADAY_PIT_AMBIGUOUS",
        "CUSTODY_UNVERIFIED",
        "TRANSFORMATION_UNVERIFIABLE",
    ):
        assert required in members
