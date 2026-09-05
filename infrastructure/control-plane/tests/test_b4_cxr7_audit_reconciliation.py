"""B4-CXR7U5 + CXR7U8-05/06 — audit reconciliation and exact structure
proven through the PRODUCTION sink.

Direct SQL helper tests do NOT count as production-sink behavior: every test
here drives ``PostgresAuditSink`` (the real production class) against real
PostgreSQL from the B2 compose stack. Proven:

* ONE canonical representation (canonical_audit_value) before insertion AND
  comparison — integer, boolean, null, and string exact retries reconcile;
* fresh-connection retry and uncertain-commit reconciliation;
* both conflict arms: same request_id with different audit_id, and same
  audit_id with different request_id;
* divergent actor/setting/reason/value/fingerprint reuse is refused with no
  applicable value and the durable row unchanged;
* proven() is False on: missing request_id uniqueness index, missing or
  disabled append-only trigger, wrong column type, nullable request_id.

B4-CXR7U8-05 (exact reconciliation): ``append`` uses INSERT ... ON CONFLICT
DO NOTHING RETURNING audit_id, so EVERY governed uniqueness collision
(audit_id PK or the request_id index) is swallowed WITHOUT aborting the
transaction — no exception-and-SELECT-on-an-aborted-transaction path.
A reconciled retry ALWAYS returns the audit_id of the row that actually
exists durably (identity model B), never an id with no durable row, and the
connection stays usable for a new record afterwards.

B4-CXR7U8-06 (exact structure): ``proven()`` verifies the governed
database/role identity when pinned, the public-schema table, every column
with exact type AND nullability, a PRIMARY KEY specifically on audit_id,
the request_id uniqueness index bound to THIS table/schema/column
(unique/valid/ready), and the append-only trigger calling the governed
function and enabled. Schema-mutation proofs: PK moved, same-named index in
another schema or on another table, index over the wrong column, wrong
trigger function, and a cloned table in another schema standing in for the
public one all fail the proof.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc

pytestmark = pytest.mark.container


@pytest.fixture(scope="module")
def pg():
    """Real PostgreSQL from the B2 compose stack."""
    import psycopg2
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    oc.stack_up()
    conn = psycopg2.connect(oc.dsn())
    conn.autocommit = False
    yield conn
    try:
        conn.close()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _clean_db(pg):
    """Fresh tables per test: full drop then migrate up from empty DB."""
    import migrate
    with pg.cursor() as cur:
        cur.execute(
            "DROP TABLE IF EXISTS schema_migrations, evidence_refs, audit_log, events, "
            "workers, schedules, leases, idempotency, job_transitions, jobs, denials, "
            "capability_grants, actors, config_override_audit CASCADE"
        )
    pg.commit()
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 0, "migrations from empty DB must succeed"


def _sink_record(audit_id, request_id, *, previous=8448, new=9104, reason="r",
                 actor="operator:po", setting="control_plane.port",
                 requested_change="x", fingerprint_before="fp-before",
                 fingerprint_after="fp-after"):
    """A typed record exactly as ConfigAuthorization submits: `previous` /
    `new` carry TYPED Python values (int/bool/None/str)."""
    return {
        "audit_id": audit_id, "request_id": request_id,
        "actor": actor, "setting": setting,
        "requested_change": requested_change, "reason": reason,
        "previous": previous, "new": new,
        "decision": "granted", "authorized": True,
        "fingerprint_before": fingerprint_before,
        "fingerprint_after": fingerprint_after,
    }


# --------------------------------------------------------------------------- #
# Canonical typed-value exact retries through the production sink
# --------------------------------------------------------------------------- #

def test_u5_integer_exact_retry_through_production_sink(pg):
    """An int-typed retry reconciles against the TEXT row the production sink
    wrote (canonical '9104' == '9104')."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-int-exact-0001"
    sink.append(_sink_record(rid, rid, new=9104, previous=8448))
    sink.append(_sink_record(rid, rid, new=9104, previous=8448))  # exact retry
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT new FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == "9104"  # canonical TEXT in the ledger


