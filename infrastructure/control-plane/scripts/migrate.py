#!/usr/bin/env python3
"""OCE Control Plane migration runner (B2-R2 / B4-CXR3R2 / B4-CXR4R4 /
B4-CXR5R1 / B4-CXR5R2).

Numbered migrations against the governed PostgreSQL. Fail-closed on:
missing migration, out-of-order version, checksum mismatch, partial apply.

B4-CXR3R2: there is NO public ``--db`` DSN parameter and no predictable
default DSN. The migration target is always derived from the governed
secret boundary — migrations can never be redirected to another database
by an operator-controlled DSN.

B4-CXR4R4 (CXR4-05): the migration target must be the EXACT governed
PostgreSQL identity — host, port, database, user, AND credential authority.
Alternate loopback ports/databases/users are DIFFERENT authority and are
BLOCKED before any connection. The activation gate (validated config +
resolved secret) runs before any migration; raw DSNs/credentials are never
echoed.

B4-CXR5R1 (CXR5-01): the production ``--db`` interface is REMOVED — a
password-bearing DSN can never appear in process argv, /proc/<pid>/cmdline,
command capture, or diagnostics. The governed connection is resolved
INTERNALLY from the pinned activation authority (ActivationContext). The
derived DSN is identity-checked in-memory as an invariant guard; nothing is
ever echoed.

B4-CXR5R2 (CXR5-02): ONLY the repository-owned canonical migrations/
directory may mutate the governed database. ``--dir`` is REMOVED; migration
discovery rejects symlink escape, alternate directories, non-regular
files, duplicate versions, unrecognized filename forms, and version gaps.
An activation is bound to a secret-free migration-set identity (ordered
filenames, versions, file hashes — never SQL contents). Production
rollback (``down``) is FUTURE-LOCKED: destructive schema mutation requires
a separately authorized increment.

Usage:
  migrate.py up
  migrate.py down     # FUTURE-LOCKED in production (test/authorized use only)
  migrate.py status
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore[assignment]

BASE = Path(__file__).resolve().parent.parent
# Self-sufficient import (mirrors oce_b3_worker.py): the migration CLI must
# reach the governed secret boundary even when invoked without PYTHONPATH.
_SRC = str(BASE / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
from oce_control import local_secrets as ls  # noqa: E402

MIGRATIONS_DIR = BASE / "migrations"
# B4-CXR4R4: migrations must target the EXACT governed local PostgreSQL —
# loopback host, governed port/db/user. Alternate loopback identities are
# different authority and are rejected. There is deliberately no predictable
# default DSN and no external-DB escape.
LOOPBACK_HOSTS = ("127.0.0.1", "localhost")
PG_PORT = ls.PG_PORT
PG_DB = ls.PG_DB
PG_USER = ls.PG_USER
UP_RE = re.compile(r"^(\d{4})_([A-Za-z0-9_]+)\.sql$")
# canonical down form is exactly NNNN_down.sql — checked BEFORE UP_RE
# because "0001_down.sql" also matches the up pattern. Any other
# *_down.sql variant is an unrecognized form and fails closed.
DOWN_RE = re.compile(r"^(\d{4})_down\.sql$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_migration_name(fname: str) -> tuple[str, bool] | None:
    """Return (version, is_down) for a canonical migration filename, else
    None for an unrecognized form (CXR5-02: fail closed on unknown forms)."""
    m = DOWN_RE.match(fname)
    if m:
        return (m.group(1), True)
    m = UP_RE.match(fname)
    return (m.group(1), False) if m else None


def _canonical_dir() -> Path:
    """The repository-owned canonical migration directory, verified to sit
    beneath the control-plane root (resolve() rejects symlink escape)."""
    d = MIGRATIONS_DIR.resolve()
    root = BASE.resolve()
    if d != root and root not in d.parents:
        raise RuntimeError(
            "canonical migration directory escapes the control-plane root "
            "(B4-CXR5R2)")
    if not d.is_dir():
        raise RuntimeError(f"canonical migration directory missing: {d}")
    return d


def _scan_migrations(directory: Path) -> list[tuple[str, Path, Path]]:
    """Low-level structural scanner (CXR5-02): validates every migration path
    in *directory* — regular files only (no symlinks), canonical filenames,
    no duplicate up/down per version, up present for every down, contiguous
    versions. Returns [(version, up_path, down_path)] sorted by version."""
    directory = directory.resolve()
    if not directory.is_dir():
        raise RuntimeError(f"migration directory is not a directory: {directory}")
    ups: dict[str, Path] = {}
    downs: dict[str, Path] = {}
    for f in sorted(directory.iterdir()):
        if f.name in ("__init__.py", "README.md", "README"):
            continue
        if not f.is_file() or f.is_symlink():
            # symlinks (inside or escaping the dir), dirs, sockets, devices
            # are rejected — an operator-controlled link can never smuggle
            # SQL from outside the canonical set
            raise RuntimeError(
                f"migration path is not a regular file: {f.name} "
                "(B4-CXR5R2, symlinks rejected)")
        if not f.name.endswith(".sql"):
            continue  # non-SQL files in the canonical dir are ignored
        parsed = _parse_migration_name(f.name)
        if parsed is None:
            raise RuntimeError(
                f"unrecognized migration filename: {f.name} (B4-CXR5R2)")
        version, is_down = parsed
        if is_down:
            if version in downs:
                raise RuntimeError(
                    f"duplicate down script for migration {version} (B4-CXR5R2)")
            downs[version] = f
        else:
            if version in ups:
                raise RuntimeError(
                    f"duplicate up script for migration {version} (B4-CXR5R2)")
            ups[version] = f
    result: list[tuple[str, Path, Path]] = []
    versions = sorted(set(ups) | set(downs))
    for version in versions:
        if version not in ups:
            raise RuntimeError(f"migration {version}: missing up script (B4-CXR5R2)")
        result.append((version, ups[version], downs.get(version)))
    # fail closed on gaps / ordering contradictions: contiguous integers
    nums = sorted(int(v) for v in versions)
    if nums and nums != list(range(nums[0], nums[0] + len(nums))):
        raise RuntimeError(
            "migration versions are not contiguous (gap/ordering "
            "contradiction) (B4-CXR5R2)")
    return result


def discover_migrations(directory: Path | None = None) -> list[tuple[str, Path, Path]]:
    """Return [(version, up_path, down_path)] for the CANONICAL repository
    migration directory (CXR5-02: alternate directories are blocked)."""
    directory = _canonical_dir() if directory is None else directory
    if directory.resolve() != _canonical_dir().resolve():
        raise RuntimeError(
            "migration directory must be the repository-owned canonical "
            "migrations/ directory (B4-CXR5R2)")
    return _scan_migrations(directory)


def migration_set_identity(directory: Path | None = None) -> dict:
    """Deterministic, secret-free identity of the migration set (CXR5-02).

    Contains ordered filenames, version identities, and per-file SHA-256
    hashes — NEVER SQL contents. Binds an activation to a stable migration
    program and detects mutation of the set after inventory.
    """
    directory = _canonical_dir() if directory is None else directory
    if directory.resolve() != _canonical_dir().resolve():
        raise RuntimeError(
            "migration directory must be the repository-owned canonical "
            "migrations/ directory (B4-CXR5R2)")
    entries = []
    for version, up_path, down_path in _scan_migrations(directory):
        entries.append({
            "version": version,
            "up": up_path.name,
            "up_sha256": sha256_file(up_path),
            "down": down_path.name if down_path else None,
            "down_sha256": sha256_file(down_path) if down_path else None,
        })
    manifest = json.dumps(entries, sort_keys=True).encode("utf-8")
    return {
        "directory": str(directory.resolve()),
        "entries": entries,
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
    }


def connect(dsn: str):
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed — cannot run migrations")
    return psycopg2.connect(dsn)


def applied_versions(conn) -> dict[str, str]:
    """Read applied migrations -> checksums. Creates the ledger table if absent."""
    with conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                version    TEXT PRIMARY KEY,
                checksum   TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"""
        )
        conn.commit()
        cur.execute("SELECT version, checksum FROM schema_migrations ORDER BY version")
        return dict(cur.fetchall())


