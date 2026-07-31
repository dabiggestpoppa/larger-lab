"""Fix agents.db schema — add research_tasks table if missing."""
import sqlite3
from pathlib import Path

db_path = Path("data/research/agents.db")
conn = sqlite3.connect(db_path)

# Check existing tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Existing tables: {[t[0] for t in tables]}")

# Create research_tasks if missing
conn.execute("""
CREATE TABLE IF NOT EXISTS research_tasks (
    id TEXT PRIMARY KEY,
    gap_id TEXT DEFAULT '',
    query TEXT NOT NULL,
    domains TEXT DEFAULT '[]',
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    assigned_to TEXT DEFAULT '',
    result_json TEXT DEFAULT '',
    confidence REAL DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT DEFAULT '',
    completed_at TEXT DEFAULT ''
)
""")
conn.commit()

# Verify
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"After fix: {[t[0] for t in tables]}")
conn.close()
print("Done!")
