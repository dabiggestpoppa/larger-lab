"""SENSOR-B5-P3-R4 — temporal eligibility and evidence rebinding.

Verification hashes bytes at derivation time; consumption re-reads and re-hashes
them.  The gap between those two moments is the attack surface this suite
exercises, and the fixture that matters is ``FlipCustody``: it returns the
approved bytes for the verifier's read and different bytes for the consumer's
re-read.  A policy that trusted its own earlier read would accept; this one
refuses.

Ordering is also under test, not merely documented: PIT and replay are settled
*before* authority, so the suite asserts that a PIT-inadmissible or
replay-blocked request never even reaches the authority source
(``source.seen == []``).  That is a stronger claim than "it returned REFUSE".

No store-consistency guarantee is claimed or faked: the custody backend is a
keyed read, and a read that happens between two references is not atomic.  The
limitation is recorded in the evidence packet rather than hidden here.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import UTC, datetime
from typing import Any

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.normalization.authority import load_trusted_authority
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.consumer.custody_authority import (
    CustodyAuthorityBasis,
    CustodyAuthorityDerivation,
    CustodyAuthorityIdentity,
    custody_authority_identity_digest,
)
from crypto_sensor_fabric.normalization.consumer.models import (
    ConsumerDecision,
    ConsumerEvidenceReference,
    ConsumerRefusalReason,
    ConsumerRequest,
)
from crypto_sensor_fabric.normalization.consumer import policy as policy_module
from crypto_sensor_fabric.normalization.consumer.policy import TrustConsumerPolicy
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    LineageState,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.sensors.side_maps import SideEvidence
from crypto_sensor_fabric.normalization.sensors.trade import (
    T1TradeRecord,
    TradeObservationInput,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.time.enums import RevisionMode, RevisionStatus
from crypto_sensor_fabric.normalization.time.replay_gate import ReplayEvidence
from crypto_sensor_fabric.normalization.time.revision_policy import (
    RevisionRecord,
    RevisionSelection,
)
from crypto_sensor_fabric.storage import CoverageState, RevisionState

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
PRODUCTION_MANIFEST = (
    QUANT_LAB
    / "config"
    / "crypto_sensor_fabric"
    / "provider_semantics"
    / "approval_manifest.json"
)

DOC_BYTES = b"synthetic venue document bytes (not a real provider document)"
TAMPERED_BYTES = b"tampered bytes that still hash to something"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P3_DOC_REF"
OTHER_REF = "OTHER_RECORD_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
ARTIFACT_ID = "registry-p3-rebind.yaml"
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
    evidence_reference: SYNTHETIC_P3_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p3-4",
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
                }
            ],
        }
    )


def _manifest(**overrides: Any) -> bytes:
    entry: dict[str, Any] = {
        "sha256": ARTIFACT_SHA,
        "approval_id": "APPROVAL-SYNTHETIC-P3",
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": "2027-01-01",
        "available_at": "2026-03-01",
        "evidence_blobs": {REF: DOC_SHA},
        "allowed_methodologies": [METHOD_ID],
        "evidence": {"BINANCE_USDM": {"isBuyerMaker": [REF]}},
        "declared_native_fields": {"BINANCE_USDM": ["isBuyerMaker"]},
        "approved_transformations": {},
        "resolved_blocking_assumptions": [ASSUMPTION],
    }
    entry.update(overrides)
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
        authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(manifest).hexdigest()
    )


def _trade_record(monkeypatch: pytest.MonkeyPatch) -> T1TradeRecord:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    authority = load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id=ARTIFACT_ID,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=CUTOFF,
    )
    payload = TradeObservationInput.model_validate(
        {
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
            "source_revision_id": "rev-p3-4",
            "source_revision_state": RevisionState.STABLE,
            "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
            "normalization_generation": "gen-p3-4",
            "raw_projection_refs": ("proj:p3:4",),
            "acquisition_refs": ("acq:p3:4",),
            "evidence_blob_hashes": (DOC_SHA,),
            "code_version": "p3",
            "config_version": "cfg-p3",
        }
    )
    return normalize_trade(payload, registry=authority)


class HeldCustody:
    def __init__(self, held: dict[str, bytes] | None = None) -> None:
        self._held = {REF: DOC_BYTES} if held is None else dict(held)
        self.reads: list[str] = []

    def read_evidence(self, reference: str) -> bytes | None:
        self.reads.append(reference)
        return self._held.get(reference)


class FlipCustody:
    """Correct bytes for the verifier's read, other bytes for the re-read.

    This is the time-of-check/time-of-use seam the design warns about, made
    explicit: a policy that reused its first read would accept.
    """

    def __init__(self, first: bytes | None, later: bytes | None) -> None:
        self._payloads = (first, later)
        self.reads: list[str] = []

    def read_evidence(self, reference: str) -> bytes | None:
        self.reads.append(reference)
        return self._payloads[0] if len(self.reads) == 1 else self._payloads[1]


def _replay_evidence(**overrides: Any) -> ReplayEvidence:
    payload: dict[str, Any] = {
        "identity_pit_resolved": True,
        "timestamp_semantics_verified": True,
        "source_evidence_refs": ("SYNTHETIC_TIMESTAMP_DOC",),
        "availability_basis": AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        "availability_confidence": "VERIFIED_SECONDARY",
        "market_available_at": datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        "interval_complete": True,
        "revision": RevisionSelection(
            mode=RevisionMode.AS_KNOWN_THEN,
            selected=(
                RevisionRecord(
                    source_revision_id="rev-p3-4",
                    normalization_generation=1,
                    supersedes_t1_record_id=None,
                    revision_status=RevisionStatus.ORIGINAL,
                    known_from=datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
                    known_to=None,
                ),
            ),
            excluded=(),
            pit_safe=True,
            pit_uncertain=False,
        ),
        "lineage": LineageState.LINEAGE_COMPLETE,
        "quality_flags": (),
    }
    payload.update(overrides)
    return ReplayEvidence.model_validate(payload)


def _evidence(*references: ConsumerEvidenceReference) -> tuple[ConsumerEvidenceReference, ...]:
    return references


def _ref(reference: str = REF, digest: str = DOC_SHA) -> ConsumerEvidenceReference:
    return ConsumerEvidenceReference(reference=reference, approved_digest=digest)


def _request(record: Any, **overrides: Any) -> ConsumerRequest:
    payload: dict[str, Any] = {
        "record": record,
        "artifact_bytes": ARTIFACT,
        "evidence_references": (_ref(),),
        "knowledge_cutoff": CUTOFF,
        "replay_evidence": _replay_evidence(),
    }
    payload.update(overrides)
    return ConsumerRequest(**payload)


class _RecordingSource:
    """Wiring double that records whether authority was even consulted."""

    def __init__(self, basis: CustodyAuthorityBasis) -> None:
        self._basis = basis
        self.seen: list[CustodyAuthorityIdentity] = []

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        self.seen.append(identity)
        return CustodyAuthorityDerivation(
            basis=self._basis,
            detail="fixture basis",
            identity_sha256=(
                custody_authority_identity_digest(identity)
                if self._basis is CustodyAuthorityBasis.AUTHORIZED
                else None
            ),
        )


def _policy(manifest: bytes, *, custody: Any = None, source: Any = None) -> TrustConsumerPolicy:
    return TrustConsumerPolicy(
        manifest_bytes=manifest,
        methodology_registry=_methodologies(),
        custody=HeldCustody() if custody is None else custody,
        authority_source=source,
    )


# ---------------------------------------------------------------------------
# A4.1 -- evidence bytes, re-read at consumption
# ---------------------------------------------------------------------------


def test_the_happy_path_rebinds_and_stops_at_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    policy = _policy(manifest, custody=HeldCustody())
    verdict = policy.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert verdict.custody_status == "VERIFIED"


def test_bytes_replaced_after_verification_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = FlipCustody(DOC_BYTES, TAMPERED_BYTES)
    verdict = _policy(manifest, custody=custody).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH
    assert len(custody.reads) >= 2  # the verifier read, then the consumer re-read


def test_bytes_removed_after_verification_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    verdict = _policy(manifest, custody=FlipCustody(DOC_BYTES, None)).evaluate(
        _request(record)
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.EVIDENCE_BYTES_MISSING


def test_digest_only_custody_is_not_custody(monkeypatch: pytest.MonkeyPatch) -> None:
    """A custody object that reports the right digest but holds no bytes."""
    record = _trade_record(monkeypatch)
    manifest = _manifest()

    class _DigestOnly:
        def read_evidence(self, reference: str) -> bytes | None:
            return None

    verdict = _policy(manifest, custody=_DigestOnly()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.custody_status == "UNVERIFIED"


def test_a_caller_digest_that_does_not_match_the_bytes_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    # The bytes are the approved ones; the CALLER's claim is wrong.
    verdict = _policy(manifest, custody=HeldCustody()).evaluate(
        _request(record, evidence_references=(_ref(digest="9" * 64),))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH


def test_evidence_bound_to_another_artifact_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Intact bytes, wrong record: cross-record reuse, not a digest mismatch."""
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = HeldCustody({REF: DOC_BYTES, OTHER_REF: DOC_BYTES})
    verdict = _policy(manifest, custody=custody).evaluate(
        _request(record, evidence_references=(_ref(OTHER_REF), _ref()))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.EVIDENCE_NOT_BOUND_TO_ARTIFACT


def test_each_evidence_reference_is_read_once_by_rebinding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A4.5: no unbounded reads.  Two reads per reference: derive, then rebind."""
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = HeldCustody()
    _policy(manifest, custody=custody).evaluate(_request(record))
    assert custody.reads.count(REF) == 2, custody.reads


# ---------------------------------------------------------------------------
# A4.2/A4.3 -- replay and PIT are settled before authority
# ---------------------------------------------------------------------------


def test_an_incomplete_interval_blocks_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    verdict = _policy(manifest, source=source).evaluate(
        _request(record, replay_evidence=_replay_evidence(interval_complete=False))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert verdict.replay_status != "ELIGIBLE"
    assert source.seen == []  # authority was never consulted


def test_an_unresolved_identity_blocks_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    verdict = _policy(manifest, source=source).evaluate(
        _request(record, replay_evidence=_replay_evidence(identity_pit_resolved=False))
    )
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert source.seen == []


def test_a_forged_eligibility_below_the_manifest_is_still_checked_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the SHIPPED manifest, replay is still adjudicated before authority."""
    record = _trade_record(monkeypatch)
    shipped = PRODUCTION_MANIFEST.read_bytes()
    monkeypatch.setattr(authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(shipped).hexdigest())
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    policy = TrustConsumerPolicy(
        manifest_bytes=shipped,
        methodology_registry=_methodologies(),
        custody=HeldCustody(),
        authority_source=source,
    )
    verdict = policy.evaluate(
        _request(record, replay_evidence=_replay_evidence(interval_complete=False))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert source.seen == []


def test_a_record_whose_approval_was_not_operative_is_pit_inadmissible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    early = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)
    verdict = _policy(manifest, source=source).evaluate(
        _request(record, knowledge_cutoff=early)
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE
    assert source.seen == []


def test_pit_inadmissibility_is_not_repaired_by_custody(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The row A17 exists for: good custody must not rescue a bad instant."""
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    verdict = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(
        _request(record, knowledge_cutoff=datetime(2026, 2, 1, 12, 0, tzinfo=UTC))
    )
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.custody_source_authorized is False


# ---------------------------------------------------------------------------
# The decision table, row by row
# ---------------------------------------------------------------------------


def test_the_accept_row_requires_every_prerequisite(monkeypatch: pytest.MonkeyPatch) -> None:
    """The accepting row, reachable only once the record binding is minted.

    Every claim the frozen schema carries is satisfied below (custody, PIT,
    replay, an authorization bound to this identity), and the row still
    terminates in ``INTEGRATION_REQUIRED`` naming
    ``REPLAY_EVIDENCE_RECORD_BINDING_V1``.  The guard is then flipped to the
    state a minted contract would create, which is the only route to the
    accepting row -- so the row needs the FOURTH claim as well.
    """
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    held = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert held.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert held.custody_status == "VERIFIED"  # the other claims DID hold
    assert policy_module.REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT in (
        held.custody_authorization_detail or ""
    )

    monkeypatch.setattr(policy_module, "REPLAY_RECORD_BINDING_ESTABLISHED", True)
    verdict = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.custody_status == "VERIFIED"
    assert verdict.pit_status == "ADMISSIBLE"
    assert verdict.replay_status == "ELIGIBLE"
    assert verdict.custody_source_authorized is True


def test_the_integration_row_is_not_a_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    verdict = _policy(manifest).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert verdict.refusal_reason is None
    assert "OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1" in (
        verdict.custody_authorization_detail or ""
    )


def test_the_unauthorized_row_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    verdict = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.UNAUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE


def test_a_custody_failure_outranks_a_granted_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    verdict = _policy(
        manifest, custody=FlipCustody(DOC_BYTES, None),
        source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED),
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


# ---------------------------------------------------------------------------
# A16 -- nothing is cached between consumptions
# ---------------------------------------------------------------------------


def test_a_second_consumption_re_derives_and_re_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = HeldCustody()
    policy = _policy(manifest, custody=custody)
    first = policy.evaluate(_request(record))
    second = policy.evaluate(_request(record))
    assert first.model_dump() == second.model_dump()
    assert custody.reads.count(REF) == 4  # two per consumption, never one

    custody._held.pop(REF)  # the store changes between consumptions
    third = policy.evaluate(_request(record))
    assert third.decision is ConsumerDecision.REFUSE
    # The blob is already gone when derivation starts, so the VERIFIER's custody
    # check fires first (CUSTODY_UNVERIFIED).  Rebinding owns the other window:
    # bytes that disappear between derivation and consumption (FlipCustody).
    assert third.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert third.custody_status == "UNVERIFIED"
    assert "CUSTODY_UNVERIFIED" in (third.refusal_detail or "")


# ---------------------------------------------------------------------------
# H02 -- replay evidence must belong to THIS consumption
# ---------------------------------------------------------------------------


def _selection(
    revision_id: str,
    *,
    known_from: datetime | None = None,
    exclude: bool = False,
) -> RevisionSelection:
    item = RevisionRecord(
        source_revision_id=revision_id,
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=known_from or datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        known_to=None,
    )
    return RevisionSelection(
        mode=RevisionMode.AS_KNOWN_THEN,
        selected=() if exclude else (item,),
        excluded=(item,) if exclude else (),
        pit_safe=True,
        pit_uncertain=exclude,
    )


def test_h02_eligible_evidence_from_an_unrelated_record_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The I05 gate answers \"is this eligible\"; it cannot answer \"whose\"."""
    record = _trade_record(monkeypatch)
    control = _policy(_manifest()).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED  # row is fine

    foreign = _replay_evidence(revision=_selection("rev-of-another-record"))
    verdict = _policy(_manifest()).evaluate(
        _request(record, replay_evidence=foreign)
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert verdict.replay_status == "NOT_BOUND"
    assert "rev-of-another-record" in (verdict.refusal_detail or "")
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_h02_evidence_selected_at_a_later_cutoff_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    later = _replay_evidence(
        revision=_selection("rev-p3-4", known_from=datetime(2026, 7, 1, tzinfo=UTC))
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=later))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE


def test_h02_a_revision_excluded_at_the_cutoff_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An eligible-looking selection that WITHHELD this record's own revision.

    ``pit_uncertain`` is False and another revision is selected, so the I05 gate
    answers ELIGIBLE: eligibility alone cannot see that the row under evaluation
    is the one that was excluded.
    """
    record = _trade_record(monkeypatch)
    mine = RevisionRecord(
        source_revision_id="rev-p3-4",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        known_to=None,
    )
    other = RevisionRecord(
        source_revision_id="rev-p3-4-corrected",
        normalization_generation=2,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.PROVIDER_CORRECTED,
        known_from=datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        known_to=None,
    )
    withheld = _replay_evidence(
        revision=RevisionSelection(
            mode=RevisionMode.AS_KNOWN_THEN,
            selected=(other,),
            excluded=(mine,),
            pit_safe=True,
            pit_uncertain=False,
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=withheld))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE
    assert "excludes revision" in (verdict.refusal_detail or "")


def test_h02_evidence_not_yet_market_available_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    unborn = _replay_evidence(market_available_at=datetime(2026, 7, 1, tzinfo=UTC))
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=unborn))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE


def test_h02_evidence_contradicting_the_records_availability_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The record declares one instant; the evidence claims another."""
    record = _trade_record(monkeypatch)
    declared = record.time.model_copy(
        update={
            "market_available_at": datetime(2026, 5, 30, 0, 0, tzinfo=UTC),
            "availability_basis": AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        }
    )
    altered = record.model_copy(update={"time": declared})
    verdict = _policy(_manifest()).evaluate(_request(altered))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert "market-availability" in (verdict.refusal_detail or "")


def test_h02_removing_the_binding_lets_foreign_evidence_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutation control: the binding is what refuses the foreign row."""
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    foreign = _replay_evidence(revision=_selection("rev-of-another-record"))

    guarded = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record, replay_evidence=foreign))
    assert guarded.decision is ConsumerDecision.REFUSE

    monkeypatch.setattr(TrustConsumerPolicy, "_bind_replay", lambda self, *args: None)
    monkeypatch.setattr(policy_module, "REPLAY_RECORD_BINDING_ESTABLISHED", True)
    mutated = _policy(
        manifest, source=_RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record, replay_evidence=foreign))
    assert mutated.decision is ConsumerDecision.ACCEPT_FIELD_BINDING  # forbidden


# ---------------------------------------------------------------------------
# F4 -- the cutoff law orders EVERY selected revision
# (SENSOR-B5-P3-R6-F4-F5-CLOSURE-R1; Agent 2 counterexample F4)
# ---------------------------------------------------------------------------

#: One selected revision, with an explicit knowledge instant.
def _revision(
    revision_id: str, *, known_from: datetime | None = None, generation: int = 1
) -> RevisionRecord:
    return RevisionRecord(
        source_revision_id=revision_id,
        normalization_generation=generation,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=known_from or datetime(2026, 5, 31, 23, 59, tzinfo=UTC),
        known_to=None,
    )


def _selection_of(
    *items: RevisionRecord, excluded: tuple[RevisionRecord, ...] = ()
) -> RevisionSelection:
    return RevisionSelection(
        mode=RevisionMode.AS_KNOWN_THEN,
        selected=tuple(items),
        excluded=excluded,
        pit_safe=True,
        pit_uncertain=False,
    )


def test_f4_a_second_selected_revision_known_after_the_cutoff_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Agent 2's F4 counterexample, exactly: chosen revision early, another late.

    ``_bind_replay`` ordered only ``selected[record_revision]`` against the
    cutoff, so this selection -- computed for a 2026-09 replay -- certified a
    2026-06 consumption and reached ``ACCEPT_FIELD_BINDING``.
    """
    record = _trade_record(monkeypatch)
    evidence = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4"),
            _revision("rev-LATER", known_from=datetime(2026, 9, 1, tzinfo=UTC)),
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=evidence))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE
    assert verdict.replay_status == "NOT_BOUND"
    assert "rev-LATER" in (verdict.refusal_detail or "")


def test_f4_a_valid_multi_revision_selection_still_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Positive control: closing F4 must not become a blanket refusal.

    Three selected revisions, every one known by the cutoff -- including one
    known EXACTLY at it, which the existing temporal law admits.
    """
    record = _trade_record(monkeypatch)
    evidence = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4"),
            _revision("rev-audit-2", known_from=datetime(2026, 5, 1, tzinfo=UTC)),
            _revision("rev-audit-3", known_from=CUTOFF),
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=evidence))
    assert verdict.decision is not ConsumerDecision.REFUSE, verdict.refusal_detail
    assert verdict.replay_status == "ELIGIBLE"
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED


def test_f4_equivalent_offsets_behave_identically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same instant in another offset is the same instant, and one second
    later is later -- the sweep compares instants, not wall-clock text."""
    from datetime import timedelta, timezone

    record = _trade_record(monkeypatch)
    plus_nine = timezone(timedelta(hours=9))
    minus_five = timezone(timedelta(hours=-5))

    same = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4"),
            _revision("rev-audit-2", known_from=datetime(2026, 6, 1, 21, 0, tzinfo=plus_nine)),
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=same))
    assert verdict.decision is not ConsumerDecision.REFUSE, verdict.refusal_detail

    later = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4"),
            _revision("rev-audit-2", known_from=datetime(2026, 6, 1, 7, 0, 1, tzinfo=minus_five)),
        )
    )
    late_verdict = _policy(_manifest()).evaluate(
        _request(record, replay_evidence=later)
    )
    assert late_verdict.decision is ConsumerDecision.REFUSE
    assert late_verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE


