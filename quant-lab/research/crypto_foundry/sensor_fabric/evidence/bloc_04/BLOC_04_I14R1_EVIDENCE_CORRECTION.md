# SENSOR-B4-I14R1 — EVIDENCE CORRECTION (append-only)

Mandate: SENSOR-B4-I14R1 (I14R1 §27). Historical I14 matrices are NOT
modified. This document corrects the RECORD of what the I14 evidence
proved, and binds the four new measured I14R1 matrices.

## What I14's matrices actually proved (and did not)

The six committed I14 matrices (BLOC_04_I14_*) were measured over
single-page flows: one `persist_batch` per durable job, plus W1–W7
restarts of that same single batch. They proved:

- exact T0A byte mapping, batch/envelope identity, content-hash
  recomputation;
- versioned manifest CAS, idempotent adoption, W7 single-advance on the
  raw path;
- source-bound MANIFEST_COMMITTED checkpoint at the V1 proof law.

They DID NOT prove — and the operator review correctly flagged — three
behaviors outside that flow:

1. **Blocker A (continuation).** After `CHECKPOINT_ADVANCED`, a genuine
   NEXT paginated batch raised `BatchAlreadyCompleted`. The I14 evidence
   matrix row "revision progression" passed only because the test itself
   drove `jobs_repo.advance_status(...ACQUIRING...)` by hand — external
   manipulation of the I07 state machine that G4-12 forbids the caller
   from needing. Measured repro: `BatchAlreadyCompleted` on page 2 with
   zero external calls.
2. **Blocker B (EMPTY_VALID progress).** `_persist_empty_valid` committed
   a durable zero-blob manifest but never called `advance_checkpoint`,
   dropped a valid `next_resume_token`, and could return
   `complete=True` while the durable job stayed `MANIFEST_COMMITTED`.
   Measured repro: token dropped, checkpoint stuck.
3. **Blocker C (multi-envelope revision invisibility).**
   `_register_revisions` registered ONLY `acquisition_ids[0]`; a change
   in a non-first envelope was durable in T0A/manifest without becoming
   revision-visible. Measured repro additionally surfaced an
   `AcquisitionIdentityConflict`: the `fp::sha` acquisition-id scheme
   collided on identical bytes re-observed at a later instant.

## Corrections sealed by I14R1

- **I14R1A — continuation authority.** At `CHECKPOINT_ADVANCED`,
  `Bloc3StorageHandoff` now classifies: EXACT_RETRY (adopt, zero
  mutation), NEXT_BATCH (proven ONLY by accepted upstream context —
  `Bloc3StorageContext.request_resume_token == current.resume_token`;
  the accepted `FetchRequest.resume_token` field; nextness is never
  inferred from bytes/timestamps/row counts/manifest versions/
  provider_cursor), and DIVERGENT_REWRITE (typed fail-closed refusal
  before any mutation). I14 owns the accepted annotated
  `CHECKPOINT_ADVANCED -> ACQUIRING` edge; the public caller never
  drives I07. At COMPLETE: exact final-batch retry adopts read-only;
  any new batch is a typed terminal refusal (`BatchAlreadyCompleted`);
  COMPLETE is never reopened.
- **I14R1B — EMPTY_VALID durable acquisition + checkpoint proof V2.**
  `AcquisitionRecord.blob_sha256` was audited: already nullable — no
  fabrication needed. An EMPTY_VALID page now persists a durable
  blob-less AcquisitionRecord carrying the accepted EMPTY_VALID quality
  flag (additive `_is_empty_valid_acquisition` shape in the I04R1 §26
  blobless gate), a durable EMPTY_CONFIRMED/UNVERIFIED manifest, and
  advances the checkpoint through THE accepted gate with the additive
  V2 proof (`proof_version=2`, `evidence_kind="EMPTY_VALID"`,
  `blob_sha256=None`), valid ONLY at the MANIFEST_COMMITTED floor.
  V1 proofs remain valid under unchanged V1 law; restart replay never
  reinterprets. No bypass, no fake blob, valid tokens preserved,
  `CHECKPOINT_ADVANCED -> COMPLETE` for empty-complete.
