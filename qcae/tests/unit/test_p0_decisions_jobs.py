"""P0-C07 — AcquisitionDecision, authority primitives, Job/Step evidence."""

from __future__ import annotations

import pytest

from qcae.core.decisions.acquisition import (
    AcquisitionDecision,
    DecisionOutcome,
    RejectionReason,
    make_acquisition_decision,
)
from qcae.core.decisions.authority import (
    AuthorityDecision,
    AuthorityOutcome,
    AuthorityProvider,
    AuthorityRequest,
    IdentityProvider,
    PolicyAction,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import (
    Job,
    JobStatus,
    Step,
    StepStatus,
    deterministic_job_id,
    make_job,
)
from qcae.core.vocabulary import AcquisitionForm

DIG = "a1b2c3d4e5f6"
AF = AcquisitionForm


def rejected_decision(**overrides) -> AcquisitionDecision:
    fields = {
        "decision_id": "dec-0001",
        "capability_scope": "CAP-ATOM-OB-STATE",
        "candidate_ref": "cand:acme/obtool",
        "form": AF.REJECT,
        "outcome": DecisionOutcome.REJECTED,
        "rationale": "AGPL license conflicts with Quant Lab distribution model",
        "rejection_reason": RejectionReason.LICENSE_CONFLICT,
        "evidence_digests": (DIG,),
        "decided_by": "human:quant-lab-operator",
    }
    fields.update(overrides)
    return AcquisitionDecision(**fields)


class TestAcquisitionDecision:
    def test_valid_rejection(self) -> None:
        rejected_decision().validate()

    def test_valid_approval(self) -> None:
        make_acquisition_decision(
            decision_id="dec-0002",
            capability_scope="CAP-ATOM-CHANGEPOINT",
            candidate_ref="cand:internal-z",
            form=AF.REIMPLEMENT_FROM_SPEC,
            outcome=DecisionOutcome.APPROVED,
            rationale="clean-room reimplementation from recovered specification",
            evidence_digests=(DIG,),
            authority_decision_ref="authdec-0007",
            decided_by="human:quant-lab-operator",
        )

    def test_valid_deferral(self) -> None:
        make_acquisition_decision(
            decision_id="dec-0003",
            capability_scope="CAP-ATOM-BENCH",
            candidate_ref="cand:slow-bench",
            form=AF.DEFER,
            outcome=DecisionOutcome.DEFERRED,
            rationale="missing benchmark environment",
            deferred_pending="benchmark environment provisioning",
        )

    def test_rejection_requires_reason(self) -> None:
        with pytest.raises(QcaeValidationError, match="rejection_reason"):
            rejected_decision(rejection_reason=None).validate()

    def test_rejection_is_negative_knowledge(self) -> None:
        """Canon 0.2.8: rejection records why, durably."""
        decision = rejected_decision()
        assert decision.rejection_reason is RejectionReason.LICENSE_CONFLICT
        assert decision.rationale

    def test_non_rejection_with_rejection_reason_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="only valid on REJECTED"):
            rejected_decision(
                outcome=DecisionOutcome.APPROVED,
                authority_decision_ref="authdec-1",
            ).validate()

    def test_deferred_requires_pending_reason(self) -> None:
        with pytest.raises(QcaeValidationError, match="deferred_pending"):
            make_acquisition_decision(
                decision_id="dec-0004",
                capability_scope="CAP-ATOM-BENCH",
                candidate_ref="cand:x",
                form=AF.DEFER,
                outcome=DecisionOutcome.DEFERRED,
                rationale="waiting on upstream",
            )

    def test_non_deferred_with_pending_reason_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="only valid on DEFERRED"):
            rejected_decision(deferred_pending="upstream release").validate()

    def test_rejected_decision_requires_evidence(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence"):
            rejected_decision(evidence_digests=()).validate()

    def test_deferred_without_evidence_allowed(self) -> None:
        make_acquisition_decision(
            decision_id="dec-0005",
            capability_scope="CAP-ATOM-BENCH",
            candidate_ref="cand:x",
            form=AF.DEFER,
            outcome=DecisionOutcome.DEFERRED,
            rationale="not currently worth integration cost",
            deferred_pending="cost re-evaluation next quarter",
        )

    def test_approval_requires_authority_decision(self) -> None:
        """Canon 0.2.12: intelligence is not authority; no self-approval."""
        with pytest.raises(QcaeValidationError, match="authority_decision_ref"):
            AcquisitionDecision(
                decision_id="dec-0006",
                capability_scope="CAP-ATOM-X",
                candidate_ref="cand:x",
                form=AF.USE_DEPENDENCY,
                outcome=DecisionOutcome.APPROVED,
                rationale="looks great",
                evidence_digests=(DIG,),
            ).validate()

    def test_bad_form_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="AcquisitionForm"):
            rejected_decision(form="BUY_EVERYTHING").validate()

    def test_duplicate_evidence_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            rejected_decision(evidence_digests=(DIG, DIG)).validate()

    def test_same_repo_different_atom_decisions(self) -> None:
        """Master prompt §17: decisions are capability/atom-scoped."""
        reject = rejected_decision(capability_scope="CAP-ATOM-ALPHA")
        approve = make_acquisition_decision(
            decision_id="dec-0008",
            capability_scope="CAP-ATOM-BETA",
            candidate_ref="cand:acme/obtool",
            form=AF.EXTRACT_ALGORITHM,
            outcome=DecisionOutcome.APPROVED,
            rationale="estimator reusable despite strategy rejection",
            evidence_digests=(DIG,),
            authority_decision_ref="authdec-2",
        )
        assert reject.candidate_ref == approve.candidate_ref
        assert reject.capability_scope != approve.capability_scope

    def test_round_trip(self) -> None:
        decision = rejected_decision(supersedes_decision="dec-0000")
        rebuilt = AcquisitionDecision.from_dict(decision.to_dict())
        assert rebuilt == decision
        assert rebuilt.outcome is DecisionOutcome.REJECTED
        assert rebuilt.rejection_reason is RejectionReason.LICENSE_CONFLICT
        assert rebuilt.form is AF.REJECT


