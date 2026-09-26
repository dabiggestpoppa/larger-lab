-- B4-CXR6R3: reversal of 0008 (schema only — no ledger rows are touched).
-- Production rollback (down) is TEST-ONLY / FUTURE-LOCKED in Book 4; this
-- file exists so the canonical migration-set identity covers every version.
DROP INDEX IF EXISTS config_override_audit_request_id_key;

ALTER TABLE config_override_audit
    ALTER COLUMN request_id DROP NOT NULL;

-- The append-only trigger is preserved (it predates 0008 and outlives it).
