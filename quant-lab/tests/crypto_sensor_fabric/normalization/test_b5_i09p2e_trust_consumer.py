"""SENSOR-B5-I09P2eR1 — trust-consumer conformance engine (EXPERIMENTAL, TEST-ONLY).

Implements the mandatory consumer behavior of
``BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md`` (P2e) as an independently
testable conformance harness.

QUARANTINED PROTOTYPE — not an authorized production consumer.
No production ingestion, no custody service, no provider approval.
``INTEGRATION_STATE`` remains ``INTEGRATION_REQUIRED``.

Reuses (does not duplicate):
* ``verify_trade_record`` / ``verify_liquidation_record`` — record verification
* ``TrustedAuthorityContext`` / ``TrustedCustodyProvider`` — trust boundary
* ``ReplayEligibility`` / ``assess_replay_eligibility`` — I05 replay gate
* ``pit_availability_refusal`` — PIT availability rule
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable
from zoneinfo import ZoneInfo

import pytest

from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_RELPATH,
    AuthorityRefusal,
    SemanticAuthority,
    SemanticAuthorityRefusal,
    evidence_digest,
    parse_approval_manifest,
    pit_availability_refusal,
)
from crypto_sensor_fabric.normalization.sensors.verification import (
    INTEGRATION_STATE,
    TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
    RecordVerification,
    RecordVerificationError,
    RecordVerificationRefusal,
    TrustedAuthorityContext,
    verify_trade_record,
)
from crypto_sensor_fabric.normalization.time.enums import ReplayEligibility
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
DOC_BYTES = b"synthetic p2e consumer document bytes"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2E_DOC_REF"

# Synthetic authority identity used by the fixtures below.  These certify no
# venue and fabricate no provider document; they exist only to exercise the
# consumer mechanism under a synthetic root.
ARTIFACT_ID = "registry-probe.yaml"
APPROVAL_ID = "APPROVAL-SYNTHETIC-P2E"
REGISTRY_DIGEST = "a" * 64


# --------------------------------------------------------------------------- #
# Consumer boundary — three typed outcomes                                    #
# --------------------------------------------------------------------------- #


class ConsumerDecision(str, Enum):
    ACCEPT_FIELD_BINDING = "ACCEPT_FIELD_BINDING"
    REFUSE = "REFUSE"
    INTEGRATION_REQUIRED = "INTEGRATION_REQUIRED"


class ConsumerRefusalReason(str, Enum):
    FORGED_TRUST_SCOPE = "FORGED_TRUST_SCOPE"
    EMPTY_UNVERIFIED_DIMENSIONS = "EMPTY_UNVERIFIED_DIMENSIONS"
    UNAUTHORIZED_CUSTODY_SOURCE = "UNAUTHORIZED_CUSTODY_SOURCE"
    DIGEST_ONLY_CUSTODY = "DIGEST_ONLY_CUSTODY"
    EVIDENCE_BYTES_MISSING = "EVIDENCE_BYTES_MISSING"
    EVIDENCE_BYTES_MISMATCH = "EVIDENCE_BYTES_MISMATCH"
    CACHED_VERDICT_DIVERGENCE = "CACHED_VERDICT_DIVERGENCE"
    FIELD_NOT_IN_ALLOWLIST = "FIELD_NOT_IN_ALLOWLIST"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    PIT_INADMISSIBLE = "PIT_INADMISSIBLE"
    REPLAY_BLOCKED = "REPLAY_BLOCKED"
    NAIVE_CUTOFF = "NAIVE_CUTOFF"
    NO_PIT_AVAILABILITY = "NO_PIT_AVAILABILITY"
    INTRADAY_PIT_AMBIGUITY = "INTRADAY_PIT_AMBIGUITY"


@dataclass(frozen=True)
class ConsumerVerdict:
    decision: ConsumerDecision
    verified_field_allowlist: tuple[str, ...]
    unverified_dimensions: tuple[str, ...]
    trust_scope: str
    pit_status: str
    replay_status: str
    custody_status: str
    custody_source_authorized: bool
    custody_source_authorization_status: str
    refusal_reason: ConsumerRefusalReason | None = None
    refusal_detail: str | None = None


# --------------------------------------------------------------------------- #
# Deterministic local test store (fixture, not production custody)            #
# --------------------------------------------------------------------------- #


class DeterministicEvidenceStore:
    """In-memory byte store used only by the conformance harness."""

    def __init__(self, blobs: dict[str, bytes] | None = None) -> None:
        self._blobs = dict(blobs or {})

    def put(self, reference: str, data: bytes) -> None:
        self._blobs[reference] = data

    def read(self, reference: str) -> bytes | None:
        return self._blobs.get(reference)


# --------------------------------------------------------------------------- #
# Consumer policy — one central evaluation policy                             #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Policy-owned custody authority capability (R5)                              #
# --------------------------------------------------------------------------- #


class AuthorityBasis(str, Enum):
    """Where a custody-authority decision came from.

    An unverified caller claim is not a category here: it is the absence of a
    capability, which is why AT53's forged boolean can no longer be honoured.
    """

    ATTESTED_OPERATOR = "ATTESTED_OPERATOR"
    SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"


@dataclass(frozen=True)
class CustodyAuthorityCapability:
    """Externally bound proof that a custody source is authorized for THIS record.

    SENSOR-B5-I09P3-R5 repair of AT43/AT53-AT57.  The capability belongs to the
    policy, never to the record producer, and is bound to:

    * the reviewed root -- a ``TrustedAuthorityContext`` re-validated through
      ``from_reviewed_root``, so a ``model_construct``-forged context dies here;
    * a loader-issued ``SemanticAuthority``, constructible only by
      ``load_semantic_authority`` over approved manifest bytes and carrying a
      private issuance seal, so a caller cannot type one into existence;
    * the record identity (artifact / approval / registry digest, record kind),
      so AT56 cross-record reuse cannot carry authorization over;
    * the knowledge cutoff, so cross-cutoff reuse re-runs PIT and replay instead
      of inheriting them.

    This repository ships an EMPTY approval manifest (``"artifacts": {}``), so no
    ``ATTESTED_OPERATOR`` capability can be minted: the authorization gate returns
    ``INTEGRATION_REQUIRED`` until an approved operator-authority mechanism
    exists.  ``SYNTHETIC_TEST_ONLY`` exists only to keep downstream field-scope
    logic testable and is never reported as ``AUTHORIZED``.

    Bounded claim: this is a data boundary inside one process.  It does not resist
    code running with the application's privileges (``model_construct`` skips
    validators), exactly as ``authority``'s own loader docstring states.
    """

    basis: AuthorityBasis
    artifact_id: str
    approval_id: str
    registry_digest: str
    record_kind: str | None
    knowledge_cutoff: datetime | None
    manifest_sha256: str | None = None

    @classmethod
    def from_reviewed_context(
        cls,
        *,
        context: TrustedAuthorityContext,
        semantic_authority: Any,
        knowledge_cutoff: datetime | None = None,
        record_kind: str | None = None,
    ) -> "CustodyAuthorityCapability":
        """Mint operator authority -- impossible while the manifest is empty."""
        if not isinstance(context, TrustedAuthorityContext):
            raise RecordVerificationError(
                RecordVerificationRefusal.TRUSTED_CONTEXT_MISMATCH,
                "custody authority requires a TrustedAuthorityContext over the "
                "reviewed root",
            )
        reviewed = TrustedAuthorityContext.from_reviewed_root(
            manifest_bytes=context.manifest_bytes, artifact_id=context.artifact_id
        )
        if not isinstance(semantic_authority, SemanticAuthority):
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.NO_APPROVAL,
                "no loader-issued approval covers this artifact; the shipped "
                "manifest approves nothing, so no custody source is authorized",
            )
        if semantic_authority.artifact_id != reviewed.artifact_id:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.UNTRUSTED_AUTHORITY,
                f"the approval names {semantic_authority.artifact_id!r}; the "
                f"reviewed context names {reviewed.artifact_id!r}",
            )
        return cls(
            basis=AuthorityBasis.ATTESTED_OPERATOR,
            artifact_id=semantic_authority.artifact_id,
            approval_id=semantic_authority.approval_id,
            registry_digest=semantic_authority.registry_digest,
            record_kind=record_kind,
            knowledge_cutoff=knowledge_cutoff,
            manifest_sha256=reviewed.manifest_sha256,
        )

    @classmethod
    def synthetic_for_field_scope_tests(
        cls,
        *,
        artifact_id: str,
        approval_id: str,
        registry_digest: str,
        record_kind: str | None = None,
        knowledge_cutoff: datetime | None = None,
    ) -> "CustodyAuthorityCapability":
        """Non-authoritative capability for downstream field-scope tests only."""
        return cls(
            basis=AuthorityBasis.SYNTHETIC_TEST_ONLY,
            artifact_id=artifact_id,
            approval_id=approval_id,
            registry_digest=registry_digest,
            record_kind=record_kind,
            knowledge_cutoff=knowledge_cutoff,
            manifest_sha256=None,
        )


class ConsumerPolicy:
    """Central fail-closed evaluation policy for trust-consumer verdicts.

    Every path (single, batch, cached, deserialized, evidence reread) funnels
    through ``_apply`` so no path can independently invent authority.
    """

    def __init__(
        self,
        *,
        context: TrustedAuthorityContext | None = None,
        store: DeterministicEvidenceStore | None = None,
        custody_authority: CustodyAuthorityCapability | None = None,
    ) -> None:
        self.context = context
        self.store = store or DeterministicEvidenceStore()
        self._custody_authority = custody_authority

    # -- custody authority (R5) ------------------------------------------------

    def _custody_grant(
        self, derived: RecordVerification, knowledge_cutoff: datetime | None
    ) -> tuple[bool, str]:
        """Decide custody-source authority from the POLICY's own capability.

        ``derived.custody_source_authorized`` is deliberately never consulted: it
        is a claim carried on the record, and AT53 showed that honouring it turns
        any callback into an approval.
        """
        capability = self._custody_authority
        if capability is None:
            return False, "INTEGRATION_REQUIRED"
        if capability.knowledge_cutoff != knowledge_cutoff:
            return False, "INTEGRATION_REQUIRED"
        if (
            capability.record_kind is not None
            and capability.record_kind != derived.record_kind
        ):
            return False, "INTEGRATION_REQUIRED"
        if (
            capability.artifact_id,
            capability.approval_id,
            capability.registry_digest,
        ) != (
            derived.artifact_id,
            derived.approval_id,
            derived.registry_digest,
        ):
            return False, "INTEGRATION_REQUIRED"
        if capability.basis is AuthorityBasis.ATTESTED_OPERATOR:
            return True, "AUTHORIZED"
        if capability.basis is AuthorityBasis.SYNTHETIC_TEST_ONLY:
            return True, "SYNTHETIC_TEST_ONLY"
        return False, "INTEGRATION_REQUIRED"

    # -- replay status ---------------------------------------------------------

    def _replay_status(self, replay_evaluation: Any) -> str:
        if replay_evaluation is None:
            return "NOT_APPLICABLE"
        eligibility = getattr(replay_evaluation, "eligibility", None)
        if eligibility is None:
            return str(replay_evaluation)
        return eligibility.value

    # -- evidence-byte rebinding (§7) ------------------------------------------

    def _rebind_evidence(
        self, evidence_references: dict[str, str] | None
    ) -> tuple[bool, ConsumerRefusalReason | None, str | None]:
        """Re-hash the bytes the store actually holds and compare to approved.

        Returns (ok, reason, detail).  A ``None`` mapping means there is
        nothing to rebind (verdict carries no evidence references).
        """
        if not evidence_references:
            return True, None, None
        for reference, expected_digest in evidence_references.items():
            data = self.store.read(reference)
            if data is None:
                return False, ConsumerRefusalReason.EVIDENCE_BYTES_MISSING, (
                    f"evidence reference {reference!r}: no bytes at consumption"
                )
            actual = evidence_digest(data)
            if actual != expected_digest:
                return False, ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH, (
                    f"evidence reference {reference!r}: {actual} != {expected_digest}"
                )
        return True, None, None

    # -- refusal builder -------------------------------------------------------

    def _refuse(
        self,
        derived: RecordVerification,
        replay_evaluation: Any,
        reason: ConsumerRefusalReason,
        detail: str,
    ) -> ConsumerVerdict:
        return ConsumerVerdict(
            decision=ConsumerDecision.REFUSE,
            verified_field_allowlist=derived.fields_verified,
            unverified_dimensions=derived.unverified_dimensions,
            trust_scope=derived.trust_scope,
            pit_status="ADMISSIBLE" if derived.pit_admissible else "INADMISSIBLE",
            replay_status=self._replay_status(replay_evaluation),
            custody_status="VERIFIED" if derived.custody_verified else "UNVERIFIED",
            custody_source_authorized=False,
            custody_source_authorization_status="UNAUTHORIZED",
            refusal_reason=reason,
            refusal_detail=detail,
        )

    # -- central inspection engine (§3, all four, every path) -----------------

    def _apply(
        self,
        derived: RecordVerification,
        required_fields: tuple[str, ...],
        replay_evaluation: Any,
        evidence_references: dict[str, str] | None,
        knowledge_cutoff: datetime | None = None,
    ) -> ConsumerVerdict:
        pit_status = "ADMISSIBLE" if derived.pit_admissible else "INADMISSIBLE"
        custody_status = "VERIFIED" if derived.custody_verified else "UNVERIFIED"
        replay_status = self._replay_status(replay_evaluation)

        # Inspection 1 — trust scope must be ECONOMIC_FIELD_BINDING.
        if derived.trust_scope != TRUST_SCOPE_ECONOMIC_FIELD_BINDING:
            return self._refuse(
                derived,
                replay_evaluation,
                ConsumerRefusalReason.FORGED_TRUST_SCOPE,
                "trust_scope must be ECONOMIC_FIELD_BINDING",
            )

        # Inspection 2 — unverified_dimensions must be nonempty.
        if not derived.unverified_dimensions:
            return self._refuse(
                derived,
                replay_evaluation,
                ConsumerRefusalReason.EMPTY_UNVERIFIED_DIMENSIONS,
                "unverified_dimensions must be nonempty",
            )

        # §7 — evidence-byte rebinding at consumption time.
        rebind_ok, rebind_reason, rebind_detail = self._rebind_evidence(
            evidence_references
        )
        if not rebind_ok:
            return self._refuse(
                derived, replay_evaluation, rebind_reason, rebind_detail  # type: ignore[arg-type]
            )

        # Inspection 4 — fields_verified is the allowlist.
        fv = set(derived.fields_verified)
        for rf in required_fields:
            if rf not in fv:
                return self._refuse(
                    derived,
                    replay_evaluation,
                    ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST,
                    f"required field {rf!r} not in verified field allowlist",
                )

        # PIT and replay are separate (§6) and are adjudicated BEFORE authority:
        # an inadmissible record is refused whatever the custody source claims.
        if not derived.pit_admissible:
            return self._refuse(
                derived,
                replay_evaluation,
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                "PIT inadmissible",
            )

        replay_blocked = (
            replay_evaluation is not None
            and getattr(replay_evaluation, "eligibility", None) is not None
            and replay_evaluation.eligibility != ReplayEligibility.ELIGIBLE
        )
        if replay_blocked:
            return self._refuse(
                derived,
                replay_evaluation,
                ConsumerRefusalReason.REPLAY_BLOCKED,
                "replay blocked",
            )

        # Inspection 3 (R5) — custody authority is decided by the policy's own
        # capability, never by the record's flag or a caller-supplied rederive.
        granted, authority_status = self._custody_grant(derived, knowledge_cutoff)
        if not granted:
            return ConsumerVerdict(
                decision=ConsumerDecision.INTEGRATION_REQUIRED,
                verified_field_allowlist=derived.fields_verified,
                unverified_dimensions=derived.unverified_dimensions,
                trust_scope=derived.trust_scope,
                pit_status=pit_status,
                replay_status=replay_status,
                custody_status=custody_status,
                custody_source_authorized=False,
                custody_source_authorization_status="INTEGRATION_REQUIRED",
                refusal_reason=None,
                refusal_detail=(
                    "custody source not authorized by policy-owned authority"
                ),
            )

        return ConsumerVerdict(
            decision=ConsumerDecision.ACCEPT_FIELD_BINDING,
            verified_field_allowlist=derived.fields_verified,
            unverified_dimensions=derived.unverified_dimensions,
            trust_scope=derived.trust_scope,
            pit_status=pit_status,
            replay_status=replay_status,
            custody_status=custody_status,
            custody_source_authorized=authority_status == "AUTHORIZED",
            custody_source_authorization_status=authority_status,
            refusal_reason=None,
            refusal_detail=None,
        )

    # -- public entry points --------------------------------------------------

    def evaluate(
        self,
        candidate: RecordVerification | None,
        rederive: Callable[[], RecordVerification],
        required_fields: tuple[str, ...] = (),
        replay_evaluation: Any = None,
        evidence_references: dict[str, str] | None = None,
        knowledge_cutoff: datetime | None = None,
    ) -> ConsumerVerdict:
        """Evaluate a verdict, re-deriving it before any inspection.

        ``candidate`` is the stored/copied/deserialized verdict (may be None for
        a fresh single-record evaluation).  ``rederive`` produces a fresh
        ``RecordVerification`` from the policy's own trusted context — never a
        context supplied by the record's producer (§4).
        """
        try:
            derived = rederive()
        except RecordVerificationError as exc:
            return ConsumerVerdict(
                decision=ConsumerDecision.REFUSE,
                verified_field_allowlist=(),
                unverified_dimensions=(),
                trust_scope="",
                pit_status="INADMISSIBLE",
                replay_status=self._replay_status(replay_evaluation),
                custody_status="UNVERIFIED",
                custody_source_authorized=False,
                custody_source_authorization_status="UNAUTHORIZED",
                refusal_reason=ConsumerRefusalReason.VERIFICATION_FAILED,
                refusal_detail=str(exc),
            )

        # §4 — copied/deserialized verdicts must not be trusted automatically.
        if candidate is not None:
            checks = [
                ("approval_id", candidate.approval_id, derived.approval_id),
                ("registry_digest", candidate.registry_digest, derived.registry_digest),
                ("artifact_id", candidate.artifact_id, derived.artifact_id),
                ("trust_scope", candidate.trust_scope, derived.trust_scope),
                ("fields_verified", candidate.fields_verified, derived.fields_verified),
                (
                    "custody_source_authorized",
                    candidate.custody_source_authorized,
                    derived.custody_source_authorized,
                ),
            ]
            for name, a, b in checks:
                if a != b:
                    return self._refuse(
                        derived,
                        replay_evaluation,
                        ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE,
                        f"{name}: candidate={a!r} derived={b!r}",
                    )

        return self._apply(
            derived,
            required_fields,
            replay_evaluation,
            evidence_references,
            knowledge_cutoff,
        )

    def evaluate_cached(
        self,
        candidate: RecordVerification,
        rederive: Callable[[], RecordVerification],
        required_fields: tuple[str, ...] = (),
        replay_evaluation: Any = None,
        evidence_references: dict[str, str] | None = None,
        knowledge_cutoff: datetime | None = None,
    ) -> ConsumerVerdict:
        """Explicit cached-verdict path (§4) — alias for ``evaluate``."""
        return self.evaluate(
            candidate,
            rederive,
            required_fields,
            replay_evaluation,
            evidence_references,
            knowledge_cutoff,
        )


# --------------------------------------------------------------------------- #
# Fixtures — build a valid RecordVerification (no extra fields)               #
# --------------------------------------------------------------------------- #


def _base_verdict(**overrides: Any) -> RecordVerification:
    payload: dict[str, Any] = {
        "record_kind": "TRADE",
        "artifact_id": ARTIFACT_ID,
        "approval_id": APPROVAL_ID,
        "registry_digest": REGISTRY_DIGEST,
        "provider": "VENUE_A",
        "semantic_mapping_approved": True,
        "record_transformation_verified": True,
        "custody_verified": True,
        "source_lineage_verified": False,
        "pit_admissible": True,
        "instrument_authenticated": False,
        "source_revision_authenticated": False,
        "downstream_trusted": True,
        "trust_scope": TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
        "unverified_dimensions": ("SOURCE_LINEAGE", "CUSTODY_SOURCE_AUTHORITY"),
        "fields_verified": ("trade_price",),
        "custody_source_authorized": False,
    }
    payload.update(overrides)
    return RecordVerification.model_validate(payload)


def _store_with_evidence() -> DeterministicEvidenceStore:
    s = DeterministicEvidenceStore()
    s.put(REF, DOC_BYTES)
    return s


def _forged_verdict(**overrides: Any) -> RecordVerification:
    """Build a verdict that violates the model's own laws.

    Uses ``model_construct`` (no validation) because the consumer must be able
    to inspect objects that could never have been produced by the real
    verifier — a forged scope, an empty unverified set, a contradiction.
    The contract §3 exists precisely for these: they did not come from this
    verifier, so the consumer must refuse them.
    """
    base = _base_verdict()
    data = base.model_dump()
    data.update(overrides)
    return RecordVerification.model_construct(**data)


def _replay_evaluation(eligibility: ReplayEligibility) -> Any:
    class _R:
        def __init__(self, eligibility: ReplayEligibility) -> None:
            self.eligibility = eligibility
            self.reasons = ("synthetic",)

    return _R(eligibility)


def _synthetic_capability(**overrides: Any) -> "CustodyAuthorityCapability":
    """Explicit, non-authoritative capability used only to drive downstream
    field-scope logic (R5).  It can never be presented as an operator decision."""
    kwargs: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "approval_id": APPROVAL_ID,
        "registry_digest": REGISTRY_DIGEST,
        "record_kind": "TRADE",
        "knowledge_cutoff": None,
    }
    kwargs.update(overrides)
    return CustodyAuthorityCapability.synthetic_for_field_scope_tests(**kwargs)


def _shipped_manifest_bytes() -> bytes:
    root = Path(__file__).resolve().parents[3]
    return (root / TRUSTED_MANIFEST_RELPATH).read_bytes()


# --------------------------------------------------------------------------- #
# Replay-evidence factory (§5 — PIT/replay separation)                        #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Tests                                                                       #
# --------------------------------------------------------------------------- #


class TestConsumerBoundary:
    def test_three_outcomes(self) -> None:
        assert ConsumerDecision.ACCEPT_FIELD_BINDING.value == "ACCEPT_FIELD_BINDING"
        assert ConsumerDecision.REFUSE.value == "REFUSE"
        assert ConsumerDecision.INTEGRATION_REQUIRED.value == "INTEGRATION_REQUIRED"

    def test_verdict_carries_field_level_scope_not_whole_record(self) -> None:
        v = _base_verdict()
        assert v.fields_verified == ("trade_price",)
        assert v.trust_scope == TRUST_SCOPE_ECONOMIC_FIELD_BINDING
        assert v.unverified_dimensions

    def test_verdict_frozen(self) -> None:
        v = _base_verdict()
        with pytest.raises(Exception):
            v.trust_scope = "FULL_RECORD_TRUST"  # type: ignore[misc]


class TestFourInspections:
    def test_inspection1_forged_trust_scope(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(trust_scope="FULL_RECORD_TRUST")
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE

    def test_inspection2_empty_unverified_dimensions(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(unverified_dimensions=())
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EMPTY_UNVERIFIED_DIMENSIONS

    def test_inspection3_unauthorized_custody_source(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict()
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
        assert out.custody_source_authorized is False
        assert out.custody_source_authorization_status == "INTEGRATION_REQUIRED"

    def test_inspection4_unlisted_field(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v, rederive=lambda: v, required_fields=("trade_price", "trade_volume")
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST

    def test_all_inspections_preserve_unverified_dimensions(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict()
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.unverified_dimensions == v.unverified_dimensions


class TestCachedVerdictRevalidation:
    def test_forged_approval_id(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(approval_id="forged")
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_forged_registry_digest(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(registry_digest="0" * 64)
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_forged_artifact_id(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(artifact_id="forged-artifact")
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_forged_field_allowlist(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(fields_verified=("trade_price", "trade_volume"))
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_forged_trust_scope(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _forged_verdict(trust_scope="FULL_RECORD_TRUST")
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_forged_custody_source_authorized(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_cached_verdict_matching_derived_passes_inspections(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        base = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate_cached(
            base,
            rederive=lambda: base,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING


class TestEvidenceByteRebinding:
    def test_missing_bytes_refused(self) -> None:
        policy = ConsumerPolicy(store=DeterministicEvidenceStore())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISSING

    def test_substituted_bytes_refused(self) -> None:
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        store.put(REF, b"substituted bytes")
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_correct_bytes_pass(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING

    def test_digest_only_custody_without_bytes_refused(self) -> None:
        """A custody-verified verdict with no evidence references to rebind is
        not automatically trusted — missing bytes means refuse (§7)."""
        policy = ConsumerPolicy(store=DeterministicEvidenceStore())
        v = _base_verdict(custody_source_authorized=True, custody_verified=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISSING

    def test_evidence_reread_detects_tamper(self) -> None:
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store, custody_authority=_synthetic_capability())
        v = _base_verdict(custody_source_authorized=True)
        out1 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out1.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        store.put(REF, b"tampered")
        out2 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out2.decision == ConsumerDecision.REFUSE
        assert out2.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH


class TestPITReplaySeparation:
    def test_pit_admissible_replay_blocked(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        blocked = _replay_evaluation(ReplayEligibility.BLOCKED_TIMESTAMP)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=blocked,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.REPLAY_BLOCKED
        assert out.pit_status == "ADMISSIBLE"

    def test_pit_inadmissible_replay_eligible(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        eligible = _replay_evaluation(ReplayEligibility.ELIGIBLE)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=eligible,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.PIT_INADMISSIBLE
        assert out.pit_status == "INADMISSIBLE"

    def test_pit_inadmissible_replay_blocked_surfaces_both(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        blocked = _replay_evaluation(ReplayEligibility.BLOCKED_TIMESTAMP)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=blocked,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.pit_status == "INADMISSIBLE"
        assert out.replay_status == ReplayEligibility.BLOCKED_TIMESTAMP.value

    def test_pit_admissible_replay_eligible_accepts(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        v = _base_verdict(custody_source_authorized=True)
        eligible = _replay_evaluation(ReplayEligibility.ELIGIBLE)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=eligible,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.pit_status == "ADMISSIBLE"
        assert out.replay_status == ReplayEligibility.ELIGIBLE.value

    @pytest.mark.parametrize("pit_ok", [True, False])
    @pytest.mark.parametrize("replay_ok", [True, False])
    def test_four_combinations(self, pit_ok: bool, replay_ok: bool) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=pit_ok,
            downstream_trusted=pit_ok,
        )
        replay = (
            ReplayEligibility.ELIGIBLE if replay_ok else ReplayEligibility.BLOCKED_TIMESTAMP
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=_replay_evaluation(replay),
            evidence_references={REF: DOC_SHA},
        )
        expected = (
            ConsumerDecision.ACCEPT_FIELD_BINDING
            if (pit_ok and replay_ok)
            else ConsumerDecision.REFUSE
        )
        assert out.decision == expected
        if not replay_ok:
            assert out.refusal_reason in (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                ConsumerRefusalReason.PIT_INADMISSIBLE,
            )


class TestPITOffsetAndDST:
    """Attack items 14 (offset-aware equality) and 15 (DST edge cases).

    These drive the reused ``pit_availability_refusal`` rule directly: the
    consumer must never duplicate it, and it must order true instants rather
    than local wall-clock text.  Equality is admissible; a naive cutoff is a
    caller error; a DST fold resolves by instant, not by local time.
    """

    # -- 14: offset-aware equality ------------------------------------------

    def test_14_same_instant_in_different_offset_is_equal(self) -> None:
        # 14:00+02:00 is exactly 12:00+00:00; equality is admissible.
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T12:00:00+00:00",
            evaluation_at=datetime(2026, 6, 1, 14, 0, tzinfo=timezone(timedelta(hours=2))),
        )
        assert out is None

    def test_14_same_instant_written_as_z_is_equal(self) -> None:
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T12:00:00Z",
            evaluation_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
        )
        assert out is None

    def test_14_one_minute_before_in_positive_offset_refused(self) -> None:
        # 13:59+02:00 == 11:59Z, one minute before 12:00Z.
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T12:00:00+00:00",
            evaluation_at=datetime(2026, 6, 1, 13, 59, tzinfo=timezone(timedelta(hours=2))),
        )
        assert out == AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE

    def test_14_offset_equality_is_not_string_equality(self) -> None:
        # A wall-clock-equal but instant-earlier cutoff in a negative offset
        # must still be refused: 12:00-05:00 == 17:00Z, before 18:00Z.
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T18:00:00+00:00",
            evaluation_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5))),
        )
        assert out == AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE

    def test_14_naive_instant_basis_text_refused(self) -> None:
        # A naive available_at_instant cannot be ordered against a cutoff.
        with pytest.raises(ValueError):
            pit_availability_refusal(
                available_at=None,
                available_at_instant="2026-06-01T12:00:00",
                evaluation_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
            )

    # -- 15: DST edge cases --------------------------------------------------

    def test_15_dst_fall_back_resolves_by_true_instant(self) -> None:
        # America/New_York 2026-11-01 01:30 occurs twice: 05:30Z (EDT, fold=0)
        # and 06:30Z (EST, fold=1).  The rule must compare instants, so the same
        # local wall time flips admissibility across the fold.
        ny = ZoneInfo("America/New_York")
        availability = "2026-11-01T06:00:00+00:00"
        before_fold = pit_availability_refusal(
            available_at=None,
            available_at_instant=availability,
            evaluation_at=datetime(2026, 11, 1, 1, 30, tzinfo=ny, fold=0),
        )
        after_fold = pit_availability_refusal(
            available_at=None,
            available_at_instant=availability,
            evaluation_at=datetime(2026, 11, 1, 1, 30, tzinfo=ny, fold=1),
        )
        assert before_fold == AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE
        assert after_fold is None

    def test_15_dst_spring_forward_naive_local_refused(self) -> None:
        # A naive local time in a DST-observing zone carries no instant.
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-03-08T07:00:00+00:00",
            evaluation_at=datetime(2026, 3, 8, 2, 30),
        )
        assert out == AuthorityRefusal.EVALUATION_TIME_REQUIRED

    def test_15_dst_same_day_date_only_is_ambiguous(self) -> None:
        # A date-only basis certifies a day, not an instant on a DST-transition day.
        out = pit_availability_refusal(
            available_at="2026-11-01",
            available_at_instant=None,
            evaluation_at=datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("America/New_York")),
        )
        assert out == AuthorityRefusal.INTRADAY_PIT_AMBIGUOUS

    def test_15_dst_later_day_date_only_passes(self) -> None:
        out = pit_availability_refusal(
            available_at="2026-11-01",
            available_at_instant=None,
            evaluation_at=datetime(2026, 11, 2, 0, 30, tzinfo=ZoneInfo("America/New_York")),
        )
        assert out is None


class TestAdversarial:
    def test_01_forged_trust_scope(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(trust_scope="FULL_RECORD_AUTHENTICITY")
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE

    def test_02_empty_unverified_dimension_set(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(unverified_dimensions=())
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EMPTY_UNVERIFIED_DIMENSIONS

    def test_03_unverified_dimensions_omitted_during_serialization(self) -> None:
        """Deserialization must not drop unverified_dimensions."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict()
        payload = v.model_dump(mode="json")
        deserialized = RecordVerification.model_validate(payload)
        assert deserialized.unverified_dimensions == v.unverified_dimensions
        out = policy.evaluate(
            deserialized, rederive=lambda: deserialized, required_fields=("trade_price",)
        )
        assert out.unverified_dimensions == v.unverified_dimensions

    def test_04_unauthorized_custody_source(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict()
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED

    def test_05_digest_only_custody_proof(self) -> None:
        policy = ConsumerPolicy(store=DeterministicEvidenceStore())
        v = _base_verdict(custody_source_authorized=True, custody_verified=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE

    def test_06_evidence_byte_substitution(self) -> None:
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        store.put(REF, b"evil bytes")
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_07_evidence_missing_at_consumption(self) -> None:
        policy = ConsumerPolicy(store=DeterministicEvidenceStore())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE

    def test_08_copied_verdict_forged_approval_id(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(approval_id="forged-approval")
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_09_copied_verdict_forged_registry_digest(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _base_verdict(registry_digest="b" * 64)
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_10_cached_verdict_after_approval_revocation(self) -> None:
        """Derived verdict differs from cached because the re-derivation now
        fails (approval revoked) — cached claim must be refused."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        cached = _base_verdict(custody_source_authorized=True)

        def rederive_revoked() -> RecordVerification:
            raise RecordVerificationError(
                RecordVerificationRefusal.APPROVAL_REVOKED,
                "approval was revoked after the cached verdict was issued",
            )

        out = policy.evaluate_cached(
            cached, rederive=rederive_revoked, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.VERIFICATION_FAILED

    def test_11_same_day_date_only_pit_ambiguity(self) -> None:
        """A date-only approval cannot certify an instant on its own day."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.PIT_INADMISSIBLE

    def test_12_missing_approval_availability(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE

    def test_13_naive_evaluation_cutoff_refused(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        # A naive cutoff cannot be ordered against availability — re-derivation
        # would refuse with PIT_CUTOFF_REQUIRED.
        def rederive_naive() -> RecordVerification:
            raise RecordVerificationError(
                RecordVerificationRefusal.PIT_CUTOFF_REQUIRED,
                "an offset-aware instant is required",
            )

        out = policy.evaluate(
            v, rederive=rederive_naive, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.VERIFICATION_FAILED

    def test_14_pit_admissible_but_replay_blocked(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        blocked = _replay_evaluation(ReplayEligibility.BLOCKED_TIMESTAMP)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=blocked,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.REPLAY_BLOCKED
        assert out.pit_status == "ADMISSIBLE"

    def test_15_replay_eligible_but_pit_inadmissible(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        eligible = _replay_evaluation(ReplayEligibility.ELIGIBLE)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=eligible,
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.PIT_INADMISSIBLE

    def test_16_unlisted_canonical_field(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_volume",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST

    def test_17_sibling_canonical_field_substitution(self) -> None:
        """A sibling field (trade_volume) is not trade_price even on the same record."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_volume",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE

    def test_18_liquidation_record_claiming_verified_economic_transformation(self) -> None:
        """record_transformation_verified stays False for liquidation; the
        consumer must not treat a liquidation canonical side as transformation-proven."""
        v = _base_verdict(
            record_kind="LIQUIDATION",
            record_transformation_verified=False,
            downstream_trusted=False,
            fields_verified=("execution_side",),
        )
        assert v.record_transformation_verified is False
        assert v.downstream_trusted is False
        out = ConsumerPolicy(store=_store_with_evidence()).evaluate(
            v,
            rederive=lambda: v,
            required_fields=("execution_side",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED

    def test_19_batch_mixed_trusted_and_refused(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        good = _base_verdict(custody_source_authorized=True)
        bad = _forged_verdict(trust_scope="FULL_RECORD_TRUST")
        results = [
            policy.evaluate(g, rederive=lambda: g, required_fields=("trade_price",), evidence_references={REF: DOC_SHA})
            for g in (good, bad)
        ]
        assert results[0].decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert results[1].decision == ConsumerDecision.REFUSE
        assert results[1].refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE

    def test_20_refusal_incorrectly_retried_as_transient(self) -> None:
        """A digest-mismatch refusal is a data verdict, not transient."""
        store = _store_with_evidence()
        store.put(REF, b"tampered")
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH
        # Retrying with the same store yields the same refusal — not transient.
        out2 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out2.decision == ConsumerDecision.REFUSE
        assert out2.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_21_unauthenticated_source_lineage_promotion(self) -> None:
        """source_lineage_verified=True without lineage_proof is contradictory."""
        with pytest.raises((ValueError, RecordVerificationError)):
            _base_verdict(source_lineage_verified=True)

    def test_22_forged_instrument_identity(self) -> None:
        """The approval names no instrument; the verdict must say so."""
        v = _base_verdict()
        assert v.instrument_authenticated is False
        assert v.instrument_authentication_ref is None

    def test_23_missing_acquisition_lineage(self) -> None:
        """ACQUISITION_LINEAGE stays unverified; no synthesis from event time/mtime/cutoff."""
        v = _base_verdict()
        assert "ACQUISITION_LINEAGE" in v.unverified_dimensions or "SOURCE_LINEAGE" in v.unverified_dimensions

    def test_24_no_cutoff_authentication_presented_as_pit_approval(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=False,
            downstream_trusted=False,
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.PIT_INADMISSIBLE


class TestMultiPathConformance:
    def test_single_record_path(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.unverified_dimensions

    def test_cached_path(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        base = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate_cached(
            base,
            rederive=lambda: base,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
        assert out.custody_source_authorized is False
        assert out.unverified_dimensions == base.unverified_dimensions

    def test_deserialized_path(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        payload = v.model_dump(mode="json")
        deserialized = RecordVerification.model_validate(payload)
        out = policy.evaluate(
            deserialized,
            rederive=lambda: deserialized,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.unverified_dimensions == deserialized.unverified_dimensions

    def test_evidence_reread(self) -> None:
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store, custody_authority=_synthetic_capability())
        v = _base_verdict(custody_source_authorized=True)
        out1 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out1.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        store.put(REF, b"tampered")
        out2 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out2.decision == ConsumerDecision.REFUSE
        assert out2.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_error_refusal_handling_typed(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(trust_scope="WRONG_SCOPE")
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason is not None
        assert isinstance(out.refusal_reason, ConsumerRefusalReason)


class TestGovernanceScope:
    def test_integration_state_unchanged(self) -> None:
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"

    def test_trust_scope_constant(self) -> None:
        assert TRUST_SCOPE_ECONOMIC_FIELD_BINDING == "ECONOMIC_FIELD_BINDING"

    def test_no_custody_authority_created(self) -> None:
        """The harness must not manufacture custody_source_authorized=True."""
        v = _base_verdict()
        assert v.custody_source_authorized is False

    def test_no_whole_record_trust_assertion(self) -> None:
        v = _base_verdict()
        assert v.downstream_trusted is not True or bool(v.fields_verified)
        assert v.trust_scope == TRUST_SCOPE_ECONOMIC_FIELD_BINDING



class TestCustodyAuthorityBoundary:
    """SENSOR-B5-I09P3-R5 — custody authorization is policy-owned, not caller-asserted.

    RED before the repair: AT43/AT53/AT55/AT56 produced ``ACCEPT_FIELD_BINDING``
    because ``ConsumerPolicy`` treated ``custody_source_authorized`` returned by a
    caller-supplied ``rederive`` callback as authority to accept.
    """

    @staticmethod
    def _authoritative(**overrides: Any) -> RecordVerification:
        return _base_verdict(custody_source_authorized=True, **overrides)

    def test_at53_caller_supplied_true_cannot_grant_acceptance(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = self._authoritative()
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
        assert out.custody_source_authorized is False
        assert out.custody_source_authorization_status == "INTEGRATION_REQUIRED"

    def test_at43_synthetic_fixture_flag_is_not_authority(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = self._authoritative()
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorization_status != "AUTHORIZED"

    def test_at54_forged_trusted_context_cannot_mint_authority(self) -> None:
        forged = TrustedAuthorityContext.model_construct(
            manifest_sha256="0" * 64,
            artifact_id=ARTIFACT_ID,
            manifest_bytes=b'{"artifacts": {}}',
        )
        with pytest.raises((RecordVerificationError, ValueError)):
            CustodyAuthorityCapability.from_reviewed_context(
                context=forged, semantic_authority=None, knowledge_cutoff=CUTOFF
            )

    def test_at55_matching_forged_cached_and_rederived_cannot_grant(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        forged = self._authoritative()
        out = policy.evaluate_cached(
            forged,
            rederive=lambda: forged,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
        assert out.custody_source_authorization_status != "AUTHORIZED"

    def test_at56_cross_record_substitution_cannot_preserve_acceptance(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        other = self._authoritative(
            artifact_id="OTHER_ARTIFACT",
            approval_id="APPROVAL-OTHER",
            registry_digest="b" * 64,
        )
        out = policy.evaluate(
            other,
            rederive=lambda: other,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED

    def test_cross_cutoff_reuse_re_evaluates_pit_and_replay(self) -> None:
        capability = _synthetic_capability(knowledge_cutoff=CUTOFF)
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=capability
        )
        v = self._authoritative()
        later = CUTOFF + timedelta(days=1)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
            knowledge_cutoff=later,
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED

    def test_synthetic_authority_is_never_presented_as_attested(self) -> None:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=_synthetic_capability()
        )
        v = self._authoritative()
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
        assert out.custody_source_authorization_status != "AUTHORIZED"
        assert out.custody_source_authorized is False

    def test_empty_shipped_manifest_never_establishes_approval(self) -> None:
        manifest = _shipped_manifest_bytes()
        parsed = parse_approval_manifest(manifest)
        assert not parsed.artifacts
        context = TrustedAuthorityContext.from_reviewed_root(
            manifest_bytes=manifest, artifact_id=ARTIFACT_ID
        )
        with pytest.raises((RecordVerificationError, ValueError)):
            CustodyAuthorityCapability.from_reviewed_context(
                context=context, semantic_authority=None, knowledge_cutoff=CUTOFF
            )

    def test_at39_verified_evidence_bytes_do_not_authorize_source(self) -> None:
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = self._authoritative()
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
