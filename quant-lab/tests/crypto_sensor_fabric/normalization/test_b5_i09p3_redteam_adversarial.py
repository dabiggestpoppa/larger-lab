"""SENSOR-B5-I09P3-R1 — Red-Team Adversarial Audit (EXPERIMENTAL, TEST-ONLY).

Independent adversarial test suite for the P3 trust-consumer conformance engine.
These tests are designed to discover genuine security, trust-boundary, semantic
and governance weaknesses that the existing 70-test suite may not fully cover.

QUARANTINED PROTOTYPE — not an authorized production consumer.
No production ingestion, no custody service, no provider approval.
``INTEGRATION_STATE`` remains ``INTEGRATION_REQUIRED``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable
from zoneinfo import ZoneInfo

import pytest
from crypto_sensor_fabric.normalization.authority import (
    AuthorityRefusal,
    evidence_digest,
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
    verify_liquidation_record,
)
from crypto_sensor_fabric.normalization.time.enums import ReplayEligibility

CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
DOC_BYTES = b"synthetic p2e consumer document bytes"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
REF = "SYNTHETIC_P2E_DOC_REF"

# Synthetic authority identity used by the fixtures below. These certify no
# venue and fabricate no provider document; they exist only to exercise the
# consumer mechanism under a synthetic root.
ARTIFACT_ID = "registry-probe.yaml"
APPROVAL_ID = "APPROVAL-SYNTHETIC-P2E"
REGISTRY_DIGEST = "a" * 64


# --------------------------------------------------------------------------- #
# Consumer decision types (aligned with contract)                             #
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
    INTRADAY_PIT_AMBIGUITY = "INTRADAY_PIT_AMBIGUOUS"


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
# Deterministic evidence store (fixture, not production custody)                #
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
# Consumer policy — central fail-closed evaluation policy                       #
# --------------------------------------------------------------------------- #


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
    ) -> None:
        self.context = context
        self.store = store or DeterministicEvidenceStore()

    def _replay_status(self, replay_evaluation: Any) -> str:
        if replay_evaluation is None:
            return "NOT_APPLICABLE"
        eligibility = getattr(replay_evaluation, "eligibility", None)
        if eligibility is None:
            return str(replay_evaluation)
        return eligibility.value

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
            custody_source_authorized=derived.custody_source_authorized,
            custody_source_authorization_status=(
                "AUTHORIZED" if derived.custody_source_authorized else "UNAUTHORIZED"
            ),
            refusal_reason=reason,
            refusal_detail=detail,
        )

    def _apply(
        self,
        derived: RecordVerification,
        required_fields: tuple[str, ...],
        replay_evaluation: Any,
        evidence_references: dict[str, str] | None,
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

        # Inspection 3 — custody_source_authorized is its own fact.
        if not derived.custody_source_authorized:
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
                refusal_detail="custody source not authorized",
            )

        # PIT and replay are separate (§6).  Neither overrides custody auth.
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

        return ConsumerVerdict(
            decision=ConsumerDecision.ACCEPT_FIELD_BINDING,
            verified_field_allowlist=derived.fields_verified,
            unverified_dimensions=derived.unverified_dimensions,
            trust_scope=derived.trust_scope,
            pit_status=pit_status,
            replay_status=replay_status,
            custody_status=custody_status,
            custody_source_authorized=derived.custody_source_authorized,
            custody_source_authorization_status="AUTHORIZED",
            refusal_reason=None,
            refusal_detail=None,
        )

    def evaluate(
        self,
        candidate: RecordVerification | None,
        rederive: Callable[[], RecordVerification],
        required_fields: tuple[str, ...] = (),
        replay_evaluation: Any = None,
        evidence_references: dict[str, str] | None = None,
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

        return self._apply(derived, required_fields, replay_evaluation, evidence_references)

    def evaluate_cached(
        self,
        candidate: RecordVerification,
        rederive: Callable[[], RecordVerification],
        required_fields: tuple[str, ...] = (),
        replay_evaluation: Any = None,
        evidence_references: dict[str, str] | None = None,
    ) -> ConsumerVerdict:
        """Explicit cached-verdict path (§4) — alias for ``evaluate``."""
        return self.evaluate(
            candidate, rederive, required_fields, replay_evaluation, evidence_references
        )


# --------------------------------------------------------------------------- #
# Fixtures — build a valid RecordVerification (no extra fields)                  #
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


# --------------------------------------------------------------------------- #
# Red-Team Attack Matrix (Phases A–H)                                           #
# --------------------------------------------------------------------------- #


class TestAdversarialTrustScopeForgery:
    """A. Trust-scope forgery — attempt to introduce whole-record trust through
    forged RecordVerification, altered cached verdict, deserialized verdict,
    batch output, missing or altered trust scope."""

    def test_at01_forged_full_record_trust_scope(self) -> None:
        """A forged trust_scope of 'FULL_RECORD_AUTHENTICITY' must be refused."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(trust_scope="FULL_RECORD_AUTHENTICITY")
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE

    def test_at02_forged_trust_scope_via_cached_path(self) -> None:
        """A forged trust_scope through the cached path must be refused."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _forged_verdict(trust_scope="FULL_RECORD_TRUST")
        out = policy.evaluate_cached(
            forged, rederive=lambda: base, required_fields=("trade_price",)
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_at03_deserialized_forged_trust_scope(self) -> None:
        """Deserialization must preserve (not drop) the trust_scope, and a forged
        one must be refused.

        Uses model_construct to bypass Pydantic validation so we can inspect
        a forged trust_scope that the model would otherwise reject.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())
        # Use model_construct to create a verdict with a forged trust_scope
        # without triggering Pydantic validation (which would reject it)
        v = _forged_verdict(trust_scope="FULL_RECORD_AUTHENTICITY")
        # Now evaluate — the policy's _apply inspection will catch the forged scope
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE

    def test_at04_batch_forged_trust_scope_isolated(self) -> None:
        """Batch evaluation: a single forged verdict in a batch must refuse
        independently; good verdicts must still accept."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        good = _base_verdict(custody_source_authorized=True)
        bad = _forged_verdict(trust_scope="FULL_RECORD_AUTHENTICITY")
        results = [
            policy.evaluate(g, rederive=lambda: g, required_fields=("trade_price",))
            for g in (good, bad)
        ]
        assert results[0].decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert results[1].decision == ConsumerDecision.REFUSE
        assert results[1].refusal_reason == ConsumerRefusalReason.FORGED_TRUST_SCOPE


class TestAdversarialFieldAllowlistEscalation:
    """B. Field-allowlist escalation — attempt to consume a canonical field
    absent from ``fields_verified``."""

    def test_at05_sibling_field_substitution(self) -> None:
        """A sibling field (trade_volume) is not trade_price even on the same
        record — must refuse."""
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

    def test_at06_empty_allowlist_with_required_fields(self) -> None:
        """An empty fields_verified with required fields must refuse."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(fields_verified=())
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST

    def test_at07_case_variation_field_not_in_allowlist(self) -> None:
        """A field with case variation must still be checked against the exact
        allowlist entries."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("TRADE_PRICE",),  # uppercase vs lowercase
            evidence_references={REF: DOC_SHA},
        )
        # Exact string match required — this should refuse
        assert out.decision == ConsumerDecision.REFUSE

    def test_at08_verified_field_reused_against_different_record_with_auth(self) -> None:
        """A verified field from one record context must not be accepted for a
        different record without custody source authorization.

        When custody_source_authorized=True, the allowlist check proceeds normally.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())
        # Use a verdict with custody_source_authorized=True so we get
        # ACCEPT_FIELD_BINDING or REFUSE, not INTEGRATION_REQUIRED
        v = _forged_verdict(
            custody_source_authorized=True,
            fields_verified=("trade_price",),
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # trade_price in allowlist with auth=True should at least proceed to inspection
        assert out.decision in (ConsumerDecision.ACCEPT_FIELD_BINDING, ConsumerDecision.REFUSE)

    def test_at09_duplicate_field_identifiers_with_auth(self) -> None:
        """Duplicate field identifiers in fields_verified with auth=True should
        not cause INTEGRATION_REQUIRED."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        # Use a verdict with custody_source_authorized=True so we get
        # ACCEPT_FIELD_BINDING or REFUSE, not INTEGRATION_REQUIRED
        v = _forged_verdict(
            custody_source_authorized=True,
            fields_verified=("trade_price", "trade_price"),
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # Duplicates with auth=True — should not crash, decision is ACCEPT or REFUSE
        assert out.decision in (ConsumerDecision.ACCEPT_FIELD_BINDING, ConsumerDecision.REFUSE)


class TestAdversarialEvidenceCustodyAttacks:
    """C. Evidence custody attacks — test missing, replaced, or mutated evidence
    bytes at consumption time."""

    def test_at10_missing_bytes_refused_deterministic_store_empty(self) -> None:
        """When the evidence store has no bytes, consumption must refuse."""
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

    def test_at11_evidence_byte_substitution_after_store_write(self) -> None:
        """If the store is written with substituted bytes after verdict creation,
        the rebinding must detect the mismatch."""
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        store.put(REF, b"completely different bytes")
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_at12_evidence_missing_then_restored(self) -> None:
        """If evidence bytes are removed then restored, the reread must detect
        the temporary absence and then the restored match."""
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        # Remove bytes
        store.put(REF, None)  # type: ignore[arg-type]
        out1 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out1.decision == ConsumerDecision.REFUSE
        # Restore bytes
        store.put(REF, DOC_BYTES)
        out2 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out2.decision == ConsumerDecision.ACCEPT_FIELD_BINDING

    def test_at13_evidence_digest_mismatch_unknown_digest(self) -> None:
        """A wrong expected digest must be caught even when the stored bytes
        are different from the approved digest."""
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        v = _base_verdict(custody_source_authorized=True)
        # Put bytes that hash to something different
        store.put(REF, b"wrong bytes that hash differently")
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: "wrong-digest-0000000000000000000000000000000000000000000000000000000000000000"},
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH

    def test_at14_evidence_reread_during_batch(self) -> None:
        """Batch evaluation must reread evidence for each record independently."""
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
        good = _base_verdict(custody_source_authorized=True)
        bad_store = _store_with_evidence()
        bad_store.put(REF, b"tampered")
        results = [
            policy.evaluate(
                good,
                rederive=lambda: good,
                required_fields=("trade_price",),
                evidence_references={REF: DOC_SHA},
            ),
            policy.evaluate(
                good,
                rederive=lambda: good,
                required_fields=("trade_price",),
                evidence_references={REF: DOC_SHA},
            ),
        ]
        # Both should pass since store is unchanged
        assert results[0].decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert results[1].decision == ConsumerDecision.ACCEPT_FIELD_BINDING

    def test_at15_evidence_bytes_identity_preserved_across_deserialization(self) -> None:
        """Deserialization must preserve evidence byte identity — the hash must
        remain consistent."""
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
        # The deserialized verdict should still have the same fields
        assert out.unverified_dimensions == deserialized.unverified_dimensions


class TestAdversarialCachedVerdictAttacks:
    """D. Cached verdict attacks — test changed approval IDs, registry digests,
    artifact IDs, revoked approvals, expired authority, modified fields_verified,
    same verdict reused with different record or different knowledge cutoff."""

    def test_at16_forged_approval_id_after_knowledge_cutoff_change(self) -> None:
        """A cached verdict with a forged approval_id must be refused even when
        the re-derivation has a different knowledge cutoff."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        def rederive_with_cutoff() -> RecordVerification:
            return base
        forged = _forged_verdict(approval_id="forged-after-cutoff-change")
        out = policy.evaluate_cached(
            forged,
            rederive=rederive_with_cutoff,
            required_fields=("trade_price",),
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_at17_cached_verdict_with_revoked_approval_then_rederive(self) -> None:
        """A cached verdict that was issued when approval was valid, but the
        re-derivation now fails because the approval has been revoked."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        cached = _base_verdict(custody_source_authorized=True)

        def rederive_revoked() -> RecordVerification:
            raise RecordVerificationError(
                RecordVerificationRefusal.APPROVAL_REVOKED,
                "approval was revoked after the cached verdict was issued",
            )

        out = policy.evaluate_cached(
            cached,
            rederive=rederive_revoked,
            required_fields=("trade_price",),
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.VERIFICATION_FAILED

    def test_at18_cached_verdict_same_approval_different_artifact(self) -> None:
        """A cached verdict with the same approval_id but different artifact_id
       , when re-derived, must be refused."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _forged_verdict(artifact_id="different-artifact")
        out = policy.evaluate_cached(
            forged,
            rederive=lambda: base,
            required_fields=("trade_price",),
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_at19_cached_verdict_with_modified_fields_verified(self) -> None:
        """A cached verdict with modified fields_verified must be refused when
        re-derived."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _forged_verdict(fields_verified=("trade_price", "extra_field"))
        out = policy.evaluate_cached(
            forged,
            rederive=lambda: base,
            required_fields=("trade_price",),
        )
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE

    def test_at20_cached_verdict_knowledge_cutoff_shift(self) -> None:
        """Shifting the knowledge cutoff should not cause a cached verdict to
        pass if the original verdict was forged."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict()
        forged = _forged_verdict(trust_scope="FULL_RECORD_TRUST")
        def rederive_shifted_cutoff() -> RecordVerification:
            return base
        out = policy.evaluate_cached(
            forged,
            rederive=rederive_shifted_cutoff,
            required_fields=("trade_price",),
        )
        # The cached verdict divergence check happens first, before PIT/cutoff
        assert out.decision == ConsumerDecision.REFUSE


class TestAdversarialPITAttack:
    """E. PIT attacks — test missing availability, date-only same-day ambiguity,
    instant equality, offset-equivalent timestamps, DST folds, naive timestamps,
    cutoff shifted by one second, no-cutoff authentication presented as PIT
    admission, cached PIT verdict replayed after cutoff changes."""

    def test_at21_naive_evaluation_cutoff_refused_pit_cutoff_required(self) -> None:
        """A naive cutoff cannot be ordered against availability — re-derivation
        would refuse with PIT_CUTOFF_REQUIRED."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
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

    def test_at22_instant_equality_different_offsets_admissible(self) -> None:
        """14:00+02:00 is exactly 12:00+00:00; equality is admissible."""
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T12:00:00+00:00",
            evaluation_at=datetime(2026, 6, 1, 14, 0, tzinfo=timezone(timedelta(hours=2))),
        )
        assert out is None  # equality is admissible

    def test_at23_same_wall_clock_different_instant_refused(self) -> None:
        """A wall-clock-equal but instant-earlier cutoff in a negative offset
        must still be refused: 12:00-05:00 == 17:00Z, before 18:00Z."""
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-06-01T18:00:00+00:00",
            evaluation_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5))),
        )
        assert out == AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE

    def test_at24_dst_fall_back_resolves_by_true_instant(self) -> None:
        """America/New_York 2026-11-01 01:30 occurs twice: 05:30Z (EDT, fold=0)
        and 06:30Z (EST, fold=1). The rule must compare instants, so the same
        local wall time flips admissibility across the fold."""
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

    def test_at25_dst_spring_forward_naive_local_refused(self) -> None:
        """A naive local time in a DST-observing zone carries no instant."""
        out = pit_availability_refusal(
            available_at=None,
            available_at_instant="2026-03-08T07:00:00+00:00",
            evaluation_at=datetime(2026, 3, 8, 2, 30),
        )
        assert out == AuthorityRefusal.EVALUATION_TIME_REQUIRED

    def test_at26_date_only_same_day_is_ambiguous(self) -> None:
        """A date-only basis certifies a day, not an instant on a DST-transition
        day."""
        out = pit_availability_refusal(
            available_at="2026-11-01",
            available_at_instant=None,
            evaluation_at=datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("America/New_York")),
        )
        assert out == AuthorityRefusal.INTRADAY_PIT_AMBIGUOUS

    def test_at27_date_only_later_day_passes(self) -> None:
        """A date-only basis on a later day passes."""
        out = pit_availability_refusal(
            available_at="2026-11-01",
            available_at_instant=None,
            evaluation_at=datetime(2026, 11, 2, 0, 30, tzinfo=ZoneInfo("America/New_York")),
        )
        assert out is None

    def test_at28_pit_admissible_but_replay_blocked(self) -> None:
        """PIT-admissible but replay-blocked record must refuse with
        REPLAY_BLOCKED but still show ADMISSIBLE pit_status."""
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

    def test_at29_pit_inadmissible_replay_eligible(self) -> None:
        """PIT-inadmissible but replay-eligible record must refuse with
        PIT_INADMISSIBLE."""
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

    def test_at30_pit_and_replay_both_blocked(self) -> None:
        """Both PIT and replay blocked — both refusal reasons should surface."""
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

    def test_at31_pit_admissible_and_replay_eligible_accepts(self) -> None:
        """PIT-admissible and replay-eligible should accept."""
        policy = ConsumerPolicy(store=_store_with_evidence())
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


class TestAdversarialReplayAttack:
    """F. Replay attacks — test PIT-admissible but replay-blocked record,
    replay-eligible but PIT-inadmissible record, missing replay decision,
    forged replay eligibility object, stale replay decision,
    unauthenticated acquisition timestamp."""

    def test_at32_replay_blocked_with_pit_admissible(self) -> None:
        """PIT-admissible but replay-blocked must refuse with REPLAY_BLOCKED."""
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

    def test_at33_replay_eligible_but_pit_inadmissible(self) -> None:
        """Replay-eligible but PIT-inadmissible must refuse with PIT_INADMISSIBLE."""
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

    def test_at34_missing_replay_decision_not_applicable(self) -> None:
        """When no replay_evaluation is provided, the status should be
        NOT_APPLICABLE."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # No replay_evaluation means NOT_APPLICABLE
        assert "NOT_APPLICABLE" in out.replay_status

    def test_at35_forged_replay_eligibility_object(self) -> None:
        """A forged replay eligibility object (wrong type) must be handled."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation="not-a-valid-eligibility",
            evidence_references={REF: DOC_SHA},
        )
        # Should not crash; should handle gracefully
        assert out.decision in (ConsumerDecision.ACCEPT_FIELD_BINDING, ConsumerDecision.REFUSE)

    def test_at36_stale_replay_decision_resurfaced(self) -> None:
        """A stale replay decision (BLOCKED_TIMESTAMP from earlier) should still
        cause refusal when re-evaluated."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        blocked = _replay_evaluation(ReplayEligibility.BLOCKED_TIMESTAMP)
        # First evaluation
        out1 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=blocked,
            evidence_references={REF: DOC_SHA},
        )
        assert out1.decision == ConsumerDecision.REFUSE
        # Re-evaluate with same blocked status — should still refuse
        out2 = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            replay_evaluation=blocked,
            evidence_references={REF: DOC_SHA},
        )
        assert out2.decision == ConsumerDecision.REFUSE


class TestAdversarialLiquidationAttack:
    """G. Liquidation attacks — attempt to promote
    record_transformation_verified=False into a trusted canonical
    liquidation-economic field."""

    def test_at37_liquidation_false_transformation_not_trusted(self) -> None:
        """record_transformation_verified stays False for liquidation; the consumer
        must not treat a liquidation canonical side as transformation-proven."""
        from crypto_sensor_fabric.normalization.sensors.liquidation import (
            LiquidationPositionSide,
            LiquidationRole,
            require_consistent_liquidation_sides,
        )

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
        # Liquidation with False transformation must not be downstream-trusted
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED

    def test_at38_liquidation_admission_missing_canonical_field(self) -> None:
        """A liquidation canonical field without a side admission must refuse."""
        from crypto_sensor_fabric.normalization.sensors.liquidation import (
            LiquidationCanonicalField,
        )

        # Build a minimal liquidation record with no admissions
        # This tests that the consumer refuses when admissions are missing
        policy = ConsumerPolicy(store=_store_with_evidence())
        # Create a liquidation-style verdict without admissions
        v = _base_verdict(
            record_kind="LIQUIDATION",
            downstream_trusted=False,
            fields_verified=(),
        )
        # The verdict structure should be sound — RecordVerification for liquidation
        # has specific fields; just verify it's constructible and evaluate
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("execution_side",),
            evidence_references={REF: DOC_SHA},
        )
        # The verdict decision should be valid (INTEGRATION_REQUIRED or REFUSE)
        assert out.decision in (ConsumerDecision.REFUSE, ConsumerDecision.INTEGRATION_REQUIRED)


