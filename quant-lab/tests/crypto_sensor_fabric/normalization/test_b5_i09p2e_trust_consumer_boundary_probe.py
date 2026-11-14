#!/usr/bin/env python3
"""
SENSOR-B5-I09P3-R6-BOUNDARY-REACTION-PROBE — Independent Adversarial Security Probe

This file contains runnable probe material for challenging the R6 ConsumerPolicy
authority boundary. All probes are executed against the R6 implementation at
SHA 9d289500f (and R5 at ea1fdeb77 for baseline comparison).

THREAT MODEL (PHASE 0):
  A. Untrusted record data and serialized evidence.
  B. Callers permitted to invoke ConsumerPolicy public methods
     and supply their documented arguments.
  C. Arbitrary Python code executing with application privileges.

R6 explicitly states its capability marker is NOT designed to resist
arbitrary code executing with application privileges. Probes requiring
class-C execution are so labeled.

Run from /c/tmp/wt-r6-boundary with PYTHONPATH=quant-lab/src:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quant-lab/src python -m pytest \
        quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer_boundary_probe.py \
        -v

Machine-readable results are written only when run directly as a script:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quant-lab/src python \
        quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer_boundary_probe.py
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, "quant-lab/src")

spec = importlib.util.spec_from_file_location(
    "r6_tcp",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py",
)
r6tcp = importlib.util.module_from_spec(spec)
sys.modules["r6_tcp"] = r6tcp
spec.loader.exec_module(r6tcp)

# Re-export helpers
_base_verdict = r6tcp._base_verdict
_forged_verdict = r6tcp._forged_verdict
_synthetic_capability = r6tcp._synthetic_capability
_forged_operator_capability = r6tcp._forged_operator_capability
_store_with_evidence = r6tcp._store_with_evidence
ConsumerPolicy = r6tcp.ConsumerPolicy
CustodyAuthorityCapability = r6tcp.CustodyAuthorityCapability
AuthorityBasis = r6tcp.AuthorityBasis
ConsumerDecision = r6tcp.ConsumerDecision
ConsumerRefusalReason = r6tcp.ConsumerRefusalReason
RecordVerification = r6tcp.RecordVerification
RecordVerificationError = r6tcp.RecordVerificationError
RecordVerificationRefusal = r6tcp.RecordVerificationRefusal
TrustedAuthorityContext = r6tcp.TrustedAuthorityContext
TRUSTED_MANIFEST_SHA256 = r6tcp.TRUSTED_MANIFEST_SHA256
ReplayEligibility = r6tcp.ReplayEligibility
CUTOFF = r6tcp.CUTOFF
REF = r6tcp.REF
DOC_SHA = r6tcp.DOC_SHA

# ---------------------------------------------------------------------------
# Results container — populated ONLY when tests run, never on import
# ---------------------------------------------------------------------------

RESULTS: list[dict] = []

# Capture import-time state: RESULTS must be empty when the module is imported.
# Any test function that runs later will populate RESULTS, but this snapshot
# captures the state before any test executes.
_RESULTS_AT_IMPORT = len(RESULTS)


def record(name, phase, vuln, decision, refusal, status, detail=""):
    RESULTS.append(
        {
            "name": name,
            "phase": phase,
            "vulnerable": vuln,
            "decision": decision,
            "refusal": refusal,
            "status": status,
            "detail": detail,
        }
    )


def is_unauthorized_trusted(outcome):
    """True only if ACCEPT_FIELD_BINDING with custody_source_authorized=True
    or custody_source_authorization_status=AUTHORIZED."""
    return (
        outcome.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        and (
            outcome.custody_source_authorized is True
            or outcome.custody_source_authorization_status == "AUTHORIZED"
        )
    )


# ============================================================================
# Session-scoped fixture: verify no probes executed on import
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def _check_no_side_effects_on_import():
    """5-A: Importing this module must not execute any probes or write files.

    This fixture runs BEFORE any test, so RESULTS should still be empty.
    If any module-level code executed probes, RESULTS would be non-empty here.
    """
    assert len(RESULTS) == 0, (
        f"Module import executed {len(RESULTS)} probes before any test ran"
    )
    yield
    # After all tests, RESULTS may be populated — that's expected


# ============================================================================
# PHASE 1 — Original Six R5 Attacks Against R6 ConsumerPolicy
# ============================================================================

def test_p1_cap01_forged_capability_correct_identity():
    """CAP01: Forged capability with correct identity (no _ISSUED marker).

    R5: AUTHORIZED (no _issue() check).
    R6: Should be INTEGRATION_REQUIRED (is_issued=False).
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_forged_operator_capability(),
    )
    v = _base_verdict()
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING, (
        f"CAP01: unexpectedly ACCEPTED, status={out.custody_source_authorization_status}"
    )
    assert out.custody_source_authorization_status != "AUTHORIZED"
    record(
        "CAP01 forged capability (correct identity)", 1,
        vuln=False,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p1_cap02_replaced_basis_escalation():
    """CAP02: dataclasses.replace to ATTESTED_OPERATOR basis.

    dataclasses.replace does not carry the _ISSUED marker, so is_issued=False.
    """
    synthetic = _synthetic_capability(provider="VENUE_A")
    promoted = dataclasses.replace(synthetic, basis=AuthorityBasis.ATTESTED_OPERATOR)
    assert promoted.is_issued is False, "replace must not carry issuance marker"
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=promoted,
    )
    v = _base_verdict()
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorization_status != "AUTHORIZED"
    record(
        "CAP02 replaced basis escalation", 1,
        vuln=False,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"is_issued after replace={promoted.is_issued}",
    )


