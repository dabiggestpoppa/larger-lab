-- B4-CXR6R3: EXACT audit idempotency — a request/correlation ID may
-- reconcile ONLY the exact same durable decision.
--
-- CXR5's append used `ON CONFLICT (audit_id) DO NOTHING` and returned
-- success; a divergent retry under one request_id could then leave the
-- second applicable value WITHOUT a durable record. This forward migration
-- (never rewrites an applied migration):
--   1. backfills legacy NULL/empty request_id rows from audit_id;
--   2. makes request_id NOT NULL;
--   3. enforces request_id uniqueness (the governed reconciliation key);
--   4. re-creates the append-only trigger unchanged (it is dropped only for
--      the duration of this schema fix, inside one transaction, and restored
--      before the migration commits).
--
-- Divergent reuse is then refused by the application (read-back + full
-- canonical-decision comparison); the database additionally refuses a
-- second row under the same request_id outright.

DROP TRIGGER IF EXISTS config_override_audit_append_only ON config_override_audit;

UPDATE config_override_audit
   SET request_id = audit_id
 WHERE request_id IS NULL OR request_id = '';

ALTER TABLE config_override_audit
    ALTER COLUMN request_id SET NOT NULL;

-- Divergent duplicates would violate this index and fail the migration
-- loudly rather than silently coalescing two different decisions.
CREATE UNIQUE INDEX IF NOT EXISTS config_override_audit_request_id_key
    ON config_override_audit (request_id);

CREATE OR REPLACE FUNCTION config_override_audit_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'config_override_audit is APPEND-ONLY: UPDATE refused (B4-CXR5R5)';
    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'config_override_audit is APPEND-ONLY: DELETE refused (B4-CXR5R5)';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS config_override_audit_append_only ON config_override_audit;
CREATE TRIGGER config_override_audit_append_only
    BEFORE UPDATE OR DELETE ON config_override_audit
    FOR EACH ROW EXECUTE FUNCTION config_override_audit_append_only();

INSERT INTO schema_migrations (version, checksum)
VALUES ('0008', 'seed') ON CONFLICT DO NOTHING;
