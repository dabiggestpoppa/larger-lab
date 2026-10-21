# Chapter 9.7 — Retrieval & Decision Reuse

## Mission

Make evidence memory operational by requiring agents to retrieve relevant prior capability knowledge before launching new discovery/proving work.

## Retrieval Order

For a capability request search:

```text
active internal receipts
prior positive knowledge
prior negative knowledge
known candidates/specifications
stale evidence needing refresh
then new external discovery
```

## Decision Reuse

A prior decision can be reused only when its material scope still matches. Otherwise reuse its evidence/test plan, not its conclusion.

## Anti-Loop Rule

Before escalating an expensive candidate, check whether the same source/revision/acquisition form has already failed and whether reconsideration conditions are actually met.

## Context Compression

Agents receive compact memory summaries plus resolvable evidence IDs rather than dumping the entire history into context.

## Invariants

1. Memory retrieval precedes redundant discovery.
2. Conclusions are reused only under matching scope.
3. Negative memory blocks pointless repetition.
4. Evidence/test plans can be reused even when decisions cannot.
5. Context compression retains resolvable provenance.

## Exit Criteria

QCAE's intelligence compounds across runs instead of resetting with each agent session.
