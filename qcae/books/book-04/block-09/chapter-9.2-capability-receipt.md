# Chapter 9.2 — Capability Receipt

## Mission

Create the canonical machine-readable record of what capability Quant Lab believes it has, why, through which implementation, under what evidence and authority, and when that belief must be revisited.

## Receipt Core

```text
receipt_id
capability/atom IDs
contract version
implementation identity/acquisition form
source/artifact revisions
integration scope
proof evidence refs
security/legal refs
quant-validation refs if applicable
known limitations/assumptions
owner
rollback path
authority record
created_at
revalidation triggers
validity/expiry state
supersedes
```

## Receipt Meaning

A receipt is not a certificate of universal correctness. It states a bounded evidence-backed capability claim under specified conditions.

## Receipt States

`ACTIVE`, `STALE`, `REVALIDATION_REQUIRED`, `SUPERSEDED`, `REVOKED`, `REJECTED`.

## Granularity

Receipts may be atom-level when different parts of one system have different evidence or lifecycle.

## Invariants

1. Receipts bind capability, implementation, evidence, scope, and authority.
2. Receipts are bounded claims, not universal guarantees.
3. Different atoms may have different receipt states.
4. Staleness/revocation is explicit.
5. New evidence supersedes rather than erases history.

## Exit Criteria

Any agent can answer "why do we trust/use this capability?" by resolving one receipt and its evidence graph.
