# SENSOR-B4-I06R1 — CANONICAL MODEL + SOURCE-IDENTITY BINDING + DECLARATION-DURABILITY SEAL

**Checkpoint:** SENSOR-B4-I06R1 (Canonical Revision Contract Microseal)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I06R1_CANONICAL_CONTRACT_DECLARATION_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`295a8af57cea8aeb13d3f06b7e5b23a521020f05` (I06E evidence + ledger freeze).
Verified exactly at session start; clean tree; full required I06 lineage
present (`ce4d8412` RATIFY → `c5c90c3e` I06A → `b43b35f5` I06B →
`e2e98331` I06C → `e0e6466d` I06D → `80cfbcfe` + `295a8af5` I06E).

## 2. Ending SHA / Commit Chain

| Commit | Stage |
|---|---|
| `2c4ad0b1` | I06R1A/R1B: canonical vocabulary (enums singleton, models.SourceRevision materialization, typed datetimes) + durable-acquisition identity binding |
| `444e2ad1` | I06R1C: typed ProviderRevisionDeclaration, crash-safe declaration-before-segment, source-namespaced deterministic declaration IDs, UTC-strict times |
| `3f142288` | I06R1D: coordinated-tamper restart + declaration crash adversarial proof |
| *(this commit)* | I06R1E: canonical-contract/declaration-durability evidence + ledger freeze |

No squash.

## 3. Operator Findings → Dispositions (§0)

| Defect | Repair |
|---|---|
| A. I06 forked frozen revision enums + SourceRevision model | `RevisionState`/`RevisionPolicy` imported from `storage.enums` only; `RevisionResolutionMode = RevisionPolicy` object alias (§4: `RevisionResolutionMode is RevisionPolicy` is TRUE); shadow `SourceRevision` deleted; `get_revision`/`list_revisions` return `storage.models.SourceRevision` with aware-UTC datetimes + canonical enum (§5-§7/§41); `first_acquisition_id` exposed via `segment_for_revision` metadata API, NOT on the frozen model (§7) |
| B. identity version not fully bound to durable acquisition truth | `identity_version: Literal[1]` on `RevisionSourceIdentityV1` AND `RevisionSegmentRecord` (§9); V2 construction rejected; V2 persisted record rejected on reload; restart re-derives identity from the durable birth acquisition for EVERY segment and requires descriptor AND key to match (§11); observation source keys bound to durable acquisitions (§12); coordinated tamper + wrong-source + duplicate-birth adversarial proofs (§13-§15) |
| C. provider-declared classification could become durable before its evidence | Declaration is committed BEFORE the segment (§25 option A): pending declaration (revision_number=None) binds source key + acquisition + blob + evidence + declared_at; a crash leaves declaration evidence only — never unsupported truth; restart proves EVERY PROVIDER_DECLARED_REVISION segment carries supporting evidence (§26, segment-driven); crash boundary matrix (§27); exact-evidence retry completes intended classification, divergent evidence is typed `RevisionDeclarationConflict` (§28) |
| D. declaration identity/time/evidence seams | `ProviderRevisionDeclaration` typed input replaces dict semantics (§24): nonempty evidence_ref + aware declared_at normalized to UTC; `Literal["revision", "canonical"]` declaration_kind (§33); default declaration ID = full SHA256 over canonical source-namespaced semantics — key, kind, transition, evidence_ref, declared_at (§35); no wall-clock registered_at in identity; exact repeat adopts committed record, no duplicate append (§37); declared_at/registered_at are typed datetimes, naive/malformed rejected (§31/§32) |
| E. birth re-registration not classification-idempotent | Birth re-registration returns the segment's OWN classification (`_BIRTH_OBSERVATION_STATES` map shared by crash-completion and idempotence paths): STABLE→FIRST_REGISTRATION/INFO, SOURCE_MUTATION→WARNING, PROVIDER_DECLARED_REVISION→NOTICE (§19); never IDENTICAL_REFETCH, no new observation, no new segment; IDENTICAL_REFETCH requires a distinct acquisition event (§21); same-process and restart results are field-identical (§20) |

**Parked (not repaired here, per §49):** broad `revisions.py` decomposition
(module remains ~2100 lines; truth-contract repair only).  Recorded as
design debt for a hygiene checkpoint; no regression surface before I07.

## 4. Fresh Baseline (§53)

Historical I06 evidence reports storage 942/939/0/3 and full 2322/2318/0/4.
Fresh pre-change baseline measured at detached worktree `295a8af5`
(recorded, not copied): **storage 939 passed / 0 failed / 3 skipped (942
collected); full 2318 passed / 0 failed / 4 skipped (2322 collected)** —
matches the frozen evidence exactly.

Method note: the first worktree attempt used the ambient `core.autocrlf=true`
checkout, which rewrote committed LF evidence bytes to CRLF on disk and
failed 11 byte-comparison tests — a checkout artifact, not product truth.
The baseline was retaken with `core.autocrlf=false` and passed exactly.
The main working tree (where evidence files were written and committed)
passes unmodified.

## 5. Canonical Vocabulary Reconciliation (§3-§8)

