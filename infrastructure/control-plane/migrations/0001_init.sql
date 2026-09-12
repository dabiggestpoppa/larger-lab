-- B2-R2 0001_init: authoritative control-plane state (PostgreSQL is truth)
BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version      TEXT PRIMARY KEY,
    checksum     TEXT NOT NULL,
    applied_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS actors (
    actor_id     TEXT PRIMARY KEY,
    actor_type   TEXT NOT NULL CHECK (actor_type IN ('operator','po','hermes','service','worker','app')),
    trust_zone   TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ,
    revoked_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS capability_grants (
    grant_id      TEXT PRIMARY KEY,
    actor_id      TEXT NOT NULL REFERENCES actors(actor_id),
    action        TEXT NOT NULL,
    target        TEXT NOT NULL,
    environment   TEXT NOT NULL,
    risk_class    TEXT NOT NULL,
    limits        JSONB NOT NULL DEFAULT '{}',
    approval_context JSONB NOT NULL DEFAULT '{}',
    issued_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at    TIMESTAMPTZ NOT NULL,
    revoked_at    TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked','expired'))
);

CREATE TABLE IF NOT EXISTS denials (
    denial_id      TEXT PRIMARY KEY,
    reason_code    TEXT NOT NULL,
    actor_id       TEXT,
    requested_action TEXT NOT NULL,
    requested_target TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    denied_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id            TEXT PRIMARY KEY,
    job_type          TEXT NOT NULL,
    schema_version    TEXT NOT NULL,
    submitting_actor  TEXT NOT NULL,
    authority_context JSONB NOT NULL,
    resource_scope    TEXT NOT NULL,
    environment       TEXT NOT NULL,
    priority          TEXT NOT NULL DEFAULT 'normal',
    idempotency_key   TEXT NOT NULL,
    payload_hash      TEXT NOT NULL,
    payload           JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    scheduled_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    attempt_number    INTEGER NOT NULL DEFAULT 0,
    retry_policy      JSONB NOT NULL DEFAULT '{"max_attempts":3,"backoff_strategy":"exponential"}',
    timeout_seconds   INTEGER NOT NULL DEFAULT 300,
    correlation_id    TEXT NOT NULL,
    parent_job_id     TEXT REFERENCES jobs(job_id),
    status            TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','scheduled','leased','running','succeeded','failed','cancelled','quarantined','expired')),
    result            JSONB,
    failure_envelope  JSONB,
    evidence_refs     JSONB NOT NULL DEFAULT '[]',
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_transitions (
    id          BIGSERIAL PRIMARY KEY,
    job_id      TEXT NOT NULL REFERENCES jobs(job_id),
    from_state  TEXT NOT NULL,
    to_state    TEXT NOT NULL,
    actor_id    TEXT,
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS idempotency (
    idempotency_key TEXT PRIMARY KEY,
    actor_id        TEXT NOT NULL,
    action          TEXT NOT NULL,
    target          TEXT NOT NULL,
    job_type        TEXT NOT NULL,
    payload_hash    TEXT NOT NULL,
    job_id          TEXT NOT NULL REFERENCES jobs(job_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leases (
    job_id      TEXT PRIMARY KEY REFERENCES jobs(job_id),
    lease_id    TEXT NOT NULL UNIQUE,
    worker_id   TEXT NOT NULL,
    leased_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL,
    heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS schedules (
    schedule_id    TEXT PRIMARY KEY,
    job_type       TEXT NOT NULL,
    payload        JSONB NOT NULL DEFAULT '{}',
    recurring      BOOLEAN NOT NULL DEFAULT FALSE,
    interval_seconds INTEGER,
    scheduled_at   TIMESTAMPTZ,
    last_run_at    TIMESTAMPTZ,
    next_run_at    TIMESTAMPTZ,
    max_concurrent INTEGER NOT NULL DEFAULT 1,
    miss_policy    TEXT NOT NULL DEFAULT 'run_once',
    paused         BOOLEAN NOT NULL DEFAULT FALSE,
    timezone       TEXT NOT NULL DEFAULT 'UTC',
    created_by     TEXT NOT NULL,
    grant_id       TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workers (
    worker_id     TEXT PRIMARY KEY,
    capabilities  JSONB NOT NULL,
    trust_zone    TEXT NOT NULL DEFAULT 'worker-local',
    admission_token_hash TEXT NOT NULL,
    max_concurrent_jobs INTEGER NOT NULL DEFAULT 1,
    connected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_heartbeat TIMESTAMPTZ,
    revoked_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    schema_version  TEXT NOT NULL,
    actor_id        TEXT NOT NULL,
    authority_grant_id TEXT NOT NULL,
    root_id         TEXT NOT NULL,
    parent_id       TEXT,
    sequence        BIGINT NOT NULL,
    target          TEXT NOT NULL,
    payload_hash    TEXT NOT NULL,
    environment     TEXT NOT NULL,
    result          JSONB NOT NULL DEFAULT '{}',
    evidence_refs   JSONB NOT NULL DEFAULT '[]',
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id   TEXT PRIMARY KEY,
    action     TEXT NOT NULL,
    actor_id   TEXT,
    target     TEXT NOT NULL,
    success    BOOLEAN NOT NULL,
    error      TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_refs (
    evidence_id  TEXT PRIMARY KEY,
    artifact_uri TEXT NOT NULL,
    sha256       TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version, checksum)
VALUES ('0001', 'seed') ON CONFLICT DO NOTHING;
COMMIT;
