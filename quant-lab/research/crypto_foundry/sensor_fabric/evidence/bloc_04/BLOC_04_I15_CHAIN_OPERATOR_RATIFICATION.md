# BLOC_04_I15_CHAIN_OPERATOR_RATIFICATION

**Mandate:** SENSOR-B4-I15R2-RATIFY — operator acceptance of the complete
hardening / security / concurrency chain, plus I16 authorization ONLY
**Branch:** agent/crypto-sensor-fabric-build
**Mandatory start HEAD:** `2a856e656f9da4b2749fa1b999e58ae26f4234be`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Scope:** I15 -> I15R1 -> I15R2 OPERATOR RATIFICATION ONLY.
I16 NOT implemented in this run. I17+ UNAUTHORIZED. G4-13 NOT EARNED.
Research FROZEN.

This document is **append-only acceptance evidence**. It does NOT rewrite the
I03–I14, I15, I15R1 or I15R2 published matrices, nor any prior ledger section.
It ratifies them and records the deltas that operator review surfaced.

---

## 1. Accepted final head and strict ancestry

**Accepted final head:** `2a856e656f9da4b2749fa1b999e58ae26f4234be`

The complete I15 chain is a **strict linear ancestry** of seven commits, each a
direct parent of the next. No merge commit, no rebase, no amend, no squash, no
force push, no rewritten history.

| # | SHA | Subject |
|---|---|---|
| 1 | `a68884627fc5af9064693f3819d0bea288d8c8d4` | I14 ratification / I15 authorization |
| 2 | `bc6d5e059f3d039235dbcc4769658819146ff7db` | SENSOR-B4-I15: seal storage hardening |
| 3 | `5d3dab104e8a8191643fe46ce1953a90918037e1` | SENSOR-B4-I15R1: TOCTOU + fresh corruption |
| 4 | `67fd2271a4137403d68c236e3e46dc2a97528389` | SENSOR-B4-I15R1-VERIFY: independent verification correction |
| 5 | `b81350a6d6b95f697957826ebdd1bafb93182947` | I15R2A: single shared canonicalization authority |
| 6 | `4ad67d393d4ecc3ed3c2bc801733acc081bc8dcb` | I15R2B: idempotent directory creation |
| 7 | `2a856e656f9da4b2749fa1b999e58ae26f4234be` | I15R2C: I15R2 evidence, governance, append-only correction |

Verified at ratification: `git merge-base --is-ancestor` for all seven SHAs
against HEAD returned true; `git log --merges a68884627..HEAD` is empty.

---

## 2. REPORT_CORRECTION — prose understated the RED baseline incidence

Operator review found a **prose-vs-matrix discrepancy** in the I15R2 baseline
record. The committed machine-readable matrix is **authoritative**.

| | trials | writers | workers | green | red | UnsafeObjectKey | components-empty |
|---|---|---|---|---|---|---|---|
| committed matrix `baseline_reproduction_at_start_head` | 15 | 8 | 120 | **8** | **7** | **12** | **4** |
| prior prose summary (I15R2 correction §4.1) | 15 | 8 | 120 | 11 | 4 | 0 | 4 |

Both records are at the same start head `67fd2271a4137403d68c236e3e46dc2a97528389`.

**REPORT_CORRECTION.** The baseline prose summary **understated the RED
incidence**: it reported 11 green / 4 red and `UNSAFE_OBJECT_KEY` x0. The
**authoritative committed evidence is 8 green / 7 red, 12 `UnsafeObjectKey`
worker failures, 4 components-empty worker failures** (and
`ATOMIC_PUBLISH_SECURITY_ERROR` = 0, `OTHER` = 0).

**Root cause of the divergence.** The matrix's baseline row carries frozen
`BASELINE_*` constants drawn from the earlier I15R1-era probe rather than
values re-measured by the final harness; the prose figure came from a separate
`run_identical_writer_trial`-based probe that happened to sample a run in which
the `UnsafeObjectKey` class did not appear. The two artifacts therefore
describe different samples of the same start head.

**Disposition.** The matrix was **NOT modified** — it is the authoritative
record. Defect A's `UnsafeObjectKey` class is now attested in the committed
baseline at real incidence (12 worker failures), which strengthens rather than
weakens the I15R2A repair case. **This correction does NOT change the
post-repair verdict**, which is separately measured (§5, §6) and independently
re-measured green by the ratification battery (§11).