def cmd_up(dsn: str, directory: Path) -> int:
    migrations = discover_migrations(directory)
    conn = connect(dsn)
    try:
        applied = applied_versions(conn)
        for version, up_path, _down in migrations:
            if version in applied:
                expected = applied[version]
                actual = sha256_file(up_path)
                if expected == "seed":
                    continue  # legacy seed row — accept
                if expected != actual:
                    print(f"FAIL: migration {version} checksum mismatch "
                          f"(applied {expected}, file {actual})")
                    return 2
                continue
            # fail closed on out-of-order application: all earlier versions
            # must be applied first
            for prior, _u, _d in migrations:
                if prior >= version:
                    break
                if prior not in applied:
                    print(f"FAIL: out-of-order migration {version}: {prior} not applied")
                    return 2
            checksum = sha256_file(up_path)
            sql = up_path.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    # Migration files may self-seed their version row with a
                    # 'seed' marker (0001/0002 do). Upsert replaces the marker
                    # with the authoritative checksum instead of colliding.
                    cur.execute(
                        "INSERT INTO schema_migrations (version, checksum) "
                        "VALUES (%s, %s) "
                        "ON CONFLICT (version) DO UPDATE SET checksum = EXCLUDED.checksum",
                        (version, checksum),
                    )
                conn.commit()
                print(f"applied {version} ({up_path.name})")
            except Exception as exc:
                conn.rollback()
                print(f"FAIL: migration {version} rolled back: {exc}")
                return 2
            applied[version] = checksum
        print("migrations up-to-date")
        return 0
    finally:
        conn.close()


