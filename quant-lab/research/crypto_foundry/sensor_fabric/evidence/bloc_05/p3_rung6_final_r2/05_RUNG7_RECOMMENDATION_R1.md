# 05 - Limitations and the updated Rung 7 recommendation

## What this package does not prove

1. **Independent acceptance.** Agent 2's targeted reattack of F4, F5 and the
   binding guard is still in progress. The operator reconciled the sequencing
   dependency so this execution could proceed in parallel; that is not an audit
   result. No independent acceptance is claimed.
2. **Parallel execution on this host.** One worker at 5,400 s is the only
   configuration observed to complete. Four workers produced a truncated bundle
   and 42 concurrency artifacts in an earlier attempt; nothing here shows the
   corpus is parallel-safe, and four workers remain unsupported.
3. **POSIX-only behaviour.** Eight of the eleven skips are symlink, mode-bit,
   case-sensitivity or `os.pathconf` paths that do not execute on Windows. They
   are the least-verified surface in the corpus.
4. **External services.** The real-PostgreSQL integration tests and the live
   network smoke are opt-in and were not exercised
   (`SENSOR_POSTGRES_TEST_DSN`, `SENSOR_NETWORK_SMOKE` unset).
5. **Replay binding completeness.** Record, provider, kind and cutoff are bound;
   the frozen schema cannot express provider + kind + artifact identity
   together, so full replay identity binding stays
   `INTEGRATION_REQUIRED` (`REPLAY_EVIDENCE_RECORD_BINDING_V1`). Fail-closed is
   proven; full binding is not.
6. **Custody-source authority.** `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`
   remains unresolved and unimplemented. The guard proves authorization cannot
   be composed without an approving artifact; it supplies no authority.
7. **Acceptance.** A green canonical run is evidence for an operator decision,
   not the decision. No provider approval, manifest activation, trust promotion,
   gate advance or Bloc 6 step was taken.

## Honest reading of the green result

4,968 anchored nodes, 4,957 passed, 0 failed, 0 errored, 11 explained skips,
0 missing, 0 extra, 0 duplicate executions, restoration verified, tracked tree
clean after, verdict reproduced by the hardened verifier from the raw result
stream against an externally supplied count and digest. The universe grew by
exactly the 16 regression nodes the repair added, and nothing else entered or
left it, so the repairs changed what the suite checks without changing what "the
suite" means for any pre-existing node.

Both defect classes that justified this cycle are now closed locally and
canonically: a second selected revision cannot escape the cutoff, and no
exception-authored detail reaches a public refusal. The unresolved replay
binding is an explicitly named integration dependency with an executable guard,
not a hidden assumption.

## Updated Rung 7 recommendation

1. **Mint `REPLAY_EVIDENCE_RECORD_BINDING_V1` as the first Rung 7 action.** It is
   now the single blocking dependency for authoritative acceptance: define the
   contract that binds provider, kind and artifact identity, then flip
   `REPLAY_RECORD_BINDING_ESTABLISHED` and re-run the five reconciled positive
   controls as the acceptance gate. No other Rung 7 work should be bundled with
   it - the boundary should be crossed by one reviewed contract, not by a
   release that hides it among other changes.
2. **Settle custody-source authority separately.**
   `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` is an operator decision and
   should be resolved by an operator artifact, not by code that infers its own
   authority.
3. **Prove parallel safety or pin serial execution.** Either fix the
   thread-cap/temp-root interference and complete a multi-worker run with zero
   missing nodes, or record serial execution as the canonical configuration in
   the runner contract so no future operator assumes otherwise.
4. **Run the POSIX surface once on Linux.** It would execute the eight skipped
   platform nodes (symlink escapes, permission fail-closed, case-sensitivity,
   `pathconf` probing) and is the cheapest remaining assurance gain.
5. **Exercise the opt-in integrations as a distinct assurance class**
   (`SENSOR_POSTGRES_TEST_DSN`, `SENSOR_NETWORK_SMOKE`), never folded into a
   canonical green.
6. **Keep authority where it is.** Provider approval, manifest activation,
   trust promotion and merge stay operator actions; Rung 7 can strengthen the
   guard without supplying the authority.

## Acceptance recommendation

Recommend **conditional acceptance of Rung 6** at
`66200f3cb18ee5cea1483d986e64502f388eeb77` on the strength of the anchored green
canonical result plus the targeted repair evidence, with the explicit condition
that authoritative acceptance waits for
`REPLAY_EVIDENCE_RECORD_BINDING_V1`, and with Agent 2's targeted reconciliation
still outstanding. This package therefore records
`P3_CANONICAL_GREEN_AWAITING_FINAL_INDEPENDENT_RECONCILIATION`, not
`P3_FINAL_REPAIRS_CLOSED_CANONICAL_GREEN_AWAITING_RATIFICATION`.
