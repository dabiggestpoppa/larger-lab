# 02 - Three separate decisions

These are independent decisions with different evidence, different risk and
different authority. This mission prepared the package; it did not take any of
them.

## D1 - Accept the bounded fail-closed production consumer implementation

**Question:** is the implementation, as tested at
`868dd3fc91b5a38d02742bd3705da0c1d78b66c3`, acceptable as the bounded
fail-closed consumer?

**Evidence a D1 decision rests on:** the canonical green execution (4,952
anchored nodes, 0 failed, 0 errored, 11 explained skips, restoration verified),
the 161-test consumer suite, the G16/G17 governance reconciliation, and the
independent Agent 2 reconciliation.

**What D1 would mean:** the code and its evidence are accepted. It does *not*
enable any additional production behaviour, because the manifest is still empty
and `INTEGRATION_STATE` still reads `INTEGRATION_REQUIRED`. An accepted
implementation with an empty trust root still refuses everything it cannot
authorise.

**What D1 would not mean:** approval of any provider, any custody source, or
any trust root. Those are D2 and D3.

**Current status:** evidence complete on the engineer side, **independent
acceptance not received**.

## D2 - Authorise production integration or merge

**Question:** may this branch be merged into the production line and wired into
a running pipeline?

**What D2 needs beyond D1:** a merge target and release process, an operational
owner for the consumer, and a decision about what the consumer should do while
its authority contracts are unresolved (the honest answer today is: report
`INTEGRATION_REQUIRED`).

**Risk if D2 is taken before its authority work:** the consumer is safe - it
refuses - but a pipeline that expects acceptance will see refusals, which is a
product decision rather than a correctness issue.

**Current status:** not authorised, not requested. No merge was performed.

## D3 - Activate actual provider and custody-source authority

**Question:** should real providers be approved and a real custody source be
authorised, so that `AUTHORIZED` bases can exist in production?

**What D3 needs:** the approval manifest populated with reviewed artifacts and
evidence (currently `{}`), and a custody-source authority record
(`OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`) that does not yet exist. Both
are operator acts of authority, not engineering acts.

**Why D3 is separate:** the consumer's guards were hardened so that authority
cannot be manufactured from configuration. H03 makes an `AUTHORIZED` basis
require a named identity digest plus membership of the artifact in the pinned
manifest's approvals; with the manifest empty, the empty-manifest bypass is
closed. D3 is therefore the *only* path to a real authorization, by design.

**Current status:** not authorised. No manifest modification was made; the
manifest hash is unchanged from the starting SHA
(`3d707c59...2654`, `artifacts = {}`, `revoked = []`).

## Sequencing that follows from the above

D1 can be decided from the evidence in this package plus Agent 2's
reconciliation. D2 is a delivery decision that does not need D3 but should be
made knowing the consumer will refuse until D3. D3 requires authority documents
that do not exist yet, so it cannot be completed by any amount of engineering
in the current scope.
