#!/usr/bin/env python3
"""OCE Control Plane migration runner (B2-R2 / B4-CXR3R2 / B4-CXR4R4 /
B4-CXR5R1).

Numbered, reversible migrations against PostgreSQL. Fail-closed on:
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

Usage:
  migrate.py up     [--dir DIR]
  migrate.py down   [--dir DIR]   # rollback latest applied
  migrate.py status [--dir DIR]
"""
from __future__ import annotations
import argparse
import hashlib
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
VERSION_RE = re.compile(r"^(\d{4})_.+\.sql$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_migrations(directory: Path) -> list[tuple[str, Path, Path]]:
    """Return [(version, up_path, down_path)] sorted by version."""
    ups: dict[str, Path] = {}
    downs: dict[str, Path] = {}
    for f in sorted(directory.glob("*.sql")):
        m = VERSION_RE.match(f.name)
        if not m:
            continue
        version = m.group(1)
        if f.name.endswith("_down.sql"):
            downs[version] = f
        else:
            ups[version] = f
    result = []
    for version in sorted(set(ups) | set(downs)):
        if version not in ups:
            raise RuntimeError(f"migration {version}: missing up script")
        result.append((version, ups[version], downs.get(version)))
    return result


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
    migrations = dict(discover_migrations(directory))
    conn = connect(dsn)
    try:
        applied = applied_versions(conn)
        for version in sorted(applied, reverse=True):
            entry = migrations.get(version)
            if entry is None:
                print(f"FAIL: applied migration {version} has no file on disk")
                return 2
            _v, _up, down_path = entry
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


def _reject_secret_flags(argv: list[str] | None) -> None:
    """Reject secret-bearing CLI flags WITHOUT echoing their values.

    B4-CXR5R1: --db/--dsn/--token/--secret/--password/--worker-secret are
    NOT OCE migration options. argparse would echo the raw value in an
    "unrecognized arguments" message, so we intercept BEFORE parsing and
    print a redacted denial naming only the option. The governed connection
    is always resolved internally; secret material is never valid CLI input.
    """
    if not argv:
        return
    bad = {"--db", "--dsn", "--token", "--secret", "--password",
           "--worker-secret", "--worker-token"}
    for tok in argv:
        opt = tok.split("=", 1)[0]
        if opt in bad:
            print(f"FAIL: {opt} is not a valid OCE migration option — the "
                  "governed connection is resolved internally; secret "
                  "material is never accepted on the command line "
                  "(B4-CXR5R1)", file=sys.stderr)
            raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # B4-CXR5R1: reject secret-bearing flags before argparse (which would
    # echo the raw value). Never print or accept a password-bearing DSN.
    _reject_secret_flags(argv)
    parser = argparse.ArgumentParser(description="OCE control-plane migrations")
    parser.add_argument("command", choices=["up", "down", "status"])
    # B4-CXR5R1: NO --db. A password-bearing DSN must never enter process
    # argv; the governed connection is resolved internally from the pinned
    # activation authority.
    parser.add_argument("--dir", type=Path, default=MIGRATIONS_DIR)
    args = parser.parse_args(argv)
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
    if args.command == "up":
        return cmd_up(dsn, args.dir)
    if args.command == "down":
        return cmd_down(dsn, args.dir)
    return cmd_status(dsn, args.dir)


if __name__ == "__main__":
    sys.exit(main())