---

## 3. Ratified security laws

### 3.1 Static symlink containment law

Ratified from `BLOC_04_I15_SYMLINK_ESCAPE_MATRIX.json` — **7/7 OK**, and
re-affirmed by `BLOC_04_I15R2_PATH_CANONICALIZATION_MATRIX.json`
(`symlink_containment_not_weakened`, outside-root mutations = 0, publish
refused `AtomicPublishSecurityError`, resolve refused).

Containment is judged against the **physical** target reached by real-path
resolution, so a link planted inside the root cannot widen the boundary. All
publication is re-validated through the containment choke point; the choke
point is a single structural choke point audited by test, not a convention.

### 3.2 Destination TOCTOU custody law

Ratified from `BLOC_04_I15R1_TOCTOU_MATRIX.json` — **13/13 OK**,
`outside_root_mutation_total` = 0, `foreign_bytes_published` = 0.

The destination namespace is custody-checked at the real check/use seam, not
merely at intent time. `check_use_swap_blob_namespace` re-probes identity
immediately before the publication act, so a destination directory swapped
between check and use is refused rather than published into. The pre-repair
counterfactual (`check_use_seam_pre_repair_counterfactual_escape`) still
demonstrates the escape it exists to prove, so the seal is **earned**, not
assumed.

### 3.3 Staged-source substitution law

Ratified from the same matrix — `check_use_swap_staging_source_namespace` and
`staged_source_substitution_pre_repair_counterfactual`, both OK.

The staging source is inode-anchored. A staged file swapped for an attacker
payload between write and link is refused, because publication binds to the
anchored source identity rather than to the path spelling. Staging escape is
likewise refused.

### 3.4 Root-as-link law A

**Preserved.** A configured storage root MAY itself be a link. Its resolved
physical target becomes the authority, and children remain bounded beneath that
resolved authority. Verified by `root_as_link_law_a_preserved`
(`root_link_accepted` true, `root_link_still_bounds_children` true) and by the
I15R1 `root_symlink_law_a_preserved` row.

### 3.5 Fresh corruption law

Ratified from `BLOC_04_I15R1_FRESH_CORRUPTION_MATRIX.json` — **10/10 OK**, every
row with `fresh_instance = true` and `repair_on_read = false`. The string
`UNSAFE_SILENT_ACCEPTANCE` appears nowhere in the matrix.

Rows: T0A, acquisition, manifest, T0B, revision, job/checkpoint, export,
DuckDB disposable, DuckDB bad-source, recovery/quarantine. Corruption is never
silently accepted on a fresh instance with repair-on-read disabled.

### 3.6 DuckDB two-law model

- **Law A —** DuckDB itself corrupt or deleted: it is **disposable** and is
  rebuilt from durable evidence.
- **Law B —** durable evidence corrupt: the rebuild **fails closed**; bad
  durable truth is NOT canonized into DuckDB.

DuckDB remains **non-authoritative**. Both rows measured OK
(`fresh_duckdb_disposable`, `fresh_duckdb_bad_source`).

### 3.7 Hardlink integrity law

Ratified from `BLOC_04_I15_CORRUPTION_MATRIX.json` —
`hardlink_mutation_detected` OK: a hardlink mutation surfaces as a **typed
integrity failure**, never as silent acceptance.

---

## 4. Shared canonical real-path authority (ratified)

`paths.canonical_real_path()` is **THE** filesystem canonicalization authority
for containment comparison. `paths.is_within_real_root()` is **THE** shared
containment predicate, used by both `paths.resolve_under_root()` and
`atomic.publish_no_replace()`.

`atomic._real_path()` and `atomic._is_within()` are **delegating aliases** — they
call the shared authority and define no competing Windows prefix law of their
own. Verified in source: `atomic.py` imports `canonical_real_path` and
`is_within_real_root` from `.paths` and returns their results directly.

**Prefix logic lives in exactly one module.** A storage-package scan finds the
extended-prefix constants and the normalization routine only in `paths.py`
(`_WINDOWS_EXTENDED_PREFIX`, `_WINDOWS_EXTENDED_UNC_PREFIX`,
`strip_windows_extended_prefix`), and the matrix row
`single_canonicalization_authority` records
`prefix_logic_holders = ["paths.py"]`. A test row enforces this mechanically.

