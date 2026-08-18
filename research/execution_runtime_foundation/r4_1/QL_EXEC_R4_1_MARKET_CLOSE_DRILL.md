# QL-EXEC-R4.1 — Market Close Drill

## Objective

Observe market-closed / recovery behaviour without latching stale truth
(TB R6.1B lesson: `ONLINE_MARKET_CLOSED` must not stick after recovery).

## Scenario

1. Feed/export reports market closed.
2. Shadow enters its expected waiting/closed state (`WAITING_FOR_BROKER` or
   broker market-closed observation).
3. Assert: zero execution attempts (broker_write_calls == 0), hypothetical
   intents may still be computed but never submitted.
4. Feed/export recovers (fresh healthy observation).
5. Assert: shadow recomputes state from the fresh observation; it does NOT
   remain latched in the stale closed state.

## Pass criteria

- no order attempt at any point
- state transition to waiting/closed is explicit
- recovery recomputes rather than latching
- legacy TB unaffected throughout

## Non-latching rule

A cached "market closed" observation is never treated as permanent truth.
Every fresh healthy observation triggers state recomputation.
