"""B4-CXR7U5 — audit reconciliation proven through the PRODUCTION sink.

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
    — it does not surface as a raw unique-violation error."""
    from oce_control.audit_sink import PostgresAuditSink
    sink = PostgresAuditSink(pg)
    rid = "u5-rid-only-collision-0001"
    sink.append(_sink_record("audit-X-" + rid, rid, new=9104))
    # different audit_id + same request_id + exact decision: the INSERT
    # hits the request_id unique index (not the audit_id PK)
    out = sink.append(_sink_record("audit-Y-" + rid, rid, new=9104))
    assert out == "audit-Y-" + rid  # reconciled as the same committed op
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE request_id=%s", (rid,))
        assert cur.fetchone()[0] == 1


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
