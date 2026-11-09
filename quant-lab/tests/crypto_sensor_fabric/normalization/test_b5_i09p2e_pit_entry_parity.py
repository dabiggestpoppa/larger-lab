"""SENSOR-B5-I09P2e - PIT entry parity across every approval-admissibility verifier.

The P2dR1 independent audit measured that the record-level verifiers refuse an
approval carrying neither ``available_at`` nor ``available_at_instant``
(``PIT_AVAILABILITY_MISSING``) and refuse a date-only approval on its own day
(``INTRADAY_PIT_AMBIGUOUS``), while ``verify_mapping_provenance`` -- the entry
point a consumer uses to re-derive one field's admission -- admitted both.

These probes are the RED reproduction and then the regression law for that
inconsistency.  Every approval, registry and blob here is SYNTHETIC and labelled
as such: a synthetic root demonstrates the mechanism, it certifies no venue and
fabricates no provider document.

Boundary statement, deliberately tested rather than assumed: the approval LOADER
stays date-granular (``test_p2e_16_the_loader_is_not_the_pit_decision_point``).
A generic loader call is not a point-in-time decision; PIT claims must go
through the verification entry points, which now share one rule.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_RELPATH,
    MappingProvenance,
    SemanticAuthorityRefusal,
    load_trusted_authority,
    verify_liquidation_admission_provenance,
    verify_mapping_provenance,
)
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
PRODUCTION_MANIFEST = QUANT_LAB / TRUSTED_MANIFEST_RELPATH

DOC_BYTES = b"synthetic p2e venue document bytes (not a real provider document)"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2E_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ARTIFACT_ID = "registry-p2e.yaml"
APPROVAL_ID = "APPROVAL-SYNTHETIC-P2E"

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
    evidence_reference: SYNTHETIC_P2E_DOC_REF
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
    evidence_reference: SYNTHETIC_P2E_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()

#: A cutoff well AFTER every date-only availability used below.
LATER = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p2e-1",
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


def _manifest(
    *,
    available_at: str | None = None,
    available_at_instant: str | None = None,
    valid_until: str | None = "2027-01-01",
    revoked: tuple[str, ...] = (),
) -> bytes:
    entry: dict[str, object] = {
        "sha256": ARTIFACT_SHA,
        "approval_id": APPROVAL_ID,
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": valid_until,
        "allowed_methodologies": [METHOD_ID, LIQ_METHOD],
        "evidence": {
            "BINANCE_USDM": {"isBuyerMaker": [REF], "side": [REF]},
        },
        "declared_native_fields": {"BINANCE_USDM": ["isBuyerMaker", "side"]},
        "resolved_blocking_assumptions": [ASSUMPTION, LIQ_ASSUMPTION],
        "evidence_blobs": {REF: DOC_SHA},
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
            "revoked_approval_ids": list(revoked),
        }
    ).encode("utf-8")


def _pin(monkeypatch: pytest.MonkeyPatch, manifest: bytes) -> None:
    monkeypatch.setattr(
        authority_module,
        "TRUSTED_MANIFEST_SHA256",
        hashlib.sha256(manifest).hexdigest(),
    )


def _provenance(manifest: bytes) -> MappingProvenance:
    """The record-side claim, built from the approved row's own identity."""
    return MappingProvenance(
        artifact_id=ARTIFACT_ID,
        approval_id=APPROVAL_ID,
        registry_digest=ARTIFACT_SHA,
        provider="BINANCE_USDM",
        provider_field="isBuyerMaker",
        canonical_field="aggressor_side",
        canonical_sensor="MECHANICAL_TRADE",
        methodology_id=METHOD_ID,
        methodology_version="1",
        evidence_reference=REF,
        semantic_confidence="VERIFIED_SECONDARY",
    )


def _liquidation_admission(manifest: bytes) -> SimpleNamespace:
    """An admission-shaped object for the delegated liquidation entry point.

    ``verify_liquidation_admission_provenance`` accepts ``object`` and reads
    exactly these attributes before reconstructing the provenance from the
    approved row, so this probe drives the real delegation path.  Only the
    availability decision is under test here.
    """
    return SimpleNamespace(
        admitted=True,
        admission_approval_id=APPROVAL_ID,
        admission_registry_digest=ARTIFACT_SHA,
        canonical_field="position_side_liquidated",
        provider_field="side",
        methodology_id=LIQ_METHOD,
        mapping_version="1",
        evidence_reference=REF,
    )


