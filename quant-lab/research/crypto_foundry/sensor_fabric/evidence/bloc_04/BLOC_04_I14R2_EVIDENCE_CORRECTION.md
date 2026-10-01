# SENSOR-B4-I14R2 — EVIDENCE CORRECTION (append-only)

Mandate: SENSOR-B4-I14R2 (§22/§23).  The four I14R1 matrices and the
I14R1 correction document are NOT modified.  This document records the
two operator-review blockers and their closure.

## Blocker A — historical evidence mutation (§1A/§2/§3/§4)

Reproduced exactly: between `706f18ed2` (accepted I14 head) and
`4111205e` (I14R1 head), `BLOC_04_I14_T0B_HANDOFF_MATRIX.json` changed
one line — `source_acquisitions` `fp-job::b4d13a6a…` became
`fp-job::20260115T010000000000Z::b4d13a6a…`.  Cause: the live I14
evidence generator republished historical matrices on every pytest run,
so the I14R1 acquisition-id law re-measured the fossil in place.

Closure:
- the fossil is RESTORED byte-exact to the accepted I14 checkpoint blob
  (`git show 706f18ed2:…T0B_HANDOFF_MATRIX.json`, sha256
  `9dc20f64cb4a0741b3a58526666167f0f797e56545dbb58ec426638f448d8c36`);
- `test_i14_evidence.py` is converted to CHECKPOINT-SCOPED IMMUTABILITY
  VALIDATION: all six I14 matrices remain live-measured in memory, but
  nothing is written by an ordinary pytest run; `_write` is gated behind
  `UPDATE_I14_EVIDENCE=1` with a typed refusal; a custody test proves
  all six files byte-equal the accepted checkpoint blobs and that a live
  measurement pass mutates none of them;
- DUAL TRUTH (§4): the I14 fossil keeps the I14-era acquisition
  identity; the observation-aware identity (`fp::observed_at::sha`) is
  current-runtime truth recorded in I14R1/R2 evidence only.  Neither
  era's evidence is rewritten to look like the other.

Generalized law (§7): once a checkpoint advances, its published evidence
files are immutable; later code changes publish new correction /
current-runtime evidence at the later checkpoint — never republish prior
checkpoint matrices.  Generator-custody audit (§29): I13 is already
custody-frozen (publication only via `__main__` +
`UPDATE_I13_EVIDENCE=1`); I05 writes outside the evidence tree; I14 was
the only live historical writer.  No systemic cross-checkpoint overwrite
problem exists; no STOP required.

## Blocker B — I06 group authority trusted its caller (§8-§21)

`register_acquisition_group` derived identity and time from
`acquisitions[0]` on the caller's word.  Closure (all measured in
BLOC_04_I14R2_GROUP_AUTHORITY_MATRIX.json via DIRECT I06 calls, §20):

- identity self-validation (§8/§10): every member's
  `RevisionSourceIdentityV1` descriptor + source_revision_key must equal
  the canonical first-member identity — compared through the model's own
  descriptor, no hand-duplicated field list; foreign-source members are
  typed-refused with zero persistence;
- observation-time coherence (§9): every member's canonical
  `response_observed_at` must equal the group instant — no
  min/max/first/last collapse;
- member uniqueness (§11): duplicate acquisition ids rejected before any
  resolution;
- exact persisted membership on replay (§12/§13): supplied id set AND
  resolved blob set must equal the persisted sets — subset, superset and
  same-blobs/different-acquisitions replays are typed conflicts;
- canonical correspondence (§14/§15): R1 stored member ids in caller
  order and blobs sorted independently — positional mapping was lost.
  Group rows now persist `member_bindings` canonical
  acquisition↔blob PAIRS sorted by blob sha; R1-shaped rows are
  reconstructed at load by resolving each member (never an ambiguous
  zip); existing fields retained (no I14R1 rewrite);
- restart every-member validation (§16/§17/§18): every persisted GROUP
  row re-proves — each member exists, physically verifies, matches
  group identity and instant, maps into the blob set exactly once; the
  domain-separated digest is recomputed from actual member blobs; group
  segments require a complete binding observation.

I14 remains a pre-validating CLIENT (§21); I06 repeats the authoritative
checks — no trust inversion.

## New measured evidence (append-only)

- `BLOC_04_I14R2_HISTORICAL_EVIDENCE_IMMUTABILITY_MATRIX.json` (§24) — 3 rows OK
- `BLOC_04_I14R2_GROUP_AUTHORITY_MATRIX.json` (§25) — 7 rows OK
- `BLOC_04_I14R2_GROUP_MEMBERSHIP_MATRIX.json` (§26) — 5 rows OK
- `BLOC_04_I14R2_RESTART_CORRUPTION_MATRIX.json` (§27) — 6 rows OK

Historical I14 matrices and the four I14R1 matrices: untouched.
