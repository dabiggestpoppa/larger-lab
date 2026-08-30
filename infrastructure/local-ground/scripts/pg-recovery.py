#!/usr/bin/env python3
"""OCE Local Ground — phase-safe PostgreSQL recovery with verified rollback
(B1-LOCAL, A-003; recovery contract, R25).

Full-replace PostgreSQL recovery runs as an EXPLICIT state machine with three
operable phases. The quarantine database (the only rollback source) is held
until EVERY fallible verification has passed:

  --phase promote   archive validated -> inventory validated -> staging
                    created -> archive restored into staging -> staging truth
                    verified -> canonical renamed to quarantine -> staging
                    renamed to canonical (promoted) -> canonical truth
                    verified. Quarantine is HELD (never dropped).
  --phase finalize  canonical truth RE-verified (fallible) -> quarantine
                    dropped -> quarantine-removal verified -> final receipt.
                    If the re-verification fails, the ORIGINAL canonical is
                    rolled back from quarantine and verified.
  --phase rollback  explicit rollback: promoted candidate removed, original
                    quarantine database restored to the canonical name,
                    rolled-back truth verified. Nonzero when rollback cannot
                    restore the original (e.g. quarantine missing).

Rollback is driven by the actual phase/state (was the canonical renamed?)
never by the inverse of `promoted`. Existence checks are performed through
the pg_database catalog before any ALTER/DROP DATABASE — `ALTER DATABASE
IF EXISTS` (invalid PostgreSQL) never appears.

Redis is never touched by this engine; transient-cache invalidation is the
caller's (restore.sh) step and happens only AFTER PostgreSQL recovery is
irreversible.

Receipt fields include rollback_required / rollback_attempted /
rollback_succeeded / rollback_failed / original_canonical_restored /
promoted_candidate_removed / quarantine_retained / rollback_verification /
final_exit_status. Any failed or unverified rollback returns nonzero.

Usage:
  pg-recovery.py --phase promote --archive <dump> --inventory <inv.json>
                 --inventory-sha <inv.sha256> [--db oce_local]
                 [--user oce_local_admin] [--container oce-local-postgresql]
                 [--verify-tables "t=count;t2=count"] [--receipt-out <file>]
  pg-recovery.py --phase finalize --receipt-in <promote-receipt.json>
                 --inventory <inv.json> --inventory-sha <inv.sha256>
                 [--db] [--user] [--container] [--receipt-out <file>]
  pg-recovery.py --phase rollback --receipt-in <promote-receipt.json>
                 --inventory <inv.json> --inventory-sha <inv.sha256>
                 [--db] [--user] [--container] [--receipt-out <file>]
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

PHASES_PROMOTE = [
    "inventory_validated",
    "archive_validated",
    "staging_created",
    "staging_restored",
    "staging_verified",
    "canonical_quarantined",
    "promoted",
    "canonical_verified",
]
PHASES_FINALIZE = [
    "final_canonical_verified",
    "quarantine_dropped",
    "quarantine_removal_verified",
]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def recovery_succeeded(receipt):
    """A recovery receipt reports success ONLY when the exit status is zero
    and no rollback is outstanding or failed. A green exit can never override
    a failed recovery invariant."""
    if receipt.get("exit_status") != 0:
        return False
    if receipt.get("rollback_failed"):
        return False
    if receipt.get("rollback_required"):
        return receipt.get("rollback_succeeded") is True
    return True


def rollback_truthful(receipt):
    """A rollback is truthful only when it was actually attempted and either
    fully succeeded (original restored + verification ok) or is truthfully
    reported as failed (e.g. missing quarantine). A rollback that was never
    attempted, or claims success without restoring the original, is a lie."""
    if receipt.get("rollback_required") is not True:
        return True
    if receipt.get("rollback_attempted") is not True:
        return False
    if receipt.get("rollback_succeeded") is True:
        return (receipt.get("original_canonical_restored") is True
                and (receipt.get("rollback_verification") or {}).get("result") == "ok")
    return receipt.get("rollback_failed") is True


def valid_phase_prefix(phases, canon):
    """True when `phases` is a non-empty prefix (in canonical order) of the
    given state machine. Receipts must never claim phases out of order or
    invent phases."""
    if not phases or len(phases) > len(canon):
        return False
    return all(g == w for g, w in zip(phases, canon))


def docker_exec(container, cmd, stdin_bytes=None, timeout=600):
    r = subprocess.run(["docker", "exec", "-i", container] + cmd,
                       input=stdin_bytes, capture_output=True, timeout=timeout)
    return r


def docker_exec_ok(container, cmd, stdin_bytes=None, timeout=600):
    r = docker_exec(container, cmd, stdin_bytes, timeout)
    if r.returncode != 0:
        raise RuntimeError(f"docker exec {' '.join(cmd)} rc={r.returncode}: "
                           + r.stderr.decode(errors="replace"))
    return r


def psql(container, db, user, sql, stdin_bytes=None):
    return docker_exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", db,
                                   "-c", sql], stdin_bytes=stdin_bytes)


def psql_ok(container, db, user, sql, stdin_bytes=None, timeout=600):
    r = psql(container, db, user, sql, stdin_bytes=stdin_bytes)
    if r.returncode != 0:
        raise RuntimeError(f"psql {db} rc={r.returncode}: "
                           + r.stderr.decode(errors="replace"))
    return r


# ── pure helpers (unit-testable without Docker) ──────────────────────────
def parse_inventory(inv_json):
    inv = json.loads(inv_json)
    assert inv.get("format") == "oce-pg-inventory-v1", inv.get("format")
    tbl = {}
    for t in inv.get("tables", []):
        tbl[t["name"]] = {
            "row_count": t.get("row_count"),
            "fingerprint": t.get("fingerprint"),
        }
    return {"database": inv.get("database"), "table_count": inv.get("table_count"),
            "tables": tbl,
            "fingerprint_algorithm": inv.get("fingerprint_algorithm"),
            "fingerprinted_tables": inv.get("fingerprinted_tables")}


def capture_inventory_rows(inventory):
    """Return {schema-qualified table: row_count} from a parsed inventory."""
    return {name: info["row_count"] for name, info in inventory["tables"].items()}


def capture_inventory_fingerprints(inventory):
    """Return {schema-qualified table: fingerprint} (only fingerprinted ones)."""
    return {name: info["fingerprint"] for name, info in inventory["tables"].items()
            if info.get("fingerprint") is not None}


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


def verify_inventory(inventory, observed_rows, probe_rows=None, observed_fingerprints=None):
    """Verify observed rows (and, when the protected inventory carries
    fingerprints, observed fingerprints) against a parsed inventory plus
    optional explicit recovery probes.

    Fingerprints are MANDATORY when the inventory carries them: a row-count
    only observation is not content proof (different data can have identical
    counts) and is rejected as `missing fingerprint evidence`. Returns
    (ok, list_of_problem_msgs).
    """
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
    # Content (fingerprint) verification: the protected inventory proves exact
    # values. If the inventory records fingerprints, observations MUST carry
    # matching fingerprints or verification fails closed.
    exp_fps = capture_inventory_fingerprints(inventory)
    if exp_fps:
        if observed_fingerprints is None:
            problems.append("missing fingerprint evidence (row counts alone cannot "
                            "prove protected values)")
        else:
            for tbl, want in exp_fps.items():
                got = observed_fingerprints.get(tbl)
                if got is None or got == "-err-":
                    problems.append(f"missing fingerprint for {tbl}")
                elif got != want:
                    problems.append(f"value fingerprint mismatch {tbl}: expected "
                                    f"{want[:16]}… got {got[:16]}…")
    return (len(problems) == 0), problems


def collect_observed_rows(container, db, user, tables):
    """Query exact row counts of each table directly via psql (docker-backed)."""
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


def fingerprint_sql(schema, rel):
    """Deterministic content fingerprint for a table: md5 over the sorted
    canonical row-JSON serialization. Identical content -> identical
    fingerprint; any value change -> different fingerprint."""
    return ('SELECT md5(COALESCE(string_agg(r, E\'\\n\' ORDER BY r), \'\')) '
            'FROM (SELECT row_to_json(t)::text AS r FROM "%s"."%s" t) sub;' % (schema, rel))


def collect_observed_fingerprints(container, db, user, tables):
    """Compute the deterministic content fingerprint of each table."""
    observed = {}
    for name in tables:
        schema, _, rel = name.partition(".")
        r = psql(container, db, user, fingerprint_sql(schema, rel))
        if r.returncode != 0:
            observed[name] = "-err-"
        else:
            observed[name] = r.stdout.strip()
    return observed


def _observed_payload(inventory, probe, observed_rows, observed_fps=None):
    """Collapse observed rows/fingerprints into a compact dict for receipts."""
    wanted = sorted(set(capture_inventory_rows(inventory)) | set(probe or {}))
    payload = {"tables": {t: observed_rows.get(t) for t in wanted}}
    if observed_fps is not None:
        payload["fingerprints"] = {t: observed_fps.get(t) for t in wanted}
    return payload


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ── docker-backed catalog / database operations (R25) ────────────────────
def _catalog_names(container, user):
    """Exact set of database names via the pg_database catalog. Existence is
    never guessed; every ALTER/DROP DATABASE follows a catalog check."""
    r = docker_exec(container, ["psql", "-X", "-A", "-t", "-U", user, "-d", "postgres",
                                "-c", "SELECT datname FROM pg_database;"])
    if r.returncode != 0:
        raise RuntimeError("cannot read pg_database catalog: "
                           + r.stderr.decode(errors="replace"))
    return {ln.strip() for ln in r.stdout.decode(errors="replace").splitlines() if ln.strip()}


def db_exists(container, user, name):
    return name in _catalog_names(container, user)


def drop_db(container, user, name):
    """Drop a database ONLY after an explicit catalog existence check."""
    if not db_exists(container, user, name):
        raise RuntimeError(f"cannot drop unknown database '{name}' (catalog check failed)")
    docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", "postgres", "-c",
                               f'DROP DATABASE "{name}" WITH (FORCE);'], timeout=120)


def rename_db(container, user, from_name, to_name):
    """Rename a database only after catalog checks: source exists, target free."""
    names = _catalog_names(container, user)
    if from_name not in names:
        raise RuntimeError(f"cannot rename missing database '{from_name}' (catalog check failed)")
    if to_name in names:
        raise RuntimeError(f"cannot rename '{from_name}' to existing database '{to_name}' "
                           "(catalog check failed)")
    docker_exec_ok(container, ["psql", "-X", "-U", user, "-d", "postgres", "-c",
                               f'ALTER DATABASE "{from_name}" RENAME TO "{to_name}";'])


def create_staging_db(container, user, base_db, stamp):
    name = f"oce_local_restore_{stamp}"
    psql_ok(container, base_db, user,
            f'CREATE DATABASE "{name}" OWNER "{user}";')
    return name


def terminate_local_connections(container, user, *dbs):
    for db in dbs:
        psql_ok(container, db, user,
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid();")


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


def _base_receipt(kind, db, container, inventory_path):
    return {"format": "oce-pg-recovery-receipt-v1",
            "operation_phase": kind,
            "database": db, "source_database": db, "target_database": db,
            "source_commit": os.environ.get("OCE_COMMIT", "unknown"),
            "source_tree": os.environ.get("OCE_TREE", "unknown"),
            "run_id": os.environ.get("OCE_RUN_ID", "not-set"),
            "inventory_path": inventory_path,
            "phases": [],
            "started_at": now_iso()}


def _atomic_write_json(path, data):
    """Commit a receipt atomically (tmp + rename) so a partial write can never
    be read as truth."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _load_receipt(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_protected_inventory(inventory_path, inventory_sha_path):
    """Load and hash-verify the protected inventory (fail closed on tamper)."""
    inv_doc = open(inventory_path, encoding="utf-8").read()
    inv_sha = open(inventory_sha_path, encoding="utf-8").read().strip()
    if hashlib.sha256(inv_doc.encode()).hexdigest() != inv_sha:
        raise RuntimeError("database inventory tampered (SHA mismatch)")
    return parse_inventory(inv_doc)