- `from .enums import RevisionPolicy, RevisionState` — no second Enum class
  exists; identity test asserts `RState is EState` and the policy alias.
- `from .models import SourceRevision` — the frozen core model is the ONLY
  public/materialized revision view.  Timestamps are `datetime` (aware UTC),
  `revision_state` is the canonical `RevisionState` enum instance.
- Canonical-vocabulary matrix case proves both singletons at runtime.

## 6. Identity Version Enforcement (§9-§10)

- `RevisionSourceIdentityV1.identity_version: Literal[1]` — V2 construction
  raises pydantic ValidationError (matrix: `identity_version_2_rejected`).
- `RevisionSegmentRecord.identity_version: Literal[1]` — a segment tampered
  to `identity_version=2` fails reload with `SourceRevisionCatalogCorrupt`.
- Registry constant `IDENTITY_VERSION = 1` unchanged; reload rejects any
  other persisted version.

## 7. Durable-Acquisition Identity Binding (§11-§15)

For EVERY committed segment, restart validation:

1. resolves `segment.first_acquisition_id` from the durable
   `AcquisitionRepository`;
2. requires the acquisition's blob to equal the segment blob;
3. re-derives `RevisionSourceIdentityV1.from_acquisition(acq)` from REQUEST
   semantics;
4. requires derived descriptor == persisted descriptor AND derived key ==
   persisted key.

For EVERY persisted observation: durable acquisition resolved; blob equal;
derived key equal to `observation.source_revision_key` (same bytes under a
different logical source is corruption, §12/§14).  Birth bindings are seeded
from segments at load (§18) and merged with observation bindings; any
acquisition owning two revisions fails closed (§15).

**Coordinated tamper result (§13):** descriptor + source key + segment_id +
physical filename rewritten consistently (descriptor hashes to the forged
key) with the durable acquisition untouched → restart FAILS
`SourceRevisionCatalogCorrupt`, because the forged identity no longer
matches the birth acquisition's request semantics.  Internal hash
consistency is not enough.

**Duplicate birth result (§15):** a forged second segment claiming the same
`first_acquisition_id` (same blob) → restart fails closed.

**Durable-acquisition request mismatch:** flipping the persisted
acquisition's `request_fingerprint` under a valid registry → restart fails
closed (descriptor no longer re-derives from durable truth).

## 8. Birth-Observation Invariant (§16-§22)

Segment birth IS the first observation (preferred simplest v1).  The birth
segment stores `first_acquisition_id`, `first_seen_at`, `blob_sha256`, and
the birth classification; `RevisionObservationRecord` exists only for
SUBSEQUENT observations.  Exactly one first-observation identity per
revision; no birth duplication (§22: A→A→B→B→A yields five acquisition
observations total — births + subsequent records).

Birth re-registration (§19): re-resolves durable acquisition, re-verifies
the physical T0A blob, recomputes the source identity, and returns the
ORIGINAL birth classification.  Same-process and restart paths produce
field-identical results (§20 matrix cases `birth_same_process_idempotent`,
`birth_restart_idempotent`).

## 9. Provider-Declaration Publication Order (§23-§29)

Durable order for a provider-declared NEW revision (§25 option A):

```
validate ProviderRevisionDeclaration (typed, evidence_ref nonempty,
declared_at aware → UTC)
→ commit immutable PENDING declaration (revision_number=None, bound to
  source key + acquisition + blob)   [evidence FIRST]
→ commit segment (PROVIDER_DECLARED_REVISION)
→ commit observation
→ success
```

A crash between declaration and segment leaves declaration evidence only —
safe, never revision truth (§27 boundary 2 matrix).  Retry semantics (§28):

- same acquisition + same declaration evidence → completes the EXACT
  intended provider-declared revision;
- same acquisition + different evidence/declared_at → typed
  `RevisionDeclarationConflict`; never silent downgrade/upgrade;
- §68 birth completion after a crash tolerates ABSENT re-supplied evidence
  (the classification and its bound evidence are already durable) but any
  supplied evidence must match.

Restart (§26): every PROVIDER_DECLARED_REVISION segment must have
supporting durable revision-declaration evidence (matching key + transition
by revision number or pending-binding); removed evidence fails closed —
segment-driven validation catches deletion.

Same-bytes declaration (§29/§34): no new content revision; the declaration
is preserved as evidence against the current revision; observation follows
existing content semantics (`IDENTICAL_REFETCH`).

## 10. Declaration ID Formula (§34-§37)

```
declaration_id = SHA256(canonical_json({
    identity_kind: "source_revision_declaration_v1",
    source_revision_key, declaration_kind, revision_number,
    bound_acquisition_id, blob_sha256, evidence_ref, declared_at(UTC ISO)
}))
```

Full 64 lowercase hex, no truncation, no wall clock.  Source-namespaced, so
two unrelated source keys can never collide (§36 matrix: revision AND
canonical declarations across two sources — all distinct, both commit,
both resolve canonically).  Explicit caller-supplied IDs remain possible
but conflicts are fail-closed via `RevisionDeclarationConflict` (§37
idempotence: exact repeat adopts; semantic divergence under one ID
conflicts).

