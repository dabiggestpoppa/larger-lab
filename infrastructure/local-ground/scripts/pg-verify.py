#!/usr/bin/env python3
"""OCE Local Ground — independent restore-boundary PostgreSQL verifier
(B1-LOCAL, A-003; recovery contract, R26).

Re-checks the canonical database against the hash-protected inventory: exact
row counts AND deterministic value fingerprints. Row counts alone are not
content proof; the fingerprints prove exact protected values. Used by
restore.sh BETWEEN promote and finalize (quarantine is still held) and by the
independent gate as an external, fresh, durable verification.

Usage:
  pg-verify.py --inventory <inventory.json> --inventory-sha <inventory.json.sha256>
               [--db oce_local] [--user oce_local_admin]
               [--container oce-local-postgresql] [--stable 2]

Exits 0 only when the canonical target matches the protected inventory for
`stable` consecutive polls. Any mismatch, missing table, tampered inventory,
or query failure exits nonzero (fail closed).
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location("pg_recovery",
                                               os.path.join(_HERE, "pg-recovery.py"))
_PG = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PG)

CONTAINER = _PG.CONTAINER
DB = _PG.DB
USER = _PG.USER


def load_protected_inventory(inventory_path, inventory_sha_path):
    inv_doc = open(inventory_path, encoding="utf-8").read()
    inv_sha = open(inventory_sha_path, encoding="utf-8").read().strip()
    if hashlib.sha256(inv_doc.encode()).hexdigest() != inv_sha:
        raise RuntimeError("database inventory tampered (SHA mismatch)")
    inv = _PG.parse_inventory(inv_doc)
    if not _PG.capture_inventory_rows(inv):
        raise RuntimeError("inventory lists no tables (cannot prove any row)")
    return inv


def verify_canonical(container, db, user, inv):
    """One full verification pass of the canonical target. Returns (ok, msgs)."""
    watch = sorted(_PG.capture_inventory_rows(inv))
    rows = _PG.collect_observed_rows(container, db, user, watch)
    fps = _PG.collect_observed_fingerprints(container, db, user, watch)
    ok, problems = _PG.verify_inventory(inv, rows, None, fps)
    return ok, problems


def main():
    args = sys.argv[1:]
    kw = {}
    stable = 2
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--inventory", "--inventory-sha", "--db", "--user", "--container"):
            i += 1
            kw[a[2:].replace("-", "_")] = args[i] if i < len(args) else None
        elif a == "--stable":
            i += 1
            stable = int(args[i]) if i < len(args) else 2
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            sys.exit(2)
        i += 1
    if not kw.get("inventory") or not kw.get("inventory_sha"):
        print("USAGE_ERROR: --inventory and --inventory-sha required", file=sys.stderr)
        sys.exit(2)
    db = kw.get("db", DB)
    user = kw.get("user", USER)
    container = kw.get("container", CONTAINER)
    try:
        inv = load_protected_inventory(kw["inventory"], kw["inventory_sha"])
    except Exception as e:
        print(f"UNVERIFIED: {e}", file=sys.stderr)
        sys.exit(1)
    streak = 0
    problems = ["no verification pass completed"]
    for attempt in range(1, max(stable, 2) * 3 + 1):
        try:
            ok, problems = verify_canonical(container, db, user, inv)
        except Exception as e:  # docker/psql unavailable or broken -> UNVERIFIED
            ok = False
            problems = [f"verification pass raised: {e}"]
        if ok:
            streak += 1
            if streak >= stable:
                print(f"CANONICAL_VERIFIED (stable x{streak}) tables={len(inv['tables'])}")
                sys.exit(0)
        else:
            streak = 0
            print(f"attempt {attempt}: not yet verified: {'; '.join(problems)}", file=sys.stderr)
        time.sleep(2)
    print("UNVERIFIED: " + "; ".join(problems), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
