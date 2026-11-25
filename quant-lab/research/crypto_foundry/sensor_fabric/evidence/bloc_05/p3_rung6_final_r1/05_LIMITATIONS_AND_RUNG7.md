# 05 - Limitations and Rung 7 recommendation

## What this package does not prove

1. **Parallel execution on this host.** Four workers produced a truncated
   bundle and 42 concurrency artifacts; one worker at 5,400 s is the only
   configuration observed to complete. The green result is serial. Nothing here
   shows the corpus is parallel-safe, and four workers should not be treated as
   supported until a parallel run completes with zero missing nodes.
2. **POSIX-only behaviour.** Eleven nodes are skipped for platform reasons
   (symlink semantics, POSIX mode bits, case sensitivity, `os.pathconf`). Those
   code paths are unexecuted on Windows and are the largest untested surface in
   the corpus.
3. **External services.** The real-PostgreSQL integration tests and the live
   network smoke are opt-in and were not exercised
   (`SENSOR_POSTGRES_TEST_DSN`, `SENSOR_NETWORK_SMOKE` unset). Every storage
   conclusion in this bundle is about the local/embedded paths the suite covers
   by default.
4. **Replay binding completeness (H02).** Record, provider, kind and cutoff are
   bound; the frozen schema cannot express provider + kind + artifact identity
   together, so those axes are named `UNRESOLVED_REPLAY_BINDING`
   (`REPLAY_EVIDENCE_RECORD_BINDING_V1`). Fail-closed is proven; full binding
   is not.
5. **Custody source authority.** `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`
   remains unresolved and unimplemented. H03 proves that authorization cannot
   be composed without an approving artifact; it does not provide an authority
   to approve anything.
6. **Acceptance.** A green canonical run is evidence for an operator decision,
   not the decision. No provider approval, manifest activation, trust
   promotion, gate advance or Bloc 6 step was taken, and no independent Agent 2
   reconciliation has been received.

## Honest reading of the green result

4,952 anchored nodes, 4,941 passed, 0 failed, 0 errored, 11 explained skips,
0 missing, 0 extra, 0 duplicates, restoration verified, tree clean after. The
run is complete relative to its own collection anchor, and the anchor digest is
identical at the starting SHA and at the verified candidate, so the repairs did
not quietly change what "the suite" means.

## Recommended Rung 7 scope

1. **Bind the replay axes the schema cannot express.** Define
   `REPLAY_EVIDENCE_RECORD_BINDING_V1` so provider, kind and artifact identity
   are bound rather than named unresolved, then re-run the H02 controls.
2. **Prove parallel safety before using it.** Either fix the OpenBLAS/temp-fs
   interference (per-worker thread caps plus per-worker temp roots are the
   obvious candidates) and complete a 4-worker run with zero missing nodes, or
   record serial execution as the canonical configuration in the runner
   contract so no future operator assumes otherwise.
3. **Run the POSIX surface once.** A Linux canonical run would execute the
   eleven skipped nodes and the symlink/permission fail-closed paths, which are
   currently the least-verified part of the storage fabric.
4. **Exercise the opt-in integrations separately** (`SENSOR_POSTGRES_TEST_DSN`,
   `SENSOR_NETWORK_SMOKE`) as a distinct assurance class, not folded into the
   canonical green.
5. **Keep the boundary where it is.** Provider approval, custody authority,
   manifest activation and trust promotion stay operator actions; the next rung
   can strengthen the *guard* without supplying the *authority*.
