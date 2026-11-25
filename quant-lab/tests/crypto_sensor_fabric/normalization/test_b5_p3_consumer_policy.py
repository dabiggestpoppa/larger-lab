"""SENSOR-B5-P3-R2 — policy-owned verification derivation.

The question this suite answers is not "does the policy return the right words"
but "can a caller put a verdict, a callback or an approval into the intake
path".  Every attack below is executed against the real
:class:`TrustConsumerPolicy`, and every passing control is paired with a
positive control on the identical fixture, so "it refuses everything" cannot
pass the file.

**The authoritative production state.**  The shipped manifest approves nothing,
so the production path returns ``INTEGRATION_REQUIRED`` for every input.  That
is asserted directly (``test_shipped_manifest_yields_integration_required``).

**The fixture root.**  To exercise anything beyond that first refusal the tests
pin a *synthetic* reviewed root the way the I09P2b–I09P2e suites already do
(``monkeypatch`` on ``TRUSTED_MANIFEST_SHA256``): a labelled approval of a
labelled synthetic registry, over a labelled synthetic evidence blob.  It
certifies no venue and fabricates no provider document.  Under that root the
pipeline runs to the authority boundary and stops there, because the missing
operator custody-source authority record is not something a test may invent.
The one branch a fixture *can* open is the wiring double in
``_FixedAuthoritySource``, which is a test object, never a production basis.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import pathlib
from datetime import UTC, datetime
from typing import Any

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.contracts.enums import AggressorSide, SensorFamily
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.consumer.custody_authority import (
    CustodyAuthorityBasis,
    CustodyAuthorityDerivation,
    CustodyAuthorityIdentity,
    ManifestCustodyAuthority,
    UNRESOLVED_AUTHORITY_CONTRACT,
)
from crypto_sensor_fabric.normalization.consumer.models import (
    ConsumerDecision,
    ConsumerRefusalReason,
    ConsumerRequest,
    ConsumerVerdict,
)
from crypto_sensor_fabric.normalization.consumer.policy import TrustConsumerPolicy
from crypto_sensor_fabric.normalization.sensors.liquidation import (
    LiquidationAggregationScope,
    LiquidationPositionSide,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.sensors.trade import (
    T1TradeRecord,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.time.replay_gate import ReplayEvidence
from crypto_sensor_fabric.normalization.time.revision_policy import (
    RevisionRecord,
    RevisionSelection,
)
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    LineageState,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.time.enums import RevisionMode, RevisionStatus
from crypto_sensor_fabric.registry.provider_registry import PROVIDER_IDS
from crypto_sensor_fabric.storage import CoverageState, RevisionState

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
POLICY_PATH = (
    QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "consumer" / "policy.py"
)
PRODUCTION_MANIFEST = (
    QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_semantics" / "approval_manifest.json"
)

DOC_BYTES = b"synthetic venue document bytes (not a real provider document)"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P3_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ARTIFACT_ID = "registry-p3-policy.yaml"
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
    evidence_reference: SYNTHETIC_P3_DOC_REF
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
    evidence_reference: SYNTHETIC_P3_DOC_REF
    semantic_confidence: VERIFIED_SECONDARY
    last_verified_date: "2026-01-01"
    version: "1"
"""

ARTIFACT = REGISTRY_TEXT.encode("utf-8")
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()


# ---------------------------------------------------------------------------
# Synthetic fixtures (no normalizer result is asserted as provider truth)
# ---------------------------------------------------------------------------


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p3-1",
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


def _manifest(**overrides: Any) -> bytes:
    entry: dict[str, Any] = {
        "sha256": ARTIFACT_SHA,
        "approval_id": "APPROVAL-SYNTHETIC-P3",
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": "2027-01-01",
        "available_at": "2026-03-01",
        "evidence_blobs": {REF: DOC_SHA},
        "allowed_methodologies": [METHOD_ID, LIQ_METHOD],
        "evidence": {
            "BINANCE_USDM": {
                "isBuyerMaker": [REF],
                "side": [REF],
                "side_exec": [REF],
            }
        },
        "declared_native_fields": {"BINANCE_USDM": ["isBuyerMaker", "side", "side_exec"]},
        "approved_transformations": {},
        "resolved_blocking_assumptions": [ASSUMPTION, LIQ_ASSUMPTION],
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
        authority_module,
        "TRUSTED_MANIFEST_SHA256",
        hashlib.sha256(manifest).hexdigest(),
    )


