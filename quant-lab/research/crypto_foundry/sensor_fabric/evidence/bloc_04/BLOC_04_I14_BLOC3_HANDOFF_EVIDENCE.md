# SENSOR-B4-I14 — BLOC 3 → BLOC 4 DURABLE HANDOFF EVIDENCE

Mandate: SENSOR-B4-I14 / G4-12 BLOC 3 HANDOFF GATE
Branch: `agent/crypto-sensor-fabric-build`
Start HEAD: `a37aad77cb2dd69e5511ea2148e39dfbb49747ed`
Expected remote main: `7c7816f382947bbc8a1f2154435fc436f2428fa8` (verified; untouched)

## 1. Scope discipline

- I14 ONLY. I15+ NOT started. Research FROZEN. No live network anywhere
  (all fixtures synthetic/offline; no socket use in the I14 suites).
- No provider adapter modified. No upstream Bloc 3 contract modified
  (`providers/base/models.py` untouched). No Bloc 4 repository semantics
  changed — I14 is COMPOSITION ONLY.
- The 7 known CRLF-only I03R1/I04 evidence files were never staged.

## 2. Integration module / API (§5/§45)

Production module: `quant-lab/src/crypto_sensor_fabric/storage/integration.py`

- `Bloc3StorageContext` (§43): REQUIRED `venue` (no hidden default, §44 —
  typed refusal at construction), optional `source_granularity`
  (accepted `Granularity`), optional `endpoint_host`/`endpoint_path`/
  `request_family`. Carries EXISTING upstream identity FetchBatch
  deliberately does not hold.
- `Bloc3StorageHandoff.persist_batch(*, job_id, batch, context,
  projection_ids=None) -> BatchPersistenceReceipt`.
- `BatchPersistenceReceipt` (§45/§46): job_id, acquisition_ids,
  blob_shas, revision_keys, projection_ids, manifest_id/version,
  checkpoint_advanced, resume_token, complete. Summary only — every
  field re-readable from the accepted durable repositories.
- Typed errors: `BatchIdentityMismatch`, `EnvelopeIdentityMismatch`,
  `EnvelopeContentHashMismatch`, `DuplicateEnvelopeContent`,
  `BatchAlreadyCompleted`, `FaultSimulated` (test hook only).
- FAULT_WINDOWS W1..W7; the hook is the instance attribute
  `fault_windows` — never a production parameter.

## 3. Input mapping audit (§41/§42/§60)

Contract gap found: NONE. `venue` and `source_granularity` were the
flagged risks; both are supplied by `Bloc3StorageContext` from accepted
upstream truth (§43). No provider-specific inference anywhere.

- 20-row mapping matrix: `BLOC_04_I14_INPUT_MAPPING_MATRIX.json`
  (20 OK / 0 FAIL / 0 counterfactuals). Every crossing field cites its
  authority. Explicit non-mapping recorded: `row_count`,
  `provider_cursor`, `duplicate_annotations`, `rate_limit_snapshot`
  (no accepted storage target; not silently collapsed, §12).

## 4. T0A byte mapping (§8/§11)

bytes → exact bytes; str → UTF-8 encoding per the accepted Bloc 3
`payload_hash` law. NO JSON reparse, NO newline/whitespace/Unicode
normalization, NO sorted-key serialization. SHA-256 recomputed over the
exact body; a lying provider `content_hash` is `EnvelopeContentHashMismatch`
BEFORE any mutation. `RawPayloadEnvelope` objects are never mutated.

## 5. Multi-envelope / EMPTY_VALID behavior (§9/§10)

- Multi-envelope: N envelopes → N durable T0A blobs, N AcquisitionRecords,
  ALL blob refs in the manifest (atomic causality, §36: manifest commits
  only with ALL payloads durable). Revision law: ONE batch is ONE source
  observation — the revision registers through the accepted I06 public
  path from the batch's FIRST acquisition anchor (registering each
  envelope as a separate observation at the same observation instant
  would trip the accepted I06 §40 source-order law, which the handoff
  never circumvents). All N envelopes remain fully durable evidence.
