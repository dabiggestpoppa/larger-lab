# BLOC_04_I15R1_EVIDENCE_CORRECTION

**Mandate:** SENSOR-B4-I15R1 — TOCTOU filesystem custody + fresh corruption re-measurement microseal
**Branch:** agent/crypto-sensor-fabric-build
**Base (start) HEAD:** `bc6d5e059f3d039235dbcc4769658819146ff7db`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Scope:** I15R1 ONLY. I16+ UNAUTHORIZED. G4-13 NOT EARNED. Research FROZEN.

This document is **append-only correction evidence**. It does NOT rewrite the
I15 matrices, the I15 ledger section, or any historical I03–I14 artifact.
**I15 remains valid historical hardening evidence.**

---

## 1. Operator review findings closed

The I15 seal was left as `PENDING_OPERATOR_REVIEW` with two open blockers:

**A. TOCTOU symlink swap was DOCUMENTED, not tested/sealed.** `resolve_under_root()`
returned the ORIGINAL unresolved path after validating real containment, and
`TOCTOU_SYMLINK_SWAP = KNOWN_LIMITATION` carried no behavioural race proof.

**B. The I15 corruption matrix did not freshly re-measure every durable
subsystem** — T0B, revision, job/checkpoint, export, DuckDB and recovery were
partly satisfied by `EXISTING_MEASURED_SUITE` citations rather than one fresh
adversarial restart measurement per surface.

I15R1 closes exactly these two. Nothing already clean in I15 was reopened.

## 2. TOCTOU — RED reproduced, then closed

**RED (reproduced at the I15 head, BEFORE the R1 repair).** A deterministic test
drove the existing `atomic.FaultPoint.BEFORE_PUBLISH` seam — the exact window
between containment validation (`resolve_under_root`) and final-name creation
(`os.link`). In the hook the `blobs` component was swapped to a link to an
outside directory. Result: `LocalBlobStore.put_bytes` **SUCCEEDED** and the
immutable blob landed OUTSIDE the configured root
(`outside/sha256/40/91/<sha>.blob`). A true race permitted an outside-root
mutation → BLOCKING.

**Repair (smallest compatible production change).** `publish_no_replace()` now
accepts a `containment_root` and anchors the commit to the REAL topology:

1. **verify BEFORE** any namespace is created — refuse typed if the final
   parent does not resolve inside the root;
2. **descriptor-relative link (POSIX)** — the parent chain is re-opened with
   `O_NOFOLLOW` component by component from the resolved root and the link is
   created with `dst_dir_fd=<open parent>`; a component swapped to a link after
   the open can no longer redirect the commit;
3. **verify AFTER + revert (cross-platform)** — if the published artifact does
   not resolve inside the root (the guarantee on platforms without
   descriptor-relative link, e.g. Windows), the outside artifact is removed and
   the commit is refused typed as `AtomicPublishSecurityError`.

Every production call site now passes its containment root: `blob_store`
(T0A), `catalog.publish_immutable_fragment` (catalogs/manifests/acquisitions),
`json_catalog`, `projections` (T0B) and `recovery`. Structural reuse is proven
by the matrix (`call_sites == anchored == 5`).

**Post-repair result:** the same check/use swap at BOTH the `blobs` and
`staging` namespaces now refuses typed with **outside-root mutation count = 0**;
the static intermediate link stays refused; a link pre-placed at the exact
final name cannot replace or redirect evidence; and accepted **root-symlink law
A** (a configured data root may itself be a link) is preserved.

**Platform guarantee is stated exactly** (no equivalent claim where it is not
equivalent): POSIX = descriptor-relative link from an open parent; Windows =
verify-before/after with revert. Measured platform this run: `win32`
(`posix_descriptor_relative_available = false`).

## 3. Fresh corruption re-measurement

