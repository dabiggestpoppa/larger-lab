#!/usr/bin/env python3
"""
SENSOR-B5-I09P3-R6-BOUNDARY-REATTACK — Independent Adversarial Security Probe

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
_forged_verdict = r5tcp_forged = r6tcp._forged_verdict
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

RESULTS: list[dict] = []


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
    tag = "VULNERABLE" if vuln else "CLOSED"
    print(f"  [{tag}] {name} (Phase {phase})")
    print(f"       decision={decision} refusal={refusal} auth_status={status}")
    if detail:
        print(f"       {detail}")


def is_unauthorized_trusted(outcome):
    return (
        outcome.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        and (
            outcome.custody_source_authorized is True
            or outcome.custody_source_authorization_status == "AUTHORIZED"
        )
    )


print("=" * 72)
print("SENSOR-B5-I09P3-R6-BOUNDARY-REATTACK — Independent Adversarial Probe")
print("R6 implementation: 9d289500f | R5 baseline: ea1fdeb77")
print("=" * 72)

# ============================================================================
# PHASE 1 — Original Six Attacks Re-executed Against R6 ConsumerPolicy
# ============================================================================
print("\n" + "=" * 72)
print("PHASE 1 — Original Six R5 Attacks Against R6 ConsumerPolicy")
print("=" * 72)

# CAP01: forged capability with correct identity
print("\n--- CAP01: forged capability with correct identity ---")
policy = ConsumerPolicy(
    store=_store_with_evidence(),
    custody_authority=_forged_operator_capability(),
)
v = _base_verdict()
out = policy.evaluate(
    v, rederive=lambda: v, required_fields=("trade_price",),
    evidence_references={REF: DOC_SHA},
)
record(
    "CAP01 forged capability (correct identity)", 1,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
)

# CAP02: replaced basis escalation
print("\n--- CAP02: replaced basis escalation ---")
synthetic = _synthetic_capability(provider="VENUE_A")
promoted = dataclasses.replace(synthetic, basis=AuthorityBasis.ATTESTED_OPERATOR)
marker_present = promoted.is_issued
policy = ConsumerPolicy(
    store=_store_with_evidence(), custody_authority=promoted,
)
v = _base_verdict()
out = policy.evaluate(
    v, rederive=lambda: v, required_fields=("trade_price",),
    evidence_references={REF: DOC_SHA},
)
record(
    "CAP02 replaced basis escalation", 1,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
    detail=f"is_issued after replace={marker_present}",
)

# CAP03: incorrect manifest digest
print("\n--- CAP03: incorrect manifest digest ---")
policy = ConsumerPolicy(
    store=_store_with_evidence(),
    custody_authority=_forged_operator_capability(manifest_sha256="0" * 64),
)
v = _base_verdict()
out = policy.evaluate(
    v, rederive=lambda: v, required_fields=("trade_price",),
    evidence_references={REF: DOC_SHA},
)
record(
    "CAP03 incorrect manifest digest", 1,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
    detail=f"expected manifest {TRUSTED_MANIFEST_SHA256[:16]}..., got 0*64",
)

# CAP08b: provider substitution
print("\n--- CAP08b: provider substitution ---")
policy = ConsumerPolicy(
    store=_store_with_evidence(),
    custody_authority=_synthetic_capability(provider="VENUE_A"),
)
v = _base_verdict(custody_source_authorized=True, provider="VENUE_B")
out = policy.evaluate(
    v, rederive=lambda: v, required_fields=("trade_price",),
    evidence_references={REF: DOC_SHA},
)
record(
    "CAP08b provider substitution", 1,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
    detail="R6 checks provider binding",
)

# CAP12: record_kind omission
print("\n--- CAP12: record kind omission ---")
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
        evidence_references={REF: DOC_SHA},
    )
    record(
        f"CAP12 record kind ({label})", 1,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )

# RG08: forged replay eligibility
print("\n--- RG08: forged replay eligibility ---")
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
record(
    "RG08 forged replay eligibility", 1,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.replay_status,
    detail="expected REFUSE/REPLAY_BLOCKED/NOT_POLICY_DERIVED",
)

# ============================================================================
# PHASE 2 — Caller-Controlled Rederivation
# ============================================================================
print("\n" + "=" * 72)
print("PHASE 2 — Caller-Controlled Rederivation Challenge")
print("=" * 72)

# A. Validated rederived verdict (control)
print("\n--- A. Validated rederived verdict (control) ---")
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

# B. model_construct-forged rederived verdict (candidate=None)
print("\n--- B. model_construct-forged rederived verdict (candidate=None) ---")
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
record(
    "B model_construct-forged rederive (candidate=None)", 2,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
    detail="candidate=None, rederive returns forged model_construct verdict",
)

# C. model_copy-forged rederived verdict (candidate=None)
print("\n--- C. model_copy-forged rederived verdict (candidate=None) ---")
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
record(
    "C model_copy-forged rederive (candidate=None)", 2,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
)

# D. candidate=None; callback returns forged object (_forged_verdict)
print("\n--- D. candidate=None; callback returns forged object ---")
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

# E. Cached candidate + callback return matching forged objects
print("\n--- E. Cached candidate + callback return matching forged objects ---")
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
record(
    "E cached+derived matching forged objects", 2,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
)

# F. Callback returns valid-looking but untrusted object
print("\n--- F. Callback returns valid-looking but untrusted object ---")
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
record(
    "F valid-looking but untrusted callback object", 2,
    vuln=is_unauthorized_trusted(out),
    decision=out.decision.value,
    refusal=out.refusal_reason.value if out.refusal_reason else None,
    status=out.custody_source_authorization_status,
)

# G. Callback raises unexpected exceptions
print("\n--- G. Callback raises unexpected exceptions ---")
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
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="rederive raises ValueError",
    )
except Exception as exc:
    record(
        "G callback raises unexpected exception", 2,
        vuln=False,
        decision="EXCEPTION", refusal=type(exc).__name__,
        status=str(exc)[:80],
        detail="exception propagates out of evaluate()",
    )

# H. Different record identity or knowledge cutoff
print("\n--- H. Different record identity or knowledge cutoff ---")
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
print("\n" + "=" * 72)
print("PHASE 3 — Issuance-Marker Challenge")
print("=" * 72)

# A. Direct _issue() call with ATTESTED_OPERATOR basis
print("\n--- A. Direct _issue() call with ATTESTED_OPERATOR basis ---")
try:
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
        evidence_references={REF: DOC_SHA},
    )
    record(
        "A Direct _issue() capability in ConsumerPolicy", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"is_issued={direct_cap.is_issued}",
    )
except Exception as exc:
    record(
        "A Direct _issue() call", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# B. Wrong manifest_sha256
print("\n--- B. Direct _issue() with wrong manifest_sha256 ---")
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
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=wrong_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "B _issue() with wrong manifest_sha256", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )
except Exception as exc:
    record(
        "B _issue() with wrong manifest_sha256", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# C. record_kind=None
print("\n--- C. Direct _issue() with record_kind=None ---")
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
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=no_kind_cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        evidence_references={REF: DOC_SHA},
    )
    record(
        "C _issue() with record_kind=None", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
    )
except Exception as exc:
    record(
        "C _issue() with record_kind=None", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# D. provider=None
print("\n--- D. Direct _issue() with provider=None ---")
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
except Exception as exc:
    record(
        "D _issue() with provider=None", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# E. dataclasses.replace to ATTESTED_OPERATOR
print("\n--- E. dataclasses.replace to ATTESTED_OPERATOR ---")
try:
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
    record(
        "E replaced capability in ConsumerPolicy", 3,
        vuln=is_unauthorized_trusted(out),
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail=f"is_issued={replaced.is_issued}",
    )
except Exception as exc:
    record(
        "E dataclasses.replace", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# F. Marker copy attack
print("\n--- F. Marker copy attack (object.__setattr__) ---")
try:
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
    object.__setattr__(plain_cap, "_issued", real_marker := getattr(
        _synthetic_capability(), "_issued"))
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
except Exception as exc:
    record(
        "F Marker-copy attack", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# G. Marker-copy with wrong manifest_sha256
print("\n--- G. Marker-copy with wrong manifest_sha256 ---")
try:
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
except Exception as exc:
    record(
        "G Marker-copy with wrong manifest_sha256", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# H. Marker-copy with wrong knowledge_cutoff
print("\n--- H. Marker-copy with wrong knowledge_cutoff ---")
try:
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
except Exception as exc:
    record(
        "H Marker-copy with wrong knowledge_cutoff", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

# I. Marker-copy with wrong provider
print("\n--- I. Marker-copy with wrong provider ---")
try:
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
except Exception as exc:
    record(
        "I Marker-copy with wrong provider", 3,
        vuln=False, decision="EXCEPTION",
        refusal=type(exc).__name__, status=str(exc)[:80],
    )

print("\n" + "=" * 72)
print("SUMMARY — R6 Boundary Reattack Challenge")
total = len(RESULTS)
closed = sum(1 for r in RESULTS if not r["vulnerable"])
vuln = sum(1 for r in RESULTS if r["vulnerable"])
print(f"CLOSED: {closed}   VULNERABLE: {vuln}   TOTAL: {total}")
for r in RESULTS:
    print(f"  [{r['phase']}] {r['name']:50s} -> "
          f"{r['decision']:25s} {r['refusal'] or '-':22s} {r['status']}")
print("=" * 72)

# Write machine-readable results
out_path = Path(
    "quant-lab/tests/crypto_sensor_fabric/normalization/"
    "boundary_reattack_results.json"
)
out_path.write_text(
    json.dumps(
        {
            "r6_sha": "9d289500fd7bdd4145d2b9d5e052b93e471cd1f1",
            "r5_sha": "ea1fdeb7714b57f07085eb6dfadefafccd7658bb",
            "probe_results": RESULTS,
            "summary": {
                "closed": closed,
                "vulnerable": vuln,
                "total": total,
            },
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(f"\nMachine-readable results written to {out_path}")