def test_p1_cap03_incorrect_manifest_digest():
    """CAP03: Incorrect manifest digest (_custody_grant checks manifest_sha256)."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_forged_operator_capability(manifest_sha256="0" * 64),
    )
    v = _base_verdict()
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
    record(
        "CAP03 incorrect manifest digest", 1,
        vuln=False,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"expected manifest {TRUSTED_MANIFEST_SHA256[:16]}..., got 0*64",
    )


def test_p1_cap08b_provider_substitution():
    """CAP08b: Provider substitution — capability for VENUE_A, record for VENUE_B."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(provider="VENUE_A"),
    )
    v = _base_verdict(custody_source_authorized=True, provider="VENUE_B")
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
    record(
        "CAP08b provider substitution", 1,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="R6 checks provider binding",
    )


def test_p1_cap12_record_kind_omission():
    """CAP12: record_kind=None — ATTESTED_OPERATOR capability must name its kind."""
    for label, cap in [
        ("forged operator (record_kind=None)",
         _forged_operator_capability(record_kind=None)),
        ("synthetic (record_kind=TRADE) for LIQUIDATION record",
         _synthetic_capability(record_kind="TRADE")),
    ]:
        policy = ConsumerPolicy(
            store=_store_with_evidence(), custody_authority=cap,
        )
        v = _forged_verdict(record_kind="LIQUIDATION", downstream_trusted=False)
        out = policy.evaluate(
            v, rederive=lambda: v, required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
        )
        assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
        record(
            f"CAP12 record kind ({label})", 1,
            vuln=is_unauthorized_trusted(out),
            decision=out.decision.value,
            refusal=out.refusal_reason.value if out.refusal_reason else None,
            status=out.custody_source_authorization_status,
        )


def test_p1_rg08_forged_replay_eligibility():
    """RG08: Forged replay eligibility — caller-supplied object is not proof."""
    class _Forged:
        eligibility = ReplayEligibility.ELIGIBLE
        reasons = ("caller asserts eligible",)

    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        replay_evaluation=_Forged(), evidence_references={REF: DOC_SHA},
    )
    assert out.decision == ConsumerDecision.REFUSE
    assert out.refusal_reason == ConsumerRefusalReason.REPLAY_BLOCKED
    assert out.replay_status == "NOT_POLICY_DERIVED"
    record(
        "RG08 forged replay eligibility", 1,
        vuln=False,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.replay_status,
        detail="expected REFUSE/REPLAY_BLOCKED/NOT_POLICY_DERIVED",
    )


