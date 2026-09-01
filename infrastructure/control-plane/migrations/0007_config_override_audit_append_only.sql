-- B4-CXR5R5: proven audit durability — transactionally isolated, secret-free,
-- reloadable, APPEND-ONLY.
--
-- 0006 created the dedicated config-override ledger. This forward migration
-- (never rewrite an applied migration):
--   1. adds the durable-record fields required by the canonical override path
--      (request/correlation id, config fingerprint before, proposed/effective
--      fingerprint after, backend identity) — all SAFE/redacted values;
--   2. enforces append-only semantics IN THE DATABASE: UPDATE and DELETE on
--      the ledger are refused by a trigger, so an accidental rewrite or a
--      forged record can never be introduced through SQL.
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

ALTER TABLE config_override_audit
    ADD COLUMN IF NOT EXISTS request_id          TEXT,
    ADD COLUMN IF NOT EXISTS fingerprint_before  TEXT,
    ADD COLUMN IF NOT EXISTS fingerprint_after   TEXT,
    ADD COLUMN IF NOT EXISTS backend_identity    TEXT NOT NULL DEFAULT 'postgres:config_override_audit';

INSERT INTO schema_migrations (version, checksum)
VALUES ('0007', 'seed') ON CONFLICT DO NOTHING;