A NEW, current-run adversarial case was executed for EVERY durable subsystem.
Each row commits valid state, tampers a durable invariant AFTER commit,
destroys the old repository/service instances, constructs a FRESH instance, and
attempts the read/rebuild. Every row records `fresh_instance = true` and
`repair_on_read = false`. No row is satisfied only by citing an existing suite.

| Subsystem | Tamper | Fresh operation | Outcome |
|---|---|---|---|
| T0A | blob payload byte flipped | fresh `LocalBlobStore.verify_blob` | QUARANTINED_ACCEPTED |
| acquisition | fragment bytes overwritten | fresh `get_acquisition` | FAIL_CLOSED_TYPED |
| manifest | fragment bytes overwritten (pointer binding) | fresh `get_current_manifest` | FAIL_CLOSED_TYPED |
| T0B | projection payload overwritten | fresh `ProjectionArtifactRepository.verify_physical` | FAIL_CLOSED_TYPED |
| revision | revision segment overwritten | fresh `SourceRevisionRegistry` + `resolve(ALL)` | FAIL_CLOSED_TYPED |
| job/checkpoint | job state overwritten | fresh `DurableJobStateRepository.get_job` | FAIL_CLOSED_TYPED |
| export | pack object overwritten | fresh `EvidencePackVerifier` + `EvidencePackRestorer` | FAIL_CLOSED_TYPED (no final-root promotion) |
| DuckDB (A) | duckdb file overwritten | fresh `rebuild_duckdb_catalog` | REBUILD_DISPOSABLE_STATE |
| DuckDB (B) | durable evidence under the catalog overwritten | fresh `rebuild_duckdb_catalog` | FAIL_CLOSED_TYPED (bad truth NOT canonized) |
| recovery/quarantine | hostile unknown + corrupt partial in staging | fresh `RecoveryEngine.scan` | QUARANTINED_ACCEPTED (valid T0A preserved, nothing promoted) |

`UNSAFE_SILENT_ACCEPTANCE` did not occur anywhere.

## 4. What I15R1 does NOT do

- It does not re-run the 10,000-manifest-row scan (the reader was not touched;
  the I15 result `created = scanned = 10000`, `invalid_rows = 0`,
  `duplicate_logical_ids = 0` stands).
- It does not modify any I15 matrix or any historical I03–I14 artifact.
- It does not start I16.

## 5. Published I15R1 evidence

- `BLOC_04_I15R1_TOCTOU_MATRIX.json`
- `BLOC_04_I15R1_FRESH_CORRUPTION_MATRIX.json`
- `BLOC_04_I15R1_EVIDENCE_CORRECTION.md` (this file)

## 6. Governance

```
SENSOR-B4-I15R1
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED              = OPERATOR_HOLD
PASS_SENSOR_B4_I15R1_TOCTOU_FRESH_CORRUPTION_SEALED       = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                                = FALSE
recommended_next                                          = OPERATOR REVIEW OF I15 -> I15R1 CHAIN
I16+                                                      = UNAUTHORIZED
G4-13                                                     = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                                  = FROZEN
```

No self-ratification. I16 not started. STOP after I15R1.

---

# APPEND-ONLY CORRECTION — independent verification pass (same checkpoint, I15R1)

Appended after the sections above; nothing above was rewritten. This pass
independently re-derived the TOCTOU result, found that the first R1 test
measured a weaker seam than the claim required, and found and fixed a
regression that the first R1 repair introduced. The I15 matrices and all
historical I03–I14 evidence remain untouched.

## C1. The first R1 test did not reach the residual check/use window

**Gap.** The first R1 test drove `FaultPoint.BEFORE_PUBLISH`, which
`LocalBlobStore.put` raises **before it calls `publish_no_replace`**. A swap
there is therefore an *already-swapped-at-entry* case: it proves the entry
check works, not that the window **inside** the writer — between the
writer's own containment check (and the parent-descriptor open) and
`os.link` — is closed. The original RED was real, but the post-repair SEAL
was measured one layer above the vulnerable code.

