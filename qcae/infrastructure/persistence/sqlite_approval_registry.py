"""SQLite approval + escalation registry (P2-C05).

Engine adapter for the governance records in
``qcae.governance.standalone.approvals`` (architecture guard: storage engines
live in infrastructure, canon 15.2). Semantics:

- approval decisions are separate durable records, never request edits;
- a GRANT must restate the request's exact (action, resource, scope, budget)
  binding — laundering is rejected at write time (directive §14);
- expired grants return None from ``effective_grant`` (§14);
- escalation decisions materialize state while preserving decision history.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
    EscalationDecision,
    EscalationRecord,
    EscalationState,
)

__all__ = ["SqliteApprovalRegistry", "APPROVAL_DDL"]

APPROVAL_DDL = """
CREATE TABLE IF NOT EXISTS governance_approval_request (
    request_id        TEXT PRIMARY KEY,
    principal         TEXT NOT NULL,
    action            TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_approval_decision (
    decision_id       TEXT PRIMARY KEY,
    request_ref       TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_approval_decision_request
    ON governance_approval_decision(request_ref);

CREATE TABLE IF NOT EXISTS governance_escalation (
    escalation_id     TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_escalation_decision (
    decision_id       TEXT PRIMARY KEY,
    escalation_ref    TEXT NOT NULL,
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_escalation_decision_ref
    ON governance_escalation_decision(escalation_ref);
"""


def _encode(record) -> tuple:
    payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
    return payload, record.digest()


def _decode(row, key: str, cls):
    payload_json, payload_digest = row
    record = cls.from_dict(json.loads(payload_json))
    if record.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored {cls.object_type()} {key!r} failed integrity check"
        )
    return record


class SqliteApprovalRegistry:
    """Durable approval + escalation state."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- Approvals -----------------------------------------------------------

    def add_request(self, request: ApprovalRequest) -> None:
        payload, digest = _encode(request)
        try:
            self._conn.execute(
                "INSERT INTO governance_approval_request (request_id, principal,"
                " action, payload_json, payload_digest, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (request.request_id, request.principal, request.action,
                 payload, digest, request.created_at),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"approval request {request.request_id!r} already exists"
            ) from exc

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_approval_request"
            " WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        return _decode((row[0], row[1]), request_id, ApprovalRequest) if row else None

    def pending_requests(self) -> List[ApprovalRequest]:
        rows = self._conn.execute(
            "SELECT r.payload_json, r.payload_digest"
            " FROM governance_approval_request r"
            " LEFT JOIN governance_approval_decision d ON d.request_ref = r.request_id"
            " WHERE d.decision_id IS NULL ORDER BY r.created_at"
        ).fetchall()
        return [_decode((r[0], r[1]), "approval", ApprovalRequest) for r in rows]

    def decisions_for_request(self, request_id: str) -> List[ApprovalDecision]:
        """All durable decisions for a request (oldest first; immutable)."""
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_approval_decision"
            " WHERE request_ref = ? ORDER BY created_at, decision_id",
            (request_id,),
        ).fetchall()
        return [_decode((r[0], r[1]), request_id, ApprovalDecision) for r in rows]

    def record_decision(self, decision: ApprovalDecision) -> None:
        decision.validate()
        request = self.get_request(decision.request_ref)
        if request is None:
            raise QcaeValidationError(
                f"decision references unknown request {decision.request_ref!r}"
            )
        # A grant must restate the request's exact binding (no laundering).
        if decision.state is ApprovalState.GRANTED:
            if (
                decision.bound_action != request.action
                or decision.bound_resource != request.resource
                or decision.bound_scope != request.scope
                or decision.bound_budget_ref != request.budget_ref
            ):
                raise QcaeValidationError(
                    "grant binding does not match the request; approval laundering rejected"
                )
        payload, digest = _encode(decision)
        try:
            self._conn.execute(
                "INSERT INTO governance_approval_decision (decision_id, request_ref,"
                " state, payload_json, payload_digest, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (decision.decision_id, decision.request_ref, decision.state.value,
                 payload, digest, decision.decided_at),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"approval decision {decision.decision_id!r} already exists"
            ) from exc

    def effective_grant(self, request_id: str, *, now: str) -> Optional[ApprovalDecision]:
        """The live grant for a request, or None (pending/denied/expired)."""
        request = self.get_request(request_id)
        if request is None:
            return None
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_approval_decision"
            " WHERE request_ref = ? ORDER BY created_at, decision_id",
            (request_id,),
        ).fetchall()
        decisions = [_decode((r[0], r[1]), request_id, ApprovalDecision) for r in rows]
        if not decisions:
            return None
        latest = decisions[-1]
        if latest.state is not ApprovalState.GRANTED:
            return None
        expiry = request.expires_at
        if expiry and now > expiry:
            return None
        return latest

    # -- Escalations ---------------------------------------------------------

    def add_escalation(self, record: EscalationRecord) -> None:
        record.validate()
        payload, digest = _encode(record)
        try:
            self._conn.execute(
                "INSERT INTO governance_escalation (escalation_id, job_id, state,"
                " payload_json, payload_digest, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (record.escalation_id, record.job_id, record.state.value,
                 payload, digest, record.created_at),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"escalation {record.escalation_id!r} already exists"
            ) from exc

    def get_escalation(self, escalation_id: str) -> Optional[EscalationRecord]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_escalation"
            " WHERE escalation_id = ?",
            (escalation_id,),
        ).fetchone()
        return _decode((row[0], row[1]), escalation_id, EscalationRecord) if row else None

    def open_escalations_for_job(self, job_id: str) -> List[EscalationRecord]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_escalation"
            " WHERE job_id = ? AND state = ? ORDER BY created_at",
            (job_id, EscalationState.OPEN.value),
        ).fetchall()
        return [_decode((r[0], r[1]), job_id, EscalationRecord) for r in rows]

    def record_escalation_decision(self, decision: EscalationDecision) -> None:
        decision.validate()
        escalation = self.get_escalation(decision.escalation_ref)
        if escalation is None:
            raise QcaeValidationError(
                f"decision references unknown escalation {decision.escalation_ref!r}"
            )
        payload, digest = _encode(decision)
        self._conn.execute(
            "INSERT INTO governance_escalation_decision (decision_id, escalation_ref,"
            " state, payload_json, payload_digest, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (decision.decision_id, decision.escalation_ref, decision.state.value,
             payload, digest, decision.decided_at),
        )
        # Materialize state on the escalation row (decision history preserved).
        updated = _with_state(escalation, decision.state)
        upayload, udigest = _encode(updated)
        self._conn.execute(
            "UPDATE governance_escalation SET state = ?, payload_json = ?,"
            " payload_digest = ? WHERE escalation_id = ?",
            (decision.state.value, upayload, udigest, decision.escalation_ref),
        )


def _with_state(record: EscalationRecord, state: EscalationState) -> EscalationRecord:
    from dataclasses import replace as dc_replace

    return dc_replace(record, state=state)
