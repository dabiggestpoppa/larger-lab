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

Recovery targets are GOVERNED (B4-CXR7U9R36/37): --db, --user and
--container are compatibility assertions that must equal the local identity
above - an alternate value is refused, so no CLI value can redirect a
destructive recovery. --receipt-out is data, not authority: it must name a
file inside this engine's recovery state directory (var/recovery, where
restore.sh stages its phase receipts), so a receipt can never overwrite
configuration, source, secrets or evidence outside that directory.

RECEIPT-WRITE AUTHORITY (B4-CXR7U9R37, hardened B4-CXR7U9R39-R2) is PROGRAM
IDENTITY: the directory is derived from where this engine file lives, so no
environment variable - including the former OCE_RECOVERY_STATE_DIR - can grant
write authority. An existing receipt is REFUSED, never silently replaced.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

CONTAINER = "oce-local-postgresql"
DB = "oce_local"
USER = "oce_local_admin"

# The destructive recovery destination is the GOVERNED local identity, and the
# engine's own transition names are derived from it, so those names have one
# owner: the constants above (B4-CXR7U9R36).
QUARANTINE_PREFIX = f"{DB}_quarantine_"
STAGING_PREFIX = f"{DB}_restore_"
RECEIPT_FORMAT = "oce-pg-recovery-receipt-v1"
TRANSITION_FORMAT = "oce-pg-recovery-transition-v1"
STAMP_RE = re.compile(r"[0-9a-f]{12}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
OPERATION_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
REVISION_RE = re.compile(r"[0-9a-f]{7,64}\Z")

# One durable recovery-operation state machine (B4-CXR7U9R39-R3, made
# operation-wide by R40-R1). PROMOTED is the ONLY state that still offers
# transition authority. ONE operation-wide claim (not one file per transition)
# selects the branch — exactly one of finalize or rollback can win it — and the
# selected transition is durably recorded, so the winner is attributable after
# a crash. States only ever move FORWARD along the ladder below; a record can
# never regress from FINALIZING/ROLLING_BACK to PROMOTED.
TRANSITION_STATE_PROMOTED = "PROMOTED"
TRANSITION_STATE_FINALIZING = "FINALIZING"
TRANSITION_STATE_ROLLING_BACK = "ROLLING_BACK"
TRANSITION_STATE_COMMIT_INTENT = "COMMIT_INTENT_RECORDED"
TRANSITION_STATE_COMMIT_POINT = "COMMIT_POINT_REACHED"
TRANSITIONS_ALLOWED_FROM_PROMOTED = ("finalize", "rollback")
# forward-only ladder: from -> states it may advance to. A same-state rewrite
# is allowed (idempotent); anything else not listed here is a regression and
# is refused.
_TRANSITION_LADDER = {
    "CREATED": {"STAGED", "FAILED"},
    "STAGED": {TRANSITION_STATE_PROMOTED, "FAILED"},
    TRANSITION_STATE_PROMOTED: {TRANSITION_STATE_FINALIZING,
                                TRANSITION_STATE_ROLLING_BACK},
    TRANSITION_STATE_FINALIZING: {TRANSITION_STATE_COMMIT_INTENT,
                                  "ROLLED_BACK", "FAILED"},
    TRANSITION_STATE_ROLLING_BACK: {"ROLLED_BACK", "FAILED"},
    TRANSITION_STATE_COMMIT_INTENT: {TRANSITION_STATE_COMMIT_POINT},
    TRANSITION_STATE_COMMIT_POINT: {"FINALIZED"},
    "FINALIZED": set(),
    "ROLLED_BACK": set(),
    "FAILED": set(),
}
_CLAIM_FORMAT = "oce-transition-claim-v1"

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


def psql_ok(container, db, user, sql, stdin_bytes=None):
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


def _verify_row_counts(inventory, observed_rows, problems):
    """Append row-count problems to *problems* (B4-CXR7U9R10 extraction)."""
    expected = capture_inventory_rows(inventory)
    for tbl, cnt in expected.items():
        got = observed_rows.get(tbl)
        if got is None:
            problems.append(f"missing table {tbl}")
        elif cnt != got:
            problems.append(f"row count mismatch {tbl}: expected {cnt} got {got}")


def _verify_probe_rows(observed_rows, probe_rows, problems):
    """Append recovery-probe problems to *problems* (extraction)."""
    for probe_tbl, probe_cnt in (probe_rows or {}).items():
        got = observed_rows.get(probe_tbl)
        if got is None:
            problems.append(f"missing recovery probe table {probe_tbl}")
        elif got != probe_cnt:
            problems.append(f"recovery probe mismatch {probe_tbl}: expected {probe_cnt} got {got}")


def _verify_fingerprints(inventory, observed_fingerprints, problems):
    """Append fingerprint-evidence problems to *problems* (extraction).

    Content (fingerprint) verification: the protected inventory proves exact
    values. If the inventory records fingerprints, observations MUST carry
    matching fingerprints or verification fails closed.
    """
    exp_fps = capture_inventory_fingerprints(inventory)
    if not exp_fps:
        return
    if observed_fingerprints is None:
        problems.append("missing fingerprint evidence (row counts alone cannot "
                        "prove protected values)")
        return
    for tbl, want in exp_fps.items():
        got = observed_fingerprints.get(tbl)
        if got is None or got == "-err-":
            problems.append(f"missing fingerprint for {tbl}")
        elif got != want:
            problems.append(f"value fingerprint mismatch {tbl}: expected "
                            f"{want[:16]}… got {got[:16]}…")


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
    _verify_row_counts(inventory, observed_rows, problems)
    _verify_probe_rows(observed_rows, probe_rows, problems)
    _verify_fingerprints(inventory, observed_fingerprints, problems)
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
            txt = r.stdout.decode(errors="replace").strip()
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
            observed[name] = r.stdout.decode(errors="replace").strip()
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
    name = STAGING_PREFIX + stamp
    psql_ok(container, base_db, user,
            f'CREATE DATABASE "{name}" OWNER "{user}";')
    return name


def terminate_local_connections(container, user, *dbs):
    for db in dbs:
        psql_ok(container, db, user,
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid();")


def clone_archive_into_container(container, archive_path):
    """Copy the custom archive into a directory the CONTAINER creates
    exclusively (mktemp -d, mode 0700) and return that path. Naming a path
    inside a shared temp directory would let anything else in the container
    pre-create it, so the copy could land on a chosen file or symlink.
    """
    made = docker_exec(container, ["mktemp", "-d"])
    remote_dir = made.stdout.decode(errors="replace").strip()
    if made.returncode != 0 or not remote_dir:
        raise RuntimeError("cannot create a private container temp directory: "
                           + made.stderr.decode(errors="replace"))
    remote = remote_dir + "/archive.dump"
    subprocess.run(["docker", "cp", archive_path, f"{container}:{remote}"],
                   check=True, capture_output=True, timeout=120)
    return remote


def validate_archive(container, remote):
    r = docker_exec(container, ["pg_restore", "--list", remote])
    if r.returncode != 0:
        raise RuntimeError("pg_restore --list failed (corrupt/invalid archive): "
                           + r.stderr.decode(errors="replace"))
    return r.stdout.decode(errors="replace")


def sha256_remote_file(container, remote):
    """SHA-256 of the file the CONTAINER holds at `remote` (R35). The restore
    reads that remote path, not this host's copy, so the bytes that are
    restored are the bytes this must be compared against the admitted source."""
    r = docker_exec(container, ["sha256sum", remote])
    if r.returncode != 0:
        raise RuntimeError("cannot hash the container copy of the archive: "
                           + r.stderr.decode(errors="replace"))
    fields = r.stdout.decode(errors="replace").split()
    digest = fields[0] if fields else ""
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise RuntimeError(f"container sha256sum returned no usable digest: {digest!r}")
    return digest


def _base_receipt(kind, db, user, container, inventory_path):
    return {"format": RECEIPT_FORMAT,
            "operation_phase": kind,
            "database": db, "source_database": db, "target_database": db,
            "user": user, "container": container,
            "source_commit": os.environ.get("OCE_COMMIT", "unknown"),
            "source_tree": os.environ.get("OCE_TREE", "unknown"),
            "run_id": os.environ.get("OCE_RUN_ID", "not-set"),
            "inventory_path": inventory_path,
            "phases": [],
            "started_at": now_iso()}


def _blocked(receipt, message):
    """Record a fail-closed refusal: the caller keeps a truthful receipt and
    no recovery step was taken (no docker call, no catalog mutation)."""
    receipt["error"] = message
    receipt["finished_at"] = now_iso()
    receipt["exit_status"] = 1
    return receipt


def _governed_identity_problems(db, user, container) -> list:
    """Recovery targets are GOVERNED, not selected (B4-CXR7U9R36/37): the
    public --db/--user/--container values are compatibility assertions that
    must equal the canonical local identity, so no CLI or environment value
    can redirect a destructive recovery. One owner for that policy."""
    return [f"{label} '{supplied}' is not the governed local value '{canon}'"
            for label, supplied, canon in (("database", db, DB),
                                           ("user", user, USER),
                                           ("container", container, CONTAINER))
            if supplied != canon]


_TEST_RECOVERY_ROOT = None


def _bind_test_recovery_root(path) -> None:
    """TEST DEPENDENCY SEAM (B4-CXR7U9R39-R2).

    Receipt-write authority is program identity, so no ambient environment can
    grant it. A test that genuinely needs different storage CONSTRUCTS this
    seam itself, in process, by importing this module and calling this
    function; it is not reachable through the production CLI, it reads no
    environment variable, and it cannot change the production default -
    unbinding restores program identity.
    """
    global _TEST_RECOVERY_ROOT
    _TEST_RECOVERY_ROOT = os.path.realpath(path)


def _unbind_test_recovery_root() -> None:
    global _TEST_RECOVERY_ROOT
    _TEST_RECOVERY_ROOT = None


def _recovery_state_dir() -> str:
    """RECEIPT-WRITE AUTHORITY (B4-CXR7U9R37, B4-CXR7U9R39-R2). The one
    directory this engine may write its OWN transition receipts into: the
    `var/recovery` directory of the program identity that owns this engine
    file. Authority derives from where the engine IS - never from the ambient
    environment - so neither the environment nor a --receipt-out value can
    widen it."""
    if _TEST_RECOVERY_ROOT is not None:
        return _TEST_RECOVERY_ROOT
    here = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(os.path.dirname(here), "var", "recovery")


def _validated_write_path(path: str) -> str:
    """Canonicalize a receipt OUTPUT path and enforce the write boundary: no
    symlink indirection in the target or in any parent component, containment
    in the recovery state directory, and an existing parent directory. Nothing
    about the phase can influence where its own receipt lands."""
    real = os.path.realpath(path)
    if real != os.path.abspath(path):
        raise RuntimeError(f"receipt output uses symlink indirection: {path}")
    root = _recovery_state_dir()
    try:
        contained = os.path.commonpath([root, real]) == root
    except ValueError:
        contained = False
    if not contained:
        raise RuntimeError("receipt output is outside the recovery state "
                           f"directory: {path}")
    parent = os.path.dirname(real)
    if not os.path.isdir(parent):
        raise RuntimeError(f"receipt output directory does not exist: {parent}")
    return real


def _fsync_dir(directory):
    """Flush a directory entry where the platform supports it (Windows does
    not, and a platform that cannot must not fail the commit)."""
    try:
        dfd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dfd)
    except OSError:
        pass
    finally:
        os.close(dfd)


def _exclusive_copy(src, dst):
    """Fallback for filesystems without hard links: create the target
    EXCLUSIVELY (so an existing receipt is refused) and flush before closing."""
    out = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(out, "wb") as f, open(src, "rb") as s:
            shutil.copyfileobj(s, f)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.unlink(dst)
        except OSError:
            pass
        raise


def _commit_receipt(path, data):
    """Commit a receipt without ever overwriting existing evidence.

    OVERWRITE POLICY (B4-CXR7U9R39-R2): a receipt file is evidence, so an
    EXISTING target is REFUSED - never silently replaced. The new receipt is
    serialized into a collision-resistant, exclusively created temporary in the
    SAME directory, flushed to disk, then linked into place exclusively, so the
    target is either complete or absent. Any failure removes the temporary and
    preserves whatever was already at the target.
    """
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".oce-receipt-", suffix=".tmp",
                               dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        try:
            os.link(tmp, path)          # exclusive: refuses an existing target
        except FileExistsError:
            raise RuntimeError(
                f"refusing to overwrite an existing receipt: {path}")
        except OSError:
            _exclusive_copy(tmp, path)
        os.unlink(tmp)
        _fsync_dir(directory)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_receipt(path):
    with open(_validated_open_path(path), encoding="utf-8") as f:
        return json.load(f)


# ── durable recovery-operation state (B4-CXR7U9R39-R3) ───────────────────
# A JSON receipt states what happened; it must not, on its own, be reusable
# authority to mutate recovery state again. Each promotion mints ONE
# high-entropy operation id and records it under the governed recovery
# boundary; a transition is permitted only while that record says PROMOTED and
# only once. Records are authority STATE (so they are updated in place), never
# evidence (receipts are evidence and are never overwritten).

def _operation_id() -> str:
    return os.urandom(16).hex()


def _transitions_dir() -> str:
    return os.path.join(_recovery_state_dir(), "transitions")


def _receipt_digest(receipt) -> str:
    """Content binding between a receipt and its operation record. Canonical
    (sorted keys, no padding) so the digest is independent of file
    whitespace and therefore checkable across processes."""
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _transition_record_path(operation_id) -> str:
    return os.path.join(_transitions_dir(), operation_id + ".json")


def _write_transition_record(operation_id, record) -> None:
    """Crash-safe update: full write + flush into the same directory, then an
    atomic replace, so a reader never sees a half-written record."""
    directory = _transitions_dir()
    os.makedirs(directory, mode=0o700, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".oce-transition-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, _transition_record_path(operation_id))
        _fsync_dir(directory)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_transition_record(operation_id, transition_dir=None):
    directory = transition_dir or _transitions_dir()
    path = os.path.join(directory, operation_id + ".json")
    if not os.path.isfile(path):
        raise RuntimeError("no durable recovery operation record for operation "
                           f"{operation_id}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _record_transition(operation_id, state, receipt, extra=None) -> None:
    """Advance the operation record. `receipt` binds the record to the exact
    promote receipt whose content authorized it. The forward-only ladder is
    enforced here: a rewrite that would move the record BACKWARD (or off the
    ladder) is refused, so a crashed FINALIZING can never be re-opened as
    PROMOTED authority by any process, and concurrent callers cannot overwrite
    one another with a lower state."""
    record = {
        "format": TRANSITION_FORMAT,
        "operation_id": operation_id,
        "state": state,
        "database": receipt.get("database"),
        "user": receipt.get("user"),
        "container": receipt.get("container"),
        "source_commit": receipt.get("source_commit"),
        "source_tree": receipt.get("source_tree"),
        "run_id": receipt.get("run_id"),
        "stamp": receipt.get("stamp"),
        "quarantine_database": receipt.get("quarantine_database"),
        "staging_database": receipt.get("staging_database"),
        "source_archive_sha256": receipt.get("source_archive_sha256"),
        "inventory_sha256": receipt.get("inventory_sha256"),
        "receipt_sha256": _receipt_digest(receipt),
        "permitted_next": (list(TRANSITIONS_ALLOWED_FROM_PROMOTED)
                           if state == TRANSITION_STATE_PROMOTED else []),
        "updated_at": now_iso(),
    }
    # first-seen time is carried forward across every state update
    created = None
    path = _transition_record_path(operation_id)
    prior = None
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                prior = json.load(f)
            created = prior.get("created_at")
        except (OSError, ValueError):
            prior = None
    record["created_at"] = created or record["updated_at"]
    # DURABLE keys recorded by earlier states (commit_point, rollback_floor,
    # selected_transition, ...) are carried forward: a state advance may not
    # silently erase facts the transaction still depends on.
    if isinstance(prior, dict):
        for key, value in prior.items():
            if key not in record:
                record[key] = value
    if extra:
        record.update(extra)
    # FORWARD-ONLY: read the durable record and refuse any regression before
    # writing. A same-state rewrite is idempotent; any move not permitted by
    # the ladder from the CURRENT durable state (FINALIZING -> PROMOTED,
    # terminal -> anything, etc.) is refused.
    if created is not None:
        try:
            with open(path, encoding="utf-8") as f:
                current = json.load(f).get("state")
        except (OSError, ValueError):
            current = None
        if current is not None and state != current \
                and state not in _TRANSITION_LADDER.get(current, set()):
            raise RuntimeError(
                f"refusing to move recovery operation {operation_id} backward: "
                f"{current!r} -> {state!r}")
    _write_transition_record(operation_id, record)


def _claim_transition(operation_id, transition, promote=None) -> dict:
    """Consume this operation's ONE-TIME transition authority BEFORE any docker
    or catalog call — OPERATION-WIDE, not per-transition (B4-CXR7U9R40-R1).

    The claim is one file per OPERATION, exclusively created: finalize and
    rollback contend on the SAME name, so exactly one branch can ever win.
    The winning branch and its binding are recorded IN the claim file, so the
    selection is durably attributable after a crash. A loser fails here, before
    any docker, catalog or receipt mutation exists to make.
    """
    if transition not in TRANSITIONS_ALLOWED_FROM_PROMOTED:
        raise RuntimeError(f"unknown transition {transition!r}")
    directory = _transitions_dir()
    os.makedirs(directory, mode=0o700, exist_ok=True)
    claim_path = os.path.join(directory, f"{operation_id}.claim")
    claim = {"format": _CLAIM_FORMAT,
             "operation_id": operation_id,
             "transition": transition,
             "claimed_at": now_iso()}
    if promote is not None:
        claim["receipt_sha256"] = _receipt_digest(promote)
    payload = json.dumps(claim, sort_keys=True, indent=2) + "\n"
    try:
        fd = os.open(claim_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        # The claim file exists but the winner may not have finished writing
        # it yet (O_EXCL create precedes the payload write). Spin briefly so
        # the refusal can NAME the winning transition truthfully; if it is
        # still unreadable, fail closed with 'unknown' — the authority is
        # spent either way.
        import time
        winner = None
        for _ in range(50):
            winner = _load_claim(operation_id)
            if winner:
                break
            time.sleep(0.01)
        chosen = winner.get("transition") if winner else "unknown"
        raise RuntimeError(
            f"recovery operation {operation_id} was already claimed for a "
            f"different or earlier transition ({chosen!r}); the "
            f"{transition!r} authority is spent")
    try:
        os.write(fd, payload.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(directory)
    # The record is moved to the IN-FLIGHT state only after the claim file won:
    # state validation happened in _validated_transition_receipt, the claim is
    # the atomic selection, and this write is forward-only (enforced in
    # _record_transition), so a crash here leaves PROMOTED + a claim file — an
    # attributable, spent authority — never a re-opened PROMOTED.
    _record_transition(operation_id,
                       TRANSITION_STATE_FINALIZING if transition == "finalize"
                       else TRANSITION_STATE_ROLLING_BACK,
                       promote, extra={"selected_transition": transition})
    return claim


def _load_claim(operation_id):
    """The durable operation-wide claim, or None if none was ever taken."""
    path = os.path.join(_transitions_dir(), f"{operation_id}.claim")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


class _ExecutionAuthorityConflict(RuntimeError):
    """A process already owns the operation's mutation interval."""


class _OperationExecutionAuthority:
    """One OS advisory lock per operation for the complete mutation interval.

    The lock file is persistent evidence, not the authority. The operating
    system owns the exclusive byte-range lock and releases it on process death,
    so a killed executor cannot leave a permanent lease. Lock acquisition is
    silent; after complete authorization, metadata is published with the exact
    operation, selected transition, receipt digest, process id, and random
    token. A denied contender restores the prior payload, and a contender never
    trusts stale metadata when the OS says the lock is held.
    """
    def __init__(self, operation_id, transition, promote):
        self.operation_id = operation_id
        self.transition = transition
        self.promote = promote
        self.fd = None
        self.path = os.path.join(_transitions_dir(), f"{operation_id}.execution.lock")
        self.original_payload = None
        self.activated = False
        self.created_transitions_dir = False

    def acquire(self):
        self.created_transitions_dir = not os.path.isdir(_transitions_dir())
        os.makedirs(_transitions_dir(), mode=0o700, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            size = os.fstat(fd).st_size
            if size == 0:
                os.write(fd, b"\0")
                size = 1
            os.lseek(fd, 0, os.SEEK_SET)
            self.original_payload = os.read(fd, size)
            os.lseek(fd, 0, os.SEEK_SET)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            owner = "unknown"
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                raw = os.read(fd, 4096).decode("utf-8", errors="replace")
                parsed = json.loads(raw)
                owner = parsed.get("transition", "unknown")
            except (OSError, ValueError):
                pass
            os.close(fd)
            raise _ExecutionAuthorityConflict(
                f"operation {self.operation_id} already has execution authority "
                f"for {owner!r}; {self.transition!r} refused") from e
        self.fd = fd
        return self

    def activate(self):
        """Publish metadata only after complete authorization under the lock.

        Binding and the OS lock are intentionally silent. A denial restores the
        exact prior lock payload (or removes the lock file), so malformed,
        substituted, replayed, and state-ineligible receipts have no durable
        execution-authority side effect.
        """
        if self.fd is None:
            raise RuntimeError("execution authority is not locked")
        metadata = {
            "format": "oce-operation-execution-authority-v1",
            "operation_id": self.operation_id,
            "transition": self.transition,
            "receipt_sha256": _receipt_digest(self.promote),
            "pid": os.getpid(),
            "token": os.urandom(16).hex(),
            "acquired_at": now_iso(),
        }
        payload = json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n"
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.ftruncate(self.fd, 0)
        os.write(self.fd, payload.encode("utf-8"))
        os.fsync(self.fd)
        _fsync_dir(_transitions_dir())
        self.activated = True

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        if self.fd is None:
            return False
        fd = self.fd
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
            self.fd = None
        if not self.activated:
            try:
                if self.original_payload in (None, b"\0"):
                    os.unlink(self.path)
                else:
                    restore = os.open(self.path, os.O_WRONLY | os.O_TRUNC, 0o600)
                    try:
                        os.write(restore, self.original_payload)
                        os.fsync(restore)
                    finally:
                        os.close(restore)
                _fsync_dir(_transitions_dir())
                if self.created_transitions_dir:
                    try:
                        os.rmdir(_transitions_dir())
                    except OSError:
                        pass
            except FileNotFoundError:
                pass
        return False


def _execution_receipt_binding(receipt_path):
    """Minimal identity used only to name/bind the execution lock.

    Full receipt/state authority is still enforced by the phase body after the
    lock is acquired and before any catalog or filesystem mutation.
    """
    promote = _load_receipt(receipt_path)
    if not isinstance(promote, dict):
        raise RuntimeError("promote receipt is not a JSON object")
    operation_id = promote.get("operation_id")
    if not isinstance(operation_id, str) or not OPERATION_ID_RE.match(operation_id):
        raise RuntimeError("promote receipt operation id is missing or malformed")
    return promote, operation_id


def _execution_binding_blocked(phase, receipt_in_path, inventory_path, db, user,
                               container, exc):
    """Return a receipt for a binding denial without entering a mutation body.

    This path performs no claim, transition rewrite, catalog observation, or
    Docker call. Its only purpose is to preserve a truthful phase denial when a
    receipt cannot even supply the operation id needed to name the OS lock.
    """
    receipt = _base_receipt(phase, db, user, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    return _blocked(receipt, f"refusing recovery execution binding: {exc}")


def _bound_operation(promote, transition_dir=None):
    """Bind a promote receipt to its ONE durable operation record: the record
    must exist, its format must be known, its content digest must match this
    receipt, and every identity field must agree. Shared by the transition
    gate (which then checks state/permission) and by RECONCILIATION (which
    must read the durable truth WITHOUT consuming any authority). Returns
    (operation_id, record)."""
    operation_id = promote.get("operation_id")
    if not isinstance(operation_id, str) or not OPERATION_ID_RE.match(operation_id):
        raise RuntimeError(f"receipt operation id {operation_id!r} is missing or malformed")
    record = _load_transition_record(operation_id, transition_dir=transition_dir)
    if record.get("format") != TRANSITION_FORMAT:
        raise RuntimeError("durable recovery operation record has an unknown format")
    if record.get("receipt_sha256") != _receipt_digest(promote):
        raise RuntimeError("receipt content does not match its durable operation "
                           "record (substituted or altered receipt)")
    for label in ("database", "user", "container", "source_commit", "source_tree",
                  "run_id", "stamp", "quarantine_database", "staging_database",
                  "source_archive_sha256", "inventory_sha256"):
        if record.get(label) != promote.get(label):
            raise RuntimeError(f"receipt {label} does not match its durable "
                               "operation record")
    return operation_id, record


def _validated_promote_receipt(path, db, user, container, inventory_path,
                               inventory_sha_path):
    """RECOVERY TRANSITION AUTHORITY (B4-CXR7U9R36).

    A promote receipt is the authority to mutate recovery TRANSITION state -
    drop the quarantine, rename a database back over the canonical name - so
    its CONTENT is authorized, not just its location: filesystem containment
    proves where the bytes came from, never what they may order. Everything
    here fails closed BEFORE any docker or catalog call, so a contained but
    forged, substituted, replayed or incomplete receipt cannot direct a
    destructive step. Separate from BACKUP ARTIFACT PATH AUTHORITY, which owns
    the archive/inventory inputs (_validated_open_path).

    This helper validates the complete engine-minted promote receipt and its
    governed identities. Callers separately bind it to the durable operation
    and enforce the exact state/branch they are authorized to exercise (fresh
    transition versus intent-bound resume).

    Returns (promote, stamp, quarantine, staging, operation_id).
    """
    promote = _load_receipt(path)
    if not isinstance(promote, dict):
        raise RuntimeError("receipt is not a JSON object")
    if promote.get("format") != RECEIPT_FORMAT:
        raise RuntimeError(f"receipt format is not {RECEIPT_FORMAT}")
    if promote.get("operation_phase") != "promote":
        raise RuntimeError("receipt is not a promote receipt "
                           f"(got {promote.get('operation_phase')!r})")
    if promote.get("exit_status") != 0:
        raise RuntimeError("receipt records a failed promote (exit_status != 0)")
    if promote.get("promoted") is not True:
        raise RuntimeError("receipt does not record a completed promotion")
    phases = promote.get("phases")
    if not isinstance(phases, list) or len(phases) != len(PHASES_PROMOTE) \
            or not valid_phase_prefix(phases, PHASES_PROMOTE):
        raise RuntimeError("receipt phase sequence is incomplete or out of order")
    for label, got, canon in (("database", promote.get("database"), db),
                              ("source_database", promote.get("source_database"), db),
                              ("target_database", promote.get("target_database"), db),
                              ("user", promote.get("user"), user),
                              ("container", promote.get("container"), container)):
        if got != canon:
            raise RuntimeError(f"receipt {label} {got!r} is not this recovery's "
                               f"governed value {canon!r}")
    stamp = promote.get("stamp")
    if not isinstance(stamp, str) or not STAMP_RE.match(stamp):
        raise RuntimeError(f"receipt stamp {stamp!r} is missing or malformed")
    quarantine = promote.get("quarantine_database")
    staging = promote.get("staging_database")
    if quarantine != QUARANTINE_PREFIX + stamp:
        raise RuntimeError(f"receipt quarantine {quarantine!r} is not bound to "
                           "its stamp")
    if staging != STAGING_PREFIX + stamp:
        raise RuntimeError(f"receipt staging {staging!r} is not bound to its stamp")
    for label, name in (("quarantine", quarantine), ("staging", staging)):
        if name == db:
            raise RuntimeError(f"receipt {label} names the canonical database")
    if not SHA256_RE.match(str(promote.get("source_archive_sha256", ""))):
        raise RuntimeError("receipt records no archive identity")
    recorded_inventory = promote.get("inventory_path")
    if not isinstance(recorded_inventory, str) or \
            os.path.realpath(recorded_inventory) != _validated_open_path(inventory_path):
        raise RuntimeError("receipt inventory is not this recovery's inventory")
    if promote.get("inventory_sha256") != _validated_read_text(inventory_sha_path).strip():
        raise RuntimeError("receipt inventory SHA is not this recovery's inventory SHA")
    recorded_run = promote.get("run_id")
    live_run = os.environ.get("OCE_RUN_ID")
    if live_run and recorded_run not in (None, "", "not-set", "unknown") \
            and recorded_run != live_run:
        raise RuntimeError("receipt was produced by a different recovery run")
    # In production a recovery carries its revision and run identity; an
    # unknown one is not authority for a destructive transition.
    for label in ("source_commit", "source_tree"):
        value = promote.get(label)
        if not isinstance(value, str) or not REVISION_RE.match(value):
            raise RuntimeError(f"receipt {label} is not a known revision: {value!r}")
    if recorded_run in (None, "", "not-set", "unknown"):
        raise RuntimeError("receipt records no authoritative run identity")
    operation_id = promote.get("operation_id")
    if not isinstance(operation_id, str) or not OPERATION_ID_RE.match(operation_id):
        raise RuntimeError(f"receipt operation id {operation_id!r} is missing or malformed")
    return promote, stamp, quarantine, staging, operation_id


def _validated_transition_receipt(path, db, user, container, inventory_path,
                                  inventory_sha_path, transition):
    promote, stamp, quarantine, staging, operation_id = _validated_promote_receipt(
        path, db, user, container, inventory_path, inventory_sha_path)
    _operation_id, record = _bound_operation(promote)
    state = record.get("state")
    if state != TRANSITION_STATE_PROMOTED:
        raise RuntimeError(
            f"recovery operation {operation_id} is {state!r}: its "
            f"{transition} authority is no longer available")
    if transition not in (record.get("permitted_next") or ()):
        raise RuntimeError(f"recovery operation {operation_id} does not permit "
                           f"{transition}")
    return promote, stamp, quarantine, staging, operation_id


def _valid_commit_intent(record, promote):
    """Validate the durable forward decision without trusting its labels."""
    intent = record.get("commit_intent")
    if not isinstance(intent, dict):
        return False
    expected = {
        "marker": "forward_commit",
        "operation_id": promote.get("operation_id"),
        "receipt_sha256": _receipt_digest(promote),
        "database": promote.get("database"),
        "user": promote.get("user"),
        "container": promote.get("container"),
        "quarantine_database": promote.get("quarantine_database"),
    }
    return all(intent.get(key) == value for key, value in expected.items()) \
        and isinstance(intent.get("at"), str)


def _validated_resume_finalize_receipt(path, db, user, container, inventory_path,
                                        inventory_sha_path):
    """Recover authority for a finalize whose ONE-TIME claim is already spent.

    Resume is narrower than fresh finalize authority. The exact promote receipt,
    operation record, finalize claim, canonical target, and durable forward
    intent must all agree. No new branch can be selected after the claim.
    """
    promote, stamp, quarantine, staging, operation_id = _validated_promote_receipt(
        path, db, user, container, inventory_path, inventory_sha_path)
    _operation_id, record = _bound_operation(promote)
    state = record.get("state")
    if state not in (TRANSITION_STATE_COMMIT_INTENT,
                     TRANSITION_STATE_COMMIT_POINT, "FINALIZED"):
        raise RuntimeError(
            f"recovery operation {operation_id} is {state!r}: it has no durable "
            "finalize intent to resume")
    claim = _load_claim(operation_id)
    if not isinstance(claim, dict) or claim.get("format") != _CLAIM_FORMAT \
            or claim.get("operation_id") != operation_id \
            or claim.get("transition") != "finalize" \
            or claim.get("receipt_sha256") != _receipt_digest(promote):
        raise RuntimeError("existing finalize claim is missing, corrupt, or bound "
                           "to different authority")
    if record.get("selected_transition") != "finalize" \
            or not _valid_commit_intent(record, promote):
        raise RuntimeError("durable finalize intent is missing, malformed, or bound "
                           "to different authority")
    if state in (TRANSITION_STATE_COMMIT_POINT, "FINALIZED"):
        commit_point = record.get("commit_point")
        if not isinstance(commit_point, dict) \
                or commit_point.get("marker") != "quarantine_dropped" \
                or not isinstance(commit_point.get("at"), str):
            raise RuntimeError("durable commit-point evidence is missing or malformed")
    return promote, stamp, quarantine, staging, operation_id, state


def _validated_preintent_abort_receipt(path, db, user, container,
                                       inventory_path, inventory_sha_path):
    """Admit recovery of the already-selected finalize branch before intent."""
    promote, stamp, quarantine, staging, operation_id = _validated_promote_receipt(
        path, db, user, container, inventory_path, inventory_sha_path)
    _operation_id, record = _bound_operation(promote)
    if record.get("state") != TRANSITION_STATE_FINALIZING:
        raise RuntimeError(
            f"pre-intent abort requires FINALIZING, got {record.get('state')!r}")
    if record.get("commit_intent") is not None \
            or record.get("commit_point") is not None:
        raise RuntimeError("pre-intent abort is forbidden after forward intent")
    if record.get("selected_transition") != "finalize":
        raise RuntimeError("pre-intent abort requires the selected finalize branch")
    claim = _load_claim(operation_id)
    if not isinstance(claim, dict) or claim.get("format") != _CLAIM_FORMAT \
            or claim.get("operation_id") != operation_id \
            or claim.get("transition") != "finalize" \
            or claim.get("receipt_sha256") != _receipt_digest(promote):
        raise RuntimeError("pre-intent abort finalize claim is missing, corrupt, or mismatched")
    floor = _floor_from_record(operation_id)
    if not isinstance(floor, dict) or not floor.get("tables") \
            or not isinstance(floor.get("rows"), dict):
        raise RuntimeError("pre-intent abort rollback floor is missing or malformed")
    return promote, stamp, quarantine, staging, operation_id, floor


def _floor_from_record(operation_id):
    """The durably recorded pre-promotion floor for this operation (B4-CXR7U9R39X).
    A transition process verifies the restored ORIGINAL against what the
    original WAS, never against the backup's description of it. A record
    without a floor predates the floor law and yields None (the fallback
    verification stays backup-based and loud, as before)."""
    try:
        record = _load_transition_record(operation_id)
    except Exception:
        return None
    floor = record.get("rollback_floor")
    if not isinstance(floor, dict) or not floor.get("tables"):
        return None
    if not isinstance(floor.get("rows"), dict):
        return None
    return floor


def _approved_roots() -> list:
    """Approved roots for artifact inputs (B4-CXR7U9R12/U9X2).

    Containment authority comes from TWO channels, neither of which the
    artifact path itself can influence:
      1. program identity - the directory holding this engine AND the
         engine's own durable recovery-state directory (var/recovery,
         where restore.sh stages its phase receipts). Both are derived
         from this file's real location, never from CLI or artifact
         data.
      2. the operator-declared OCE_BACKUP_ROOTS list (os.pathsep
         separated), exported by restore.sh for the backup store it
         opened, or supplied by a test harness. CLI arguments can never
         approve their own containment root.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    roots = [here,
             os.path.join(os.path.dirname(here), "var", "recovery")]
    for part in os.environ.get("OCE_BACKUP_ROOTS", "").split(os.pathsep):
        cand = part.strip()
        if cand and os.path.isdir(cand):
            roots.append(os.path.realpath(cand))
    return roots


def _validated_open_path(path: str) -> str:
    """Canonicalize an operator-selected artifact path and ENFORCE
    containment on it (B4-CXR7U9R7/R12).

    These paths are DATA, never authority: they cannot alter executable
    identity (docker/pg_restore are driven by this engine itself),
    credentials, the governed database destination, or any decision
    authority; their content is SHA-verified before use (tamper fails
    closed). They come from the operator or the governed restore pipeline,
    never from untrusted runtime data.

    Enforced here, in order:
      1. no symlink indirection - realpath(path) must equal abspath(path),
         so the artifact must BE the named file, not a pointer elsewhere;
      2. containment - the real path must sit inside an approved root
         (_approved_roots owns which roots and where they come from);
      3. the path must be an existing regular file.

    Single-admission note (B4-CXR7U9R35): every phase admits the artifact path
    ONCE and hands the returned canonical path to every later sink (hashing,
    the container copy, the container-side re-hash), so no sink sees the raw
    CLI string. A replacement of the admitted host file between admission and
    the container copy is inside the single-principal trusted computing base
    and is NOT detected; what IS enforced is that the bytes the container
    holds are the bytes of this admitted path (the container re-hash must
    equal the recorded source hash before any staging or canonical mutation).
    """
    real = os.path.realpath(path)
    if real != os.path.abspath(path):
        raise RuntimeError(f"path uses symlink indirection: {path}")
    roots = _approved_roots()
    contained = False
    for root in roots:
        try:
            if os.path.commonpath([root, real]) == root:
                contained = True
                break
        except ValueError:
            pass
    if not contained:
        raise RuntimeError(
            "path is outside every approved backup root "
            f"(program identity or OCE_BACKUP_ROOTS): {path}")
    if not os.path.isfile(real):
        raise RuntimeError(f"not a regular file: {path}")
    return real


def _validated_read_text(path: str) -> str:
    """Read a path as UTF-8 text after containment validation.

    B4-CXR7U9R14: the validated path itself (never the raw argument) is
    what reaches the open() sink, so the reading sink only ever sees a
    realpath-resolved, approved-root-contained path.
    """
    return open(os.path.realpath(_validated_open_path(path)),
                encoding="utf-8").read()


def _load_protected_inventory(inventory_path, inventory_sha_path):
    """Load and hash-verify the protected inventory (fail closed on tamper)."""
    inv_doc = _validated_read_text(inventory_path)
    inv_sha = _validated_read_text(inventory_sha_path).strip()
    if hashlib.sha256(inv_doc.encode()).hexdigest() != inv_sha:
        raise RuntimeError("database inventory tampered (SHA mismatch)")
    return parse_inventory(inv_doc)


def _verify_db(container, db, user, inventory, probe):
    """Row counts + protected fingerprints of one database. Returns
    (ok, problems, rows, fps)."""
    watch = sorted(set(capture_inventory_rows(inventory)) | set(probe))
    rows = collect_observed_rows(container, db, user, watch)
    fps = None
    if capture_inventory_fingerprints(inventory):
        fps = collect_observed_fingerprints(container, db, user, watch)
    ok, problems = verify_inventory(inventory, rows, probe, fps)
    return ok, problems, rows, fps


def _capture_floor(container, db, user, inventory, probe):
    """ROLLBACK FLOOR (B4-CXR7U9R39X): capture the pre-promotion canonical
    truth as IT is, not as the backup describes it. A full replace exists
    precisely because the live database may legitimately differ from the
    backup (probe tables absent, newer rows, drifted values) - so a rollback
    verified against the BACKUP's inventory would fail on a correctly restored
    original. The floor is a small in-memory spec (row counts + fingerprints
    of exactly the tables the backup verifies) captured BEFORE any durable
    mutation, and never claims the original matched the backup."""
    watch = sorted(set(capture_inventory_rows(inventory)) | set(probe))
    if not watch:
        return None
    rows = collect_observed_rows(container, db, user, watch)
    fps = collect_observed_fingerprints(container, db, user, watch)
    return {"tables": watch, "rows": rows, "fingerprints": fps}


def _verify_against_floor(container, db, user, floor):
    """Verify one database against a captured floor: every watched table must
    exist with the floor's exact row count and content fingerprint. Returns
    (ok, problems, detail) in the same shape as rollback_recovery's detail."""
    rows = collect_observed_rows(container, db, user, floor["tables"])
    fps = collect_observed_fingerprints(container, db, user, floor["tables"])
    problems = []
    for name in floor["tables"]:
        expected = floor["rows"].get(name)
        got = rows.get(name)
        if got == -1 or got is None:
            problems.append(f"table {name} unreadable after rollback (got {got})")
        elif expected is not None and got != expected:
            problems.append(f"row count mismatch {name}: expected {expected} got {got}")
        expected_fp = (floor["fingerprints"] or {}).get(name)
        got_fp = (fps or {}).get(name)
        if got_fp == "-err-" or got_fp is None:
            problems.append(f"missing fingerprint for {name}")
        elif expected_fp is not None and got_fp != expected_fp:
            problems.append(f"value fingerprint mismatch {name}")
    detail = {"rollback_verification": {"result": "ok" if not problems else "failed",
                                        "tables": rows, "floor_verified": True}}
    if fps is not None:
        detail["rollback_verification"]["fingerprints"] = fps
    return not problems, problems, detail


def rollback_recovery(container, user, db, quarantine, inventory, probe, floor=None):
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
        # A rollback proves the ORIGINAL was restored, never that the original
        # equals the backup: verification compares against the pre-promotion
        # floor when one was captured, and only falls back to the backup's
        # inventory when no floor exists (an unverified rollback then stays
        # loud, as before).
        if floor is not None:
            ok, vprobs, vdetail = _verify_against_floor(container, db, user, floor)
        else:
            ok, vprobs, rows, fps = _verify_db(container, db, user, inventory, probe)
            vdetail = {"rollback_verification": {"result": "ok" if ok else "failed"}}
            if fps is not None:
                vdetail["rollback_verification"]["fingerprints"] = fps
            vdetail["rollback_verification"]["tables"] = rows
        detail.update(vdetail)
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
    receipt = _base_receipt("promote", db, user, container, inventory_path)
    targets = _governed_identity_problems(db, user, container)
    if targets:
        return _blocked(receipt, "refusing recovery target: " + "; ".join(targets))
    stamp = hashlib.sha256(os.urandom(8)).hexdigest()[:12]
    quarantine = QUARANTINE_PREFIX + stamp
    receipt["stamp"] = stamp
    receipt["quarantine_database"] = quarantine
    receipt["quarantine_held"] = True
    receipt["quarantine_dropped"] = False
    receipt["promoted"] = False
    # ONE durable operation per promotion (R39-R3). The id is minted now so
    # every receipt can name its operation, but the durable record is opened
    # only when the promotion starts touching recovery-durable state: an
    # invocation refused during preflight writes NO operation state at all.
    operation_id = _operation_id()
    receipt["operation_id"] = operation_id
    operation_started = False
    staging = None
    quarantined = False
    remote = None
    try:
        # 1. protected inventory validated (hash + parse + non-empty truth)
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        receipt["inventory_path"] = _validated_open_path(inventory_path)
        receipt["inventory_sha256"] = _validated_read_text(inventory_sha_path).strip()
        probe = parse_probe_spec(probe_spec)
        if not (capture_inventory_rows(inventory) or probe):
            raise RuntimeError("database inventory lists no tables to verify (incomplete backup)")
        receipt["phases"].append("inventory_validated")
        # 2. archive admitted ONCE: this one canonical identity feeds the hash,
        #    the container copy and the container-side re-hash (R35). Every
        #    later sink consumes `archive_path`; the raw CLI string is never
        #    handed to a sink again.
        archive_path = _validated_open_path(archive)
        source_sha = sha256_file(archive_path)
        receipt["source_archive_sha256"] = source_sha
        remote = clone_archive_into_container(container, archive_path)
        validate_archive(container, remote)
        # the restore consumes the CONTAINER's copy: prove it is the admitted
        # bytes before any staging or canonical mutation exists to make
        remote_sha = sha256_remote_file(container, remote)
        receipt["remote_archive_sha256"] = remote_sha
        if remote_sha != source_sha:
            raise RuntimeError("the container copy of the archive does not match "
                               "the admitted source (SHA mismatch)")
        receipt["archive_validated"] = True
        receipt["phases"].append("archive_validated")
        # ROLLBACK FLOOR: captured now - after the archive is admitted (so a
        # hostile-artifact refusal still makes ZERO container calls, R7) and
        # before ANY durable mutation - so a rollback verifies the restored
        # ORIGINAL against what the original was, not against the backup (a
        # full replace exists because they can differ).
        floor = _capture_floor(container, db, user, inventory, probe)
        receipt["rollback_floor_captured"] = floor is not None
        # postgres version
        ver = psql(container, db, user, "SHOW server_version;")
        receipt["postgres_version"] = (ver.stdout.decode(errors="replace").strip()
                                       if ver.returncode == 0 else "")
        # 3. staging created - the first recovery-durable mutation, so the
        #    operation record (and with it any transition authority) begins here
        _record_transition(operation_id, "CREATED", receipt)
        operation_started = True
        staging = create_staging_db(container, user, db, stamp)
        receipt["staging_database"] = staging
        receipt["phases"].append("staging_created")
        # 4. restore into staging with exit-on-error. pg_restore consumes the
        #    container path, so no host-side read (and no stdin payload) is
        #    involved: the bytes restored are the bytes re-hashed above (R35).
        r = docker_exec(container, ["pg_restore", "-U", user, "--exit-on-error",
                                    "--no-owner", "--no-privileges", "--dbname", staging, remote],
                        timeout=1800)
        if r.returncode != 0:
            raise RuntimeError("pg_restore into staging failed: "
                               + r.stderr.decode(errors="replace"))
        receipt["phases"].append("staging_restored")
        # 5. staging truth verified (counts + protected fingerprints)
        ok, problems, rows, fps = _verify_db(container, staging, user, inventory, probe)
        receipt["staging_verification"] = {"result": "ok" if ok else "failed",
                                           "tables": rows}
        if fps is not None:
            receipt["staging_verification"]["fingerprints"] = fps
        if not ok:
            raise RuntimeError("staging verification FAILED: " + "; ".join(problems))
        receipt["phases"].append("staging_verified")
        _record_transition(operation_id, "STAGED", receipt)
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
        ok2, problems2, rows2, fps2 = _verify_db(container, db, user, inventory, probe)
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
        # PROMOTED is the state that still offers transition authority; hold the
        # record's digest and identity to this exact receipt. The pre-promotion
        # floor is durably part of the record: the later finalize/rollback
        # processes verify the restored original against THIS, in their own
        # process, without trusting the backup to describe the original.
        _record_transition(operation_id, TRANSITION_STATE_PROMOTED, receipt,
                           extra={"rollback_floor": floor})
        return receipt
    except Exception as e:
        receipt["error"] = str(e)
        if quarantined:
            # Failure after canonical->quarantine began: ROLL BACK now. The
            # rollback source (quarantine) is still present by construction,
            # and the pre-promotion floor defines what "restored" means.
            ok_rb, rb_problems, rb_detail = rollback_recovery(
                container, user, db, quarantine, inventory, probe, floor=floor)
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
        # A failed promotion offers no transition authority at all (and a
        # preflight refusal has no operation to record).
        if operation_started:
            _record_transition(operation_id, "FAILED", receipt,
                               extra={"error": str(e)})
        return receipt


# ── phase: finalize ──────────────────────────────────────────────────────
def _phase_finalize_locked(receipt_in_path, inventory_path, inventory_sha_path, db,
                           user, container, probe_spec, execution_authority,
                           resume_only=False):
    receipt = _base_receipt("resume-finalize" if resume_only else "finalize",
                            db, user, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    targets = _governed_identity_problems(db, user, container)
    if targets:
        return _blocked(receipt, "refusing recovery target: " + "; ".join(targets))

    resumed = False
    durable_state = TRANSITION_STATE_FINALIZING
    if resume_only:
        try:
            (promote, stamp, quarantine, staging, operation_id,
             durable_state) = _validated_resume_finalize_receipt(
                 receipt_in_path, db, user, container, inventory_path,
                 inventory_sha_path)
            resumed = True
        except Exception as e:
            return _blocked(
                receipt, f"refusing recovery resume authority: {e}")
        execution_authority.activate()
    else:
        try:
            promote, stamp, quarantine, staging, operation_id = \
                _validated_transition_receipt(
                    receipt_in_path, db, user, container, inventory_path,
                    inventory_sha_path, "finalize")
            # Full receipt/state/identity authorization is complete while the OS
            # lock is held. Consume the one operation branch, then publish
            # execution metadata before any catalog or filesystem mutation.
            _claim_transition(operation_id, "finalize", promote)
            execution_authority.activate()
        except Exception as e:
            return _blocked(
                receipt, f"refusing recovery transition authority: {e}")
    receipt["stamp"] = stamp
    receipt["staging_database"] = staging
    receipt["quarantine_database"] = quarantine
    receipt["source_archive_sha256"] = promote.get("source_archive_sha256")
    receipt["promoted"] = True
    receipt["resumed"] = resumed
    receipt["rollback_required"] = False
    receipt["rollback_attempted"] = False
    receipt["rollback_succeeded"] = None
    receipt["rollback_failed"] = False
    receipt["original_canonical_restored"] = False
    receipt["promoted_candidate_removed"] = False
    receipt["quarantine_retained"] = False
    floor = _floor_from_record(operation_id)
    inventory = None
    probe = {}
    try:
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        probe = parse_probe_spec(probe_spec)
        # The last fallible verification is always performed before the drop.
        # On resume it re-proves canonical content from the same protected
        # inventory; quarantine presence then determines whether the physical
        # drop still has work to do.
        ok, problems, rows, fps = _verify_db(container, db, user, inventory, probe)
        receipt["final_verification"] = {"result": "ok" if ok else "failed",
                                         "tables": rows}
        if fps is not None:
            receipt["final_verification"]["fingerprints"] = fps
        if not ok:
            raise RuntimeError("final canonical verification FAILED: "
                               + "; ".join(problems))
        receipt["phases"].append("final_canonical_verified")

        if resumed and durable_state == "FINALIZED":
            if db_exists(container, user, quarantine):
                raise RuntimeError("FINALIZED operation has a live quarantine")
            receipt["commit_intent_recorded"] = True
            receipt["commit_point_recorded"] = True
            receipt["quarantine_dropped"] = True
            receipt["quarantine_removal_verified"] = True
            receipt["phases"].extend(["quarantine_dropped",
                                      "quarantine_removal_verified"])
            receipt["finished_at"] = now_iso()
            receipt["exit_status"] = 0
            receipt["redis_restored"] = False
            return receipt

        # BEFORE THE DROP: make the irreversible forward decision durable. From
        # this point the shell forbids rolling back either store, even if this
        # process dies before Docker accepts the drop.
        if not resumed or durable_state == TRANSITION_STATE_FINALIZING:
            _record_transition(
                operation_id, TRANSITION_STATE_COMMIT_INTENT, promote,
                extra={"commit_intent": {
                    "marker": "forward_commit",
                    "operation_id": operation_id,
                    "receipt_sha256": _receipt_digest(promote),
                    "database": db,
                    "user": user,
                    "container": container,
                    "quarantine_database": quarantine,
                    "at": now_iso()}})
            durable_state = TRANSITION_STATE_COMMIT_INTENT
        receipt["commit_intent_recorded"] = True

        if resumed and durable_state in (TRANSITION_STATE_COMMIT_INTENT,
                                         TRANSITION_STATE_COMMIT_POINT) \
                and not db_exists(container, user, quarantine):
            # Crash after DROP returned but before COMMIT_POINT_REACHED landed.
            receipt["quarantine_dropped"] = True
        else:
            drop_db(container, user, quarantine)
            receipt["quarantine_dropped"] = True
        receipt["phases"].append("quarantine_dropped")

        # Record observed physical completion immediately after the drop. A
        # restart can reconstruct COMMIT_POINT_REACHED from the durable intent
        # plus authoritative catalog/content observations.
        _record_transition(operation_id, TRANSITION_STATE_COMMIT_POINT, promote,
                           extra={"commit_point": {
                               "marker": "quarantine_dropped",
                               "at": now_iso()}})
        durable_state = TRANSITION_STATE_COMMIT_POINT
        receipt["commit_point_recorded"] = True
        if db_exists(container, user, quarantine):
            raise RuntimeError("quarantine database still present after DROP")
        receipt["quarantine_removal_verified"] = True
        receipt["phases"].append("quarantine_removal_verified")
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 0
        receipt["redis_restored"] = False
        _record_transition(operation_id, "FINALIZED", promote)
        return receipt
    except Exception as e:
        receipt["error"] = str(e)
        intent_bound = receipt.get("commit_intent_recorded") is True \
            or durable_state in (TRANSITION_STATE_COMMIT_INTENT,
                                 TRANSITION_STATE_COMMIT_POINT, "FINALIZED")
        if not intent_bound:
            # Failure before durable intent: the quarantine is still the
            # rollback source, so recovery may restore both stores.
            receipt["rollback_required"] = True
            if inventory is None:
                receipt["rollback_attempted"] = True
                receipt["rollback_succeeded"] = False
                receipt["rollback_failed"] = True
                receipt["original_canonical_restored"] = False
                receipt["rollback_error"] = (
                    f"cannot verify rollback: inventory unavailable ({e})")
            else:
                try:
                    ok_rb, rb_problems, rb_detail = rollback_recovery(
                        container, user, db, quarantine, inventory, probe, floor=floor)
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
            # Intent is the forward decision. Never relabel it FAILED or roll
            # back after this boundary; a restart must resume the same operation.
            receipt["quarantine_retained"] = receipt.get("quarantine_dropped") is not True
            receipt["postgres_committed"] = receipt.get("quarantine_dropped") is True
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        if intent_bound:
            _record_transition(operation_id, durable_state, promote,
                               extra={"error": str(e)})
        else:
            _record_transition(
                operation_id,
                "ROLLED_BACK" if receipt.get("rollback_succeeded") is True else "FAILED",
                promote, extra={"error": str(e)})
        return receipt


def phase_finalize(receipt_in_path, inventory_path, inventory_sha_path, db,
                   user, container, probe_spec):
    """Fresh finalize under the operation's OS-backed execution authority."""
    try:
        promote, operation_id = _execution_receipt_binding(receipt_in_path)
    except Exception as exc:
        return _execution_binding_blocked(
            "finalize", receipt_in_path, inventory_path, db, user, container, exc)
    with _OperationExecutionAuthority(operation_id, "finalize", promote) as authority:
        return _phase_finalize_locked(
            receipt_in_path, inventory_path, inventory_sha_path, db, user,
            container, probe_spec, authority, resume_only=False)


def phase_resume_finalize(receipt_in_path, inventory_path, inventory_sha_path,
                           db, user, container, probe_spec):
    """Resume a spent finalize claim after a crash under the same executor lock."""
    try:
        promote, operation_id = _execution_receipt_binding(receipt_in_path)
    except Exception as exc:
        return _execution_binding_blocked(
            "resume-finalize", receipt_in_path, inventory_path, db, user,
            container, exc)
    with _OperationExecutionAuthority(operation_id, "resume-finalize", promote) as authority:
        return _phase_finalize_locked(
            receipt_in_path, inventory_path, inventory_sha_path, db, user,
            container, probe_spec, authority, resume_only=True)


# ── phase: rollback (explicit) ───────────────────────────────────────────
def _phase_rollback_locked(receipt_in_path, inventory_path, inventory_sha_path, db,
                           user, container, probe_spec, execution_authority):
    receipt = _base_receipt("rollback", db, user, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    targets = _governed_identity_problems(db, user, container)
    if targets:
        return _blocked(receipt, "refusing recovery target: " + "; ".join(targets))
    try:
        promote, stamp, quarantine, staging, operation_id = _validated_transition_receipt(
            receipt_in_path, db, user, container, inventory_path, inventory_sha_path,
            "rollback")
        # Full receipt/state/identity authorization is complete under the OS
        # lock. Consume the one operation branch, then publish execution
        # metadata before any docker or catalog call exists to make.
        _claim_transition(operation_id, "rollback", promote)
        execution_authority.activate()
        floor = _floor_from_record(operation_id)
    except Exception as e:
        return _blocked(receipt, f"refusing recovery transition authority: {e}")
    receipt["stamp"] = stamp
    receipt["quarantine_database"] = quarantine
    receipt["rollback_required"] = True
    inventory = None
    probe = {}
    try:
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        probe = parse_probe_spec(probe_spec)
        ok, problems, detail = rollback_recovery(container, user, db, quarantine,
                                                 inventory, probe, floor=floor)
        receipt.update(detail)
        if not ok:
            receipt["rollback_error"] = "; ".join(problems)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 0 if ok else 1
        _record_transition(operation_id, "ROLLED_BACK" if ok else "FAILED", promote)
        return receipt
    except Exception as e:
        receipt["rollback_attempted"] = True
        receipt["rollback_succeeded"] = False
        receipt["rollback_failed"] = True
        receipt["original_canonical_restored"] = False
        receipt["rollback_error"] = str(e)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        _record_transition(operation_id, "FAILED", promote, extra={"error": str(e)})
        return receipt


def phase_rollback(receipt_in_path, inventory_path, inventory_sha_path, db,
                   user, container, probe_spec):
    try:
        promote, operation_id = _execution_receipt_binding(receipt_in_path)
    except Exception as exc:
        return _execution_binding_blocked(
            "rollback", receipt_in_path, inventory_path, db, user, container, exc)
    with _OperationExecutionAuthority(operation_id, "rollback", promote) as authority:
        return _phase_rollback_locked(
            receipt_in_path, inventory_path, inventory_sha_path, db, user,
            container, probe_spec, authority)


# ── phase: pre-intent rollback (finalize-claimed recovery) ─────────────
def phase_preintent_rollback(receipt_in_path, inventory_path, inventory_sha_path,
                             db, user, container, probe_spec):
    """Recover the selected finalize branch after death before forward intent."""
    receipt = _base_receipt("preintent-rollback", db, user, container,
                            inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    targets = _governed_identity_problems(db, user, container)
    if targets:
        return _blocked(receipt, "refusing recovery target: " + "; ".join(targets))
    try:
        (promote, _stamp, _quarantine, _staging,
         operation_id, _floor) = _validated_preintent_abort_receipt(
             receipt_in_path, db, user, container, inventory_path,
             inventory_sha_path)
    except Exception as e:
        return _blocked(receipt, f"refusing pre-intent abort authority: {e}")
    try:
        with _OperationExecutionAuthority(
                operation_id, "preintent-rollback", promote) as authority:
            # Re-validate after acquiring the OS lock: no finalize executor or
            # competing recovery process can mutate while this authority is held.
            (promote, stamp, quarantine, staging, operation_id,
             floor) = _validated_preintent_abort_receipt(
                 receipt_in_path, db, user, container, inventory_path,
                 inventory_sha_path)
            authority.activate()
            receipt.update({
                "stamp": stamp,
                "staging_database": staging,
                "quarantine_database": quarantine,
                "source_archive_sha256": promote.get("source_archive_sha256"),
                "promoted": True,
                "rollback_required": True,
                "rollback_attempted": True,
            })
            inventory = _load_protected_inventory(inventory_path,
                                                   inventory_sha_path)
            probe = parse_probe_spec(probe_spec)
            if not db_exists(container, user, quarantine):
                raise RuntimeError("pre-intent abort quarantine is missing")
            ok, problems, rows, fps = _verify_db(
                container, db, user, inventory, probe)
            receipt["canonical_verification"] = {
                "result": "ok" if ok else "failed", "tables": rows,
            }
            if fps is not None:
                receipt["canonical_verification"]["fingerprints"] = fps
            if not ok:
                raise RuntimeError("pre-intent canonical verification failed: "
                                   + "; ".join(problems))
            ok_rb, rb_problems, rb_detail = rollback_recovery(
                container, user, db, quarantine, inventory, probe, floor=floor)
            receipt.update(rb_detail)
            receipt["rollback_succeeded"] = ok_rb
            receipt["rollback_failed"] = not ok_rb
            if not ok_rb:
                receipt["rollback_error"] = "; ".join(rb_problems)
                raise RuntimeError(receipt["rollback_error"])
            _record_transition(
                operation_id, "ROLLED_BACK", promote,
                extra={"preintent_abort": {
                    "marker": "finalize_aborted_before_intent",
                    "operation_id": operation_id,
                    "receipt_sha256": _receipt_digest(promote),
                    "at": now_iso(),
                }})
            receipt["finished_at"] = now_iso()
            receipt["exit_status"] = 0
            return receipt
    except _ExecutionAuthorityConflict:
        # Execution-authority contention is not an operation receipt. Writing
        # one would make the loser mutate evidence despite being refused.
        raise
    except Exception as e:
        if not receipt.get("error"):
            receipt["error"] = str(e)
        receipt.setdefault("rollback_attempted", True)
        receipt.setdefault("rollback_succeeded", False)
        receipt.setdefault("rollback_failed", True)
        receipt.setdefault("original_canonical_restored", False)
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt


# ── phase: reconcile (crash recovery) ────────────────────────────────
def _quarantine_present(container, user, quarantine):
    return db_exists(container, user, quarantine)


def _canonical_matches_inventory(container, db, user, inventory, probe):
    ok, _problems, _rows, _fps = _verify_db(container, db, user, inventory, probe)
    return ok


def phase_reconcile(receipt_in_path, inventory_path, inventory_sha_path, db,
                    user, container, probe_spec):
    """B4-CXR7U9R40-R2: resolve an AMBIGUOUS restart without guessing.

    A crash/interrupt between PostgreSQL's irreversible commit point (the
    quarantine drop) and restore.sh's volatile `PG_FINALIZED=true` can leave
    the shell without commit knowledge. Reconciliation reads the DURABLE
    truth — the transition record, the quarantine's presence in the catalog,
    canonical-database content, and the receipt's own committed evidence —
    and reports the coherent result; it never mutates either store.
    """
    receipt = _base_receipt("reconcile", db, user, container, inventory_path)
    receipt["promote_receipt"] = receipt_in_path
    targets = _governed_identity_problems(db, user, container)
    if targets:
        return _blocked(receipt, "refusing recovery target: " + "; ".join(targets))
    try:
        # Read-only authority inspection: NO claim is taken, nothing consumed.
        promote = _load_receipt(receipt_in_path)
        if promote.get("operation_phase") != "promote" \
                or promote.get("exit_status") != 0:
            raise RuntimeError("reconcile requires a successful promote receipt")
        operation_id, record = _bound_operation(promote)
    except Exception as e:
        return _blocked(receipt, f"refusing reconcile authority: {e}")
    receipt["operation_id"] = operation_id
    state = record.get("state")
    receipt["durable_state"] = state
    try:
        inventory = _load_protected_inventory(inventory_path, inventory_sha_path)
        probe = parse_probe_spec(probe_spec)
    except Exception as e:
        receipt["error"] = f"reconcile could not verify its inputs: {e}"
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt
    quarantine = record.get("quarantine_database")
    # 1. Durable state and 2. catalog observation, fail-closed.
    observation = {"durable_state": state,
                   "quarantine_present": None,
                   "canonical_matches_inventory": None}
    try:
        observation["quarantine_present"] = \
            _quarantine_present(container, user, quarantine)
        observation["canonical_matches_inventory"] = \
            _canonical_matches_inventory(container, db, user, inventory, probe)
    except Exception as e:
        receipt["error"] = f"reconcile could not observe durable truth: {e}"
        receipt["observation"] = observation
        receipt["finished_at"] = now_iso()
        receipt["exit_status"] = 1
        return receipt
    receipt["observation"] = observation
    # 3. Decide WITHOUT guessing — every accepted combination is named here;
    #    anything else is reported as unreconciled and exits nonzero.
    if state in ("FINALIZED",):
        verdict = "committed"
    elif state == TRANSITION_STATE_COMMIT_INTENT:
        # The forward decision is durable. Whether DROP ran is not guessed from
        # volatile receipt fields: the catalog says whether resume must execute
        # it, and canonical content must still match in either case.
        if observation["canonical_matches_inventory"] is not True:
            verdict = "unreconciled"
        elif observation["quarantine_present"] in (True, False):
            verdict = "resume_required"
        else:
            verdict = "unreconciled"
    elif state == TRANSITION_STATE_COMMIT_POINT:
        if observation["quarantine_present"] is False \
                and observation["canonical_matches_inventory"] is True:
            verdict = "committed"
        else:
            verdict = "unreconciled"
    elif state == TRANSITION_STATE_FINALIZING:
        if observation["quarantine_present"] is True \
                and observation["canonical_matches_inventory"] is True:
            verdict = "preintent_abort_required"
        else:
            verdict = "unreconciled"
    elif state == TRANSITION_STATE_ROLLING_BACK:
        if observation["quarantine_present"] is True:
            verdict = "rolled_back_available"
        else:
            verdict = "unreconciled"
    elif state == TRANSITION_STATE_PROMOTED:
        verdict = "rolled_back_available"
    elif state in ("ROLLED_BACK", "FAILED"):
        verdict = "rolled_back" if state == "ROLLED_BACK" else "unreconciled"
    else:
        verdict = "unreconciled"
    receipt["verdict"] = verdict
    receipt["committed"] = verdict == "committed"
    receipt["finished_at"] = now_iso()
    receipt["exit_status"] = 0 if verdict in (
        "committed", "rolled_back", "rolled_back_available",
        "preintent_abort_required", "resume_required") else 1
    return receipt


def _classify_record_for_shell(record, promote=None):
    """The single rollback-legality law for both engine callers and the shell.

    Codes are deliberately small and stable: 0 means rollback is legal, 3 means
    the durable forward decision forbids it, and 4 means unknown/malformed and
    therefore fails closed. When a promote receipt is supplied, the operation
    record is also bound to that exact receipt and the intent is checked; the
    shell uses that form and never derives trust from a state label alone.
    """
    if not isinstance(record, dict) or record.get("format") not in (None, TRANSITION_FORMAT):
        return 4
    state = record.get("state")
    if state == TRANSITION_STATE_FINALIZING:
        # A commit marker in FINALIZING is impossible under the explicit ladder
        # (the old drop-before-record window). Never treat it as authority.
        if record.get("commit_intent") is not None or record.get("commit_point") is not None:
            return 4
        if record.get("selected_transition") == "finalize":
            return 5
        return 4
    if state in ("CREATED", "STAGED", TRANSITION_STATE_PROMOTED,
                 TRANSITION_STATE_ROLLING_BACK, "ROLLED_BACK", "FAILED"):
        if state == TRANSITION_STATE_ROLLING_BACK \
                and record.get("selected_transition") not in (None, "rollback"):
            return 4
        return 0
    if state == TRANSITION_STATE_COMMIT_INTENT:
        intent = record.get("commit_intent")
        if not isinstance(intent, dict) or intent.get("marker") != "forward_commit":
            return 4
        if promote is not None and not _valid_commit_intent(record, promote):
            return 4
        return 3
    if state in (TRANSITION_STATE_COMMIT_POINT, "FINALIZED"):
        if promote is not None and not _valid_commit_intent(record, promote):
            return 4
        commit_point = record.get("commit_point")
        if not isinstance(commit_point, dict) \
                or commit_point.get("marker") != "quarantine_dropped":
            return 4
        return 3
    return 4


def _classify_state_for_shell(path):
    """Classify a transition record without docker; malformed means fail closed."""
    try:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, ValueError):
        return 4
    return _classify_record_for_shell(record)


def _classify_rollback_for_shell(receipt_path, transition_dir=None):
    """Bind the shell's legality decision to the exact promote receipt."""
    try:
        promote = _load_receipt(receipt_path)
        if not isinstance(promote, dict) \
                or promote.get("format") != RECEIPT_FORMAT \
                or promote.get("operation_phase") != "promote" \
                or promote.get("exit_status") != 0 \
                or promote.get("promoted") is not True:
            return 4
        _operation_id, record = _bound_operation(
            promote, transition_dir=transition_dir)
        return _classify_record_for_shell(record, promote)
    except (OSError, ValueError, RuntimeError, TypeError):
        return 4


def _parse_cli(argv):
    """Parse the recovery CLI into (phase, probe, kw). Exits 2 on unknown args."""
    kw = {}
    phase = None
    probe = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--phase", "--archive", "--inventory", "--inventory-sha", "--db",
                 "--user", "--container", "--receipt-out", "--receipt-in",
                 "--verify-tables", "--classify-state", "--classify-rollback",
                 "--transition-dir"):
            i += 1
            val = argv[i] if i < len(argv) else None
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
    return phase, probe, kw


def _validate_cli(phase, kw):
    """Fail closed on incomplete recovery invocations (usage errors, exit 2)."""
    if phase not in ("promote", "finalize", "resume-finalize",
                     "preintent-rollback", "rollback", "reconcile"):
        print("USAGE_ERROR: --phase <promote|finalize|resume-finalize|preintent-rollback|rollback|reconcile> required",
              file=sys.stderr)
        sys.exit(2)
    if not kw.get("inventory") or not kw.get("inventory_sha"):
        print("USAGE_ERROR: --inventory and --inventory-sha required", file=sys.stderr)
        sys.exit(2)
    if phase == "promote" and not kw.get("archive"):
        print("USAGE_ERROR: --phase promote requires --archive", file=sys.stderr)
        sys.exit(2)
    if phase in ("finalize", "resume-finalize", "preintent-rollback",
                 "rollback", "reconcile") and not kw.get("receipt_in"):
        print(f"USAGE_ERROR: --phase {phase} requires --receipt-in", file=sys.stderr)
        sys.exit(2)
    targets = _governed_identity_problems(kw.get("db", DB), kw.get("user", USER),
                                          kw.get("container", CONTAINER))
    if targets:
        print("USAGE_ERROR: recovery targets are governed: " + "; ".join(targets),
              file=sys.stderr)
        sys.exit(2)
    in_path, out_path = kw.get("receipt_in"), kw.get("receipt_out")
    if in_path and out_path and os.path.realpath(in_path) == os.path.realpath(out_path):
        # A receipt is evidence: it may not be both the authority for a
        # transition and the file that transition rewrites.
        print("USAGE_ERROR: --receipt-in and --receipt-out are the same file; "
              "a receipt cannot be its own output", file=sys.stderr)
        sys.exit(2)


def main():
    phase, probe, kw = _parse_cli(sys.argv[1:])
    # Shell-support mode (B4-CXR7U9R41-R2): classify a durable transition
    # record by exit code, no docker/catalog access. Not a recovery phase.
    if kw.get("classify_state"):
        sys.exit(_classify_state_for_shell(kw["classify_state"]))
    if kw.get("classify_rollback"):
        sys.exit(_classify_rollback_for_shell(
            kw["classify_rollback"], kw.get("transition_dir")))
    _validate_cli(phase, kw)
    out = kw.get("receipt_out")
    if out:
        try:
            out = _validated_write_path(out)
        except RuntimeError as e:
            print(f"USAGE_ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        if os.path.exists(out):
            # Preflight: a receipt is evidence, so an existing one is refused
            # BEFORE any destructive step runs, not after it.
            print("USAGE_ERROR: refusing to overwrite an existing receipt: "
                  f"{out}", file=sys.stderr)
            sys.exit(2)
    # the destructive destination is the governed identity, full stop
    db, user, container = DB, USER, CONTAINER
    try:
        if phase == "promote":
            receipt = phase_promote(kw["archive"], kw["inventory"],
                                    kw["inventory_sha"], db, user, container, probe)
        elif phase == "finalize":
            receipt = phase_finalize(kw["receipt_in"], kw["inventory"],
                                     kw["inventory_sha"], db, user, container, probe)
        elif phase == "resume-finalize":
            receipt = phase_resume_finalize(
                kw["receipt_in"], kw["inventory"], kw["inventory_sha"], db, user,
                container, probe)
        elif phase == "preintent-rollback":
            receipt = phase_preintent_rollback(
                kw["receipt_in"], kw["inventory"], kw["inventory_sha"], db, user,
                container, probe)
        elif phase == "reconcile":
            receipt = phase_reconcile(
                kw["receipt_in"], kw["inventory"], kw["inventory_sha"], db, user,
                container, probe)
        else:
            receipt = phase_rollback(
                kw["receipt_in"], kw["inventory"], kw["inventory_sha"], db, user,
                container, probe)
    except _ExecutionAuthorityConflict as e:
        # A refused contender must not write a phase receipt: it owns no
        # operation mutation interval and therefore owns no new evidence.
        print("BLOCKED:", e, file=sys.stderr)
        sys.exit(1)
    if out:
        try:
            _commit_receipt(out, receipt)
        except Exception as e:  # the operation ran: a lost receipt is BLOCKED, not silent
            print(f"BLOCKED: cannot commit receipt {out}: {e}", file=sys.stderr)
            sys.exit(1)
        print("receipt ->", out)
    if receipt.get("exit_status") != 0:
        print("BLOCKED:", receipt.get("error", f"postgres {phase} failed"),
              file=sys.stderr)
        sys.exit(1)
    print(f"postgres {phase} complete")


if __name__ == "__main__":
    main()
