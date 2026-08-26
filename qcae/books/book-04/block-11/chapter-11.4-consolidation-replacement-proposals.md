# Chapter 11.4 — Consolidation & Replacement Proposals

## Mission

Turn validated internal burden findings into bounded engineering proposals with contracts, evidence, migration plans, and rollback rather than vague refactor recommendations.

## Proposal Types

`CONSOLIDATE`, `REPLACE`, `EXTRACT`, `STANDARDIZE_INTERFACE`, `DEPRECATE`, `KEEP`, `INVESTIGATE`.

## Proposal Package

```text
problem/capability
current implementations/consumers
contract requirements
evidence of burden
candidate target state
expected net gain
migration stages
compatibility risks
proof required
rollback
required authority
```

## Consumer Safety

No consolidation proposal is valid until distinct consumer requirements and non-goals are represented. Shared-looking utilities may encode important domain differences.

## Quant/CEREBUS Boundary

Generic consolidation must not erase CEREBUS-specific structural semantics or risk constraints merely to standardize interfaces.

## Invariants

1. Proposals are capability/consumer grounded.
2. Refactor aesthetic alone is insufficient.
3. Migration and rollback accompany replacement.
4. CEREBUS semantics survive generic consolidation.
5. Proposal is not execution authority.

## Exit Criteria

Engineering opportunities are implementation-ready enough for later agent planning without authorizing the change themselves.
