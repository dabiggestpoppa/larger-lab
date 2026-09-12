# BLOC 4 — I02R1 OPERATOR RATIFICATION EVIDENCE (SENSOR-B4-I02R1-RATIFY)

Checkpoint: SENSOR-B4-I02R1-RATIFY — OPERATOR ACCEPTS I02R1/I02, RECONCILES
TEST-NODE TRUTH, AUTHORIZES I03 ONLY
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA (mandatory): `e525779a4c214968de4f6c7a728710490cb5939e`
  (SENSOR-B4-I02R1D — ledger reconciliation)
Ending SHA: this commit (governance-only; no implementation code)
Commit type: GOVERNANCE ONLY — no runtime modules, tests or evidence beyond
this ratification record and the implementation-ledger update were changed.

## 1. Operator decisions

The operator ACCEPTS both proposed I02R1/I02 verdicts:

| Verdict | Decision |
|---|---|
| `PASS_SENSOR_B4_I02R1_CANONICAL_PATHS_SEALED` | `OPERATOR_ACCEPTED` |
| `PASS_SENSOR_B4_I02_CONTENT_ADDRESSING_PATHS_CHECKSUMS` | `OPERATOR_ACCEPTED` |

Readiness flags recorded as TRUE:

```text
CONTENT_ADDRESSING_READY  = TRUE
PATH_CONTRACT_READY       = TRUE
CHECKSUM_PRIMITIVES_READY = TRUE
```

Authorization is EXCLUSIVELY:

```text
SENSOR-B4-I03  ATOMIC FILESYSTEM BACKEND
```

`SENSOR-B4-I04` is NOT authorized and MUST NOT be started.

## 2. Historical evidence preserved

- `evidence/bloc_04/BLOC_04_I02_CONTENT_ADDRESSING_EVIDENCE.md` — immutable,
  NOT rewritten (constraint §3 of the checkpoint order).
- `evidence/bloc_04/BLOC_04_I02R1_CANONICAL_PATH_SEAL_EVIDENCE.md` — immutable
  historical checkpoint evidence, NOT rewritten.

No passing behavior was altered to make any historical number come true.
Truth is recorded in the section below; historical prose remains historical.

## 3. Test-count truth reconciliation

### 3.1 Method

- `pytest --collect-only -q` over `quant-lab/tests/crypto_sensor_fabric/storage`
  and over the full test tree (pytest 8.x, `.venv` Python 3.12.13).
- Storage suite executed: `259 passed` (0 failed) — collection and execution
  totals agree.

### 3.2 Observable node accounting (this checkout, HEAD e525779a)

| Storage test file | Collected nodes |
|---|---|
| `test_enums.py` | 18 |
| `test_models.py` | 81 |
| `test_serialization.py` | 16 |
| `test_checksums.py` | 35 |
| `test_paths.py` | 109 |
| **storage total** | **259** |

Full suite: **1639 collected** = 1638 runnable + 1 env-gated live-smoke skip
(`sensor_network_smoke` marker, fail-closed without `SENSOR_NETWORK_SMOKE=1`).
This matches the I02R1 seal evidence's reported runtime result
"1638 passed / 0 failed / 1 skipped".

### 3.3 Path-suite growth (I02 → I02R1)

```text
I02 path suite      87 nodes
I02R1 final path   109 nodes
NET                 +22 nodes
```

Net growth is +22, matching the operator's stated net of +22 for both the
path suite AND the full suite (collected 1617 → 1639; passed 1616 → 1638).

### 3.4 Historical wording discrepancy — recorded, not rewritten

The I02R1 seal evidence (§9) and the I02R1A commit message/ledger say
"35 new I02R1A tests" and the I02R1A commit additionally reported a
"storage suite: 272 passed". The observable collectible-node accounting is:

- **I02R1A contributed +20 nodes**, not +35: 16 new test functions, of which
  `test_over_escaped_safe_char_rejected` is 5-way parametrized
  (`%41/%61/%30/%5F/%2D`) → 15 + 5 = 20. The "+35" wording counts neither
  pytest functions nor collectible nodes; it overstates the node addition.
- **I02R1B contributed net +2 nodes**: 3 new full-SHA projection-key tests
  (`test_full_digest_in_filename`, `test_hash_prefix_length_removed_from_canonical_api`,
  `test_collision_adversarial_same_prefix`) replace the legacy
  `test_bad_prefix_length_rejected` (1 node removed).
- **Net I02R1 = +22 nodes** (20 + 2), which exactly matches the observable
  87 → 109 path-suite and 1617 → 1639 full-suite deltas.
- The I02R1A-era "272" storage-suite total is not reproducible from the
  committed tree: 237 (pre-I02R1 storage) + 20 = 257 at I02R1A, + 2 = 259 at
  I02R1B/HEAD. The current observable truth is **259**, which is recorded here
  and in the ledger.

Corrected cumulative table (observable):

| Checkpoint | Storage nodes added (net, observable) |
|---|---|
| I02C (checksums + paths) | +122 (35 + 87) |
| I02R1A (canonical decoding) | +20 |
| I02R1B (full-SHA projection key) | +2 |
| **Storage total** | **259** |

## 4. I03 authorization — scope envelope (only what I03 may build)

- `quant-lab/src/crypto_sensor_fabric/storage/` additions: `compression.py`,
  `atomic.py`, `blob_store.py` (one-to-one responsibilities).
- Tests: `quant-lab/tests/crypto_sensor_fabric/storage/test_compression.py`,
  `test_atomic.py`, `test_blob_store.py`.
- Local filesystem backend only; configurable runtime data root; staging +
  exact-source streaming write + optional ZSTD wrapper + flush + fsync +
  staged verification + same-filesystem validation + no-clobber atomic
  publication + parent-directory fsync + immutable final blob guard +
  blob exists/open/verify + idempotent duplicate behavior + crash/fault
  injection tests.
- Nothing else: no AcquisitionRecord repository, no partition manifests, no
  current pointers, no source-revision registry, no durable StorageJobState,
  no resume advancement, no T0B Parquet projections, no DuckDB, no PostgreSQL,
  no backfill, no live recording, no Bloc 5 normalization.

## 5. No implementation in this commit

`git show --stat` of this commit contains ONLY this ratification evidence and
the implementation-ledger update. No `storage/` runtime module, no test file,
no dependency change, no network call was made for this commit.

## 6. Next checkpoint

The sole authorized next checkpoint is **SENSOR-B4-I03 — ATOMIC FILESYSTEM
BACKEND** (target `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`).
`SENSOR-B4-I04` remains NOT started and MUST NOT begin.