# SENSOR-B4-I08 — Recovery / Quarantine

**Checkpoint:** SENSOR-B4-I08 — recovery/quarantine scanner
**Branch:** agent/crypto-sensor-fabric-build
**Starting SHA:** fd96160485ad44763022f6a1f07f80e5ffb5d794 (accepted I07 chain head)
**I07 ratification SHA:** abcc1b40 (SENSOR-B4-I07R1I-RATIFY, governance-only)
**Ending SHA:** see commit chain below
**Operator review state at freeze:** the complete I07 chain (I07, I07R1,
I07R1F, I07R1G, I07R1H, I07R1I) is `OPERATOR_ACCEPTED` per the operator's
ratification instruction; `DURABLE_RESUME_IMPLEMENTED = TRUE`;
`RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE` after this
checkpoint; I08 is proposed `PENDING_OPERATOR_REVIEW` — nothing here is
self-ratified.  I09+ NOT started.

---

## 1. Frozen doctrine references

- `bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md` §17–§21:
  recovery classes, no-silent-repair, quarantine preference.
- `bloc_04/06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md`:
  crash-matrix acceptance scenarios.
- `bloc_04/07_BLOC_04_FREEZE_MANIFEST.md`: frozen vocabularies and
  quarantine layout.
- Operator instruction §3–§44 (this checkpoint's contract).

Core doctrine applied: detection is not permission to mutate; no silent
repair; never manufacture missing provenance; never rewrite immutable
historical truth; a corrupted source object is quarantined, not
overwritten; an orphan is reconciled only when context proves what it is;
a stale-looking lock with unprovable ownership is never auto-deleted; a
recovery plan is revalidated immediately before apply; advance cursors
only behind durable truth.

## 2. Commit chain

| Commit | Content |
|---|---|
| `abcc1b40` | SENSOR-B4-I07R1I-RATIFY — operator accepts the I07 chain, authorizes I08 (governance-only ledger truth) |
| `efde153e` | I08-A — SENSOR-B4-I08A: the two-phase RecoveryEngine — read-only deterministic scan + explicit apply/quarantine + typed finding vocabulary + append-only RecoveryAction journal (`recovery.py`) — with its behavioral proof (`test_recovery.py`) |
| `ae348941` | I08-B — SENSOR-B4-I08B: crash matrix, idempotence, TOCTOU and path-safety proof on the real I07 stack (`test_recovery_crash_matrix.py`) |
| I08-C | SENSOR-B4-I08C: frozen machine evidence (4 matrices), evidence MD, ledger reconciliation (`test_i08_evidence.py`) — this commit |

**Commit-staging deviation (recorded, not repaired):** the preferred
five-stage I08A–I08E chain was delivered as THREE commits.  The engine
(scan, apply, quarantine, journal) matured as one module, so the A/B/C/D
stage boundaries collapsed into the module commit (A), the adversarial
proof commit (B) and the evidence/ledger freeze commit (C).  Each commit
carries independent content; nothing was squashed and no history was
rewritten.

## 3. Scanner architecture (§35 single module)

`quant-lab/src/crypto_sensor_fabric/storage/recovery.py` — ONE focused
module, no jobs.py refactor, no module split:

- `RecoveryEngine` — the two explicit phases:
  - `scan(*, recovery_run_id=None) -> RecoveryScanResult` — READ-ONLY:
    never deletes, moves, rewrites, registers provenance, advances jobs,
    clears locks, changes manifests or moves a cursor.  Read access goes
    through existing repository APIs wherever possible (public gated
    `get_job` for jobs; repository forensic views for manifests;
    repositories' own Parquet row decoders for catalog-wide reads).
  - `apply_plan(result, *, recovery_run_id=None) -> list[RecoveryAction]`
    — the ONLY mutating path.  Every action revalidates its target
    against the scanned before-state first (§28 TOCTOU); a mismatch
    raises typed `RecoveryPlanConflict` and nothing is applied for that
    action.
- `RecoveryJournal` — append-only durable journal under
  `<t0_root>/catalogs/recovery/actions/` through the shared
  `DurableJsonCatalog` primitive (hashed physical keys, staged fsync'd
  writes, no-clobber publish, corruption fail-closed, I07R1F cache lock).
- Typed internal finding vocabulary (§25): UNCOMMITTED_STAGING,
  ORPHAN_DURABLE_BLOB, ORPHAN_PROJECTION, ORPHAN_MANIFEST, CORRUPT_BLOB,
  MISSING_MANIFEST_TARGET, ACQUISITION_SOURCE_QUARANTINED,
  JOB_DURABILITY_DIVERGENCE, LOCK_PRESENT_OWNER_UNPROVEN,
  UNKNOWN_CONTEXT.  No frozen enum was modified.
- Deterministic output (§26): findings sorted by
  (problem, object_type, object_id, detail); counts derived; same tree +
  same inputs ⇒ identical `RecoveryScanResult.to_dict()` (proven by
  repeat-scan byte-identical comparison).
- Run identity (§8): explicit `recovery_run_id` accepted everywhere;
  `new_run_id()` fallback is a monotonic counter under a lock hashed into
  a full digest — never wall-clock formatting, never temp paths.

## 4. RecoveryAction journal design (§6/§7)

- The FROZEN `RecoveryAction` model (03 doc §17) is used verbatim for
  every record whose object is one of the seven frozen
  `StorageObjectType` members; the frozen model was NOT altered.
- Internal durable envelope for staging artifacts and job locks (no
  frozen StorageObjectType member exists): the envelope carries the
  semantic `object_type` string, `storage_object_type=None`, plus
  envelope-level `action_kind` for run-scoped dedup.  This is the
  "internal durable envelope rather than changing frozen fields" option
  of §6.
- Logical action id = `action_identity()` = full SHA-256 over canonical
  JSON (sorted keys) of exactly: recovery_run_id, object_type, object_id,
  problem, resolution, before_state, after_state.  Registration time is
  EXCLUDED from identity and from the semantic-equality comparison, so
  operational registration time never changes scientific identity (§7).
- Exact retry: the catalog commit raises `JsonCatalogConflict` (same id,
  different envelope bytes only because of `registered_at`); the journal
  compares ALL semantic fields and, when they agree, ADOPTS the existing
  durable record — idempotent (§27).  Genuine divergence (tampered
  fragment, different semantics under the same id) raises typed
  `RecoveryActionConflict`; the underlying catalog independently refuses
  overwrite with `JsonCatalogConflict`.  `None` and `{}` before/after
  states are normalized to `{}` before identity and envelope so the two
  spellings can never fork the id.
- Read surface (§32, narrow): `journal.action_ids()`,
  `journal.get(id)`, `journal.list_for_run(run_id)`,
  `journal.list_for_object(type, id)`,
  `journal.to_recovery_action(payload)` — NOT the I12 query service.

## 5. Scan/apply separation results (§5/§13/§21)

- `test_recovery.py::test_scan_finds_all_defect_classes_read_only`:
  full content census of every file under the T0 root before and after a
  scan that surfaces six finding classes — byte-identical (read-only
  proof), plus deterministic repeat scan.
- `test_recovery.py::test_scan_read_only...` / matrix case
  `scan_read_only`: same proof on the real I07 stack.
- Corrupt-but-cached truth is forensic only: the forged event the refresh
  adopted into the catalog cache is visible to NO public read except
  through the I07R1I validation gate (`get_job` fails closed); apply-path
  transitions are refused by the runtime gate, so cached corruption can
  never become runtime state (§13, proven in
  `test_job_durability_divergence_detected_and_transition_refused`).

## 6. Apply revalidation rule (§28)

Every `_execute_*` handler first re-resolves and re-verifies its target:

- CORRUPT_BLOB: blob must STILL fail verification (`RecoveryPlanConflict`
  when it now verifies).
- ORPHAN_DURABLE_BLOB: metadata must still be absent and bytes present;
  plan applied only then.
- ORPHAN_PROJECTION / ORPHAN_MANIFEST / MISSING_MANIFEST_TARGET: target
  must still exist and hold the scanned state.
- JOB_DURABILITY_DIVERGENCE: chain must STILL fail validation through the
  PUBLIC gated read (which refreshes first); removal of the forged record
  mid-flight leaves cache-vs-disk divergence, which still fails closed —
  the plan stays refuse-safe rather than silently healing.
- Locks: lock file must still exist for the record; explicit clear
  requires the exact expected fingerprint.

Stale plan ⇒ typed `RecoveryPlanConflict`, no partial application of that
action (proven: metadata-appears case, corrupt-blob-repaired case).

## 7. Per-class findings and behavior

### Staging (§13, class A)
`<t0_root>/staging/**.partial` (the actual implementation layout — blob
store `put()` writes `<secrets.token_hex>.partial` under `staging/`) is
classified UNCOMMITTED_STAGING with location, size and byte SHA.  Apply
preserves the bytes under `quarantine/malformed/` with byte-equality
revalidation; resume is never advanced from staging.

### Orphan durable blob (§12, class B)
Committed physical object under `blobs/sha256/**` without durable
EvidenceBlob metadata (rename-committed / metadata-lost crash).  Apply
verifies bytes against the content-addressed name, then:
- registered operator context (explicit `register_orphan_context`) +
  byte-verified identity ⇒ reconcile through the PUBLIC
  `append_metadata` / `append_acquisition` APIs (their validation stays
  authoritative; a refusal leaves the orphan unresolved, recorded);
- no proven context ⇒ unknown_context quarantine, bytes preserved.
  Provenance is NEVER manufactured.

### Orphan projection (§14, classes C/H)
`projection_sha256` is the physical file-bytes hash (verified from
`ProjectionArtifactRepository._verify_physical_projection`), so a
physical `projections/**.parquet` hashing to no committed artifact record
is ORPHAN_PROJECTION.  Apply quarantines under unknown_context; lineage
is never manufactured; repair only through canonical repository APIs
when unambiguous (none is invented in I08).

### Orphan manifest fragments (§15, class G)
Detected through the manifests module's own fragments + chain logic
(unknown-context findings additionally cover unparseable fragments).
Apply reconciles through the PUBLIC `append_partition_manifest` with
public-pointer CAS attestation ONLY when ancestry is exact (supersedes is
in the chain or None) and every blob ref verifies; otherwise the orphan
is recorded UNRESOLVED.  NO "latest wins": the crash-5 test proves the
committed chain stays v1 after apply.

### Missing manifest targets (§16, class D)
Manifest history is immutable: the finding names manifest, partition,
version and missing refs; apply records evidence only and re-verifies
the fail-closed gate.  No in-place edit; a replacement, if ever
justified, is a NEW version.

### Acquisition → quarantined/missing blob (§17, class E)
Acquisition history untouched; the dependency is recorded and the
physical-verification gate is re-verified to fail closed for the
affected record at apply time.

### Job durability divergence (§18/§19, class F)
Detection uses the PUBLIC gated `get_job` (lock → refresh both catalogs →
`_validate_job_chain` → state) — the I07R1H/I07R1I accepted authority, so
a forged event published after construction IS seen (the refresh adopts
it).  Apply attempts the safe annotated transition to QUARANTINED through
the public `advance_status` API with a nonempty recovery reason; the
frozen graph accepts the edge in principle, but the runtime gate refuses
ANY operation on a corrupt chain, so the outcome is the journaled
UNRESOLVED record with the refusal reason (explicitly permitted by §18)
— old checkpoint events are never mutated and the event count is
unchanged.  QUARANTINED remains terminal; no automatic
QUARANTINED → ACQUIRING edge was invented.

### Job locks (§20, class I)
LOCK_PRESENT_OWNER_UNPROVEN — never "stale"; scan/apply never delete a
lock.  `clear_job_lock()` is the explicit operator path: requires the
exact expected job id hashing to the lock fingerprint, refuses when an
in-process owner holds the job's RLock (non-blocking probe), journals the
RecoveryAction BEFORE removing the file.  No TTL deletion.

## 8. Corrupt blob quarantine (§11, class J)

Apply re-verifies corruption, moves the corrupt bytes into
`quarantine/integrity/` via `publish_no_replace` (the shared atomic
no-clobber primitive) and unlinks the source only after publication —
bytes preserved throughout.  The canonical location becomes unusable
(bytes gone; every existing integrity gate fails closed; typed
`BlobMissing`/`QUARANTINED_INTEGRITY_FAILURE` surfaces).  An explicit
QUARANTINED_INTEGRITY_FAILURE metadata row is ATTEMPTED through the
public `append_metadata` API — the physical gate is expected to refuse it
once the bytes are gone, and the attempt is recorded in the journal
after-state, never forced by hand-written fragments.  Affected
acquisition/manifest history is preserved untouched and surfaced as
dependency findings.  A second valid representation of the same source
SHA (other encoding) is never destroyed — only the corrupt physical key
is quarantined.

## 9. Quarantine paths, no-clobber, safety (§9/§10/§29/§30)

- Categories implemented: `integrity`, `malformed`, `unknown_context`
  (the three §9 minimums).  Security-specific categories NOT invented;
  no secure-delete; no automatic action on arbitrary T0 content.
- Destination formula:
  `quarantine/<category>/<object_type>-<sha256(bytes)[:32]>-<sha256(object_id)[:32]><suffix>`
  — content hash decides byte-identity (exact retry adopts the existing
  identical artifact, returning False "adopted"), object hash separates
  distinct objects sharing bytes; different bytes behind the same
  locator raise typed `RecoveryQuarantineConflict` (no overwrite ever).
- Path safety (§29): every discovered path and destination is asserted
  lexically AND `resolve()`-contained under the T0 root; `..`-escapes and
  symlink escapes raise `RecoveryPathSafetyError`; no raw logical id ever
  becomes a path component (destination names are hash-based).
  Proven: outside-root move refused with nothing created;
  symlink-source case refused (POSIX run; honestly SKIPPED_ON_WINDOWS in
  the committed matrix — the Windows CI surface cannot create the POSIX
  symlink attack, recorded rather than faked).

## 10. Crash matrix (§24) — all 12 frozen scenarios

Committed matrix `BLOC_04_I08_CRASH_MATRIX.json` — 12 cases, ALL `OK`:

1. crash halfway through blob write → UNCOMMITTED_STAGING; no committed
   claim; no cursor movement; staging quarantined (bytes preserved).
2. crash after blob rename before metadata → ORPHAN_DURABLE_BLOB;
   without proven context: unknown_context quarantine (with-context
   reconciliation is separately proven in `test_recovery_crash_matrix.py`
   via the public APIs).
3. crash after acquisition commit before projection → T0A valid,
   projection rebuildable, scan clean (no manufactured findings).
4. crash after projection write before manifest → ORPHAN_PROJECTION
   detected; lineage verified before any reconciliation.
5. crash before manifest-current pointer update → immutable orphan
   fragment recorded UNRESOLVED; current pointer stays old valid truth
   (chain = [pm-c5-mx] after apply).
6. crash before resume advancement → durable batch valid; checkpoint
   state holds exact blob/manifest anchors; resume NOT skipped; scan
   clean.
7. identical refetch → same content identity; existing acquisition
   semantics preserved.
8. same source/request with mutated bytes → two acquisition records on
   the same blob (I06 revision semantics preserved; recovery adds
   nothing).
9. corrupted stored blob → integrity quarantine; canonical key empty;
   corrupt bytes preserved; acquisition history intact.
10. missing manifest target → typed finding + planned evidence action;
    canonical chain intact; repository blob-ref gate still fails closed.
11. parser bug / invalid projection → T0A retained; bad projection
    quarantined as unknown context; no source rewrite.
12. concurrent writers to same logical partition → stale
    `expected_current` refused with `ManifestCASConflict`; correct CAS
    append wins (I04 §40 preserved).

## 11. Idempotence matrix (§27/§28/§20)

`BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json` — 6 cases, ALL `OK`:
scan_read_only (byte census identical), repeat_scan_same_findings,
repeat_apply_idempotent (first applies, same-run second returns zero new
actions, single artifact), stale_plan_conflict (typed), 
recovery_action_exact_retry (adopts existing) +
divergence_typed (catalog refuses overwrite), foreign_lock_not_auto_deleted.

## 12. Scan and quarantine matrices (§37)

- `BLOC_04_I08_RECOVERY_SCAN_MATRIX.json` — 11 cases (clean_root,
  uncommitted_staging, orphan_durable_blob, orphan_projection,
  orphan_manifest, missing_manifest_blob, quarantined_blob_dependency,
  job_durability_divergence, lock_owner_unproven, unknown_context,
  scan_deterministic_sorted): ALL `OK`.
- `BLOC_04_I08_QUARANTINE_MATRIX.json` — 9 cases (corrupt_blob_quarantined,
  quarantine_bytes_preserved, canonical_bad_object_unusable, no_overwrite
  [adopt + conflict], exact_retry_idempotent, different_bytes_conflict,
  unknown_context_quarantine, path_escape_rejected,
  symlink_escape_rejected): 8 `OK` + 1 `SKIPPED_ON_WINDOWS` (POSIX-only
  symlink attack; recorded honestly, not faked).

Evidence governance (§40): builders are pure; normal pytest generates to
tmp and compares byte-for-byte against committed files
(`test_generated_matches_committed`); `test_evidence_directory_untouched_after_run`
proves pytest never writes the evidence tree.  Publication happened once
via the explicit module invocation.

## 13. I07 regression firewall (§33)

Full storage suite green at the final tree including every accepted I07
guarantee: public `advance_status` signature (no resume token / anchors /
gate flag), `advance_checkpoint` sole cursor writer, checkpoint proof V1,
persisted-floor cross-config retries, same transition graph runtime and
restart (I07R1G 17 forged-proof cases + control; I07R1H 13 chain cases +
intact control), catalog RLock, validated public `get_job` /
`list_transitions`, failed outer-entry rollback, same-thread retry
revalidation, two-repository refresh and sequence serialization.
Counts: storage **1191 passed / 0 failed / 4 skipped**; full **2570 passed /
0 failed / 5 skipped** (exact counts in §15).  Historical I07 evidence
untouched (`git status`: only additions under `evidence/bloc_04/`, the
seven documented pre-existing CRLF-churn legacy files restored before
commit — zero content delta).

## 14. Scope boundaries (§21/§22/§23/§33)

No quota engine, no disk-pressure thresholds (I09); no DuckDB, no
PostgreSQL (I10/I11); no RawEvidenceQuery service, no general replay API
(I12); no provider integration; no I08→I13/I14 scope creep.  Network = 0;
provider source unchanged; research not resumed; I09 NOT started.

## 15. Fresh baseline and final counts (§39)

Fresh post-ratification baseline at `abcc1b40` (measured, not copied):
storage **1142 passed / 0 failed / 3 skipped**, full **2521 passed /
0 failed / 4 skipped**.

Final at the I08 tree (recorded runs):
- storage: **1191 passed / 0 failed / 4 skipped** (+49 vs baseline)
- full: **2570 passed / 0 failed / 5 skipped** (+49)
- zero failures; the one unrelated blob-store threading flake documented
  at I07R1H did not reproduce in the final recorded runs.

## 16. Ruff / mypy (§32) — precise statements

- Ruff: `All checks passed!` on the complete changed scope
  (`recovery.py`, `test_recovery.py`, `test_recovery_crash_matrix.py`,
  `test_i08_evidence.py`).
- mypy production source: `recovery.py` checked — the ONLY error in its
  dependency closure is the exact documented pre-existing
  `probes/planner.py:79 [call-overload]` baseline.  No new error class or
  instance in production code.
- mypy new test modules (source root explicitly configured via
  `MYPYPATH=src;tests/crypto_sensor_fabric/storage` +
  `--explicit-package-bases`, the I07R1G/I07R1H convention; the repo has
  no `[tool.mypy]` policy): `test_recovery.py`,
  `test_recovery_crash_matrix.py`, `test_i08_evidence.py` — each fully
  clean, the only remaining error per run being the same
  `probes/planner.py:79` baseline.  No import-not-found, no arg-type
  residue.  The sibling-loader note: static analysis cannot see
  `test_job_state_r1.py` through `load_sibling`, so the crash-matrix
  module uses an explicit `_engine(stack)` helper and a typed factory
  instead of a subclass of the loaded base class — that is why it is
  fully clean without per-file ignores.

## 17. External CI / network / provider (§31/§42)

No GitHub CI success is claimed: no workflow runs or combined statuses
exist for this branch.  Network = 0 (pure local filesystem storage).
Provider source unchanged (`git status`: no `providers/` modifications).
No quota, no DuckDB, no Postgres, no RawEvidenceQuery, no recovery of
research streams.

## 18. Proposed verdicts and stop gate (§36/§41/§43)

- `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED =
  PENDING_OPERATOR_REVIEW` (proposed; NOT self-ratified).
- `RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`.
- `recommended_next = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR`.
- `next_checkpoint_authorized = FALSE`.
- Ledger during repair: Current checkpoint = SENSOR-B4-I08; I07 chain all
  `OPERATOR_ACCEPTED`; `DURABLE_RESUME_IMPLEMENTED = TRUE`.
- STOP GATE honored: I09/I10/I11/I12/I13/I14/I15/I16/I17 NOT started;
  research NOT resumed.