**Correct seam (no sleep, no timing).** `publish_no_replace` records
`OP_FINAL_LINK` through its existing `OpRecorder` seam *after* both
containment checks and *after* the parent descriptor is opened, immediately
before `os.link`. The test now injects the swap there.

| Seam | I15 head (`bc6d5e05`) | I15R1 head |
|---|---|---|
| caller seam (`BEFORE_PUBLISH`) | PUT SUCCEEDED · **1** outside-root mutation | refused `AtomicPublishSecurityError` · 0 |
| **residual seam (`OP_FINAL_LINK`)** | PUT SUCCEEDED · **1** outside-root mutation | refused `AtomicPublishSecurityError` · 0 |

Both I15-head cells were reproduced against a clean `git archive` export of
`bc6d5e059f3d039235dbcc4769658819146ff7db` (pre-seeded mirrored namespace so
the redirected link cannot fail for an unrelated reason). The residual-seam
RED at the I15 head is the decisive one: it is inside the writer.

**Pre-repair counterfactual (new matrix row, `SYNTHETIC_COUNTERFACTUAL`).**
With the R1 primitive disabled in-process (`_is_within` → always True,
`_open_parent_no_follow` → None, i.e. exactly I15-head semantics) the same
seam commits **outside** the root: `outside_root_mutations = 1`,
`typed_refusal = null`. The seal is therefore earned by the production
primitive, not by the test harness.

**TOCTOU matrix: 11 rows (was 9), 11 OK, 0 FAIL, 1 synthetic counterfactual.**
Outside-root mutation count across every escape row = **0**.

## C2. Regression found by this pass and fixed: Windows `\\?\` false refusal