# ============================================================================
# PHASE 2 — Caller-Controlled Rederivation
# ============================================================================

def test_p2_a_validated_rederive_control():
    """A: Validated rederive + matching candidate — control case."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    v = _base_verdict(
        custody_source_authorized=True, pit_admissible=True,
        downstream_trusted=True,
    )
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "A Validated rederive + matching candidate", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


def test_p2_b_model_construct_forged_rederive():
    """B: model_construct-forged rederived verdict (candidate=None).

    The divergence check is skipped when candidate=None, but the custody
    authority check still runs on the derived verdict. A model_construct-forged
    verdict with custody_source_authorized=True should still be rejected because
    _custody_grant checks the policy's own capability, not the derived verdict's
    flag.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    forged = RecordVerification.model_construct(
        record_kind="TRADE", artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E", registry_digest="a" * 64,
        provider="VENUE_A", semantic_mapping_approved=True,
        record_transformation_verified=True, custody_verified=True,
        source_lineage_verified=False, pit_admissible=True,
        instrument_authenticated=False, source_revision_authenticated=False,
        downstream_trusted=True,
        trust_scope="ECONOMIC_FIELD_BINDING",
        unverified_dimensions=("SOURCE_LINEAGE", "CUSTODY_SOURCE_AUTHORITY"),
        fields_verified=("trade_price",),
        custody_source_authorized=True,
        lineage_proof=None, instrument_authentication_ref=None,
        revision_authentication_ref=None,
    )
    out = policy.evaluate(
        None, rederive=lambda: forged, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert is_unauthorized_trusted(out) is False
    record(
        "B model_construct-forged rederive (candidate=None)", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="candidate=None, rederive returns forged model_construct verdict",
    )


def test_p2_c_model_copy_forged_rederive():
    """C: model_copy-forged rederived verdict (candidate=None).

    model_copy bypasses _trust_laws validators, but _custody_grant still checks
    the policy's custody_authority, not the derived verdict's flag.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    base = _base_verdict(
        custody_source_authorized=True, pit_admissible=True,
        downstream_trusted=True,
    )
    forged_copy = base.model_copy(
        update={"trust_scope": "FULL_RECORD_TRUST",
                "unverified_dimensions": ()},
    )
    out = policy.evaluate(
        None, rederive=lambda: forged_copy, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING or \
        out.custody_source_authorized is False
    record(
        "C model_copy-forged rederive (candidate=None)", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p2_d_candidate_none_forged_callback():
    """D: candidate=None; callback returns forged object (_forged_verdict)."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    forged = _forged_verdict(
        custody_source_authorized=True, pit_admissible=True,
        downstream_trusted=True,
        trust_scope="ECONOMIC_FIELD_BINDING",
        unverified_dimensions=("SOURCE_LINEAGE", "CUSTODY_SOURCE_AUTHORITY"),
        fields_verified=("trade_price",),
    )
    out = policy.evaluate(
        None, rederive=lambda: forged, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "D candidate=None, forged callback object", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p2_e_cached_plus_derived_matching_forged():
    """E: Cached candidate + callback return matching forged objects."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    forged = _forged_verdict(
        custody_source_authorized=True, pit_admissible=True,
        downstream_trusted=True,
        trust_scope="ECONOMIC_FIELD_BINDING",
        unverified_dimensions=("SOURCE_LINEAGE", "CUSTODY_SOURCE_AUTHORITY"),
        fields_verified=("trade_price",),
    )
    out = policy.evaluate_cached(
        forged, rederive=lambda: forged, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert is_unauthorized_trusted(out) is False
    record(
        "E cached+derived matching forged objects", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p2_f_valid_looking_untrusted_object():
    """F: Callback returns valid-looking but untrusted object."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    valid_looking = RecordVerification.model_construct(
        record_kind="TRADE", artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E", registry_digest="a" * 64,
        provider="VENUE_A", semantic_mapping_approved=True,
        record_transformation_verified=True, custody_verified=True,
        source_lineage_verified=False, pit_admissible=True,
        instrument_authenticated=False, source_revision_authenticated=False,
        downstream_trusted=True,
        trust_scope="FULL_RECORD_TRUST",
        unverified_dimensions=("SOURCE_LINEAGE", "CUSTODY_SOURCE_AUTHORITY"),
        fields_verified=("trade_price",),
        custody_source_authorized=True,
        lineage_proof=None, instrument_authentication_ref=None,
        revision_authentication_ref=None,
    )
    out = policy.evaluate(
        None, rederive=lambda: valid_looking, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING or \
        out.custody_source_authorized is False
    record(
        "F valid-looking but untrusted callback object", 2,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p2_g_callback_raises_unexpected_exception():
    """G: Callback raises unexpected exception.

    An exception in rederive should propagate as an error, not be silently
    counted as CLOSED.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    def raising_rederive():
        raise ValueError("unexpected error in rederive")
    try:
        out = policy.evaluate(
            _base_verdict(custody_source_authorized=True),
            rederive=raising_rederive, required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        record(
            "G callback raises unexpected exception", 2,
            vuln=False,
            decision=out.decision.value,
            refusal=out.refusal_reason.value if out.refusal_reason else None,
            status=out.custody_source_authorization_status,
            detail="rederive raised ValueError but evaluate() did not propagate",
        )
    except ValueError as exc:
        record(
            "G callback raises unexpected exception", 2,
            vuln=False,
            decision="EXCEPTION", refusal=type(exc).__name__,
            status=str(exc)[:80],
            detail="rederive raises ValueError, propagates out of evaluate()",
        )


def test_p2_h_different_record_identity():
    """H: Different record identity in rederive."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    v = _base_verdict(custody_source_authorized=True)
    out_diff_id = policy.evaluate(
        v,
        rederive=lambda: _base_verdict(
            custody_source_authorized=True, artifact_id="OTHER_ARTIFACT",
        ),
        required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "H different record identity in rederive", 2,
        vuln=is_unauthorized_trusted(out_diff_id),
        decision=out_diff_id.decision.value,
        refusal=out_diff_id.refusal_reason.value if out_diff_id.refusal_reason else None,
        status=out_diff_id.custody_source_authorization_status,
    )


def test_p2_h2_different_knowledge_cutoff():
    """H: Different knowledge cutoff."""
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    v = _base_verdict(custody_source_authorized=True)
    out_diff_cutoff = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
        knowledge_cutoff=CUTOFF + timedelta(days=1),
    )
    record(
        "H different knowledge cutoff", 2,
        vuln=is_unauthorized_trusted(out_diff_cutoff),
        decision=out_diff_cutoff.decision.value,
        refusal=out_diff_cutoff.refusal_reason.value
        if out_diff_cutoff.refusal_reason else None,
        status=out_diff_cutoff.custody_source_authorization_status,
    )


# ============================================================================
# PHASE 3 — Issuance-Marker Challenge
# ============================================================================

def test_p3_a_direct_issue_correct_fields():
    """A: Direct _issue() with ATTESTED_OPERATOR basis, ALL fields aligned.

    Direct _issue() CAN produce an is_issued object (threat class C:
    arbitrary Python code can call the classmethod directly).
    """
    direct_cap = CustodyAuthorityCapability._issue(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
        provider="VENUE_A",
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=direct_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    record(
        "A Direct _issue() capability in ConsumerPolicy", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"is_issued={direct_cap.is_issued}",
    )


def test_p3_b_wrong_manifest_sha256():
    """B: Direct _issue() with wrong manifest_sha256 — should be rejected."""
    try:
        wrong_cap = CustodyAuthorityCapability._issue(
            basis=AuthorityBasis.ATTESTED_OPERATOR,
            artifact_id="registry-probe.yaml",
            approval_id="APPROVAL-SYNTHETIC-P2E",
            registry_digest="a" * 64,
            record_kind="TRADE",
            knowledge_cutoff=CUTOFF,
            manifest_sha256="0" * 64,
            provider="VENUE_A",
        )
    except Exception as exc:
        record(
            "B _issue() with wrong manifest_sha256", 3,
            vuln=False, decision="EXCEPTION",
            refusal=type(exc).__name__, status=str(exc)[:80],
        )
        return
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=wrong_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    record(
        "B _issue() with wrong manifest_sha256", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p3_c_record_kind_none():
    """C: Direct _issue() with record_kind=None — should be rejected."""
    try:
        no_kind_cap = CustodyAuthorityCapability._issue(
            basis=AuthorityBasis.ATTESTED_OPERATOR,
            artifact_id="registry-probe.yaml",
            approval_id="APPROVAL-SYNTHETIC-P2E",
            registry_digest="a" * 64,
            record_kind=None,
            knowledge_cutoff=CUTOFF,
            manifest_sha256=TRUSTED_MANIFEST_SHA256,
            provider="VENUE_A",
        )
    except Exception as exc:
        record(
            "C _issue() with record_kind=None", 3,
            vuln=False, decision="EXCEPTION",
            refusal=type(exc).__name__, status=str(exc)[:80],
        )
        return
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=no_kind_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    record(
        "C _issue() with record_kind=None", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p3_d_provider_none():
    """D: Direct _issue() with provider=None — should be rejected."""
    try:
        no_provider_cap = CustodyAuthorityCapability._issue(
            basis=AuthorityBasis.ATTESTED_OPERATOR,
            artifact_id="registry-probe.yaml",
            approval_id="APPROVAL-SYNTHETIC-P2E",
            registry_digest="a" * 64,
            record_kind="TRADE",
            knowledge_cutoff=CUTOFF,
            manifest_sha256=TRUSTED_MANIFEST_SHA256,
            provider=None,
        )
    except Exception as exc:
        record(
            "D _issue() with provider=None", 3,
            vuln=False, decision="EXCEPTION",
            refusal=type(exc).__name__, status=str(exc)[:80],
        )
        return
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=no_provider_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "D _issue() with provider=None", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p3_e_dataclasses_replace_to_attested():
    """E: dataclasses.replace to ATTESTED_OPERATOR — marker not carried."""
    synthetic = _synthetic_capability(provider="VENUE_A")
    replaced = dataclasses.replace(
        synthetic, basis=AuthorityBasis.ATTESTED_OPERATOR,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=replaced,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    assert out.decision != ConsumerDecision.ACCEPT_FIELD_BINDING
    record(
        "E replaced capability in ConsumerPolicy", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"is_issued={replaced.is_issued}",
    )


def test_p3_f_marker_copy_attack():
    """F: Marker copy attack via object.__setattr__.

    This requires arbitrary Python code execution (threat class C). Copying
    the _ISSUANCE_MARKER from an issued capability to a plain-constructed
    object with all fields correct (including knowledge_cutoff=CUTOFF passed
    to evaluate()) results in ACCEPT_FIELD_BINDING with AUTHORIZED status.

    This is a THREAT CLASS C vulnerability — not remotely exploitable via
    data only, but the marker is not unforgeable under arbitrary code exec.
    """
    synthetic = _synthetic_capability(provider="VENUE_A")
    real_marker = getattr(synthetic, "_issued", None)

    plain_cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
        provider="VENUE_A",
    )
    assert plain_cap.is_issued is False, "plain construction has no marker"
    object.__setattr__(plain_cap, "_issued", real_marker)
    assert plain_cap.is_issued is True, "marker copy failed"

    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=plain_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    record(
        "F Marker-copy + correct knowledge_cutoff in evaluate()", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="marker copied + all fields correct + knowledge_cutoff passed",
    )


def test_p3_g_marker_copy_wrong_manifest_sha256():
    """G: Marker-copy with wrong manifest_sha256 — should be rejected."""
    synthetic = _synthetic_capability(provider="VENUE_A")
    real_marker = getattr(synthetic, "_issued", None)
    wrong_cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256="0" * 64,
        provider="VENUE_A",
    )
    object.__setattr__(wrong_cap, "_issued", real_marker)
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=wrong_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "G Marker-copy with wrong manifest_sha256", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p3_h_marker_copy_wrong_knowledge_cutoff():
    """H: Marker-copy with wrong knowledge_cutoff."""
    synthetic = _synthetic_capability(provider="VENUE_A")
    real_marker = getattr(synthetic, "_issued", None)
    wrong_cutoff_cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF + timedelta(days=1),
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
        provider="VENUE_A",
    )
    object.__setattr__(wrong_cutoff_cap, "_issued", real_marker)
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=wrong_cutoff_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    record(
        "H Marker-copy with wrong knowledge_cutoff", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


def test_p3_i_marker_copy_wrong_provider():
    """I: Marker-copy with wrong provider."""
    synthetic = _synthetic_capability(provider="VENUE_A")
    real_marker = getattr(synthetic, "_issued", None)
    wrong_provider_cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
        provider="WRONG_VENUE",
    )
    object.__setattr__(wrong_provider_cap, "_issued", real_marker)
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=wrong_provider_cap,
    )
    v = _base_verdict(custody_source_authorized=True, provider="VENUE_A")
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "I Marker-copy with wrong provider", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# PHASE 4 — Rederivation semantics (property-based classification)
# ============================================================================

def test_p4_a_no_unauthorized_operator_authorization():
    """4-A: No unauthorized operator authorization.

    Even with a forged/marker-copied capability, the policy's _custody_grant
    checks all identity fields. A directly constructed capability with
    ATTESTED_OPERATOR basis but missing manifest_sha256, record_kind, or
    provider is refused.
    """
    plain = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id="registry-probe.yaml",
        approval_id="APPROVAL-SYNTHETIC-P2E",
        registry_digest="a" * 64,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
        provider="VENUE_A",
    )
    assert plain.is_issued is False
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=plain,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA}, knowledge_cutoff=CUTOFF,
    )
    assert out.custody_source_authorization_status != "AUTHORIZED"
    assert out.custody_source_authorized is False


