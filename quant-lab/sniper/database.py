"""
Prop Firm Sniper — SQLite Database
3 tables: prop_firms, capital_deployments, pes_snapshots
"""

import sqlite3
import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "sniper.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS prop_firms (
            firm_id         TEXT PRIMARY KEY,
            name            TEXT NOT NULL UNIQUE,
            website         TEXT,
            account_sizes   TEXT NOT NULL DEFAULT '[]',
            cost_per_size   TEXT NOT NULL DEFAULT '{}',
            promo_active    TEXT,
            max_daily_loss_pct      REAL NOT NULL DEFAULT 0.05,
            max_trailing_dd_pct     REAL NOT NULL DEFAULT 0.06,
            consistency_rule        TEXT NOT NULL DEFAULT '{}',
            min_trading_days        INTEGER NOT NULL DEFAULT 5,
            payout_cycle_days       INTEGER NOT NULL DEFAULT 14,
            payout_buffer_days      INTEGER NOT NULL DEFAULT 3,
            payout_method           TEXT DEFAULT 'Crypto',
            scaling_rules           TEXT NOT NULL DEFAULT '{}',
            allowed_instruments     TEXT NOT NULL DEFAULT '[]',
            news_restrictions       INTEGER DEFAULT 0,
            ff_status               TEXT DEFAULT 'UNTESTED',
            patch_signals           TEXT DEFAULT '[]',
            last_updated            TEXT NOT NULL,
            status                  TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at              TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS capital_deployments (
            deployment_id       TEXT PRIMARY KEY,
            firm_id             TEXT NOT NULL REFERENCES prop_firms(firm_id),
            account_size        INTEGER NOT NULL,
            quantity            INTEGER NOT NULL DEFAULT 1,
            total_cost          REAL NOT NULL,
            total_risk_capital  REAL NOT NULL,
            pes_score           REAL NOT NULL,
            effective_exposure  REAL NOT NULL,
            capital_velocity    REAL NOT NULL,
            crossover_threshold REAL NOT NULL,
            equivalent_live_leverage REAL,
            deployed_at         TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'ACTIVE',
            config_version      INTEGER DEFAULT 1,
            notes               TEXT
        );

        CREATE TABLE IF NOT EXISTS pes_snapshots (
            snapshot_id         TEXT PRIMARY KEY,
            snapshot_date       TEXT NOT NULL,
            firm_id             TEXT NOT NULL REFERENCES prop_firms(firm_id),
            account_size        INTEGER NOT NULL,
            pes_score           REAL NOT NULL,
            effective_leverage  REAL,
            consistency_drag    REAL,
            velocity_factor     REAL,
            opportunity_cost_live REAL,
            is_optimal          INTEGER DEFAULT 0,
            notes               TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_firms_status ON prop_firms(status);
        CREATE INDEX IF NOT EXISTS idx_deployments_firm ON capital_deployments(firm_id);
        CREATE INDEX IF NOT EXISTS idx_deployments_status ON capital_deployments(status);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON pes_snapshots(snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_snapshots_firm ON pes_snapshots(firm_id);
    """)
    conn.commit()
    conn.close()


# ─── Firm CRUD ──────────────────────────────────────────────

def upsert_firm(firm_data: dict) -> str:
    """Insert or update a prop firm. Returns firm_id."""
    conn = get_connection()
    firm_id = firm_data.get("firm_id", str(uuid.uuid4()))
    now = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT INTO prop_firms (
            firm_id, name, website, account_sizes, cost_per_size, promo_active,
            max_daily_loss_pct, max_trailing_dd_pct, consistency_rule,
            min_trading_days, payout_cycle_days, payout_buffer_days,
            payout_method, scaling_rules, allowed_instruments,
            news_restrictions, ff_status, patch_signals, last_updated, status
        ) VALUES (?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            website=excluded.website,
            account_sizes=excluded.account_sizes,
            cost_per_size=excluded.cost_per_size,
            promo_active=excluded.promo_active,
            max_daily_loss_pct=excluded.max_daily_loss_pct,
            max_trailing_dd_pct=excluded.max_trailing_dd_pct,
            consistency_rule=excluded.consistency_rule,
            min_trading_days=excluded.min_trading_days,
            payout_cycle_days=excluded.payout_cycle_days,
            payout_buffer_days=excluded.payout_buffer_days,
            payout_method=excluded.payout_method,
            scaling_rules=excluded.scaling_rules,
            allowed_instruments=excluded.allowed_instruments,
            news_restrictions=excluded.news_restrictions,
            ff_status=excluded.ff_status,
            patch_signals=excluded.patch_signals,
            last_updated=excluded.last_updated,
            status=excluded.status
    """, (
        firm_id,
        firm_data["name"],
        firm_data.get("website", ""),
        json.dumps(firm_data.get("account_sizes", [])),
        json.dumps(firm_data.get("cost_per_size", {})),
        json.dumps(firm_data.get("promo_active", {})),
        firm_data.get("max_daily_loss_pct", 0.05),
        firm_data.get("max_trailing_dd_pct", 0.06),
        json.dumps(firm_data.get("consistency_rule", {"max_day_pct_of_total": 0.30})),
        firm_data.get("min_trading_days", 5),
        firm_data.get("payout_cycle_days", 14),
        firm_data.get("payout_buffer_days", 3),
        firm_data.get("payout_method", "Crypto"),
        json.dumps(firm_data.get("scaling_rules", {})),
        json.dumps(firm_data.get("allowed_instruments", [])),
        firm_data.get("news_restrictions", False),
        firm_data.get("ff_status", "UNTESTED"),
        json.dumps(firm_data.get("patch_signals", [])),
        now,
        firm_data.get("status", "ACTIVE"),
    ))
    conn.commit()
    conn.close()
    return firm_id


def get_firm(firm_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM prop_firms WHERE firm_id = ?", (firm_id,)).fetchone()
    conn.close()
    if row:
        return _decode_firm(dict(row))
    return None


def get_firm_by_name(name: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM prop_firms WHERE name = ?", (name,)).fetchone()
    conn.close()
    if row:
        return _decode_firm(dict(row))
    return None


def list_firms(status: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM prop_firms WHERE status = ?", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM prop_firms ORDER BY name").fetchall()
    conn.close()
    return [_decode_firm(dict(r)) for r in rows]


def update_ff_status(firm_id: str, ff_status: str, patch_signal: Optional[dict] = None):
    conn = get_connection()
    conn.execute("UPDATE prop_firms SET ff_status = ?, last_updated = ? WHERE firm_id = ?",
                 (ff_status, datetime.utcnow().isoformat(), firm_id))
    if patch_signal:
        row = conn.execute("SELECT patch_signals FROM prop_firms WHERE firm_id = ?", (firm_id,)).fetchone()
        existing = json.loads(row["patch_signals"] or "[]")
        existing.append({**patch_signal, "detected_at": datetime.utcnow().isoformat()})
        conn.execute("UPDATE prop_firms SET patch_signals = ? WHERE firm_id = ?",
                     (json.dumps(existing), firm_id))
    conn.commit()
    conn.close()


# ─── Deployment CRUD ────────────────────────────────────────

def insert_deployment(firm_id: str, account_size: int, quantity: int,
                      pes_result, notes: str = "") -> str:
    """Insert a capital deployment from a PESResult."""
    conn = get_connection()
    deployment_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    total_cost = pes_result.account_size * quantity  # simplified; real: cost_per_size
    total_risk = account_size * quantity * 0.05  # simplified

    conn.execute("""
        INSERT INTO capital_deployments (
            deployment_id, firm_id, account_size, quantity, total_cost,
            total_risk_capital, pes_score, effective_exposure, capital_velocity,
            crossover_threshold, equivalent_live_leverage, deployed_at, status, notes
        ) VALUES (?, ?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        deployment_id, firm_id, account_size, quantity, total_cost,
        total_risk, pes_result.pes_score, pes_result.effective_exposure,
        pes_result.capital_velocity, pes_result.crossover_threshold,
        pes_result.effective_leverage, now, "ACTIVE", notes,
    ))
    conn.commit()
    conn.close()
    return deployment_id


def list_deployments(status: str = "ACTIVE") -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.*, f.name as firm_name
        FROM capital_deployments d
        JOIN prop_firms f ON d.firm_id = f.firm_id
        WHERE d.status = ?
        ORDER BY d.deployed_at DESC
    """, (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_deployment_status(deployment_id: str, status: str):
    conn = get_connection()
    conn.execute("UPDATE capital_deployments SET status = ? WHERE deployment_id = ?",
                 (status, deployment_id))
    conn.commit()
    conn.close()


# ─── PES Snapshots ─────────────────────────────────────────

def insert_pes_snapshot(firm_id: str, account_size: int, pes_result) -> str:
    conn = get_connection()
    snap_id = str(uuid.uuid4())
    today = date.today().isoformat()

    conn.execute("""
        INSERT INTO pes_snapshots (
            snapshot_id, snapshot_date, firm_id, account_size, pes_score,
            effective_leverage, consistency_drag, velocity_factor,
            opportunity_cost_live, is_optimal, notes
        ) VALUES (?, ?,?,?,?,?,?,?,?,?,?)
    """, (
        snap_id, today, firm_id, account_size, pes_result.pes_score,
        pes_result.effective_leverage, pes_result.consistency_drag,
        pes_result.capital_velocity, pes_result.opportunity_cost_live,
        1 if pes_result.is_optimal else 0,
        "; ".join(pes_result.notes) if pes_result.notes else "",
    ))
    conn.commit()
    conn.close()
    return snap_id


def get_latest_snapshots() -> list[dict]:
    """Get the most recent snapshot per firm."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, f.name as firm_name, f.status as firm_status
        FROM pes_snapshots s
        JOIN prop_firms f ON s.firm_id = f.firm_id
        WHERE s.snapshot_date = (
            SELECT MAX(s2.snapshot_date) FROM pes_snapshots s2 WHERE s2.firm_id = s.firm_id
        )
        ORDER BY s.pes_score DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_optimal_deployments() -> list[dict]:
    """Get deployments currently marked as optimal."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.*, f.name as firm_name, f.account_sizes, f.cost_per_size
        FROM capital_deployments d
        JOIN prop_firms f ON d.firm_id = f.firm_id
        WHERE d.status = 'ACTIVE'
        ORDER BY d.pes_score DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Helpers ────────────────────────────────────────────────

def _decode_firm(row: dict) -> dict:
    """Decode JSON fields from database row."""
    for field in ["account_sizes", "cost_per_size", "promo_active", "consistency_rule",
                  "scaling_rules", "allowed_instruments", "patch_signals"]:
        if field in row and row[field]:
            try:
                row[field] = json.loads(row[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return row