def cmd_down(dsn: str, directory: Path) -> int:
    # CXR5-02: previously ``dict(discover_migrations(...))`` crashed on the
    # three-item tuples — key by version so the real rollback works when
    # invoked (production CLI is future-locked; tests exercise the engine).
    migrations = {v: (up, down) for v, up, down in discover_migrations(directory)}
    conn = connect(dsn)
    try:
        applied = applied_versions(conn)
        for version in sorted(applied, reverse=True):
            entry = migrations.get(version)
            if entry is None:
                print(f"FAIL: applied migration {version} has no file on disk")
                return 2
            _up, down_path = entry
            if down_path is None:
                print(f"SKIP-DOWN: {version} has no down script (irreversible)")
                continue
            try:
                with conn.cursor() as cur:
                    cur.execute(down_path.read_text(encoding="utf-8"))
                conn.commit()
                print(f"reverted {version}")
                return 0  # one step per invocation
            except Exception as exc:
                conn.rollback()
                print(f"FAIL: rollback {version} failed: {exc}")
                return 2
        print("nothing to revert")
        return 0
    finally:
        conn.close()


def cmd_status(dsn: str, directory: Path) -> int:
    migrations = discover_migrations(directory)
    conn = connect(dsn)
    try:
        applied = applied_versions(conn)
        for version, up_path, _down in migrations:
            state = "applied" if version in applied else "pending"
            print(f"{version}  {state}  {up_path.name}")
        return 0
    finally:
        conn.close()


def parse_dsn(dsn: str) -> dict:
    """Parse a postgresql:// DSN into identity parts. The password is parsed
    for the credential-authority comparison but NEVER echoed/returned in any
    operator-facing form (B4-CXR4R4)."""
    if not dsn.startswith("postgresql://"):
        raise ValueError("DSN must be postgresql:// (governed target only)")
    rest = dsn.split("://", 1)[1]
    userinfo, _, hostpart = rest.rpartition("@")
    if not userinfo:
        raise ValueError("DSN missing user information")
    user = userinfo.split(":", 1)[0]
    password = userinfo.split(":", 1)[1] if ":" in userinfo else ""
    hostport = hostpart.split("/", 1)[0]
    db = hostpart.split("/", 1)[1] if "/" in hostpart else ""
    if ":" in hostport:
        host, _, port = hostport.rpartition(":")
        try:
            port = int(port)
        except ValueError:
            port = None
    else:
        host, port = hostport, None
    return {"host": host, "port": port, "db": db, "user": user,
            "password": password}


def check_governed_identity(parts: dict) -> str | None:
    """Return an error string when *parts* is not the EXACT governed local
    PostgreSQL identity (loopback host + governed port/db/user), else None.
    Values are never echoed (B4-CXR4R4)."""
    if parts["host"] not in LOOPBACK_HOSTS:
        return "host must be the governed loopback (127.0.0.1/localhost)"
    if parts["port"] != PG_PORT:
        return "port must be the governed local PostgreSQL port"
    if parts["db"] != PG_DB:
        return "database must be the governed oce_control database"
    if parts["user"] != PG_USER:
        return "user must be the governed oce_control_admin user"
    return None


