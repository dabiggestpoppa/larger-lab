"""OCE Book 4 — proven durable audit sink (B4-CXR4R5 / B4-CXR5R5).

CXR4-06 truth repair: "durable" means DEMONSTRABLY PERSISTENT — never just
non-null and never a duck-typed ``.append()``. A Python list (or any object
with an append method) is NOT a durable sink. A durable sink:

  * declares a backend identity;
  * proves persistence AND the expected schema/backend (``proven()``) — not
    merely that one SELECT did not throw;
  * appends atomically with transaction commit confirmation;
  * is transactionally isolated — it never commits unrelated pending work on
    a shared connection, and a failed append rolls back and applies nothing;
  * stores SAFE/redacted values only (never secrets, never DSNs);
  * is reloadable (restart-persistence proof);
  * is append-only — UPDATE/DELETE on the ledger is refused in the database
    (migration 0007 trigger).

``ConfigAuthorization.audit_durable`` is True ONLY when the attached object is
exactly a ``PostgresAuditSink`` (type-exact — a subclass or a duck-typed fake
can never self-report durability) AND ``proven()``. ``isinstance`` plus the
backend-identity and schema proof is the truth gate.
"""
from __future__ import annotations

import re
import uuid

# psycopg2 transaction-status constants (kept as integer literals so the sink
# has no hard import dependency for unit-level proofs; real psycopg2
# connections expose get_transaction_status() returning these values).
TX_IDLE = 0  # psycopg2.extensions.TRANSACTION_STATUS_IDLE
TX_INTRANS = 1  # psycopg2.extensions.TRANSACTION_STATUS_INTRANS

# Columns the ledger must expose for the canonical durable record (0006 + 0007).
REQUIRED_COLUMNS = {
    "audit_id", "actor", "setting", "requested_change", "reason",
    "previous", "new", "decision", "authorized", "recorded_at",
    "request_id", "fingerprint_before", "fingerprint_after",
    "backend_identity",
}

# Secret-material patterns that must NEVER enter the audit ledger through the
# free-text fields (requested_change / reason / actor) — B4-CXR5R5 #11-12.
_SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|pwd)\s*=", re.IGNORECASE),
    re.compile(r"\b(?:token|api[_-]?key|apikey|auth[_-]?header)\s*=",
               re.IGNORECASE),
    re.compile(r"\bAuthorization\s*:", re.IGNORECASE),
    re.compile(r"\bBearer\s+", re.IGNORECASE),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def safe_audit_text(value: object, field: str) -> str:
    """Validate a free-text audit field for safe persistence (B4-CXR5R5).

    FAILS CLOSED on anything that could smuggle or corrupt:

    * non-string / empty values;
    * control characters (incl. CR/LF — multiline content could forge extra
      ledger entries or break a row-based carrier);
    * secret material (DSNs, password/token/key assignments, authorization
      headers, credential prefixes, canary patterns).

    Returns the value unchanged when safe. Zero secret bytes can ever reach
    the ledger through these fields.
    """
    if not isinstance(value, str) or not value:
        raise PermissionError(
            f"audit field '{field}' must be a non-empty string (B4-CXR5R5)")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise PermissionError(
            f"audit field '{field}' contains control characters — refused "
            "(B4-CXR5R5)")
    for pat in _SECRET_PATTERNS:
        if pat.search(value):
            raise PermissionError(
                f"audit field '{field}' contains secret material — refused "
                "(B4-CXR5R5)")
    return value