def test_f4_a_duplicate_selected_identity_cannot_hide_a_late_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The id-keyed view would keep the LAST entry; the sequence is authoritative.

    Ordering here is (late, early) for the same id, so a dict built over the
    entries kept the early one and the late entry was never read.
    """
    record = _trade_record(monkeypatch)
    evidence = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4", known_from=datetime(2026, 9, 1, tzinfo=UTC)),
            _revision("rev-p3-4"),
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=evidence))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert "more than once" in (verdict.refusal_detail or "")


def test_f4_a_selected_entry_cannot_also_be_excluded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """selected ∪ excluded is empty; a self-contradicting selection proves nothing."""
    record = _trade_record(monkeypatch)
    mine = _revision("rev-p3-4")
    evidence = _replay_evidence(
        revision=_selection_of(mine, excluded=(_revision("rev-p3-4"),))
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=evidence))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert "BOTH selected and excluded" in (verdict.refusal_detail or "")


def test_f4_entry_order_cannot_change_the_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    early = _revision("rev-audit-2", known_from=datetime(2026, 5, 1, tzinfo=UTC))
    late = _revision("rev-LATER", known_from=datetime(2026, 9, 1, tzinfo=UTC))
    chosen = _revision("rev-p3-4")

    outcomes = []
    for items in ((chosen, early, late), (late, chosen, early), (early, late, chosen)):
        verdict = _policy(_manifest()).evaluate(
            _request(record, replay_evidence=_replay_evidence(revision=_selection_of(*items)))
        )
        outcomes.append(
            (verdict.decision, verdict.refusal_reason, verdict.replay_status)
        )
    assert len(set(outcomes)) == 1, outcomes
    assert outcomes[0][0] is ConsumerDecision.REFUSE
    assert outcomes[0][1] is ConsumerRefusalReason.PIT_INADMISSIBLE


def test_f4_a_malformed_non_chosen_selected_instant_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A malformed entry that is not the chosen one is still evidence to order.

    Driven at the seam: the request revalidation normally refuses such a
    selection first, and this proves the binding itself does not treat an
    unorderable entry as if it were absent.
    """
    record = _trade_record(monkeypatch)
    broken = RevisionRecord.model_construct(
        source_revision_id="rev-broken",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from="not-an-instant",
        known_to=None,
    )
    evidence = _replay_evidence(
        revision=_selection_of(_revision("rev-p3-4"), broken)
    )
    refusal = _policy(_manifest())._bind_replay(  # noqa: SLF001
        evidence, record, CUTOFF
    )
    assert refusal is not None
    reason, detail = refusal
    assert reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert "not a timestamp" in detail


