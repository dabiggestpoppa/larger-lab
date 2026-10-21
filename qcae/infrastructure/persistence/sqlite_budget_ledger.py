"""SQLite budget ledger (P2-C08 adapter; engine code stays in infrastructure).

Budgets are mutable operational state (canon permits this for current state;
historical truth remains in the event log), but rows still carry an integrity
digest so tampering is detected on read.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Optional

from qcae.core.errors import QcaeValidationError
from qcae.orchestration.orchestrator.budgets import Budget

__all__ = ["SqliteBudgetLedger", "BUDGET_DDL"]

BUDGET_DDL = """
CREATE TABLE IF NOT EXISTS runtime_budget (
    budget_id         TEXT PRIMARY KEY,
    owner_kind        TEXT NOT NULL,
    owner_id          TEXT NOT NULL,
    parent_budget_id  TEXT NOT NULL DEFAULT '',
    state             TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_budget_owner ON runtime_budget(owner_id);
"""


def _encode(budget: Budget) -> tuple:
    payload = json.dumps(budget.to_dict(), ensure_ascii=False, sort_keys=True)
    return payload, budget.digest()


def _decode(payload_json: str, payload_digest: str, key: str) -> Budget:
    budget = Budget.from_dict(json.loads(payload_json))
    if budget.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored Budget {key!r} failed integrity check (digest mismatch)"
        )
    return budget


class SqliteBudgetLedger:
    """Upsert-style operational ledger with row integrity on read."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, budget: Budget) -> None:
        payload, digest = _encode(budget)
        self._conn.execute(
            "INSERT INTO runtime_budget (budget_id, owner_kind, owner_id,"
            " parent_budget_id, state, payload_json, payload_digest)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(budget_id) DO UPDATE SET"
            " owner_kind=excluded.owner_kind, owner_id=excluded.owner_id,"
            " parent_budget_id=excluded.parent_budget_id, state=excluded.state,"
            " payload_json=excluded.payload_json, payload_digest=excluded.payload_digest",
            (
                budget.budget_id,
                budget.owner_kind,
                budget.owner_id,
                budget.parent_budget_id,
                budget.state.value,
                payload,
                digest,
            ),
        )

    def get(self, budget_id: str) -> Optional[Budget]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_budget"
            " WHERE budget_id = ?",
            (budget_id,),
        ).fetchone()
        return _decode(row[0], row[1], budget_id) if row else None

    def delete(self, budget_id: str) -> None:
        self._conn.execute(
            "DELETE FROM runtime_budget WHERE budget_id = ?", (budget_id,)
        )