def _verify_db(container, db, user, inventory, probe, label):
    """Row counts + protected fingerprints of one database. Returns
    (ok, problems, rows, fps)."""
    watch = sorted(set(capture_inventory_rows(inventory)) | set(probe))
    rows = collect_observed_rows(container, db, user, watch)
    fps = None
    if capture_inventory_fingerprints(inventory):
        fps = collect_observed_fingerprints(container, db, user, watch)
    ok, problems = verify_inventory(inventory, rows, probe, fps)
    return ok, problems, rows, fps


def rollback_recovery(container, user, db, quarantine, inventory, probe):
    """Restore the pre-promotion canonical truth from quarantine and verify it.
    Returns (ok, problems, detail). Never raises for reportable rollback
    outcomes; a rollback that cannot restore the original returns ok=False."""
    detail = {"rollback_attempted": True, "rollback_succeeded": False,
              "rollback_failed": False, "original_canonical_restored": False,
              "promoted_candidate_removed": False, "quarantine_retained": False}
    problems = []
    try:
        names = _catalog_names(container, user)
        # terminate connections only to databases that actually exist
        live = [d for d in (db, quarantine) if d in names]
        if live:
            terminate_local_connections(container, user, *live)
        q_exists = quarantine in names
        candidate_exists = db in names
        if not q_exists:
            problems.append("quarantine database missing — original truth unavailable")
            detail["rollback_failed"] = True
            detail["quarantine_retained"] = False
            return False, problems, detail
        # remove the promoted candidate FIRST (it occupies the canonical name),
        # then rename the original quarantine database back to canonical.
        if candidate_exists:
            drop_db(container, user, db)
            detail["promoted_candidate_removed"] = True
        rename_db(container, user, quarantine, db)
        detail["original_canonical_restored"] = True
        ok, vprobs, rows, fps = _verify_db(container, db, user, inventory, probe,
                                           "rollback")
        detail["rollback_verification"] = {"result": "ok" if ok else "failed"}
        if fps is not None:
            detail["rollback_verification"]["fingerprints"] = fps
        detail["rollback_verification"]["tables"] = rows
        if not ok:
            problems.extend(vprobs)
            detail["rollback_failed"] = True
            return False, problems, detail
        detail["rollback_succeeded"] = True
        detail["rollback_failed"] = False
        return True, problems, detail
    except Exception as e:  # an exception IS a failed rollback
        problems.append(f"rollback raised: {e}")
        detail["rollback_failed"] = True
        detail["rollback_error"] = str(e)
        return False, problems, detail


