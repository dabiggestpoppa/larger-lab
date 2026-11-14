#!/usr/bin/env python3
"""
SENSOR-B5-I09P3-R5-BASELINE-PROBE — Executable R5 baseline comparison

Runs the same attack scenarios against R5 (ea1fdeb77) to document
the R5/R6 divergence. R5's CustodyAuthorityCapability has NO provider
field, NO _issue() classmethod, and IS frozen (no object.__setattr__
marker copy). R5's _custody_grant returns AUTHORIZED for ATTESTED_OPERATOR
basis — unlike R6 which requires the issuance marker.

Run from /c/tmp/wt-r6-boundary:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=C:/tmp/wt-r5/quant-lab/src python \
        quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_r5_baseline_probe.py
"""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
from datetime import UTC, datetime, timedelta

sys.path.insert(0, "C:/tmp/wt-r5/quant-lab/src")

spec = importlib.util.spec_from_file_location(
    "r5_tcp",
    "C:/tmp/wt-r5/quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py",
)
r5tcp = importlib.util.module_from_spec(spec)
sys.modules["r5_tcp"] = r5tcp
spec.loader.exec_module(r5tcp)

ConsumerPolicy = r5tcp.ConsumerPolicy
CustodyAuthorityCapability = r5tcp.CustodyAuthorityCapability
AuthorityBasis = r5tcp.AuthorityBasis
ConsumerDecision = r5tcp.ConsumerDecision
ConsumerRefusalReason = r5tcp.ConsumerRefusalReason
RecordVerification = r5tcp.RecordVerification
TRUSTED_MANIFEST_SHA256 = "dummy-manifest-sha256"  # R5 does not check manifest_sha256
_replay_evaluation = r5tcp._replay_evaluation
_store_with_evidence = r5tcp._store_with_evidence
CUTOFF = r5tcp.CUTOFF
REF = r5tcp.REF
DOC_SHA = r5tcp.DOC_SHA

ARTIFACT_ID = r5tcp.ARTIFACT_ID
APPROVAL_ID = r5tcp.APPROVAL_ID
REGISTRY_DIGEST = r5tcp.REGISTRY_DIGEST


def _base_verdict(**overrides):
    return r5tcp._base_verdict(**overrides)


def _synthetic_capability(**overrides):
    return r5tcp._synthetic_capability(**overrides)


RESULTS = []