- EMPTY_VALID (0 envelopes + EMPTY_VALID flag): NOTHING fabricated —
  no empty blob, no fake T0A. Durable truth = manifest with zero
  blob_refs, coverage `EMPTY_CONFIRMED`, integrity `UNVERIFIED` (I04 §46
  vacuous-claim rule). No acquisition exists to anchor a manifest-floor
  checkpoint, so the cursor truthfully stays put (explicit no-resume
  state, §24); no token invented, no false progress.

## 6. Sequences (§25)

Successful partial batch:

    PLANNED → ACQUIRING → RAW_STAGED → RAW_COMMITTED → PROJECTION_PENDING
    → PROJECTION_COMMITTED → MANIFEST_COMMITTED → CHECKPOINT_ADVANCED
    (via advance_checkpoint, the accepted I07 gate, MANIFEST_COMMITTED floor)

Partial batch ends CHECKPOINT_ADVANCED with the adapter's exact
`next_resume_token` (§22/§24). Complete batch continues
CHECKPOINT_ADVANCED → COMPLETE exactly once (§23/§50); the gate is never
skipped. Duplicate/restart after COMPLETE adopts frozen history; a
divergent batch is `BatchAlreadyCompleted` (§35).

## 7. Partition / manifest identity (§19/§20/§40)

Partition key: accepted I04 identity shape
`provider/venue/sensor/instrument/requested_start.date()` composed from
batch + context fields (no ad-hoc inference). Versioned CAS: next
version = current+1, `supersedes_manifest_id` = current id, explicit
`expected_current`; no auto-rebase. W6/W7 retry adoption: if the current
pointer already references the EXACT intended manifest (identity fields,
blob refs, projection refs, coverage, integrity, logical window), it is
re-read and adopted — no duplicate semantic version.

## 8. Checkpoint floor (§21) and ordering (§51/§66/§67)

The I14 composition wires `DurableJobStateRepository` at
`min_durable_status=MANIFEST_COMMITTED`. The repository was NOT weakened.
Structural ordering proof: the manifest is durable and re-reads
successfully BEFORE `advance_checkpoint` runs; the inversion
counterfactual (checkpoint attempt from RAW state, no manifest) is
REFUSED with `JobResumeGateError` — measured in the IDEMPOTENCE matrix.

## 9. Crash matrix W1-W7 (§27/§28/§47/§48/§53/§62)

`BLOC_04_I14_CRASH_RESTART_MATRIX.json`: 8 rows (W1-W7 + W7-specific),
8 OK / 0 FAIL. For EVERY window: fault raised, fresh repositories
reconstructed from disk, `resume_after == resume_before`, final durable
semantic digest == clean-run digest, retry manifest id == clean-run
manifest id.

Survivors observed (§53 law respected — no deletion to mimic rollback):
W1: nothing new. W2: T0A blob (content-addressed dedupe absorbs the
retry, §30). W3: blob+acquisition (append_acquisition idempotence, §31).
W4/W5: +revision (I06 idempotent re-register, §32). W6: committed
manifest, checkpoint old. W7: fully durable manifest, checkpoint old —
retry adopts via manifest idempotent-completion law and advances
EXACTLY once (§29); W7-specific row proves 1 checkpoint transition and
exactly 1 durable copy of the intended manifest across both runs.

## 10. Duplicate / divergent / two-job behavior (§34/§35/§49/§56)

- Identical redelivery: adoption receipt (`checkpoint_advanced=False`),
  no durable mutation, digest stable. Checkpoint transitions stay at 1.
- Divergent retry after a consumed checkpoint: typed
  `BatchAlreadyCompleted` refusal; the accepted continuation path for a
  genuine NEXT batch is the annotated CHECKPOINT_ADVANCED→ACQUIRING
  transition (measured in the revision-progression test).
