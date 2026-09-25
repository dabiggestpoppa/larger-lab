# SENSOR-B4-I10R2-RATIFY — Operator Ratification

## Decision

The operator accepts the complete technical chain:

`SENSOR-B4-I10 -> SENSOR-B4-I10R1 -> SENSOR-B4-I10R2`

This ratification applies to the superseding live implementation and the append-only R1/R2 evidence. Historical I10 evidence remains immutable historical counterevidence where its original builders were weaker. Historical I10R1 evidence remains immutable.

Mandatory start SHA:

`a4ee26379f159ca61de7b8cd49436873caf15936`

No amend, reset, rebase, squash, or force push was used.

## Accepted commit chain

### I10

- `328721e065974187862a8f6b3c0a34fc4ea8e75e` — I10A
- `60c5e40c95028506e628a45788ba62793b1ef2df` — I10B
- `e2d58be6fe2f351dd9b5a41989e09264533419a3` — I10C
- `94b9c39e19374ef0e124c43f42e97a54aab0f0fe` — I10D
- `f400f6edb762e77d30bb4629d423f0afdadb2c51` — I10D-R1

### I10R1

- `343873a102501528e896dbc24b60601ff96b02e5` — I10R1A
- `08edabead2ad895a10599b7503063c74e65ddc27` — I10R1B
- `ac1c6db68af06d833e44ed3df1f2c36e0422b1f2` — I10R1C
- `9dfbf85ff74a5f2ce4f985326c9ccd37bafc2053` — I10R1D
- `51e23b1054b7c1ee4869289025238ac6ecdad7bc` — I10R1 lint/read-only proof

### I10R2

- `b984b19be161b7b94526366b16dac74d7236143d` — I10R2A
- `f074978ebc9123e42c519e96ac07c9a795f8bf12` — I10R2B
- `ef0fca9b9b34f05ed5fec364578a0cfe8e900882` — I10R2C
- `8d4cf06eb6a890993fbdfb8b1197665d37e706b1` — I10R2D
- `a4ee26379f159ca61de7b8cd49436873caf15936` — I10R2D-R1

## Frozen G4-09 acceptance

**G4-09 — CATALOG REBUILD GATE: IMPLEMENTATION_PASS**

G4-09 passes when DuckDB discovery is reconstructed from manifest/projection files on an empty catalog with equivalent discovery results. The accepted implementation satisfies this through:

- rebuildable, non-authoritative DuckDB role;
- deterministic empty-root bootstrap;
- eight frozen discovery views;
- destroy/rebuild and rebuild-twice equivalence;
- evidence-tree immutability;
- atomic candidate construction, validation, and `os.replace` publication;
- read-only consumer boundary;
- exact schema/version validation;
- metadata-level lineage binding;
- explicit missingness;
- historical revision multiplicity;
- root relocation preserving canonical identities; and
- zero dependency on DuckDB as scientific truth.

## Accepted architecture and repairs

DuckDB remains a rebuildable discovery catalog, not scientific truth. I10R1 established `VIEW_SCHEMAS` as the single ordered schema authority, made candidate construction and publication transactional, preserved provider and sensor dimensions in storage usage, retained NULL T0A ownership where metadata does not durably own it, kept ordinary discovery metadata-only, and replaced weaker static evidence with measured production-behavior evidence.

I10R2 binds projection lineage at metadata level. It validates the lineage record type and identities, typed entries, manifest and projection binding, contiguous source order, row bounds, context binding, artifact existence, ordered artifact/source parity, source blob and acquisition existence, acquisition-to-blob equality, usable provenance, provider/venue/sensor/native-instrument identity, and granularity when both sides carry it. It does not call the physical lineage resolver, decompress T0A, recompute H1, or rescan T0A payload bytes.

