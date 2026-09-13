-- B4-CXR4R5: reversible removal of the config-override audit ledger.
DROP TABLE IF EXISTS config_override_audit;
DELETE FROM schema_migrations WHERE version = '0006';
