# SENSOR-B4-I11R1 — PostgreSQL Runtime Truth + Schema/API Correctness Microseal

## Runtime

- PostgreSQL: **16.15**, local disposable cluster on loopback `127.0.0.1:55432`.
- Runtime provisioning: official PostgreSQL 16.15 Windows package via winget, then a disposable `initdb` cluster using local PostgreSQL binaries.
- `postgres_runtime_provision_network=YES` (official package acquisition only).
- `dependency_resolution_network=NO` for this R1 pass; the existing psycopg dependency was reused.
- Provider/product network: `ZERO`.
- Local PostgreSQL loopback: `YES`.
- Cloud databases and provider APIs were not contacted.

## Repairs measured

- Resume-token columns are absent from the PostgreSQL acquisition contract and DDL.
- Acquisition `provider_checksum_verified` is PostgreSQL `boolean`; temporal fields are `timestamptz`; numeric fields are typed.
- `TABLE_SCHEMAS` is the single authority for DDL, column order, nullability, primary keys, and foreign keys.
- Exact catalog validation rejects extra tables/columns, wrong types/nullability/PK/FK, and wrong schema metadata.
- Canonical ordering uses explicit per-table sort keys.
- `integrity_checks` uses `check_id` conflict semantics; quota and backup use singleton upserts.
- Column vocabulary and secret-shaped value detection are separate.
- Complete reconstruction requires an explicit `MetadataInventory`; no private DuckDB readers or T0A payload readers are used.

## Measured results

- Exact schema install/reinstall/validation: PASS.
- Populated reconstruction: 2 provider rows, 2 readiness rows, 2 jobs, 2 transitions, 2 blobs, 2 acquisitions, 2 manifests, 2 revisions, 1 recovery summary.
- Drop/reinstall/rebuild parity: PASS.
- Repeated refresh idempotence: PASS.
- Failed refresh rollback: PASS.
- Concurrent refresh serialization: PASS in the real two-connection integration test.
- Integrity/quota/backup operational APIs: PASS; divergent integrity identity refused.
- I07/I08/I09 authority firewall integration: PASS.
- Zero `LocalBlobStore.verify_blob`, `open_blob`, and `_decode_stats` calls during reconstruction: PASS.
- Original blocked I11 evidence hashes: unchanged.
- Measured (not hard-coded) values now back the extra-table schema attack
  refusal and the T0 evidence-immutability rows.

## CRLF test-environment finding (not an I11R1 code change)

The prior 59-failure attribution was verified rather than assumed. The
machine-wide `core.autocrlf=true` (from `C:/Program Files/Git/etc/gitconfig`,
not from this repository) rewrote 3236 committed LF blobs to CRLF in the
worktree at checkout, so byte-comparing LF-producing evidence builders against
CRLF worktree files failed. No committed bytes were rewritten: this worktree
was set to `core.autocrlf=false` (worktree-scoped) and every affected file was
restored to be byte-identical to its committed blob.

A separate, pre-existing mutation remains in an accepted checkpoint test:
`test_catalog_evidence.py` and `test_i04r1_evidence.py` write seven
`BLOC_04_I0*` evidence files with `Path.write_text`, which translates `
` to
`
` on Windows. Those files are rewritten with CRLF on every test run.
Their content is unchanged modulo line endings and no test asserts on their
bytes. Fixing an accepted I04 test is outside the I11R1 scope.

## Evidence matrices

- `BLOC_04_I11R1_SCHEMA_RUNTIME_MATRIX.json` — 5 rows (4 measured `OK`, 1 counterfactual `FAIL`)
- `BLOC_04_I11R1_POPULATED_RECONSTRUCTION_MATRIX.json` — 5 rows (4 measured `OK`, 1 counterfactual `FAIL`)
- `BLOC_04_I11R1_AUTHORITY_FIREWALL_MATRIX.json` — 3 rows (2 measured `OK`, 1 counterfactual `FAIL`)
- `BLOC_04_I11R1_TRANSACTION_CONCURRENCY_MATRIX.json` — 3 rows (2 measured `OK`, 1 counterfactual `FAIL`)
- `BLOC_04_I11R1_OPERATIONAL_STATE_MATRIX.json` — 5 rows (4 measured `OK`, 1 counterfactual `FAIL`)
- `BLOC_04_I11R1_EVIDENCE_TRUTH_MATRIX.json` — 3 rows (2 measured `OK`, 1 counterfactual `FAIL`)

Every normal row is measured and `OK`; every `counterfactual_*` row is
synthetic and `FAIL`. Normal pytest regenerates these payloads in memory and
byte-compares committed artifacts; publication requires the explicit
`UPDATE_I11R1_EVIDENCE=1` override.

## Governance

`PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED=PENDING_OPERATOR_REVIEW`

`G4-10_OPERATIONAL_METADATA_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`

`next_checkpoint_authorized=FALSE`

`recommended_next=OPERATOR REVIEW OF COMPLETE I11 -> I11R1 CHAIN`

I12 remains unauthorized. Research remains frozen. This microseal does not
self-ratify I11 or I11R1.
