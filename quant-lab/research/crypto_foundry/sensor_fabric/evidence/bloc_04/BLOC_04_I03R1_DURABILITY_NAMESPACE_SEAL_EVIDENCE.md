# BLOC 4 — I03R1 DURABILITY NAMESPACE SEAL EVIDENCE

Checkpoint: **SENSOR-B4-I03R1 — ORPHAN-RETRY + DIRECTORY-NAMESPACE DURABILITY SEAL**
Target verdict (proposed): `PASS_SENSOR_B4_I03R1_DURABILITY_NAMESPACE_SEALED`
Then proposed operator acceptance: `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA (mandated + verified): `c6e0448d0cf231b670d2d182c06753716f5a35bd`
  (SENSOR-B4-I03D — atomic filesystem evidence and ledger)
Ending SHA: `9363143e` + I03R1D commit (see ledger)
Operator hold verdict:
  `HOLD_PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND_PENDING_I03R1_DURABILITY_NAMESPACE_SEAL`

## 0. SCOPE DISCIPLINE

I03's architecture is ACCEPTED and was NOT redesigned. Untouched frozen
surfaces: exact-source SHA-256; H1/H2/H3 separation; NONE/ZSTD wrappers;
`LocalBlobStore` public shape; content-addressed T0A keys; staging layout;
file flush/fsync; staged verification; no-clobber hard-link publication;
cross-device denial; immutable final objects; crash A–F vocabulary.

Three NARROW durability seams were repaired. No I04, no recovery scanner,
no manifests, no provider work.

## 1. COMMITS (I03R1 sequence)

| Commit | Checkpoint | Content |
| --- | --- | --- |
| `d19e9d13` | SENSOR-B4-I03R1A | Reuse/orphan durability sealed before successful dedupe |
| `9225acb6` | SENSOR-B4-I03R1B | Durable directory-chain creation + fail-closed component probing |
| `9363143e` | SENSOR-B4-I03R1C | Namespace/crash/race adversarial evidence + supplemental matrix |
| (this commit) | SENSOR-B4-I03R1D | Evidence freeze + ledger |

## 2. HISTORICAL I03 EVIDENCE — IMMUTABLE

Never rewritten: `BLOC_04_I03_ATOMIC_FILESYSTEM_EVIDENCE.md`,
`BLOC_04_I03_CRASH_MATRIX.json`, `BLOC_04_I03_ATOMIC_ORDER.json`.

Mechanical proof: the crash-matrix generator test now REGENERATES its six
rows in memory and asserts byte-equality against the frozen historical
artifact — any future durability-behavior drift fails loudly instead of
silently falsifying history. The atomic-order generator (whose operation
stream legitimately gained I03R1 milestones) now seals the SUPPLEMENTAL
`BLOC_04_I03R1_ATOMIC_ORDER.json` instead of touching the historical file.

## 3. DEFECT A — ORPHAN RETRY (SEALED)

**Old behavior:** a retry after crash E
(`AFTER_PUBLISH_BEFORE_DIR_FSYNC`) verified the existing final object and
returned `REUSED_EXISTING` / SUCCESS **without re-establishing
parent-directory durability** — silently promoting an orphan whose
namespace commit was never proven.

**New rule (§4/§5):** every path returning `PutDisposition.REUSED_EXISTING`
must prove CURRENT durability before success:

```
STAGE_WRITE < FILE_FLUSH < FILE_FSYNC < STAGE_VERIFY
  < EXISTING_FINAL_VERIFY < PARENT_DIR_FSYNC
  < STAGING_CLEANUP < SUCCESS_RETURN