The first R1 repair compared `os.path.realpath(candidate)` against
`os.path.realpath(root)` as plain strings. On Windows those two calls are
**not stable**: CPython's `ntpath.realpath` strips the extended-length
`\\?\` prefix only when its post-strip re-resolution check succeeds, so the
*same* directory is returned prefixed on some calls and unprefixed on
others. Observed during concurrent publication:

```
realpath(candidate) = '\\?\C:\...\blobs\sha256\fc\9a'
root_real           =       'C:\...\diag_z5a0ieyq'
=> containment verdict: FALSE  (false "resolves outside the root")
```

Valid concurrent writes were refused `AtomicPublishSecurityError`. Measured
impact on `test_concurrent_identical_writers_one_final`, 8 threads × same
payload, 15 trials each, run back to back:

| Tree | Passes / 15 |
|---|---|
| I15 head `bc6d5e05` | 5 |
| I15R1 first repair (unfixed) | 3 / 10 trials |
| I15R1 + `\\?\` normalisation (this pass) | 8 |

**Fix.** `_real_path()` normalises the `\\?\` and `\\?\UNC\` spellings before
any containment comparison; both sides of the comparison now go through it.
No-op on POSIX, where `realpath` is stable. The containment decision itself
is unchanged — a genuine link escape is still refused (verified: both TOCTOU
seams still refuse with 0 outside-root mutations after the fix).

## C3. Residual concurrency flake — PRE-EXISTING, reported, NOT fixed here

With the false refusal removed, the known concurrency flake remains at the
I15 head's own rate. It has **two** distinct Windows path-API causes, both
present at `bc6d5e05` before any I15R1 code existed, and both in code
outside the I15R1 authorization:

1. `paths.resolve_under_root` (I15 code) raises
   `UnsafeObjectKey: object key containment failed` when its own
   `realpath` comparison hits the same `\\?\` spelling instability;
2. `atomic.ensure_durable_directory` (I03 code) raises
   `ValueError: components must be nonempty` when `Path.exists()` returns a
   transient `False` for a directory another thread is creating, leaving
   the missing-component list empty.

Both fail CLOSED (no escape, no silent acceptance). Neither is an I15R1
regression. I15R1 does **not** reopen I15 or I03 code to fix them: that is a
new checkpoint and needs operator authorization. Measured baseline for the
operator: I15 head `bc6d5e05` fails 10 / 15 trials; this head fails 7 / 15.

## C4. Second RED found by this pass: the STAGING SOURCE was still unguarded

**Gap.** The R1 repair anchored only the DESTINATION of the atomic link. The
`os.link` SOURCE (`staging_path`) sits in the same check/use window and was
never re-validated, so a swap of the staging namespace could substitute a
different durable file for the one that had just been staged and verified.

**RED, measured.** At the `OP_FINAL_LINK` seam (inside `publish_no_replace`,
after its checks), the staging namespace is replaced by a link whose target
already holds a file named like the in-flight staged artifact. Result at the
pre-repair head:

```
outcome            = PUT_SUCCEEDED
disposition        = COMMITTED_NEW
receipt sha256     = 9bb24023...   (genuine payload)
published blob sha = 84e3b4d2...   (ATTACKER bytes, is_genuine = false)
```

Content-addressed storage's central invariant was broken: foreign bytes were
published under an already-verified content address, with a receipt asserting
a digest the artifact does not have. No outside-root mutation is involved —
this is a **silent integrity violation inside the root**, which is strictly
worse than the escape it accompanied.

**Repair (smallest compatible).** In `publish_no_replace`, when a containment
root is supplied:

1. the `(st_dev, st_ino)` identity of the staged artifact is captured
   immediately after the existing “is a regular file” check — before the
   window opens (`st_ino` is the Windows file index too, and a hard link
   shares it with its source);
2. the staged source must still resolve INSIDE the containment root just
   before the commit;
3. immediately after the commit the published NAME must report the SAME
   `(st_dev, st_ino)` as the staged artifact, otherwise the artifact is
   unlinked, the commit is reverted and the refusal is typed
   (`AtomicPublishSecurityError`).

This is the `lstat/fstat identity revalidation immediately around publication`
pattern of §6, and it is platform-neutral (no descriptor-relative source
required).

**Post-repair:** the same substitution is refused typed with 0 artifacts
published. The counterfactual row (identity check made vacuous) publishes
attacker bytes at a content address and is recorded as the measured RED.

**TOCTOU matrix after this correction: 13 rows, 13 OK, 0 FAIL, 2 synthetic
counterfactuals.** Outside-root mutation count = 0; foreign-bytes-published
count = 0.

## C5. Re-verification summary after the correction

- Focused I15R1 + I15: **42 passed** (`test_i15_hardening` 17,
  `test_i15_resource_bounds` 12, `test_i15r1_toctou` 2,
  `test_i15r1_fresh_corruption` 11), 0 failed.
- Full storage suite (final head): **1791 passed / 11 skipped / 0 failed**.
- Full project suite `quant-lab/tests` (final head): **3170 passed / 12 skipped
  / 0 failed**.
  An earlier full-project run reported 1 failure,
  `test_i07r1h_evidence::test_evidence_directory_untouched_after_run`. Its
  diff named exactly the three I15 matrices, and the cause was operator
  error, not the code: `git checkout` of those matrices was executed WHILE the
  suite was running, landing between that test's before/after directory hash
  snapshots. Re-run without touching the worktree: 0 failed. Reported for
  completeness rather than hidden.
- Earlier full-storage runs of this checkpoint, before the C2/C4 repairs,
  measured 1787 passed / 11 skipped / 4 failed; all four were re-measured in
  isolation — 3 were environmental (`git show` subprocess raised
  `STATUS_DLL_INIT_FAILED` under the long run; all 3 pass alone) and 1 was the
  pre-existing concurrency flake of C3.
- Ruff on changed scope: clean. compileall: clean. mypy: 10 errors, all
  pre-existing in `providers/`, 0 in `atomic.py`.
- I15 matrices: **unchanged** — re-running the I15 suites rewrites only
  informational timing/memory fields, which were reverted, never staged.
- I11R2 governance-binding audit: no new test file names (an existing I15R1
  test file was extended), regeneration byte-stable, 4 audit tests pass.
