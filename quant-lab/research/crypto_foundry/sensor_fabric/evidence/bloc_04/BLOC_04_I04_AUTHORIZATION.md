# BLOC 4 — I04 AUTHORIZATION EVIDENCE (SENSOR-B4-I04-AUTH)

Checkpoint: SENSOR-B4-I04-AUTH — OPERATOR CONFIRMS I03/I03R1 ACCEPTANCE AND
AUTHORIZES I04 ONLY
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA (mandatory): `fb00a58775a39b516247bcca7f693a96d45a3086`
  (SENSOR-B4-I03R1-RATIFY)
Ending SHA: this commit (governance-only; no implementation code)
Commit type: GOVERNANCE ONLY — no runtime modules, tests or evidence beyond
this authorization record and the implementation-ledger update were changed.

## 1. Operator decisions

The operator CONFIRMS the accepted I03/I03R1 verdicts and authorizes I04:

| Verdict | Decision |
|---|---|
| `PASS_SENSOR_B4_I03R1_DURABILITY_NAMESPACE_SEALED` | `OPERATOR_ACCEPTED` |
| `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND` | `OPERATOR_ACCEPTED` |

Readiness flags confirmed TRUE:

```text
ATOMIC_FILESYSTEM_BACKEND_READY = TRUE
T0A_BLOB_BACKEND_IMPLEMENTED    = TRUE
```

Authorization is EXCLUSIVELY:

```text
SENSOR-B4-I04  ACQUISITION + MANIFEST REPOSITORY
```

`SENSOR-B4-I05` is NOT authorized and MUST NOT be started.

## 2. I03R1 root-policy prose reconciliation (chronological, §3)

The historical I03R1 seal evidence
`BLOC_04_I03R1_DURABILITY_NAMESPACE_SEAL_EVIDENCE.md` remains IMMUTABLE
history.  Its prose ("configured storage root must pre-exist") does NOT match
the accepted implementation: `LocalBlobStore` permits a missing configured
root, and the first put durably creates the missing namespace components from
the deepest existing ancestor via `ensure_durable_directory()` (explicitly
allowed by the operator checkpoint).  The chronological correction is
recorded HERE — the implementation is safe and is NOT changed to make old
prose true.

ACTUAL ROOT POLICY (accepted, effective for I04 repositories too):

- existing root directory → use it;
- existing non-directory → fail closed (`InvalidStorageRoot`);
- missing root → MAY be created through durable directory-chain creation
  from the deepest existing ancestor (`ensure_durable_directory_chain()`);
- no blind recursive `os.makedirs()` + durability assumption anywhere.

## 3. I04 authorization — scope envelope (only what I04 may build)

- Durable local metadata/catalog layer over the accepted I03 T0A backend:
  `EvidenceBlob` metadata, `AcquisitionRecord` history, append-only
  `PartitionManifest` versions, current-partition pointer semantics,
  referential integrity between metadata and physical T0A, and
  concurrency-safe manifest advancement.
- Immutable dataset-style Parquet catalog fragments (PyArrow, already in
  project dependencies) under `<t0_root>/catalogs/manifests/`.
- Local filesystem partition-scoped writer lock + expected-current CAS.
- Tests: referential integrity; concurrent manifest versioning; pointer
  crash matrix.

NOT authorized (DO NOT implement in I04): T0B Parquet raw-record projections
(I05), ProjectionLineage, SourceRevision registry, StorageJobState
persistence, resume advancement, DuckDB, PostgreSQL, raw query service,
Bloc 3 live integration, provider network acquisition, blob/projection
queries, recovery scanner.

## 4. No implementation in this commit

`git show --stat` of this commit contains ONLY this authorization evidence and
the implementation-ledger update.  No `storage/` runtime module, no test
file, no dependency change, no network call was made for this commit.

## 5. Next checkpoint

The sole authorized next checkpoint is **SENSOR-B4-I04 — ACQUISITION +
MANIFEST REPOSITORY** (target `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`).
`SENSOR-B4-I05` remains NOT started and MUST NOT begin.