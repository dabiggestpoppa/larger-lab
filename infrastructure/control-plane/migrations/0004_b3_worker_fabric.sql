-- B3 Worker Fabric: durable authoritative state for identity, outbound
-- sessions, immutable artifacts and retry/dead-letter records.
--
-- Extends (never weakens) the ratified Book 2 schema. Reversible via
-- 0004_down.sql.

-- B3-C1: operator-admitted capability catalogue (OCE admits, workers do not).
CREATE TABLE IF NOT EXISTS capability_admissions (
    capability        TEXT PRIMARY KEY,
    admitted_by       TEXT NOT NULL,
    admitted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    note              TEXT NOT NULL DEFAULT ''
);

-- B3-C1/C3: durable fabric fence/bookkeeping for a worker instance.
CREATE TABLE IF NOT EXISTS worker_fabric_instances (
    worker_id         TEXT PRIMARY KEY REFERENCES workers(worker_id),
    protocol_version  TEXT NOT NULL,
    worker_version    TEXT NOT NULL,
    host_os_class     TEXT NOT NULL,
    runtime_class     TEXT NOT NULL,
    trust_zone        TEXT NOT NULL,
    sandbox_profile   TEXT NOT NULL DEFAULT 'default',
    fence_generation  BIGINT NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- B3-C2: outbound session records (secret stored hashed as a verifier).
CREATE TABLE IF NOT EXISTS worker_sessions (
    session_id        TEXT PRIMARY KEY,
    worker_id         TEXT NOT NULL REFERENCES workers(worker_id),
    protocol_version  TEXT NOT NULL,
    trust_zone        TEXT NOT NULL,
    capabilities      JSONB NOT NULL DEFAULT '[]',
    verifier          TEXT NOT NULL,
    challenge         TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at        TIMESTAMPTZ NOT NULL,
    last_heartbeat    TIMESTAMPTZ,
    revoked_at        TIMESTAMPTZ,
    draining          BOOLEAN NOT NULL DEFAULT FALSE,
    generation        BIGINT NOT NULL DEFAULT 1
);

-- B3-C5: durable, content-addressed references to immutable artifacts.
CREATE TABLE IF NOT EXISTS b3_artifacts (
    manifest_id       TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL REFERENCES jobs(job_id),
    attempt           INTEGER NOT NULL,
    worker_id         TEXT NOT NULL REFERENCES workers(worker_id),
    producer_identity TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload           JSONB NOT NULL           -- manifest body (hashes/sizes)
);

-- B3-C6: dead-letter + retry bookkeeping for worker failure handling.
CREATE TABLE IF NOT EXISTS b3_dead_letters (
    job_id            TEXT PRIMARY KEY REFERENCES jobs(job_id),
    attempt           INTEGER NOT NULL,
    worker_id         TEXT NOT NULL REFERENCES workers(worker_id),
    reason            TEXT NOT NULL,
    detail            TEXT NOT NULL DEFAULT '',
    idempotency_key   TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    authorized_retry_at TIMESTAMPTZ,
    operator_actor    TEXT
);

CREATE INDEX IF NOT EXISTS idx_b3_sessions_worker ON worker_sessions(worker_id);
CREATE INDEX IF NOT EXISTS idx_b3_artifacts_job ON b3_artifacts(job_id);
CREATE INDEX IF NOT EXISTS idx_b3_dl_created ON b3_dead_letters(created_at);