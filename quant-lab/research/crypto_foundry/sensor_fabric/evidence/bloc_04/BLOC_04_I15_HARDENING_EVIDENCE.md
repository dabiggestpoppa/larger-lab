# BLOC_04_I15_HARDENING_EVIDENCE

**Mandate:** SENSOR-B4-I15 — HARDENING AND SECURITY
**Branch:** agent/crypto-sensor-fabric-build
**Base (start) HEAD:** `a68884627fc5af9064693f3819d0bea288d8c8d4`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Scope:** secret safety / path containment / symlink escape / corruption handling / resource bounds over ALREADY ACCEPTED Bloc 4 surfaces. I16+ UNAUTHORIZED. G4-13 NOT EARNED. Research FROZEN.

**Production diff:** exactly ONE file — `src/crypto_sensor_fabric/storage/paths.py` (`resolve_under_root`). No provider, storage-architecture, query-semantics, revision-semantics or normalisation changes.
**Historical evidence diff:** ZERO (7 old I03R1/I04 artifacts carry CRLF-only churn, allowlisted; never staged/normalised).

Published I15 matrices (this checkpoint only):

| Matrix | Rows |
|---|---|
| BLOC_04_I15_SECRET_SAFETY_MATRIX.json | see `rows_total` |
| BLOC_04_I15_PATH_TRAVERSAL_MATRIX.json | see `rows_total` |
| BLOC_04_I15_SYMLINK_ESCAPE_MATRIX.json | see `rows_total` |
| BLOC_04_I15_CORRUPTION_MATRIX.json | see `rows_total` |
| BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json | see `rows_total` |
| BLOC_04_I15_MANIFEST_SCAN_MATRIX.json | see `rows_total` |

---

## 1. RED finding — static symlink escape (failure-first)

**Attack path:** a link planted at an intermediate directory inside the configured storage root (`blobs/`, `staging/`) redirected a blob WRITE outside the configured root.

- Configured root: the T0A storage root.
- Symlink target: a directory OUTSIDE the root.
- Operation attempted: `LocalBlobStore.put_bytes(...)` (public API).
- Outside-root mutation produced: YES.
- **Pre-repair result = UNSAFE.**

**Root cause:** `resolve_under_root()` was LEXICAL-only; its docstring deferred symlink escape to a later hardening checkpoint.

## 2. Repair — single containment choke point

`resolve_under_root()` now resolves BOTH the root and the candidate through the filesystem and refuses (typed `ValueError`) any target whose REAL location is not the root itself or a descendant of it; it returns the UN-resolved path. **Chosen law A:** a configured DATA ROOT MAY ITSELF be a symlink — its resolved target is the authority (containment is relative to the RESOLVED root).

- **Post-repair:** same attack → typed refusal; outside-root mutation count = 0.
- A link pre-placed at the EXACT final artifact name is refused by typed containment OR `AtomicPublishError` (no-replace publication); the outside file is untouched.
- **Bypass audit:** the hardened helper is the single filesystem containment choke point for caller-influenced keys (blob_store, catalog, manifests, json_catalog/duckdb_catalog, projection resolver/projections, export, recovery). No audited module opens a directly-joined caller key.

**STATIC_SYMLINK_ESCAPE = SEALED.**
**TOCTOU_SYMLINK_SWAP = KNOWN_LIMITATION** — validate-then-swap race safety is explicitly NOT claimed (static escape rejection only).

## 3. Secret safety

- Repository secret scan over source / tests / evidence roots: **0** credential-shaped findings after a NARROW allowlist (TEST_ONLY sentinels + documented EXACT accepted redaction-fixture literals only — never "ignore all token/secret", never a tests-wide or entropy-wide suppression).
- **Self-match exclusion:** the scanner's own regex/source definitions are not counted as findings.
- **Detection proof:** a separate temporary fixture carrying runtime-built realistic synthetic credential SHAPES (bearer / AWS access-key / JWT) IS detected — proving the allowlist is not a blanket suppression.
- **Runtime sentinel:** secret-bearing request/auth metadata is refused typed (`SecretBearingAcquisitionMetadata`); the error names no value; a recursive durable-tree scan finds **0** sentinel occurrences (per-case, isolated). Raw provider response bytes remain exact evidence (never redacted). Accepted URL/header/DSN sanitizers proven.
- **Error-message safety:** secret-bearing path/URL metadata errors carry no sentinel; no post-refusal durable failure/quarantine metadata carries it.

## 4. Path containment

- Traversal matrix (short, mixed, absolute POSIX/Windows, drive-relative, UNC, `file://`, encoded, double-encoded, NUL, Unicode lookalike, trailing dot/space, Windows reserved names, extended-length device path, shell-style expansions): every hostile key **typed-refused or literally contained**.
- **Outside-root mutations across every attack = 0.**
- Provider-supplied path-like values enter keys ONLY through the canonical percent-encoding (opaque, literal-safe) — identifier safety is NOT confused with path safety.

## 5. No shell interpolation

- **Structural:** zero `subprocess` / `os.system` / `shell=True` / `Popen` in Bloc 4 storage.
- **Behavioural:** a shell-metacharacter instrument (`…; touch PWNED && …`) persists as DATA only; **0** shell artifacts.

