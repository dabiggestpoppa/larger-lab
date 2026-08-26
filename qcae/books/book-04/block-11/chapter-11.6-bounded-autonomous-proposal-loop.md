# Chapter 11.6 — Bounded Autonomous Proposal Loop

## Mission

Allow QCAE to continuously generate and refine engineering opportunities while preventing self-directed architecture mutation outside explicit authority.

## Loop

```text
observe capability census/memory/change signals
→ identify opportunity
→ retrieve evidence/negative memory
→ perform bounded investigation
→ draft proposal + proof/migration plan
→ rank
→ submit for review/authority
→ if approved, hand to later execution architecture
→ ingest outcome/evidence
```

## Budgets

Autonomous investigation is constrained by search, compute, execution, network, and change budgets defined by policy/runtime books.

## No Self-Approval

The worker that discovers and argues for a change cannot manufacture the authority to perform it. Evidence generation and authorization remain separate.

## Stop Rules

Stop when expected information gain is low, hard blocker is reached, sufficient evidence exists for review, or budget is exhausted.

## Feedback

Accepted, rejected, failed, and deferred proposals all return to memory so proposal quality improves without repeatedly reopening settled work.

## OCE Future

When OCE is ready, this loop submits structured authority requests and receives governed execution scope. Standalone QCAE uses the same semantic boundary through a local shim.

## Invariants

1. Autonomous intelligence may investigate/propose within budget.
2. It cannot self-grant mutation authority.
3. Search/proof stop rules apply internally too.
4. Proposal outcomes become memory.
5. OCE integration changes governance transport, not reasoning/evidence semantics.

## Exit Criteria

QCAE can behave like a persistent engineering intelligence system without becoming an uncontrolled self-modifying agent.
