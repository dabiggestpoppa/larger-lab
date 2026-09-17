-- B3-R2: durable fabric leases/fencing, retry/poison/dead-letter state, and
-- PO-authorized-retry audit. Extends migration 0004 (never rewrites it).
-- PostgreSQL remains authoritative; the fabric reads/writes are transactional.
-- Reversible via 0005_down.sql.

-- Authority: fabric worker identities are issued by OCE admission. This
-- augments the Book 2 `workers` table with the immutable issued identity and
-- operator-admitted capabilities referenced by capability_admissions(0004).
ALTER TABLE worker_fabric_instances ADD COLUMN IF NOT EXISTS
    admission_actor TEXT NOT NULL DEFAULT '';
ALTER TABLE worker_fabric_instances ADD COLUMN IF NOT EXISTS
    credential_verifier TEXT;              -- sha256 of out-of-band shared secret (hashed at rest)
ALTER TABLE worker_fabric_instances ADD COLUMN IF NOT EXISTS
    capabilities JSONB NOT NULL DEFAULT '[]';
ALTER TABLE worker_fabric_instances ADD COLUMN IF NOT EXISTS
    revoked_at TIMESTAMPTZ;
ALTER TABLE worker_fabric_instances ADD COLUMN IF NOT EXISTS
    status TEXT NOT NULL DEFAULT 'admitted';  -- admitted|draining|revoked|removed

-- Durable fenced lease per logical job. The UNIQUE(job_id) enforces a single
-- active lease; fence_generation is monotonically bumped on each re-claim so a
-- stale worker's fence can never commit a result after a newer claim.
CREATE TABLE IF NOT EXISTS b3_fabric_leases (
    job_id            TEXT PRIMARY KEY,
    lease_id          TEXT NOT NULL,
    worker_id         TEXT NOT NULL REFERENCES workers(worker_id),
    fence             BIGINT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active',  -- active|released|expired|cancelled
    ttl_s             INTEGER NOT NULL DEFAULT 60,
    claimed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at        TIMESTAMPTZ NOT NULL,
    surrendered_at    TIMESTAMPTZ,
    UNIQUE (job_id, lease_id),
    UNIQUE (job_id, fence)
);

-- Effect idempotency: one accepted material effect per logical job.
CREATE TABLE IF NOT EXISTS b3_effects (
    effect_key        TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    lease_id          TEXT NOT NULL,
    fence             BIGINT NOT NULL,
    applied_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    producer_identity TEXT NOT NULL,
    UNIQUE (job_id)
);

-- Stale/late results that missed their current lease land here durably.
CREATE TABLE IF NOT EXISTS b3_quarantine (
    id                BIGSERIAL PRIMARY KEY,
    job_id            TEXT NOT NULL,
    lease_id          TEXT NOT NULL,
    fence             BIGINT NOT NULL,
    result_ref        TEXT,
    reason            TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_b3_quarantine_job ON b3_quarantine(job_id);

-- Durable retry bookkeeping per job (counters, backoff, exhaustion marker).
CREATE TABLE IF NOT EXISTS b3_retry_state (
    job_id            TEXT PRIMARY KEY,
    attempts          INTEGER NOT NULL DEFAULT 0,
    max_retries       INTEGER NOT NULL DEFAULT 3,
    classified        TEXT,
    last_reason       TEXT NOT NULL DEFAULT '',
    exhausted_at      TIMESTAMPTZ,
    poison            BOOLEAN NOT NULL DEFAULT FALSE
);

-- Dead letters reference jobs; carries the durable failure truth (0004 has the
-- base table); add poison + authorized-retry audit linkage here.
ALTER TABLE b3_dead_letters ADD COLUMN IF NOT EXISTS
    poison BOOLEAN NOT NULL DEFAULT FALSE;

-- PO-authorized retry audit records (who, when, granted or denied).
CREATE TABLE IF NOT EXISTS b3_authorized_retries (
    id                BIGSERIAL PRIMARY KEY,
    job_id            TEXT NOT NULL,
    actor             TEXT NOT NULL,
    decision          TEXT NOT NULL,       -- granted|denied
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    note              TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_b3_retries_job ON b3_authorized_retries(job_id);