class TestAuthority:
    def test_valid_request_and_decision(self) -> None:
        request = AuthorityRequest(
            request_id="authreq-0001",
            action=PolicyAction.MAY_EXECUTE_IN_SANDBOX,
            subject_id="cand:acme/obtool",
            justification="zero-trust proving run in isolated sandbox",
            requested_by="worker:sandbox-build",
            context={"sandbox_profile": "zero-trust-default"},
        )
        request.validate()
        decision = AuthorityDecision(
            decision_id="authdec-0001",
            request_ref="authreq-0001",
            action=PolicyAction.MAY_EXECUTE_IN_SANDBOX,
            outcome=AuthorityOutcome.GRANT,
            decided_by="local-policy-shim",
            decided_at="2026-09-12T00:00:00Z",
        )
        decision.validate()

    def test_policy_actions_cover_canon_035(self) -> None:
        assert {a.value for a in PolicyAction} == {
            "may_discover",
            "may_clone_to_sandbox",
            "may_execute_in_sandbox",
            "may_access_dataset_class",
            "may_generate_adapter",
            "may_persist_registry_record",
            "requires_human_approval_for_integration",
        }

    def test_authority_outcomes_cover_canon_036(self) -> None:
        assert {o.value for o in AuthorityOutcome} == {
            "GRANT", "DENY", "REQUEST_MORE_EVIDENCE",
        }

    def test_bad_action_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="PolicyAction"):
            AuthorityRequest(
                request_id="authreq-2",
                action="do_anything_i_want",
                subject_id="cand:x",
                justification="because",
                requested_by="worker:x",
            ).validate()

    def test_provider_protocol_shape(self) -> None:
        """Core depends only on the Protocol; adapters implement it (canon 0.3.6)."""

        class _Shim:
            def decide(self, request: AuthorityRequest) -> AuthorityDecision:
                return AuthorityDecision(
                    decision_id="authdec-shim",
                    request_ref=request.request_id,
                    action=request.action,
                    outcome=AuthorityOutcome.DENY,
                    decided_by="local-policy-shim",
                    decided_at="2026-09-12T00:00:00Z",
                    reason="default deny",
                )

        shim = _Shim()
        assert isinstance(shim, AuthorityProvider)
        decision = shim.decide(
            AuthorityRequest(
                request_id="authreq-3",
                action=PolicyAction.MAY_DISCOVER,
                subject_id="CAP-REPLAY-001",
                justification="github search",
                requested_by="worker:discovery",
            )
        )
        assert decision.outcome is AuthorityOutcome.DENY
        decision.validate()

    def test_identity_provider_protocol_shape(self) -> None:
        class _Identity:
            def current_identity(self) -> str:
                return "human:quant-lab-operator"

        assert isinstance(_Identity(), IdentityProvider)

    def test_authority_round_trip(self) -> None:
        decision = AuthorityDecision(
            decision_id="authdec-9",
            request_ref="authreq-9",
            action=PolicyAction.REQUIRES_HUMAN_APPROVAL_FOR_INTEGRATION,
            outcome=AuthorityOutcome.REQUEST_MORE_EVIDENCE,
            decided_by="local-policy-shim",
            decided_at="2026-09-12T01:00:00Z",
            reason="integration evidence missing",
        )
        rebuilt = AuthorityDecision.from_dict(decision.to_dict())
        assert rebuilt == decision
        assert rebuilt.outcome is AuthorityOutcome.REQUEST_MORE_EVIDENCE


