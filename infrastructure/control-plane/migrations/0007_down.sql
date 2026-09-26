DROP TRIGGER IF EXISTS config_override_audit_append_only ON config_override_audit;
DROP FUNCTION IF EXISTS config_override_audit_append_only();

ALTER TABLE config_override_audit
    DROP COLUMN IF EXISTS request_id,
    DROP COLUMN IF EXISTS fingerprint_before,
    DROP COLUMN IF EXISTS fingerprint_after,
    DROP COLUMN IF EXISTS backend_identity;