- Same bytes, two jobs: blob dedupe shares content; acquisitions and
  checkpoint anchors stay identity-bound per job. Same blob SHA never
  transfers checkpoint authority.
- Same request / different bytes: two explicit revisions, both T0A
  blobs preserved, explicit manifest supersession (v2 supersedes v1).

## 11. T0B handoff (§17/§18/§57/§64)

T0A-only path remains fully valid. T0A+T0B fixture commits a REAL T0B
projection through the accepted I05 `T0BProjectionService` over the
handoff's own durable T0A evidence, then binds `projection_refs` into
the manifest through the accepted I04 CAS with a wired
`ProjectionLineageResolver` — commit accepted, lineage resolves over the
exact T0A blobs. Broken-lineage counterfactual: dangling projection ref
→ manifest commit FAILS CLOSED (accepted I04/I05 law), checkpoint stays
old. T0B failure law (§18): T0A stays durable; no checkpoint advance
without manifest.

## 12. Concurrency (§55/§56/§65)

Same job double-persist: exactly ONE checkpoint transition, no manifest
version fork, stable final state (job lock + frozen graph +
committed-checkpoint retry law). Stale-writer counterfactual: an intent
computed two versions behind the current pointer is refused by the
accepted manifest CAS (`ManifestCASConflict`) — no last-writer-wins.

## 13. Evidence matrices (§59)

| Matrix | Rows | OK | FAIL | Synthetic counterfactuals |
|---|---|---|---|---|
| INPUT_MAPPING | 20 | 20 | 0 | 0 |
| DURABILITY_ORDER | 8 | 8 | 0 | 0 |
| CRASH_RESTART | 8 | 8 | 0 | 0 |
| IDEMPOTENCE | 13 | 13 | 0 | 1 |
| T0B_HANDOFF | 3 | 3 | 0 | 1 |
| CONCURRENCY | 2 | 2 | 0 | 1 |

Every PASS row derives from measured production behavior
(`test_i14_evidence.py`); one explicit counterfactual per matrix where
present, per §59.

## 14. No-network proof (§38) & secret scan (§39)

I14 suites (`test_i14_handoff.py`, `test_i14_evidence.py`) use only
synthetic offline FetchBatch/RawPayloadEnvelope fixtures; no socket
import, no provider call. Secret scan over the new module, fixtures and
published evidence: no API key/secret/password/authorization/cookie
material. Retrieval metadata passes the accepted I04R1 secret firewall
at append — never bypassed. `RawPayloadEnvelope.retrieval_metadata` is
not persisted into acquisition retrieval fields by the mapping.

## 15. Statics

- Ruff (changed scope): clean — `integration.py`,
  `test_i14_handoff.py`, `test_i14_evidence.py`.
- compileall: clean.
- mypy (changed production scope): 0 findings in `integration.py`
  (10 pre-existing unrelated findings in `providers/gate|deribit/probe.py`
  via followed imports — not I14 scope, no new findings).

## 16. G4-12 verdict

ALL of the following are proven together (§76): Bloc 3 typed input +
exact evidence persistence + acquisition provenance + revision handling
+ manifest durability + checkpoint-after-manifest ordering + restart
safety + idempotent retry + no cursor skip.

    PASS_SENSOR_B4_I14_BLOC3_INTEGRATION_SEALED
      = PENDING_OPERATOR_REVIEW
    G4-12_BLOC3_HANDOFF_GATE
      = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
    next_checkpoint_authorized = FALSE
    recommended_next = OPERATOR REVIEW OF SENSOR-B4-I14 / G4-12
    I15+ = UNAUTHORIZED; research = FROZEN

Do NOT self-ratify. Historical evidence untouched (§77). I08 recovery
remains owner of orphan reconciliation (§54) — W6 orphan-fragment
survivors were left in place per law.