def record(name, vuln, decision, refusal, status, detail=""):
    RESULTS.append(
        {
            "name": name,
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
# R5: Direct ATTESTED_OPERATOR construction — R5 GRANTS AUTHORIZED
# ============================================================================

def test_r5_direct_attested_operator():
    """R5: Direct CustodyAuthorityCapability with ATTESTED_OPERATOR basis.

    R5 constructs this directly (no _issue() required). _custody_grant returns
    (True, "AUTHORIZED") for ATTESTED_OPERATOR basis. R5 VULNERABLE.
    """
    cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id=ARTIFACT_ID,
        approval_id=APPROVAL_ID,
        registry_digest=REGISTRY_DIGEST,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorized is True
    assert out.custody_source_authorization_status == "AUTHORIZED"
    record(
        "R5 direct ATTESTED_OPERATOR construction → AUTHORIZED", True,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="R5 grants AUTHORIZED for direct ATTESTED_OPERATOR construction",
    )


# ============================================================================
# R5: SYNTHETIC_TEST_ONLY — ACCEPT_FIELD_BINDING but NOT AUTHORIZED
# ============================================================================

def test_r5_synthetic_test_only():
    """R5: SYNTHETIC_TEST_ONLY capability → ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY.

    custody_source_authorized=False (because status != "AUTHORIZED"),
    custody_source_authorization_status="SYNTHETIC_TEST_ONLY".
    Not an unauthorized trusted outcome.
    """
    cap = _synthetic_capability(
        knowledge_cutoff=CUTOFF,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorized is False
    assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
    record(
        "R5 SYNTHETIC_TEST_ONLY → ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
        detail="Not AUTHORIZED — not an unauthorized trusted outcome",
    )


# ============================================================================
# R5: No provider field — provider mismatch not checkable
# ============================================================================

def test_r5_no_provider_field():
    """R5: CustodyAuthorityCapability has NO provider field.

    Provider substitution attack is not expressible in R5's data model.
    """
    cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.SYNTHETIC_TEST_ONLY,
        artifact_id=ARTIFACT_ID,
        approval_id=APPROVAL_ID,
        registry_digest=REGISTRY_DIGEST,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
    )
    # Verify no provider field exists
    assert not hasattr(cap, "provider"), "R5 capability must not have provider field"
    record(
        "R5 no provider field in capability", False,
        decision="N/A", refusal=None, status="N/A",
        detail="R5 data model lacks provider field — provider-mismatch attack not expressible",
    )


# ============================================================================
# R5: Frozen dataclass — no object.__setattr__ marker copy
# ============================================================================

def test_r5_frozen_no_marker_copy():
    """R5: CustodyAuthorityCapability is frozen — object.__setattr__ raises.

    Marker-copy attack (threat class C in R6) is not possible in R5 because
    the dataclass is frozen.
    """
    cap = _synthetic_capability(knowledge_cutoff=CUTOFF)
    try:
        object.__setattr__(cap, "_issued", object())
        record(
            "R5 frozen dataclass marker copy", True,
            decision="EXCEPTION", refusal=None, status="SETATTR_SUCCEEDED",
            detail="ERROR: object.__setattr__ succeeded on frozen dataclass",
        )
    except (dataclasses.FrozenInstanceError, AttributeError) as exc:
        record(
            "R5 frozen dataclass marker copy blocked", False,
            decision="BLOCKED", refusal=type(exc).__name__,
            status=str(exc)[:80],
            detail="object.__setattr__ raises on frozen dataclass — marker copy not possible",
        )


# ============================================================================
# R5: No _issue() classmethod
# ============================================================================

def test_r5_no_issue_classmethod():
    """R5: CustodyAuthorityCapability has no _issue() classmethod.

    Direct _issue() attack is not expressible in R5.
    """
    assert not hasattr(CustodyAuthorityCapability, "_issue"), \
        "R5 capability must not have _issue() classmethod"
    record(
        "R5 no _issue() classmethod", False,
        decision="N/A", refusal=None, status="N/A",
        detail="R5 lacks _issue() — direct _issue() attack not expressible",
    )


# ============================================================================
# R5: Rederivation with SYNTHETIC_TEST_ONLY — ACCEPT_FIELD_BINDING but not AUTHORIZED
# ============================================================================

def test_r5_rederive_synthetic():
    """R5: Rederivation with SYNTHETIC_TEST_ONLY capability.

    Returns ACCEPT_FIELD_BINDING with SYNTHETIC_TEST_ONLY status —
    not an unauthorized trusted outcome.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(knowledge_cutoff=CUTOFF),
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
    record(
        "R5 rederive with SYNTHETIC_TEST_ONLY → ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
        detail="Not AUTHORIZED — not an unauthorized trusted outcome",
    )


# ============================================================================
# R5: Wrong knowledge_cutoff → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_wrong_knowledge_cutoff():
    """R5: Wrong knowledge_cutoff → INTEGRATION_REQUIRED."""
    cap = _synthetic_capability(knowledge_cutoff=CUTOFF + timedelta(days=1))
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 wrong knowledge_cutoff → INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# R5: Wrong record_kind → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_wrong_record_kind():
    """R5: record_kind mismatch → INTEGRATION_REQUIRED."""
    cap = _synthetic_capability(
        record_kind="LIQUIDATION", knowledge_cutoff=CUTOFF,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True, record_kind="TRADE")
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 wrong record_kind → INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# R5: No capability → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_no_capability():
    """R5: No custody_authority → INTEGRATION_REQUIRED."""
    policy = ConsumerPolicy(store=_store_with_evidence())
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 no custody_authority → INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import pytest
    sys.exit(
        pytest.main([__file__, "-v", "--tb=short"])
    )