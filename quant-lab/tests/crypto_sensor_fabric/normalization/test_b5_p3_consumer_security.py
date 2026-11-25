"""SENSOR-B5-P3-R5 — executable adversarial security validation (A01–A20).

Each attack here has the six parts the directive requires: a valid positive
control, a concrete adversarial input, the actual production entry point, the
expected decision, the forbidden outcome, and an assertion that the *specific*
control fired.  A generic refusal is not accepted as proof of a specific
mechanism, and a policy that refused everything would fail the positive controls
in the same file.

**Threat classes, kept distinct (04_THREAT_MODEL.md).**

* T1/T2 — hostile data and a hostile caller.  Everything A01–A20 attacks; this
  is the boundary the code actually claims.
* T4 / threat class C — arbitrary code in the same interpreter.  Out of scope
  and documented as such: X01 (construct the policy over your own manifest),
  X02 (monkeypatch the verifier), X03 (replace the custody provider),
  X04 (resource exhaustion), X05 (host/dependency compromise), X06 (how a future
  operator authority is granted).  ``test_scope_documentation_names_x01_to_x06``
  fails if that documentation disappears.  Some tests *below* monkeypatch the
  verifier to hand the policy a forged verdict — that is deliberate: they are
  not claiming T4 is defended, they are claiming the consumer independently
  re-checks what it is handed.

**Mutation controls** (``TestMutationControls``) remove one control at a time
and show the forbidden outcome becomes reachable.  A control that no mutation
can make load-bearing is a control nobody has tested.
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
from crypto_sensor_fabric.contracts.enums import AggressorSide
from crypto_sensor_fabric.normalization.authority import load_trusted_authority
from crypto_sensor_fabric.normalization.common.methodologies import (
    NormalizationMethodologyRegistry,
)
from crypto_sensor_fabric.normalization.consumer.custody_authority import (
    CustodyAuthorityBasis,
    CustodyAuthorityDerivation,
    CustodyAuthorityIdentity,
    ManifestCustodyAuthority,
    custody_authority_identity_digest,
)
from crypto_sensor_fabric.normalization.consumer.models import (
    ConsumerDecision,
    ConsumerEvidenceReference,
    ConsumerRefusalReason,
    ConsumerRequest,
    ConsumerVerdict,
    CustodyAuthorityBasis as VerdictBasis,
)
from crypto_sensor_fabric.normalization.consumer import policy as policy_module
from crypto_sensor_fabric.normalization.consumer.policy import TrustConsumerPolicy
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    LineageState,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.sensors.liquidation import (
    LiquidationAggregationScope,
    LiquidationObservationInput,
    LiquidationPositionSide,
    normalize_liquidation,
)
from crypto_sensor_fabric.normalization.sensors.side_maps import SideEvidence
from crypto_sensor_fabric.normalization.sensors.trade import (
    TradeObservationInput,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.sensors.verification import (
    RecordVerification,
    verify_trade_record,
)
from crypto_sensor_fabric.normalization.time.enums import RevisionMode, RevisionStatus
from crypto_sensor_fabric.normalization.time.replay_gate import ReplayEvidence
from crypto_sensor_fabric.normalization.time.revision_policy import (
    RevisionRecord,
    RevisionSelection,
)
from crypto_sensor_fabric.storage import CoverageState, RevisionState

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
CONSUMER = QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "consumer"
PRODUCTION_MANIFEST = (
    QUANT_LAB
    / "config"
    / "crypto_sensor_fabric"
    / "provider_semantics"
    / "approval_manifest.json"
)

DOC_BYTES = b"synthetic venue document bytes (not a real provider document)"
TAMPERED_BYTES = b"tampered bytes"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P3_DOC_REF"
OTHER_REF = "OTHER_RECORD_DOC_REF"
METHOD_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"
LIQ_METHOD = "LIQUIDATION_SIDE_BINANCE_V1"
ASSUMPTION = "venue documents isBuyerMaker as the maker-side flag"
LIQ_ASSUMPTION = "venue documents side as the liquidated position side"
ARTIFACT_ID = "registry-p3-security.yaml"
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
EARLY = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)

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
# Fixtures
# ---------------------------------------------------------------------------


def _methodologies() -> NormalizationMethodologyRegistry:
    return NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "m-p3-5",
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
        authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(manifest).hexdigest()
    )


def _authority(manifest: bytes):
    return load_trusted_authority(
        manifest_bytes=manifest,
        artifact_id=ARTIFACT_ID,
        artifact_bytes=ARTIFACT,
        methodology_registry=_methodologies(),
        evaluation_at=CUTOFF,
    )


def _trade_record(monkeypatch: pytest.MonkeyPatch) -> Any:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
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
            "source_revision_id": "rev-p3-5",
            "source_revision_state": RevisionState.STABLE,
            "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
            "normalization_generation": "gen-p3-5",
            "raw_projection_refs": ("proj:p3:5",),
            "acquisition_refs": ("acq:p3:5",),
            "evidence_blob_hashes": (DOC_SHA,),
            "code_version": "p3",
            "config_version": "cfg-p3",
        }
    )
    return normalize_trade(payload, registry=_authority(manifest))


def _liq_record(monkeypatch: pytest.MonkeyPatch) -> Any:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    payload = LiquidationObservationInput(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSDT",
        liquidation_event_id="liq-p3-5",
        position_side_liquidated=LiquidationPositionSide.LONG,
        execution_side=AggressorSide.SELL,
        native_position_side_field="side",
        native_position_side_value="LONG",
        native_execution_side_field="side_exec",
        native_execution_side_value="SELL",
        quantity_native="2.5",
        quantity_native_unit="BTC",
        aggregation_scope=LiquidationAggregationScope.EVENT_LEVEL,
        source_precision=TimestampPrecision.MILLISECOND,
        source_revision_id="rev-p3-5",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-p3-5",
        raw_projection_refs=("proj:p3:5",),
        acquisition_refs=("acq:p3:5",),
        evidence_blob_hashes=(DOC_SHA,),
        code_version="p3",
        config_version="cfg-p3",
    )
    return normalize_liquidation(payload, registry=_authority(manifest))


class HeldCustody:
    def __init__(self, held: dict[str, bytes] | None = None) -> None:
        self._held = {REF: DOC_BYTES} if held is None else dict(held)
        self.reads: list[str] = []

    def read_evidence(self, reference: str) -> bytes | None:
        self.reads.append(reference)
        return self._held.get(reference)


class FlipCustody:
    def __init__(self, first: bytes | None, later: bytes | None) -> None:
        self._payloads = (first, later)
        self.reads: list[str] = []

    def read_evidence(self, reference: str) -> bytes | None:
        self.reads.append(reference)
        return self._payloads[0] if len(self.reads) == 1 else self._payloads[1]


class EmptyCustody:
    def read_evidence(self, reference: str) -> bytes | None:
        return None


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
                    source_revision_id="rev-p3-5",
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


class _Source:
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


def _policy(
    manifest: bytes,
    *,
    custody: Any = None,
    source: Any = None,
) -> TrustConsumerPolicy:
    return TrustConsumerPolicy(
        manifest_bytes=manifest,
        methodology_registry=_methodologies(),
        custody=HeldCustody() if custody is None else custody,
        authority_source=source,
    )


def _forged_verdict(**updates: Any) -> RecordVerification:
    """A ``model_construct`` verification: right class, no laws, no derivation."""
    return RecordVerification.model_construct(
        record_kind="TRADE",
        artifact_id=ARTIFACT_ID,
        approval_id="APPROVAL-FORGED",
        registry_digest=ARTIFACT_SHA,
        provider="BINANCE_USDM",
        semantic_mapping_approved=True,
        record_transformation_verified=True,
        custody_verified=True,
        source_lineage_verified=True,
        pit_admissible=True,
        downstream_trusted=True,
        trust_scope="ECONOMIC_FIELD_BINDING",
        unverified_dimensions=("SOURCE_LINEAGE",),
        custody_source_authorized=True,
        fields_verified=("aggressor_side",),
        **updates,
    )


# ---------------------------------------------------------------------------
# A01/A02/A16 -- no verdict, callback or cached object can arrive
# ---------------------------------------------------------------------------


def test_a01_callback_injection_has_no_intake(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()

    # positive control: the same request without the field reaches the pipeline
    control = _policy(manifest).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    # attack: name a callback on the request and on the entry point
    with pytest.raises(Exception):
        _request(record, rederive=lambda: _forged_verdict())
    with pytest.raises(Exception):
        _request(record, callback=lambda: _forged_verdict())
    signature = inspect.signature(TrustConsumerPolicy.evaluate)
    assert list(signature.parameters) == ["self", "request"]
    for parameter in signature.parameters.values():
        assert "Callable" not in str(parameter.annotation)

    # forbidden outcome: an accepted forged verification
    assert control.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_a02_model_construct_verification_cannot_be_an_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    forged = _forged_verdict()

    control = _policy(manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)).evaluate(
        _request(record)
    )
    assert control.decision is ConsumerDecision.ACCEPT_FIELD_BINDING  # the real path works

    with pytest.raises(Exception):
        _request(record, candidate=forged)
    with pytest.raises(Exception):
        _request(record, verdict=forged)

    # a forged *request* is revalidated, and its forged fields do not survive
    forced = ConsumerRequest.model_construct(
        record=record,
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(),
        knowledge_cutoff=datetime(2026, 6, 1, 12, 0),
        replay_evidence=_replay_evidence(),
        claimed_manifest_bytes=None,
    )
    refused = _policy(manifest).evaluate(forced)
    assert refused.decision is ConsumerDecision.REFUSE


def test_a16_a_cached_verdict_is_never_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = HeldCustody()
    policy = _policy(manifest, custody=custody)
    assert policy.evaluate(_request(record)).decision is ConsumerDecision.INTEGRATION_REQUIRED
    reads_first = custody.reads.count(REF)
    assert policy.evaluate(_request(record)).decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert custody.reads.count(REF) == 2 * reads_first  # every consumption re-reads


# ---------------------------------------------------------------------------
# A03/A10/A11 -- forged result contents
# ---------------------------------------------------------------------------


def test_a03_a_contradictory_verification_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _poisoned(*args: Any, **kwargs: Any) -> Any:
        return verify_trade_record(*args, **kwargs).model_copy(
            update={"fields_verified": ()}
        )

    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    monkeypatch.setattr(
        policy_module, "verify_trade_record", _poisoned
    )
    verdict = _policy(
        manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED


def test_a10_a_forged_trust_scope_never_accepts(monkeypatch: pytest.MonkeyPatch) -> None:
    def _widened(*args: Any, **kwargs: Any) -> Any:
        return verify_trade_record(*args, **kwargs).model_copy(
            update={"trust_scope": "FULL_RECORD_TRUST"}
        )

    record = _trade_record(monkeypatch)
    manifest = _manifest()
    monkeypatch.setattr(
        policy_module, "verify_trade_record", _widened
    )
    verdict = _policy(
        manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.refusal_reason in {
        ConsumerRefusalReason.FORGED_TRUST_SCOPE,
        ConsumerRefusalReason.VERIFICATION_FAILED,
    }
    # the second line of defence exists even when assert_trustworthy fires first
    text = (CONSUMER / "policy.py").read_text(encoding="utf-8")
    assert "FORGED_TRUST_SCOPE" in text


def test_a11_an_empty_dimension_list_never_reads_as_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The type law first: an acceptance must enumerate its gaps.
    with pytest.raises(Exception):
        ConsumerVerdict(
            decision=ConsumerDecision.ACCEPT_FIELD_BINDING,
            verified_field_allowlist=("aggressor_side",),
            unverified_dimensions=(),
            pit_status="ADMISSIBLE",
            replay_status="ELIGIBLE",
            custody_status="VERIFIED",
            custody_source_authorization_status=VerdictBasis.AUTHORIZED,
            custody_source_authorized=True,
        )

    def _empty(*args: Any, **kwargs: Any) -> Any:
        return verify_trade_record(*args, **kwargs).model_copy(
            update={"unverified_dimensions": (), "downstream_trusted": True}
        )

    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    monkeypatch.setattr(
        policy_module, "verify_trade_record", _empty
    )
    verdict = _policy(
        manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)
    ).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE


# ---------------------------------------------------------------------------
# A04/A05/A06/A08/A09 -- approval, capability and identity attacks
# ---------------------------------------------------------------------------


def test_a04_manifest_substitution_is_compared_not_adopted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    attacker = _manifest(approval_id="APPROVAL-ATTACKER")

    control = _policy(manifest).evaluate(_request(record, claimed_manifest_bytes=manifest))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    refused = _policy(manifest).evaluate(
        _request(record, claimed_manifest_bytes=attacker)
    )
    assert refused.decision is ConsumerDecision.REFUSE
    assert refused.refusal_reason is ConsumerRefusalReason.TRUSTED_CONTEXT_MISMATCH


def test_a05_a_minted_capability_authorizes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    # H03: "minting" the most permissive derivation the type allows is itself
    # impossible without naming an identity -- a wildcard grant cannot be
    # constructed at all, so there is nothing to mint.
    with pytest.raises(Exception):
        CustodyAuthorityDerivation(
            basis=CustodyAuthorityBasis.AUTHORIZED, detail="minted"
        )
    minted = CustodyAuthorityDerivation(
        basis=CustodyAuthorityBasis.AUTHORIZED,
        detail="minted",
        identity_sha256="0" * 64,
    )
    assert minted.basis is CustodyAuthorityBasis.AUTHORIZED

    # there is no field on the request into which it can be placed
    for field_name in ("custody_authority", "authority", "capability", "basis"):
        with pytest.raises(Exception):
            _request(record, **{field_name: minted})

    # and the production policy derives its own answer, which is not that one
    verdict = _policy(manifest).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED

    # no issuance machinery exists to mint from (identifiers, not prose: the
    # module docstring names ``_issue()`` precisely to say it is absent)
    tree = ast.parse((CONSUMER / "custody_authority.py").read_text(encoding="utf-8"))
    identifiers = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "_issue" not in identifiers
    assert "is_issued" not in identifiers
    assert "_ISSUANCE_MARKER" not in identifiers


def test_a06_a_copied_marker_changes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _Source(CustodyAuthorityBasis.INTEGRATION_REQUIRED)
    policy = _policy(manifest, source=source)

    # A "stolen marker" has nothing to attach to: the source has no such state,
    # and adding one to the instance does not change the answer.
    object.__setattr__(source, "_issued", object())
    object.__setattr__(source, "_ISSUANCE_MARKER", object())
    verdict = policy.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert verdict.custody_source_authorized is False


def test_a07_cross_record_evidence_reuse_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    custody = HeldCustody({REF: DOC_BYTES, OTHER_REF: DOC_BYTES})

    control = _policy(manifest, custody=custody).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    reused = _policy(manifest, custody=custody).evaluate(
        _request(record, evidence_references=(_ref(OTHER_REF), _ref()))
    )
    assert reused.decision is ConsumerDecision.REFUSE
    assert reused.refusal_reason is ConsumerRefusalReason.EVIDENCE_NOT_BOUND_TO_ARTIFACT


def test_a08_cross_cutoff_authority_cannot_be_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _Source(CustodyAuthorityBasis.AUTHORIZED)
    policy = _policy(manifest, source=source)

    verdict = policy.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.ACCEPT_FIELD_BINDING
    # the identity the source saw is bound to THIS request's cutoff
    assert source.seen[-1].knowledge_cutoff == CUTOFF

    later = datetime(2027, 6, 1, 12, 0, tzinfo=UTC)
    expired = policy.evaluate(_request(record, knowledge_cutoff=later))
    assert expired.decision is ConsumerDecision.REFUSE
    assert expired.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    # the expired instant never even reached the authority source
    assert len(source.seen) == 1

    # and if it HAD reached it, the production derivation refuses that cutoff
    production_source = ManifestCustodyAuthority(manifest_bytes=manifest)
    derivation = production_source.authorize(
        source.seen[0].model_copy(
            update={"knowledge_cutoff": later, "manifest_sha256": hashlib.sha256(manifest).hexdigest()}
        )
    )
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED
    assert derivation.basis is not CustodyAuthorityBasis.AUTHORIZED


def test_a09_no_synthetic_basis_exists_to_promote() -> None:
    assert "SYNTHETIC_TEST_ONLY" not in {member.name for member in CustodyAuthorityBasis}
    for path in sorted(CONSUMER.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for statement in node.body:
                    if isinstance(statement, ast.Assign) and isinstance(
                        statement.value, ast.Constant
                    ):
                        value = statement.value.value
                        if isinstance(value, str):
                            assert "SYNTHETIC" not in value, (path.name, value)
    with pytest.raises(Exception):
        ConsumerVerdict(
            decision=ConsumerDecision.REFUSE,
            refusal_reason=ConsumerRefusalReason.VERIFICATION_FAILED,
            pit_status="INADMISSIBLE",
            replay_status="BLOCKED",
            custody_status="UNVERIFIED",
            custody_source_authorization_status=VerdictBasis.AUTHORIZED,
            custody_source_authorized=True,
        )


# ---------------------------------------------------------------------------
# A12–A15 -- fields, evidence, replay
# ---------------------------------------------------------------------------


def test_a12_a_field_outside_the_allowlist_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest).evaluate(
        _request(record, required_fields=("aggressor_side",))
    )
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    refused = _policy(manifest).evaluate(
        _request(record, required_fields=("price_canonical",))
    )
    assert refused.decision is ConsumerDecision.REFUSE
    assert refused.refusal_reason is ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST


def test_a13_evidence_substitution_refuses_for_both_record_kinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    for build in (_trade_record, _liq_record):
        record = build(monkeypatch)
        control = _policy(manifest).evaluate(_request(record))
        assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED, build.__name__

        refused = _policy(manifest, custody=FlipCustody(DOC_BYTES, TAMPERED_BYTES)).evaluate(
            _request(record)
        )
        assert refused.decision is ConsumerDecision.REFUSE, build.__name__
        assert (
            refused.refusal_reason is ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH
        ), build.__name__


def test_a14_digest_only_custody_refuses_for_both_record_kinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    for build in (_trade_record, _liq_record):
        record = build(monkeypatch)
        control = _policy(manifest).evaluate(_request(record))
        assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED, build.__name__

        refused = _policy(manifest, custody=EmptyCustody()).evaluate(_request(record))
        assert refused.decision is ConsumerDecision.REFUSE, build.__name__
        assert refused.custody_status == "UNVERIFIED", build.__name__


def test_a15_forged_replay_eligibility_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ClaimedEligible:
        eligibility = "ELIGIBLE"
        reasons: tuple[str, ...] = ()

    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)).evaluate(
        _request(record)
    )
    assert control.decision is ConsumerDecision.ACCEPT_FIELD_BINDING
    assert control.replay_status == "ELIGIBLE"

    forced = ConsumerRequest.model_construct(
        record=record,
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(_ref(),),
        knowledge_cutoff=CUTOFF,
        replay_evidence=_ClaimedEligible(),
        claimed_manifest_bytes=None,
    )
    verdict = _policy(manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)).evaluate(
        forced
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_a15b_a_blocked_replay_gate_blocks_before_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    source = _Source(CustodyAuthorityBasis.AUTHORIZED)
    verdict = _policy(manifest, source=source).evaluate(
        _request(record, replay_evidence=_replay_evidence(interval_complete=False))
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert source.seen == []


# ---------------------------------------------------------------------------
# A17–A20 -- ordering, crashes, provenance, empty manifest
# ---------------------------------------------------------------------------


def test_a17_pit_inadmissible_authority_refuses_for_both_kinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    for build in (_trade_record, _liq_record):
        record = build(monkeypatch)
        source = _Source(CustodyAuthorityBasis.AUTHORIZED)
        verdict = _policy(manifest, source=source).evaluate(
            _request(record, knowledge_cutoff=EARLY)
        )
        assert verdict.decision is ConsumerDecision.REFUSE, build.__name__
        assert verdict.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE
        assert source.seen == []


def test_a18_a_verifier_exception_refuses_and_system_exit_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    def _explode(*args: Any, **kwargs: Any) -> None:
        raise ValueError("interpreter detail")

    monkeypatch.setattr(
        policy_module, "verify_trade_record", _explode
    )
    refused = _policy(manifest, source=_Source(CustodyAuthorityBasis.AUTHORIZED)).evaluate(
        _request(record)
    )
    assert refused.decision is ConsumerDecision.REFUSE
    assert refused.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH
    assert len(refused.refusal_detail or "") <= 200

    def _exit(*args: Any, **kwargs: Any) -> None:
        raise SystemExit(3)

    monkeypatch.setattr(
        policy_module, "verify_trade_record", _exit
    )
    with pytest.raises(SystemExit):
        _policy(manifest).evaluate(_request(record))


def test_a19_missing_provenance_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)
    manifest = _manifest()
    control = _policy(manifest).evaluate(_request(record))
    assert control.decision is ConsumerDecision.INTEGRATION_REQUIRED

    stripped = record.model_copy(update={"authority_provenance": None})
    refused = _policy(manifest).evaluate(_request(stripped))
    assert refused.decision is ConsumerDecision.REFUSE
    assert refused.refusal_reason is ConsumerRefusalReason.VERIFICATION_FAILED
    assert "PROVENANCE_MISSING" in (refused.refusal_detail or "")


def test_a20_the_empty_manifest_is_the_integration_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shipped = PRODUCTION_MANIFEST.read_bytes()
    records = [_trade_record(monkeypatch), _liq_record(monkeypatch)]
    monkeypatch.setattr(
        authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(shipped).hexdigest()
    )
    policy = TrustConsumerPolicy(
        manifest_bytes=shipped,
        methodology_registry=_methodologies(),
        custody=HeldCustody(),
        authority_source=_Source(CustodyAuthorityBasis.AUTHORIZED),  # even a grant
    )
    for record in records:
        verdict = policy.evaluate(_request(record))
        # Not "no restrictions": the computed answer is that there is no
        # authority to be had, and a wiring double cannot change that, because
        # the record never verifies against an empty root.
        assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED, build.__name__
        assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
        assert verdict.custody_source_authorized is False


# ---------------------------------------------------------------------------
# Scope documentation (A5.2)
# ---------------------------------------------------------------------------


def test_scope_documentation_names_x01_to_x06() -> None:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    for marker in ("X01", "X02", "X03", "X04", "X05", "X06"):
        assert marker in text, marker
    policy_text = (CONSUMER / "policy.py").read_text(encoding="utf-8")
    assert "does not resist code" in policy_text
    assert "application's privileges" in policy_text


# ---------------------------------------------------------------------------
# Mutation controls (A5.1)
# ---------------------------------------------------------------------------


class TestMutationControls:
    """Remove one control; the forbidden outcome must become reachable."""

    def test_removing_rebinding_lets_swapped_bytes_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        record = _trade_record(monkeypatch)
        manifest = _manifest()

        guarded = _policy(
            manifest,
            custody=FlipCustody(DOC_BYTES, TAMPERED_BYTES),  # fresh flip per attempt
            source=_Source(CustodyAuthorityBasis.AUTHORIZED),
        ).evaluate(_request(record))
        assert guarded.decision is ConsumerDecision.REFUSE  # the control works

        monkeypatch.setattr(
            TrustConsumerPolicy, "_rebind", lambda self, *args: None
        )
        mutated = _policy(
            manifest,
            custody=FlipCustody(DOC_BYTES, TAMPERED_BYTES),
            source=_Source(CustodyAuthorityBasis.AUTHORIZED),
        ).evaluate(_request(record))
        assert mutated.decision is ConsumerDecision.ACCEPT_FIELD_BINDING  # forbidden

    def test_removing_the_replay_gate_lets_a_blocked_record_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from crypto_sensor_fabric.normalization.consumer import policy as policy_module

        record = _trade_record(monkeypatch)
        manifest = _manifest()
        blocked = _replay_evidence(interval_complete=False)
        source = _Source(CustodyAuthorityBasis.AUTHORIZED)

        guarded = _policy(manifest, source=source).evaluate(
            _request(record, replay_evidence=blocked)
        )
        assert guarded.decision is ConsumerDecision.REFUSE

        monkeypatch.setattr(
            TrustConsumerPolicy,
            "_adjudicate_replay",
            lambda self, evidence: policy_module._ReplayAdjudication(
                status="ELIGIBLE", blocked=False, detail=""
            ),
        )
        mutated = _policy(manifest, source=source).evaluate(
            _request(record, replay_evidence=blocked)
        )
        assert mutated.decision is ConsumerDecision.ACCEPT_FIELD_BINDING  # forbidden

    def test_removing_the_pit_mapping_misreports_a_time_violation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from crypto_sensor_fabric.normalization.consumer import policy as policy_module

        # A PIT violation only the VERIFIER can see: the approval becomes
        # operative after this cutoff, while the replay evidence is known and
        # market-available inside it.  H02's binding therefore passes, and the
        # verifier's refusal is the one the PIT mapping classifies.
        record = _trade_record(monkeypatch)
        late = _manifest(available_at="2026-06-02")
        monkeypatch.setattr(
            authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(late).hexdigest()
        )
        guarded = _policy(late).evaluate(_request(record))
        assert guarded.refusal_reason is ConsumerRefusalReason.PIT_INADMISSIBLE
        assert guarded.replay_status == "ELIGIBLE"

        monkeypatch.setattr(policy_module, "_PIT_REFUSALS", frozenset())
        mutated = _policy(late).evaluate(_request(record))
        assert mutated.refusal_reason is not ConsumerRefusalReason.PIT_INADMISSIBLE
        # the answer is still not acceptance -- the mapping classifies, it does
        # not gate -- which is exactly why it is a mutation of REPORTING, not of
        # the boundary
        assert mutated.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING

    def test_removing_the_empty_manifest_mapping_misreports_the_state(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from crypto_sensor_fabric.normalization.consumer import policy as policy_module

        shipped = PRODUCTION_MANIFEST.read_bytes()
        record = _trade_record(monkeypatch)
        monkeypatch.setattr(
            authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(shipped).hexdigest()
        )
        policy = TrustConsumerPolicy(
            manifest_bytes=shipped,
            methodology_registry=_methodologies(),
            custody=HeldCustody(),
        )
        guarded = policy.evaluate(_request(record))
        assert guarded.decision is ConsumerDecision.INTEGRATION_REQUIRED

        monkeypatch.setattr(policy_module, "_INTEGRATION_ABSENT_REFUSALS", frozenset())
        mutated = _policy(shipped).evaluate(_request(record))
        assert mutated.decision is ConsumerDecision.REFUSE  # forbidden classification
        assert mutated.decision is not ConsumerDecision.INTEGRATION_REQUIRED


# ---------------------------------------------------------------------------
# H01-H04 -- final hardening (SENSOR-B5-P3-R6-FINAL-VERIFICATION-R1)
# ---------------------------------------------------------------------------

#: A string no public verdict may ever contain.  Its shape is the one that
#: actually leaks in production: a credential inside a driver's message.
_SECRET = "AKIA-P3-SENTINEL-CREDENTIAL-DO-NOT-RELAY-9f4c"


def _public_text(verdict: Any) -> str:
    """Everything a verdict exposes, as one string."""
    return repr(verdict.model_dump())


def test_h01_a_verifier_crash_message_is_never_relayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 200-character bound limits the leak; it does not prevent it."""
    record = _trade_record(monkeypatch)

    def _explode(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError(f"connect failed: postgres://root:{_SECRET}@db/sensor")

    monkeypatch.setattr(
        policy_module, "verify_trade_record",
        _explode,
    )
    verdict = _policy(_manifest()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH
    assert _SECRET not in _public_text(verdict)
    assert "RuntimeError" in (verdict.refusal_detail or "")  # the class IS disclosed
    assert len(verdict.refusal_detail or "") <= 400


def test_h01_a_replay_gate_crash_message_is_never_relayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)

    def _explode(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError(f"gate exploded while reading token {_SECRET}")

    monkeypatch.setattr(
        policy_module, "assess_replay_eligibility",
        _explode,
    )
    verdict = _policy(_manifest()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.REPLAY_BLOCKED
    assert _SECRET not in _public_text(verdict)


def test_h01_a_custody_crash_message_is_never_relayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)

    class _LeakyCustody:
        def read_evidence(self, reference: str) -> bytes | None:
            raise OSError(f"cannot open /srv/{_SECRET}/evidence.bin")

    verdict = _policy(_manifest(), custody=_LeakyCustody()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert _SECRET not in _public_text(verdict)


def test_h01_keyboard_interrupt_still_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The withheld-message rule must not start swallowing process signals."""
    record = _trade_record(monkeypatch)

    def _interrupt(*args: Any, **kwargs: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(
        policy_module, "verify_trade_record",
        _interrupt,
    )
    with pytest.raises(KeyboardInterrupt):
        _policy(_manifest()).evaluate(_request(record))


class _WildcardSource:
    """A wiring double that authorizes whatever identity it is handed."""

    def __init__(self) -> None:
        self.seen: list[CustodyAuthorityIdentity] = []

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        self.seen.append(identity)
        return CustodyAuthorityDerivation(
            basis=CustodyAuthorityBasis.AUTHORIZED,
            detail="wildcard grant",
            identity_sha256=custody_authority_identity_digest(identity),
        )


class _WrongIdentitySource:
    """Authorizes a *different* identity than the one it was asked about."""

    def __init__(self, cutoff: datetime) -> None:
        self._cutoff = cutoff

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        other = identity.model_copy(update={"knowledge_cutoff": self._cutoff})
        return CustodyAuthorityDerivation(
            basis=CustodyAuthorityBasis.AUTHORIZED,
            detail="authorized for another cutoff",
            identity_sha256=custody_authority_identity_digest(other),
        )


def test_h03_authority_for_another_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)
    source = _WrongIdentitySource(datetime(2027, 1, 1, tzinfo=UTC))
    verdict = _policy(_manifest(), source=source).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE
    assert verdict.custody_source_authorized is False


def test_h03_an_empty_manifest_cannot_be_authorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No empty-manifest request becomes authorized, even with a grant wired in."""
    shipped = PRODUCTION_MANIFEST.read_bytes()
    record = _trade_record(monkeypatch)
    monkeypatch.setattr(
        authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(shipped).hexdigest()
    )
    source = _WildcardSource()
    policy = TrustConsumerPolicy(
        manifest_bytes=shipped,
        methodology_registry=_methodologies(),
        custody=HeldCustody(),
        authority_source=source,
    )
    verdict = policy.evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.INTEGRATION_REQUIRED
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING
    assert verdict.custody_source_authorized is False
    assert source.seen == []  # the seam is never even consulted


def test_h03_a_conclusion_naming_an_unapproved_artifact_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The empty-manifest guard itself, reached through the conclusion path."""
    from crypto_sensor_fabric.normalization.consumer import policy as policy_module

    record = _trade_record(monkeypatch)
    source = _WildcardSource()
    policy = _policy(_manifest(), source=source)
    derived = policy._derive(record, ARTIFACT, CUTOFF)  # noqa: SLF001
    forged = derived.model_copy(update={"artifact_id": "NOT-AN-APPROVED-ARTIFACT"})
    verdict = policy._conclude(  # noqa: SLF001
        request=_request(record),
        derived=forged,
        cutoff=CUTOFF,
        replay=policy_module._ReplayAdjudication(
            status="ELIGIBLE", blocked=False, detail=""
        ),
        pit_status="ADMISSIBLE",
        custody_status="VERIFIED",
    )
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE
    assert "no empty-manifest request may become authorized" in (
        verdict.refusal_detail or ""
    )


def test_h03_a_malformed_derivation_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)

    class _Malformed:
        def authorize(self, identity: CustodyAuthorityIdentity) -> Any:
            return {"basis": "AUTHORIZED"}

    verdict = _policy(_manifest(), source=_Malformed()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH


def test_h03_a_model_construct_authorization_without_identity_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _trade_record(monkeypatch)

    class _Unbound:
        def authorize(self, identity: CustodyAuthorityIdentity) -> Any:
            # model_construct skips the law that requires an identity digest
            return CustodyAuthorityDerivation.model_construct(
                basis=CustodyAuthorityBasis.AUTHORIZED,
                detail="unbound",
                unresolved_contract=None,
            )

    verdict = _policy(_manifest(), source=_Unbound()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE


def test_h03_a_raising_source_relays_no_message(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _trade_record(monkeypatch)

    class _Raising:
        def authorize(self, identity: CustodyAuthorityIdentity) -> Any:
            raise RuntimeError(f"vault token {_SECRET} rejected")

    verdict = _policy(_manifest(), source=_Raising()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.refusal_reason is ConsumerRefusalReason.VERIFIER_CRASH
    assert _SECRET not in _public_text(verdict)


def test_h04_a_model_construct_request_holding_junk_refuses_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _trade_record(monkeypatch)  # pins the fixture root
    manifest = _manifest()
    for junk in (object(), "not-a-record", 42, None, 3.5):
        forced = ConsumerRequest.model_construct(
            record=junk,
            artifact_bytes=ARTIFACT,
            required_fields=(),
            evidence_references=(),
            knowledge_cutoff=CUTOFF,
            replay_evidence=_replay_evidence(),
            claimed_manifest_bytes=None,
        )
        verdict = _policy(manifest).evaluate(forced)
        assert verdict.decision is ConsumerDecision.REFUSE, junk
        assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_h04_a_verification_with_unusable_fields_refuses_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inspection reads a verification; a forged one must not raise from it."""
    record = _trade_record(monkeypatch)
    junk = RecordVerification.model_construct(
        record_kind="TRADE",
        artifact_id=ARTIFACT_ID,
        approval_id="APPROVAL-FORGED",
        registry_digest=ARTIFACT_SHA,
        provider="BINANCE_USDM",
        semantic_mapping_approved=True,
        record_transformation_verified=True,
        custody_verified=True,
        source_lineage_verified=True,
        pit_admissible=True,
        downstream_trusted=True,
        trust_scope="ECONOMIC_FIELD_BINDING",
        unverified_dimensions=("SOURCE_LINEAGE",),
        custody_source_authorized=True,
        fields_verified=([], ["aggressor_side"]),
    )
    monkeypatch.setattr(
        policy_module, "verify_trade_record",
        lambda *args, **kwargs: junk,
    )
    verdict = _policy(_manifest()).evaluate(_request(record))
    assert verdict.decision is ConsumerDecision.REFUSE
    assert verdict.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING


def test_h04_a_non_request_argument_is_still_a_programmer_error() -> None:
    policy = TrustConsumerPolicy(
        manifest_bytes=PRODUCTION_MANIFEST.read_bytes(),
        methodology_registry=_methodologies(),
        custody=HeldCustody(),
    )
    with pytest.raises(TypeError):
        policy.evaluate({"record": "nope"})  # type: ignore[arg-type]
