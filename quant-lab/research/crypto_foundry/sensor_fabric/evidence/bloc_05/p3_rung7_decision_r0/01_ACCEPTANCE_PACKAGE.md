# 01 - Operator acceptance package

## Implementation commit ladder

| # | SHA | Subject | Effect |
| --- | --- | --- | --- |
| 0 | `5ee268b1d872fe4040d2d1505d012f344e7b5d54` | B5-P3-R5: executable production consumer security suite | starting point |
| 1 | `d81cceb28aa79870f6702bed053bfb6d8d80f2c1` | B5-P3-R6: total fail-closed boundary and replay rebinding | H01-H05 repairs, G17 reconciliation |
| 2 | `868dd3fc91b5a38d02742bd3705da0c1d78b66c3` | B5-P3-R6: keep the leak sentinel out of credential shape | fixture-only fix required by the canonical run |
| 3 | `eb3644f03528744c85811b3ff1d80789fe69fc54` | B5-P3-R6: publish the Rung 6 verification record | +7 evidence files, +637/-0, no code |

**Final canonical candidate: `868dd3fc91b5a38d02742bd3705da0c1d78b66c3`.**
Publication `eb3644f03` is documentation only.

## Canonical execution accounting (at the candidate)

| Field | Value |
| --- | --- |
| Collection anchor | 4,952 nodes, digest `f2fc9090...d1931`, 13 groups |
| Anchor stability | identical at starting SHA and at the candidate |
| Disposition / assurance | `COMPLETE` / `ANCHORED_COMPLETE` |
| Outcome | `GREEN` |
| Passed / failed / errored | 4,941 / 0 / 0 |
| Skipped | 11, each with a recorded platform or opt-in reason |
| Missing / extra / duplicates | 0 / 0 / 0 |
| JUnit | `tests=4952 failures=0 errors=0 skipped=11 time=1494.799s` |
| Independent re-verify | `verify --require-anchor` exit 0, external anchor 4,952, digest checked, recomputed counts equal recorded |
| Evidence restoration | attempted, verified, 11 paths, 0 failures |
| Tree after run | clean, 0 dirty paths, 0 untracked additions |
| Execution configuration | 1 worker, 5,400 s partition budget, thread caps 1 |

Two earlier attempts are preserved as failed evidence:
four workers → `INCOMPLETE_INFRA` (parallel interference, 42 concurrency
artifacts, all green serially); one worker at the default 900 s timeout →
`INCOMPLETE_INFRA` (partition timeout, plus four failures caused by this
mission's own credential-shaped test sentinel, fixed in `868dd3fc9`).

## Governance reconciliation

* **G16** (I08 scope admission, recorded in R5): confirmed prospective by
  measurement - `+15/-3`, one live predicate gained `/consumer/`, no sealed
  evidence touched, exact-file constraint in I05/I10 `P3_MASTER_EXACT_PATHS`.
* **G17** (found in this mission, disclosed): the I06 audit and producer never
  admitted `consumer/` and their pins were stale. Fixed by a disclosed
  prospective amendment plus mechanical republication of the I05, I06 and I09
  artifacts by their own producers. I06 producer is idempotent across two runs.
* Focused governance set at the candidate: 432 passed (governance 415 + I15
  hardening 17), consumer suite 161 passed.

## Independent acceptance status

**Not received.** No Agent 2 reconciliation result of F1-F3 or H03/H05 has
reached this mission. The canonical verification above is the *primary*
engineer-side result; it is not independent acceptance and is not presented as
such.

## Current production capabilities

What the shipped consumer actually does, under the empty pinned manifest:

1. **Closed verdict vocabulary.** `ACCEPT_FIELD_BINDING`, `REFUSE`,
   `INTEGRATION_REQUIRED`. There is no `ACCEPT` and no `AUTHORIZED` decision;
   `AUTHORIZED` is a custody *basis*, deliberately kept out of the decision
   vocabulary.
2. **Closed refusal vocabulary.** 14 codes, each naming one control
   (field scope, PIT admissibility, replay blocking, evidence binding, trust
   context, custody source, verifier crash). No generic failure laundering.
3. **Field-scope acceptance.** A record may be accepted only for an allowlisted
   economic field with evidence bound to this artifact; anything else refuses.
4. **PIT law.** Cutoffs must be offset-aware and non-date-only; a selection that
   excludes the record's revision, or includes a revision known after the
   cutoff, refuses as `PIT_INADMISSIBLE`.
5. **Replay binding on the axes the frozen schema carries.** Revision identity,
   cutoff and declared availability are bound; wrong-row evidence refuses as
   `REPLAY_BLOCKED`.
6. **Evidence custody.** Two-read digest binding: the adjudicated bytes and the
   recorded bytes must be the same bytes.
7. **Custody authority derived from the pinned root.** `AUTHORIZED` requires a
   named identity digest (manifest, artifact, approval, registry, record kind,
   provider, cutoff) and membership of that artifact in the manifest's
   approvals. With the manifest empty, no authorization can be composed.
8. **Total fail-closed boundary.** Unexpected exceptions contribute only their
   class (payload withheld); `KeyboardInterrupt`/`SystemExit` propagate; only
   programmer errors raise.

## Explicitly unsupported capabilities

1. No provider approval and no manifest entry exists (`artifacts = {}`); the
   trust root is `B5_I09P2A_EMPTY_TRUST_ROOT_V1`.
2. No custody-source authorization: `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`
   is unresolved and unimplemented (see 03).
3. Replay evidence cannot be bound on provider, record kind or artifact
   identity: `REPLAY_EVIDENCE_RECORD_BINDING_V1` is unresolved (see 03).
4. No production integration: `INTEGRATION_STATE` is `INTEGRATION_REQUIRED`, so
   the consumer reports integration-required rather than accepting a record
   whose custody basis cannot be authorized.
5. No cached-verdict divergence path: `CACHED_VERDICT_DIVERGENCE` is a reserved,
   unreachable code; the interface was omitted rather than shipped unused.
6. No wildcard record kind: `SUPPORTED_RECORD_KINDS = ("TRADE", "LIQUIDATION")`.

## Known environmental limitations

1. The green result is **serial**. Four-worker execution is unsupported on this
   host (OpenBLAS thread exhaustion and shared Windows temp staging).
2. **Eleven skips** are POSIX or opt-in only: symlink semantics, mode bits, case
   sensitivity, `os.pathconf`, real PostgreSQL (`SENSOR_POSTGRES_TEST_DSN`),
   live network smoke (`SENSOR_NETWORK_SMOKE`). Those paths are unexecuted here.
3. Host: Windows 10 (26200), CPython 3.11.9, pytest 9.0.3, 8 CPUs.
4. The canonical bundle is local evidence, not committed: see 04.

## Remaining integration dependencies

| Dependency | Blocks | Owner |
| --- | --- | --- |
| `REPLAY_EVIDENCE_RECORD_BINDING_V1` | replay evidence cannot be bound to provider / record kind / artifact | schema owner + operator |
| `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` | no custody source can be authorised at all | operator authority |
| Provider approval / manifest population | any real `AUTHORIZED` basis | operator |
| Independent acceptance (Agent 2) | D1 | independent reviewer |
| POSIX + opt-in integration runs (optional) | narrower assurance gap | operator scheduling |

None of these is removed by accepting D1; D1 accepts the implementation and its
fail-closed behaviour, not the authority it is waiting for.
