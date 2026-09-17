-- B3-R2 down: remove durable fabric leases/fencing, retry, quarantine, effect
-- idempotency, and authorized-retry audit state added by 0005. Fabric columns
-- added to worker_fabric_instances / b3_dead_letters are also dropped.
DROP TABLE IF EXISTS b3_authorized_retries;
DROP TABLE IF EXISTS b3_retry_state;
DROP TABLE IF EXISTS b3_quarantine;
DROP TABLE IF EXISTS b3_effects;
DROP TABLE IF EXISTS b3_fabric_leases;

ALTER TABLE b3_dead_letters DROP COLUMN IF EXISTS poison;

ALTER TABLE worker_fabric_instances DROP COLUMN IF EXISTS admission_actor;
ALTER TABLE worker_fabric_instances DROP COLUMN IF EXISTS credential_verifier;
ALTER TABLE worker_fabric_instances DROP COLUMN IF EXISTS capabilities;
ALTER TABLE worker_fabric_instances DROP COLUMN IF EXISTS revoked_at;
ALTER TABLE worker_fabric_instances DROP COLUMN IF EXISTS status;