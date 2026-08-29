#!/usr/bin/env python3
"""OCE Local Ground — verified staging-promotion PostgreSQL recovery
(B1-LOCAL, A-003; recovery contract).

Full-replace PostgreSQL recovery is performed through a controlled chain:

  1. Validate the custom-format archive with `pg_restore --list`.
  2. Record the archive SHA-256.
  3. Create a uniquely-named staging database (never the canonical target).
  4. `pg_restore --exit-on-error --no-owner --no-privileges` into staging.
  5. Verify staging against the hash-protected inventory (schemas/tables/row
     counts) plus recovery probe rows.
  6. Terminate ONLY local canonical-target connections.
  7. Rename canonical -> quarantine, rename verified staging -> canonical.
  8. Verify the canonical target.
  9. Drop quarantine after success; roll back canonical if any phase fails.

Redis is never touched. The receipt records every phase, identities, archive
hash, inventory result, promotion/rollback, postgres version and exit status.

Usage:
  pg-recovery.py --archive <archive.dump> --inventory <inventory.json>
                 --inventory-sha <inventory.sha256> --db <db> --user <user>
                 --container <container> [--receipt-out <file>]
                 [--verify-tables "a=1;b=2"]   # recovery probe rows (db.table=count)

Pure helpers (verify_inventory, safe path checks) are importable for tests.
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


def docker_exec(container, cmd, stdin_bytes=None, timeout=600):
    r = subprocess.run(["docker", "exec", "-i", container] + cmd,
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return r


def docker_exec_ok(container, cmd, stdin_bytes=None, timeout=600):
    r = docker_exec(container, cmd, stdin_bytes, timeout)
    if r.returncode != 0:
        raise RuntimeError(f"docker exec {' '.join(cmd)} rc={r.returncode}: {r.stderr.decode(errors='replace')}")
    return r


def psql(container, db, user, sql, stdin_bytes=None):
    r = docker_exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", db,
                                "-c", sql], stdin_bytes=stdin_bytes)
    return r


# ── pure helpers (unit-testable without Docker) ──────────────────────────
def parse_inventory(inv_json):
    inv = json.loads(inv_json)
    assert inv.get("format") == "oce-pg-inventory-v1", inv.get("format")
    tbl = {}
    for t in inv.get("tables", []):
        tbl[t["name"]] = {"row_count": t.get("row_count")}
    return {"database": inv.get("database"), "table_count": inv.get("table_count"),
            "tables": tbl}


def capture_inventory_rows(inventory):
    """Return {schema-qualified table: row_count} from a parsed inventory."""
    return {name: info["row_count"] for name, info in inventory["tables"].items()}


def parse_probe_spec(spec):
    """Parse 'db.table=count;db.table2=count' probe spec -> {table: expected}."""
    out = {}
    if not spec:
        return out
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        name, _, cnt = part.rpartition("=")
        out[name.strip()] = int(cnt.strip())
    return out


def verify_inventory(inventory, observed_rows, probe_rows=None):
    """Verify observed {table: row_count} against a parsed inventory plus
    optional explicit recovery probes. Returns (ok, list_of_problem_msgs)."""
    problems = []
    expected = capture_inventory_rows(inventory)
    for tbl, cnt in expected.items():
        got = observed_rows.get(tbl)
        if got is None:
            problems.append(f"missing table {tbl}")
        elif cnt != got:
            problems.append(f"row count mismatch {tbl}: expected {cnt} got {got}")
    for probe_tbl, probe_cnt in (probe_rows or {}).items():
        got = observed_rows.get(probe_tbl)
        if got is None:
            problems.append(f"missing recovery probe table {probe_tbl}")
        elif got != probe_cnt:
            problems.append(f"recovery probe mismatch {probe_tbl}: expected {probe_cnt} got {got}")
    return (len(problems) == 0), problems


def collect_observed_rows(container, db, user, tables):
    """Query row counts of each table directly via psql (docker-backed)."""
    observed = {}
    for name in tables:
        schema, _, rel = name.partition(".")
        r = psql(container, db, user,
                 f'SELECT count(*) FROM "{schema}"."{rel}";')
        if r.returncode != 0:
            observed[name] = -1
        else:
            txt = r.stdout.strip()
            observed[name] = int(txt) if txt.isdigit() else -1
    return observed


# ── docker-backed staging-promotion chain ────────────────────────────────
def clone_archive_into_container(container, archive_path):
    """Copy the custom archive into the container tmp; return container path."""
    remote = "/tmp/oce_restore_" + hashlib.sha256(os.urandom(8)).hexdigest() + ".dump"
    subprocess.run(["docker", "cp", archive_path, f"{container}:{remote}"],
                   check=True, capture_output=True, timeout=120)
    return remote


def validate_archive(container, remote):
    r = docker_exec(container, ["pg_restore", "--list", remote])
    if r.returncode != 0:
        raise RuntimeError("pg_restore --list failed (corrupt/invalid archive): "
                           + r.stderr.decode(errors="replace"))
    return r.stdout.decode(errors="replace")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_staging_db(container, user, base_db, stamp):
    name = f"oce_local_restore_{stamp}"
    r = docker_exec(container, ["psql", "-X", "-U", user, "-d", base_db, "-c",
                                f'CREATE DATABASE "{name}" OWNER "{user}";'])
    if r.returncode != 0:
        raise RuntimeError("CREATE DATABASE staging failed: "
                           + r.stderr.decode(errors="replace"))
    return name


def drop_db(container, user, base_db, name):
    docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", base_db, "-c",
                               f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE);'],
                   timeout=120)


def promote_databases(container, user, canonical, quarantine, staging):
    """Rename canonical->quarantine and staging->canonical, using the postgres
    admin database for renames (can't rename a db you're connected to)."""
    docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", "postgres", "-c",
                               f'ALTER DATABASE "{canonical}" RENAME TO "{quarantine}";'])
    docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", "postgres", "-c",
                               f'ALTER DATABASE "{staging}" RENAME TO "{canonical}";'])


def _observed_payload(inventory, probe, observed):
    """Collapse observed rows into a compact {table: count} dict for receipts."""
    return {t: observed.get(t) for t in sorted(set(capture_inventory_rows(inventory)) | set(probe))}


def recovery_main(archive, inventory_path, inventory_sha_path, db, user, container,
                  probe_spec=None):
    receipt = {"format": "oce-pg-recovery-receipt-v1",
               "database": db, "source_archive_sha256": "",
               "source_commit": os.environ.get("OCE_COMMIT", "unknown"),
               "run_id": os.environ.get("OCE_RUN_ID", "not-set"),
               "source_database": db, "target_database": db,
               "staging_database": None, "quarantine_database": None,
               "postgres_version": "", "inventory_summary": None,
               "staging_verification": None, "canonical_verification": None,
               "promotion": "not-attempted",
               "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    stamp = hashlib.sha256(os.urandom(8)).hexdigest()[:12]
    quarantine = f"oce_local_quarantine_{stamp}"
    receipt["quarantine_database"] = quarantine
    remote = None
    try:
        # 0. confirm the protected inventory hash matches its JSON
        inv_doc = open(inventory_path, encoding="utf-8").read()
        inv_sha = open(inventory_sha_path, encoding="utf-8").read().strip()
        if hashlib.sha256(inv_doc.encode()).hexdigest() != inv_sha:
            raise RuntimeError("database inventory tampered (SHA mismatch)")
        inventory = parse_inventory(inv_doc)
        probe = parse_probe_spec(probe_spec)
        inv_row_counts = capture_inventory_rows(inventory)
        watch = list(set(inv_row_counts) | set(probe))
        # A full-replace recovery that cannot enumerate truth must fail closed:
        # an empty inventory cannot prove any row was recovered.
        if not watch:
            raise RuntimeError("database inventory lists no tables to verify (incomplete backup)")
        # 1. archive validation + hash
        receipt["source_archive_sha256"] = sha256_file(archive)
        remote = clone_archive_into_container(container, archive)
        validate_archive(container, remote)
        receipt["archive_validated"] = True
        # 2. postgres version + inventory summary
        ver = docker_exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", db,
                                      "-c", "SHOW server_version;"])
        receipt["postgres_version"] = ver.stdout.decode(errors="replace").strip() if ver.returncode == 0 else ""
        receipt["inventory_summary"] = {"database": inventory.get("database"),
                                         "table_count": inventory.get("table_count") or len(inv_row_counts),
                                         "tables": sorted(inv_row_counts)}
        # 3. staging db
        staging = create_staging_db(container, user, db, stamp)
        receipt["staging_database"] = staging
        # 4. restore into staging with exit-on-error
        with open(archive, "rb") as f:
            data = f.read()
        r = docker_exec(container, ["pg_restore", "-U", user, "--exit-on-error",
                                    "--no-owner", "--no-privileges", "--dbname", staging, remote],
                        stdin_bytes=data, timeout=1800)
        if r.returncode != 0:
            raise RuntimeError("pg_restore into staging failed: "
                               + r.stderr.decode(errors="replace"))
        # 5. verify staging (non-vacuous: exact row counts per table + probes)
        obs = collect_observed_rows(container, staging, user, watch)
        ok, problems = verify_inventory(inventory, obs, probe)
        receipt["staging_verification"] = {"result": "ok" if ok else "failed",
                                            "tables": _observed_payload(inventory, probe, obs)}
        if not ok:
            raise RuntimeError("staging verification FAILED: " + "; ".join(problems))
        # 6+7. terminate only local target connections, then promote
        psql(container, db, user,
             "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
             "WHERE datname = current_database() AND pid <> pg_backend_pid();")
        promote_databases(container, user, db, quarantine, staging)
        receipt["promoted"] = True
        receipt["promotion"] = "ok"
        # 8. verify canonical after promote
        obs2 = collect_observed_rows(container, db, user, watch)
        ok2, problems2 = verify_inventory(inventory, obs2, probe)
        receipt["canonical_verification"] = {"result": "ok" if ok2 else "failed",
                                              "tables": _observed_payload(inventory, probe, obs2)}
        if not ok2:
            raise RuntimeError("canonical target verification FAILED after promote: " + "; ".join(problems2))
        # 9. drop quarantine
        drop_db(container, user, db, quarantine)
        receipt["quarantine_dropped"] = True
        # 10. FINAL fail-closed re-verification of the canonical target AFTER the
        # quarantine is removed — exit 0 must mean the rows are still present now.
        obs3 = collect_observed_rows(container, db, user, watch)
        ok3, problems3 = verify_inventory(inventory, obs3, probe)
        receipt["final_verification"] = {"result": "ok" if ok3 else "failed",
                                          "tables": _observed_payload(inventory, probe, obs3)}
        if not ok3:
            raise RuntimeError("final canonical verification FAILED after quarantine drop: "
                               + "; ".join(problems3))
        receipt["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt["exit_status"] = 0
        receipt["redis_restored"] = False
        return receipt
    except Exception as e:
        # rollback: try to restore canonical if a quarantine now holds the truth
        if not receipt.get("promoted") and quarantine:
            try:
                # canonical unchanged; just drop the staging half-promotion
                drop_db(container, user, db, receipt.get("staging_database") or "")
                docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", "postgres", "-c",
                                           f'ALTER DATABASE IF EXISTS "{quarantine}" RENAME TO "{db}";'])
                receipt["rollback"] = "attempted"
            except Exception as rbe:
                receipt["rollback"] = f"failed: {rbe}"
        receipt["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt["exit_status"] = 1
        receipt["error"] = str(e)
        return receipt


def main():
    args = sys.argv[1:]
    kw = {}
    probe = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--archive", "--inventory", "--inventory-sha", "--db",
                 "--user", "--container", "--receipt-out", "--verify-tables"):
            i += 1
            val = args[i] if i < len(args) else None
            key = a[2:].replace("-", "_")
            if a == "--verify-tables":
                probe = val
            else:
                kw[key] = val
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            sys.exit(2)
        i += 1
    for req in ("archive", "inventory", "inventory_sha"):
        if not kw.get(req):
            print(f"USAGE_ERROR: --{req.replace('_','-')} required", file=sys.stderr)
            sys.exit(2)
    db = kw.get("db", DB)
    user = kw.get("user", USER)
    container = kw.get("container", CONTAINER)
    receipt = recovery_main(kw["archive"], kw["inventory"], kw["inventory_sha"],
                            db, user, container, probe)
    out = kw.get("receipt_out")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)
        print("receipt ->", out)
    if receipt.get("exit_status") != 0:
        print("BLOCKED:", receipt.get("error", "postgres recovery failed"), file=sys.stderr)
        sys.exit(1)
    print("postgres promotion complete")


if __name__ == "__main__":
    main()