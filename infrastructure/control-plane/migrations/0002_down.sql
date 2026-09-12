-- B2-R2 0002_down: drop indexes
BEGIN;
DROP INDEX IF EXISTS idx_transitions_job;
DROP INDEX IF EXISTS idx_grants_actor;
DROP INDEX IF EXISTS idx_audit_actor;
DROP INDEX IF EXISTS idx_events_type;
DROP INDEX IF EXISTS idx_events_root;
DROP INDEX IF EXISTS idx_schedules_next_run;
DROP INDEX IF EXISTS idx_leases_expires;
DROP INDEX IF EXISTS idx_jobs_parent;
DROP INDEX IF EXISTS idx_jobs_correlation;
DROP INDEX IF EXISTS idx_jobs_scheduled_at;
DROP INDEX IF EXISTS idx_jobs_status;
DROP INDEX IF EXISTS idx_idempotency_job;
DROP INDEX IF EXISTS idx_idempotency_full;
DELETE FROM schema_migrations WHERE version = '0002';
COMMIT;
