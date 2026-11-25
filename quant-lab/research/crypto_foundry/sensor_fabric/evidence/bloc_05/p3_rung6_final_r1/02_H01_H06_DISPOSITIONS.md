# 02 - H01-H06 dispositions

Each item states the defect, the repair, the executed evidence that closes it,
and what this mission deliberately did not do. All counts are measured, not
targets.

## H01 - diagnostic confidentiality: CLOSED

Defect: an unexpected exception escaping a dependency could carry arbitrary
text (driver messages, DSNs, paths) into a public verdict.

Repair: `_withheld()` contributes only the exception class for unexpected
failures; authored refusal codes and field names are still published because
they are repo-authored; `KeyboardInterrupt` and `SystemExit` propagate.

Evidence: `test_b5_p3_consumer_security.py` (39 tests) drives raises from the
record source, custody gate and replay provider, asserts the sentinel never
appears in the published verdict, and asserts that `KeyboardInterrupt` and
`SystemExit` still propagate. The full repository secret scan (17/17
`test_i15_hardening`) is green with the sentinel in tree - the sentinel was
re-shaped precisely so that scanner stays meaningful.

Residual: authoring a *new* refusal code that embeds data is still possible;
that is a review obligation, not a runtime hole.

## H02 - replay-evidence binding: REPAIRED, ONE AXIS NAMED UNRESOLVED

Defect: offered replay evidence was not bound to the record, provider, kind or
cutoff it claimed to justify.

Repair: binding failures are mapped by nature - cutoff and revision-time
violations to `PIT_INADMISSIBLE`, wrong-row and malformed evidence to
`REPLAY_BLOCKED` - and the unbound state is explicit
(`replay_status = "NOT_BOUND"`), never an implicit pass.

Evidence: `test_b5_p3_consumer_rebinding.py` (25 tests) covers record swap,
provider swap, kind swap, cutoff shift, malformed rows and the fail-closed
default, each asserting the exact code.

Residual (disclosed, not hidden): the frozen replay schema cannot express
provider, kind and artifact identity together, so those three axes are named
`UNRESOLVED_REPLAY_BINDING` under `REPLAY_EVIDENCE_RECORD_BINDING_V1`. The
contract that would bind them is not implemented in this mission. This is the
one place where "fail closed" and "fully bound" differ, and it is reported as
such in 05 and in the machine-readable record.

## H03 - trusted authority composition: CLOSED

Defect: an `AUTHORIZED` custody derivation could be composed against an empty
approval manifest, i.e. authorization without an approving artifact.

Repair: `identity_sha256` is required when `basis is AUTHORIZED`; the policy
recomputes `custody_authority_identity_digest(identity)` and refuses any
`AUTHORIZED` artifact whose `artifact_id` is absent from the pinned manifest.

Evidence: `test_b5_p3_consumer_custody.py` (33 tests) includes the empty
manifest, a manifest with a different artifact id, a tampered identity digest
and the positive control. The pinned manifest in tree still has
`artifacts = {}` and `revoked_approval_ids = []` under
`B5_I09P2A_EMPTY_TRUST_ROOT_V1`, so the empty-manifest path is exercised
against the real pinned root, not a fixture.

## H04 - complete fail-closed boundary: CLOSED

Defect: `evaluate` had reachable non-`ConsumerRequest` inputs that raised
instead of refusing.

Repair: `evaluate` is a thin guard around `_evaluate`; defensive `_bounded`
and `_identifiers` builders and constructor type checks make only programmer
errors raise. Every request-shaped hazard becomes a typed verdict.

Evidence: `test_b5_p3_consumer_policy.py` (28 tests) incl. `None`, wrong types,
structured sequences, oversized identifiers and mutation controls that remove
one guard at a time and show the forbidden verdict becomes reachable.

## H05 - evidence snapshot custody: CLOSED

Defect: an evidence file could change between the read used to decide and the
read used to record, so the verdict could cite a snapshot that was never
adjudicated.

Repair/evidence: two-read custody - the adjudicated bytes and the recorded
bytes are compared, and a mismatch is a typed refusal.
`test_b5_p3_consumer_contracts.py` (36 tests) covers the stable case, the
changed-between-reads case and the disappearing-file case.

## H06 - governance reconciliation of the I08 amendment (G16): CONFIRMED PROSPECTIVE

Question: is the I08 scope-admission amendment discovered in R5 a prospective
amendment or a retroactive loosening of a seal?

Measured answer, mechanically: the R5 change to
`test_b5_i08_scope_audit.py` is **+15 / -3**. The only predicate change adds
`/consumer/` to one live admission assertion; the added lines are a disclosure
comment naming the directive and stating that every previously admitted path is
still admitted and that `identity/`, `terms/`, `time/` and the top-level
modules are still refused by name. No sealed historical evidence, record or
artifact is touched, and the package's exact file set is constrained separately
by I05/I10 `P3_MASTER_EXACT_PATHS`, so the amendment does not become a
directory-wide permission slip.

Disposition: prospective amendment, disclosed as G16, admitted by name - not a
retroactive seal change. Historical trust is preserved: no prior approval,
manifest entry or evidence hash was rewritten to make the new tree pass. The
same pattern was then required again for the I06 audit in this mission (G17,
see 04), which is why G17 is recorded as a pre-existing governance red rather
than a new one.

## Mission boundary (unchanged)

Not done, by directive: no production merge, no provider approval, no
custody-source authorization, no manifest activation, no trust promotion, no
gate or Bloc 6 advancement, no self-ratification.
`OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` remains unresolved and
unimplemented.
