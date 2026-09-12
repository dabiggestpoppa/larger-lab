#!/usr/bin/env python3
"""OCE Local Ground — capture a deterministic, hash-protected PostgreSQL
database inventory (B1-LOCAL, A-003; recovery contract, R26).

The inventory enumerates every user table (schema-qualified) with its exact
row count AND a deterministic content fingerprint (md5 over the sorted
canonical row-JSON serialization), plus the PostgreSQL server version, all
from a running `oce-local-postgresql` container via `docker exec`.

Row counts alone are NOT content proof (different data can have identical
counts); the fingerprint proves exact values. Verification compares the
protected fingerprints at staging, promoted-canonical, restore-boundary and
rollback time. The algorithm is deterministic and documented:

    md5( string_agg( row_to_json(t)::text, '\n' ORDER BY row_to_json(t)::text ) )

Identical content -> identical fingerprint; any value change -> different
fingerprint. Fingerprint capture failure fails the whole inventory (the
backup cannot claim content proof). It is written next to the custom-format
archive so a full-replace restore can verify staging byte-for-byte before
promotion.

Usage:
    pg-inventory.py --out <inventory.json> [--container oce-local-postgresql]
                    [--db oce_local] [--user oce_local_admin]

Writes <inventory.json> and <inventory.sha256> (SHA-256 of the JSON). Exit code
is non-zero on any capture failure (fail closed).
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

CONTAINER = "oce-local-postgresql"
DB = "oce_local"
USER = "oce_local_admin"
FINGERPRINT_ALGORITHM = "md5-of-sorted-row-json"


def _exec(container, cmd):
    r = subprocess.run(["docker", "exec", container] + cmd,
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"docker exec {' '.join(cmd)} rc={r.returncode}: {r.stderr}")
    return r.stdout


def _psql(container, db, user, query):
    return _exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", db,
                             "-c", query])


def fingerprint_sql(schema, rel):
    """Deterministic content fingerprint for a table (documented algorithm):
    md5 over the sorted canonical row-JSON serialization."""
    return ('SELECT md5(COALESCE(string_agg(r, E\'\\n\' ORDER BY r), \'\')) '
            'FROM (SELECT row_to_json(t)::text AS r FROM "%s"."%s" t) sub;' % (schema, rel))


def _fingerprint(container, db, user, schema, rel):
    out = _psql(container, db, user, fingerprint_sql(schema, rel)).strip()
    if not out or len(out) != 32:
        raise RuntimeError(f"fingerprint capture failed for {schema}.{rel} (got {out!r})")
    return out


def capture(container=CONTAINER, db=DB, user=USER):
    # server version
    ver = _psql(container, db, user, "SHOW server_version_num;").strip()
    # all user tables not in system schemas
    tbl_rows = _psql(container, db, user, (
        "SELECT schemaname || '.' || tablename FROM pg_tables "
        "WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1;"
    )).splitlines()
    tables = []
    fingerprinted = []
    for tn in tbl_rows:
        tn = tn.strip()
        if not tn:
            continue
        schema, rel = tn.split(".", 1)
        # exact row count (deterministic snapshot of authoritative truth)
        cnt = _psql(container, db, user,
                    f'SELECT count(*) FROM "{schema}"."{rel}";').strip()
        # exact content fingerprint (proves values, not only counts)
        fp = _fingerprint(container, db, user, schema, rel)
        tables.append({"name": tn, "row_count": int(cnt) if cnt.isdigit() else -1,
                       "fingerprint": fp})
        fingerprinted.append(tn)
    inv = {
        "format": "oce-pg-inventory-v1",
        "database": db,
        "pg_version_num": ver,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "table_count": len(tables),
        "fingerprint_algorithm": FINGERPRINT_ALGORITHM,
        "fingerprinted_tables": fingerprinted,
        "tables": tables,
    }
    return inv


def main():
    args = sys.argv[1:]
    out = None
    container, db, user = CONTAINER, DB, USER
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out":
            i += 1
            out = args[i] if i < len(args) else None
        elif a == "--container":
            i += 1
            container = args[i] if i < len(args) else CONTAINER
        elif a == "--db":
            i += 1
            db = args[i] if i < len(args) else DB
        elif a == "--user":
            i += 1
            user = args[i] if i < len(args) else USER
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            sys.exit(2)
        i += 1
    if not out:
        print("USAGE_ERROR: --out required", file=sys.stderr)
        sys.exit(2)
    try:
        inv = capture(container, db, user)
    except Exception as e:
        print(f"BLOCKED: cannot capture database inventory: {e}", file=sys.stderr)
        sys.exit(3)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    with open(out + ".sha256", "w", encoding="utf-8") as f:
        f.write(h + "\n")
    print(f"inventory -> {out} (tables={inv['table_count']} fingerprinted={len(inv['fingerprinted_tables'])})")
    sys.exit(0)


if __name__ == "__main__":
    main()
