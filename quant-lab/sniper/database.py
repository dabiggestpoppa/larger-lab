"""
CEREBUS Sniper — Database Layer
================================
SQLite database for prop firm scanning.
Tables: prop_firms, capital_deployments, sniper_snapshots
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "sniper.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS prop_firms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            account_size REAL DEFAULT 10000,
            drawdown_pct REAL DEFAULT 10,
            profit_target REAL DEFAULT 10,
            min_trading_days INTEGER DEFAULT 5,
            max_daily_loss_pct REAL DEFAULT 5,
            max_total_loss_pct REAL DEFAULT 10,
            payout_ratio REAL DEFAULT 0.8,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS capital_deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            total_cost REAL DEFAULT 0,
            status TEXT DEFAULT 'ACTIVE',
            strategy TEXT DEFAULT 'symmetry_trap',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (firm_id) REFERENCES prop_firms(id)
        );

        CREATE TABLE IF NOT EXISTS sniper_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            pes_score REAL DEFAULT 0,
            win_rate REAL DEFAULT 0,
            trades INTEGER DEFAULT 0,
            pnl_pips REAL DEFAULT 0,
            regime TEXT DEFAULT 'UNKNOWN',
            tier TEXT DEFAULT 'T2',
            asian_range_pips REAL DEFAULT 0,
            dist_to_25_pips REAL DEFAULT 0,
            dist_to_132_pips REAL DEFAULT 0,
            bias TEXT DEFAULT 'UNKNOWN',
            session TEXT DEFAULT 'UNKNOWN',
            day_of_week INTEGER DEFAULT -1,
            snapshot_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (firm_id) REFERENCES prop_firms(id)
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_firm ON sniper_snapshots(firm_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_symbol ON sniper_snapshots(symbol);
        CREATE INDEX IF NOT EXISTS idx_snapshots_pes ON sniper_snapshots(pes_score);
        CREATE INDEX IF NOT EXISTS idx_deployments_firm ON capital_deployments(firm_id);
    """)
    conn.commit()
    conn.close()


