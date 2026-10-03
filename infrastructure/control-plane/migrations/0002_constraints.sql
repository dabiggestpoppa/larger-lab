-- B2-R2 0002_constraints: uniqueness + indexes for idempotency, leases, jobs
BEGIN;

-- Idempotency collision guard: same key must map to identical
-- (actor, action, target, job_type, payload_hash). Enforced in the
-- adapter's INSERT ... ON CONFLICT logic; index supports the lookup.
CREATE UNIQUE INDEX IF NOT EXISTS idx_idempotency_full
    ON idempotency (idempotency_key, actor_id, action, target, job_type, payload_hash);
CREATE INDEX IF NOT EXISTS idx_idempotency_job ON idempotency (job_id);

-- Job lookups
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_at ON jobs (scheduled_at) WHERE status IN ('pending','scheduled');
CREATE INDEX IF NOT EXISTS idx_jobs_correlation ON jobs (correlation_id);
CREATE INDEX IF NOT EXISTS idx_jobs_parent ON jobs (parent_job_id) WHERE parent_job_id IS NOT NULL;

-- Lease expiry sweep
CREATE INDEX IF NOT EXISTS idx_leases_expires ON leases (expires_at);

-- Schedules due
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules (next_run_at) WHERE paused = FALSE;

-- Events by causal root
CREATE INDEX IF NOT EXISTS idx_events_root ON events (root_id, sequence);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);

-- Audit history by actor/time
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log (actor_id, recorded_at);

-- Grants by actor/status
CREATE INDEX IF NOT EXISTS idx_grants_actor ON capability_grants (actor_id, status);

-- Job transitions by job
CREATE INDEX IF NOT EXISTS idx_transitions_job ON job_transitions (job_id, transitioned_at);

INSERT INTO schema_migrations (version, checksum)
VALUES ('0002', 'seed') ON CONFLICT DO NOTHING;
COMMIT;
