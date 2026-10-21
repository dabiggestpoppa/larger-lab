# Chapter 17.10 — Retiring Capability

## Mission

Define how an operator deliberately removes a capability or implementation from active use while preserving provenance, negative knowledge, receipts, and migration history.

## Retirement Reasons

- superseded by better implementation;
- no longer needed;
- unacceptable maintenance burden;
- security/license risk;
- upstream abandonment;
- internal consolidation;
- failed revalidation;
- strategic simplification.

## Retirement Plan

```text
identify consumers/dependents
freeze final known state
select replacement or removal path
migrate/disable consumers
remove secrets/authority
remove monitoring/update jobs where appropriate
archive receipts/evidence
mark lifecycle RETIRED/SUPERSEDED
verify no active dependency remains
```

## Historical Memory

Retirement never deletes the reasoning history by default. Future QCAE discovery should know what existed, why it was removed, and whether conditions for reconsideration exist.

## Rollback Window

Material retirements may retain a bounded rollback period where technically and legally appropriate before final cleanup.

## Invariants

1. Retirement is graph-aware and consumer-aware.
2. Authority/secrets are revoked with removal.
3. Historical evidence and receipts remain durable.
4. Supersession is linked to replacement capability.
5. Retirement reduces operational burden rather than leaving orphan infrastructure.
6. Reconsideration uses historical evidence instead of starting from zero.

## Exit Criteria

Operators can remove capability cleanly without destroying institutional memory or leaving hidden dependencies behind.