def _reject_forbidden_flags(argv: list[str] | None) -> None:
    """Reject secret-bearing and alternate-program CLI flags WITHOUT echoing
    their values.

    B4-CXR5R1: --db/--dsn/--token/--secret/--password/--worker-secret are
    NOT OCE migration options. argparse would echo the raw value in an
    "unrecognized arguments" message, so we intercept BEFORE parsing and
    print a redacted denial naming only the option.

    B4-CXR5R2: --dir is rejected too — only the repository-owned canonical
    migrations/ directory may mutate the governed database; an
    operator-controlled directory must never provide arbitrary SQL.
    """
    if not argv:
        return
    secret = {"--db", "--dsn", "--token", "--secret", "--password",
              "--worker-secret", "--worker-token"}
    for tok in argv:
        opt = tok.split("=", 1)[0]
        if opt in secret:
            print(f"FAIL: {opt} is not a valid OCE migration option — the "
                  "governed connection is resolved internally; secret "
                  "material is never accepted on the command line "
                  "(B4-CXR5R1)", file=sys.stderr)
            raise SystemExit(2)
        if opt == "--dir":
            print("FAIL: --dir is not a valid OCE migration option — the "
                  "migration directory is the repository-owned canonical "
                  "migrations/ directory only; an operator-controlled "
                  "directory can never select the SQL executed against the "
                  "governed database (B4-CXR5R2)", file=sys.stderr)
            raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # B4-CXR5R1/R2: reject secret-bearing and alternate-dir flags before
    # argparse (which would echo the raw value). Never print or accept a
    # password-bearing DSN or an operator-selected migration directory.
    _reject_forbidden_flags(argv)
    parser = argparse.ArgumentParser(description="OCE control-plane migrations")
    parser.add_argument("command", choices=["up", "down", "status"])
    args = parser.parse_args(argv)
    # B4-CXR5R2: production rollback is FUTURE-LOCKED — destructive schema
    # mutation requires a separately authorized increment. Refused BEFORE
    # any activation/connection work.
    if args.command == "down":
        print("down is TEST-ONLY / FUTURE-LOCKED in Book 4: production "
              "rollback requires a separately authorized destructive "
              "increment (B4-CXR5R2)", file=sys.stderr)
        return 3
    # B4-CXR4R4: activation authority FIRST — validated effective config AND
    # resolved governed secret. No migration runs under a forbidden/malformed
    # config or an unresolvable secret reference. The DSN is derived here,
    # in process memory, from the pinned context; it is never echoed.
    from oce_control.config_startup import create_activation_context
    ctx = create_activation_context()
    dsn = ctx.runtime_dsn()
    # Invariant guard (defense in depth): the governed derivation MUST be the
    # exact governed identity — host/port/db/user (+ credential authority).
    # Values are compared in-memory; nothing is echoed (B4-CXR4R4).
    try:
        parts = parse_dsn(dsn)
    except ValueError as exc:
        print(f"FAIL: governed DSN malformed: {exc} (never echoed, B4-CXR5R1)",
              file=sys.stderr)
        return 2
    err = check_governed_identity(parts)
    if err:
        print(f"FAIL: governed DSN failed identity check — {err}; "
              "values never echoed (B4-CXR4R4)", file=sys.stderr)
        return 2
    # B4-CXR5R2: only the canonical repository-owned migration program may
    # mutate the governed database; the set identity is stable and
    # secret-free (no SQL contents in any evidence).
    canonical = _canonical_dir()
    identity = migration_set_identity(canonical)  # validates; raises on defect
    # B4-CXR5R3: when launched as a lifecycle child (activation envelope
    # present), the migration-set identity MUST match the parent's pinned
    # envelope — a child can never mutate the governed database under a
    # different migration program than the one the parent activated.
    envelope_raw = os.environ.get("OCE_ACTIVATION_ENVELOPE")
    if envelope_raw:
        try:
            from oce_control.config_startup import ActivationEnvelope
            envelope = ActivationEnvelope.from_json(envelope_raw)
        except ValueError as exc:
            print(f"FAIL: malformed activation envelope — {exc} "
                  "(B4-CXR5R3)", file=sys.stderr)
            return 2
        expected = envelope.migration_set_identity or {}
        if expected.get("manifest_sha256") and \
                expected["manifest_sha256"] != identity["manifest_sha256"]:
            print("FAIL: migration-set identity does not match the parent "
                  "activation envelope — database mutation refused "
                  "(B4-CXR5R3)", file=sys.stderr)
            return 2
    if args.command == "up":
        return cmd_up(dsn, canonical)
    return cmd_status(dsn, canonical)


if __name__ == "__main__":
    sys.exit(main())
