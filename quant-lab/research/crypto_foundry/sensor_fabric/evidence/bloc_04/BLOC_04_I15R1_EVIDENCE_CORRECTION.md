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
