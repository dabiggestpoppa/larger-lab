-- Phase 11 Stability Database Schema
-- Tracks runtime metrics, observer events, continuity states, and drift

-- Runtime metrics (collected every minute)
CREATE TABLE IF NOT EXISTS runtime_metrics (
    timestamp REAL PRIMARY KEY,
    observer_count INTEGER,
    active_observers INTEGER,
    event_throughput REAL,
    memory_usage_mb REAL,
    entropy_score REAL,
    drift_score REAL,
    websocket_status TEXT,
    openrouter_status TEXT,
    uptime_seconds REAL
);

-- Observer lifecycle events
CREATE TABLE IF NOT EXISTS observer_events (
    event_id TEXT PRIMARY KEY,
    observer_id TEXT,
    event_type TEXT, -- spawn, heartbeat, death, recovery
    timestamp REAL,
    details TEXT
);

-- Continuity states for reconstruction validation
CREATE TABLE IF NOT EXISTS continuity_states (
    state_id TEXT PRIMARY KEY,
    observer_id TEXT,
    identity_hash TEXT,
    trajectory_hash TEXT,
    goal_hash TEXT,
    memory_hash TEXT,
    timestamp REAL,
    valid INTEGER DEFAULT 1
);

-- Entropy history tracking
CREATE TABLE IF NOT EXISTS entropy_history (
    timestamp REAL PRIMARY KEY,
    entropy_score REAL,
    source TEXT,
    details TEXT
);

-- Drift scores over time
CREATE TABLE IF NOT EXISTS drift_scores (
    timestamp REAL PRIMARY KEY,
    element_id TEXT,
    drift_score REAL,
    divergence_rate REAL,
    details TEXT
);

-- Restart and recovery events
CREATE TABLE IF NOT EXISTS restart_reconstruction (
    event_id TEXT PRIMARY KEY,
    restart_type TEXT, -- kill, crash, planned
    timestamp REAL,
    recovery_time_seconds REAL,
    continuity_loss_percent REAL,
    success INTEGER
);

-- Memory integrity tracking
CREATE TABLE IF NOT EXISTS memory_integrity (
    check_id TEXT PRIMARY KEY,
    timestamp REAL,
    memory_id TEXT,
    integrity_score REAL,
    contradictions_found INTEGER,
    corruption_detected INTEGER
);

-- Chaos injection events
CREATE TABLE IF NOT EXISTS chaos_events (
    event_id TEXT PRIMARY KEY,
    chaos_type TEXT,
    target TEXT,
    timestamp REAL,
    duration_seconds REAL,
    severity REAL,
    recovered INTEGER DEFAULT 0,
    recovery_time REAL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_observer_events_timestamp ON observer_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_continuity_observer ON continuity_states(observer_id);
CREATE INDEX IF NOT EXISTS idx_entropy_timestamp ON entropy_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_drift_element ON drift_scores(element_id);