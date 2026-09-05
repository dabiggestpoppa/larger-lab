# SENSOR-B4-I04R1 — ACQUISITION-PROVENANCE + H3-INTEGRITY + POINTER-TRUTH SEAL

Chronology: **I04 original → operator review → I04R1 repair.**  The four
historical I04 evidence artifacts (`BLOC_04_I04_ACQUISITION_MANIFEST_EVIDENCE.md`,
`BLOC_04_I04_CATALOG_SCHEMAS.json`, `BLOC_04_I04_MANIFEST_CONCURRENCY.json`,
`BLOC_04_I04_AUTHORIZATION.md`) are historical checkpoint evidence and are
NOT rewritten.  This file supersedes the affected claims with the corrected
implementation and new proof, in the operator's original-claim → finding →
correction → proof form.

## Checkpoint facts

- Starting SHA (exact): `f95ceaa58aa1e0d02135dd050a15e00bc37ace95` (SENSOR-B4-I04E), clean tree, required I04 lineage verified.
- Commits (per preferred sequence §55, no squash):
  1. `efde5fea` SENSOR-B4-I04R1A — require matching acquisition provenance before manifest publication
  2. `df0d28ca` SENSOR-B4-I04R1B — earn H3/provider-integrity claims from exact source bytes
  3. `0a112ccf` SENSOR-B4-I04R1C — seal blobless outcomes and non-secret acquisition metadata
  4. `cdef2ab3` SENSOR-B4-I04R1D — close current-pointer schema and partition binding
  5. (this commit) SENSOR-B4-I04R1E — freeze provenance/integrity evidence and ledger
- Ending SHA: see ledger / `git log` (SENSOR-B4-I04R1E)
- Operator hold verdict: `HOLD_PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY_PENDING_I04R1_PROVENANCE_INTEGRITY_SEAL` — four truth-seam classes (A provenance, B H3, C blobless/secrets, D pointer) closed by this microseal.

## Defect A — manifest-without-acquisition

- **Original I04 behavior:** a PartitionManifest could reference a verified
  blob (physical + blob metadata) with ZERO durable AcquisitionRecord — the
  frozen ordering (blob durability → EvidenceBlob metadata → AcquisitionRecord
  → PartitionManifest) was not enforced at manifest publication.
- **Final matching-acquisition rule (I04R1 §5/§6):** every non-empty manifest
  `blob_ref` requires at least one durable acquisition with
  `blob_sha256 == ref` AND matching `provider_id`/`venue`/`sensor_family`/
  `native_instrument` (plus `native_granularity` where BOTH sides are known).
  Requested-time equality is deliberately NOT required (requested time !=
  logical/event time).  Byte identity NEVER transfers provider identity and
  NEVER manufactures sensor-family attribution.  Zero-blob manifests remain
  valid with UNVERIFIED integrity.  Missing provenance raises typed
  `MissingAcquisitionProvenance`.  The repository dependency is explicit:
  `PartitionManifestRepository` receives an `AcquisitionRepository` (wired by
  `LocalEvidenceCatalog`); no hidden global state.
- **Adversarial proofs (all typed tests):** blob+metadata with no acquisition
  → FAIL; wrong provider → FAIL; wrong venue → FAIL; wrong sensor → FAIL;
  wrong native instrument → FAIL; granularity conflict when both known → FAIL;
  multiple acquisitions with one matching → PASS; zero-blob NOT_ATTEMPTED
  manifest → PASS.
- **Implementation:** `find_matching_acquisitions`/`has_matching_acquisition`/
  `list_acquisitions_for_blob` (narrow provenance reads — NOT RawEvidenceQuery;
  I12 owns that).  Correctness-first local v1: matching scans immutable
  acquisition fragments; I10 DuckDB / I11 Postgres later provide indexed
  discovery (I04R1 §48).

## Defect B — H3/provider-integrity trust

- **Original H3 defect:** `provider_checksum_algorithm=MD5`,
  `provider_checksum_value=all-zero`, `provider_checksum_verified=True` could
  be persisted against unrelated source bytes — a caller boolean was treated
  as verification evidence.
- **Final H3 recomputation behavior (I04R1 §14-§19):** before acquisition
  publication the repository recomputes the EXPLICIT algorithm (SHA256 /
  MD5 / CRC32 — never inferred from digest length, unknown algorithms fail
  typed) over the EXACT decoded T0A source bytes (`open_blob`).  Then:
  `verified=True` requires observed match; `verified=False` requires observed
  mismatch; a mismatched claim → `ProviderChecksumClaimConflict`; a persisted
  mismatch is retained ONLY as explicit failure evidence (`verified=False` +
  `failure_ref`/explicit failure); `verified=None` means NOT YET CLAIMED
  VERIFIED; `verified=True` with no blob → rejected (no bytes to prove
  against).  Results: real MD5 → accepted; fake MD5 verified=True → rejected;
  real SHA256 → accepted; real CRC32 → accepted; verified=False on matching
  bytes → claim conflict; algorithm never inferred.
- **EvidenceBlob provider-integrity policy (I04R1 §20/§21):**
  `BlobMetadataRepository` may append initial physical metadata at UNVERIFIED
  or LOCAL_HASH_VERIFIED only; caller-set PROVIDER_HASH_VERIFIED →
  `UnearnedProviderIntegrityClaim`.  Provider proof lives in the durable
  AcquisitionRecord (algorithm/value/verified=True AFTER repository
  recomputation); old metadata is never mutated to upgrade its enum.