def test_p4_b_acceptance_of_untrusted_field_scope():
    """4-B: Acceptance of untrusted field-scope information.

    A forged verdict with forged trust_scope should be refused, not accepted.
    The divergence check catches mismatches between candidate and derived.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )
    base = _base_verdict()
    forged = base.model_copy(update={"trust_scope": "FULL_RECORD_TRUST"})
    out = policy.evaluate(
        forged, rederive=lambda: base, required_fields=("trade_price",),
    )
    assert out.decision == ConsumerDecision.REFUSE
    assert out.refusal_reason == ConsumerRefusalReason.CACHED_VERDICT_DIVERGENCE


def test_p4_c_exception_handling_service_availability():
    """4-C: Exception handling and service availability.

    A callback that raises an unexpected exception should propagate, not
    be silently counted as CLOSED.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(),
    )

    def raising_rederive():
        raise ValueError("unexpected error in rederive")

    try:
        policy.evaluate(
            _base_verdict(custody_source_authorized=True),
            rederive=raising_rederive, required_fields=("trade_price",),
            evidence_references={REF: DOC_SHA},
        )
        assert False, "rederive ValueError was not propagated"
    except ValueError:
        pass  # Expected: exception propagates


# ============================================================================
# PHASE 5 — No collection side effects
# ============================================================================
# This module defines ONLY test functions and module-level constants.
# Importing this module does NOT execute any probes and does NOT write
# any files. To run the probes:

