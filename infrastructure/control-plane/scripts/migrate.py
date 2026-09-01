#!/usr/bin/env python3
"""OCE Control Plane migration runner (B2-R2 / B4-CXR3R2).

Numbered, reversible migrations against PostgreSQL. Fail-closed on:
missing migration, out-of-order version, checksum mismatch, partial apply.

B4-CXR3R2: ``--db`` is REQUIRED and must target the governed loopback
PostgreSQL (127.0.0.1/localhost only). There is no predictable default
DSN and migrations can never be redirected to an external database.

Usage:
  migrate.py up     --db DSN [--dir DIR]
  migrate.py down   --db DSN [--dir DIR]   # rollback latest applied
  migrate.py status --db DSN [--dir DIR]
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

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
# B4-CXR3R2: migrations must target the governed loopback PostgreSQL only.
# There is deliberately no predictable default DSN and no external-DB escape.
LOOPBACK_HOSTS = ("127.0.0.1", "localhost")
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


def _dsn_host(dsn: str) -> str:
    """Extract the host from a postgresql:// DSN (userinfo ignored)."""
    rest = dsn.split("://", 1)[1] if "://" in dsn else dsn
    rest = rest.split("/", 1)[0]          # drop the database path
    hostport = rest.rsplit("@", 1)[-1]    # drop userinfo (last @ wins)
    return hostport.rsplit(":", 1)[0] if ":" in hostport else hostport


def main() -> int:
    parser = argparse.ArgumentParser(description="OCE control-plane migrations")
    parser.add_argument("command", choices=["up", "down", "status"])
    parser.add_argument("--db", required=True,
                        help="PostgreSQL DSN (governed, loopback-only)")
    parser.add_argument("--dir", type=Path, default=MIGRATIONS_DIR)
    args = parser.parse_args()
    # B4-CXR3R2: fail closed before ANY connection when --db targets a
    # non-loopback host — migrations can never be redirected outside the
    # governed local database.
    if _dsn_host(args.db) not in LOOPBACK_HOSTS:
        print("FAIL: --db must target the governed loopback PostgreSQL "
              "(127.0.0.1/localhost only); external DB redirection is "
              "rejected (B4-CXR3R2)", file=sys.stderr)
        return 2
    if args.command == "up":
        return cmd_up(args.db, args.dir)
    if args.command == "down":
        return cmd_down(args.db, args.dir)
    return cmd_status(args.db, args.dir)


if __name__ == "__main__":
    sys.exit(main())
