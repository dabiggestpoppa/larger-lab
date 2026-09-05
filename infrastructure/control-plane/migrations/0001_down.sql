-- B2-R2 0001_down: reverse initial schema
BEGIN;
DROP TABLE IF EXISTS evidence_refs;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS workers;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS leases;
DROP TABLE IF EXISTS idempotency;
DROP TABLE IF EXISTS job_transitions;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS denials;
DROP TABLE IF EXISTS capability_grants;
DROP TABLE IF EXISTS actors;
DELETE FROM schema_migrations WHERE version = '0001';
COMMIT;
