"""SENSOR-B5-I09P3-R3 — authority-origin security gate (EXPERIMENTAL, TEST-ONLY).

Independent negative acceptance suite for the P3 trust-consumer prototype.  It
does not re-test behaviour that already exists; it states the behaviour the
prototype MUST have before any consumer may treat ``custody_source_authorized``
as authority, and it requires refusal (or ``INTEGRATION_REQUIRED``) wherever the
prototype currently grants authority to a claim it does not own.

Authority categories this gate keeps apart:

* ``NO_AUTHORITY``            — this repository's production state (flag False)
* ``SYNTHETIC_TEST_AUTHORITY`` — a fixture flag set inside a test helper
* ``UNVERIFIED_CALLER_CLAIM``  — a boolean supplied by whoever supplies records
* ``ATTESTED_EXTERNAL_AUTHORITY`` — an operator-owned custody attestation, which
  does not exist in this repository

The prototype under test is the test-resident ``ConsumerPolicy``.  It exists in
TWO copies with the same authorization dataflow: the P3 conformance engine
(``test_b5_i09p2e_trust_consumer.py``) and the R1/R2 red-team harness
(``test_b5_i09p3_redteam_adversarial.py``).  Every gate below is parameterised
over both copies, because a repair that fixes one copy and not the other is not
a repair.

QUARANTINED PROTOTYPE — not an authorized production consumer.  No production
ingestion, no custody service, no provider approval.  ``INTEGRATION_STATE``
remains ``INTEGRATION_REQUIRED``.

Test-first discipline: this module is written to FAIL against the unmodified P3
prototype.  Failures are RED evidence, not defects in the test.  No prototype
implementation is edited here.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

import pytest

from crypto_sensor_fabric.normalization.sensors.verification import (
    INTEGRATION_STATE,
    TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
    RecordVerification,
    TrustedAuthorityContext,
    verify_liquidation_record,
    verify_trade_record,
)
from crypto_sensor_fabric.normalization.time.enums import ReplayEligibility

_HERE = Path(__file__).resolve().parent

#: quant-lab/ — ``_HERE`` is tests/crypto_sensor_fabric/normalization.
_QUANT_LAB = _HERE.parents[3]

#: The two prototype copies of the consumer policy, by label.
_HARNESS_PATHS: dict[str, Path] = {
    "p3_conformance_engine": _HERE / "test_b5_i09p2e_trust_consumer.py",
    "redteam_harness_r2": _HERE / "test_b5_i09p3_redteam_adversarial.py",
}

_SAFE_DECISIONS = frozenset({"REFUSE", "INTEGRATION_REQUIRED"})

_LOADED: dict[str, Any] = {}


def _load_harness(label: str) -> Any:
    """Load one prototype copy by path, without package-relative imports.

    Both copies are pytest modules rather than importable packages, so they are
    loaded explicitly.  Loading is cached per label for the module's lifetime.
    """
    if label in _LOADED:
        return _LOADED[label]
    path = _HARNESS_PATHS[label]
    if not path.is_file():
        pytest.fail(
            f"prototype harness {label!r} is missing at {path}; the gate cannot "
            "be evaluated against a consumer policy that does not exist"
        )
    spec = importlib.util.spec_from_file_location(f"_r3_prototype_{label}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import machinery
        pytest.fail(f"cannot build an import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _LOADED[label] = module
    return module


@pytest.fixture(params=tuple(_HARNESS_PATHS), scope="module")
def harness(request: pytest.FixtureRequest) -> Any:
    """Both prototype copies, so one repaired copy cannot hide the other."""
    return _load_harness(request.param)


def _decision(out: Any) -> str:
    return str(getattr(out.decision, "value", out.decision))


def assert_authority_not_granted(out: Any, control: str) -> None:
    """The mandatory outcome: no ACCEPT, and no AUTHORIZED custody status."""
    decision = _decision(out)
    assert decision in _SAFE_DECISIONS, (
        f"{control}: the consumer returned {decision} for an authority claim it "
        f"does not own (custody_source_authorized="
        f"{out.custody_source_authorized!r}, "
        f"status={out.custody_source_authorization_status!r}). "
        "The safe outcomes are REFUSE or INTEGRATION_REQUIRED."
    )
    assert not (
        out.custody_source_authorized
        and out.custody_source_authorization_status == "AUTHORIZED"
    ), (
        f"{control}: custody authorization was promoted to AUTHORIZED without a "
        "policy-owned operator attestation"
    )


def _authorized_verdict(h: Any, **overrides: Any) -> Any:
    """A model-VALID verdict claiming authority (not merely a constructed one)."""
    overrides.setdefault("custody_source_authorized", True)
    return h._base_verdict(**overrides)


class TestR3AuthorityOriginGate:
    """Strict negative gates: each requires refusal, not observation."""

    def test_rg01_caller_controlled_rederive_cannot_authorize(
        self, harness: Any
    ) -> None:
        """Gate 1 — caller-controlled rederive yielding authorized=True.

        Attacker control: supplies the ``rederive`` callable itself.  Required:
        the policy refuses, because a callable the caller supplies is an
        UNVERIFIED CALLER CLAIM, never ATTESTED EXTERNAL AUTHORITY.
        """
        h = harness
        forged = h._forged_verdict(
            custody_source_authorized=True, custody_verified=True
        )
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: forged,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG01 caller-controlled rederive")

    def test_rg02_forged_authority_context_cannot_authorize(
        self, harness: Any
    ) -> None:
        """Gate 2 — forged ``TrustedAuthorityContext``.

        Attacker control: constructs the context object directly (bypassing
        ``from_reviewed_root``) and hands it to the policy.  Required: the
        policy validates the context against the pinned root, or refuses.
        """
        h = harness
        forged_context = TrustedAuthorityContext.model_construct(
            manifest_sha256="0" * 64,
            artifact_id="forged-artifact",
            manifest_bytes=b"forged manifest bytes",
        )
        policy = h.ConsumerPolicy(
            context=forged_context, store=h._store_with_evidence()
        )
        out = policy.evaluate(
            None,
            rederive=lambda: _authorized_verdict(h),
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG02 forged authority context")

    def test_rg03_agreeing_forged_cached_and_rederived_cannot_authorize(
        self, harness: Any
    ) -> None:
        """Gate 3 — forged cached and re-derived verdicts that agree.

        Attacker control: makes both sides of the divergence check claim
        authority, so agreement is mistaken for corroboration.  Required: the
        policy refuses; two copies of one unverified claim are still one claim.
        """
        h = harness
        cached = h._forged_verdict(custody_source_authorized=True)
        derived = h._forged_verdict(custody_source_authorized=True)
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate_cached(
            cached,
            rederive=lambda: derived,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG03 agreeing forged cached verdict")

    def test_rg04_authorization_flag_reused_between_records(
        self, harness: Any
    ) -> None:
        """Gate 4 — authorization flag reused between records.

        Attacker control: keeps the approval identity but presents a different
        record (different provider).  Required: authorization is record-bound, so
        the policy refuses the second record.
        """
        h = harness
        other_record = _authorized_verdict(h, provider="VENUE_B")
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: other_record,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG04 cross-record flag reuse")

    def test_rg05_authorization_is_bound_to_a_knowledge_cutoff(
        self, harness: Any
    ) -> None:
        """Gate 5 — authorization flag reused across different cutoffs.

        Attacker control: reuses an authorized decision after the knowledge
        cutoff moves.  Required: the decision carries (and the consumer checks)
        the cutoff at which it was established; otherwise reuse across cutoffs is
        structurally unguarded.
        """
        h = harness
        assert "knowledge_cutoff" in RecordVerification.model_fields, (
            "RG05 cutoff binding: RecordVerification carries no knowledge_cutoff, "
            "so an authorized verdict cannot be bound to the instant at which it "
            "was established and may be replayed across cutoffs"
        )
        signature = inspect.signature(h.ConsumerPolicy.evaluate)
        assert "knowledge_cutoff" in signature.parameters, (
            "RG05 cutoff binding: the consumer policy cannot be told which cutoff "
            "it is evaluating at, so it cannot verify that an authorization was "
            "established before that cutoff"
        )

    def test_rg06_synthetic_fixture_cannot_masquerade_as_operator_authority(
        self, harness: Any
    ) -> None:
        """Gate 6 — synthetic fixture masquerading as operator authorization.

        Attacker control: a model-VALID fixture (no ``model_construct`` bypass)
        that simply sets the flag True.  Required: synthetic test authority never
        becomes AUTHORIZED custody status.
        """
        h = harness
        synthetic = _authorized_verdict(h)
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: synthetic,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG06 synthetic fixture authority")

    def test_rg07_correct_digest_with_unauthorized_source_stays_integration_required(
        self, harness: Any
    ) -> None:
        """Gate 7 — correct evidence digest paired with an unauthorized source.

        This is the invariant the production verifier already honours: hashing
        the approved bytes proves custody, never custody-source authority.  It is
        asserted here as the positive anchor the gate must not weaken.
        """
        h = harness
        verdict = h._base_verdict(custody_source_authorized=False)
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: verdict,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert _decision(out) == "INTEGRATION_REQUIRED", (
            "RG07 digest-without-authority: matching evidence bytes must yield "
            f"INTEGRATION_REQUIRED, got {_decision(out)}"
        )
        assert out.custody_source_authorized is False

    def test_rg08_forged_replay_eligibility_cannot_authorize(
        self, harness: Any
    ) -> None:
        """Gate 8 — forged replay eligibility.

        Attacker control: supplies the replay evaluation object, claiming
        ELIGIBLE while the fingerprint is already consumed.  Required: the policy
        refuses, because a caller-supplied eligibility claim is not replay proof.
        """

        class _ForgedReplay:
            eligibility = ReplayEligibility.ELIGIBLE
            already_consumed = True
            fingerprint_reused = True
            reasons = ("caller asserts eligible after the fingerprint was consumed",)

        h = harness
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: _authorized_verdict(h),
            required_fields=("trade_price",),
            replay_evaluation=_ForgedReplay(),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert _decision(out) == "REFUSE", (
            "RG08 forged replay eligibility: a caller-supplied ELIGIBLE claim "
            f"must be refused, got {_decision(out)}"
        )

    def test_rg09_cross_record_approval_or_artifact_substitution(
        self, harness: Any
    ) -> None:
        """Gate 9 — cross-record approval or artifact substitution.

        Attacker control: swaps approval_id and artifact_id while keeping the
        verified field.  Required: the policy refuses; authorization belongs to
        an (approval, artifact, record) identity, not to a field name.
        """
        h = harness
        substituted = _authorized_verdict(
            h,
            artifact_id="ARTIFACT-B",
            approval_id="APPROVAL-B",
            registry_digest="b" * 64,
        )
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: substituted,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG09 cross-record substitution")

    def test_rg10_deserialized_decision_cannot_be_replayed_as_authority(
        self, harness: Any
    ) -> None:
        """Gate 10 — deserialized accepted decision replayed without verification.

        Attacker control: serialises a verdict that claims authority and feeds it
        back as both candidate and re-derived result.  Required: deserialization
        is not verification, so the policy refuses.
        """
        h = harness
        original = _authorized_verdict(h)
        rehydrated = RecordVerification.model_validate(original.model_dump(mode="json"))
        assert rehydrated.custody_source_authorized is True
        policy = h.ConsumerPolicy(store=h._store_with_evidence())
        out = policy.evaluate(
            rehydrated,
            rederive=lambda: rehydrated,
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG10 deserialized decision replay")

    def test_rg11_absent_operator_attestation_cannot_authorize(
        self, harness: Any
    ) -> None:
        """Gate 11 — absent operator-authority attestation.

        Attacker control: sets the flag True and supplies no authority context at
        all.  Required: with no operator attestation present, the outcome is
        INTEGRATION_REQUIRED or REFUSE — never ACCEPT with AUTHORIZED.
        """
        h = harness
        policy = h.ConsumerPolicy(context=None, store=h._store_with_evidence())
        out = policy.evaluate(
            None,
            rederive=lambda: _authorized_verdict(h),
            required_fields=("trade_price",),
            evidence_references={h.REF: h.DOC_SHA},
        )
        assert_authority_not_granted(out, "RG11 absent operator attestation")


class TestR3ProductionLimits:
    """The production limits this gate relies on, asserted not assumed."""

    def test_rg12_empty_production_manifest_mints_no_authority(self) -> None:
        """Gate 12 — empty production approval manifest.

        The production manifest admits no artifacts, and both production
        verifiers hardcode ``custody_source_authorized=False``.  This gate pins
        that: production cannot mint the authority the prototype hands out.
        """
        assert INTEGRATION_STATE == "INTEGRATION_REQUIRED", (
            "RG12 empty manifest: production trust must remain INTEGRATION_REQUIRED"
        )
        assert TRUST_SCOPE_ECONOMIC_FIELD_BINDING == "ECONOMIC_FIELD_BINDING"
        for verifier, name in (
            (verify_trade_record, "verify_trade_record"),
            (verify_liquidation_record, "verify_liquidation_record"),
        ):
            source = inspect.getsource(verifier)
            assert "custody_source_authorized=False" in source, (
                f"RG12 empty manifest: {name} must hardcode "
                "custody_source_authorized=False; production must not mint "
                "custody-source authority"
            )
        default = RecordVerification.model_fields[
            "custody_source_authorized"
        ].default
        assert default is False, (
            "RG12 empty manifest: the RecordVerification default must be False "
            f"(NO AUTHORITY), got {default!r}"
        )


class TestR3GovernanceScope:
    """Governance facts about where this gate is allowed to live."""

    def test_rg13_gate_is_outside_the_frozen_i10_named_prefix_allowance(
        self,
    ) -> None:
        """Record, rather than assume, the scope admission.

        Bloc 05 I10's staged allowlist (``test_b5_i05_scope_audit.py`` row A8)
        admits exactly the named prefixes ``sensors/``, ``test_b5_i10`` and
        ``fixtures/i10/``.  This file is ``test_b5_i09p3_redteam_r3_*``, so it is
        NOT admitted by that allowance.  Renaming it to ``test_b5_i10...`` would
        disguise its purpose, and silently widening the allowlist is forbidden;
        the admission therefore requires an explicit, disclosed governance
        update before this gate may count as a governed suite.
        """
        name = Path(__file__).name
        assert name.startswith("test_b5_i09p3_redteam_r3_"), (
            "RG13: the gate must keep its honest red-team name; renaming it to "
            "fit a frozen prefix would disguise an unauthorized test"
        )
        assert not name.startswith("test_b5_i10"), (
            "RG13: this gate is not an I10 test and must not be named as one"
        )
        assert _QUANT_LAB.is_dir(), "RG13: quant-lab root must resolve for evidence paths"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
