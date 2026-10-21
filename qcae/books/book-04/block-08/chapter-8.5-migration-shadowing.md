# Chapter 8.5 — Migration & Shadowing

## Mission

Move from current capability to acquired capability incrementally, comparing behavior before irreversible cutover.

## Migration Ladder

```text
offline replay
→ shadow execution
→ bounded non-authoritative use
→ partial traffic/workload
→ controlled cutover
```

Not every capability requires every stage, but skipping a material stage requires justification.

## Shadowing

Run old and new implementations on identical inputs where possible. Compare outputs, errors, latency, state transitions, and resource behavior without allowing the shadow candidate to create production side effects.

## Divergence Ledger

Classify differences as expected, bug, contract violation, data/environment difference, or unresolved.

## Quant Boundary

For trading capability, shadow/paper operation remains non-authoritative. It may validate operational behavior but cannot grant capital authority.

## State Migration

Persistent state conversions require explicit schema/version, validation, backup, and reverse/restore strategy.

## Invariants

1. Migration is staged proportional to risk.
2. Shadowing cannot create authoritative side effects.
3. Divergence is explained rather than averaged.
4. State migration is versioned/reversible where feasible.
5. Paper/shadow trading is not live-trading authority.

## Exit Criteria

The candidate can replace or supplement the current capability with observed equivalence/differences and controlled state transition.
