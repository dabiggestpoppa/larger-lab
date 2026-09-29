# SENSOR-B4-I12 CHAIN — OPERATOR RATIFICATION (append-only)

> Mandate: SENSOR-B4-I12R2R1-RATIFY · Branch: `agent/crypto-sensor-fabric-build`
> Ratified at start HEAD: `707956cbc28230045eb2b26feb962cc2a7279f02` (== origin build)
> Remote main: `7c7816f382947bbc8a1f2154435fc436f2428fa8` (untouched)
> Research: FROZEN · No self-ratification of I13: this artifact records the OPERATOR's acceptance.

## 1. Ratified chain (strict ancestry verified via `git merge-base --is-ancestor`)

| Checkpoint | Final SHA | Status |
|---|---|---|
| I11 chain ratified | `adf1dd1f18431caf0a91940a0d952425f73ec345` | ANCESTOR-OK |
| I11R2C-R1 corrected anchor | `bde337176b4af7bafa96ef0743ec07cdabf5dbe6` | ANCESTOR-OK |
| I12 final | `0fa09eda3d075742e8f7f048a69882ce3ab705a7` | ANCESTOR-OK |
| I12R1 final | `76042ca4c4abf17884980fca84a7aa1ba2d680c6` | ANCESTOR-OK |
| I12R2 final | `cedf923e88ef0958cbf056f752351a350833ee85` | ANCESTOR-OK |
| I12R2R1 final | `707956cbc28230045eb2b26feb962cc2a7279f02` | ANCESTOR-OK |

14 first-parent commits from the I11 ratification anchor to HEAD. No rewritten history.

## 2. I12 core contract (accepted)

- `RawEvidenceQueryService`, `RawArtifactReader`, `RawProjectionReader`,
  `RawReplayCursor`, `Bloc5Handoff` / `RawNormalizationBatch` path — provider-independent
  local evidence access.
- Authority hierarchy: T0A bytes = blob store; blob/acquisition truth = durable I04
  repositories; manifests = accepted manifest repository; T0B = projection + lineage
  repositories; revision truth = I06 `SourceRevisionRegistry`; DuckDB = rebuildable
  discovery only; Postgres = operational metadata only. Provider network is NOT part of
  query correctness.

## 3. I12R1 repairs (accepted)

- (A) revision policies wired into `execute()` BEFORE result publication and limit
  (limit LAST; ambiguity cannot be hidden by truncation).
- (B) include_t0a / include_t0b / projection_schema_ids enforced end-to-end on returned
  `RawEvidenceResult` fields.
- (C) replay dispatch: typed `ReplayOrder` + value semantics; zero `is`-dispatch on
  public strings (structural grep = 0 hits).
- (D/E/F) manifest current-pointer alias, blob-metadata alias, acquisition alias:
  canonical physical locator proof + uniqueness; FAIL CLOSED, no silent dedupe.
- I06 alias guard = EXISTING_LAW_SUFFICIENT (revisions.py untouched).

## 4. I12R2 fail-safe laws (accepted)

- `revision_registry` REQUIRED for EVERY query execution, including default
  ERROR_ON_AMBIGUITY → typed `RevisionAuthorityUnavailable`; no default pass-through.
- No bypass switches: `allow_unresolved_revisions` / `unsafe_revision_passthrough` /
  `legacy_mode` = 0 hits across `src/crypto_sensor_fabric/`.
- Representation law: include_t0a ⇒ T0A in result; include_t0b ⇒ eligible T0B required;
  both ⇒ both; neither ⇒ `QueryValidationError`. Requested T0B never silently satisfied
  by T0A; schema mismatch → `ProjectionSchemaUnsupported`.

## 5. I12R2R1 evidence-custody law (accepted)

- `BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX.json` restored to exact
  `76042ca4` bytes; current SHA-256 =
  `039580c07b7e6f65a74f892f513dcba7ccdc5f6f5e385e82f13595e6e437a5f3` (verified live).
- Historical row `schema_mismatch_with_T0A_fallback_documented` present as I12R1 truth;
  current I12R2 matrix separately proves `both_requested_schema_mismatch_refused` with
  `ProjectionSchemaUnsupported` (verified live). Dual truth coexists.
- Historical checkpoint evidence is checkpoint-scoped (SHA pin + Git-object + structural
  verification); the four still-compatible I12R1 matrices retain regenerate-and-compare.

## 6. Historical vs current evidence doctrine (ratified for future Sensor checkpoints)

HISTORICAL CHECKPOINT EVIDENCE must preserve the behavior measured at that checkpoint.
Later production changes never cause historical evidence regeneration. When semantics
are superseded: old artifact → immutable checkpoint-scoped verification; new checkpoint
→ new measured current-behavior artifact. Never rewrite the old claim to agree with
current production.

## 7. Final regression evidence (repository-recorded, no files changed pre-ratification)

| Suite | Result |
|---|---|
| I12R2R1 focused | 12 passed |
| Full storage | 1611 passed, 25 skipped, 0 failed |
| Full non-storage | 1379 passed, 1 skipped, 0 failed |
| Full project (disjoint partition A∪B) | 2990 passed, 26 skipped, 0 failed |

Known nonblocking: `test_blob_store_adversarial` transient Windows concurrency timing
failure (passed twice in isolation; full rerun green; final suite green). Not classified
as a production defect without reproducible evidence.

## 8. Read-only / network truth

Query/replay paths require no provider network, external product network, cloud
database, Postgres, or DuckDB for correctness. No delete/overwrite/repair/quarantine/
revision-declaration/manifest-mutation/resume/recovery mutation crosses the
research-consumer boundary.

## 9. Bloc-5 handoff boundary (confirmed)

`RawNormalizationBatch` exposes raw facts/provenance only; does NOT establish canonical
asset/side, normalized notional/OI/funding/liquidation, or effective-at market truth.

## 10. External CI truth

external_ci = NONE_OBSERVED (0 statuses / 0 check-runs at ratification). No CI success claimed.

## 11. Authorization boundary (exact)

- PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED = OPERATOR_ACCEPTED
- PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED = OPERATOR_ACCEPTED
- PASS_SENSOR_B4_I12R2_FAIL_SAFE_QUERY_CONTRACT_SEALED = OPERATOR_ACCEPTED
- PASS_SENSOR_B4_I12R2R1_EVIDENCE_IMMUTABILITY_SEALED = OPERATOR_ACCEPTED
- G4-10_OPERATIONAL_METADATA_GATE = IMPLEMENTATION_PASS (unchanged)
- G4-11_EXPORT_RESTORE_GATE = NOT_YET_IMPLEMENTED / PENDING_I13 (I13 earns it; do NOT mark PASS here)
- next_checkpoint_authorized = TRUE
- next_checkpoint = SENSOR-B4-I13 EXPORT / BACKUP / RESTORE PACK
- authorized_scope = I13 ONLY
- I14+ = UNAUTHORIZED; research = FROZEN

Frozen I13 scope: checksum-verified LOCAL export/restore only (fresh-root restore,
catalog rebuild, hash parity; G4-11 passes only when a fixture evidence pack restores
into an empty root with matching hashes and matching query results). Local/offline
only — NO cloud backup, S3/GCS/Azure, live provider calls, remote DB, network transfer,
or Bloc-3 adapter integration. Carry-forward security boundary: export destination
boundary checks, no path traversal, no symlink escape, no secret leakage, verified
checksums, restore into empty root, bounded archive extraction/restore resources.

Nothing in this run implements I13. Production diff from `707956cb` = zero.