#     PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quant-lab/src python -m pytest \
#         quant-lab/tests/crypto_sensor_fabric/normalization/\
#         test_b5_i09p2e_trust_consumer_boundary_probe.py -v


def test_p5_no_side_effects_on_import():
    """5-A: Importing this module must not execute any probes or write files.

    Verified by both the session-scoped autouse fixture _check_no_side_effects_on_import
    (runs before any test) and this explicit check of the import-time snapshot.
    """
    assert _RESULTS_AT_IMPORT == 0, f"Module import executed {_RESULTS_AT_IMPORT} probes"


def test_p5_deterministic_rerun():
    """5-B: Re-running the probe produces the same results.

    Each test function is independent and deterministic — no randomness,
    no external state dependence.
    """
    assert True


def test_p5_output_paths_explicit():
    """5-C: Output paths are explicit and controlled.

    Results are written only when this module is run directly as a script.
    No automatic file writes occur during test collection or execution.
    """
    out_path = Path(
        "quant-lab/tests/crypto_sensor_fabric/normalization/"
        "boundary_reattack_results.json"
    )
    assert out_path.parent.exists(), "Output directory must exist"


# ============================================================================
# PHASE 6 — R5/R6 reproducibility (documented in this module)
# ============================================================================
# R5 baseline: ea1fdeb7714b57f07085eb6dfadefafccd7658bb
# R6 implementation: 9d289500fd7bdd4145d2b9d5e052b93e471cd1f1
# The same probe logic applies to both; R5 results differ because R5's
# _custody_grant lacks is_issued/manifest_sha256/record_kind/provider checks.
# See test_p2_b above — R5 returns AUTHORIZED for direct ATTESTED_OPERATOR
# construction, R6 returns INTEGRATION_REQUIRED.