def _refusal(call) -> str:
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        call()
    return caught.value.refusal.value


def _verify_mapping(manifest: bytes, cutoff: datetime | date | None) -> None:
    return verify_mapping_provenance(
        _provenance(manifest),
        manifest_bytes=manifest,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=cutoff,
    )


def _verify_liquidation(manifest: bytes, cutoff: datetime | date | None) -> None:
    return verify_liquidation_admission_provenance(
        _liquidation_admission(manifest),
        artifact_id=ARTIFACT_ID,
        manifest_bytes=manifest,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=cutoff,
    )


# ---------------------------------------------------------------------------
# RED reproduction -- these three invariants FAILED at f199a7e3
# ---------------------------------------------------------------------------


def test_p2e_01_missing_both_availability_fields_is_not_pit_admissible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F02: an availability-less approval was admissible at ANY cutoff."""
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    assert (
        _refusal(lambda: _verify_mapping(manifest, datetime(2026, 2, 1, tzinfo=UTC)))
        == "PIT_AVAILABILITY_MISSING"
    )


@pytest.mark.parametrize("hour", [0, 9, 15, 23])
def test_p2e_02_same_day_date_only_is_ambiguous_at_intraday_cutoffs(
    monkeypatch: pytest.MonkeyPatch, hour: int
) -> None:
    """The loader truncates the cutoff to a date and admitted 09:00 and 15:00."""
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    assert (
        _refusal(
            lambda: _verify_mapping(
                manifest, datetime(2026, 3, 1, hour, 30, tzinfo=UTC)
            )
        )
        == "INTRADAY_PIT_AMBIGUOUS"
    )


def test_p2e_03_a_naive_cutoff_cannot_establish_intraday_admissibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    assert (
        _refusal(lambda: _verify_mapping(manifest, datetime(2026, 6, 1, 12, 0)))
        == "EVALUATION_TIME_REQUIRED"
    )


# ---------------------------------------------------------------------------
# Laws that must keep holding
# ---------------------------------------------------------------------------


def test_p2e_04_a_later_day_is_admissible(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    _verify_mapping(manifest, datetime(2026, 3, 2, 0, 0, tzinfo=UTC))


def test_p2e_05_an_earlier_day_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    assert (
        _refusal(lambda: _verify_mapping(manifest, datetime(2026, 2, 28, tzinfo=UTC)))
        == "APPROVAL_NOT_YET_AVAILABLE"
    )


@pytest.mark.parametrize(
    "cutoff,expected",
    [
        (datetime(2026, 3, 1, 14, 59, tzinfo=UTC), "APPROVAL_NOT_YET_AVAILABLE"),
        (datetime(2026, 3, 1, 15, 0, tzinfo=UTC), None),
        (datetime(2026, 3, 1, 15, 1, tzinfo=UTC), None),
    ],
)
def test_p2e_06_instant_precision_boundaries(
    monkeypatch: pytest.MonkeyPatch, cutoff: datetime, expected: str | None
) -> None:
    manifest = _manifest(available_at_instant="2026-03-01T15:00:00+00:00")
    _pin(monkeypatch, manifest)
    if expected is None:
        _verify_mapping(manifest, cutoff)
    else:
        assert _refusal(lambda: _verify_mapping(manifest, cutoff)) == expected


def test_p2e_07_offset_representations_of_one_instant_agree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(available_at_instant="2026-03-01T10:00:00-05:00")  # 15:00Z
    _pin(monkeypatch, manifest)
    assert (
        _refusal(
            lambda: _verify_mapping(manifest, datetime(2026, 3, 1, 14, 59, tzinfo=UTC))
        )
        == "APPROVAL_NOT_YET_AVAILABLE"
    )
    _verify_mapping(manifest, datetime(2026, 3, 1, 15, 0, tzinfo=UTC))


def test_p2e_08_dst_repeated_hour_orders_real_instants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """01:30-04:00 == 05:30Z; the repeated local hour must not be flattened."""
    manifest = _manifest(available_at_instant="2026-11-01T01:30:00-04:00")
    _pin(monkeypatch, manifest)
    assert (
        _refusal(
            lambda: _verify_mapping(manifest, datetime(2026, 11, 1, 5, 15, tzinfo=UTC))
        )
        == "APPROVAL_NOT_YET_AVAILABLE"
    )
    _verify_mapping(manifest, datetime(2026, 11, 1, 5, 45, tzinfo=UTC))


def test_p2e_09_a_bare_date_cutoff_keeps_the_date_granular_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A date cutoff makes no intraday claim, so the frozen date law stands."""
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    _verify_mapping(manifest, date(2026, 3, 1))
    assert (
        _refusal(lambda: _verify_mapping(manifest, date(2026, 2, 28)))
        == "APPROVAL_NOT_YET_AVAILABLE"
    )


