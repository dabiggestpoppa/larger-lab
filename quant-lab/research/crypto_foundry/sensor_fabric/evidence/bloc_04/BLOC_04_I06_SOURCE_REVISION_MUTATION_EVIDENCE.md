# SENSOR-B4-I06 — SOURCE REVISION / MUTATION REGISTRY

**Checkpoint:** SENSOR-B4-I06 (Source Revision / Mutation Registry)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I06_SOURCE_REVISION_MUTATION_REGISTRY`; proposed `G4-04_REVISION_GATE = IMPLEMENTATION_PASS`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`9740510d5ea5693c94937cda4b5a5356b448c41c` (I05R4E evidence freeze).
Verified exactly at session start; clean tree; required I05R4 lineage
(`5a982b80` → `f08c3019` → `1855844c` → `b9802e39` → `9740510d`) present.

## 2. Ending SHA / Commit Chain

| Commit | Stage |
|---|---|
| `ce4d8412` | I05R4-RATIFY: operator accepts the complete I05 chain, corrects evidence wording, authorizes I06 ONLY |
| `c5c90c3e` | I06A: freeze source-revision identity V1 and immutable revision records |
| `b43b35f5` | I06B: implement durable mutation/refetch registry and source-key coordination |
| `e2e98331` | I06C: implement explicit revision declarations and fail-safe resolution modes |
| `e0e6466d` | I06D: seal temporal, concurrency, restart, corruption and A-B-A adversarial proof |
| `80cfbcfe` | I06E: freeze I06 machine matrices (deterministic, read-only verified) |
| *(this commit)* | I06E: evidence + ledger freeze |

No squash.

## 3. I05 Ratification (§2/§3)

Governance commit `ce4d8412` records operator acceptance of:

- `PASS_SENSOR_B4_I05R4_EVIDENCE_INTERFACE_RETRY_SEALED`
- `PASS_SENSOR_B4_I05R3_LINEAGE_IDENTITY_TIME_SEALED`
- `PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED`
- `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED`
- `PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE`

and authorizes SENSOR-B4-I06 ONLY. Flags set TRUE: `T0A_EVIDENCE_PIPELINE_COMPLETE`,
`T0B_PROJECTION_SCHEMA_READY`, `T0B_PHYSICAL_PROJECTION_WRITER_READY`,
`T0B_PROJECTION_CATALOG_IMPLEMENTED`, `T0B_LINEAGE_REPOSITORY_IMPLEMENTED`,
`T0B_TO_T0A_LINEAGE_COMPLETE`, `T0B_STORAGE_IMPLEMENTED`.

**I05R4 evidence-wording reconciliation (§3, governance-only):** the I05R4
checkpoint ADDED new evidence files, so the post-I05R4 evidence-tree hash
cannot literally equal the entire pre-I05R4 evidence tree. What is actually
proven, and now recorded chronologically in `BLOC_04_I05R4_OPERATOR_RATIFICATION.md`:

- historical I05/I05R1/I05R2/I05R3 evidence files were NOT modified by I05R4;
- the NEW I05R4 evidence files were committed;
- normal test execution left all committed evidence bytes unchanged;
- the evidence tree was git-clean after the final suites.

No behavioral repair. Historical I05R4 evidence untouched.

## 4. Fresh Baseline (§86)

Historical I05R4 evidence reports storage 875/872/0/3 and full 2255/2251/0/4.
Fresh pre-change HEAD baseline (recorded, not copied): **identical at
measurement time — storage 872 passed / 0 failed / 3 skipped (875 collected);
full 2251 passed / 0 failed / 4 skipped (2255 collected)**.

## 5. RevisionSourceIdentityV1 (§9-§14)

- `identity_version = 1` — closed contract; any future change to source-key
  semantics requires a new identity version and never silently re-keys an
  existing registry.
- Frozen field set (REQUEST semantics only): `provider_id`, `venue`,
  `sensor_family`, `native_instrument`, `native_granularity`,
  `request_fingerprint`, `requested_start`, `requested_end`,
  `endpoint_host`, `endpoint_path`, `request_family`.
- Excluded (§11): acquisition_id, blob_sha256, adapter versions,
  request_started_at, response_observed_at, ingested_at, actual range,
  HTTP status, schema_state, provider checksums, resume tokens, quality
  flags, failure_ref, wall clocks. `source_locator` is deliberately absent
  (§12) — it may be a temporary delivery URL; request semantics are the
  generic identity authority.
- Canonicalization (§10): enums by value; timestamps UTC ISO-8601 (aware
  inputs normalized; naive rejected); native strings preserved exactly.

## 6. Source Key Formula (§13)

```
source_revision_key = SHA256(canonical_json_bytes({
    "identity_version": 1,
    "fields": { ...frozen V1 field set... }
}))
```

Full 64 lowercase hex, no truncation, language-neutral canonical JSON
(sorted keys, compact separators). The descriptor is persisted INSIDE every
segment record. On every reload the descriptor is recomputed and must hash
to the stored key — mismatch ⇒ `SourceRevisionCatalogCorrupt` (§14).
The content hash NEVER enters the source key (§8): mutation mints a
REVISION, never a new "source".

## 7. Durable Layout (§28)

```
catalogs/source_revisions/
    segments/       one immutable birth record per revision
                    (segment_id = <source_revision_key>:<revision_number>;
                     the catalog logical id — one source owns MANY segments)
    observations/   one immutable observation per subsequent acquisition
                    (observation_id = acquisition_id)
    declarations/   explicit provider revision/canonical evidence
    locks/          per-source-key coordination locks