def test_f4_an_excluded_future_revision_needs_no_cutoff_instant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exclusion evidence is retained BECAUSE it was not knowable here.

    Ordering the excluded half against the cutoff would delete the evidence of
    the exclusion, which is the opposite of the requirement.
    """
    record = _trade_record(monkeypatch)
    evidence = _replay_evidence(
        revision=_selection_of(
            _revision("rev-p3-4"),
            excluded=(
                _revision("rev-FUTURE", known_from=datetime(2026, 12, 1, tzinfo=UTC)),
            ),
        )
    )
    verdict = _policy(_manifest()).evaluate(_request(record, replay_evidence=evidence))
    assert verdict.decision is not ConsumerDecision.REFUSE, verdict.refusal_detail
    assert verdict.replay_status == "ELIGIBLE"


def test_f1_the_unresolved_binding_guard_is_executable_and_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F1 residual: four distinct claims, and the fourth is not establishable."""
    assert policy_module.REPLAY_RECORD_BINDING_ESTABLISHED is False
    assert len(policy_module.REPLAY_BINDING_CLAIMS) == 4
    assert set(policy_module.REPLAY_BINDING_CLAIMS) == {
        "TEMPORAL_ELIGIBILITY",
        "REVISION_IDENTITY_COMPATIBILITY",
        "RECORD_PROVIDER_ARTIFACT_BINDING",
        "AUTHORITY_TO_CONSUME",
    }

    record = _trade_record(monkeypatch)
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    held = _policy(_manifest(), source=source).evaluate(_request(record))
    assert held.decision is ConsumerDecision.INTEGRATION_REQUIRED
    detail = held.custody_authorization_detail or ""
    assert policy_module.REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT in detail
    assert "met:" in detail  # the claims that DID hold are named, not collapsed

    # M-BIND: flipping the guard alone makes the unsupported acceptance
    # reachable again, which is what makes it a guard rather than prose.
    monkeypatch.setattr(policy_module, "REPLAY_RECORD_BINDING_ESTABLISHED", True)
    unsupported = _policy(_manifest(), source=source).evaluate(_request(record))
    assert unsupported.decision is ConsumerDecision.ACCEPT_FIELD_BINDING


# ---------------------------------------------------------------------------
# H05 -- one evidence snapshot, two measured reads
# ---------------------------------------------------------------------------


def test_h05_both_reads_are_of_the_same_approved_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    custody = HeldCustody()
    source = _RecordingSource(CustodyAuthorityBasis.AUTHORIZED)
    verdict = _policy(_manifest(), custody=custody, source=source).evaluate(
        _request(record)
    )
    # The terminal outcome is the record-binding gate (F1 residual); the two
    # measured reads and the identity the source saw are independent of it.
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert custody.reads == [REF, REF]  # derivation, then the consumption re-read
    assert source.seen[-1].artifact_id == ARTIFACT_ID
    assert verdict.custody_status == "VERIFIED"


def test_h05_an_omitted_reference_is_not_silently_re_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No claim, no second read -- measured rather than assumed."""
    record = _trade_record(monkeypatch)
    custody = HeldCustody()
    verdict = _policy(_manifest(), custody=custody).evaluate(
        _request(record, evidence_references=())
    )
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    # Measured, not assumed: one read, because the caller made no second claim.
    # The window between the verifier's read and consumption is therefore
    # unobserved -- there is nothing to compare against (A4.5's honest limit).
    assert custody.reads == [REF]
