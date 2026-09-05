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

    ``proven()`` proves the exact governed structure (B4-CXR7U8-06): table/
    schema identity, every required column with type AND nullability, a
    PRIMARY KEY specifically on audit_id, the request_id uniqueness index
    bound to this exact table/schema/column, and the append-only trigger with
    the governed function enabled. SAFE values only.
    """

    backend_identity = "postgres:config_override_audit"

    def __init__(self, conn, *, governed_database: str | None = None,
                 governed_user: str | None = None):
        self._conn = conn
        # Pinned governed identity (B4-CXR7U8-06): proven() verifies the
        # connection is attached to EXACTLY this database/role, so a cloned
        # table on a non-governed database is never proven. The production
        # seam pins these from the ActivationContext-derived connection; when
        # None the database-identity probe is skipped (structure-only proof).
        self._governed_database = governed_database
        self._governed_user = governed_user

    def _tx_status(self) -> int:
        fn = getattr(self._conn, "get_transaction_status", None)
        if fn is None:
            return TX_IDLE  # unit fakes without the probe default to idle
        return int(fn())

    def proven(self) -> bool:
        """Prove the EXACT governed structure (B4-CXR7U8-06), not merely that
        a SELECT did not throw. Inside one read-only transaction (rolled back
        so the dedicated connection is left IDLE):

        * when a governed database identity is pinned at construction, the
          connection must be attached to that exact database (current_db) and
          role (current_user) — a cloned table on a non-governed database is
          NEVER proven;
        * the governed table exists in schema 'public' and every required
          column is present with the EXPECTED type AND nullability (the
          NOT NULL set matches the 0006/0007/0008 migration exactly);
        * the PRIMARY KEY is specifically on audit_id (a PK on any other
          column fails the proof);
        * the request_id uniqueness index belongs to THIS exact table and
          schema, is unique/valid/ready, and covers exactly request_id (a
          same-named index on another table, in another schema, or over the
          wrong column fails the proof);
        * the append-only trigger belongs to this exact table, calls the
          expected governed function, and is enabled;
        * the connection is left in an acceptable transaction state (IDLE).
        """
        try:
            with self._conn.cursor() as cur:
                # 0. exact governed database/role identity (when pinned)
                if self._governed_database is not None:
                    cur.execute("SELECT current_database(), current_user")
                    row = cur.fetchone()
                    if row is None or row[0] != self._governed_database:
                        return False
                    if self._governed_user is not None and \
                            row[1] != self._governed_user:
                        return False
                # 1. table identity in the governed schema
                cur.execute(
                    "SELECT to_regclass('public.config_override_audit') "
                    "IS NOT NULL")
                if not cur.fetchone()[0]:
                    return False
                # 2. required columns, types AND nullability
                cur.execute(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'config_override_audit'")
                colinfo = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
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
                not_null = {"audit_id", "actor", "setting",
                            "requested_change", "reason", "decision",
                            "authorized", "recorded_at", "request_id",
                            "backend_identity"}
                for col in not_null:
                    if colinfo[col][1] != "NO":
                        return False
                for col in REQUIRED_COLUMNS - not_null:
                    if colinfo[col][1] != "YES":
                        return False
                # 3. PRIMARY KEY specifically on audit_id IN THE GOVERNED
                #    public schema (a same-named table cloned in another
                #    schema can never satisfy the proof)
                cur.execute(
                    "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c "
                    "JOIN pg_class t ON t.oid = c.conrelid "
                    "JOIN pg_namespace ns ON ns.oid = t.relnamespace "
                    "WHERE t.relname = 'config_override_audit' "
                    "AND ns.nspname = 'public' AND c.contype = 'p'")
                pk_row = cur.fetchone()
                if pk_row is None or "PRIMARY KEY (audit_id)" not in pk_row[0]:
                    return False
                # 4. request_id uniqueness bound to THIS table, unique,
                #    valid, ready, covering exactly request_id
                cur.execute(
                    "SELECT i.indisunique, i.indisvalid, i.indisready, "
                    "pg_get_indexdef(i.indexrelid) "
                    "FROM pg_index i "
                    "JOIN pg_class idx ON idx.oid = i.indexrelid "
                    "JOIN pg_class tbl ON tbl.oid = i.indrelid "
                    "JOIN pg_namespace ns ON ns.oid = idx.relnamespace "
                    "WHERE idx.relname = 'config_override_audit_request_id_key' "
                    "AND tbl.relname = 'config_override_audit' "
                    "AND ns.nspname = 'public'")
                idx = cur.fetchone()
                if idx is None or not (idx[0] and idx[1] and idx[2]):
                    return False
                if "(request_id)" not in idx[3]:
                    return False  # same-named index over the WRONG column
                # 5. append-only trigger: exact table + governed function +
                #    enabled
                cur.execute(
                    "SELECT t.tgname, p.proname, t.tgenabled "
                    "FROM pg_trigger t "
                    "JOIN pg_proc p ON p.oid = t.tgfoid "
                    "WHERE t.tgrelid = 'config_override_audit'::regclass "
                    "AND NOT t.tgisinternal")
                trig = None
                for trow in cur.fetchall():
                    if trow[0] == "config_override_audit_append_only":
                        trig = trow
                if trig is None or \
                        trig[1] != "config_override_audit_append_only" or \
                        trig[2] not in ("O", "A"):
                    return False
                cur.execute("SELECT 1 FROM config_override_audit LIMIT 1")
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


    # INSERT handled with ON CONFLICT DO NOTHING RETURNING: every governed
    # uniqueness constraint (audit_id PRIMARY KEY AND the request_id unique
    # index) is swallowed WITHOUT aborting the transaction — a request_id-only
    # collision no longer raises and then tries to reconcile on an aborted
    # transaction (B4-CXR7U8-05).
    _INSERT_SQL = (
        "INSERT INTO config_override_audit "
        "(audit_id, request_id, actor, setting, requested_change, "
        " reason, previous, new, decision, authorized, "
        " fingerprint_before, fingerprint_after, backend_identity) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT DO NOTHING RETURNING audit_id")

    # Full canonical decision columns compared on conflict (B4-CXR6R3): a
    # request/correlation ID may reconcile ONLY the EXACT same durable
    # decision. Looked up by EITHER governed key (the row that actually
    # blocked the insert); every semantic field compared canonically.
    _RECONCILE_SQL = (
        "SELECT audit_id, actor, setting, requested_change, reason, "
        "previous, new, decision, authorized, fingerprint_before, "
        "fingerprint_after, backend_identity "
        "FROM config_override_audit "
        "WHERE request_id = %s OR audit_id = %s "
        "ORDER BY recorded_at, audit_id")

    def append(self, record: dict) -> str:
        """Persist *record* atomically with commit confirmation; returns the
        audit ID of the row that ACTUALLY EXISTS durably (B4-CXR7U8-05).

        Idempotency is EXACT (B4-CXR6R3): a request/correlation ID may
        reconcile ONLY the same committed decision.

        * NEW record: INSERT ... ON CONFLICT DO NOTHING RETURNING audit_id —
          a returned row means a fresh durable insert; commit confirmation;
          the returned audit_id is the inserted one.
        * CONFLICT on ANY governed uniqueness constraint (audit_id PK or the
          unique request_id index) is handled WITHOUT aborting the
          transaction: no row is returned, the conflicting durable row is
          read back by request_id OR audit_id, and every canonical semantic
          field is compared.
        * EXACT retry (one durable row matches every canonical field):
          reconciles as the SAME committed operation and returns THAT row's
          durable audit_id (identity model B: distinct IDs are permitted but
          the returned ID always resolves to the existing durable row).
        * DIVERGENT reuse (no durable row matches every field): FAIL CLOSED —
          PermissionError, no applicable value, the existing durable row is
          unchanged, and the transaction stays usable (rolled back by the
          caller contract only on failure paths that need it).

        Typed `previous`/`new` values (int/bool/None/str) are normalized
        through canonical_audit_value() BEFORE insertion AND BEFORE
        comparison — PostgreSQL returns TEXT columns as strings, and only one
        canonical form makes exact-retry comparison truthful.
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
        previous = canonical_audit_value(record.get("previous"), "previous")
        new_value = canonical_audit_value(record.get("new"), "new")
        decision = str(record.get("decision", "granted"))
        authorized = bool(record.get("authorized", True))
        fp_before = record.get("fingerprint_before")
        fp_after = record.get("fingerprint_after")
        expected = (
            actor, setting, requested_change, reason,
            previous, new_value, decision, authorized,
            fp_before, fp_after, self.backend_identity)
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    self._INSERT_SQL,
                    (audit_id, request_id, actor, setting,
                     requested_change, reason, previous, new_value,
                     decision, authorized, fp_before, fp_after,
                     self.backend_identity))
                returned = cur.fetchone()
                if returned is not None:
                    durable_audit_id = str(returned[0])
                    self._conn.commit()  # commit confirmation
                    return durable_audit_id
                # conflict on a governed uniqueness constraint (audit_id PK
                # OR the unique request_id index) — the transaction is still
                # USABLE (ON CONFLICT DO NOTHING never aborts it). Reconcile
                # against the durable row that actually exists.
                cur.execute(self._RECONCILE_SQL, (request_id, audit_id))
                matches = []
                for row in cur.fetchall():
                    if tuple(row[1:]) == expected:
                        matches.append(str(row[0]))
                if len(matches) == 1:
                    durable_audit_id = matches[0]
                    self._conn.commit()
                    return durable_audit_id
                if len(matches) > 1:
                    raise RuntimeError(
                        "duplicate durable rows reconcile the same retry — "
                        "governed uniqueness is broken; manual remediation "
                        "required (B4-CXR7U8-05)")
                raise PermissionError(
                    "request_id/audit_id reuse with a DIVERGENT durable "
                    "decision — refused; no applicable value and the existing "
                    "durable row is unchanged (B4-CXR6R3)")
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