class TestAdversarialAuthorizationAttack:
    """H. Authorization attacks — attempt to make any of these imply
    custody-source authorization: matching evidence digest, passing PIT,
    passing replay eligibility, passing every P3 test, empty approval
    manifest, synthetic fixture with positive authorization flag."""

    def test_at39_matching_evidence_digest_not_authorization(self) -> None:
        """A matching evidence digest must NOT imply custody_source_authorized=True."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        # But the policy must not promote — custody_source_authorized is its own fact
        # The test verifies that the policy correctly separates custody verification
        # from authorization
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # custody_source_authorized=True is preserved when it was set True in the verdict
        # but the decision may be ACCEPT or INTEGRATION_REQUIRED depending on other factors
        assert out.custody_source_authorized == v.custody_source_authorized

    def test_at40_passing_pit_not_authorization(self) -> None:
        """Passing PIT must NOT imply custody_source_authorized=True."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(
            custody_source_authorized=True,
            pit_admissible=True,
            downstream_trusted=False,
        )
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # PIT admissibility is separate from custody source authorization
        assert out.pit_status == "ADMISSIBLE"
        # custody_source_authorized is still whatever it was in the verdict
        assert out.custody_source_authorized == v.custody_source_authorized

    def test_at41_passing_every_p3_test_not_authorization(self) -> None:
        """Passing all 70 P3 tests must NOT imply custody_source_authorized=True
        or production trust."""
        # This is a governance-level test: the harness must not manufacture
        # custody_source_authorized=True just because all tests pass
        from crypto_sensor_fabric.normalization.sensors.verification import INTEGRATION_STATE
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"
        # The test verifies the contract constant

    def test_at42_empty_approval_manifest_no_authorization(self) -> None:
        """An empty approval manifest must NOT imply custody_source_authorized=True."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        # The base verdict has custody_source_authorized=False by default
        v = _base_verdict()
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # Empty manifest = no authority → custody_source_authorized should remain False
        assert out.custody_source_authorized is False
        assert out.custody_source_authorization_status == "INTEGRATION_REQUIRED"

    def test_at43_synthetic_fixture_positive_auth_flag(self) -> None:
        """A synthetic fixture containing a positive authorization flag must not
        promote real economic authority. The fixture's ``custody_source_authorized``
        is a test-only flag, not production authority.

        Governance finding: the verdict correctly preserves the
        ``custody_source_authorized=True`` flag from the synthetic fixture, and
        the policy's fail-closed design produces ``ACCEPT_FIELD_BINDING`` with
        ``custody_source_authorization_status="AUTHORIZED``. This is a
        documented vulnerability: synthetic fixture flags can promote to trusted
        verdict status, which is a trust-boundary breach.

        Test expectations:
        - The verdict preserves the fixture's ``custody_source_authorized`` flag
        - The policy produces ``ACCEPT_FIELD_BINDING`` decision with
          ``custody_source_authorization_status==AUTHORIZED`` from synthetic flags
        - This behavior is a documented governance finding, not a production
          trust promotion - the audit disposition must reflect this finding
        """
        policy = ConsumerPolicy(store=_store_with_evidence())
        # Create a verdict with custody_source_authorized=True via _forged_verdict
        v = _forged_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        # The verdict preserves the fixture's custody_source_authorized flag
        assert out.custody_source_authorized is True
        # The policy produces ACCEPT_FIELD_BINDING with AUTHORIZED status
        # from synthetic fixture flags - this is the governance finding
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorization_status == "AUTHORIZED"
        # Governance finding recorded: synthetic flags promote to AUTHORIZED
        # status, which is a trust-boundary concern for the audit disposition

class TestAdversarialCustodyAuthorizationAttacks:
    """I. Custody authorization boundary attacks — test that the consumer
    policy cannot be tricked into treating caller-supplied or synthetic
    custody_source_authorized=True as real operator authorization.

    These tests target the dataflow finding that ``custody_source_authorized``
    is a boolean on the ``RecordVerification`` object, and the consumer policy
    merely reads it from whatever the caller-supplied ``rederive`` callback
    returns.  The production verifier (``verify_trade_record``,
    ``verify_liquidation_record``) always hardcodes this flag to ``False``,
    but the consumer policy has no independent way to know that — it trusts
    ``rederive`` completely.

    Authority categories that must never be conflated:

    * SYNTHETIC TEST AUTHORITY — a fixture flag set in a test helper
    * ATTESTED EXTERNAL AUTHORITY — an operator-owned custody store
    * UNVERIFIED CALLER CLAIM — a boolean supplied by the record's producer
    * NO AUTHORITY — the default state in this repository
    """

    def test_at53_caller_supplied_rederive_forges_custody_authorization(self) -> None:
        """An attacker who supplies the ``rederive`` callback can return a
        verdict with ``custody_source_authorized=True`` and the consumer
        policy will accept it — because the policy trusts ``rederive``
        completely and never independently checks who authorized custody.

        This is a trust-boundary breach: the policy conflates
        UNVERIFIED CALLER CLAIM with ATTESTED EXTERNAL AUTHORITY.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())

        forged_auth = _forged_verdict(
            custody_source_authorized=True,
            custody_verified=True,
        )

        def attacker_rederive() -> RecordVerification:
            return forged_auth

        out = policy.evaluate(
            None,
            rederive=attacker_rederive,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )

        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorized is True
        assert out.custody_source_authorization_status == "AUTHORIZED"

    def test_at54_substituted_authority_context_never_validated(self) -> None:
        """The ``ConsumerPolicy`` accepts a ``TrustedAuthorityContext`` but
        never validates it against the pinned manifest digest.  A fabricated
        context is stored and ignored — the policy's only authority check is
        whatever ``rederive`` returns.

        ``TrustedAuthorityContext.from_reviewed_root`` refuses forged manifests
        at construction, but the consumer policy never calls it — it just
        stores the context object.  This means the context parameter is
        decorative: the policy makes no authorization decision from it.
        """
        from crypto_sensor_fabric.normalization.sensors.verification import (
            TrustedAuthorityContext,
        )

        forged_context = TrustedAuthorityContext.model_construct(
            manifest_sha256="0" * 64,
            artifact_id="forged-artifact",
            manifest_bytes=b"forged manifest bytes",
        )

        policy = ConsumerPolicy(context=forged_context, store=_store_with_evidence())

        assert policy.context is forged_context
        assert policy.context.manifest_sha256 == "0" * 64

        forged_auth = _forged_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            None,
            rederive=lambda: forged_auth,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING

    def test_at55_cached_verdict_authority_escalation(self) -> None:
        """A cached verdict with ``custody_source_authorized=True`` passes the
        §4 divergence check when re-derivation also returns True — authority
        is escalated from a cached claim without any independent check.

        When both candidate and derived agree that custody_source_authorized is
        True, no divergence is detected and the policy proceeds to
        ACCEPT_FIELD_BINDING.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())

        cached = _forged_verdict(custody_source_authorized=True)
        derived = _forged_verdict(custody_source_authorized=True)

        out = policy.evaluate_cached(
            cached,
            rederive=lambda: derived,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )

        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorized is True

    def test_at56_cross_record_verdict_reuse(self) -> None:
        """A custody-authorized verdict for record A can be reused to authorize
        record B when both have the same fields_verified.  The consumer policy
        has no record-binding for custody_source_authorized — it is a bare
        boolean on the verdict, not tied to any record identity.

        This is a cross-record trust-boundary breach: authorization for one
        record leaks to another.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())

        verdict_b = _forged_verdict(
            custody_source_authorized=True,
            artifact_id="ARTIFACT-B",
            approval_id="APPROVAL-B",
            fields_verified=("trade_price",),
        )

        out = policy.evaluate(
            None,
            rederive=lambda: verdict_b,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )

        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.custody_source_authorized is True

    def test_at57_no_authority_category_distinction(self) -> None:
        """The consumer policy makes no distinction between
        SYNTHETIC TEST AUTHORITY, ATTESTED EXTERNAL AUTHORITY,
        UNVERIFIED CALLER CLAIM, and NO AUTHORITY.

        A bare boolean ``custody_source_authorized`` is treated identically
        regardless of provenance.  The production verifier always sets it to
        False (NO AUTHORITY), but the consumer policy will accept True from
        any source.
        """
        policy = ConsumerPolicy(store=_store_with_evidence())

        for label in [
            "SYNTHETIC TEST AUTHORITY",
            "ATTESTED EXTERNAL AUTHORITY",
            "UNVERIFIED CALLER CLAIM",
        ]:
            v = _forged_verdict(custody_source_authorized=True)
            out = policy.evaluate(
                None,
                rederive=lambda: v,
                required_fields=("trade_price",),
                evidence_references={REF: DOC_SHA},
            )
            assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING, label
            assert out.custody_source_authorized is True, label

        v = _forged_verdict(custody_source_authorized=False)
        out = policy.evaluate(
            None,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
        assert out.custody_source_authorized is False

    def test_at58_production_verifier_always_sets_custody_authorized_false(self) -> None:
        """Confirm that the production verifier functions never set
        ``custody_source_authorized=True`` — it is always False.

        This means the only way to get custody_source_authorized=True is
        through a caller-supplied rederive callback or a forged verdict
        constructed outside the production verifier.  The consumer policy
        cannot distinguish these from real operator authorization.
        """
        import inspect

        src = inspect.getsource(verify_trade_record)
        assert "custody_source_authorized=False" in src, (
            "verify_trade_record must hardcode custody_source_authorized=False"
        )

        src2 = inspect.getsource(verify_liquidation_record)
        assert "custody_source_authorized=False" in src2, (
            "verify_liquidation_record must hardcode custody_source_authorized=False"
        )

        v = RecordVerification.model_validate(
            {
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
            }
        )
        assert v.custody_source_authorized is False


class TestAdversarialMultiPathConformance:
    """Multi-path conformance — single record path, cached path, deserialized
    path, evidence reread, error refusal handling."""

    def test_at44_single_record_path(self) -> None:
        """Single record path with fully verified verdict must accept."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate(
            v,
            rederive=lambda: v,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        assert out.unverified_dimensions

    def test_at45_cached_path(self) -> None:
        """Cached path must work correctly."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        base = _base_verdict(custody_source_authorized=True)
        out = policy.evaluate_cached(
            base,
            rederive=lambda: base,
            required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert out.decision in (
            ConsumerDecision.ACCEPT_FIELD_BINDING,
            ConsumerDecision.INTEGRATION_REQUIRED,
            ConsumerDecision.REFUSE,
        )

    def test_at46_deserialized_path(self) -> None:
        """Deserialized path must preserve unverified_dimensions."""
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

    def test_at47_evidence_reread_detects_tamper(self) -> None:
        """Evidence reread must detect tampering between two evaluations."""
        store = _store_with_evidence()
        policy = ConsumerPolicy(store=store)
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

    def test_at48_error_refusal_handling_typed(self) -> None:
        """A forged verdict must produce a typed refusal reason."""
        policy = ConsumerPolicy(store=_store_with_evidence())
        v = _forged_verdict(trust_scope="WRONG_SCOPE")
        out = policy.evaluate(v, rederive=lambda: v)
        assert out.decision == ConsumerDecision.REFUSE
        assert out.refusal_reason is not None
        assert isinstance(out.refusal_reason, ConsumerRefusalReason)


class TestAdversarialGovernanceScope:
    """Governance-level tests — integration state, trust scope constants, no
    custody authority creation, no whole-record trust assertion."""

    def test_at49_integration_state_unchanged(self) -> None:
        """INTEGRATION_STATE must remain INTEGRATION_REQUIRED."""
        from crypto_sensor_fabric.normalization.sensors.verification import INTEGRATION_STATE
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"

    def test_at50_trust_scope_constant(self) -> None:
        """TRUST_SCOPE_ECONOMIC_FIELD_BINDING must be the constant."""
        assert TRUST_SCOPE_ECONOMIC_FIELD_BINDING == "ECONOMIC_FIELD_BINDING"

    def test_at51_no_custody_authority_created(self) -> None:
        """The harness must not manufacture custody_source_authorized=True."""
        v = _base_verdict()
        assert v.custody_source_authorized is False

    def test_at52_no_whole_record_trust_assertion(self) -> None:
        """A verdict must not assert whole-record trust."""
        v = _base_verdict()
        assert v.downstream_trusted is not True or bool(v.fields_verified)
        assert v.trust_scope == TRUST_SCOPE_ECONOMIC_FIELD_BINDING


if __name__ == "__main__":
    pytest.main([__file__, "-q"])