class TestJobStep:
    def test_deterministic_identity_stable(self) -> None:
        """Same logical work => same identity, regardless of timing/host."""
        a = deterministic_job_id("discover", "CAP-REPLAY-001", "run-1")
        b = deterministic_job_id("discover", "CAP-REPLAY-001", "run-1")
        assert a == b

    def test_deterministic_identity_discriminating(self) -> None:
        assert deterministic_job_id("discover", "CAP-REPLAY-001", "run-1") != (
            deterministic_job_id("discover", "CAP-REPLAY-001", "run-2")
        )
        assert deterministic_job_id("discover", "CAP-REPLAY-001", "run-1") != (
            deterministic_job_id("forensic", "CAP-REPLAY-001", "run-1")
        )

    def test_deterministic_id_survives_round_trip(self) -> None:
        det_id = deterministic_job_id("prove", "cand:acme/obtool", "nightly-42")
        job = make_job(
            job_id="job-physical-1",
            deterministic_id=det_id,
            job_kind="prove",
            subject_ref="cand:acme/obtool",
            steps=(
                Step(step_id="step-1", step_kind="build"),
                Step(step_id="step-2", step_kind="contract-tests"),
            ),
            worker_role="Sandbox / Build Worker",
            created_by="orchestrator",
            created_at="2026-09-12T00:00:00Z",
        )
        rebuilt = Job.from_dict(job.to_dict())
        assert rebuilt.deterministic_id == det_id
        assert rebuilt == job
        assert all(isinstance(s, Step) for s in rebuilt.steps)

    def test_deterministic_id_must_come_from_generator(self) -> None:
        with pytest.raises(QcaeValidationError, match="deterministic_job_id"):
            make_job(
                job_id="job-2",
                deterministic_id="totally-random",
                job_kind="prove",
                subject_ref="cand:x",
            )

    def test_failed_step_requires_error(self) -> None:
        with pytest.raises(QcaeValidationError, match="error"):
            Step(step_id="step-9", step_kind="build", status=StepStatus.FAILED).validate()

    def test_step_evidence_linkage(self) -> None:
        step = Step(
            step_id="step-3",
            step_kind="contract-tests",
            status=StepStatus.SUCCEEDED,
            evidence_digests=(DIG,),
        )
        step.validate()

    def test_bad_step_evidence_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="evidence_digests"):
            Step(
                step_id="step-4",
                step_kind="build",
                evidence_digests=("nope",),
            ).validate()

    def test_job_statuses(self) -> None:
        assert {s.value for s in JobStatus} == {
            "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED",
        }
        assert {s.value for s in StepStatus} == {
            "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "SKIPPED", "CANCELLED",
        }

    def test_duplicate_steps_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_job(
                job_id="job-3",
                deterministic_id=deterministic_job_id("k", "subj-1", "key-1"),
                job_kind="k",
                subject_ref="subj-1",
                steps=(
                    Step(step_id="step-1", step_kind="build"),
                    Step(step_id="step-1", step_kind="test"),
                ),
            )

    def test_bad_subject_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="subject_ref"):
            make_job(
                job_id="job-4",
                deterministic_id=deterministic_job_id("k", "bad subject!", "key-2"),
                job_kind="k",
                subject_ref="bad subject!",
            )
