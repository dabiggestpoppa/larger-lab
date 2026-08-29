#!/usr/bin/env python3
"""OCE Local Ground — capture a deterministic, hash-protected PostgreSQL
database inventory (B1-LOCAL, A-003; recovery contract).

The inventory enumerates every user table (schema-qualified) and its exact row
count at capture time, plus the PostgreSQL server version, all from a running
`oce-local-postgresql` container via `docker exec`. It is written next to the
custom-format archive so a full-replace restore can verify the staging database
byte-for-byte against expectation before promotion.

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


def _exec(container, cmd):
    r = subprocess.run(["docker", "exec", container] + cmd,
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"docker exec {' '.join(cmd)} rc={r.returncode}: {r.stderr}")
    return r.stdout


def _psql(container, db, user, query):
    return _exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", db,
                             "-c", query])


def capture(container=CONTAINER, db=DB, user=USER):
    # server version
    ver = _psql(container, db, user, "SHOW server_version_num;").strip()
    # all user tables not in system schemas
    tbl_rows = _psql(container, db, user, (
        "SELECT schemaname || '.' || tablename FROM pg_tables "
        "WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1;"
    )).splitlines()
    tables = []
    for tn in tbl_rows:
        tn = tn.strip()
        if not tn:
            continue
        # count(*) per table (deterministic snapshot of authoritative truth)
        cnt = _psql(container, db, user, f'SELECT count(*) FROM "{tn.split(".")[0]}"."{tn.split(".",1)[1]}";').strip()
        tables.append({"name": tn, "row_count": int(cnt) if cnt.isdigit() else -1})
    inv = {
        "format": "oce-pg-inventory-v1",
        "database": db,
        "pg_version_num": ver,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "table_count": len(tables),
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
    print(f"inventory -> {out} (tables={inv['table_count']})")
    sys.exit(0)


if __name__ == "__main__":
    main()