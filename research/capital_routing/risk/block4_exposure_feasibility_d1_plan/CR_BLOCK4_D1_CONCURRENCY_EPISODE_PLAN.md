# CR-BLOCK4-D1 CONCURRENCY / EPISODE PLAN

## Verified frozen truth

- max concurrency: **3** (R1_CONCURRENCY_SUMMARY.csv)
- hours with 2 positions: 565; 3 positions: 20; 4+: 0
- max gross exposure: 18.1878 f-units
- episodes at 12h interval: **482**; max events in one episode: 10

## Plans

- event-level feasibility (each accepted target against the contract)
- episode / account-level resource feasibility (overlapping events against
  shared account resources)

## Causal account replay (D1.4)

Sequential replay, no future resource information:

    admitted event -> economic target -> physical feasibility
    -> if executable, occupy physical resource -> release at frozen event close
    -> next event

## H1 vs physical failure

- H1 admission is NEVER rewritten.
- An H1-approved event that fails physical constraints is labeled
  PHYSICALLY_UNEXECUTABLE.
- Physical blocks are never fed back into the primary research admission history.

## Exit/release semantics

Execution-safety implementation (not new alpha): heat is released only when a
position is actually confirmed closed in broker truth (same-science rule from
planning R1, Part 20).
