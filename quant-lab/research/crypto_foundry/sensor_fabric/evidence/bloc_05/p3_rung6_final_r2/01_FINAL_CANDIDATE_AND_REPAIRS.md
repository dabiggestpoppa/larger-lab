# 01 - Final candidate, freeze verification and the repairs under it

## Candidate

| Item | Value |
| --- | --- |
| Branch | `agent/crypto-sensor-fabric-p3-production-master-r1` |
| Final repaired candidate | `66200f3cb18ee5cea1483d986e64502f388eeb77` |
| Commit subject | `B5-P3-R6: close selected-revision cutoff and typed-refusal leakage` |
| Parent | `21fd7e473a534c38b237729f9474c46bb94267ee` |
| Local HEAD | `66200f3cb18ee5cea1483d986e64502f388eeb77` |
| Remote `origin` branch head | `66200f3cb18ee5cea1483d986e64502f388eeb77` (equal) |

## Freeze and preflight measurements

| Check | Result |
| --- | --- |
| Exact candidate SHA | matches |
| Local/remote equality | equal (`git ls-remote`) |
| Tracked tree clean | yes (`git status --porcelain` empty on tracked paths; the only untracked path is the historical `p3-r6-final` bundle inside the guarded evidence tree) |
| Files changed by the repair commit | exactly 4: `normalization/consumer/policy.py`, `test_b5_p3_consumer_policy.py`, `test_b5_p3_consumer_rebinding.py`, `test_b5_p3_consumer_security.py` (+691 / -42) |
| Approval manifest byte-identical | yes - same git blob `7be15e8e56c87a4acea533a7b2382c1f5d5ad2f9` at `868dd3fc9` and at `66200f3cb`; SHA-256 `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` |
| `INTEGRATION_STATE` unchanged | `INTEGRATION_REQUIRED`, and the repair diff contains zero occurrences of the symbol |
| Authorized Python inventory | 1,111 tracked `.py` files: 157 under `quant-lab/src/`, 249 under `quant-lab/tests/` |
| Governance bindings | manifest `{}` artifacts, `[]` revoked ids, authority `B5_I09P2A_EMPTY_TRUST_ROOT_V1` |
| Host configuration | 1 worker, numerical thread caps pinned to 1, partition timeout 5,400 s (the known-good configuration; the 4-worker failure mode was not retried) |

## F4 - every selected revision obeys the knowledge cutoff

Defect (reproduced before repair against `868dd3fc9`): `_bind_replay` projected
`selection.selected` to an id-keyed mapping and then ordered only the record's
own revision against the cutoff, so a second selected revision whose
`known_from` was after the cutoff was silently admissible. The id-keyed
projection also let a later duplicate entry be overwritten by an earlier one.

Repair: the original `tuple(selected)` / `tuple(excluded)` sequences are
validated before any mapping - non-blank revision identity, duplicate selected
identity refuses, `selected ∩ excluded` refuses, the record's own revision must
be selected and not excluded (pre-existing law preserved verbatim), then every
selected entry's `known_from` must be offset-aware and `<= cutoff` under the
existing strict `>` temporal law, so exact-cutoff equality remains admissible.
The excluded half is deliberately not ordered: an excluded future revision is
retained *because* it was not knowable, and ordering it would delete the
evidence of its exclusion.

Tracked controls (8, `test_b5_p3_consumer_rebinding.py`): late second selected
revision refuses; a valid three-revision selection still passes (no blanket
refusal); equivalent offsets behave identically; duplicate selected identity
cannot hide a late entry; selected-cannot-also-be-excluded; entry order cannot
change the decision (3 permutations); malformed non-chosen instant refuses;
excluded future revision needs no cutoff instant.

## F5 - no typed-exception detail in a public refusal

Defect (reproduced before repair): `"<CODE>: <detail>"` for
`RecordVerificationError` and `str(exc)` for `SemanticAuthorityRefusal` placed
verifier-authored text in `refusal_detail`; the replay gate's
`UnassessableReplayEvidence` message was relayed by `_bounded`.