def test_p2e_10_no_cutoff_and_no_availability_is_not_a_pit_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approval authentication alone is still available, and is not a PIT claim."""
    manifest = _manifest(valid_until=None)
    _pin(monkeypatch, manifest)
    _verify_mapping(manifest, None)


def test_p2e_11_availability_without_a_cutoff_requires_the_instant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    assert (
        _refusal(lambda: _verify_mapping(manifest, None)) == "EVALUATION_TIME_REQUIRED"
    )


def test_p2e_12_revoked_and_expired_approvals_stay_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revoked = _manifest(available_at="2026-03-01", revoked=(APPROVAL_ID,))
    _pin(monkeypatch, revoked)
    assert _refusal(lambda: _verify_mapping(revoked, LATER)) == "APPROVAL_REVOKED"
    expired = _manifest(available_at="2026-03-01", valid_until="2026-02-01")
    _pin(monkeypatch, expired)
    assert _refusal(lambda: _verify_mapping(expired, LATER)) == "AUTHORITY_EXPIRED"


def test_p2e_13_a_substituted_manifest_is_not_an_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin(monkeypatch, _manifest(available_at="2026-03-01"))
    substitute = _manifest(available_at="2026-01-02")
    assert (
        _refusal(lambda: _verify_mapping(substitute, LATER)) == "TRUSTED_ROOT_MISMATCH"
    )


def test_p2e_14_the_shipped_root_admits_nothing() -> None:
    with pytest.raises(SemanticAuthorityRefusal) as caught:
        load_trusted_authority(
            manifest_bytes=PRODUCTION_MANIFEST.read_bytes(),
            artifact_id=ARTIFACT_ID,
            artifact_bytes=ARTIFACT,
            methodology_registry=_methodologies(),
            evaluation_at=LATER,
        )
    assert caught.value.refusal.value in {"NO_APPROVAL", "ARTIFACT_NOT_APPROVED"}


# ---------------------------------------------------------------------------
# Parity: every PIT verification entry point answers the same way
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,cutoff,expected",
    [
        ({}, datetime(2026, 2, 1, tzinfo=UTC), "PIT_AVAILABILITY_MISSING"),
        (
            {"available_at": "2026-03-01"},
            datetime(2026, 3, 1, 15, 0, tzinfo=UTC),
            "INTRADAY_PIT_AMBIGUOUS",
        ),
        ({"available_at": "2026-03-01"}, datetime(2026, 3, 2, tzinfo=UTC), None),
        (
            {"available_at_instant": "2026-03-01T15:00:00+00:00"},
            datetime(2026, 3, 1, 14, 0, tzinfo=UTC),
            "APPROVAL_NOT_YET_AVAILABLE",
        ),
    ],
)
def test_p2e_15_both_authority_entry_points_share_one_rule(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    cutoff: datetime,
    expected: str | None,
) -> None:
    manifest = _manifest(**kwargs)  # type: ignore[arg-type]
    _pin(monkeypatch, manifest)
    for call in (
        lambda: _verify_mapping(manifest, cutoff),
        lambda: _verify_liquidation(manifest, cutoff),
    ):
        if expected is None:
            call()
        else:
            assert _refusal(call) == expected


def test_p2e_16_the_loader_is_not_the_pit_decision_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Documented residual boundary, pinned so it cannot drift silently.

    The loader answers "were these bytes approved, as of this date"; it stays
    date-granular because the I05/I06 contracts pin that behaviour.  A PIT
    admissibility claim must therefore go through a verification entry point,
    which is where the one shared rule lives.
    """
    manifest = _manifest(available_at="2026-03-01")
    _pin(monkeypatch, manifest)
    authority = load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id=ARTIFACT_ID,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=datetime(2026, 3, 1, 15, 0, tzinfo=UTC),
    )
    assert authority.available_at == "2026-03-01"
    assert (
        _refusal(
            lambda: _verify_mapping(manifest, datetime(2026, 3, 1, 15, 0, tzinfo=UTC))
        )
        == "INTRADAY_PIT_AMBIGUOUS"
    )
