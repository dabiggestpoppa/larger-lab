# SENSOR-B4-I12R2R1 — HISTORICAL EVIDENCE IMMUTABILITY REPAIR
## (append-only governance repair narrative)

> Mandate: SENSOR-B4-I12R2R1 · Branch: `agent/crypto-sensor-fabric-build`
> Start HEAD: `cedf923e88ef0958cbf056f752351a350833ee85`
> Accepted I12R1 head (checkpoint anchor): `76042ca4c4abf17884980fca84a7aa1ba2d680c6`
> Research: FROZEN · I13+: UNAUTHORIZED · **NO PRODUCTION CHANGES**

---

## 1. Finding

The I12R2 PRODUCTION repair is accepted as technically correct pending
governance closure.  The defect is EVIDENCE GOVERNANCE ONLY: the I12R2
publication modified
`BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX.json` (regenerating its
superseded fallback row from current production behavior), which violated
the append-only historical-evidence law — the historical I12R1 artifact
must remain the evidence actually published at the I12R1 checkpoint, even
when later production behavior supersedes it.

## 2. Exact restoration (Git object truth, not reconstruction)

The artifact was restored by `git cat-file blob
76042ca4c4abf17884980fca84a7aa1ba2d680c6:<path>` — no hand reconstruction.

| State | SHA-256 |
|---|---|
| Before repair (post-I12R2 publication) | `14119b519970d2914baf7d14977d62550e186a11ee42d7d5a695d267ef43e163` |
| Restored (current worktree) | `039580c07b7e6f65a74f892f513dcba7ccdc5f6f5e385e82f13595e6e437a5f3` |
| At accepted I12R1 head `76042ca4c` | `039580c07b7e6f65a74f892f513dcba7ccdc5f6f5e385e82f13595e6e437a5f3` |

Equality of the last two hashes IS the restoration proof.

## 3. Historical vs current semantic distinction (dual truth)

- **HISTORICAL (I12R1 artifact, restored):**
  `schema_mismatch_with_T0A_fallback_documented` = OK —
  both representations requested + schema mismatch → valid T0A returned
  with `projection_refs=[]` (option-A fallback).  This is the behavior
  actually published at I12R1; it is HISTORICAL and SUPERSEDED, not
  current production truth.
- **CURRENT (I12R2, unchanged):**
  `both_requested_schema_mismatch_refused` = OK in
  `BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json`, and live
  production raises `ProjectionSchemaUnsupported` for the same query
  (proven by `test_i12r2r1_evidence_immutability.py`, including the §14
  dual-truth test that passes ONLY if both statements hold
  simultaneously).

Both truths coexist.  The I12R2 runtime, tests and evidence are NOT
reverted; the I12R2 closure narrative received an APPENDED dual-truth
marker section (nothing above it rewritten).

## 4. Verification architecture — before / after

- **BEFORE (defective):** `test_i12r1_evidence.py` regenerated the
  historical representation matrix from CURRENT production and compared it
  byte-for-byte to the published artifact.  Valid only while no later
  checkpoint intentionally changes production semantics; at I12R2 it
  either fails the comparison or pressures a history rewrite (which is
  what happened).
- **AFTER (checkpoint-scoped, I12R2R1 §5):** for THAT ONE matrix only,
  acceptance = immutable checkpoint identity — SHA-256 pin
  `I12R1_REPRESENTATION_EVIDENCE_SHA256` at `I12R1_ACCEPTED_HEAD`
  = `76042ca4c4…`, cross-checked against Git object truth — PLUS the
  structural evidence law (mandate/checkpoint identity, matrix identity,
  10 rows, exactly one synthetic-counterfactual FAIL, historical fallback
  row present with its original measured payload, every row classified and
  measured as originally published).  The other four I12R1 matrices keep
  the regenerate-and-compare law (their semantics remain compatible);
  their publication set excludes the historical matrix so a future builder
  regression cannot silently rewrite it.

## 5. Scope

- Changed: `test_i12r1_evidence.py` (narrow: representation matrix moved
  to checkpoint-scoped verification), restored artifact, this narrative,
  the ledger, and the new governance test
  `test_i12r2r1_evidence_immutability.py` (12 tests).
- **ZERO production source diff from `cedf923e8`** (query.py, replay.py,
  catalog.py, manifests.py, models.py, revisions.py, __init__.py all
  untouched).
- I12R2 technical semantics: UNCHANGED.
