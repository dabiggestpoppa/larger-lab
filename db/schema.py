"""
OWL Self-Healing Error Database Schema
SQLite — single file, zero config
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "owl_health.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            source TEXT NOT NULL,          -- 'gateway', 'agent', 'tool', 'workspace', 'startup'
            severity TEXT NOT NULL,        -- 'info', 'warn', 'error', 'critical'
            category TEXT NOT NULL,        -- 'symlink', 'timeout', 'stall', 'ephemeral', 'permission', 'network', 'memory', 'unknown'
            message TEXT NOT NULL,
            raw_log_line TEXT,
            file_path TEXT,                -- workspace file if applicable
            resolved INTEGER DEFAULT 0,
            resolution TEXT,
            resolution_timestamp TEXT,
            occurrence_count INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS bug_annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_id INTEGER REFERENCES errors(id),
            bug_file TEXT NOT NULL,        -- path to bug markdown file
            title TEXT NOT NULL,
            description TEXT,
            root_cause TEXT,
            suggested_fix TEXT,
            status TEXT DEFAULT 'open',    -- 'open', 'investigating', 'fixed', 'wontfix'
            priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS startup_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            check_name TEXT NOT NULL,
            status TEXT NOT NULL,          -- 'pass', 'warn', 'fail'
            details TEXT,
            errors_found INTEGER DEFAULT 0,
            errors_logged INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS self_healing_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            trigger_error_id INTEGER REFERENCES errors(id),
            action_taken TEXT NOT NULL,
            success INTEGER DEFAULT 0,
            details TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_errors_severity ON errors(severity);
        CREATE INDEX IF NOT EXISTS idx_errors_category ON errors(category);
        CREATE INDEX IF NOT EXISTS idx_errors_resolved ON errors(resolved);
        CREATE INDEX IF NOT EXISTS idx_errors_source ON errors(source);
        CREATE INDEX IF NOT EXISTS idx_bug_status ON bug_annotations(status);
    """)
    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    path = init_db()
    print(f"Database initialized: {path}")
