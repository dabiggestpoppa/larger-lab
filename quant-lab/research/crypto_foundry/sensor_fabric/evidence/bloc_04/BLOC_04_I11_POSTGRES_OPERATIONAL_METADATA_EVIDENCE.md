# SENSOR-B4-I11 — PostgreSQL Operational Metadata Evidence

## Runtime truth

- `POSTGRES_RUNTIME_VALIDATION=BLOCKED_ENVIRONMENT`
- `G4-10_OPERATIONAL_METADATA_GATE=PENDING_REAL_POSTGRES_RUNTIME`
- `PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED=BLOCKED_RUNTIME_VALIDATION`
- PostgreSQL server version: unavailable; no server was connected.
- Driver: `psycopg[binary]` resolved to `3.3.6`; dependency-resolution network: `YES`.
- Product/provider/test external network: `ZERO`.
- Local PostgreSQL loopback traffic: `ZERO` because no local runtime or DSN was available.

The offline implementation and firewall tests are present, but SQL generation and
stubs are not treated as integration evidence. G4-10 is not claimed.

## Authority map

`provider_registry` and `adapter_readiness` are allowlisted config mirrors.
`storage_jobs` and `storage_job_transitions` mirror accepted I07 state through
its public reads. `blobs_current_metadata`, `acquisitions`,
`partition_manifest_current`, and `source_revisions` mirror accepted public
catalog/revision readers. `recovery_runs` is a narrow summary derived from
`RecoveryJournal.list_for_run`. `integrity_checks`, `quota_state`, and
`backup_state` are `OPERATIONAL_ONLY`; they are not reconstructed from a
missing durable source and are not policy authority.

PostgreSQL never replaces T0A bytes, T0B artifacts, I06 revisions, I07 resume
truth, I08 recovery journals, I09 quota policy, manifests, or DuckDB discovery.
The importer has no private DuckDB reader calls and no T0A payload-read path.

## Firewall and transaction design

The fixed schema is `crypto_sensor_fabric_ops`, version `1`, role
`operational_metadata_non_raw`, with the twelve conceptual I11 tables plus
`schema_metadata`. The schema has no `BYTEA`, JSONB, generic payload/content/
body/data column, or raw/table/market-data warehouse. Text metadata is bounded.
Secret-shaped provider/readiness values are omitted or refused; DSN errors are
redacted.

Refresh validates the complete snapshot before `BEGIN`, takes the fixed
transaction-scoped PostgreSQL advisory lock, replaces all reconstructible rows
as one transaction, validates schema/foreign-key invariants, and commits.
Failures roll back the prior snapshot. Operational-only tables are not
truncated. Point writes are limited to the three operational-only tables.

## Measured offline results

- Focused I11: **5 passed, 2 skipped** (real PostgreSQL tests skipped without
  `SENSOR_POSTGRES_TEST_DSN`).
- Changed-scope Ruff: passed.
- Changed-scope compileall: passed.
- Changed-scope mypy: no I11 error; the imported pre-existing
  `probes/planner.py:79 [call-overload]` remains.
- Repository mypy baseline: 15 errors in 9 files, unchanged by I11.
- Broader storage Ruff baseline: the two known I08 findings remain `F401` and
  `F811` in `test_i08_evidence.py`; I11 changed scope adds zero.
- The Windows checkout also presents historical committed evidence with CRLF
  while builders emit LF, causing historical byte-comparison failures in the
  broad suites. No historical evidence was rewritten.

## Required real-runtime follow-up

Before G4-10 can pass, run the opt-in integration tests against a real local
PostgreSQL 16 (or another explicitly recorded supported version), execute the
loss/drop/rebuild, rollback, concurrency, tamper, operational-state, and
zero-payload-read proofs, then replace this blocked evidence with measured
runtime evidence. Do not self-ratify and do not begin I12.
