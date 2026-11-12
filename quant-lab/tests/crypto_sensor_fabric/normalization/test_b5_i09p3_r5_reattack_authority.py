"""SENSOR-B5-I09P3-R5-INDEPENDENT-REATTACK — authority reattack (TEST-ONLY).

Independent security reattack of the R5 custody-authority repair
(``ea1fdeb7714b57f07085eb6dfadefafccd7658bb``).  Two parts:

**Part A — R3 replay.**  The 13 R3 gates, re-expressed against the R5 API while
preserving each original attack hypothesis.  R5 replaced the record-carried
boolean with a policy-supplied ``CustodyAuthorityCapability``, so the gates that
used to set a verdict flag now attack the capability instead.  No gate is
re-pointed from "must refuse" to "must accept".

**Part B — capability forgery.**  Attacks the new capability directly: the
question is whether the constructor is a trust boundary or merely an API
convention.

QUARANTINED PROTOTYPE.  No production ingestion, no custody service, no provider
approval.  ``INTEGRATION_STATE`` remains ``INTEGRATION_REQUIRED``.

Adaptation record (disclosed, because a silent adaptation would be a fake pass):

* R3 parameterised every gate over **two** prototype copies.  R5 contains one
  copy, so the parameterisation collapses 24 collected cases to 13 gate
  identities.  The invariants are unchanged; only the copy count shrank.
* RG06 previously required ``REFUSE``/``INTEGRATION_REQUIRED`` for a synthetic
  fixture.  R5 deliberately keeps a ``SYNTHETIC_TEST_ONLY`` capability for
  downstream field-scope tests.  The preserved hypothesis is "synthetic input
  must never become operator authority", so RG06 now requires status
  ``SYNTHETIC_TEST_ONLY`` with ``custody_source_authorized is False`` and
  explicitly forbids ``AUTHORIZED``.  It does not require refusal.
* RG05 previously asserted the absence of cutoff binding.  R5 adds it, so RG05
  now asserts the binding exists **and** that a capability minted at one cutoff
  is refused at another.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from crypto_sensor_fabric.normalization.authority import SemanticAuthority
from crypto_sensor_fabric.normalization.sensors.verification import (
    INTEGRATION_STATE,
    RecordVerification,
    TrustedAuthorityContext,
    verify_liquidation_record,
    verify_trade_record,
)
from crypto_sensor_fabric.normalization.time.enums import ReplayEligibility

_HERE = Path(__file__).resolve().parent
# _HERE is .../quant-lab/tests/crypto_sensor_fabric/normalization, so the
# quant-lab root is two levels up from it (not three).
_QUANT_LAB = _HERE.parents[2]

POLICY_PATH = _HERE / "test_b5_i09p2e_trust_consumer.py"

R5_SHA = "ea1fdeb7714b57f07085eb6dfadefafccd7658bb"

_SAFE_DECISIONS = frozenset({"REFUSE", "INTEGRATION_REQUIRED"})

_module: Any = None


def policy_module() -> Any:
    global _module
    if _module is None:
        if not POLICY_PATH.is_file():
            pytest.fail(f"R5 policy module missing at {POLICY_PATH}")
        spec = importlib.util.spec_from_file_location("_r5_reattack_policy", POLICY_PATH)
        if spec is None or spec.loader is None:  # pragma: no cover
            pytest.fail(f"cannot build import spec for {POLICY_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _module = module
    return _module


def _decision(out: Any) -> str:
    return str(getattr(out.decision, "value", out.decision))


def assert_not_operator_authority(out: Any, control: str) -> None:
    """No operator authority may be granted to a claim the policy does not own."""
    decision = _decision(out)
    assert decision in _SAFE_DECISIONS, (
        f"{control}: decision={decision} for an authority claim the policy does "
        f"not own (authorized={out.custody_source_authorized!r}, "
        f"status={out.custody_source_authorization_status!r})"
    )
    assert out.custody_source_authorization_status != "AUTHORIZED", (
        f"{control}: custody authority was promoted to AUTHORIZED"
    )


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def h() -> Any:
    return policy_module()


def _ev(h: Any) -> dict[str, str]:
    return {h.REF: h.DOC_SHA}


def _verdict(h: Any, **overrides: Any) -> Any:
    return h._base_verdict(**overrides)


def _policy(h: Any, capability: Any = None) -> Any:
    return h.ConsumerPolicy(store=h._store_with_evidence(), custody_authority=capability)


def _operator_capability(h: Any, **overrides: Any) -> Any:
    """The forged capability: public dataclass, ATTESTED_OPERATOR, no seal."""
    kwargs: dict[str, Any] = {
        "basis": h.AuthorityBasis.ATTESTED_OPERATOR,
        "artifact_id": h.ARTIFACT_ID,
        "approval_id": h.APPROVAL_ID,
        "registry_digest": h.REGISTRY_DIGEST,
        "record_kind": "TRADE",
        "knowledge_cutoff": None,
        "manifest_sha256": None,
    }
    kwargs.update(overrides)
    return h.CustodyAuthorityCapability(**kwargs)


T1 = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
T2 = T1 + timedelta(days=1)


# --------------------------------------------------------------------------- #
# Part A — R3 gate replay against the R5 API
# --------------------------------------------------------------------------- #


class TestR3Replay:
    def test_rg01_caller_controlled_rederive_cannot_authorize(self, h: Any) -> None:
        """RG01 — a verdict flag from a caller-supplied rederive grants nothing."""
        forged = h._forged_verdict(custody_source_authorized=True, custody_verified=True)
        out = _policy(h).evaluate(
            None,
            rederive=lambda: forged,
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG01")

    def test_rg02_forged_authority_context_cannot_authorize(self, h: Any) -> None:
        """RG02 — a directly constructed TrustedAuthorityContext grants nothing."""
        forged_context = TrustedAuthorityContext.model_construct(
            manifest_sha256="0" * 64,
            artifact_id="forged-artifact",
            manifest_bytes=b"forged manifest bytes",
        )
        policy = h.ConsumerPolicy(context=forged_context, store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: _verdict(h, custody_source_authorized=True),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG02")

    def test_rg03_agreeing_forged_copies_cannot_authorize(self, h: Any) -> None:
        """RG03 — two agreeing forged copies are still one unverified claim."""
        cached = h._forged_verdict(custody_source_authorized=True)
        derived = h._forged_verdict(custody_source_authorized=True)
        out = _policy(h).evaluate_cached(
            cached,
            rederive=lambda: derived,
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG03")

    def test_rg04_flag_reused_between_records(self, h: Any) -> None:
        """RG04 — a flag set for one record authorizes no other record."""
        out = _policy(h).evaluate(
            None,
            rederive=lambda: _verdict(h, custody_source_authorized=True, provider="VENUE_B"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG04")

    def test_rg05_cutoff_binding_exists_and_is_enforced(self, h: Any) -> None:
        """RG05 — authority is bound to the cutoff at which it was established."""
        assert "knowledge_cutoff" in inspect.signature(h.ConsumerPolicy.evaluate).parameters, (
            "RG05: the consumer must be told which cutoff it evaluates at"
        )
        capability = _operator_capability(h, knowledge_cutoff=T1)
        at_t1 = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
            knowledge_cutoff=T1,
        )
        at_t2 = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
            knowledge_cutoff=T2,
        )
        assert _decision(at_t1) == "ACCEPT_FIELD_BINDING", "RG05: same-cutoff must be honoured"
        assert _decision(at_t2) == "INTEGRATION_REQUIRED", (
            f"RG05: a capability minted at {T1.isoformat()} must not authorize at "
            f"{T2.isoformat()}; got {_decision(at_t2)}"
        )

    def test_rg06_synthetic_never_becomes_operator_authority(self, h: Any) -> None:
        """RG06 (adapted) — synthetic capability stays SYNTHETIC_TEST_ONLY."""
        synthetic = h.CustodyAuthorityCapability.synthetic_for_field_scope_tests(
            artifact_id=h.ARTIFACT_ID,
            approval_id=h.APPROVAL_ID,
            registry_digest=h.REGISTRY_DIGEST,
            record_kind="TRADE",
        )
        out = _policy(h, synthetic).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert out.custody_source_authorization_status != "AUTHORIZED", (
            "RG06: a synthetic capability must never be labelled AUTHORIZED"
        )
        assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY", (
            f"RG06: expected SYNTHETIC_TEST_ONLY, got "
            f"{out.custody_source_authorization_status!r}"
        )
        assert out.custody_source_authorized is False, (
            "RG06: synthetic authority must not set custody_source_authorized"
        )

    def test_rg07_digest_without_authority_stays_integration_required(self, h: Any) -> None:
        """RG07 — matching bytes prove custody, never authority."""
        out = _policy(h).evaluate(
            None,
            rederive=lambda: _verdict(h, custody_source_authorized=False),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert _decision(out) == "INTEGRATION_REQUIRED"
        assert out.custody_source_authorized is False

    def test_rg08_forged_replay_eligibility_cannot_authorize(self, h: Any) -> None:
        """RG08 — a caller-supplied replay object is not replay proof."""

        class _ForgedReplay:
            eligibility = ReplayEligibility.ELIGIBLE
            already_consumed = True
            fingerprint_reused = True
            reasons = ("caller asserts eligible after the fingerprint was consumed",)

        out = _policy(h).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            replay_evaluation=_ForgedReplay(),
            evidence_references=_ev(h),
        )
        assert _decision(out) == "REFUSE", (
            f"RG08: a forged ELIGIBLE claim must be refused; got {_decision(out)}"
        )

    def test_rg09_cross_record_approval_or_artifact_substitution(self, h: Any) -> None:
        """RG09 — swapped identity mints nothing without a matching capability."""
        out = _policy(h).evaluate(
            None,
            rederive=lambda: _verdict(
                h,
                artifact_id="ARTIFACT-B",
                approval_id="APPROVAL-B",
                registry_digest="b" * 64,
            ),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG09")

    def test_rg10_deserialized_decision_cannot_be_replayed_as_authority(
        self, h: Any
    ) -> None:
        """RG10 — deserialization is not verification."""
        original = _verdict(h, custody_source_authorized=True)
        rehydrated = RecordVerification.model_validate(original.model_dump(mode="json"))
        out = _policy(h).evaluate(
            rehydrated,
            rederive=lambda: rehydrated,
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG10")

    def test_rg11_absent_operator_attestation_cannot_authorize(self, h: Any) -> None:
        """RG11 — with no capability present, the outcome is INTEGRATION_REQUIRED."""
        out = _policy(h, None).evaluate(
            None,
            rederive=lambda: _verdict(h, custody_source_authorized=True),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "RG11")

    def test_rg12_empty_production_manifest_mints_no_authority(self) -> None:
        """RG12 — production cannot mint what the prototype can be handed."""
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"
        for verifier, name in (
            (verify_trade_record, "verify_trade_record"),
            (verify_liquidation_record, "verify_liquidation_record"),
        ):
            assert "custody_source_authorized=False" in inspect.getsource(verifier), (
                f"RG12: {name} must not mint custody authority"
            )
        default = RecordVerification.model_fields["custody_source_authorized"].default
        assert default is False

    def test_rg13_gate_is_outside_the_frozen_i10_named_prefix_allowance(self) -> None:
        """RG13 — record the scope fact rather than assume admission."""
        name = Path(__file__).name
        assert name.startswith("test_b5_i09p3_r5_reattack_"), (
            "RG13: keep the honest reattack name; renaming to fit a frozen prefix "
            "would disguise an unauthorized test"
        )
        assert not name.startswith("test_b5_i10")


# --------------------------------------------------------------------------- #
# Part B — capability forgery
# --------------------------------------------------------------------------- #


class TestCapabilityForgery:
    def test_cap01_direct_construction_with_attested_operator(self, h: Any) -> None:
        """CAP01 — a public dataclass constructed directly with ATTESTED_OPERATOR.

        Attacker control: ordinary Python in the same process constructs the
        capability.  Required: no operator authority, because the object has no
        issuance proof.
        """
        capability = _operator_capability(h)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP01 direct dataclass construction")

    def test_cap02_manifest_digest_is_never_validated(self, h: Any) -> None:
        """CAP02 — a capability whose manifest digest is pure garbage.

        Required: refused, because the digest is the only field tying the
        capability to the reviewed root.
        """
        capability = _operator_capability(h, manifest_sha256="0" * 64)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP02 invalid manifest digest")

    def test_cap03_basis_is_plain_replaceable_data(self, h: Any) -> None:
        """CAP03 — a synthetic capability promoted to ATTESTED_OPERATOR by replace.

        Required: refused.  If ``dataclasses.replace`` alone escalates the basis,
        the basis is data, not a decision.
        """
        synthetic = h.CustodyAuthorityCapability.synthetic_for_field_scope_tests(
            artifact_id=h.ARTIFACT_ID,
            approval_id=h.APPROVAL_ID,
            registry_digest=h.REGISTRY_DIGEST,
            record_kind="TRADE",
        )
        promoted = replace(synthetic, basis=h.AuthorityBasis.ATTESTED_OPERATOR)
        out = _policy(h, promoted).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP03 basis promotion by replace")

    def test_cap04_forged_semantic_authority_is_refused(self, h: Any) -> None:
        """CAP04 — a duck-typed stand-in for SemanticAuthority must be refused."""
        reviewed = TrustedAuthorityContext.from_reviewed_root(
            manifest_bytes=_shipped_manifest_bytes(), artifact_id="any-artifact"
        )

        class _FakeSemanticAuthority:
            artifact_id = "any-artifact"
            approval_id = "FAKE"
            registry_digest = "a" * 64

        with pytest.raises(Exception):
            h.CustodyAuthorityCapability.from_reviewed_context(
                context=reviewed, semantic_authority=_FakeSemanticAuthority()
            )

    def test_cap05_model_construct_flag_is_ignored(self, h: Any) -> None:
        """CAP05 — a model_construct verdict claiming authority grants nothing."""
        forged = h._forged_verdict(custody_source_authorized=True)
        out = _policy(h, None).evaluate(
            None,
            rederive=lambda: forged,
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP05 model_construct flag")

    def test_cap06_forged_reviewed_context_cannot_mint(self, h: Any) -> None:
        """CAP06 — from_reviewed_context re-validates the root."""
        forged_context = TrustedAuthorityContext.model_construct(
            manifest_sha256="0" * 64,
            artifact_id="forged",
            manifest_bytes=b"forged manifest bytes",
        )
        with pytest.raises(Exception):
            h.CustodyAuthorityCapability.from_reviewed_context(
                context=forged_context, semantic_authority=object()
            )

    def test_cap07_correct_manifest_with_unauthorized_source(self, h: Any) -> None:
        """CAP07 — a genuine reviewed root does not authorize an unapproved source."""
        reviewed = TrustedAuthorityContext.from_reviewed_root(
            manifest_bytes=_shipped_manifest_bytes(), artifact_id="any-artifact"
        )
        with pytest.raises(Exception):
            h.CustodyAuthorityCapability.from_reviewed_context(
                context=reviewed, semantic_authority=object()
            )

    def test_cap08_cross_record_reuse(self, h: Any) -> None:
        """CAP08 — a capability for artifact A must not authorize artifact B."""
        capability = _operator_capability(h)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h, artifact_id="ARTIFACT-B"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP08 cross-record reuse")

    def test_cap08b_provider_substitution(self, h: Any) -> None:
        """CAP08b — same approval/artifact, different provider.

        Required: refused.  Provider is part of record identity (R3 RG04), and a
        venue's custody authorization never transfers.
        """
        capability = _operator_capability(h)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h, provider="VENUE_B"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP08b provider substitution")

    def test_cap09_cross_approval_reuse(self, h: Any) -> None:
        """CAP09 — a capability for approval X must not authorize approval Y."""
        out = _policy(h, _operator_capability(h)).evaluate(
            None,
            rederive=lambda: _verdict(h, approval_id="APPROVAL-B"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP09 cross-approval reuse")

    def test_cap10_cross_registry_reuse(self, h: Any) -> None:
        """CAP10 — a capability for registry digest X must not authorize Y."""
        out = _policy(h, _operator_capability(h)).evaluate(
            None,
            rederive=lambda: _verdict(h, registry_digest="b" * 64),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP10 cross-registry reuse")

    def test_cap11_cross_cutoff_reuse(self, h: Any) -> None:
        """CAP11 — a capability minted at T1 must not authorize at T2."""
        capability = _operator_capability(h, knowledge_cutoff=T1)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
            knowledge_cutoff=T2,
        )
        assert_not_operator_authority(out, "CAP11 cross-cutoff reuse")

    def test_cap12_record_kind_substitution(self, h: Any) -> None:
        """CAP12 — an unbound record_kind must not authorize another record kind."""
        capability = _operator_capability(h, record_kind=None)
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: h._forged_verdict(record_kind="LIQUIDATION"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP12 record-kind substitution")

    def test_cap12b_explicit_kind_mismatch_is_refused(self, h: Any) -> None:
        """CAP12b — an explicit TRADE capability must not authorize LIQUIDATION."""
        capability = _operator_capability(h, record_kind="TRADE")
        out = _policy(h, capability).evaluate(
            None,
            rederive=lambda: h._forged_verdict(record_kind="LIQUIDATION"),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert_not_operator_authority(out, "CAP12b explicit kind mismatch")

    def test_cap13_synthetic_capability_is_never_authorized(self, h: Any) -> None:
        """CAP13 — a synthetic capability is never reported as operator authority."""
        synthetic = h.CustodyAuthorityCapability.synthetic_for_field_scope_tests(
            artifact_id=h.ARTIFACT_ID,
            approval_id=h.APPROVAL_ID,
            registry_digest=h.REGISTRY_DIGEST,
            record_kind="TRADE",
        )
        out = _policy(h, synthetic).evaluate(
            None,
            rederive=lambda: _verdict(h),
            required_fields=("trade_price",),
            evidence_references=_ev(h),
        )
        assert out.custody_source_authorization_status != "AUTHORIZED"
        assert out.custody_source_authorized is False

    def test_cap14_shipped_manifest_is_empty(self, h: Any) -> None:
        """CAP14 — the shipped manifest approves no artifact."""
        manifest = json.loads(_shipped_manifest_bytes().decode("utf-8"))
        assert manifest.get("artifacts") == {}, (
            "CAP14: the shipped approval manifest must approve no artifact"
        )
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED"


def _shipped_manifest_bytes() -> bytes:
    h = policy_module()
    return (_QUANT_LAB / h.TRUSTED_MANIFEST_RELPATH).read_bytes()


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