def list_firms(status: Optional[str] = None) -> list[dict]:
    """List all prop firms, optionally filtered by status."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM prop_firms WHERE status = ? ORDER BY name", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM prop_firms ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_firm_by_name(name: str) -> Optional[dict]:
    """Get a firm by name."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM prop_firms WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_deployments(status: Optional[str] = None) -> list[dict]:
    """List all capital deployments."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT d.*, f.name as firm_name FROM capital_deployments d "
            "JOIN prop_firms f ON d.firm_id = f.id "
            "WHERE d.status = ? ORDER BY d.created_at DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT d.*, f.name as firm_name FROM capital_deployments d "
            "JOIN prop_firms f ON d.firm_id = f.id ORDER BY d.created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_snapshots(limit: int = 50) -> list[dict]:
    """Get the latest sniper snapshots."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT s.*, f.name as firm_name FROM sniper_snapshots s "
        "JOIN prop_firms f ON s.firm_id = f.id "
        "ORDER BY s.snapshot_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_deployments_with_firms() -> list[dict]:
    """Get active deployments joined with firm data."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT d.*, f.name as firm_name, f.status as firm_status "
        "FROM capital_deployments d "
        "JOIN prop_firms f ON d.firm_id = f.id "
        "WHERE d.status = 'ACTIVE' AND f.status = 'ACTIVE' "
        "ORDER BY d.total_cost DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_optimal_deployments(min_pes: float = 70.0, min_wr: float = 0.6) -> list[dict]:
    """Get optimal deployments based on PES score and win rate."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT s.*, f.name as firm_name FROM sniper_snapshots s "
        "JOIN prop_firms f ON s.firm_id = f.id "
        "WHERE s.pes_score >= ? AND s.win_rate >= ? "
        "ORDER BY s.pes_score DESC, s.win_rate DESC",
        (min_pes, min_wr)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pes_trend(firm_id: int, days: int = 30) -> list[dict]:
    """Get PES score trend for a firm."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT snapshot_at, pes_score, win_rate, pnl_pips, symbol "
        "FROM sniper_snapshots "
        "WHERE firm_id = ? AND snapshot_at >= datetime('now', ?) "
        "ORDER BY snapshot_at ASC",
        (firm_id, f"-{days} days")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_snapshot(firm_id: int, symbol: str, pes_score: float,
                    win_rate: float, trades: int, pnl_pips: float,
                    regime: str, tier: str, asian_range_pips: float,
                    dist_to_25_pips: float, dist_to_132_pips: float,
                    bias: str, session: str, day_of_week: int,
                    _conn: Optional[sqlite3.Connection] = None):
    """Insert a new sniper snapshot. Uses provided connection or creates one."""
    conn = _conn or get_connection()
    conn.execute(
        "INSERT INTO sniper_snapshots "
        "(firm_id, symbol, pes_score, win_rate, trades, pnl_pips, "
        "regime, tier, asian_range_pips, dist_to_25_pips, dist_to_132_pips, "
        "bias, session, day_of_week) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (firm_id, symbol, pes_score, win_rate, trades, pnl_pips,
         regime, tier, asian_range_pips, dist_to_25_pips, dist_to_132_pips,
         bias, session, day_of_week)
    )
    if _conn is None:
        conn.commit()
        conn.close()


def seed_sample_data():
    """Seed the database with 100+ prop firm configurations. Call init_database() first."""
    from sniper.prop_firm_scanner import PROP_FIRMS, FX_PAIRS, compute_pes_score

    conn = get_connection()

    # Insert all unique firms
    seen_firms = set()
    for firm_name, account_size, dd_pct, pt_pct, min_days, max_dd, max_tl, payout, tier in PROP_FIRMS:
        key = (firm_name, account_size)
        if key not in seen_firms:
            seen_firms.add(key)
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO prop_firms "
                    "(name, status, account_size, drawdown_pct, profit_target, "
                    "min_trading_days, max_daily_loss_pct, max_total_loss_pct, payout_ratio) "
                    "VALUES (?, 'ACTIVE', ?, ?, ?, ?, ?, ?, ?)",
                    (firm_name, account_size, dd_pct, pt_pct, min_days, max_dd, max_tl, payout)
                )
            except sqlite3.IntegrityError:
                pass

    # Get firm IDs
    firm_ids = [r[0] for r in conn.execute("SELECT id FROM prop_firms").fetchall()]

    import random
    random.seed(42)

    # Create deployments for each firm across FX pairs
    for firm_id in firm_ids:
        firm_name = conn.execute("SELECT name FROM prop_firms WHERE id = ?", (firm_id,)).fetchone()[0]
        for symbol in FX_PAIRS:
            if random.random() > 0.4:  # 60% of pairs deployed
                cost = random.uniform(500, 8000)
                qty = random.randint(1, 5)
                strategy = random.choice(["symmetry_trap", "p90_cascade"])
                try:
                    conn.execute(
                        "INSERT INTO capital_deployments "
                        "(firm_id, symbol, quantity, total_cost, strategy) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (firm_id, symbol, qty, cost, strategy)
                    )
                except sqlite3.IntegrityError:
                    pass

    # Create snapshots with computed PES scores
    for firm_id in firm_ids:
        firm_row = conn.execute(
            "SELECT name, account_size, drawdown_pct, profit_target, payout_ratio FROM prop_firms WHERE id = ?",
            (firm_id,)
        ).fetchone()
        firm_name, account_size, dd_pct, pt_pct, payout = firm_row

        for symbol in FX_PAIRS[:15]:  # Top 15 pairs per firm
            tier = random.choice(["T1", "T2", "T3", "T4"])
            pes = compute_pes_score(firm_name, symbol, tier, account_size, dd_pct, pt_pct, payout)
            wr = random.uniform(0.40, 0.85)
            trades = random.randint(3, 60)
            pnl = random.uniform(-800, 3000)
            regime = random.choice(["CONFIRMED", "CAUTION", "FAILED"])
            ar = random.uniform(8, 50)
            d25 = random.uniform(-40, 40)
            d132 = random.uniform(15, 100)
            bias = random.choice(["Bullish", "Bearish"])
            session = random.choice(["asian", "london", "ny"])
            dow = random.randint(0, 4)

            insert_snapshot(
                firm_id, symbol, pes, wr, trades, pnl,
                regime, tier, ar, d25, d132, bias, session, dow,
                _conn=conn
            )

    conn.commit()
    conn.close()
    print(f"Database seeded: {len(seen_firms)} firms, {len(firm_ids)} firm IDs, {len(FX_PAIRS)} pairs")