# ── phase: promote ───────────────────────────────────────────────────────
def phase_promote(archive, inventory_path, inventory_sha_path, db, user,
                  container, probe_spec):
    receipt = _base_receipt("promote", db, container, inventory_path)
    stamp = hashlib.sha256(os.urandom(8)).hexdigest()[:12]
    quarantine = f"oce_local_quarantine_{stamp}"
    receipt["stamp"] = stamp
    receipt["quarantine_database"] = quarantine
    receipt["quarantine_held"] = True
    receipt["quarantine_dropped"] = False
    receipt["promoted"] = False
    staging = None
    quarantined = False
    remote = None
    try:
        # 1. protected inventory validated (hash + parse + non-empty truth)
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        receipt["inventory_sha256"] = open(inventory_sha_path, encoding="utf-8").read().strip()
        probe = parse_probe_spec(probe_spec)
        if not (capture_inventory_rows(inventory) or probe):
            raise RuntimeError("database inventory lists no tables to verify (incomplete backup)")
        receipt["phases"].append("inventory_validated")
        # 2. archive validated + hashed
        receipt["source_archive_sha256"] = sha256_file(archive)
        remote = clone_archive_into_container(container, archive)
        validate_archive(container, remote)
        receipt["archive_validated"] = True
        receipt["phases"].append("archive_validated")
        # postgres version
        ver = psql(container, db, user, "SHOW server_version;")
        receipt["postgres_version"] = (ver.stdout.decode(errors="replace").strip()
                                       if ver.returncode == 0 else "")
        # 3. staging created
        staging = create_staging_db(container, user, db, stamp)
        receipt["staging_database"] = staging
        receipt["phases"].append("staging_created")
        # 4. restore into staging with exit-on-error
        with open(archive, "rb") as f:
            data = f.read()
        r = docker_exec(container, ["pg_restore", "-U", user, "--exit-on-error",
                                    "--no-owner", "--no-privileges", "--dbname", staging, remote],
                        stdin_bytes=data, timeout=1800)
        if r.returncode != 0:
            raise RuntimeError("pg_restore into staging failed: "
                               + r.stderr.decode(errors="replace"))
        receipt["phases"].append("staging_restored")
        # 5. staging truth verified (counts + protected fingerprints)
        ok, problems, rows, fps = _verify_db(container, staging, user, inventory, probe, "staging")
        receipt["staging_verification"] = {"result": "ok" if ok else "failed",
                                           "tables": rows}
        if fps is not None:
            receipt["staging_verification"]["fingerprints"] = fps
        if not ok:
            raise RuntimeError("staging verification FAILED: " + "; ".join(problems))
        receipt["phases"].append("staging_verified")
        # 6. terminate ONLY local canonical-target connections
        terminate_local_connections(container, user, db)
        # 7. canonical -> quarantine (catalog-checked rename)
        rename_db(container, user, db, quarantine)
        quarantined = True
        receipt["phases"].append("canonical_quarantined")
        # 8. staging -> canonical (promoted)
        rename_db(container, user, staging, db)
        receipt["promoted"] = True
        receipt["promotion"] = "ok"
        receipt["phases"].append("promoted")
        # 9. canonical truth verified (counts + fingerprints) — quarantine held
        ok2, problems2, rows2, fps2 = _verify_db(container, db, user, inventory, probe, "canonical")
        receipt["canonical_verification"] = {"result": "ok" if ok2 else "failed",
                                             "tables": rows2}
        if fps2 is not None:
            receipt["canonical_verification"]["fingerprints"] = fps2
        if not ok2:
            raise RuntimeError("canonical target verification FAILED after promote: "
                               + "; ".join(problems2))
        receipt["phases"].append("canonical_verified")
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 0
        receipt["redis_restored"] = False
        return receipt
    except Exception as e:
        receipt["error"] = str(e)
        if quarantined:
            # Failure after canonical->quarantine began: ROLL BACK now. The
            # rollback source (quarantine) is still present by construction.
            ok_rb, rb_problems, rb_detail = rollback_recovery(
                container, user, db, quarantine, inventory, probe)
            receipt["rollback_required"] = True
            receipt.update(rb_detail)
            if not ok_rb:
                receipt["rollback_error"] = "; ".join(rb_problems)
        else:
            # Failure before canonical rename: canonical untouched; just remove
            # the staging half-construction (if any).
            receipt["rollback_required"] = False
            if staging and db_exists(container, user, staging):
                try:
                    drop_db(container, user, staging)
                except Exception as e2:
                    receipt["staging_cleanup_error"] = str(e2)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt


