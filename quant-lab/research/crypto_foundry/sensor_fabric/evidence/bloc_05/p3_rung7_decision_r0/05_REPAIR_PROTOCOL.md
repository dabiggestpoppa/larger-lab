# 05 - Repair readiness

Agent 2 is reattacking F1-F3 and H03/H05. This mission made **no repair**,
because no independently confirmed defect was received. The candidate is
preserved unchanged at `868dd3fc91b5a38d02742bd3705da0c1d78b66c3`.

## If a material defect is confirmed

1. **Reproduce first.** A confirmed defect must be reproduced as a failing test
   at the frozen candidate before any code changes. A report that cannot be
   reproduced is recorded as a reproduced-attempt with its outcome, not silently
   patched.
2. **Smallest authorized repair.** Fix the defect only; no refactors, no
   adjacent hardening, no test weakening. If the fix would require changing a
   frozen schema or an operator-approved artifact, it stops at this mission's
   boundary and becomes an operator decision.
3. **Publish separately.** The repair is a new commit on the same branch, with
   its own message naming the reproduced failure. It is not folded into
   `868dd3fc9` or `eb3644f03`.
4. **The freeze is invalidated.** Stated explicitly because it is the easy
   mistake: any change to production or canonical-test source produces a new
   candidate SHA. The Rung 6 canonical bundle then describes **different bytes**
   and must not be cited for the repaired candidate - not even when the change
   is small and obviously safe.
5. **Determine re-verification by what changed:**
   * *Production source only* - node identities and the collection digest
     usually stay the same, but a full canonical execution at the new candidate
     is still required. The old bundle is retained as history, not as evidence
     for the new SHA.
   * *Test source added or removed* - the collection anchor changes; re-collect,
     record the new count and digest, then execute with the new anchor.
   * *Evidence or documentation only* - no re-execution and no new candidate;
     the tested SHA is unchanged. This is exactly what `eb3644f03` is.
6. **Report the dependency.** If re-verification is required but cannot be run
   in the current session, the disposition is "repair published, re-verification
   outstanding", never "green at the repaired candidate".

## If no material defect is found

The candidate and the publication stand as they are. The Rung 7 package remains
`RUNG7_DECISION_PACKAGE_READY_AWAITING_INDEPENDENT_ACCEPTANCE`, and Agent 2's
reconciliation becomes the independent input for D1.

## What a repair would not change

The hard stop is unchanged by any repair: no production merge, no provider
approval, no custody-source activation, no manifest modification, no trust
promotion, no gate or Bloc 6 advancement, no self-ratification.