**Why raw `Path.resolve()` is not an authority (ratified).**
`os.path.realpath` on Windows returns the extended-length prefix on some calls
and omits it on others, so the SAME physical directory is spelled two ways.
The matrix row `naive_resolve_is_not_a_containment_authority` measures
`raw_resolve_contained = false` against `canonical_contained = true` for the
same physical path — a false refusal of a legitimate child, surfaced as
`UnsafeObjectKey`.

### 4.1 Windows path law (ratified)

- `C:\dir` and `\\?\C:\dir` are the **same authority**
  (`windows_extended_prefix_same_authority`: `canonical_equal` true,
  `raw_spellings_differ` true).
- `\\?\UNC\server\share` normalizes to `\\server\share`
  (`unc_and_extended_unc_spelling_law`: `extended_unc_normalised` true). This is
  a **pure string law** and required **no live network share**.
- A genuine **outside** extended path is still **refused**
  (`outside_root_still_refused`: `outside_refused` true, `traversal_refused`
  true).
- Off Windows the normalization is a strict no-op
  (`posix_spelling_unchanged` true).

### 4.2 Case law (ratified — deliberate NO case folding)

Matrix row `case_law_platform_specific`: `explicit_case_folding_used` = **false**,
`windows_path_case_insensitive` = true, `posix_path_case_sensitive` = true.

There is **no** `normcase`, no `.lower()`, no `casefold` in `paths.py` or
`atomic.py` (verified by source grep). This is deliberate: `PureWindowsPath`
comparison is already case-insensitive while `PurePosixPath` is not, so
lowercasing would merge two genuinely different POSIX directories and **weaken**
containment. Windows semantics are therefore honoured per platform, and **no
POSIX authority widening** was introduced.

---

## 5. Directory-race repair (ratified) and the 100x8 availability proof

### 5.1 Pre-repair RED, reproduced deterministically

Another writer creating the complete target chain between the entry target
probe and the walk-up probe collapsed `missing` to `[]`, so
`ensure_durable_directory_chain(target, [])` raised
`ValueError("components must be nonempty")` for a legitimate concurrent
creation. Matrix row `directory_create_race_reproduced` re-executes the
**verbatim pre-repair logic** with `sleeps_used = 0` and asserts
`counterfactual_raises = true` — the seal is earned by the repair, not by
timing luck.

### 5.2 Post-repair law

- Target appeared and is a **plain directory** -> **idempotent success**
  (`directory_create_race_idempotent`: `empty_components_calls` = 0,
  `seam_repair_returns_target` true).
- Target appeared as a **file / link / junction / other non-directory** ->
  **fail closed, left untouched** (`directory_race_onto_link_or_file_fails_closed`:
  `file_refused` true, `link_refused` true, `conflicting_object_removed` false).
- **No blind retry loops.** Correctness comes from idempotent creation and
  atomic no-clobber publication, never from retry, and never from catching
  `ValueError` / `UnsafeObjectKey` / `AtomicPublishSecurityError` at
  `LocalBlobStore.put` — no such catch exists in the writer.

### 5.3 NAME-MAX probe law (ratified)

Matrix row `name_max_probe_race_fails_closed`: `guessed_fallback_used` =
**false**, `identity_revalidated` = true, a vanished probed parent raises
`DurabilityUnsupported` and creates nothing. The component-length probe remains
**evidence-based**, the parent is revalidated as the same plain directory
immediately before and after the probe, and the I03 filesystem-truth law is
preserved. A vanished or replaced parent fails closed.

### 5.4 PRIMARY AVAILABILITY PROOF — 100 trials x 8 identical writers

`identical_writer_stress_after_repair`, matrix-verified:

- trials **100**, writers/trial **8**
- **100 green / 0 red**
- `committed_new_total` **100**, `reused_existing_total` **700** — every trial
  exactly one committed publication and seven benign reuse
- `unexpected_exceptions` **0**, `unsafe_object_key` **0**,
  `value_error_components_empty` **0**, `atomic_publish_security_error` **0**
- `final_object_count_violations` **0**, `hash_violations` **0**

A benign same-hash publication-race loser still resolves through
`AtomicPublishTargetExists` -> verify winner -> `REUSED_EXISTING` and is never
converted into a generic security refusal
(`same_hash_final_race_law`: `loser_exception` `AtomicPublishTargetExists`,
`security_refusals` 0, `winner_intact` true). Worker outcomes are collected by
an explicit per-worker `try/except` with four declared outcomes
(`worker_exception_capture`: `unhandled_thread_exceptions` 0).

