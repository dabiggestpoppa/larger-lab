# QL_EXEC_R4_TB_BASKET_EXECUTION_CONTRACT

The TB basket is three legs (GBPAUD, GBPNZD, AUDNZD), max one concurrent.
R3's GenericRuntime proves a single-leg lifecycle; the basket is expressed
through a NEW strategy-agnostic multi-leg orchestration layer above
`BrokerSession` (see `QL_EXEC_R4_MULTI_LEG_ORCHESTRATION.md`).

## Write-ahead

Before the first leg submit, the parent plan + every leg intent is committed
durably (journal `BASKET_PLAN_CREATED` + per-leg `ExecutionIntent`). No broker
call happens inside a DB write transaction.

## Open

1. `order_check` all three legs (no sends).
2. Submit legs sequentially (deterministic order L1/L2/L3).
3. Verify fills against broker truth (ownership tag + magic).
4. `OPEN` only after all three fills verified; `BROKEN_HEDGE` -> flatten owned
   -> `ABORTED_FLAT` on partial; `ABORTED_FLAT` on zero fill.

## Broken hedge / flatten

Any partial combination (leg rejected / partial / missing) prioritizes risk
reduction: close only owned legs, verify flat, never claim a non-owned leg.

## Close

Basket-level: close all owned legs, verify broker flat before `CLOSED`. A
failed close leaves the plan `RECONCILIATION_REQUIRED` (never marks CLOSED while
owned exposure remains).

## Ownership

Per-leg logical ownership id + broker tag (`TB|<basket>|<symbol>|<leg>` + magic).
The durable ledger is authoritative; the tag is a lookup key.

## Restart

Reconstruct from broker + ledger: all legs present => adopt OPEN; partial =>
flatten; no exposure + pending intents => abort (never blind resubmit).

## Parity result

EXACT normal path; SAFETY_STRENGTHENING_NONREGRESSIVE failure path (generic
emits explicit per-leg fill confirmation and never marks CLOSED while owned).