I10R2 also validates the complete durable RecoveryJournal envelope before projecting the narrow quarantine view: exact record shape, recovery identity and run identity, valid object/problem/resolution fields, nullable string `action_kind` and `operation_id`, evidence reference, before/after state parsing, aware `registered_at`, semantic action identity, and coherent `StorageObjectType` mapping. Internal recovery object types remain legal only with their accepted null-storage mapping semantics.

## Evidence truth

- Lineage binding matrix: 10 rows, 9 `OK`, 1 deliberate counterfactual `FAIL`.
- Recovery envelope matrix: 10 rows, 9 `OK`, 1 deliberate counterfactual `FAIL`.
- Measurement parity matrix: 8 rows, 7 `OK`, 1 deliberate counterfactual `FAIL`.
- Every non-counterfactual row is mechanically observed and `OK`.
- Every `counterfactual_*` row is deliberately synthetic and `FAIL`.
- `result == "OK"` if and only if every required invariant is boolean true.

Historical I10 and I10R1 evidence is byte-identical and was not rewritten. Current R2 matrices and the R2 governance microseal regenerate byte-identically under normal verification; verification did not update committed evidence.

## Final verification truth

- Focused I10/I10R1/I10R2 plus DuckDB rebuild tests: **77 passed**.
- I09/I09R1 regression slice: **83 passed**.
- Required I07/I08 regression slice: **95 passed**.
- Complete storage suite: **1466 passed, 4 skipped**.
- Project test tree was partitioned into non-overlapping storage and non-storage collections: storage **1470 collected / 1466 passed / 4 skipped**; non-storage **1380 collected / 1379 passed / 1 skipped**; combined **2850 collected / 2845 passed / 5 skipped**. No path was omitted or executed twice. The monolithic `pytest tests/ -q` invocation was not claimed as passed.
- Ruff for the changed I10/I10R1/I10R2 scope and `duckdb_catalog.py`: passed. A broader storage-test lint invocation still reports two pre-existing I08 evidence-test findings (`F401`, `F811`).
- `compileall` for storage source and tests: passed.
- Targeted mypy for `duckdb_catalog.py`: passed. Repository-convention mypy reports 15 pre-existing errors outside this ratification scope.
- Product/test network calls: zero; the only network operation authorized for this checkpoint is the required Git push.
- External CI: no GitHub check-runs or status conclusions exist for this head; no external-CI pass is claimed.

## Historical immutability and diff firewall

Historical I08 and I09/I09R1 accepted evidence, all seven historical I10 artifacts, and all seven historical I10R1 artifacts remain byte-identical. This ratification adds only the ratification artifact and current-ledger governance/history update. Production implementation, provider code, I11 implementation, I12 implementation, and frozen Bloc-4 planning diffs are zero.

## Known non-blocking hardening notes

1. R2 evidence refusal helpers classify any thrown exception as a rebuild refusal. Focused executable tests separately require `DuckDBCatalogCorrupt`; future I15/I16 evidence hardening may narrow matrix causal typing.
2. DuckDB discovery intentionally does not duplicate every deeper physical `ProjectionLineageResolver` validation owned by the accepted I05 chain. I10R2 proves the metadata-level relation set required for discovery while preserving the no-T0A-rescan cost law.

These observations do not reopen G4-09 and do not authorize modifying I10 during this ratification.

## Governance transition

```text
PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED
  = OPERATOR_ACCEPTED

PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED
  = OPERATOR_ACCEPTED

PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED
  = OPERATOR_ACCEPTED

G4-09_CATALOG_REBUILD_GATE
  = IMPLEMENTATION_PASS

next_checkpoint_authorized
  = TRUE

next_checkpoint
  = SENSOR-B4-I11 POSTGRESQL OPERATIONAL METADATA REPOSITORY

authorized_scope
  = I11 ONLY

I12+
  = UNAUTHORIZED

research
  = FROZEN
```

I11 is authorized but was not started in this ratification. Research remains frozen. The next work must stop at the authorized I11 boundary unless a later operator instruction expands scope.
