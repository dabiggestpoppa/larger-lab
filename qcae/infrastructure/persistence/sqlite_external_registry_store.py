"""SQLite persistence for A-001 cross-registry references (reconciliation §7,
P1 spec §12).

External registry references are durable, append-only, and owner-pinned:

- the (registry, external_id) pair is the natural key — one reference record
  per external object;
- ``owner_domain`` is part of the identity: a reference claiming the same
  external object under a *different* owner is rejected as an ownership
  rewrite (no silent laundering of external knowledge into QCAE-owned);
- no lifecycle mutation API exists: QCAE observes/submits, never governs
  (A-001 §6).
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.amendments.a001.external_registry import ExternalRegistryRef
from qcae.core.errors import QcaeValidationError

__all__ = ["SqliteExternalRegistryRefRepository", "EXTERNAL_REGISTRY_DDL"]

EXTERNAL_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS external_registry_ref (
    registry       TEXT NOT NULL,
    external_id    TEXT NOT NULL,
    owner_domain   TEXT NOT NULL,
    payload_json   TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    PRIMARY KEY (registry, external_id)
);
CREATE INDEX IF NOT EXISTS ix_extref_owner ON external_registry_ref(owner_domain);
"""


class SqliteExternalRegistryRefRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, ref: ExternalRegistryRef) -> None:
        ref.validate()
        payload = json.dumps(ref.to_dict(), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO external_registry_ref (registry, external_id, owner_domain,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?, ?)",
                (ref.registry.value, ref.external_id, ref.owner_domain, payload,
                 ref.digest()),
            )
        except sqlite3.IntegrityError as exc:
            existing = self.get(registry_value=ref.registry.value, external_id=ref.external_id)
            if existing is not None:
                if existing.owner_domain != ref.owner_domain:
                    raise QcaeValidationError(
                        f"external ref {ref.external_id!r} is owned by "
                        f"{existing.owner_domain!r}; re-registering under "
                        f"{ref.owner_domain!r} is an ownership rewrite (A-001 §6)"
                    ) from exc
                if existing.digest() == ref.digest():
                    return  # idempotent re-add of identical reference
                raise QcaeValidationError(
                    f"external ref {ref.external_id!r} already stored with different "
                    "metadata; store the updated reference as a new record "
                    "(append-only)"
                ) from exc
            raise QcaeValidationError(f"external ref rejected: {exc}") from exc

    def get(self, external_id: str, registry_value: str = "") -> Optional[ExternalRegistryRef]:
        where = "external_id = ?" + (" AND registry = ?" if registry_value else "")
        params: tuple = (external_id, registry_value) if registry_value else (external_id,)
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM external_registry_ref WHERE " + where,
            params,
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        ref = ExternalRegistryRef.from_dict(data)
        if ref.digest() != row[1]:
            raise QcaeValidationError(
                f"external ref {external_id!r} failed integrity check"
            )
        return ref

    def list_by_owner(self, owner_domain: str) -> List[ExternalRegistryRef]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM external_registry_ref"
            " WHERE owner_domain = ? ORDER BY registry, external_id",
            (owner_domain,),
        ).fetchall()
        return [ExternalRegistryRef.from_dict(json.loads(r[0])) for r in rows]

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM external_registry_ref").fetchone()
        return int(row[0])
