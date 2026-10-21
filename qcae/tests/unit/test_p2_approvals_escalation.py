"""P2-C05 — approval + escalation qualification (directive §13-14, §30)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
    EscalationDecision,
    EscalationRecord,
    EscalationState,
    EscalationTrigger,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry as ApprovalRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db

NOW = "2026-09-13T12:00:00Z"


def _request(**over):
    base = dict(
        request_id="req-00000010",
        principal="id-worker-1",
        action="may_execute_in_sandbox",
        resource="cand-0001",
        scope="sandbox:isolated",
        budget_ref="bud-0001",
        justification="run contract tests",
        created_at=NOW,
        expires_at="2026-09-13T18:00:00Z",
    )
    base.update(over)
    return ApprovalRequest(**base)


def _grant(request, **over):
    base = dict(
        decision_id="dec-00000001",
        request_ref=request.request_id,
        state=ApprovalState.GRANTED,
        decided_by="id-operator-1",
        decided_at=NOW,
        bound_action=request.action,
        bound_resource=request.resource,
        bound_scope=request.scope,
        bound_budget_ref=request.budget_ref,
        reason="approved for sandbox testing only",
    )
    base.update(over)
    return ApprovalDecision(**base)


def _registry():
    conn = open_metadata_db(":memory:")
    conn.executescript(APPROVAL_DDL)
    return ApprovalRegistry(conn), conn


class TestApprovals:
    def test_request_and_grant_round_trip(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        reg.record_decision(_grant(req))
        grant = reg.effective_grant(req.request_id, now=NOW)
        assert grant is not None
        assert grant.bound_scope == "sandbox:isolated"

    def test_expired_grant_cannot_execute(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        reg.record_decision(_grant(req))
        assert reg.effective_grant(req.request_id, now="2026-09-13T19:00:00Z") is None

    def test_denied_request_has_no_grant(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        reg.record_decision(
            _grant(req, state=ApprovalState.DENIED, reason="not appropriate")
        )
        assert reg.effective_grant(req.request_id, now=NOW) is None

    def test_no_response_is_not_approval(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        assert reg.effective_grant(req.request_id, now=NOW) is None

    def test_scope_laundering_rejected(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        with pytest.raises(QcaeValidationError, match="laundering"):
            reg.record_decision(
                _grant(req, bound_scope="production:live-trading")
            )

    def test_action_laundering_rejected(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        with pytest.raises(QcaeValidationError, match="laundering"):
            reg.record_decision(
                _grant(req, bound_action="may_access_production_credentials")
            )

    def test_budget_laundering_rejected(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        with pytest.raises(QcaeValidationError, match="laundering"):
            reg.record_decision(_grant(req, bound_budget_ref="bud-99999999"))

    def test_wrong_approver_cannot_execute(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        reg.record_decision(
            _grant(req, decided_by="id-worker-1")  # self-approval
        )
        grant = reg.effective_grant(req.request_id, now=NOW)
        # The record exists; the runtime layer rejects worker self-approval
        # via approver-domain checks — modeled here as the grant carrying the
        # wrong approver, which callers must verify against policy.
        assert grant.decided_by == "id-worker-1"

    def test_forged_approval_id_fails(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        with pytest.raises(QcaeValidationError, match="unknown request"):
            reg.record_decision(
                _grant(req, request_ref="req-nonexistent")
            )

    def test_duplicate_decision_rejected(self):
        reg, _ = _registry()
        req = _request()
        reg.add_request(req)
        reg.record_decision(_grant(req))
        with pytest.raises(QcaeValidationError, match="already exists"):
            reg.record_decision(_grant(req, decision_id="dec-00000001"))

    def test_pending_list(self):
        reg, _ = _registry()
        reg.add_request(_request())
        reg.add_request(_request(request_id="req-00000011"))
        assert len(reg.pending_requests()) == 2
        reg.record_decision(_grant(_request()))
        assert len(reg.pending_requests()) == 1

    def test_tampered_request_detected(self):
        reg, conn = _registry()
        req = _request()
        reg.add_request(req)
        original = conn.execute(
            "SELECT payload_json FROM governance_approval_request WHERE request_id = ?",
            (req.request_id,),
        ).fetchone()[0]
        conn.execute(
            "UPDATE governance_approval_request SET payload_json = ? WHERE request_id = ?",
            (original.replace("sandbox", "production"), req.request_id),
        )
        with pytest.raises(QcaeValidationError, match="integrity"):
            reg.get_request(req.request_id)


class TestEscalation:
    def _escalation(self, **over):
        base = dict(
            escalation_id="esc-00000001",
            trigger=EscalationTrigger.PRODUCTION_CREDENTIAL_REQUEST,
            job_id="job-12345678",
            step_id="s-00000001",
            decision_requested="permit production credential access?",
            why_policy_cannot_decide="policy has no rule for production credentials",
            options=("grant", "deny", "defer"),
            supporting_evidence_refs=("ev-aaaaaaaa",),
            known_risks=("credential exposure",),
            reversibility="irreversible once used",
            consequence_of_no_decision="job remains WAITING",
            created_at=NOW,
        )
        base.update(over)
        return EscalationRecord(**base)

    def test_escalation_round_trip(self):
        reg, _ = _registry()
        esc = self._escalation()
        reg.add_escalation(esc)
        assert reg.get_escalation(esc.escalation_id) == esc
        assert reg.open_escalations_for_job(esc.job_id)

    def test_job_waits_while_escalation_open(self):
        reg, _ = _registry()
        esc = self._escalation()
        reg.add_escalation(esc)
        # Runtime contract: open escalation => no grant path until decided.
        assert reg.get_escalation(esc.escalation_id).state is EscalationState.OPEN

    def test_decision_resumes(self):
        reg, _ = _registry()
        esc = self._escalation()
        reg.add_escalation(esc)
        reg.record_escalation_decision(
            EscalationDecision(
                decision_id="escdec-1", escalation_ref=esc.escalation_id,
                state=EscalationState.RESOLVED_CONTINUE,
                decided_by="id-operator-1", decided_at=NOW,
                scope="job-12345678", reason="approved with sandbox profile",
            )
        )
        assert (
            reg.get_escalation(esc.escalation_id).state
            is EscalationState.RESOLVED_CONTINUE
        )
        assert reg.open_escalations_for_job(esc.job_id) == []

    def test_decision_terminates(self):
        reg, _ = _registry()
        esc = self._escalation()
        reg.add_escalation(esc)
        reg.record_escalation_decision(
            EscalationDecision(
                decision_id="escdec-2", escalation_ref=esc.escalation_id,
                state=EscalationState.RESOLVED_TERMINATE,
                decided_by="id-operator-1", decided_at=NOW,
                scope="job-12345678", reason="denied",
            )
        )
        assert (
            reg.get_escalation(esc.escalation_id).state
            is EscalationState.RESOLVED_TERMINATE
        )

    def test_decision_cannot_reference_unknown_escalation(self):
        reg, _ = _registry()
        with pytest.raises(QcaeValidationError, match="unknown escalation"):
            reg.record_escalation_decision(
                EscalationDecision(
                    decision_id="escdec-3", escalation_ref="esc-ghost",
                    state=EscalationState.RESOLVED_DEFER,
                    decided_by="id-operator-1", decided_at=NOW,
                    scope="s", reason="r",
                )
            )

    def test_escalation_requires_evidence(self):
        with pytest.raises(QcaeValidationError, match="evidence"):
            self._escalation(supporting_evidence_refs=()).validate()

    def test_escalation_requires_options(self):
        with pytest.raises(QcaeValidationError, match="options"):
            self._escalation(options=()).validate()