```

Frozen by `is_canonical_reuse_order()` and applied uniformly to: ordinary
existing-blob reuse, same-hash publish-race loser, retry after crash E,
retry after crash F. Not special-cased per test. A reuse result whose op
stream lacks the parent fsync FAILS (`test_reuse_without_parent_fsync_rejected`).

**Crash-E retry result (§6):** crash attempt raises `FaultError` with final
existing, no success returned, parent fsync unobserved; the retry verifies
the existing final (`EXISTING_FINAL_VERIFY`), fsyncs the final parent
BEFORE success, returns `REUSED_EXISTING`, never rewrites/repaces final
bytes, and preserves content identity. The crashed attempt's staging file
remains preserved crash evidence (I03 §42 — no auto-recovery in I03R1);
the retry cleans only its own staging artifact.

**Crash-F regression (§7):** `test_retry_after_durable_publication_dedupes`
and `retry_after_crash_F` matrix row remain green; the retry performs an
EXTRA directory fsync (extra fsync is acceptable, never weaker safety).

**Race-loser durability (§8):** on `AtomicPublishTargetExists` the loser
verifies the winner, then fsyncs the winner's final parent before
returning `REUSED_EXISTING` — the success contract is now identical
whether reuse came from a pre-existing object or a concurrent winner.

## 4. DEFECT B — DIRECTORY-CHAIN DURABILITY (SEALED)

**Old behavior:** `publish_no_replace` did blind
`os.makedirs(fp.parent, exist_ok=True)`; only the final leaf parent was
fsynced after publication. A first write could create
`blobs/`, `blobs/sha256/`, `blobs/sha256/ab/`, `blobs/sha256/ab/cd/` with
no explicit durability story for the new namespace components.

**New mechanism (§9/§10):** reusable primitives in `atomic.py`:

- `ensure_durable_directory_chain(base, components)` — from the existing
  trusted ancestor, for every missing component: validate component against
  the ACTUAL limit probed from its EXISTING parent → `mkdir` child → fsync
  child (`DIR_FSYNC`) → fsync parent (`PARENT_NAMESPACE_FSYNC`) → descend;
- `ensure_durable_directory(target)` — walks up to the deepest existing
  ancestor and applies the chain helper below it (used by the store for the
  staging namespace too).

`publish_no_replace` now creates the final parent chain through this helper
BEFORE the device check and the link; blind `os.makedirs` is gone from the
commit path (§13). Concurrent `FileExistsError` races are tolerated
(confirm-directory-and-continue); an existing file/symlink/incompatible
component FAILS CLOSED — never deleted or replaced (§11).

**Operation-order invariant (§23), machine-proven:**
`DURABLE_DIRECTORY_CHAIN_READY < ATOMIC_PUBLISH < FINAL_PARENT_FSYNC <
SUCCESS_RETURN`, with distinguishable tags `DIR_CREATE`, `DIR_FSYNC`,
`PARENT_NAMESPACE_FSYNC`, `FINAL_LINK`, `FINAL_PARENT_FSYNC` (§22). Proven
in `BLOC_04_I03R1_ATOMIC_ORDER.json`: for a fresh root the sequence is
4×(dir_create, dir_fsync, parent_namespace_fsync) → device_check →
atomic_publish → final_link → parent_dir_fsync → final_parent_fsync →
staging_cleanup → success_return.

**Existing-namespace regression (§24):** when all directories already
exist, zero dir-create milestones are emitted, but the final parent fsync
still occurs after publication (and on the reuse path before success).

**Root policy (§12):** the storage root keeps its existing honest contract:
the constructor REQUIRES the configured root to pre-exist as a directory
(`InvalidStorageRoot` otherwise; only `blobs/` + `staging/` below it are
created, now durably). The backend does not silently recursive-create the
root while claiming full namespace durability.

**Final publication remains no-clobber (§14/§15):** `os.link` unchanged;
`os.replace` forbidden; final parent fsync still occurs after the link —
directory-path durability and final-filename-entry durability are both
present and separately tagged.

## 5. DEFECT C — TRUE FILESYSTEM COMPONENT LIMIT (SEALED)

**Old behavior:** `default_name_max()` silently fell back to 255 when the
pathconf query failed (e.g. nonexistent target directory) — a guess, not
proof. The generated `<nonce>.partial` component was never validated.

**New policy (§16/§17):** `default_name_max(path)`:

- FAILS CLOSED on a nonexistent directory (`DurabilityUnsupported`) —
  probing a future path cannot prove filesystem truth;
- POSIX: queries `PC_NAME_MAX` on an existing directory; a failing query
  raises `DurabilityUnsupported` — never a silent 255
  (`test_posix_probe_failure_fails_closed`);
- Windows / no-pathconf platforms: documented NTFS 255 UTF-16-unit limit is
  EXPLICIT PLATFORM POLICY, honestly recorded as policy, not dynamic proof
  (backend components are ASCII after canonical escaping, units == bytes).

The store's `_component_limit_for()` probes from the deepest EXISTING
ancestor of the target path (same filesystem, same limit) — the §18 rule
that each component is validated using its existing parent's context, never
a not-yet-created directory (`test_store_component_check_uses_existing_ancestor`).

**Staging components (§19):** before any staging write, the store validates
`"staging"`, the escaped `job_id` (existing I03 behavior), and NOW the
generated `<nonce>.partial` component against the actual limit — typed
`ComponentTooLong` before `open()`, never a late raw `ENAMETOOLONG`
(`test_nonce_component_validated_before_open`,
`test_over_limit_staging_filename_fails_typed_before_open`).

**Final blob components (§20):** `blobs`, `sha256`, `h0h1`, `h2h3`,
`<full_sha>.blob[.zst]` are validated against the same actual-limit policy
before any final artifact write. **No truncation/normalization/native-id
hashing anywhere** (§21) — an over-limit canonical identity fails typed.

## 6. NO AUTO-RECOVERY (§26/§27)

I03R1 makes a normal retry safe; it does NOT implement I08: no stale
partial enumeration, no orphan catalog reconciliation, no quarantine
movement, no bulk recovery, no recovery evidence engine. A retry on a known
content key adopts the verified existing object; crash-injected leftovers
are intentionally preserved. `REUSED_EXISTING` means only: the physical
byte object exists, verifies, and current filesystem durability is
re-established. It creates NO AcquisitionRecord, PartitionManifest,
SourceRevision, StorageJobState, or resume token.

## 7. MACHINE EVIDENCE (§29)

- `BLOC_04_I03R1_NAMESPACE_DURABILITY.json` — supplemental matrix, 5 rows
  (`fresh_namespace_commit`, `reuse_existing`, `retry_after_crash_E`,
  `retry_after_crash_F`, `publish_race_loser`), fields: case,
  directory_chain_ready, parent_fsync_before_success, success_returned,
  disposition, final_verified, no_overwrite, test_name. Generated
  deterministically by tests; no volatile wall clock.
- `BLOC_04_I03R1_ATOMIC_ORDER.json` — proven operation sequence for a fresh
  namespace (see §4 above).

## 8. REQUIRED TESTS (§32) — ALL PRESENT

1–3 crash-E/crash-F retry durability (`TestReuseDurability`,
matrix rows); 4 ordinary-reuse parent fsync; 5 race-loser parent fsync;
6–8 fresh-fanout durable chain + order (`TestDurableDirectoryChain`,
`TestNamespaceDurabilityOrder`); 9–10 actual NAME_MAX probe + fail-closed
probe failure (`TestNameMaxProbe`); 11–12 staging nonce validated /
over-limit typed pre-open (`TestStagingNonceComponent`); 13 creation race
tolerated; 14 non-directory component fails closed; 15–18 original I03
no-clobber, crash A–F, NONE/ZSTD round-trip, concurrent-writer suites all
remain green (398 → 426 storage nodes, 0 failures).

## 9. VERIFICATION RESULTS

| Gate | Result |
| --- | --- |
| Storage suite | 426 nodes: 424 passed, 2 skipped (platform skip: POSIX-only probe test), 0 failed |
| Full `tests/crypto_sensor_fabric` | 1806 collected: **1803 passed, 0 failed, 3 skipped** (floor ≥1768) |
| Net I03R1 delta | +36 nodes vs I03 baseline (1770→1806 collected) |
| ruff (changed scope) | All checks passed |
| mypy (changed scope) | 0 errors in `atomic.py` + `blob_store.py` (remaining repo errors are the documented pre-existing yaml/planner baseline in untouched modules) |
| Network calls | 0 |
| Provider code changes | none |
| Cross-device denial | unchanged (`CrossFilesystemAtomicityError`, no copy fallback) |
| Hard-link no-clobber | unchanged |
| H1/H2/H3 | unchanged |
| NONE/ZSTD exact round-trip | unchanged, green |
| Crash matrix A–F | historical artifact byte-identical, behavior green |

## 10. BOUNDARY (§30/§35)

`ATOMIC_FILESYSTEM_BACKEND_READY = TRUE`, `T0A_BLOB_BACKEND_IMPLEMENTED =
TRUE`, `T0A_EVIDENCE_PIPELINE_COMPLETE = FALSE` (I04 metadata/manifests do
not exist), `MANIFEST_REPOSITORY_IMPLEMENTED = FALSE`,
`T0B_STORAGE_IMPLEMENTED = FALSE`, `next_checkpoint_authorized = FALSE`.
SENSOR-B4-I04 (ACQUISITION + MANIFEST REPOSITORY) NOT started. Bloc 5 not
started. MECH21/LF14 not resumed.

Proposed verdict: `PASS_SENSOR_B4_I03R1_DURABILITY_NAMESPACE_SEALED`, then
operator acceptance of `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`.
