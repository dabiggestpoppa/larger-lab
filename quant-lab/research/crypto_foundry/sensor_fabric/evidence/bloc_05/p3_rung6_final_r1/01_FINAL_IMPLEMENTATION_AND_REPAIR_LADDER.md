# 01 - Final implementation and repair ladder

Everything below is additive on
`agent/crypto-sensor-fabric-p3-production-master-r1`. No audit branch was
merged, nothing was force-pushed, and no history was rewritten; `5ee268b1d` is
an ancestor of the verified candidate.

| # | SHA | Subject | Scope |
| --- | --- | --- | --- |
| 0 | `5ee268b1d872fe4040d2d1505d012f344e7b5d54` | B5-P3-R5: complete executable production consumer security suite | starting point of this mission |
| 1 | `d81cceb28aa79870f6702bed053bfb6d8d80f2c1` | B5-P3-R6: enforce a total fail-closed boundary and rebind replay evidence | H01-H05 and the G17 reconciliation |
| 2 | `868dd3fc91b5a38d02742bd3705da0c1d78b66c3` | B5-P3-R6: keep the leak sentinel out of credential shape | follow-up required by the canonical run itself (see 03) |

## Commit 1 - `d81cceb28`

Purpose: make the production trust consumer total at its boundary instead of
correct only on the paths the R5 suite happened to exercise.

* **H01 - diagnostic confidentiality.** `policy.py` gained `_withheld()`.
  Unexpected exceptions now contribute only their class name to a public
  verdict; authored refusal codes and field names survive because they are
  repo-authored. `KeyboardInterrupt` and `SystemExit` are re-raised unchanged
  and are never absorbed into a verdict.
* **H02 - replay-evidence binding.** `_bind_replay()` now returns
  `(reason, detail)` and binds the offered evidence to record, provider, kind
  and cutoff. Cutoff and revision-time violations map to `PIT_INADMISSIBLE`;
  wrong-row and malformed evidence map to `REPLAY_BLOCKED`; an unbound state is
  `replay_status = "NOT_BOUND"` rather than an implicit pass. The axes the
  frozen schema cannot express (provider, kind, artifact) are named
  `UNRESOLVED_REPLAY_BINDING` under `REPLAY_EVIDENCE_RECORD_BINDING_V1` instead
  of being silently ignored (see 05).
* **H03 - trusted authority composition.** `CustodyAuthorityDerivation`
  gained `identity_sha256`, required whenever `basis is AUTHORIZED`. The policy
  compares it against `custody_authority_identity_digest(identity)` and refuses
  an `AUTHORIZED` artifact whose `artifact_id` is not present in the pinned
  manifest's approvals, which closes the empty-manifest authorization bypass.
* **H04 - complete fail-closed boundary.** `evaluate` is now a thin guard
  around `_evaluate`. Defensive `_bounded` and `_identifiers` builders plus
  constructor type checks make only genuine programmer errors raise (a
  non-`ConsumerRequest` `TypeError`, a bad constructor argument); every
  request-shaped hazard becomes a typed refusal.
* **G17 - consumer admission reconciliation.** The I06 replay-safety audit and
  the I06 producer allowlists never admitted `consumer/`, and their pinned
  hashes predated the R5 tree. Fixed by a disclosed prospective amendment
  (`P3_CONSUMER_EXACT_PATHS`, `P3_DISCLOSED_SHA256`,
  `P3_DISCLOSED_EVIDENCE_SHA256`) plus mechanical republication of the I05, I06
  and I09 artifacts. See 04.

## Commit 2 - `868dd3fc9`

The first complete Worker-level run of the whole repository surfaced a real
defect in the R6 fixtures, not in the product code: the H01 leak sentinel was
written as a DSN with `user:password@`, and the I15 repository secret scan
correctly flags credential-shaped text even inside test fixtures. Four
`test_i15_hardening` tests failed for that reason alone.

The sentinel now names itself (`P3-SENTINEL-VALUE-DO-NOT-RELAY`) and the crash
fixture keeps its message shape without a credential pattern. A leak test does
not need a real-looking secret to prove that a message is withheld. After the
change the I15 hardening suite is 17/17 and the consumer suite is still
161/161.

## Files touched by this mission

Product code (2): `normalization/consumer/policy.py`,
`normalization/consumer/custody_authority.py`.

Tests (7): `test_b5_p3_consumer_{policy,rebinding,security,custody}.py` (new
H01-H05 tests and binding doubles), `test_b5_i05_scope_audit.py`,
`test_b5_i10_scope_audit.py` (I06 test path admitted by name),
`test_b5_i06_replay_safety.py` (`P3_CONSUMER_EXACT_PATHS`,
`P3_TIME_VALIDATION_SHA256`).

Producer (1): `scripts/b5_i06_replay_safety.py` (disclosed source and evidence
pins).

Evidence (4): `bloc_05_time_validation.json`,
`bloc_05_semantic_validation.json`, `bloc_05_replay_safety_validation.json`,
`BLOC_05_I06_SCOPE_AUDIT.json` - republished mechanically by their own
producers, not hand-edited.