### 5.5 Distinct-writer proof — the repair is NOT overfit to the same-hash race

`distinct_writer_stress_after_repair`: trials 5 x 8 **distinct** payloads.
`each_sha_exactly_once` = **true**, `crosstalk` = **0**, `hash_failures` = **0**,
`security_false_positives` = **0**. Every expected SHA is represented correctly
as a durable content identity.

---

## 6. Security regression re-check (ratified)

Availability was not purchased with security. Re-running the I15R1 malicious
race matrix unchanged: **13 rows / 13 OK**, `outside_root_mutations` = **0**,
`foreign_bytes_published` = **0**, and **both synthetic counterfactuals still
demonstrate their RED behaviour** when protection is disabled
(`check_use_seam_pre_repair_counterfactual_escape`,
`staged_source_substitution_pre_repair_counterfactual`).

Covered: destination namespace swap, staging-source substitution, static
intermediate escape, staging escape, final-name attack, root-link law A.

### 6.1 FINAL-NAME HISTORICAL DELTA — reported, NOT rewritten

One informational field re-measures differently on current runtime:

| field | committed I15R1 bytes | current runtime |
|---|---|---|
| `final_name_preexisting_link` -> `measured.refusal` | `NotADirectoryError` | `UnsafeObjectKey` |

The invariant is **unchanged**: `result = OK`,
`outside_file_untouched = true`, outside-root mutations 0, foreign bytes 0.

**Cause.** The planted object is a **broken reparse point**, so a raw
`Path.resolve()` raised an untyped `OSError` that escaped `put()`. The shared
`is_within_real_root()` catches that `OSError` and fails closed **earlier and
typed**. Current behavior is strictly stricter.

**The I15R1 historical matrix was NOT modified.** Per the append-only rule the
committed bytes stand as the I15R1 record and this delta is recorded here only.

---

## 7. Secret safety (ratified)

`BLOC_04_I15_SECRET_SAFETY_MATRIX.json` — **13/13 OK**:

- repository secret scan clean across source, tests/fixtures and evidence
  (`repo_secret_scan_source`, `repo_secret_scan_tests_fixtures`,
  `repo_secret_scan_evidence`)
- the allowlist is sentinel-only (`allowlist_is_sentinel_only`)
- URL, header and DSN credential families refused (request family, userinfo
  host, query/path)
- raw source RESPONSE evidence preserved exact and unredacted
  (`raw_body_evidence_not_redacted`)
- runtime request/auth sentinel **absent from durable metadata**
  (`durable_metadata_sentinel_scan`)
- **error messages do not leak the value** (`error_message_and_metadata_no_secret`)
- the scanner is neither blind nor self-matching (`scanner_self_match_excluded`,
  `scanner_would_detect_realistic_credential`)

**No credential is persisted through metadata.**

---

## 8. Path traversal / shell / hardlink (ratified)

`BLOC_04_I15_PATH_TRAVERSAL_MATRIX.json` — **36/36 OK**, including
`outside_root_mutation_total` and `containment_choke_point_bypass_audit`.
Traversal attempts are refused; literal in-root names are still contained (no
over-refusal). Shell interpolation yields **0 execution artifacts**
(`storage_zero_shell_structural`); malicious input is treated as **data**
(`malicious_instrument_is_data`).

---

## 9. Resource hardening (ratified)

`BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json` — **16/16 OK**:
1 GiB-equivalent **streaming** hash with a **bounded** chunk; large T0A
**streaming** write; **bounded** content dedupe; **configurable** chunk size and
export ceilings; injectable free-space check; DuckDB many-projection scale and
revision-chain scale **measured**; query-result bound and materialization
bounded; projection input and T0A streaming input bounded; the accepted **I09
disk watermark policy preserved** (`critical_watermark_p0_preservation`,
`disk_watermark_policy_matrix`).

### 9.1 10k manifest-row truth

`BLOC_04_I15_MANIFEST_SCAN_MATRIX.json`, `manifest_scan_scale_10k_real_rows` OK:

- `manifest_rows_created` **10,000** — ACTUAL VALID `PartitionManifest` rows,
  one per record, in the production on-disk layout
- `manifest_rows_scanned` **10,000** via the **production** reader
  (`RecoveryEngine._all_manifests -> read_fragment + _manifest_from_row`)
