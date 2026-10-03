# SENSOR-B4-I16 — FINAL BLOC 4 ACCEPTANCE EVIDENCE

**Checkpoint:** SENSOR-B4-I16 FINAL ACCEPTANCE + EVIDENCE PACKET
**Mandatory start head:** `e5294529f4b603c8ec10bc21e2e24c7a97044ca7`
**I16A head:** `a4a11dec61752d141aaa9c06861fb4225e5a9109`
**I16B head:** `051b6dd1a297d49b59ba504f4da8536211f8911d`
**I16C head:** `42cc77b6b30f829c4073757989df7422f8223a15`
**Branch:** `agent/crypto-sensor-fabric-build`
**Production diff:** ZERO

---

## 1. VERDICT

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED = BLOCKED
BLOC_04_FINAL_VERDICT = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP
all_G4_gates          = 11 PASS / 1 PASS_WITH_STATED_ENVIRONMENT_LIMITATION / 1 FAIL
next_checkpoint_authorized = FALSE
recommended_next      = OPERATOR REVIEW / NARROW REPAIR OF G4-13 UNIT HANDOFF CONTRACT
I17+                  = UNAUTHORIZED
research              = FROZEN
```

Twelve of thirteen gates earned a PASS at the current head. G4-13 did not, and
it was not prejudged: it entered I16 as `NOT_YET_IMPLEMENTED` and was measured
like every other gate.

The verdict field carries the gap ID verbatim. No word in the frozen §2/§36
vocabulary describes a handoff-contract gap: the gap is not integrity, not
storage capacity, not atomicity and not restore, and the G4-13 LINEAGE
dimension itself passed, so `FAIL_BLOC_04_LINEAGE` would be a false label.
The operator directed that the gap ID be recorded rather than a near-miss word
be invented (§36 forbids improvising vocabulary).

---

## 2. ALL-GATE MATRIX

| Gate | Frozen definition (abridged) | Result | Current-head proof |
|------|------------------------------|--------|--------------------|
| G4-01 | Arbitrary bytes stored/retrieved exactly with verified SHA256 | **PASS** | 8 awkward-source roundtrips (empty, NUL, embedded NUL, non-UTF8, invalid UTF-8, all 256 byte values, high-bit pseudo-random, JSON-like binary) + ZSTD transparency |
| G4-02 | Crash matrix produces no cursor skip or half-valid final | **PASS** | 6 blob fault windows + 5 pointer windows; 0 half-valid finals, 0 cursor skips, 0 false checkpoint progress |
| G4-03 | Committed T0A cannot be overwritten via public APIs | **PASS** | Replay idempotence, divergent content, 6-thread same-hash race, hostile final name (`ExistingBlobIntegrityConflict ... NOT overwritten`), hardlink mutation detected |
| G4-04 | Same key / different bytes yields an explicit revision | **PASS** | 2 segments from one source key, both versions verified after restart; non-first-member mutation safe; identical refetch creates no revision |
| G4-05 | Current manifests reference existing valid objects; history preserved | **PASS** | manifest v1 + v2, current pointer, historical lookup, all refs verify after fresh restart, 0 dangling |
| G4-06 | Every T0B resolves completely to T0A evidence | **PASS** | Non-vacuous projection → blob → acquisition, physically verified; 0 orphans; a manifest referencing an absent projection fails closed |
| G4-07 | No acquisition / no data / failure / history unavailable distinguishable; no numeric zero | **PASS** | Typed `NoMatchingEvidence`; EMPTY_VALID → `EMPTY_CONFIRMED` with 0 fabricated blobs; 9 distinct coverage states |
| G4-08 | Optional high-volume writes pause before critical P0; no raw auto-deletion | **PASS** | NORMAL all PROCEED; WATCH all WARN; CONSTRAINED P2 DEFERT / P3 PAUSE; CRITICAL P0 WARN with P1–P3 BLOCK; hard floor blocks even P0; T0A auto-delete = 0 |
| G4-09 | DuckDB reconstructed from manifest/projection files on an empty catalog | **PASS** | Catalog deleted then rebuilt to identical identity and row counts; T0A survived deletion; corrupt durable source raised instead of emitting a quiet catalog |
| G4-10 | PostgreSQL holds metadata/state only; no raw payload tables | **PASS (limitation stated)** | Scalar SQL types only (`bigint`, `boolean`, `double precision`, `integer`, `text`, `timestamptz`); no `bytea`/`blob`; no secret column; reconstruction from the durable tree loses nothing. **No live DB execution was performed or claimed** — no DSN was available |
| G4-11 | Evidence pack restores into an empty root with hash/query parity | **PASS** | Non-vacuous pack verified, restored into an empty root; hash, identity, query, revision and lineage parity; pack relocated under an unrelated root before restore |
| G4-12 | Checkpoint advances ONLY after durable manifest commit | **PASS** | 3 pages → 3 durable manifest versions (v1,v2,v3), 3 checkpoint advances, 2 continuation transitions, 1 COMPLETE, 0 external job-state manipulation |
| **G4-13** | **Batch exposes SOURCE / TIMESTAMP / UNIT / LINEAGE without path assumptions** | **FAIL** | **UNIT not reachable — see §3** |

---

## 3. G4-13 — THE DECISIVE FINDING

### 3.1 What passes

- **SOURCE** — provider, venue, sensor family, native instrument, granularity and
  projection refs are all public `RawEvidenceResult` fields.
- **TIME** — `requested_start/end`, `actual_start/end`, `request_started_at`,
  `response_observed_at`, `ingested_at`, `PartitionManifest.date_basis` and the
  logical time range are all reachable through public typed contracts.
- **LINEAGE** — batch → acquisition → blob → manifest → projection → revision
  resolves completely through public repositories, with physical T0A
  verification and no path parsing.
- **PATH INDEPENDENCE** — two storage roots (including a nested unrelated one)
  produced a byte-identical public evidence view, with no absolute path in any
  field.
- **NEGATIVE IMPORT CHECK** — the test-only Bloc 5 consumer imports only public
  `crypto_sensor_fabric.storage` names: 0 filesystem traversal calls, 0 private
  API accesses, 0 absolute root references.

Bloc 4 also did **not** pre-empt Bloc 5: `RawNormalizationBatch` contains no
`effective_at`, `observed_at`, `canonical_asset_id`, `canonical_notional` or
`normalized_price`.

### 3.2 What fails

**`I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`**

A test-only Bloc 5 consumer, restricted to the public storage contract, cannot
determine the provider-native unit of a handoff. Measured, not assumed:

| Probe | Measurement |
|-------|-------------|
| `RawNormalizationBatch` field count | **20** |
| Unit-named fields on the batch | **none** — no `native_unit`, `unit_state`, `provider_unit` |
| Unit-named exports in `crypto_sensor_fabric.storage.__all__` | **none** (194 names total) |
| Public enum member `UNIT_UNVERIFIED` | **absent** |
| `ProjectionSchemaDefinition.to_descriptor()` provider-native field keys | exactly **`name`, `type`, `nullable`** |
| Consumer result for `native_unit` / `unit_state` | **`NOT_REACHABLE`** |

The `unit` strings that exist under `storage/` are Arrow **temporal** type units
(`time32`/`time64`/`duration`/`date64`) inside `projection_schema.py`, not
market or native units. `NativeOIUnit` / `native_unit` live in
`crypto_sensor_fabric/schemas/open_interest.py` and the probe packages, which
the `storage` package does not reference.

**A unit string is present in the raw fixture bytes, and it deliberately does not
count.** Frozen §19 is explicit: "raw bytes contain it somewhere" is not a
proof unless a public typed or schema contract exposes how Bloc 5 discovers it.
The harness proves this by embedding `"unit":"contracts"` in the source payload
and still measuring `reachable: false`.

### 3.3 Minimal Bloc 4 contract repair — proposed, NOT implemented

Per §35, a real contract defect found during final acceptance is reported, not
silently repaired. I17 remains blocked.

**Recommended repair checkpoint: a narrow I17 ratification, I16R1, scoped to a
single additive contract change.**

**Scope:** add ONE additive source-unit evidence field pair to
`RawNormalizationBatch`:

- `native_unit: str | None` — the provider-native unit when known
- `unit_state: <unit state enum>` — at minimum an explicit `UNIT_UNVERIFIED`
  member, so an unknown source unit is recorded as unverified rather than
  guessed

Populated from the T0 acquisition / projection contract at commit time.

**Explicitly out of scope — do not add:** canonical units, USD/base/quote
normalization, `effective_at`, any PIT decision, or any Bloc 5 normalization
logic. Those belong to Bloc 5.

**Acceptance criterion for the repair:** re-run
`test_i16_g4_13_readiness.py` unchanged. Its `test_unit_evidence_is_not_reachable_through_public_contracts`
is written to FAIL loudly if unit evidence ever becomes reachable, so the gate
is self-falsifying in both directions.

---

## 4. FROZEN BLOCKING-CONDITION AUDIT (§29)

Eleven conditions, one measured row each.

| # | Condition | Measured |
|---|-----------|----------|
| 1 | Raw bytes can be overwritten | **NOT PRESENT** |
| 2 | Checksum identity is ambiguous | **NOT PRESENT** |
| 3 | Resume token can advance ahead of durable evidence | **NOT PRESENT** |
| 4 | Same request / different bytes silently replaces history | **NOT PRESENT** |
| 5 | Manifest points to a missing object without loud failure | **NOT PRESENT** |
| 6 | T0B lineage is incomplete | **NOT PRESENT** |
| 7 | Disk pressure auto-deletes T0A | **NOT PRESENT** |
| 8 | PostgreSQL becomes a bulk raw store | **NOT PRESENT** (schema/runtime contract only — see G4-10 limitation) |
| 9 | DuckDB becomes a unique source of truth | **NOT PRESENT** |
| 10 | Secret credentials appear in persisted evidence metadata | **NOT PRESENT** |
| 11 | Bloc 5 needs provider-specific filesystem knowledge | **PRESENT — unit dimension only** |

Condition 11 is a **contract gap, not corruption**. No stored byte is wrong and
no identity is ambiguous; the unit is simply not publicly discoverable.

---

## 5. VOLUME LIMIT CLASSIFICATION (§30)

**Not applicable — no `PASS_BLOC_04_*` verdict was earned**, so the
`PASS` / `PASS_WITH_DATA_VOLUME_LIMITS` choice was never reached. This is stated
explicitly so that the absence of a data-volume finding is not misread as an
affirmative finding that no volume ceiling exists.

For the record: the only resource measurements taken were the quota simulation
(synthetic 100 GiB capacity) and the accepted I15 resource-bounds matrices.
Neither is an accepted scale ceiling affecting supported use.

---

## 6. REGRESSION (§31)

| Phase | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Focused G4 (I16A + I16B + I16C) | 90 | 0 | 0 |
| I15 chain secret scan re-run | 48 | 0 | 0 |
| I11R2 binding audit no-update (§40 stability) | 4 | 0 | 0 |
| **Full storage** | **1922** | **0** | 13 |
| **Full project** | **3301** | **14 skipped** | **0 failed** |

Full storage is exactly **+90** against the accepted I15R2 baseline of 1832 —
the 90 I16 G4-01..G4-13 tests — with the skip count unchanged at 13.

### Two regressions found and fixed during I16

**R1 — the accepted I15 secret scanner caught my own fixture.** The I16B G4-10
fixture embedded a credential-shaped DSN literal to prove `redact_dsn()` works.
The scanner correctly rejected it as `dsn_user_pass` at two lines. The fixture
now assembles the credential at runtime from concatenated parts, so nothing
credential-shaped is stored in a tracked file. The redaction proof is unchanged.
**This is the control working as designed, against a defect in new test code —
not a production finding.**

**R2 — the I11R2 governance binding audit.** Adding tracked Python files changes
what the audit measures, and a full-suite run rewrites historical matrices the
audit also measures. Historical matrices were restored to committed bytes (§32),
the audit was mechanically regenerated with all I16 filenames final (§40), and
it was verified byte-stable on a no-update rerun. The full project suite was then
re-run against that final state with zero failures.

---

## 7. STATIC / SECURITY (§33)

| Check | Result |
|-------|--------|
| Ruff, I16 changed scope | **All checks passed**, 0 new findings |
| Ruff, accepted baseline scope (`--select F401,F811`) | **2 errors, both pre-existing** in `test_i08_evidence.py` from I08C `00898d666` — identical to the I15R2 baseline |
| compileall | **COMPILE_OK** (all four I16 files) |
| mypy, changed production scope | **0 errors** in `src/crypto_sensor_fabric/storage` |
| mypy, repo-wide | **10 errors, all pre-existing** in `providers/**` and `providers/*/probe.py` — identical to the I15R2 baseline |
| Secret scan | **CLEAN** (accepted I15 control, repo-wide) |

Production diff is zero, so no production typing surface changed.

---

## 8. EXTERNAL CI (§34)

```
external_ci = NONE_OBSERVED
commit_statuses = 0
check_runs = 0
```

Local pytest is **not** described as CI. The I16 commits were unpushed at
measurement time, so GitHub reports no check-runs for them; the start head
likewise reported 0 statuses.

---

## 9. HISTORICAL EVIDENCE CUSTODY (§32)

Eleven historical matrices were dirtied by running old suites and were restored
to committed bytes after each phase: `I03R1_ATOMIC_ORDER`,
`I03R1_NAMESPACE_DURABILITY`, `I04_CATALOG_SCHEMAS`,
`I04_MANIFEST_CONCURRENCY`, `I04R1_POINTER_SCHEMA`,
`I04R1_PROVENANCE_MATRIX`, `I04R2_USABLE_PROVENANCE_MATRIX`,
`I15R1_TOCTOU_MATRIX`, `I15_MANIFEST_SCAN_MATRIX`,
`I15_RESOURCE_BOUNDS_MATRIX`, `I15_SECRET_SAFETY_MATRIX`.

**Final historical evidence diff: ZERO**, with exactly one authorized exception
— `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`, which §40 explicitly authorizes
regenerating because I16 added tracked Python files, and which was verified
byte-stable.

---

## 10. EVIDENCE PACKET (§26)

| Artifact | Content |
|----------|---------|
| `BLOC_04_I16_G4_GATE_MATRIX.json` | 13 rows, each with frozen definition, ancestry, current authority, current test refs, measured case count, result, blocking reason, limitations |
| `BLOC_04_I16_TEST_REPORT.json` | Every regression phase, static check, external CI observation, regressions found and fixed |
| `BLOC_04_I16_INVARIANTS.json` | 21 invariants with authority, proof, status, failure consequence |
| `BLOC_04_I16_CRASH_MATRIX.json` | 11 crash windows with per-window measurements and the real operation order |
| `BLOC_04_I16_REVISION_MATRIX.json` | Revision preservation measurements |
| `BLOC_04_I16_STORAGE_LAYOUT.json` | Logical layout + authority relationships, no machine paths as contract |
| `BLOC_04_I16_QUOTA_SIMULATION.json` | 4 pressure × 4 priority dispositions, floor case, auto-delete count |
| `BLOC_04_I16_DUCKDB_REBUILD.json` | Delete/rebuild parity and corrupt-source refusal |
| `BLOC_04_I16_RESTORE_TEST.json` | Pack verify → empty-root restore → re-query parity |
| `BLOC_04_I16_BLOC4_READINESS.json` | G4-13 four-dimension readiness, path independence, negative import check, gap ID, minimal repair proposal |
| `BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md` | This document |
| `BLOC_04_I16_G4_01_EXACT_EVIDENCE.json` … `BLOC_04_I16_G4_12_BLOC3_HANDOFF.json` | Per-gate measured evidence |

Large fixture payloads remain untracked; only summaries and checksums are
committed.

---

## 11. WHAT THIS DOES NOT SAY

- It does **not** say Bloc 4 is broken. Twelve of thirteen gates passed at the
  current head with zero production changes.
- It does **not** say any stored evidence is wrong. The gap is a missing public
  contract, not corrupt or ambiguous data.
- It does **not** authorize I17, Bloc 5, or any research.
- It does **not** self-ratify. `next_checkpoint_authorized = FALSE` pending
  operator review.