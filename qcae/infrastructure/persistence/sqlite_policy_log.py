"""SQLite adapter for the governance PolicyDecisionLog port (P2-C04).

Engine code stays in infrastructure per the architecture guard (canon 15.2);
governance code depends only on the Protocol in
``qcae.governance.standalone.authority``.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.policy import PolicyDecision, PolicyRequest

__all__ = ["SqlitePolicyDecisionLog", "GOVERNANCE_DDL"]

GOVERNANCE_DDL = """
CREATE TABLE IF NOT EXISTS governance_policy_request (
    request_ref       TEXT PRIMARY KEY,
    principal         TEXT NOT NULL,
    action            TEXT NOT NULL,
    resource          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_policy_decision (
    decision_id       TEXT PRIMARY KEY,
    request_ref       TEXT NOT NULL,
    decision          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_gov_decision_request
    ON governance_policy_decision(request_ref);
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


class SqlitePolicyDecisionLog:
    """Append-oriented policy request/decision persistence."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def record_request(self, request_ref: str, request: PolicyRequest) -> None:
        payload, digest = _encode(request)
        try:
            self._conn.execute(
                "INSERT INTO governance_policy_request (request_ref, principal,"
                " action, resource, payload_json, payload_digest, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (request_ref, request.principal, request.action, request.resource,
                 payload, digest, "recorded"),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"policy request {request_ref!r} already exists (duplicate request)"
            ) from exc

    def record_decision(self, request_ref: str, decision: PolicyDecision) -> None:
        payload, digest = _encode(decision)
        self._conn.execute(
            "INSERT INTO governance_policy_decision (decision_id, request_ref,"
            " decision, payload_json, payload_digest, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (decision.decision_id, request_ref, decision.decision.value,
             payload, digest, decision.created_at),
        )

    def decisions_for_request(self, request_ref: str) -> List[PolicyDecision]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_policy_decision"
            " WHERE request_ref = ? ORDER BY created_at, decision_id",
            (request_ref,),
        ).fetchall()
        return [_decode((r[0], r[1]), request_ref, PolicyDecision) for r in rows]

    def get_decision(self, decision_id: str) -> Optional[PolicyDecision]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM governance_policy_decision"
            " WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        return _decode((row[0], row[1]), decision_id, PolicyDecision) if row else None