- `invalid_rows` **0**, `duplicate_logical_ids` **0**, `deterministic_order`
  true, `scan_peak_memory_bytes` bounded
- `corpus_construction` is recorded as a **benchmark fixture (canonical
  serializer + schema, production on-disk layout) — NOT append throughput**.

**Write throughput was measured separately** (`write_scale_production_append` in
the resource-bounds matrix) and is **not** misrepresented as 10k append
throughput.

---

## 10. Windows junction note (ratified as a known implementation fact)

A Windows junction may report `is_symlink() == False`. Security does **not**
depend on `is_symlink()`: containment resolves the **physical** target through
the shared real-path authority and refuses outside-root authority regardless of
how the filesystem classifies the object. Verified on this host, where the
symlink rows were exercised via `_winapi.CreateJunction`
(`link_mechanism` = `junction`, publish refused `AtomicPublishSecurityError`,
outside-root mutations 0).

This is **not a blocker**. I15 ratification is deliberately **not broadened**
into another junction checkpoint.

---

## 11. POSIX structural / runtime truth (honest, not fabricated)

- `POSIX_STRUCTURAL_PATH` = **VERIFIED** — per-component descriptor-relative
  opens carry `O_DIRECTORY` and `O_NOFOLLOW` on **every** component,
  `per_component_opens` = 3, and `dst_dir_fd` is passed to `os.link`.
- `POSIX_RUNTIME_TOCTOU` = **NOT_MEASURED_ON_THIS_HOST**. This is a Windows
  host: `os.supports_dir_fd` is empty and `os.O_DIRECTORY` is absent, so the
  descriptor-relative branch never executes here and **no runtime result is
  claimed**.

No POSIX runtime evidence is fabricated. This alone does **not** block I15
ratification because the host-specific Windows path was behaviourally exercised
and the POSIX branch is explicit and structurally proven.

---

## 12. Transient 29-failure run — KNOWN TEST-ENVIRONMENT DEBT, not a production defect

Operator review does **NOT** accept the transient 29-failure storage run as a
production defect. It was investigated, isolated and re-measured green:

- the affected projection modules pass **89/89 in isolation**;
- full storage with the production changes but **excluding** only the new I15R2
  test files: **1791 passed / 11 skipped / 0 failed** — exactly the I15R1
  baseline, proving the production repair introduces no failure;
- full storage **including** them: **1832 passed / 13 skipped / 0 failed**;
- full project: **3211 passed / 14 skipped / 0 failed**.

**Recorded as KNOWN TEST-ENVIRONMENT DEBT:** several projection tests use
hard-coded Windows `C:\tmp_*` roots and interact poorly under long / high-load
test runs. **Not fixed during ratification. No production redesign is
authorized from it.**

---

## 13. Local regression truth at the accepted head

Executed at `2a856e656f9da4b2749fa1b999e58ae26f4234be` in
`.worktrees/sensor-b4-i11`:

| suite | result |
|---|---|
| I15R2 focused (canonicalization + concurrent publication) | included below |
| I15R1 TOCTOU + fresh corruption | included below |
| I15 hardening / resource bounds / 10k manifest scan | included below |
| I03 atomic + blob-store adversarial concurrency | included below |
| path / canonicalization tests | included below |
| I11R2 governance-binding audit | included below |
| **combined ratification battery** | **253 passed / 2 skipped / 0 failed** (404.91s) |
| **full storage** (`tests/crypto_sensor_fabric/storage`) | **1832 passed / 13 skipped / 0 failed** (1216.06s) |
| **full project** (`quant-lab/tests`) | **3211 passed / 14 skipped / 0 failed** (1293.82s) |

**ZERO deterministic failures.** The 2 skips are the known platform skips (true
symlinks require privilege on Windows, which uses junctions).

**Static checks.** Ruff **clean on every file the I15 chain changed** (the only
2 repo-wide ruff findings are pre-existing `F401`/`F811` in
`tests/crypto_sensor_fabric/storage/test_i08_evidence.py`, last touched at
`00898d666` / SENSOR-B4-I08C on 2026-09-22 and untouched by this chain).
`compileall` clean. mypy: **10 pre-existing errors, 0 in `paths.py` or
`atomic.py`** (all in `providers/` and `probes/`). Secret scan clean.