```

All publications use `DurableJsonCatalog` (staging → flush → fsync → verify
→ no-clobber publish → parent-dir fsync). No `write_text`, no overwrite, no
mutable history.

## 8. Registration Gates

- Sealed dependencies (§16): `RevisionAcquisitionSource`,
  `RevisionBlobSource`, `RevisionPhysicalStore` protocols enforced at
  CONSTRUCTION — `RevisionConfigurationError` otherwise; no optional proof
  dependencies.
- Durable acquisition resolution (§15): the registry resolves the
  `AcquisitionRecord` itself; caller-supplied records are never authority.
- Blob required (§17): blobless (failure/no-data/unavailable) acquisitions
  stay in acquisition history but create NO content segment
  (`RevisionContentUnavailable`); no zero hash is manufactured.
- Physical T0A verification (§18): at least one stored representation must
  verify `LOCAL_HASH_VERIFIED`; presence-only is insufficient; missing
  metadata or unprovable bytes ⇒ `RevisionContentCorrupt`.
- Forensic observations (§19): the acquisition may be OBSERVED because the
  provider returned exact bytes, with `usable_provenance=False` preserved
  via THE one I04R2 §13 predicate (`is_usable_manifest_provenance`) — no
  duplicated eligibility logic; revision evidence never promotes usability.
- Seen time (§20): `response_observed_at` only. `registered_at` is
  operational audit (§21, injected clock) and never controls chronology,
  numbering or keys; it is also excluded from semantic conflict comparison.

## 9. Classification Semantics (§22-§27, §33-§41)

- First observation ⇒ rev1 `STABLE` (§23); segment birth IS the first
  observation (§32) with `first_acquisition_id` preserved.
- Identical bytes to the CURRENT segment ⇒ `IDENTICAL_REFETCH` observation,
  NO new revision (§24); `last_seen_at` is MATERIALIZED from append-only
  observations (§30) — birth records are never rewritten.
- Different bytes ⇒ new revision: `SOURCE_MUTATION` (WARNING) or
  `PROVIDER_DECLARED_REVISION` (NOTICE) ONLY with explicit declaration
  evidence (§25/§33). `UNKNOWN_REVISION` is never a default (§38).
- A→B→A ⇒ THREE segments (§26); identical bytes are identical to the
  CURRENT segment only (§27); history is never collapsed by blob identity
  (§66 proven byte-identical rev1 across later revisions).
- Provider declaration requires durable `evidence_ref` — never inferred
  from bytes/ETag/status/filenames (§33). Declared revision ≠ canonical
  (§61). Provider-declared same-bytes preserved as declaration evidence
  with unchanged revision number (§34).
- Ordering (§39/§40/§41): observations append-chronological by seen_at;
  earlier-than-latest ⇒ `RevisionObservationOrderConflict`; identical
  seen_at with differing bytes ⇒ `RevisionTemporalAmbiguity` (fail closed);
  identical seen_at with identical bytes ⇒ legal refetch. No renumbering,
  ever.

## 10. Writer Coordination (§43-§46)

Per-source-key filesystem lock (no-clobber create; bounded wait via
`lock_timeout_seconds`). A pre-existing lock raises `RevisionLockHeld` and
is NEVER auto-deleted (I08 owns stale-lock recovery). Concurrent identical
refetches converge to one segment with both observations (§45). Concurrent
different-byte mutations serialize through the lock: exactly one winner,
the loser fails typed, revision numbering can never fork (§46 — proven with
threads on the real registry).

## 11. Idempotence (§47/§48/§68)

Re-registering an acquisition re-resolves durable truth, RE-VERIFIES the
physical blob, recomputes the key and compares the binding against DURABLE
truth (segment birth binding + persisted observation semantics; a tampered
in-memory binding fails typed). Divergence ⇒ `RevisionObservationConflict`.
Concurrent duplicate commits adopt only on semantic agreement
(`registered_at` excluded as operational); divergence ⇒ typed conflict.
Crash between segment birth and observation completes on retry with the
segment's OWN classification — never a different revision chain (§68).

## 12. Restart / Corruption (§49/§79/§80)

Reload validation: identity descriptor recomputes to the stored key;
segment_id binds to (key, revision_number); revision numbers contiguous
from 1 per source; first_seen_at strictly increasing; segments' first
acquisitions exist durably with matching blobs; observations reference
existing revisions with matching blobs and durable acquisitions; no
acquisition belongs to two revisions; declarations reference existing
revisions; frozen vocabularies (state/severity/kind) enforced on reload.
Every corruption mode fails closed as `SourceRevisionCatalogCorrupt` —
a corrupt committed object never becomes "not registered".

## 13. Resolution (§54-§62)

`RevisionResolution` exposes key, policy, selected numbers, ambiguous flag,
all candidates, canonical evidence. Frozen policies, fail-safe:

| Policy | Behavior |
|---|---|
| `ERROR_ON_AMBIGUITY` (default) | 0 ⇒ NotFound, 1 ⇒ it, >1 ⇒ `RevisionAmbiguityError` — never picks latest (§55) |
| `ALL` | full A→B→A sequence, no blob dedupe (§56) |
| `FIRST_SEEN` | explicit opt-in; revision 1; NOT automatic PIT truth (§57) |
| `LATEST_SEEN` | explicit opt-in; latest OBSERVED state, not economic truth (§58) |
| `EXACT_REVISION` | requires number ≥ 1; unknown ⇒ NotFound; no fallback (§59) |
| `PROVIDER_DECLARED_CANONICAL` | unique explicit canonical only; zero ⇒ `RevisionResolutionUnavailable`; >1 distinct ⇒ ambiguous; duplicate declarations of one revision resolve consistently (§60) |

Selection resolves VERSION IDENTITY only — it never asserts blob integrity
or acquisition usability (§62; proven: forensic-birth revision resolves
while usability stays an acquisition-level property).

## 14. T0B Non-Invalidation (§63-§66)

Proven with the real production stack: a valid rev1 projection chain
(artifact + context + lineage) built from a rev1 acquisition remains
`validate_projection_ref`-valid through the production resolver AFTER rev2
is registered; the manifest's immutable content is untouched; rev1 segment,
acquisition and blob bytes remain byte-identical. No supersede, no
invalidation, no manifest mutation, no automatic revision_count retrofit
(§65).

## 15. Machine Evidence (§85)

- `BLOC_04_I06_IDENTITY_MATRIX.json` — derivation, exclusion, full-hex key,
  descriptor tamper fail-closed, identity_version frozen.
- `BLOC_04_I06_MUTATION_MATRIX.json` — A→B→A, identical refetch,
  out-of-order fail-closed, same-time ambiguity fail-closed, corrupted-blob
  re-registration failure, restart preservation.
- `BLOC_04_I06_RESOLUTION_MATRIX.json` — all six policies, canonical
  uniqueness/ambiguity/duplicates.

All three are deterministic (canonical JSON, fixed clocks, no wall clock)
and published once explicitly via the generator's `_publish()` entry point;
the pytest layer is READ-ONLY and compares regenerated bytes against
committed bytes (I05R4 read-only evidence policy — a production behavior
change now breaks the evidence test instead of silently rewriting history).

## 16. Final Counts (§86/§90)

| Check | Result |
|---|---|
| storage | **939 passed / 0 failed / 3 skipped** (942 collected) |
| full suite | **2318 passed / 0 failed / 4 skipped** (2322 collected) |
| ruff (changed scope) | clean |
| mypy (changed scope) | clean (pre-existing `probes/planner.py:79` baseline only) |
| network calls | 0 |
| provider source changes | none |
| evidence tree after suites | git diff clean |

Final passing counts exceed the fresh baseline (+67 storage, +67 full).

## 17. Gates

- [x] exact start `9740510d...`; complete I05 chain operator-ratified
- [x] old evidence untouched; I05R4 hash wording chronologically corrected
- [x] identity versioned; source key excludes content hash and wall-clock identity
- [x] source key deterministic full SHA256; persisted descriptor recomputes
- [x] rev1 STABLE / IDENTICAL_REFETCH / SOURCE_MUTATION / A→B→A / contiguous numbering
- [x] no old content overwritten; repeated acquisitions visible; last_seen append-only
- [x] provider declaration explicit, never inferred; declared ≠ canonical
- [x] canonical requires evidence; multiple distinct canonicals ambiguous
- [x] ERROR_ON_AMBIGUITY never picks latest; ALL complete; FIRST/LATEST explicit; EXACT strict
- [x] out-of-order and same-time conflicting observations fail closed
- [x] per-source concurrency cannot fork numbering; stale lock never auto-deleted
- [x] re-registration re-verifies physical truth; corrupt blob prevents idempotent success
- [x] registry survives restart; corrupt registry fails closed
- [x] forensic acquisitions never promoted
- [x] rev2 does not invalidate rev1 T0B; old manifests not mutated
- [x] no RawEvidenceQuery/job-state/recovery-scanner/quota/DuckDB/Postgres/Bloc3 integration
- [x] no network; provider code unchanged; evidence tests read-only
- [x] full suite ≥ fresh baseline; zero failures; ruff clean; mypy changed scope clean
- [x] I07 NOT started; Bloc 5 NOT started; research NOT resumed

## 18. Next

`SOURCE_REVISION_REGISTRY_IMPLEMENTED = TRUE`, `SOURCE_MUTATION_EXPLICIT = TRUE`,
`REVISION_RESOLUTION_READY = TRUE`. `DURABLE_RESUME_IMPLEMENTED = FALSE`,
`RECOVERY_SCANNER_IMPLEMENTED = FALSE`, `next_checkpoint_authorized = FALSE`.
Recommended next (operator review required): **SENSOR-B4-I07 DURABLE JOB
STATE + RESUME COUPLING**. NOT started.

**STOP GATE honored.**