## 11. UTC Declaration Contract (§30-§33)

- `evidence_ref` nonempty everywhere (typed input + both declaration
  methods); empty/whitespace/None rejected.
- `declared_at`/`registered_at` on `RevisionDeclarationRecord`, and all
  segment/observation time fields, are typed `datetime` with aware-only
  validation normalized to UTC (§31/§32).  No `str(datetime)` path exists;
  reload rejects naive/malformed timestamps via pydantic (catalog corrupt).
- `declaration_kind: Literal["revision", "canonical"]` (§33).

## 12. Regression Seals

- **Resolution (§43/§44):** all six policies unchanged and green —
  ERROR_ON_AMBIGUITY never picks latest; ALL returns A→B→A undeduped;
  FIRST/LATEST explicit-only; EXACT strict; provider-canonical uniqueness.
- **Revision sequence (§45):** rev1 STABLE; new-acquisition identical bytes
  → IDENTICAL_REFETCH; new bytes → SOURCE_MUTATION; A→B→A → 1/2/3;
  same-time differing bytes → `RevisionTemporalAmbiguity`; out-of-order →
  `RevisionObservationOrderConflict`.
- **Forensic (§46):** `usable_provenance` flows through the single I04R2
  predicate; forensic observations remain usable_provenance=false and are
  never promoted by canonical-model cleanup.
- **T0B non-invalidation (§47):** I06D proof stays green — rev2 does not
  rewrite rev1 T0A/acquisition/T0B/lineage/manifest.
- **Concurrency (§48):** per-source lock unchanged; concurrent different-byte
  mutations serialize (no fork); stale locks never auto-deleted.

## 13. Test Counts / Gates

- Fresh baseline: storage 939 passed / 0 failed / 3 skipped; full 2318 / 0
  failed / 4 skipped.
- Final: **storage 960 passed / 0 failed / 3 skipped; full 2339 passed /
  0 failed / 4 skipped** (≥ baseline; +21 I06R1 tests, 0 failures).
- ruff: clean on changed scope (storage package + all six I06 test files).
- mypy: `revisions.py` clean (only the pre-existing baseline error in
  `probes/planner.py:79`, present before this checkpoint).
- network = 0; provider source unchanged (no provider module touched);
- historical I06 evidence untouched (git history has zero modifications to
  the four frozen I06 evidence artifacts after `295a8af5`); I06R1 evidence
  is superseding and read-only under the I05R4 policy.
- Frozen `enums.py`/`models.py` byte-identical (git diff empty) — canonical
  vocabulary was reconciled by IMPORT, never by editing the frozen files.

## 14. Machine Evidence (§51)

Published once explicitly, then read-only compared by pytest:

- `BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json` —
  canonical_revision_state_singleton, canonical_revision_policy_singleton,
  canonical_source_revision_model, identity_version_2_rejected,
  birth_same_process_idempotent, birth_restart_idempotent.
- `BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json` — descriptor_key_valid,
  coordinated_descriptor_key_tamper, observation_wrong_source_same_blob,
  duplicate_birth_acquisition, durable_acquisition_request_mismatch.
- `BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json` —
  empty_revision_evidence_ref, empty_canonical_evidence_ref,
  naive_declared_at, cross_source_revision_ids, cross_source_canonical_ids,
  provider_declared_complete, crash_before_declaration,
  crash_after_declaration_before_segment, provider_declared_retry,
  missing_declaration_restart, same_bytes_declaration_no_new_segment.

All deterministic (fixed T1 clock; two-generation byte-identical verified
before publication).  Test layer generates to memory/tmp_path and compares
against committed bytes; normal pytest never writes the evidence tree.

## 15. Ledger (§56)

If operator accepts:

- `PASS_SENSOR_B4_I06R1_CANONICAL_CONTRACT_DECLARATION_SEALED` (proposed)
- then `PASS_SENSOR_B4_I06_SOURCE_REVISION_MUTATION_REGISTRY`
- then `G4-04_REVISION_GATE = IMPLEMENTATION_PASS`

Flags: `SOURCE_REVISION_REGISTRY_IMPLEMENTED=TRUE`,
`SOURCE_MUTATION_EXPLICIT=TRUE`, `REVISION_RESOLUTION_READY=TRUE`,
`REVISION_CANONICAL_CONTRACT_SEALED=TRUE`,
`PROVIDER_DECLARATION_DURABILITY_SEALED=TRUE`;
`DURABLE_RESUME_IMPLEMENTED=FALSE`, `RECOVERY_SCANNER_IMPLEMENTED=FALSE`,
`next_checkpoint_authorized=FALSE`; recommended next =
**SENSOR-B4-I07 DURABLE JOB STATE + RESUME COUPLING** (NOT started).

## 16. STOP GATE (§58)

I07 NOT started.  No job-state/resume implementation, no recovery scanner,
no DuckDB/Postgres, no RawEvidenceQuery, no Bloc-3 integration, no
backfill/recorder, research NOT resumed.  Evidence returned to operator.
