-- B2-R4: worker admission/capability enforcement + durable scheduler context.
--
-- Audit gap 11: jobs carry `required_capabilities` enforced at claim time.
-- Audit gap 15: schedules persist the full submission context so restart
-- recovery is faithful to the authoritative PostgreSQL state.
--
-- Reversible via 0003_down.sql.

ALTER TABLE jobs
    ADD COLUMN IF NOT EXISTS required_capabilities JSONB NOT NULL DEFAULT '[]';

ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS submitting_actor TEXT NOT NULL DEFAULT '';
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS resource_scope TEXT NOT NULL DEFAULT 'default';
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS environment TEXT NOT NULL DEFAULT 'local';
ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS priority TEXT NOT NULL DEFAULT 'normal';
