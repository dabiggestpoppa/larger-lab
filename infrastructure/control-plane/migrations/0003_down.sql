-- Rollback of 0003_b2r4_capabilities_and_schedules.sql.

ALTER TABLE jobs
    DROP COLUMN IF EXISTS required_capabilities;

ALTER TABLE schedules
    DROP COLUMN IF EXISTS submitting_actor;
ALTER TABLE schedules
    DROP COLUMN IF EXISTS resource_scope;
ALTER TABLE schedules
    DROP COLUMN IF EXISTS environment;
ALTER TABLE schedules
    DROP COLUMN IF EXISTS priority;
