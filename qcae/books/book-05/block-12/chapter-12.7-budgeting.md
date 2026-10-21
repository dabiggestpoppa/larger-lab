# Chapter 12.7 — Budgeting

## Mission

Control tokens, tool calls, network queries, clones, storage, compute, sandbox time, and candidate count so QCAE spends expensive effort only where expected information/capability value justifies it.

## Budget Dimensions

```text
LLM tokens/cost
tool/API calls
search pages
candidate count
repository-comprehension depth
sandbox CPU/memory/time
benchmark repetitions
storage/evidence volume
wall-clock deadline
```

## Hierarchical Budgets

Budget can exist at:

```text
system
request
candidate
worker step
```

Unused budget does not imply it should be consumed.

## Progressive Spend

Cheap filters precede expensive proving. Budget increases only as candidates survive evidence gates.

## Expected Value

The Orchestrator should compare likely information gain against marginal cost. A cheap test that can eliminate a candidate should run before a costly benchmark.

## Reservation

Reserve some budget for diverse alternatives and independent review so the first promising candidate does not consume all resources.

## Overrun

Workers cannot silently exceed limits. They return `BUDGET_EXHAUSTED/PARTIAL` or request an explicit extension with rationale.

## Quant Compute

Large backtests/Monte Carlo/ML experiments must have experiment budgets and stop conditions. More compute cannot substitute for weak methodology.

## Invariants

1. Budgets are explicit and hierarchical.
2. Spend escalates with evidence.
3. Candidate diversity receives protected budget where useful.
4. Workers cannot silently overrun.
5. Budget exhaustion remains visible.
6. Compute volume never compensates for invalid methodology.

## Exit Criteria

QCAE can execute long investigations predictably without uncontrolled context, API, or compute growth.