# ── phase: finalize ──────────────────────────────────────────────────────
def phase_finalize(receipt_in_path, inventory_path, inventory_sha_path, db,
                   user, container, probe_spec):
    promote = _load_receipt(receipt_in_path)
    if promote.get("operation_phase") != "promote" or promote.get("promoted") is not True:
        raise RuntimeError("finalize requires a successful promote receipt "
                           f"(got phase={promote.get('operation_phase')})")
    quarantine = promote.get("quarantine_database")
    if not quarantine:
        raise RuntimeError("promote receipt lacks quarantine_database")
    receipt = _base_receipt("finalize", db, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    receipt["stamp"] = promote.get("stamp")
    receipt["staging_database"] = promote.get("staging_database")
    receipt["quarantine_database"] = quarantine
    receipt["source_archive_sha256"] = promote.get("source_archive_sha256")
    receipt["promoted"] = True
    receipt["rollback_required"] = False
    receipt["rollback_attempted"] = False
    receipt["rollback_succeeded"] = None
    receipt["rollback_failed"] = False
    receipt["original_canonical_restored"] = False
    receipt["promoted_candidate_removed"] = False
    receipt["quarantine_retained"] = False
    inventory = None
    probe = {}
    try:
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        probe = parse_probe_spec(probe_spec)
        # 1. FINAL canonical truth re-verified while quarantine still exists
        # (never run a fallible verification after removing the rollback source)
        ok, problems, rows, fps = _verify_db(container, db, user, inventory, probe, "final")
        receipt["final_verification"] = {"result": "ok" if ok else "failed",
                                         "tables": rows}
        if fps is not None:
            receipt["final_verification"]["fingerprints"] = fps
        if not ok:
            raise RuntimeError("final canonical verification FAILED (quarantine "
                               "held; rolling back): " + "; ".join(problems))
        receipt["phases"].append("final_canonical_verified")
        # 2. quarantine dropped (catalog check + verified removal)
        drop_db(container, user, quarantine)
        receipt["quarantine_dropped"] = True
        receipt["phases"].append("quarantine_dropped")
        if db_exists(container, user, quarantine):
            raise RuntimeError("quarantine database still present after DROP")
        receipt["quarantine_removal_verified"] = True
        receipt["phases"].append("quarantine_removal_verified")
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 0
        receipt["redis_restored"] = False
        return receipt
    except Exception as e:
        receipt["error"] = str(e)
        if receipt.get("quarantine_dropped") is not True:
            # Fallible verification failed before quarantine removal: ROLL BACK.
            receipt["rollback_required"] = True
            if inventory is None:
                # Without the protected inventory the rollback cannot be
                # VERIFIED: fail loudly, never claim restoration succeeded.
                receipt["rollback_attempted"] = True
                receipt["rollback_succeeded"] = False
                receipt["rollback_failed"] = True
                receipt["original_canonical_restored"] = False
                receipt["rollback_error"] = (f"cannot verify rollback: inventory unavailable ({e})")
            else:
                try:
                    ok_rb, rb_problems, rb_detail = rollback_recovery(
                        container, user, db, quarantine, inventory, probe)
                    receipt["rollback_attempted"] = True
                    receipt.update(rb_detail)
                    if not ok_rb:
                        receipt["rollback_error"] = "; ".join(rb_problems)
                except Exception as e2:
                    receipt["rollback_attempted"] = True
                    receipt["rollback_succeeded"] = False
                    receipt["rollback_failed"] = True
                    receipt["rollback_error"] = f"rollback raised: {e2}"
        else:
            # Quarantine already dropped; data is promoted+verified. This is a
            # cleanup/evidence failure, not a data failure — still nonzero.
            receipt["quarantine_retained"] = False
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt


# ── phase: rollback (explicit) ───────────────────────────────────────────
def phase_rollback(receipt_in_path, inventory_path, inventory_sha_path, db,
                   user, container, probe_spec):
    promote = _load_receipt(receipt_in_path)
    quarantine = promote.get("quarantine_database")
    if not quarantine:
        raise RuntimeError("rollback requires a promote receipt with quarantine_database")
    receipt = _base_receipt("rollback", db, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    receipt["stamp"] = promote.get("stamp")
    receipt["quarantine_database"] = quarantine
    receipt["rollback_required"] = True
    inventory = None
    probe = {}
    try:
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        probe = parse_probe_spec(probe_spec)
        ok, problems, detail = rollback_recovery(container, user, db, quarantine,
                                                 inventory, probe)
        receipt.update(detail)
        if not ok:
            receipt["rollback_error"] = "; ".join(problems)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 0 if ok else 1
        return receipt
    except Exception as e:
        receipt["rollback_attempted"] = True
        receipt["rollback_succeeded"] = False
        receipt["rollback_failed"] = True
        receipt["original_canonical_restored"] = False
        receipt["rollback_error"] = str(e)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt


def main():
    args = sys.argv[1:]
    kw = {}
    phase = None
    probe = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--phase", "--archive", "--inventory", "--inventory-sha", "--db",
                 "--user", "--container", "--receipt-out", "--receipt-in",
                 "--verify-tables"):
            i += 1
            val = args[i] if i < len(args) else None
            if a == "--phase":
                phase = val
            elif a == "--verify-tables":
                probe = val
            else:
                kw[a[2:].replace("-", "_")] = val
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            sys.exit(2)
        i += 1
    if phase not in ("promote", "finalize", "rollback"):
        print("USAGE_ERROR: --phase <promote|finalize|rollback> required", file=sys.stderr)
        sys.exit(2)
    if not kw.get("inventory") or not kw.get("inventory_sha"):
        print("USAGE_ERROR: --inventory and --inventory-sha required", file=sys.stderr)
        sys.exit(2)
    if phase == "promote" and not kw.get("archive"):
        print("USAGE_ERROR: --phase promote requires --archive", file=sys.stderr)
        sys.exit(2)
    if phase in ("finalize", "rollback") and not kw.get("receipt_in"):
        print(f"USAGE_ERROR: --phase {phase} requires --receipt-in", file=sys.stderr)
        sys.exit(2)
    db = kw.get("db", DB)
    user = kw.get("user", USER)
    container = kw.get("container", CONTAINER)
    if phase == "promote":
        receipt = phase_promote(kw["archive"], kw["inventory"], kw["inventory_sha"],
                                db, user, container, probe)
    elif phase == "finalize":
        receipt = phase_finalize(kw["receipt_in"], kw["inventory"], kw["inventory_sha"],
                                 db, user, container, probe)
    else:
        receipt = phase_rollback(kw["receipt_in"], kw["inventory"], kw["inventory_sha"],
                                 db, user, container, probe)
    out = kw.get("receipt_out")
    if out:
        _atomic_write_json(out, receipt)
        print("receipt ->", out)
    if receipt.get("exit_status") != 0:
        print("BLOCKED:", receipt.get("error", f"postgres {phase} failed"),
              file=sys.stderr)
        sys.exit(1)
    print(f"postgres {phase} complete")


if __name__ == "__main__":
    main()
