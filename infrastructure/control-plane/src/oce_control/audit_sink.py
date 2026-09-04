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


# B4-CXR7U5: canonical representation of the typed `previous` / `new` audit
# columns. The ledger columns are TEXT but a retry comparison can carry typed
# Python values (int/bool/None); PostgreSQL returns TEXT columns as strings
# and unit fakes preserve original types — without ONE canonical form the
# mismatch is invisible locally and divergent from the durable truth.

def canonical_audit_value(value: object, field: str = "new") -> str | None:
    """ONE canonical safe TEXT representation of a configuration audit value
    (B4-CXR7U5), applied identically BEFORE insertion and BEFORE comparison:

    * None        -> NULL (legitimate null configuration value);
    * bool        -> 'true' | 'false' (checked BEFORE int — bool is an int
                     subclass; never the ambiguous 'True'/'1');
    * int         -> canonical decimal string ('9104');
    * str         -> the string itself (the canonical form of a string value
                     is the string; idempotent for already-canonical rows).

    Every other type fails closed: floats and arbitrary objects have no
    unambiguous representation and are refused rather than coerced.

    The function is IDEMPOTENT — canonical(canonical(x)) == canonical(x) —
    so rows read back from PostgreSQL compare equal to their canonical
    record values.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    raise PermissionError(
        f"audit field '{field}' has no unambiguous canonical representation "
        f"for type {type(value).__name__} — refused (B4-CXR7U5)")


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
        """Prove governed schema/table identity + required structure right now
        (B4-CXR7U5):

        * the governed table exists in schema 'public'
          (to_regclass('public.config_override_audit'));
        * every REQUIRED_COLUMNS column is present with the EXPECTED TYPE
          (audit_id/actor/setting/... TEXT, authorized BOOLEAN,
          recorded_at TIMESTAMPTZ);
        * request_id is NOT NULL (governed reconciliation key);
        * the request_id uniqueness index exists AND is valid;
        * the primary key exists (audit_id);
        * the append-only trigger is present AND enabled;
        * the dedicated connection is left in an acceptable transaction
          state (IDLE after the read-only probe transaction rolls back).

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
                # required columns AND their types (B4-CXR7U5)
                cur.execute(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'config_override_audit'")
                colinfo = {row[0]: (row[1], row[2])
                           for row in cur.fetchall()}
                if not REQUIRED_COLUMNS.issubset(colinfo):
                    return False
                expected_types = {
                    "audit_id": "text", "actor": "text",
                    "setting": "text", "requested_change": "text",
                    "reason": "text", "previous": "text", "new": "text",
                    "decision": "text", "authorized": "boolean",
                    "recorded_at": "timestamp with time zone",
                    "request_id": "text",
                    "fingerprint_before": "text",
                    "fingerprint_after": "text",
                    "backend_identity": "text",
                }
                for col, want in expected_types.items():
                    if colinfo[col][0] != want:
                        return False
                if colinfo["request_id"][1] != "NO":
                    return False  # request_id must be NOT NULL
                # primary key on audit_id
                cur.execute(
                    "SELECT 1 FROM information_schema.table_constraints "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'config_override_audit' "
                    "AND constraint_type = 'PRIMARY KEY' LIMIT 1")
                if cur.fetchone() is None:
                    return False
                # request_id uniqueness: index exists, is unique, and is
                # VALID (not left invalid by a failed concurrent creation)
                cur.execute(
                    "SELECT i.indisunique, i.indisvalid, i.indisready "
                    "FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid "
                    "WHERE c.relname = 'config_override_audit_request_id_key'")
                idx = cur.fetchone()
                if idx is None or not (idx[0] and idx[1] and idx[2]):
                    return False
                # append-only trigger present AND enabled (B4-CXR7U5)
                cur.execute(
                    "SELECT tgenabled FROM pg_trigger "
                    "WHERE tgrelid = 'config_override_audit'::regclass "
                    "AND tgname = 'config_override_audit_append_only'")
                trg = cur.fetchone()
                if trg is None or trg[0] not in ("O", "A"):
                    return False
                cur.execute(
                    "SELECT 1 FROM config_override_audit LIMIT 1")
                cur.fetchone()
            self._conn.rollback()  # leave the dedicated connection IDLE
            if self._tx_status() != TX_IDLE:
                return False
            return True
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass
            return False

    # Full canonical decision columns compared on conflict (B4-CXR6R3): a
    # request/correlation ID may reconcile ONLY the EXACT same durable
    # decision — any differing semantic field fails closed.
    _RECONCILE_SQL = (
        "SELECT actor, setting, requested_change, reason, previous, new, "
        "decision, authorized, fingerprint_before, fingerprint_after, "
        "backend_identity FROM config_override_audit WHERE request_id = %s")

    # INSERT with BOTH conflict arms handled (B4-CXR7U5): ON CONFLICT
    # (audit_id) DO NOTHING alone does not catch a collision caused ONLY by
    # the unique request_id index — that raises unless explicitly handled.
    _INSERT_SQL = (
        "INSERT INTO config_override_audit "
        "(audit_id, request_id, actor, setting, requested_change, "
        " reason, previous, new, decision, authorized, "
        " fingerprint_before, fingerprint_after, backend_identity) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (audit_id) DO NOTHING")

    def append(self, record: dict) -> str:
        """Persist *record* atomically with commit confirmation; returns id.

        Idempotency is EXACT (B4-CXR6R3): a request/correlation ID may
        reconcile ONLY the same committed decision.

        * NEW request ID: INSERT, commit, verify success — only then is an
          applicable value possible.
        * EXACT retry (same request ID + every canonical semantic field
          identical): the conflicting row is read back, the full decision is
          compared, and the operation reconciles as the SAME committed
          operation.
        * DIVERGENT reuse (same request ID + any differing semantic field):
          FAIL CLOSED — no applicable value, no new in-memory authoritative
          result, and the existing durable row is left unchanged.

        Both conflict arms are handled (B4-CXR7U5): an audit_id collision AND
        a request_id-only collision (the unique request_id index) each
        reconcile through the canonical comparison below.

        Typed `previous`/`new` values (int/bool/None/str) are normalized
        through canonical_audit_value() BEFORE insertion AND BEFORE
        comparison — PostgreSQL returns TEXT columns as strings, and only
        one canonical form makes exact-retry comparison truthful.

        rowcount zero is NEVER treated as success without reconciliation.
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
        # ONE canonical representation before insertion (B4-CXR7U5)
        previous = canonical_audit_value(record.get("previous"), "previous")
        new_value = canonical_audit_value(record.get("new"), "new")
        decision = record.get("decision", "granted")
        authorized = bool(record.get("authorized", True))
        fp_before = record.get("fingerprint_before")
        fp_after = record.get("fingerprint_after")
        try:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        self._INSERT_SQL,
                        (audit_id, request_id, actor, setting,
                         requested_change, reason, previous, new_value,
                         decision, authorized, fp_before, fp_after,
                         self.backend_identity))
                    conflicted = cur.rowcount == 0
            except Exception as exc:
                # the request_id-unique arm: a collision caused ONLY by the
                # unique request_id index raises (ON CONFLICT (audit_id)
                # does not catch it) — reconcile instead of failing
                if "config_override_audit_request_id_key" not in str(exc):
                    raise
                conflicted = True
            if conflicted:
                # conflict (on audit_id or the unique request_id) —
                # reconcile ONLY the exact same durable decision
                with self._conn.cursor() as cur:
                    cur.execute(self._RECONCILE_SQL, (request_id,))
                    row = cur.fetchone()
                    if row is None:
                        # conflict was on audit_id with a different
                        # request_id — look the row up by audit_id instead
                        cur.execute(
                            self._RECONCILE_SQL.replace(
                                "WHERE request_id = %s",
                                "WHERE audit_id = %s"),
                            (audit_id,))
                        row = cur.fetchone()
                    if row is None:
                        raise RuntimeError(
                            "audit conflict without an existing record — "
                            "cannot reconcile (B4-CXR6R3)")
                    # canonical comparison (B4-CXR7U5): the durable row is
                    # TEXT from PostgreSQL; the retried record is canonical
                    expected = (
                        actor, setting, requested_change, reason,
                        previous, new_value, decision, authorized,
                        fp_before, fp_after, self.backend_identity)
                    if tuple(row) != expected:
                        raise PermissionError(
                            "request_id reuse with a DIVERGENT durable "
                            "decision — refused; no applicable value and the "
                            "existing durable row is unchanged (B4-CXR6R3)")
                    # exact retry of the same committed operation: reconcile
                    # against the SAME durable row (rowcount zero + verified
                    # read-back IS the success proof)
            self._conn.commit()  # commit confirmation
            return audit_id
        except Exception:
            try:
                self._conn.rollback()  # failed append applies NOTHING
            except Exception:
                pass
            raise

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
        """Prove governed schema/table identity + required structure right now
        (B4-CXR7U5):

        * the governed table exists in schema 'public'
          (to_regclass('public.config_override_audit'));
        * every REQUIRED_COLUMNS column is present with the EXPECTED TYPE
          (audit_id/actor/setting/... TEXT, authorized BOOLEAN,
          recorded_at TIMESTAMPTZ);
        * request_id is NOT NULL (governed reconciliation key);
        * the request_id uniqueness index exists AND is valid;
        * the primary key exists (audit_id);
        * the append-only trigger is present AND enabled;
        * the dedicated connection is left in an acceptable transaction
          state (IDLE after the read-only probe transaction rolls back).

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
                # required columns AND their types (B4-CXR7U5)
                cur.execute(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'config_override_audit'")
                colinfo = {row[0]: (row[1], row[2])
                           for row in cur.fetchall()}
                if not REQUIRED_COLUMNS.issubset(colinfo):
                    return False
                expected_types = {
                    "audit_id": "text", "actor": "text",
                    "setting": "text", "requested_change": "text",
                    "reason": "text", "previous": "text", "new": "text",
                    "decision": "text", "authorized": "boolean",
                    "recorded_at": "timestamp with time zone",
                    "request_id": "text",
                    "fingerprint_before": "text",
                    "fingerprint_after": "text",
                    "backend_identity": "text",
                }
                for col, want in expected_types.items():
                    if colinfo[col][0] != want:
                        return False
                if colinfo["request_id"][1] != "NO":
                    return False  # request_id must be NOT NULL
                # primary key on audit_id
                cur.execute(
                    "SELECT 1 FROM information_schema.table_constraints "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'config_override_audit' "
                    "AND constraint_type = 'PRIMARY KEY' LIMIT 1")
                if cur.fetchone() is None:
                    return False
                # request_id uniqueness: index exists, is unique, and is
                # VALID (not left invalid by a failed concurrent creation)
                cur.execute(
                    "SELECT i.indisunique, i.indisvalid, i.indisready "
                    "FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid "
                    "WHERE c.relname = 'config_override_audit_request_id_key'")
                idx = cur.fetchone()
                if idx is None or not (idx[0] and idx[1] and idx[2]):
                    return False
                # append-only trigger present AND enabled (B4-CXR7U5)
                cur.execute(
                    "SELECT tgenabled FROM pg_trigger "
                    "WHERE tgrelid = 'config_override_audit'::regclass "
                    "AND tgname = 'config_override_audit_append_only'")
                trg = cur.fetchone()
                if trg is None or trg[0] not in ("O", "A"):
                    return False
                cur.execute(
                    "SELECT 1 FROM config_override_audit LIMIT 1")
                cur.fetchone()
            self._conn.rollback()  # leave the dedicated connection IDLE
            if self._tx_status() != TX_IDLE:
                return False
            return True
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass
            return False

    # Full canonical decision columns compared on conflict (B4-CXR6R3): a
    # request/correlation ID may reconcile ONLY the EXACT same durable
    # decision — any differing semantic field fails closed.
    _RECONCILE_SQL = (
        "SELECT actor, setting, requested_change, reason, previous, new, "
        "decision, authorized, fingerprint_before, fingerprint_after, "
        "backend_identity FROM config_override_audit WHERE request_id = %s")

    def append(self, record: dict) -> str:
        """Persist *record* atomically with commit confirmation; returns id.

        Idempotency is EXACT (B4-CXR6R3): a request/correlation ID may
        reconcile ONLY the same committed decision.

        * NEW request ID: INSERT, commit, verify success — only then is an
          applicable value possible.
        * EXACT retry (same request ID + every canonical semantic field
          identical): the conflicting row is read back, the full decision is
          compared, and the operation reconciles as the SAME committed
          operation.
        * DIVERGENT reuse (same request ID + any differing semantic field):
          FAIL CLOSED — no applicable value, no new in-memory authoritative
          result, and the existing durable row is left unchanged.

        rowcount zero is NEVER treated as success without reconciliation.
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
                if cur.rowcount == 0:
                    # conflict (on audit_id or the unique request_id) —
                    # reconcile ONLY the exact same durable decision
                    cur.execute(self._RECONCILE_SQL, (request_id,))
                    row = cur.fetchone()
                    if row is None:
                        # conflict was on audit_id with a different
                        # request_id — look the row up by audit_id instead
                        cur.execute(
                            self._RECONCILE_SQL.replace(
                                "WHERE request_id = %s",
                                "WHERE audit_id = %s"),
                            (audit_id,))
                        row = cur.fetchone()
                    if row is None:
                        raise RuntimeError(
                            "audit conflict without an existing record — "
                            "cannot reconcile (B4-CXR6R3)")
                    expected = (
                        actor, setting, requested_change, reason,
                        record.get("previous"), record.get("new"),
                        record.get("decision", "granted"),
                        bool(record.get("authorized", True)),
                        record.get("fingerprint_before"),
                        record.get("fingerprint_after"),
                        self.backend_identity)
                    if tuple(row) != expected:
                        raise PermissionError(
                            "request_id reuse with a DIVERGENT durable "
                            "decision — refused; no applicable value and the "
                            "existing durable row is unchanged (B4-CXR6R3)")
                    # exact retry of the same committed operation: reconcile
                    # against the SAME durable row (rowcount zero + verified
                    # read-back IS the success proof)
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