def _authority(manifest: bytes):
    from crypto_sensor_fabric.normalization.authority import load_trusted_authority

    return load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id=ARTIFACT_ID,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=CUTOFF,
    )


def _trade_payload(**overrides: Any) -> Any:
    from crypto_sensor_fabric.normalization.sensors.side_maps import SideEvidence
    from crypto_sensor_fabric.normalization.sensors.trade import TradeObservationInput

    payload: dict[str, Any] = {
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
        "source_revision_id": "rev-p3-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p3-1",
        "raw_projection_refs": ("proj:p3:1",),
        "acquisition_refs": ("acq:p3:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p3",
        "config_version": "cfg-p3",
    }
    payload.update(overrides)
    return TradeObservationInput.model_validate(payload)


def _trade_record(monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> T1TradeRecord:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    return normalize_trade(_trade_payload(), registry=_authority(manifest))


def _liq_payload(**overrides: Any) -> Any:
    from crypto_sensor_fabric.normalization.sensors.liquidation import (
        LiquidationObservationInput,
    )

    payload: dict[str, Any] = {
        "provider": "BINANCE_USDM",
        "venue": "BINANCE",
        "native_instrument": "BTCUSDT",
        "liquidation_event_id": "liq-p3-1",
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
        "source_revision_id": "rev-p3-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-p3-1",
        "raw_projection_refs": ("proj:p3:1",),
        "acquisition_refs": ("acq:p3:1",),
        "evidence_blob_hashes": (DOC_SHA,),
        "code_version": "p3",
        "config_version": "cfg-p3",
    }
    payload.update(overrides)
    return LiquidationObservationInput(**payload)


def _liq_record(monkeypatch: pytest.MonkeyPatch) -> Any:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    return normalize_liquidation(_liq_payload(), registry=_authority(manifest))


class HeldCustody:
    """Test custody: an independently held BYTE store, never a digest map."""

    def __init__(self, held: dict[str, bytes] | None = None) -> None:
        self._held = {REF: DOC_BYTES} if held is None else dict(held)
        self.reads: list[str] = []

    def read_evidence(self, reference: str) -> bytes | None:
        self.reads.append(reference)
        return self._held.get(reference)


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
                    source_revision_id="rev-p3-1",
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


def _request(record: Any, **overrides: Any) -> ConsumerRequest:
    payload: dict[str, Any] = {
        "record": record,
        "artifact_bytes": ARTIFACT,
        "knowledge_cutoff": CUTOFF,
        "replay_evidence": _replay_evidence(),
    }
    payload.update(overrides)
    return ConsumerRequest(**payload)


def _policy(
    manifest: bytes | None = None,
    *,
    custody: Any = "default",
    authority_source: Any = None,
) -> TrustConsumerPolicy:
    """Build the production policy over the pinned root currently installed."""
    return TrustConsumerPolicy(
        manifest_bytes=manifest if manifest is not None else _manifest(),
        methodology_registry=_methodologies(),
        custody=HeldCustody() if custody == "default" else custody,
        authority_source=authority_source,
    )


class _FixedAuthoritySource:
    """TEST DOUBLE at the policy seam (design spec E) -- never a production basis.

    It exists so the accepting branch and the ``UNAUTHORIZED`` branch can be
    exercised at all.  ``test_the_production_source_never_authorizes`` asserts
    that the shipped source cannot do this, which is the point: the double
    certifies nothing outside this suite.
    """

    def __init__(self, basis: CustodyAuthorityBasis, detail: str = "fixture basis") -> None:
        self._basis = basis
        self._detail = detail
        self.seen: list[CustodyAuthorityIdentity] = []

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        self.seen.append(identity)
        return CustodyAuthorityDerivation(basis=self._basis, detail=self._detail)


# ---------------------------------------------------------------------------
# Positive controls: the pipeline actually runs
# ---------------------------------------------------------------------------


def test_a_valid_trade_request_reaches_the_verifier_and_stops_at_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert verdict.verified_field_allowlist == ("aggressor_side",)
    assert verdict.pit_status == "ADMISSIBLE"
    assert verdict.replay_status == "ELIGIBLE"
    assert verdict.custody_status == "VERIFIED"
    assert verdict.custody_source_authorized is False
    assert "OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1" in (
        verdict.custody_authorization_detail or ""
    )


def test_a_valid_liquidation_request_reaches_the_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _liq_record(monkeypatch)
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert set(verdict.verified_field_allowlist) == {
        "position_side_liquidated",
        "execution_side",
    }
    assert verdict.custody_status == "VERIFIED"


def test_the_shipped_manifest_yields_integration_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """The authoritative production state, with NO fixture root."""
    record = _trade_record(monkeypatch)
    monkeypatch.undo()
    monkeypatch.setattr(
        authority_module,
        "TRUSTED_MANIFEST_SHA256",
        hashlib.sha256(PRODUCTION_MANIFEST.read_bytes()).hexdigest(),
    )
    policy = TrustConsumerPolicy(
        manifest_bytes=PRODUCTION_MANIFEST.read_bytes(),
        methodology_registry=_methodologies(),
        custody=HeldCustody(),
    )
    for request in (
        _request(record),
        _request(record, required_fields=("aggressor_side",)),
        _request(record, evidence_references=()),
    ):
        verdict = policy.evaluate(request)
        assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
        assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
        assert verdict.custody_source_authorized is False


def test_the_accepting_branch_is_reachable_only_through_the_test_double(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A wiring double can accept; the shipped source cannot (see next test)."""
    record = _trade_record(monkeypatch)
    source = _FixedAuthoritySource(CustodyAuthorityBasis.AUTHORIZED)
    verdict = _policy(authority_source=source).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.custody_source_authorized is True
    assert verdict.custody_source_authorization_status is CustodyAuthorityBasis.AUTHORIZED
    assert verdict.unverified_dimensions  # an acceptance still enumerates its gaps
    assert source.seen and source.seen[0].record_kind == "TRADE"


def test_the_production_source_never_authorizes(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    policy = _policy(custody=HeldCustody())
    assert isinstance(policy._authority_source, ManifestCustodyAuthority)  # noqa: SLF001
    verdict = policy.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED


def test_field_binding_and_source_authority_stay_separable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verified fields never promote source authority, and vice versa."""
    record = _trade_record(monkeypatch)
    verified = _policy().evaluate(_request(record))
    assert verified.verified_field_allowlist  # fields DID bind
    assert verified.custody_source_authorized is False  # authority did NOT follow

    unauthorized = _FixedAuthoritySource(CustodyAuthorityBasis.UNAUTHORIZED, "fixture denies")
    denied = _policy(authority_source=unauthorized).evaluate(_request(record))
    assert denied.decision is ConsumerDecision.REFUSE
    assert denied.refusal_reason is ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE
    assert denied.verified_field_allowlist  # fields still bound; the answer is refusal


def test_custody_integrity_is_a_prerequisite_of_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    source = _FixedAuthoritySource(CustodyAuthorityBasis.AUTHORIZED)
    no_custody = _policy(custody=None, authority_source=source)
    verdict = no_custody.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.custody_source_authorized is False


# ---------------------------------------------------------------------------
# A01/A02/A16 -- there is no place for a verdict to arrive
# ---------------------------------------------------------------------------


def test_evaluate_takes_a_request_and_nothing_else() -> None:
    signature = inspect.signature(TrustConsumerPolicy.evaluate)
    assert list(signature.parameters) == ["self", "request"]
    for parameter in signature.parameters.values():
        assert "Callable" not in str(parameter.annotation)
        assert "RecordVerification" not in str(parameter.annotation)


def test_the_policy_module_never_names_a_callback_intake() -> None:
    """Checked as CODE, not as prose: the docstring may quote the harness."""
    text = POLICY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    identifiers = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    assert "rederive" not in identifiers
    assert "Callable" not in identifiers
    assert "candidate" not in identifiers
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in (
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "glob",
        "yaml",
        "crypto_sensor_fabric.providers",
    ):
        assert forbidden not in imported, forbidden


def test_a_verdict_or_callback_cannot_be_smuggled_through_the_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    for field_name in ("verdict", "candidate", "rederive", "callback", "authority"):
        with pytest.raises(Exception):
            _request(record, **{field_name: object()})


def test_evaluate_refuses_a_non_request(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    policy = _policy(manifest)
    for not_a_request in (None, {"record": None}, b"request"):
        with pytest.raises(TypeError):
            policy.evaluate(not_a_request)  # type: ignore[arg-type]


def test_a_validator_bypass_is_caught_by_revalidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    forged = ConsumerRequest.model_construct(
        record=record,
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(),
        knowledge_cutoff=datetime(2026, 6, 1, 12, 0),  # naive: no validator ran
        replay_evidence=_replay_evidence(),
        claimed_manifest_bytes=None,
    )
    verdict = _policy().evaluate(forged)
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert "schema" in (verdict.refusal_detail or "")


# ---------------------------------------------------------------------------
# A03/A19 -- the verifier, its refusals and its crashes
# ---------------------------------------------------------------------------


def test_missing_provenance_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch).model_copy(update={"authority_provenance": None})
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert "PROVENANCE_MISSING" in (verdict.refusal_detail or "")


def test_an_unverified_required_field_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(
        _request(record, required_fields=("price_canonical", "aggressor_side"))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST


def test_a_verifier_crash_refuses_and_never_accepts(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom: internal detail that must not be echoed verbatim")

    monkeypatch.setattr(
        "crypto_sensor_fabric.normalization.consumer.policy.verify_trade_record", _explode
    )
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH
    assert len(verdict.refusal_detail or "") <= 400


def test_a_keyboard_interrupt_is_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _interrupt(*args: Any, **kwargs: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "crypto_sensor_fabric.normalization.consumer.policy.verify_trade_record", _interrupt
    )
    record = _trade_record(monkeypatch)
    with pytest.raises(KeyboardInterrupt):
        _policy().evaluate(_request(record))


def test_a_contradictory_verification_refuses_rather_than_accepts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``model_copy(update=...)`` forgery handed back by the verifier seam."""
    from crypto_sensor_fabric.normalization.sensors.verification import verify_trade_record

    def _forged(*args: Any, **kwargs: Any) -> Any:
        return verify_trade_record(*args, **kwargs).model_copy(
            update={"trust_scope": "FULL_RECORD_TRUST"}
        )

    record = _trade_record(monkeypatch)
    monkeypatch.setattr(
        "crypto_sensor_fabric.normalization.consumer.policy.verify_trade_record", _forged
    )
    verdict = _policy(
        authority_source=_FixedAuthoritySource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert "CONTRADICTORY_VERIFICATION" in (verdict.refusal_detail or "")


def test_a_verification_of_another_record_kind_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from crypto_sensor_fabric.normalization.sensors.verification import verify_trade_record

    def _wrong_kind(*args: Any, **kwargs: Any) -> Any:
        return verify_trade_record(*args, **kwargs).model_copy(
            update={"record_kind": "LIQUIDATION"}
        )

    record = _trade_record(monkeypatch)
    monkeypatch.setattr(
        "crypto_sensor_fabric.normalization.consumer.policy.verify_trade_record", _wrong_kind
    )
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert "record_kind" in (verdict.refusal_detail or "")


# ---------------------------------------------------------------------------
# A04 -- a caller's approval never follows its own record
# ---------------------------------------------------------------------------


def test_a_claimed_manifest_is_compared_not_adopted(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    foreign = _manifest(approval_id="APPROVAL-ATTACKER")
    verdict = _policy().evaluate(_request(record, claimed_manifest_bytes=foreign))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.TRUSTED_CONTEXT_MISMATCH


def test_the_matching_claimed_manifest_changes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    without = _policy(manifest).evaluate(_request(record))
    with_claim = _policy(manifest).evaluate(
        _request(record, claimed_manifest_bytes=manifest)
    )
    assert without.model_dump() == with_claim.model_dump()


def test_the_policy_refuses_a_foreign_root_at_construction() -> None:
    with pytest.raises(ValueError):
        TrustConsumerPolicy(
            manifest_bytes=_manifest(approval_id="APPROVAL-ATTACKER"),
            methodology_registry=_methodologies(),
            custody=HeldCustody(),
        )


def test_a_manifest_substitution_cannot_produce_a_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(authority_module, "TRUSTED_MANIFEST_SHA256", "0" * 64)
    with pytest.raises(ValueError):
        _policy(PRODUCTION_MANIFEST.read_bytes())


# ---------------------------------------------------------------------------
# A15/A16 -- replay, PIT and stale inputs
# ---------------------------------------------------------------------------


def test_a_request_without_replay_evidence_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(_request(record, replay_evidence=None))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert verdict.replay_status == "NOT_POLICY_DERIVED"


def test_a_forged_replay_evaluation_cannot_arrive(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ForgedEvaluation:
        eligibility = "ELIGIBLE"
        reasons: tuple[str, ...] = ()

    record = _trade_record(monkeypatch)
    forged = ConsumerRequest.model_construct(
        record=record,
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(),
        knowledge_cutoff=CUTOFF,
        replay_evidence=_ForgedEvaluation(),
        claimed_manifest_bytes=None,
    )
    verdict = _policy(
        authority_source=_FixedAuthoritySource(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(forged)
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_a_missing_cutoff_is_pit_inadmissible(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(_request(record, knowledge_cutoff=None))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE


def test_a_naive_cutoff_is_refused_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    forged = ConsumerRequest.model_construct(
        record=record,
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(),
        knowledge_cutoff=datetime(2026, 6, 1, 12, 0),
        replay_evidence=_replay_evidence(),
        claimed_manifest_bytes=None,
    )
    verdict = _policy().evaluate(forged)
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason in {
        ConsumerRefusalReason.NAIVE_CUTOFF,
        ConsumerRefusalReason.VERIFICATION_FAILED,
    }


# ---------------------------------------------------------------------------
# Bounded diagnostics
# ---------------------------------------------------------------------------


def test_diagnostics_are_bounded_and_carry_no_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A trust boundary that leaks payload in an error string is an exfil channel.

    The *caller's own* identifier may legitimately appear in a refusal -- it is
    their data, and naming which provider mismatched is the useful part of the
    message.  What must never appear is artifact or evidence content, and no
    message may exceed the bound.
    """

    def _noisy(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("x" * 5000 + " TAIL-MARKER-PAST-THE-BOUND")

    monkeypatch.setattr(
        "crypto_sensor_fabric.normalization.consumer.policy.verify_trade_record", _noisy
    )
    record = _trade_record(monkeypatch)
    verdict = _policy().evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH
    detail = verdict.refusal_detail or ""
    # The design allows the exception's own first 200 characters for diagnosis;
    # this proves the bound is real rather than decorative.
    assert len(detail) <= 200
    assert "TAIL-MARKER-PAST-THE-BOUND" not in detail
    assert "Traceback" not in detail
    # Artifact and evidence CONTENT is never relayed by this code at all.
    assert ARTIFACT.decode() not in detail
    assert DOC_BYTES.decode() not in detail


def test_the_provider_registry_used_by_the_fixtures_is_the_real_one() -> None:
    """The synthetic registry names a provider the production registry knows."""
    assert "BINANCE_USDM" in PROVIDER_IDS
    assert SensorFamily.MECHANICAL_TRADE.value == "MECHANICAL_TRADE"
