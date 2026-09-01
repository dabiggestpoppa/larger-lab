"""OCE Book 4 — proven durable audit sink (B4-CXR4R5).

CXR4-06 truth repair: "durable" means DEMONSTRABLY PERSISTENT — never just
non-null and never a duck-typed ``.append()``. A Python list (or any object
with an append method) is NOT a durable sink. A durable sink:

  * declares a backend identity;
  * proves persistence (``proven()``) — e.g. a live transaction-capable
    connection to the append-only PostgreSQL ledger;
  * appends atomically with transaction commit confirmation;
  * can be read back (reload/restart persistence proof);
  * stores SAFE/redacted values only (never secrets, never DSNs).

``ConfigAuthorization.audit_durable`` is True ONLY when the attached object
is a ``DurableAuditSink`` AND ``proven()`` — isinstance is the truth gate.
"""
from __future__ import annotations

import uuid


class DurableAuditSink:
    """Base contract for a PROVEN durable, append-only audit sink.

    isinstance() is the truth gate: ConfigAuthorization.audit_durable is
    True ONLY when the attached object is a DurableAuditSink AND proven().
    A list or a duck-typed .append() object is never durable.
    """

    backend_identity = "abstract"

    def proven(self) -> bool:
        """True only when persistence can be DEMONSTRATED right now."""
        return False

    def append(self, record: dict) -> str:
        """Persist *record* atomically with commit confirmation; returns id."""
        raise NotImplementedError

    def read_back(self) -> list[dict]:
        """Reload the ledger (restart-persistence proof)."""
        raise NotImplementedError


class PostgresAuditSink(DurableAuditSink):
    """Append-only config-override audit in the governed PostgreSQL
    (table ``config_override_audit``, migration 0006). SAFE values only."""

    backend_identity = "postgres:config_override_audit"

    def __init__(self, conn):
        self._conn = conn

    def proven(self) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1 FROM config_override_audit LIMIT 1")
                cur.fetchone()
            return True
        except Exception:
            return False

    def append(self, record: dict) -> str:
        audit_id = record.get("audit_id") or uuid.uuid4().hex
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO config_override_audit "
                "(audit_id, actor, setting, requested_change, reason, "
                " previous, new, decision, authorized) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (audit_id, record.get("actor", ""), record.get("setting", ""),
                 record.get("requested_change", ""), record.get("reason", ""),
                 record.get("previous"), record.get("new"),
                 record.get("decision", "granted"),
                 bool(record.get("authorized", True))))
        self._conn.commit()  # commit confirmation
        return audit_id

    def read_back(self) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT audit_id, actor, setting, requested_change, reason, "
                "previous, new, decision, authorized, recorded_at "
                "FROM config_override_audit ORDER BY recorded_at, audit_id")
            rows = cur.fetchall()
        cols = ["audit_id", "actor", "setting", "requested_change", "reason",
                "previous", "new", "decision", "authorized", "recorded_at"]
        return [dict(zip(cols, r)) for r in rows]