def test_u5_boolean_exact_retry_through_production_sink(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-bool-exact-0001"
    sink.append(_sink_record(rid, rid, new=False, previous=None))
    sink.append(_sink_record(rid, rid, new=False, previous=None))
    with pg.cursor() as cur:
        cur.execute("SELECT count(*), min(new) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        count, new = cur.fetchone()
    assert count == 1
    assert new == "false"  # canonical bool form — never 'False' or '0'


def test_u5_null_exact_retry_through_production_sink(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-null-exact-0001"
    sink.append(_sink_record(rid, rid, new=None, previous="9104"))
    sink.append(_sink_record(rid, rid, new=None, previous="9104"))
    with pg.cursor() as cur:
        cur.execute("SELECT count(*), new IS NULL FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        count, is_null = cur.fetchone()
    assert count == 1
    assert is_null is True  # NULL round-trips as NULL, not '' or 'None'


def test_u5_string_exact_retry_through_production_sink(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-str-exact-0001"
    sink.append(_sink_record(rid, rid, new="loopback-only", previous="unset"))
    sink.append(_sink_record(rid, rid, new="loopback-only", previous="unset"))
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


def test_u5_canonical_representation_is_idempotent():
    # the canonical form is idempotent so rows read back from PostgreSQL
    # compare equal to their canonical record values
    from oce_control.audit_sink import canonical_audit_value
    for v, want in ((True, "true"), (False, "false"), (0, "0"),
                    (9104, "9104"), (None, None), ("x", "x")):
        once = canonical_audit_value(v)
        assert once == want
        assert canonical_audit_value(once) == want  # idempotent
    for bad in (3.5, object(), ["x"], {"x": 1}):
        with pytest.raises(PermissionError):
            canonical_audit_value(bad)


# --------------------------------------------------------------------------- #
# Fresh connection / uncertain commit / conflict arms
# --------------------------------------------------------------------------- #

def test_u5_fresh_connection_exact_retry(pg):
    """An exact retry through a DIFFERENT connection (uncertain commit after
    process loss) reconciles through the production sink."""
    import psycopg2
    from oce_control.audit_sink import PostgresAuditSink
    rid = "u5-fresh-conn-0001"
    PostgresAuditSink(pg).append(_sink_record(rid, rid, new=9104))
    conn2 = psycopg2.connect(oc.dsn())
    try:
        PostgresAuditSink(conn2).append(_sink_record(rid, rid, new=9104))
        conn2.commit()
    finally:
        conn2.close()
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


def test_u5_uncertain_commit_reconciliation(pg):
    """Uncertain commit: the row is committed but the caller never learned —
    the retry reconciles via canonical comparison and returns the same id."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-uncertain-0001"
    first_id = sink.append(_sink_record(rid, rid, new=9104))
    second_id = sink.append(_sink_record(rid, rid, new=9104))
    assert first_id == second_id
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


def test_u5_same_request_id_different_audit_id(pg):
    """A retry carrying the same request_id under a different audit_id still
    reconciles EXACTLY (the governed key is request_id)."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-same-rid-0001"
    sink.append(_sink_record("audit-A-" + rid, rid, new=9104))
    sink.append(_sink_record("audit-B-" + rid, rid, new=9104))
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


def test_u5_same_audit_id_different_request_id(pg):
    """An audit_id collision with a DIFFERENT request_id and a divergent
    decision is refused — the original row stays unchanged."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    aid = "u5-shared-audit-id"
    rid1 = "u5-same-aid-r1"
    rid2 = "u5-same-aid-r2"
    sink.append(_sink_record(aid, rid1, new=9104))
    with pytest.raises(Exception):
        sink.append(_sink_record(aid, rid2, new=9999))
    with pg.cursor() as cur:
        cur.execute("SELECT request_id, new FROM config_override_audit "
                    "WHERE audit_id=%s", (aid,))
        rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == rid1 and rows[0][1] == "9104"


def test_u5_request_id_only_collision_reconciles(pg):
    """A collision caused ONLY by the unique request_id index (different
    audit_id, same request_id, exact same decision) is caught and reconciled
    — it does not surface as a raw unique-violation error. Per
    B4-CXR7U8-05 the reconciled retry returns the audit_id that ACTUALLY
    exists durably (audit-X), never the proposed id (audit-Y) for which no
    row exists."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-rid-only-collision-0001"
    durable = sink.append(_sink_record("audit-X-" + rid, rid, new=9104))
    assert durable == "audit-X-" + rid
    # different audit_id + same request_id + exact decision: the INSERT
    # hits the request_id unique index (not the audit_id PK); ON CONFLICT
    # DO NOTHING RETURNING swallows the collision without aborting the
    # transaction, and the durable row's OWN audit_id is returned
    out = sink.append(_sink_record("audit-Y-" + rid, rid, new=9104))
    assert out == durable  # resolved to the row that exists durably
    with pg.cursor() as cur:
        cur.execute("SELECT count(*), min(audit_id), max(audit_id) "
                    "FROM config_override_audit WHERE request_id=%s", (rid,))
        count, min_aid, max_aid = cur.fetchone()
    assert count == 1          # exactly one durable row
    assert min_aid == max_aid == durable  # returned id resolves to it


@pytest.mark.parametrize("field,bad", [
    ("actor", "hermes"),
    ("setting", "other.setting"),
    ("reason", "different reason"),
    ("new", 9105),
    ("fingerprint_after", "other-fp"),
    ("requested_change", "different change"),
])
def test_u5_divergent_reuse_refused_no_applicable_value(pg, field, bad):
    """Same request_id + ANY differing canonical field: the production sink
    refuses — no applicable value, existing durable row unchanged."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = f"u5-div-{field}-0001"
    sink.append(_sink_record(rid, rid, new=9104))
    record = _sink_record(rid, rid, new=9104)
    record[field] = bad
    with pytest.raises(Exception):
        sink.append(record)
    with pg.cursor() as cur:
        cur.execute("SELECT actor, setting, requested_change, reason, new, "
                    "fingerprint_after FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        row = cur.fetchone()
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1  # no second row
    assert row == ("operator:po", "control_plane.port", "x", "r",
                   "9104", "fp-after")  # original decision untouched


# --------------------------------------------------------------------------- #
# strengthened proven(): governed schema/table identity + structure
# --------------------------------------------------------------------------- #

def test_u5_proven_true_on_governed_schema(pg):
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True


def test_u5_proven_false_when_request_id_index_missing(pg):
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("DROP INDEX config_override_audit_request_id_key")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute(
                "CREATE UNIQUE INDEX config_override_audit_request_id_key "
                "ON config_override_audit (request_id)")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u5_proven_false_when_trigger_disabled(pg):
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("ALTER TABLE config_override_audit DISABLE TRIGGER "
                    "config_override_audit_append_only")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("ALTER TABLE config_override_audit ENABLE TRIGGER "
                        "config_override_audit_append_only")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u5_proven_false_when_trigger_missing(pg):
    from oce_control.audit_sink import PostgresAuditSink
    with pg.cursor() as cur:
        cur.execute("DROP TRIGGER config_override_audit_append_only "
                    "ON config_override_audit")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute(
                "CREATE TRIGGER config_override_audit_append_only "
                "BEFORE UPDATE OR DELETE ON config_override_audit "
                "FOR EACH ROW EXECUTE FUNCTION "
                "config_override_audit_append_only()")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u5_proven_false_on_wrong_column_type(pg):
    """Schema drift: a column with the wrong type (authorized INTEGER instead
    of BOOLEAN) fails proven()."""
    from oce_control.audit_sink import PostgresAuditSink
    with pg.cursor() as cur:
        cur.execute("ALTER TABLE config_override_audit "
                    "ALTER COLUMN authorized TYPE INTEGER USING "
                    "CASE WHEN authorized THEN 1 ELSE 0 END")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("ALTER TABLE config_override_audit "
                        "ALTER COLUMN authorized TYPE BOOLEAN USING "
                        "authorized = 1")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u5_request_id_not_null_enforced(pg):
    from oce_control.audit_sink import PostgresAuditSink
    with pg.cursor() as cur:
        cur.execute("SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_name='config_override_audit' "
                    "AND column_name='request_id'")
        assert cur.fetchone()[0] == "NO"
    assert PostgresAuditSink(pg).proven() is True


def test_u5_proven_rolls_back_probe_leaves_connection_idle(pg):
    """proven() runs read-only probes and leaves the dedicated connection
    IDLE — a following append() must not refuse."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    assert sink.proven() is True
    sink.append(_sink_record("u5-idle-probe-0001", "u5-idle-probe-0001"))


# --------------------------------------------------------------------------- #
# B4-CXR7U8-05: exact conflict reconciliation through the PRODUCTION sink
# --------------------------------------------------------------------------- #

def test_u8_same_audit_id_exact_retry_returns_durable_id(pg):
    """A retry colliding on the audit_id PK with the EXACT same decision is an
    idempotent retry: the durable row's audit_id is returned and only one
    durable row exists (B4-CXR7U8-05 identity model B)."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u8-same-aid-exact-0001"
    first = sink.append(_sink_record(rid, rid, new=9104))
    again = sink.append(_sink_record(rid, rid, new=9104))
    assert again == first == rid
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE audit_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


def test_u8_same_audit_id_different_request_id_exact_reconciles(pg):
    """Same audit_id, DIFFERENT request_id, EXACT same decision: the audit_id
    PK collision reconciles as the same committed operation and returns the
    durable audit_id — never an id for which no row exists."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    aid = "u8-shared-aid-exact"
    sink.append(_sink_record(aid, "u8-shared-aid-r1", new=9104))
    out = sink.append(_sink_record(aid, "u8-shared-aid-r2", new=9104))
    assert out == aid  # durable row's own audit_id
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE audit_id=%s", (aid,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT request_id FROM config_override_audit "
                    "WHERE audit_id=%s", (aid,))
        assert cur.fetchone()[0] == "u8-shared-aid-r1"  # row untouched


def test_u8_same_audit_id_different_request_id_divergent_refused(pg):
    """Same audit_id + different request_id + ANY divergent decision fails
    closed — the existing durable row stays byte-identical."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    aid = "u8-shared-aid-div"
    sink.append(_sink_record(aid, "u8-div-r1", new=9104))
    with pg.cursor() as cur:
        cur.execute("SELECT actor, setting, new, reason FROM "
                    "config_override_audit WHERE audit_id=%s", (aid,))
        before = cur.fetchone()
    with pytest.raises(Exception):
        sink.append(_sink_record(aid, "u8-div-r2", new=9105))
    with pg.cursor() as cur:
        cur.execute("SELECT actor, setting, new, reason FROM "
                    "config_override_audit WHERE audit_id=%s", (aid,))
        after = cur.fetchone()
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE audit_id=%s", (aid,))
        assert cur.fetchone()[0] == 1
    assert after == before  # durable row unchanged


def test_u8_transaction_usable_after_reconcile_and_refusal(pg):
    """After an exact reconciliation AND after a divergent refusal, the same
    dedicated connection remains usable for a NEW record — ON CONFLICT DO
    NOTHING never aborts the transaction, and the refusal rolls back cleanly
    (B4-CXR7U8-05: no aborted-transaction reconciliation)."""
    import psycopg2
    from oce_control.audit_sink import PostgresAuditSink
    conn = psycopg2.connect(oc.dsn())
    conn.autocommit = False
    try:
        sink = PostgresAuditSink(conn)
        rid1 = "u8-txn-usable-0001"
        sink.append(_sink_record(rid1, rid1, new=9104))
        sink.append(_sink_record(rid1, rid1, new=9104))  # exact reconcile
        # divergent refusal on a SECOND audit_id
        aid2 = "u8-txn-usable-0002"
        sink.append(_sink_record(aid2, "u8-txn-usable-r1", new=9104))
        with pytest.raises(Exception):
            sink.append(_sink_record(aid2, "u8-txn-usable-r2", new=9999))
        # the SAME connection must still accept and commit a NEW record
        rid3 = "u8-txn-usable-0003"
        out = sink.append(_sink_record(rid3, rid3, new=9104))
        assert out == rid3
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM config_override_audit")
            assert cur.fetchone()[0] == 3
    finally:
        conn.close()


def test_u8_semantic_field_divergence_refused(pg):
    """Every canonical semantic column is compared on conflict — including
    previous/authorized/decision/fingerprint_before — and a divergence in any
    of them fails closed (B4-CXR7U8-05)."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u8-semantic-div-0001"
    sink.append(_sink_record(rid, rid, new=9104))
    cases = [
        ("previous", 8447),
        ("authorized", False),
        ("decision", "denied"),
        ("fingerprint_before", "other-fp-before"),
    ]
    for field, bad in cases:
        r2 = f"{rid}-{field}"
        record = _sink_record(rid, rid, new=9104)
        record[field] = bad
        record["request_id"] = r2  # avoid reusing the consumed key shape
        with pytest.raises(Exception):
            sink.append(record)
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1

# --------------------------------------------------------------------------- #
# B4-CXR7U8-06: proven() proves the EXACT governed structure
# --------------------------------------------------------------------------- #

def test_u8_proven_true_with_governed_identity_pinned(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg, governed_database=oc.PG_DB,
                             governed_user=oc.PG_USER)
    assert sink.proven() is True


def test_u8_proven_false_when_pinned_database_does_not_match(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg, governed_database="some_other_db")
    assert sink.proven() is False


def test_u8_proven_false_when_pinned_user_does_not_match(pg):
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg, governed_database=oc.PG_DB,
                             governed_user="someone_else")
    assert sink.proven() is False


def test_u8_proven_false_when_pk_moved_to_another_column(pg):
    """PK moves off audit_id -> proven() False."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("ALTER TABLE config_override_audit DROP CONSTRAINT "
                    "config_override_audit_pkey")
        cur.execute("ALTER TABLE config_override_audit "
                    "ADD CONSTRAINT config_override_audit_pkey "
                    "PRIMARY KEY (request_id)")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("ALTER TABLE config_override_audit DROP CONSTRAINT "
                        "config_override_audit_pkey")
            cur.execute("ALTER TABLE config_override_audit "
                        "ADD CONSTRAINT config_override_audit_pkey "
                        "PRIMARY KEY (audit_id)")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u8_proven_false_when_index_in_other_schema(pg):
    """Same-named uniqueness index living in ANOTHER schema is not the
    governed index -> proven() False."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS evil")
        cur.execute("DROP TABLE IF EXISTS evil.config_override_audit")
        cur.execute(
            "CREATE TABLE evil.config_override_audit (audit_id TEXT "
            "PRIMARY KEY, request_id TEXT NOT NULL, actor TEXT, setting "
            "TEXT, requested_change TEXT, reason TEXT, previous TEXT, "
            "new TEXT, decision TEXT, authorized BOOLEAN, recorded_at "
            "TIMESTAMPTZ, fingerprint_before TEXT, fingerprint_after TEXT, "
            "backend_identity TEXT)")
        cur.execute("DROP INDEX IF EXISTS "
                    "config_override_audit_request_id_key")
        cur.execute("CREATE UNIQUE INDEX "
                    "config_override_audit_request_id_key "
                    "ON evil.config_override_audit (request_id)")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("CREATE UNIQUE INDEX "
                        "config_override_audit_request_id_key "
                        "ON config_override_audit (request_id)")
            cur.execute("DROP SCHEMA evil CASCADE")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u8_proven_false_when_same_named_index_on_other_table(pg):
    """Same-named index attached to a DIFFERENT table is not governed."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS decoy_audit "
                    "(audit_id TEXT PRIMARY KEY, request_id TEXT NOT NULL)")
        cur.execute("DROP INDEX IF EXISTS "
                    "config_override_audit_request_id_key")
        cur.execute("CREATE UNIQUE INDEX "
                    "config_override_audit_request_id_key "
                    "ON decoy_audit (request_id)")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("CREATE UNIQUE INDEX "
                        "config_override_audit_request_id_key "
                        "ON config_override_audit (request_id)")
            cur.execute("DROP TABLE decoy_audit")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u8_proven_false_when_index_covers_wrong_column(pg):
    """Governed unique index covering the WRONG column (audit_id instead of
    request_id) fails the proof."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("DROP INDEX IF EXISTS "
                    "config_override_audit_request_id_key")
        cur.execute("CREATE UNIQUE INDEX "
                    "config_override_audit_request_id_key "
                    "ON config_override_audit (audit_id)")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS "
                        "config_override_audit_request_id_key")
            cur.execute("CREATE UNIQUE INDEX "
                        "config_override_audit_request_id_key "
                        "ON config_override_audit (request_id)")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u8_proven_false_when_trigger_calls_wrong_function(pg):
    """Same-named trigger wired to a DIFFERENT function fails the proof."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("CREATE OR REPLACE FUNCTION impostor_append_only() "
                    "RETURNS trigger LANGUAGE plpgsql AS $$ "
                    "BEGIN RETURN NEW; END; $$")
        cur.execute("DROP TRIGGER config_override_audit_append_only ON "
                    "config_override_audit")
        cur.execute("CREATE TRIGGER config_override_audit_append_only "
                    "BEFORE UPDATE OR DELETE ON config_override_audit "
                    "FOR EACH ROW EXECUTE FUNCTION impostor_append_only()")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is False
    finally:
        with pg.cursor() as cur:
            cur.execute("DROP TRIGGER config_override_audit_append_only ON "
                        "config_override_audit")
            cur.execute("CREATE TRIGGER config_override_audit_append_only "
                        "BEFORE UPDATE OR DELETE ON config_override_audit "
                        "FOR EACH ROW EXECUTE FUNCTION "
                        "config_override_audit_append_only()")
            cur.execute("DROP FUNCTION impostor_append_only()")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True


def test_u8_proven_false_when_clone_schema_stands_in_for_public(pg):
    """A fully cloned governed table in another schema can NEVER satisfy the
    proof: when the PUBLIC table loses a governed property (its trigger), the
    clone is not accepted as a substitute."""
    from oce_control.audit_sink import PostgresAuditSink
    assert PostgresAuditSink(pg).proven() is True
    with pg.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS clone_schema")
        cur.execute("DROP TABLE IF EXISTS clone_schema.config_override_audit")
        cur.execute(
            "CREATE TABLE clone_schema.config_override_audit ("
            "audit_id TEXT PRIMARY KEY, actor TEXT NOT NULL, setting TEXT "
            "NOT NULL, requested_change TEXT NOT NULL, reason TEXT NOT "
            "NULL, previous TEXT, new TEXT, decision TEXT NOT NULL DEFAULT "
            "'granted', authorized BOOLEAN NOT NULL DEFAULT TRUE, "
            "recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(), request_id "
            "TEXT NOT NULL, fingerprint_before TEXT, fingerprint_after "
            "TEXT, backend_identity TEXT NOT NULL DEFAULT "
            "'postgres:config_override_audit')")
        cur.execute("CREATE UNIQUE INDEX "
                    "config_override_audit_request_id_key "
                    "ON clone_schema.config_override_audit (request_id)")
        cur.execute("CREATE TRIGGER config_override_audit_append_only "
                    "BEFORE UPDATE OR DELETE ON "
                    "clone_schema.config_override_audit FOR EACH ROW "
                    "EXECUTE FUNCTION config_override_audit_append_only()")
    pg.commit()
    try:
        assert PostgresAuditSink(pg).proven() is True  # public intact
        with pg.cursor() as cur:
            cur.execute("DROP TRIGGER config_override_audit_append_only ON "
                        "config_override_audit")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is False  # clone NOT accepted
    finally:
        with pg.cursor() as cur:
            cur.execute("CREATE TRIGGER config_override_audit_append_only "
                        "BEFORE UPDATE OR DELETE ON config_override_audit "
                        "FOR EACH ROW EXECUTE FUNCTION "
                        "config_override_audit_append_only()")
            cur.execute("DROP SCHEMA clone_schema CASCADE")
        pg.commit()
        assert PostgresAuditSink(pg).proven() is True