- **I14R1C — multi-envelope group revision law.** I06 was audited and
  EXTENDED additively (no contract gap): `SourceRevisionRegistry.
  register_acquisition_group(acquisition_ids, observation_id,
  observation_digest)` reuses the entire existing classification
  machinery with one deterministic observation identity over the
  COMPLETE envelope group. One FetchBatch = one observation = one
  instant (I06 §40 preserved). One acquisition event per batch
  observation instant (`fp::observed_at::sha`) removes the identical-
  bytes collision. Additive `content_scope="GROUP_OBSERVATION"` on
  segments and observations keeps the strict single-blob reload law
  for all historical rows (absent field = legacy SINGLE law).  Manifest
  evidence set == revision observation set.
- **Group digest domain (I14R1 §13).** `group_content_digest(members)`
  = `sha256("sensor-revision-group-v1\\n" + "\\n".join(sorted(unique
  member blob SHAs)))` — canonical SET (Bloc 3 declares no envelope
  ordering semantic; §18F: [X,Y] vs [Y,X] is the SAME observation),
  domain-separated (never ambiguous with a literal blob SHA),
  RECOMPUTED by I06 from the durable member blobs on every
  registration and every restart replay — a forged digest can never
  mint classification truth.
- **Group membership persistence (I14R1 §16/§17).** Group observation
  rows durably persist `member_acquisition_ids` (COMPLETE) and
  `member_blob_sha256` (COMPLETE canonical set). The digest alone is
  NOT lineage: the restart loader refuses any GROUP row (or group
  segment) whose member sets are absent, whose members do not bind to
  the segment birth, or whose member blob set does not recompute to
  the persisted group digest. "Which acquisitions/blobs constituted
  this source revision?" is durably answerable.
- **Checkpoint proof V1/V2 law (I14R1 §15/§16).** V1 remains closed and
  unchanged (5 fields, mandatory 64-hex blob anchor — blobless V1 is
  still corruption). V2 = V1 fields + `evidence_kind`, valid ONLY at
  the MANIFEST_COMMITTED floor, ONLY for `evidence_kind="EMPTY_VALID"`,
  ONLY with `blob_sha256=None`; the gate re-proves the durable empty
  acquisition, empty manifest, coverage/integrity and job identity.
  Restart replay is VERSION-AWARE: each event validates under its OWN
  persisted proof version; mixed V1/V2 chains replay cleanly.
- **Acquisition-id law correction.** I14's `fp::sha` scheme was lossy
  for identical bytes at different instants; sealed law is
  `fp::observed_at::sha` (empty events: `fp::observed_at::EMPTY_VALID`).
  Exact retry of the same observation keeps the same acquisition id;
  the same bytes at a later instant are a different acquisition event
  with the same blob SHA.
- **Re-measured historical row note.** The live I14 evidence module
  re-measures its matrices on every run; the acquisition-id law change
  legitimately re-measured one row of
  `BLOC_04_I14_T0B_HANDOFF_MATRIX.json` (`source_acquisitions` now
  carries the observation-instant id). No historical invariant changed;
  all other I14 matrix files are byte-identical.

## New measured evidence (append-only)

- `BLOC_04_I14R1_CONTINUATION_MATRIX.json` (§28) — 9 rows OK
- `BLOC_04_I14R1_EMPTY_VALID_CHECKPOINT_MATRIX.json` (§29) — 7 rows OK
- `BLOC_04_I14R1_MULTI_ENVELOPE_REVISION_MATRIX.json` (§30) — 6 rows OK
- `BLOC_04_I14R1_RESTART_MATRIX.json` (§18/§28) — 3 rows OK

Every row is PRODUCTION_MEASURED (real durable stacks, real accepted
repositories, synthetic/offline fixtures, zero network). Historical
I03–I14 evidence files: untouched.
