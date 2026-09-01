-- B4-CXR4R5: durable, append-only configuration-override audit.
-- "Durable" means demonstrably persistent (transaction-committed, reloadable,
-- append-only) — never just non-null. The generic Book 2 audit_log remains
-- untouched; this ledger is dedicated to configuration overrides and stores
-- SAFE/redacted values only (never secrets, never DSNs).
CREATE TABLE IF NOT EXISTS config_override_audit (
    audit_id        TEXT PRIMARY KEY,
    actor           TEXT NOT NULL,
    setting         TEXT NOT NULL,
    requested_change TEXT NOT NULL,
    reason          TEXT NOT NULL,
    previous        TEXT,
    new             TEXT,
    decision        TEXT NOT NULL DEFAULT 'granted',
    authorized      BOOLEAN NOT NULL DEFAULT TRUE,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version, checksum)
VALUES ('0006', 'seed') ON CONFLICT DO NOTHING;