- **Manifest provider-integrity rule (I04R1 §22-§24):** a manifest claiming
  PROVIDER_HASH_VERIFIED requires on EVERY blob_ref: local physical
  verification + durable metadata + durable matching acquisition provenance +
  a matching acquisition carrying earned (recomputed) H3 verified=True
  (`has_earned_h3_proof`) — else `UnearnedProviderIntegrityClaim`.  A LOCAL
  claim requires physical + metadata + provenance but NOT H3.  UNVERIFIED
  preserves truthful coverage but never drops provenance.

## Defect C — blobless outcomes and secrets

- **Original blobless heuristic:** `status is not None and not
  status.startswith("2")` — too weak: "OK", "SUCCESS", "CURRENT_ONLY" were
  treated as failure evidence.
- **Final blobless rule (I04R1 §25-§27):** `blob_sha256 is None` requires
  `failure_ref` OR an explicitly PARSED numeric HTTP failure code (>= 400) —
  no string-prefix guessing; failure_ref remains preferred.
- **Secret-bearing metadata guard (I04R1 §28-§32):** a narrow repository
  boundary refuses, before persistence: endpoint_host containing userinfo/
  query/fragment/path material or Authorization-like keys; endpoint_path
  containing query/fragment/userinfo or secret keys; request_family carrying
  secret keys; source_locator with URL userinfo or secret-bearing query keys
  (frozen vocabulary: authorization, proxy-authorization, cookie, set-cookie,
  x-api-key, api-key, apikey, access-token, token, bearer, secret,
  client-secret, password, signature, sig — `access_token`/`access-token`
  normalized; `sig` word-bounded so it cannot match inside `signature`).
  REJECT, never silently redact; error text names the KEY, never the VALUE.
  Public non-secret query parameters are preserved.  This is the narrow
  I04R1 boundary, NOT the full I15 scanner.

## Defect D — closed pointer schema

- **Original pointer parser:** `str()`/`int()` coercion, extra JSON fields
  silently ignored, no schema version, no partition binding on read.
- **Final closed pointer schema (I04R1 §34-§37):** `schema_version=1`
  (integer, not bool/string; unknown versions corrupt); partition_key /
  partition_manifest_id nonempty strings (numeric values rejected, never
  coerced); manifest_version integer >= 1 (bool/str/float rejected);
  previous_manifest_id null or nonempty string; updated_at timezone-aware
  ISO-8601; ANY unknown field → `CurrentPointerCorrupt`; missing required
  field → `CurrentPointerCorrupt`.
- **Partition-key binding (I04R1 §38/§40):** `read_current_pointer(key)` fails
  `CurrentPointerCorrupt` when the pointer's exact logical partition_key does
  not equal the requested key — the physical locator hash is never
  authoritative.
- **Previous-manifest binding (I04R1 §39):** pointer validation proves
  `pointer.previous_manifest_id == manifest.supersedes_manifest_id` on every
  read; inconsistent ancestry is corrupt, not merely retry-relevant.
- **Regressions:** P1-P5 crash matrix green; old-or-new pointer visibility
  green; 8-writer CAS green; immutable Parquet behavior unchanged.

## Machine evidence (deterministic, byte-stable across regeneration)

- `BLOC_04_I04R1_PROVENANCE_MATRIX.json` — cases: no_acquisition,
  matching_acquisition, wrong_provider, wrong_sensor, wrong_instrument,
  multiple_one_matching, h3_valid, h3_false_claim, h3_missing_proof,
  provider_integrity_manifest; fields: manifest_allowed,
  matching_acquisition_count, local_integrity_proven, provider_integrity_proven,
  expected_error, test_name.  No wall-clock nondeterminism (injected fixed
  clocks; scheduling-independent fields only).
- `BLOC_04_I04R1_POINTER_SCHEMA.json` — closed field contract
  (schema_version=1, field/type/constraint) + 17 adversarial parse cases
  (valid + 16 typed-rejection cases, each expected_outcome verified).

## Verification

- Storage suite: 536 collected / 534 passed / 2 platform skips (490 → 536,
  +46 I04R1 tests).
- Full suite: **1913 passed / 0 failed / 3 skipped** (1916 collected; floor
  >= 1867).  (One pre-existing blob_store adversarial thread-race test flakes
  only under full-suite load and passes in isolation; it is untouched by
  I04R1.)
- ruff: clean on the changed scope (src + tests).
- mypy: clean on the changed scope — only the pre-existing
  `probes/planner.py:79` baseline and yaml-stub noise in untouched files.
- Network calls: 0.  Provider code: unchanged (no provider integration, no
  provider network).
- No T0B, no SourceRevision registry, no SOURCE_MUTATION, no active resume
  advancement, no DuckDB, no PostgreSQL, no recovery scanner, no backfill,
  no live recorder.  Historical I04 evidence untouched.
- **I05 (Raw Projection + Lineage) NOT started.**

## Verdicts

- Proposed: `PASS_SENSOR_B4_I04R1_PROVENANCE_INTEGRITY_SEALED`
- Then proposed operator acceptance: `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`
- Recommended next (NOT authorized): SENSOR-B4-I05 — RAW PROJECTION + LINEAGE LAYER