**No new Python test was added by ratification**, so per the governing rule the
I11R2 governance-binding audit was **NOT republished** and remains byte-stable
at `python_files_scanned` = 997.

---

## 14. External CI truth

At head `2a856e656f9da4b2749fa1b999e58ae26f4234be`: **0 statuses, 0 check-runs,
0 workflow runs** on `agent/crypto-sensor-fabric-build`.

`external_ci = NONE_OBSERVED`. Local pytest is **not** CI and is not described
as such. All verification in §13 is local.

---

## 15. Historical evidence law (honoured)

I03–I14, I15, I15R1 and I15R2 published evidence was **not modified**.

Re-running the suites dirties a bounded set of **informational** fields. After
every ratification run the dirty files were inspected, then the historical
bytes were **restored before diffing and before committing**. The remeasurement
was **never staged**.

Files re-measured and reverted during ratification (all informational only):

| file | nature of the rewrite |
|---|---|
| `BLOC_04_I03R1_ATOMIC_ORDER.json` | JSON-**equal**; serialization order only |
| `BLOC_04_I15R1_TOCTOU_MATRIX.json` | the §6.1 `final_name_preexisting_link` refusal label |
| `BLOC_04_I15_MANIFEST_SCAN_MATRIX.json` | informational timing / peak-memory |
| `BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json` | informational timing / peak-memory |
| `BLOC_04_I15_SECRET_SAFETY_MATRIX.json` | `files_scanned` counts only |
| `BLOC_04_I03R1_NAMESPACE_DURABILITY.json`, `BLOC_04_I04R1_POINTER_SCHEMA.json`, `BLOC_04_I04R1_PROVENANCE_MATRIX.json`, `BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json`, `BLOC_04_I04_CATALOG_SCHEMAS.json`, `BLOC_04_I04_MANIFEST_CONCURRENCY.json` | informational |

Verified after restoration: **every historical evidence artifact is
byte-identical to its committed state.** Ratification created a NEW acceptance
artifact only; the **production diff is ZERO**.

---

## 16. I16 authorization boundary

`SENSOR-B4-I16` — **FINAL ACCEPTANCE + EVIDENCE PACKET** — is now authorized.

**Frozen contract.** I16 must **RUN ALL G4 GATES** and **PRODUCE FINAL BLOC 4
EVIDENCE**. It was **not implemented** during this ratification.

**I16 must NOT prejudge its verdict.** The verdict must be **earned** from the
gates. `PASS` is **not** preselected by this ratification. Allowed final Bloc 4
verdict vocabulary:

- `PASS_BLOC_04_IMPLEMENTED`
- `PASS_BLOC_04_IMPLEMENTED_WITH_DATA_VOLUME_LIMITS`
- `BLOCKED_BLOC_04_INTEGRITY`
- `BLOCKED_BLOC_04_STORAGE_CAPACITY`
- `FAIL_BLOC_04_ATOMICITY`
- `FAIL_BLOC_04_LINEAGE`
- `FAIL_BLOC_04_RESTORE`

**G4-13 remains UNPASSED** = `NOT_YET_IMPLEMENTED` /
`PENDING_I16_OR_LATER_AS DEFINED`. Its definition — PASS when
`RawNormalizationBatch` exposes sufficient source, timestamp, unit and lineage
evidence for PIT normalization without filesystem/path assumptions — is
**not** earned by ratifying I15. **I16 must evaluate G4-13 along with all other
G4 gates.**

**I17 firewall.** I16 authorization does **NOT** authorize I17 Bloc 5 handoff,
normalization implementation, research restart, provider redesign, storage
architecture redesign, new query semantics, or new revision semantics. I17
remains blocked until I16 final acceptance.

**Research remains FROZEN.**

---

## 17. Ratification verdict

The complete **I15 -> I15R1 -> I15R2** chain is **OPERATOR ACCEPTED**.

The chain closes secret safety, traversal containment, static symlink escape,
TOCTOU destination custody, TOCTOU staging-source custody, fresh corruption
handling, hardlink integrity detection, resource bounds, the 10k actual
manifest-row scan, Windows canonical path authority, benign concurrent
publication stability, directory-creation race closure, and security-preserving
concurrency — with historical evidence custody preserved and a **zero**
production diff.

**No production defect was found requiring a source change**, so no repair
checkpoint is issued. `SENSOR-B4-I16` is authorized for implementation only.