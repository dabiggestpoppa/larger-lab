-- QL-EXEC-R3 — GenericRuntime durable store schema (SQLite + WAL).
-- One database per runtime_id at state/<runtime_id>/runtime.sqlite.
-- The runtime_events table is APPEND-ONLY; other tables are materialized
-- current-state (updated in the same transaction as the event that changed
-- them). No broker calls happen inside any write transaction.

PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 10000;

CREATE TABLE IF NOT EXISTS runtime_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS desired_state (
    runtime_id  TEXT PRIMARY KEY,
    state       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT NOT NULL UNIQUE,
    event_type   TEXT NOT NULL,
    ts           TEXT NOT NULL,
    dedup_key    TEXT UNIQUE,
    payload      TEXT NOT NULL DEFAULT '{}',
    payload_hash TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_events_type ON runtime_events(event_type);

CREATE TABLE IF NOT EXISTS strategy_events (
    event_id               TEXT PRIMARY KEY,
    strategy_id            TEXT NOT NULL,
    event_kind             TEXT NOT NULL DEFAULT '',
    deployment_generation  TEXT NOT NULL DEFAULT '',
    signal_time            TEXT NOT NULL DEFAULT '',
    payload                TEXT NOT NULL DEFAULT '{}',
    ts                     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capital_decisions (
    decision_id    TEXT PRIMARY KEY,
    event_id       TEXT NOT NULL,
    strategy_id    TEXT NOT NULL,
    kind           TEXT NOT NULL,
    admitted_f     REAL,
    reservation_id TEXT NOT NULL DEFAULT '',
    policy_id      TEXT NOT NULL DEFAULT '',
    reason         TEXT NOT NULL DEFAULT '',
    ts             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS economic_targets (
    target_id        TEXT PRIMARY KEY,
    event_id         TEXT NOT NULL,
    strategy_id      TEXT NOT NULL,
    account_id       TEXT NOT NULL,
    instrument       TEXT NOT NULL DEFAULT '',
    broker_symbol    TEXT NOT NULL DEFAULT '',
    side             TEXT NOT NULL DEFAULT '',
    target_quantity  REAL,
    target_notional  REAL,
    ts               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_intents (
    intent_id              TEXT PRIMARY KEY,
    runtime_id             TEXT NOT NULL,
    account_id             TEXT NOT NULL,
    strategy_id            TEXT NOT NULL,
    deployment_generation  TEXT NOT NULL,
    event_id               TEXT NOT NULL,
    economic_target_id     TEXT NOT NULL,
    instrument             TEXT NOT NULL DEFAULT '',
    broker_symbol          TEXT NOT NULL DEFAULT '',
    side                   TEXT NOT NULL DEFAULT '',
    broker_quantity        REAL NOT NULL DEFAULT 0,
    logical_ownership_id   TEXT NOT NULL,
    ownership_tag          TEXT NOT NULL DEFAULT '',
    broker_magic           INTEGER NOT NULL DEFAULT 0,
    state                  TEXT NOT NULL,
    broker_order_id        TEXT NOT NULL DEFAULT '',
    broker_position_id     TEXT NOT NULL DEFAULT '',
    filled_quantity        REAL NOT NULL DEFAULT 0,
    fill_price             REAL,
    reason                 TEXT NOT NULL DEFAULT '',
    ts                     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_intents_event ON execution_intents(event_id);

CREATE TABLE IF NOT EXISTS broker_orders (
    order_id           TEXT PRIMARY KEY,
    intent_id          TEXT NOT NULL,
    symbol             TEXT NOT NULL DEFAULT '',
    side               TEXT NOT NULL DEFAULT '',
    requested_quantity REAL NOT NULL DEFAULT 0,
    filled_quantity    REAL NOT NULL DEFAULT 0,
    status             TEXT NOT NULL DEFAULT '',
    ownership_tag      TEXT NOT NULL DEFAULT '',
    ts                 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions_owned (
    logical_ownership_id  TEXT PRIMARY KEY,
    runtime_id            TEXT NOT NULL,
    account_id            TEXT NOT NULL,
    strategy_id           TEXT NOT NULL,
    intent_id             TEXT NOT NULL,
    event_id              TEXT NOT NULL,
    symbol                TEXT NOT NULL DEFAULT '',
    side                  TEXT NOT NULL DEFAULT '',
    requested_quantity    REAL NOT NULL DEFAULT 0,
    filled_quantity       REAL NOT NULL DEFAULT 0,
    state                 TEXT NOT NULL,
    broker_position_id    TEXT NOT NULL DEFAULT '',
    broker_order_id       TEXT NOT NULL DEFAULT '',
    ownership_tag         TEXT NOT NULL DEFAULT '',
    fill_price            REAL,
    ts                    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliation_runs (
    run_id          TEXT PRIMARY KEY,
    state           TEXT NOT NULL,
    clean           INTEGER NOT NULL,
    blocked_reason  TEXT NOT NULL DEFAULT '',
    owned_count     INTEGER NOT NULL DEFAULT 0,
    foreign_count   INTEGER NOT NULL DEFAULT 0,
    detail          TEXT NOT NULL DEFAULT '',
    ts              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS heartbeats (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    runtime_id      TEXT NOT NULL,
    state           TEXT NOT NULL,
    desired_state   TEXT NOT NULL,
    blocking_reason TEXT NOT NULL DEFAULT '',
    ts              TEXT NOT NULL
);