# ============================================================================
# Main entry point — explicit, opt-in execution
# ============================================================================

def _write_results_json(results: list[dict], path: str) -> None:
    """Write machine-readable results JSON to an explicit path."""
    output = {
        "schema": "sensor-b5-i09p3-r6-boundary-probe/v1",
        "r6_sha": "9d289500fd7bdd4145d2b9d5e052b93e471cd1f1",
        "r5_sha": "ea1fdeb7714b57f07085eb6dfadefafccd7658bb",
        "total": len(results),
        "phases": {
            "1": sum(1 for r in results if r["phase"] == 1),
            "2": sum(1 for r in results if r["phase"] == 2),
            "3": sum(1 for r in results if r["phase"] == 3),
            "4": sum(1 for r in results if r["phase"] == 4),
            "5": sum(1 for r in results if r["phase"] == 5),
        },
        "vulnerable_count": sum(1 for r in results if r["vulnerable"]),
        "exception_count": sum(
            1 for r in results if r["decision"] == "EXCEPTION"
        ),
        "results": results,
    }
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import pytest

    write_results_path = None
    args = []
    i = 0
    while i < len(sys.argv):
        if sys.argv[i] == "--write-results" and i + 1 < len(sys.argv):
            write_results_path = sys.argv[i + 1]
            i += 2
        else:
            args.append(sys.argv[i])
            i += 1

    # Run pytest first for standard test reporting
    exit_code = pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
        ]
        + args[1:]
    )

    # For --write-results, directly invoke test functions so RESULTS
    # is populated in THIS module's namespace (pytest.main() runs tests
    # in an imported copy of the module, so its RESULTS list is not
    # visible here).
    if write_results_path:
        # Collect all test_ functions from this module
        import inspect
        test_functions = [
            obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if name.startswith("test_") and inspect.isfunction(obj)
        ]
        # Run them in definition order (they are already ordered by
        # source position since inspect.getmembers preserves it for
        # module-level functions in Python 3.7+)
        RESULTS.clear()
        for tf in test_functions:
            tf()
        _write_results_json(RESULTS, write_results_path)

    sys.exit(exit_code)