Repair: `_approved_refusal` / `_refusal_token` admit only members of
`RecordVerificationRefusal` or `AuthorityRefusal` (or their exact values);
anything else becomes a fixed `UNSPECIFIED_REFUSAL`. `str(exc)`, `repr(exc)` and
`exc.detail` are never used, and no log line is used as a substitute. Every
exception-to-verdict path was inspected: verifier, `RecordVerificationError`
(PIT / integration-absent / other), `SemanticAuthorityRefusal`, `_rebind`
loader, replay gate, custody read, authority-source derivation. Classification
still reads the mutable `_PIT_REFUSALS` / `_INTEGRATION_ABSENT_REFUSALS` sets, so
the two existing reporting mutations keep their meaning. `KeyboardInterrupt` and
`SystemExit` still propagate.

Tracked controls (7, `test_b5_p3_consumer_security.py`) assert the
non-credential-shaped sentinel `P3-SENTINEL-VALUE-DO-NOT-RELAY` is absent from
`repr(verdict.model_dump())` across the typed verifier path, every
`RecordVerificationRefusal` member (the code still travels), the
`SemanticAuthorityRefusal` `str(exc)` vector, a payload wearing an approved
code's clothes, the loader path during rebinding, the replay gate's own message,
and `SystemExit` propagation.

## Executable replay-binding guard

```
REPLAY_BINDING_CLAIMS = (
    "TEMPORAL_ELIGIBILITY",             # established by the I05 gate and the F4 sweep
    "REVISION_IDENTITY_COMPATIBILITY",  # established by _bind_replay
    "RECORD_PROVIDER_ARTIFACT_BINDING", # NOT expressible in the frozen schema
    "AUTHORITY_TO_CONSUME",             # established by the custody source
)
REPLAY_RECORD_BINDING_ESTABLISHED: bool = False
REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT = "REPLAY_EVIDENCE_RECORD_BINDING_V1"
```

While the guard is `False`, an evaluation satisfying every claim the frozen
schema can carry terminates in `INTEGRATION_REQUIRED` naming
`REPLAY_EVIDENCE_RECORD_BINDING_V1` and enumerating the met claims. This
terminal state is intentional: complete replay identity binding remains an
integration dependency, and an unsupported binding cannot establish
authoritative acceptance. No schema was invented, I05 was not rewritten, the
manifest was not touched, and no trust or integration state advanced.

The accepting branch stays reachable and exercised: harness tests flip the guard
with `monkeypatch.setattr(policy_module, "REPLAY_RECORD_BINDING_ESTABLISHED",
True)` - the state a minted contract would create - and thereby prove the accept
machinery was not deleted. That is a demonstration of downstream mechanism, not
production authorization.

## Targeted verification and mutation controls

| Suite | Result |
| --- | --- |
| Consumer modules (`contracts`, `custody`, `policy`, `rebinding`, `security`) | 177 passed |
| Adjacent replay/authority (`i05` gate, revision policy, evidence, i05/i06 replay safety, i09p2a authority, i09p2d custody scope PIT, i09p2e PIT entry parity) | 194 passed |
| Governance / scope / trust (i05 scope, i10 scope, i09p2b trusted root, i09p2c record verification, i09p2e trust consumer, i09 semantics, i05/i06 replay safety) | 331 passed |
| Independent audit suite, unadjusted | 5 failed / 28 passed - the two defect tests now pass; the 5 failures are the pre-guard positive controls reconciled in `04` |
| Independent audit suite, guard flipped | 33 passed |

Mutation controls were applied to a disposable copy of `quant-lab/src`; no
mutated code was committed and the worktree source was never mutated:

| id | mutation | outcome |
| --- | --- | --- |
| M-F4 | restore chosen-only cutoff checking through the id-keyed view | detected (2 detectors fail; positive controls still pass, so the detectors fire on the hole and not on a blanket refusal) |
| M-F5 | restore raw typed-refusal detail in the public refusal | detected |
| M-BIND | set `REPLAY_RECORD_BINDING_ESTABLISHED = True` with no minted contract | detected |

## Independent targeted acceptance

Status: **pending**. Agent 2's reattack request is reproduced in `03`. The
operator authorized this canonical execution concurrently with that reattack.
No independent acceptance of F4, F5 or the binding boundary is claimed in this
package.