## 6. Hardlink audit

Mutating accepted immutable evidence through a hardlink is **detected typed** by content verification (`QUARANTINED_INTEGRITY_FAILURE`) — never silently accepted.

## 7. Corruption handling (FRESH-RESTART)

Fresh repository instances used throughout; an in-memory cached refusal is never counted.

| Subsystem | Mutation | Outcome |
|---|---|---|
| T0A payload | byte tamper after commit | QUARANTINED_ACCEPTED (`QUARANTINED_INTEGRITY_FAILURE`) |
| Manifest fragment | overwrite after commit | FAIL_CLOSED_TYPED (fresh read; no repair-on-read) |
| Acquisition fragment | overwrite after commit | FAIL_CLOSED_TYPED (fresh read) |
| DuckDB | corrupt/delete db file | REBUILD_DISPOSABLE_STATE from durable evidence |
| Recovery | hostile staging state | read-only scan; nothing created/deleted; valid T0A preserved; hostile file never promoted |

T0B, revision, job/checkpoint and export corruption are cited to EXISTING measured suites (I05R1-R4, I06 + I14R2 `RESTART_CORRUPTION` 6/6, I07R1I, I13) — no generic "exception happened" rows.

## 8. Resource bounds

- **Logical 1 GiB-equivalent streaming hash:** memory bounded by the configured chunk, never by source size. **T0A = SAFE_BY_STREAMING_API** (64 MiB-equivalent virtual stream written at 256 KiB chunks; dedupe → `REUSED_EXISTING` without double-buffering).
- **SCAN_SCALE (frozen benchmark honoured literally):** `manifest_rows_created = 10,000`, `manifest_rows_scanned = 10,000`, `invalid_rows = 0`, `duplicate_logical_ids = 0`, `fragment_files = 10,000` (one canonical parquet row per fragment — the accepted catalog physically requires `len(rows) == 1`), deterministic (sorted) order, peak scan memory ≈ 56 MiB. Corpus construction was EXPLICIT benchmark-fixture setup with the canonical serializer/schema into the production on-disk layout; the ACTUAL scan ran PRODUCTION reader code (`RecoveryEngine._all_manifests` → `read_fragment` + `_manifest_from_row`). Pointer/parquet-object counts were NEVER relabelled as manifest rows.
- **WRITE_SCALE measured SEPARATELY:** 200 real `append_partition_manifest` appends = 24.44 s (full durability re-proof per append). No 10,000-append throughput claim.
- **DuckDB scale:** rebuild + read-only query over 150 projection identities completes.
- **Export/restore:** object-count / object-byte / total-byte / manifest-byte ceilings + injectable free-space law.
- **Query bound:** `RawEvidenceQuery.limit` is the explicit caller result bound; the reader materializes the gated set (no invented pagination semantics).
- **Revision chain (200):** ALL / FIRST / LATEST / EXACT exact; no recursion failure; no silent truncation.
- **Disk-watermark MATRIX (accepted I09 semantics preserved):**

| Pressure | P0 | P1 | P2 | P3 |
|---|---|---|---|---|
| NORMAL | PROCEED | PROCEED | PROCEED | PROCEED |
| WATCH | WARN | WARN | WARN | WARN |
| CONSTRAINED | PROCEED | PROCEED | DEFER | PAUSE |
| CRITICAL | WARN | BLOCK | BLOCK | BLOCK |

Absolute floor blocks even P0. **No automatic T0A deletion.** Resource ceilings are CONFIGURATION: independent fixtures prove different safe limits leave scientific evidence identity unchanged.

## 9. Regressions (after final code)

Focused I15: `test_i15_hardening.py` 17 passed; `test_i15_resource_bounds.py` 12 passed; `test_i15_manifest_scan_scale.py` 2 passed.
Storage subsystem regressions green: core path/blob/catalog/manifest 295 passed (1 pre-existing known concurrency flake — passes on retry, reproduced at untouched baseline); projections/revisions/duckdb/export/quota/atomic 300 passed; recovery/job-state/I04 212 passed (1 skipped); I05-I07 123 passed; I08-I10 223 passed; I11-I12 141 passed (21 skipped, postgres BLOCKED_ENVIRONMENT); I13-I14 143 passed (2 skipped); checksums/models/serialization/provenance 314 passed. **ZERO deterministic failures.**

Tooling: compileall OK; Ruff clean on changed scope (2 pre-existing findings in untouched `test_i08_evidence.py`); mypy storage = 10 errors all pre-existing in probes/providers (0 new). `external_ci = NONE_OBSERVED`.

**Pre-existing defect surfaced and fixed forward:** the I14R2-RATIFY committed ledger carried 42 CRLF sequences and failed `test_job_state_r1i.py::test_ledger_is_utf8_lf` at UNTOUCHED HEAD. The I15 ledger append normalises the document to UTF-8 LF; no prior commit amended.

## 10. Governance

```
SENSOR-B4-I15
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED          = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                            = FALSE
recommended_next                                      = OPERATOR REVIEW OF SENSOR-B4-I15
I16+                                                  = UNAUTHORIZED
G4-13                                                 = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                              = FROZEN
```

No self-ratification. I16 not started. STOP after I15.
