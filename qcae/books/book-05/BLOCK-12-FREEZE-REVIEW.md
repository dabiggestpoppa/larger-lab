# Book V — Block 12 Freeze Review

**Result:** READY TO FREEZE

## Chain

```text
12.1 Orchestrator
→ 12.2 Specialized Workers
→ 12.3 Worker Contracts
→ 12.4 Context Isolation
→ 12.5 Handoffs
→ 12.6 Failure Recovery
→ 12.7 Budgeting
→ 12.8 Human Escalation
```

## Frozen Invariants

1. QCAE is orchestrated through explicit jobs, not one giant continuous prompt.
2. Workers are capability-bounded and least-privileged.
3. Worker request/result contracts are typed and versioned.
4. Durable artifacts outrank conversation context.
5. Context is assembled per task; prior claims retain verification state.
6. Handoffs are evidence/artifact based.
7. Worker crashes and malformed outputs cannot corrupt canonical state.
8. Retries are bounded and class-specific.
9. Budgets are explicit, hierarchical, and evidence-progressive.
10. No worker can silently expand authority or budget.
11. Human escalation is required at material authority/irreversibility boundaries.
12. Approval scope is narrow and recorded.
13. Orchestrator coordinates evidence progression but cannot override hard gates.
14. Logical worker specialization does not force unnecessary microservices.

## Block 13 Handoff

Block 13 must provide the local runtime services that make these contracts executable without OCE: state persistence, local policy, evidence storage, secrets boundary, sandbox manager, job queue, CLI/API, and graceful OCE absence.

**Block 12 status: FROZEN v0.1.**
