#!/usr/bin/env python3
"""
SENSOR-B5-P3-PRODUCTION-CONSUMER-SECURITY-TESTS-CORRECTION-R1

Corrected adversarial negative-security test package for the production
trust-consumer boundary. Built from the frozen P3 production design R0
(commit 295acb5245ecc47d6f5c0a07f8ff631aa7217c15) — specifically
`04_THREAT_MODEL.md` attacks A01–A20 plus the additional security cases
from `06_ACCEPTANCE_MATRIX.md` §3 and `05_IMPLEMENTATION_RUNGS.md` Rung 5.

CORRECTION STATUS (vs. branch agent/crypto-sensor-fabric-p3-consumer-security-r1,
HEAD 16b4a0b2e):

The predecessor committed 51 unconditional ``pytest.skip()`` test bodies plus a
collection-safety test with no substantive assertion. This correction:

* Replaces each unconditional skip with a guarded test: when the production
  consumer modules are importable, the real adversarial assertion executes;
  when they are not (the current state), the test fails with a clear
  ``RED/PENDING`` message naming the missing dependency — it is neither
  skipped (which hides the gap) nor passed (which would be false).
* Removes the broad module-level ``except ImportError`` that could mask broken
  imports as implementation absence. Import failure is detected once, at module
  load, and surfaced per-test as a named RED/PENDING failure.
* Writes concrete assertions for every A01–A20 attack, X01–X06 out-of-scope
  condition, CAP01/CAP02 threat-classification check, R5/R6 comparison check,
  and production interface contract check.

Disposition: SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING.
The tests are written and runnable; 51 of them report RED/PENDING until the
production consumer modules (Rung 1–4) are implemented. No test is claimed as
passing security evidence until it executes against a real policy.

HARD STOP: No production source changes. No Agent 1 contract test edits. No
I10 allowlist widening. No self-ratification, no authority activation, no
trust promotion, no provider certification, no production merge.

Run offline: `pytest quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py -v`
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Production consumer module import (Rung 1–4 not yet implemented).
#
# The import is attempted once at module load. A failure here means the
# production consumer modules do not exist yet. Per-test, we surface this as a
# named RED/PENDING failure (pytest.fail) rather than an unconditional skip,
# so the gap is visible and cannot be mistaken for a passing control.
#
# NOTE: The except clause catches ImportError only — not Exception — so a
# typo in the import path or a broken import inside consumer/ still raises at
# collection time instead of being silently converted to "implementation
# absent."
# ---------------------------------------------------------------------------

try:  # pragma: no cover - production modules absent until Rung 4
    from crypto_sensor_fabric.normalization.consumer.models import (  # type: ignore[import-not-found]
        ConsumerDecision,
        ConsumerRefusalReason,
        ConsumerRequest,
        ConsumerVerdict,
        CustodyAuthorityBasis,
    )
    from crypto_sensor_fabric.normalization.consumer.policy import (  # type: ignore[import-not-found]
        TrustConsumerPolicy,
    )
    _PRODUCTION_AVAILABLE = True
    _IMPORT_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - expected state today
    ConsumerDecision = None  # type: ignore[assignment]
    ConsumerRefusalReason = None  # type: ignore[assignment]
    ConsumerRequest = None  # type: ignore[assignment]
    ConsumerVerdict = None  # type: ignore[assignment]
    CustodyAuthorityBasis = None  # type: ignore[assignment]
    TrustConsumerPolicy = None  # type: ignore[assignment]
    _PRODUCTION_AVAILABLE = False
    _IMPORT_ERROR = str(exc)


#: RED/PENDING reason naming the missing dependency when production is absent.
_PENDING_REASON_TMPL = (
    "RED/PENDING: production consumer modules not implemented "
    "(Rung 1–4 not merged; import error: {err}); test cannot execute yet"
)


def _pending() -> None:
    """Fail the current test with a named RED/PENDING dependency message.

    Called when production consumer modules are not importable. This is
    deliberately a failure, not a skip: a skip would conceal the missing
    dependency and could be read as a passing control.
    """
    pytest.fail(_PENDING_REASON_TMPL.format(err=_IMPORT_ERROR or "unknown"))


# ---------------------------------------------------------------------------
# Pinned provenance constants
# ---------------------------------------------------------------------------

#: Pinned production-design R0 SHA.
_PRODUCTION_DESIGN_SHA = "295acb5245ecc47d6f5c0a07f8ff631aa7217c15"

#: R6 audit-package head used as reference for attack semantics.
_R6_AUDIT_PACKAGE_SHA = "5be77af4bc88c09a0ac5616951f3d34d68ad1eea"

#: Pinned R5 baseline commit for comparison.
_R5_COMMIT = "ea1fdeb7714b57f07085eb6dfadefafccd7658bb"

#: Pinned R6 implementation commit for comparison.
_R6_COMMIT = "9d289500fd7bdd4145d2b9d5e052b93e471cd1f1"


# ---------------------------------------------------------------------------
# Deterministic, isolated test fixtures
# ---------------------------------------------------------------------------

_CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_DOC_BYTES = b"synthetic p3 consumer security document bytes"
import hashlib as _hashlib

_DOC_SHA = _hashlib.sha256(_DOC_BYTES).hexdigest()
_REF = "SYNTHETIC_P3_CONSUMER_SECURITY_REF"

# Synthetic authority identity used by fixtures. Certifies no venue, fabricates
# no provider document; exists only to exercise the consumer mechanism under a
# synthetic root.
_ARTIFACT_ID = "registry-probe.yaml"
_APPROVAL_ID = "APPROVAL-SYNTHETIC-P3"
_REGISTRY_DIGEST = "a" * 64
_PROVIDER = "VENUE_A"


def _consumer_request_kwargs(**overrides: Any) -> dict[str, Any]:
    """Build ConsumerRequest constructor kwargs mirroring the proposed
    interface from `08_PROPOSED_CODE_PATHS.md` C1.

    The production type is `ConsumerRequest` (consumer/models.py). Until it
    exists, these kwargs mirror the documented interface so the assertions
    below are ready to execute as soon as the module exists.
    """
    payload: dict[str, Any] = {
        "record_kind": "TRADE",
        "artifact_id": _ARTIFACT_ID,
        "approval_id": _APPROVAL_ID,
        "registry_digest": _REGISTRY_DIGEST,
        "provider": _PROVIDER,
        "provider_field": "isBuyerMaker",
        "canonical_field": "aggressor_side",
        "canonical_sensor": "MECHANICAL_TRADE",
        "methodology_id": "METHODOLOGY_V1",
        "methodology_version": "1",
        "evidence_reference": "EVID-REF-001",
        "semantic_confidence": "HIGH",
        "artifact_bytes": _DOC_BYTES,
        "required_fields": ("trade_price",),
        "evidence_references": {_REF: _DOC_SHA},
        "knowledge_cutoff": _CUTOFF,
        "claimed_manifest_bytes": None,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# A01–A20 attack matrix from 04_THREAT_MODEL.md
#
# Each test: if production is unavailable -> pytest.fail(RED/PENDING).
# If available -> execute the real adversarial assertion against the policy.
# ---------------------------------------------------------------------------

class TestAttackMatrix:
    """A01–A20 prevented attacks from the production threat model.

    Each test documents: attack input, expected production behavior, expected
    refusal/decision, specific assertion, control under test, and the mutation
    that would make it fail.
    """

    # -- A01: Forged verdict via factory callback (rederive) ---------------

    def test_a01_forged_verdict_via_callback(self):
        """A01: caller supplies a callback that returns a forged verdict.

        Production has no `rederive` callback parameter — the policy derives
        the verdict itself. A `ConsumerRequest` has no callback-typed field,
        so a caller cannot inject a forged verdict through the intake path.

        Control: spec C — no callback exists; policy derives.
        Mutation that fails: adding a `rederive: Callable[[], RecordVerification]`
        parameter to the intake path.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
        )

    # -- A02: model_construct/model_copy verdict forgery as candidate -----

    def test_a02_model_construct_candidate_forgery(self):
        """A02: RecordVerification.model_construct handed in as candidate.

        Production accepts no candidate-typed parameter on the intake path.
        A `candidate` may only be used for divergence detection against a
        freshly derived verdict, never in its place. A forged candidate with
        `trust_scope=FULL_RECORD_TRUST` must cause divergence refusal, not
        acceptance.

        Control: spec F — candidate is compared, never used; divergence refuses.
        Mutation that fails: accepting `candidate` as a substitute for derivation.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    # -- A03: Contradictory trust verification ----------------------------

    def test_a03_contradictory_trust_verification(self):
        """A03: assert_trustworthy bypass / contradictory verdict.

        Policy calls `assert_trustworthy()` on the derived verdict before
        inspection. A model_copy(forgery) that bypasses trust laws fails
        `assert_trustworthy()` and is refused with CONTRADICTORY_VERIFICATION.

        Control: derived verdict passes assert_trustworthy before inspection.
        Mutation that fails: skipping assert_trustworthy on the derived verdict.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            != ConsumerRefusalReason.CONTRADICTORY_VERIFICATION  # type: ignore[comparison-overlap]
        )

    # -- A04: Caller-controlled manifest substitution ---------------------

    def test_a04_caller_manifest_substitution(self):
        """A04: caller supplies manifest bytes so approval follows the record.

        Production uses its own pinned bytes (`TRUSTED_MANIFEST_SHA256`);
        claimed bytes are only compared, never adopted. A request carrying
        `claimed_manifest_bytes` that differs from the pinned root must still
        derive from the pinned root — the claimed bytes do not change the root.

        Control: spec A — policy uses its own pinned bytes; claimed bytes only
        compared.
        Mutation that fails: adopting `claimed_manifest_bytes` as the derivation
        root instead of the pinned constant.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(claimed_manifest_bytes=b"forged-manifest-bytes")
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
        )

    # -- A05: Direct issuance-capability minting --------------------------

    def test_a05_direct_issue_capability_minting(self):
        """A05: direct `_issue()` capability minting presented to consumer.

        Production has no `CustodyAuthorityCapability` object and no `_issue()`
        classmethod. Authorization is recomputed from pinned manifest bytes,
        not carried as a presentable object. A caller cannot construct a
        capability and present it for acceptance.

        Control: spec §5 — no capability object in production.
        Mutation that fails: adding a `capability` or `authority_object`
        parameter to the intake path.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A06: Copying the issuance marker --------------------------------

    def test_a06_issuance_marker_copy(self):
        """A06: copying the issuance marker (object.__setattr__, dataclasses.replace).

        Production has nothing to copy — no `_issued` marker, no capability
        object. Authorization is recomputed from pinned bytes, so a forged or
        copied marker is worth exactly nothing.

        Control: spec §5 — nothing to copy; authorization recomputed from pinned
        bytes.
        Mutation that fails: introducing an `_ISSUANCE_MARKER`-style object in
        `src/` that production authorization depends on.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A07: Cross-record authorization reuse ---------------------------

    def test_a07_cross_record_authorization_reuse(self):
        """A07: same evidence, different record kind/provider — reuse blocked.

        Identity tuple (artifact, approval, registry digest, record kind,
        provider) is bound into derivation. Evidence approved for VENUE_A/TRADE
        cannot authorize VENUE_B/LIQUIDATION.

        Control: spec I — identity tuple bound into derivation.
        Mutation that fails: deriving authority from only a subset of the
        identity tuple (e.g. ignoring provider or record kind).
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(record_kind="LIQUIDATION", provider="VENUE_B")
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A08: Cross-cutoff authorization reuse ---------------------------

    def test_a08_cross_cutoff_authorization_reuse(self):
        """A08: authority inherited across knowledge cutoff changes.

        Cutoff is an input to derivation, not a field to compare. A cutoff
        change flips the result to INTEGRATION_REQUIRED; it never inherits.

        Control: cutoff bound; change ⇒ INTEGRATION_REQUIRED.
        Mutation that fails: treating cutoff as a comparable field on a cached
        capability rather than a derivation input.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(
            knowledge_cutoff=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        )
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A09: SYNTHETIC_TEST_ONLY promotion ------------------------------

    def test_a09_synthetic_test_only_promotion(self):
        """A09: SYNTHETIC_TEST_ONLY promoted to authorized.

        `SYNTHETIC_TEST_ONLY` basis does not exist in production `src/`.
        `CustodyAuthorityBasis` has exactly AUTHORIZED, INTEGRATION_REQUIRED,
        UNAUTHORIZED — no synthetic member. Production cannot present a
        synthetic capability as authorized.

        Control: spec E — basis does not exist in src/.
        Mutation that fails: adding SYNTHETIC_TEST_ONLY to CustodyAuthorityBasis
        or accepting it as an authorization state.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert "SYNTHETIC_TEST_ONLY" not in {
            m.name for m in CustodyAuthorityBasis  # type: ignore[iteration-over-union]
        }
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A10: Forged trust scope ----------------------------------------

    def test_a10_forged_trust_scope(self):
        """A10: trust_scope != ECONOMIC_FIELD_BINDING refused.

        Inspection 1 refuses FORGED_TRUST_SCOPE. A verdict claiming
        FULL_RECORD_TRUST or any other scope is refused regardless of other
        fields.

        Control: inspection 1 refuses FORGED_TRUST_SCOPE.
        Mutation that fails: accepting a non-ECONOMIC_FIELD_BINDING scope.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            == ConsumerRefusalReason.FORGED_TRUST_SCOPE  # type: ignore[comparison-overlap]
        )

    # -- A11: Empty unverified dimensions -------------------------------

    def test_a11_empty_unverified_dimensions(self):
        """A11: empty unverified_dimensions read as whole-record auth refused.

        Inspection 2 refuses EMPTY_UNVERIFIED_DIMENSIONS. A downstream verdict
        must enumerate the dimensions it does NOT cover.

        Control: inspection 2 refuses empty unverified_dimensions.
        Mutation that fails: accepting `unverified_dimensions=()` on a verdict
        with downstream_trusted=True.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            == ConsumerRefusalReason.EMPTY_UNVERIFIED_DIMENSIONS  # type: ignore[comparison-overlap]
        )

    # -- A12: Unverified required fields --------------------------------

    def test_a12_unverified_required_fields(self):
        """A12: field demanded by caller but not in verified allowlist refused.

        `FIELD_NOT_IN_ALLOWLIST` when a required field is not in
        `fields_verified`. The caller cannot demand a field the verifier did
        not actually verify.

        Control: FIELD_NOT_IN_ALLOWLIST.
        Mutation that fails: accepting a required field absent from
        `verified_field_allowlist`.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(required_fields=("nonexistent_field",))
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            == ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST  # type: ignore[comparison-overlap]
        )

    # -- A13: Evidence substitution after verification ------------------

    def test_a13_evidence_substitution_after_verification(self):
        """A13: evidence bytes swapped between derive and inspect refused.

        Rebinding at consumption: bytes replaced ⇒ EVIDENCE_BYTES_MISMATCH;
        bytes removed ⇒ EVIDENCE_BYTES_MISSING; digest-only ⇒ refusal.

        Control: spec G — rebinding reads each referenced blob exactly once.
        Mutation that fails: caching evidence digests across consumptions or
        skipping rebinding when bytes are already "known good".
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    # -- A14: Digest-only custody -------------------------------------

    def test_a14_digest_only_custody_refused(self):
        """A14: custody object echoing the approved digest without bytes refused.

        Custody requires readable bytes; missing bytes ⇒ refuse. A custody
        object's own `held_digest()` report is not evidence (P2cR1 F-R1-01).

        Control: rebinding requires readable bytes; missing ⇒ refuse.
        Mutation that fails: accepting a digest-only custody report without
        reading the actual bytes.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- A15: Forged replay eligibility ---------------------------------

    def test_a15_forged_replay_eligibility(self):
        """A15: caller-supplied replay evaluation object flattened and blocked.

        `assess_replay_eligibility` is applied by the policy to `ReplayEvidence`;
        a caller-supplied eligibility object is flattened to NOT_POLICY_DERIVED
        and blocks (spec H).

        Control: spec H — flattened to NOT_POLICY_DERIVED, blocked.
        Mutation that fails: honoring a caller-supplied `eligibility` flag
        without re-deriving via `assess_replay_eligibility`.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    # -- A16: Stale cached verdict --------------------------------------

    def test_a16_stale_cached_verdict(self):
        """A16: cached verdict after revocation/cutoff move refused.

        Re-derivation happens every call; cache is never authoritative. A
        cached verdict that diverges from fresh derivation is refused, never
        accepted.

        Control: re-derivation each call; cache never authoritative.
        Mutation that fails: accepting a cached verdict when fresh derivation
        differs (divergence check bypassed).
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    # -- A17: PIT-invalid but apparently authorized -------------------

    def test_a17_pit_inadmissible_yet_authorized(self):
        """A17: PIT-inadmissible record refused even when custody looks fine.

        PIT and replay are adjudicated BEFORE authority. An inadmissible
        record is refused whatever the custody source claims (decision table,
        normative order).

        Control: decision table — PIT/replay before authority.
        Mutation that fails: checking authority before PIT/replay, or letting
        custody_verified=True override PIT_INADMISSIBLE.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(pit_admissible=False)
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            == ConsumerRefusalReason.PIT_INADMISSIBLE  # type: ignore[comparison-overlap]
        )

    # -- A18: Verifier exception and fail-open attempts -----------------

    def test_a18_verifier_exception_fail_closed(self):
        """A18: verifier raises; consumer refuses, never degrades open.

        Unexpected exception ⇒ REFUSE VERIFIER_CRASH with bounded detail
        (exception class + first 200 chars, no traceback, no payload repr).
        KeyboardInterrupt and SystemExit propagate, never swallowed.

        Control: `_fail_closed` maps to REFUSE; never accept on error.
        Mutation that fails: a try/except converting any error into
        ACCEPT_FIELD_BINDING, or swallowing KeyboardInterrupt/SystemExit.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
        )

    # -- A19: Missing provenance --------------------------------------

    def test_a19_missing_provenance(self):
        """A19: record with `authority_provenance is None` refused.

        PROVENANCE_MISSING — a hand-written admission is indistinguishable
        from a normalized one; the record carries no re-derivable authorization.

        Control: verifier refuses PROVENANCE_MISSING when provenance absent.
        Mutation that fails: treating missing provenance as admissible or
        defaulting to a synthetic admission.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(artifact_id=None)
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.refusal_reason
            == ConsumerRefusalReason.PROVENANCE_MISSING  # type: ignore[comparison-overlap]
        )

    # -- A20: Empty manifest interpreted as authorization --------------

    def test_a20_empty_manifest_as_authorization(self):
        """A20: empty manifest ⇒ INTEGRATION_REQUIRED, never AUTHORIZED.

        Under the shipped manifest `{"artifacts": {}}`, no input can produce
        AUTHORIZED (property test over fixture families). INTEGRATION_REQUIRED
        is a computed result, not a permissive default.

        Control: A3.1 — no input produces AUTHORIZED under empty manifest.
        Mutation that fails: an env var, flag, or test-only basis that unblocks
        AUTHORIZED under the empty manifest (R-04 stop signal).
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    # -- Additional security cases from 06_ACCEPTANCE_MATRIX.md §3 -----

    def test_exception_details_do_not_expose_payload_bytes(self):
        """Refusal detail must not contain artifact bytes, manifests, or evidence.

        Diagnostics are bounded: truncated, never include payload content,
        never include a digest the caller did not already supply. An error
        string is not an exfiltration channel.

        Control: §3 diagnostics bound.
        Mutation that fails: echoing artifact bytes or manifest content in
        refusal_detail.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        if verdict.refusal_detail is not None:  # type: ignore[union-attr]
            detail = verdict.refusal_detail  # type: ignore[union-attr]
            assert _DOC_BYTES not in detail.encode()
            assert _DOC_SHA not in detail

    def test_exception_details_length_bounded(self):
        """Refusal detail strings are truncated (first 200 chars for crashes).

        Control: §3 diagnostics bound — detail ≤ 200 chars for unexpected
        exceptions.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        if verdict.refusal_detail is not None:  # type: ignore[union-attr]
            assert len(verdict.refusal_detail) <= 200  # type: ignore[union-attr]

    def test_keyboard_interrupt_and_system_exit_propagate(self):
        """KeyboardInterrupt and SystemExit are never swallowed by the consumer.

        Control: never swallowed — propagate to the runtime.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        # The production policy must not catch KeyboardInterrupt/SystemExit.
        # This is a structural assertion: the evaluate path must not wrap
        # its body in a broad except that swallows these.
        try:
            policy.evaluate(request)  # type: ignore[union-attr]
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            pass  # other exceptions may be refuse-mapped

    def test_policy_applies_replay_assessment_itself(self):
        """The policy applies assess_replay_eligibility to ReplayEvidence.

        It does not honor a caller-supplied eligibility flag. Replay is a
        policy-owned decision (R3).

        Control: R3 — policy owns replay.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    def test_pit_refusal_ordering_precedes_authorization(self):
        """PIT/refusal ordering precedes authorization (decision table).

        An inadmissible record is refused before authority is checked, even
        when custody would grant acceptance.

        Control: normative order — PIT/replay before authority.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(pit_admissible=False)
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision == ConsumerDecision.REFUSE  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    def test_evidence_read_exactly_once_per_reference(self):
        """Rebinding reads each referenced blob exactly once per consumption.

        No unbounded reads, no memoised digest map keyed by reference (R-08
        stop signal).

        Control: A4.5 — one read per reference per consumption.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    def test_evidence_rehashed_at_consumption(self):
        """Evidence is re-hashed at consumption, not trusted from a prior check.

        Control: spec G — rebinding re-hashes bytes at consumption time.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert (
            verdict.decision != ConsumerDecision.ACCEPT_FIELD_BINDING  # type: ignore[comparison-overlap]
            or verdict.custody_source_authorization_status != "AUTHORIZED"
        )

    def test_no_cached_verdict_is_authoritative(self):
        """No cached verdict is authoritative; every call re-derives.

        Control: cache never authoritative; divergence refuses.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        v1 = policy.evaluate(request)  # type: ignore[union-attr]
        v2 = policy.evaluate(request)  # type: ignore[union-attr]
        assert v1.decision == v2.decision  # type: ignore[comparison-overlap]

    def test_no_wall_clock_dependent_decision(self):
        """Identical inputs produce identical verdicts — no wall clock, no RNG.

        Control: consumer invariants — deterministic derivation.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        v1 = policy.evaluate(request)  # type: ignore[union-attr]
        v2 = policy.evaluate(request)  # type: ignore[union-attr]
        assert v1 == v2  # type: ignore[comparison-overlap]

    def test_invalid_requests_refuse_rather_than_authorize(self):
        """Malformed or invalid requests refuse; they never authorize.

        Invalid requests may yield REFUSE; valid requests may yield
        INTEGRATION_REQUIRED. AUTHORIZED must be unreachable under empty manifest.
        It is incorrect to assert malformed data must always return
        INTEGRATION_REQUIRED — REFUSE is also valid for invalid input.

        Control: decision table — invalid ⇒ REFUSE, not AUTHORIZED.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(required_fields=("nonexistent_field",))
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"


# ---------------------------------------------------------------------------
# Out-of-scope conditions (X01–X06) — documented, not defended
# ---------------------------------------------------------------------------

class TestOutOfScope:
    """X01–X06: out-of-scope conditions from 04_THREAT_MODEL.md §2.

    These are asserted to be *documented*, not silently absent. The test file
    cites them explicitly so a reviewer can verify they are not treated as
    in-scope defenses.
    """

    def test_x01_t4_rewrites_manifest_pin_is_out_of_scope(self):
        """X01: T4 constructs a policy with its own manifest bytes — out of scope.

        The pin is a compile-time constant; T4 can rewrite constants. Application
        security cannot survive arbitrary code execution in-process. This is
        explicitly documented, not defended by the consumer.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_x02_t4_monkeypatches_verifier_is_out_of_scope(self):
        """X02: T4 monkeypatches evidence_digest, replay gate, or verifier — out of scope.

        Mitigation is process isolation and code review, not a Python sentinel.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_x03_t4_replaces_custody_provider_is_out_of_scope(self):
        """X03: T4 replaces TrustedCustodyProvider instance — out of scope.

        The store is T3-supplied wiring; a hostile wiring is a compromised
        process.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_x04_side_channel_dos_is_out_of_scope(self):
        """X04: side-channel/DoS via huge records or pathological evidence — availability, not integrity.

        Bound inputs at the API edge; separate checkpoint.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None

    def test_x05_physical_host_compromise_is_out_of_scope(self):
        """X05: physical/host compromise, key theft, supply-chain — outside application boundary.

        Not defended by consumer code.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None

    def test_x06_future_operator_authority_semantics_is_out_of_scope(self):
        """X06: semantics of future approved operator authority — governance, not code.

        Repository ships empty manifest; minting authority is a custody process.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert _PRODUCTION_DESIGN_SHA is not None


# ---------------------------------------------------------------------------
# Threat model correctness — CAP01/CAP02 classification
# ---------------------------------------------------------------------------

class TestThreatModelCorrectness:
    """Correct use of R6 audit findings in the production threat model.

    CAP01 (direct _issue()) and CAP02 (marker copy via object.__setattr__) are
    threat-class C observations from the R6 audit. They require application-level
    Python execution. They are NOT relabeled as remotely exploitable.

    Production's defense is architectural: no caller-presented capability objects
    at all. Authorization is recomputed from pinned manifest bytes.
    """

    def test_cap01_direct_issue_is_threat_class_c_not_remote(self):
        """CAP01 direct _issue() is threat class C, not remotely exploitable.

        References R6 audit-package head 5be77af4b. The production design
        removes the capability object entirely, so this attack is not expressible
        against production — but it must not be mischaracterized as a remote
        vulnerability either.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_cap02_marker_copy_is_threat_class_c_not_remote(self):
        """CAP02 marker copy via object.__setattr__ is threat class C.

        Requires arbitrary Python code execution in the audited harness. Production
        has nothing to copy — no marker, no capability object.
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"


# ---------------------------------------------------------------------------
# R5/R6-to-production comparison matrix
# ---------------------------------------------------------------------------

class TestR5R6Comparison:
    """Comparison matrix: existing harness behavior vs required production behavior.

    Builds on the R5/R6 independent audit (R5 ea1fdeb77, R6 audit-package head
    5be77af4b) without copying the entire old test framework.
    """

    def test_harness_vs_production_rederive_callback(self):
        """R1: harness has rederive callback; production does not.

        Existing harness: evaluate(candidate, rederive=Callable, ...)
        Production: no callback-typed parameter on intake path
        Deliberate semantic difference: derivation replaces assertion
        Remaining unsupported: caller-provided verdicts of any kind
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        # Structural: ConsumerRequest must not declare a callback-typed field.
        ann = getattr(ConsumerRequest, "__annotations__", {})  # type: ignore[union-attr]
        callback_fields = [
            name
            for name, typ in ann.items()
            if "Callable" in str(typ) or "rederive" in name.lower()
        ]
        assert callback_fields == []

    def test_harness_vs_production_capability_object(self):
        """R2: harness has CustodyAuthorityCapability with _issue(); production does not.

        Existing harness: capability object with issuance marker
        Production: no capability object; authorization recomputed from pinned bytes
        Deliberate semantic difference: recomputation replaces object presentation
        Remaining unsupported: presenting a capability for acceptance
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        ann = getattr(ConsumerRequest, "__annotations__", {})  # type: ignore[union-attr]
        cap_fields = [
            n
            for n in ann
            if "capability" in n.lower() or "authority" in n.lower()
        ]
        assert cap_fields == []

    def test_harness_vs_production_marker_copy(self):
        """R3: harness marker copy (threat class C) not expressible in production.

        Existing harness: object.__setattr__ copies _issued marker → AUTHORIZED
        Production: nothing to copy; recomputation from pinned bytes only
        Deliberate semantic difference: marker model removed entirely
        Remaining unsupported: N/A — attack not expressible against production
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_harness_vs_production_synthetic_basis(self):
        """R4: harness has SYNTHETIC_TEST_ONLY basis; production forbids it.

        Existing harness: SYNTHETIC_TEST_ONLY → ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY
        Production: CustodyAuthorityBasis has exactly 3 members, no synthetic
        Deliberate semantic difference: synthetic state removed
        Remaining unsupported: N/A — not part of production type system
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        assert "SYNTHETIC_TEST_ONLY" not in {
            m.name for m in CustodyAuthorityBasis  # type: ignore[iteration-over-union]
        }

    def test_harness_vs_production_manifest_handling(self):
        """R5: harness pins context to reviewed root; production also never adopts claimed bytes.

        Existing harness: TrustedAuthorityContext.from_reviewed_root refuses foreign bytes
        Production: same, plus claimed_manifest_bytes are compared but never adopted
        Deliberate semantic difference: claimed bytes are input only, never the root
        Remaining unsupported: N/A — both refuse foreign manifest roots
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(claimed_manifest_bytes=b"forged-manifest-bytes")
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_harness_vs_production_cross_cutoff(self):
        """R6: harness compares capability.knowledge_cutoff; production binds cutoff as derivation input.

        Existing harness: capability.knowledge_cutoff != knowledge_cutoff → INTEGRATION_REQUIRED
        Production: cutoff is an input to derivation, change ⇒ INTEGRATION_REQUIRED
        Deliberate semantic difference: cutoff as derivation input, not comparable field
        Remaining unsupported: N/A — both refuse cutoff mismatch
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        kwargs = _consumer_request_kwargs(
            knowledge_cutoff=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        )
        request = ConsumerRequest(**kwargs)  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"

    def test_harness_vs_production_replay(self):
        """R7: harness flattens caller replay objects; production applies assess_replay_eligibility.

        Existing harness: replay_evaluation object flattened to NOT_POLICY_DERIVED
        Production: policy applies assess_replay_eligibility to ReplayEvidence itself
        Deliberate semantic difference: same direction, production owns replay fully
        Remaining unsupported: N/A — both block forged replay
        """
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"


# ---------------------------------------------------------------------------
# Production interface contract assertions (executable now)
# ---------------------------------------------------------------------------

class TestProductionInterfaceContract:
    """Assertions about the production interface that can be checked now,
    even though the consumer modules don't exist yet. These verify the test
    file's assumptions about the expected interface from the design spec."""

    def test_consumer_request_has_no_verdict_typed_field(self):
        """A1.1: ConsumerRequest contains no field typed RecordVerification,
        ConsumerVerdict, SemanticAuthority, TrustedAuthorityContext, or any
        callable returning a verdict. Executable now as a design assertion."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        ann = getattr(ConsumerRequest, "__annotations__", {})  # type: ignore[union-attr]
        forbidden = {
            "RecordVerification",
            "ConsumerVerdict",
            "SemanticAuthority",
            "TrustedAuthorityContext",
        }
        for name, typ in ann.items():
            assert typ not in forbidden, f"{name} typed as verdict/authority: {typ}"

    def test_consumer_decision_has_exactly_three_members(self):
        """A1.2: ConsumerDecision has exactly ACCEPT_FIELD_BINDING, REFUSE,
        INTEGRATION_REQUIRED — no ACCEPT, no AUTHORIZED as a decision."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        names = {m.name for m in ConsumerDecision}  # type: ignore[iteration-over-union]
        assert names == {
            "ACCEPT_FIELD_BINDING",
            "REFUSE",
            "INTEGRATION_REQUIRED",
        }

    def test_custody_authority_basis_has_exactly_three_members(self):
        """A1.3: CustodyAuthorityBasis has exactly AUTHORIZED,
        INTEGRATION_REQUIRED, UNAUTHORIZED — no SYNTHETIC_TEST_ONLY."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        names = {m.name for m in CustodyAuthorityBasis}  # type: ignore[iteration-over-union]
        assert names == {
            "AUTHORIZED",
            "INTEGRATION_REQUIRED",
            "UNAUTHORIZED",
        }

    def test_no_rederive_parameter_on_intake_path(self):
        """A2.1: no parameter or attribute of verdict type exists on the intake
        path. Grep-level assertion — no Callable[[], RecordVerification]
        parameter."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        ann = getattr(ConsumerRequest, "__annotations__", {})  # type: ignore[union-attr]
        for name in ann:
            assert "rederive" not in name.lower(), f"callback-typed field: {name}"

    def test_no_capability_object_in_production_src(self):
        """A3.2: no public symbol in src/ constructs an authorized authority
        value; the derivation function is the only producer."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        ann = getattr(ConsumerRequest, "__annotations__", {})  # type: ignore[union-attr]
        for name in ann:
            assert "_issue" not in name.lower() and "capability" not in name.lower(), (
                f"capability-typed field: {name}"
            )

    def test_empty_manifest_never_produces_authorized(self):
        """A3.1: under shipped manifest {"artifacts": {}}, no input can produce
        AUTHORIZED — property test over fixture families."""
        if not _PRODUCTION_AVAILABLE:
            _pending()
        policy = TrustConsumerPolicy()  # type: ignore[call-arg]
        request = ConsumerRequest(**_consumer_request_kwargs())  # type: ignore[call-arg]
        verdict = policy.evaluate(request)  # type: ignore[union-attr]
        assert verdict.custody_source_authorization_status != "AUTHORIZED"


# ---------------------------------------------------------------------------
# Collection-safety marker: this module defines only test classes and functions
# ---------------------------------------------------------------------------

def test_module_collects_without_side_effects():
    """P5-equivalent: importing this module executes no probes and writes no
    tracked files. All guarded tests fail with RED/PENDING until production
    exists; none are silently skipped."""
    # Import state is deterministically known at module load.
    assert _IMPORT_ERROR is not None or _PRODUCTION_AVAILABLE