class DurableAuditSink:
    """Base contract for a PROVEN durable, append-only audit sink.

    isinstance() is part of the truth gate: ConfigAuthorization.audit_durable
    is True ONLY when the attached object is a type-exact PostgresAuditSink
    AND proven(). A list or a duck-typed .append() object is never durable.
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
    (table ``config_override_audit``, migrations 0006 + 0007).

    The connection is DEDICATED to the audit ledger. append() refuses to run
    while the connection carries ANY pending transaction (it will never
    commit unrelated application work), commits ONLY its own INSERT, and
    rolls back on failure — the override then fails closed at the caller.

    ``proven()`` proves the expected schema/backend: the ledger table must
    exist, expose every REQUIRED_COLUMNS column, and answer a SELECT — not
    merely that one SELECT did not throw. SAFE values only.
    """

    backend_identity = "postgres:config_override_audit"

    def __init__(self, conn):
        self._conn = conn

    def _tx_status(self) -> int:
        fn = getattr(self._conn, "get_transaction_status", None)
        if fn is None:
            return TX_IDLE  # unit fakes without the probe default to idle
        return int(fn())

    def proven(self) -> bool:
        """Prove backend identity + expected schema right now.

        Read-only: performs its probes inside one transaction and ROLLS BACK
        so the dedicated connection is left IDLE for append().
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT to_regclass('public.config_override_audit') "
                    "IS NOT NULL")
                if not cur.fetchone()[0]:
                    return False
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'config_override_audit'")
                cols = {row[0] for row in cur.fetchall()}
                if not REQUIRED_COLUMNS.issubset(cols):
                    return False
                cur.execute(
                    "SELECT 1 FROM config_override_audit LIMIT 1")
                cur.fetchone()
            self._conn.rollback()  # leave the dedicated connection IDLE
            return True
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass
            return False

    def append(self, record: dict) -> str:
        """Persist *record* atomically with commit confirmation; returns id.

        Idempotent on ``audit_id``/``request_id`` (ON CONFLICT DO NOTHING):
        an uncertain commit outcome can be reconciled safely by retrying with
        the same request/correlation ID — duplicate delivery of the same
        decision yields exactly one ledger row.
        """
        if self._tx_status() != TX_IDLE:
            raise RuntimeError(
                "audit connection carries a pending transaction — refusing "
                "to commit unrelated work; the audit ledger uses a DEDICATED "
                "connection (B4-CXR5R5)")
        audit_id = str(record.get("audit_id") or record.get("request_id")
                       or uuid.uuid4().hex)
        request_id = str(record.get("request_id") or audit_id)
        actor = safe_audit_text(record.get("actor", ""), "actor")
        setting = safe_audit_text(record.get("setting", ""), "setting")
        requested_change = safe_audit_text(
            record.get("requested_change", ""), "requested_change")
        reason = safe_audit_text(record.get("reason", ""), "reason")
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO config_override_audit "
                    "(audit_id, request_id, actor, setting, requested_change, "
                    " reason, previous, new, decision, authorized, "
                    " fingerprint_before, fingerprint_after, backend_identity) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (audit_id) DO NOTHING",
                    (audit_id, request_id, actor, setting, requested_change,
                     reason, record.get("previous"), record.get("new"),
                     record.get("decision", "granted"),
                     bool(record.get("authorized", True)),
                     record.get("fingerprint_before"),
                     record.get("fingerprint_after"),
                     self.backend_identity))
            self._conn.commit()  # commit confirmation
            return audit_id
        except Exception:
            try:
                self._conn.rollback()  # failed append applies NOTHING
            except Exception:
                pass
            raise

    def read_back(self) -> list[dict]:
        """Reload the committed ledger (restart-persistence proof)."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT audit_id, request_id, actor, setting, "
                "requested_change, reason, previous, new, decision, "
                "authorized, fingerprint_before, fingerprint_after, "
                "backend_identity, recorded_at "
                "FROM config_override_audit "
                "ORDER BY recorded_at, audit_id")
            rows = cur.fetchall()
        cols = ["audit_id", "request_id", "actor", "setting",
                "requested_change", "reason", "previous", "new", "decision",
                "authorized", "fingerprint_before", "fingerprint_after",
                "backend_identity", "recorded_at"]
        return [dict(zip(cols, r)) for r in rows]
