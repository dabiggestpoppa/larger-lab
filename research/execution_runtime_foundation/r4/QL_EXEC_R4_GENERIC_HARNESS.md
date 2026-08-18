# QL_EXEC_R4_GENERIC_HARNESS (PATH B)

`GenericTBHarness` (`execution_runtime/tb/harness.py`) expresses the SAME TB
system through the generic runtime contracts:

- `TBStrategyAdapter` — canonical `TriangularBasisLiveEngine` behind the R1
  `StrategyAdapter` protocol (primary shadow / control executable).
- `TBCapitalPolicyAdapter` — transparent admission (no CR science).
- `TBTranslationAdapter` — model weight -> notional -> lots via the sealed
  execution contract (R1 `CapitalTranslationAdapter` protocol).
- `BasketOrchestrator` — multi-leg write-ahead execution above `BrokerSession`.
- `SimBrokerSession` — the R3 transport-neutral broker (per-symbol failure
  injection for the failure matrix).
- `RuntimeStore` — the R3 durable SQLite/WAL store (append-only journal,
  intents, owned positions).

## Architecture difference (documented)

R3's `GenericRuntime` core proves the SINGLE-leg lifecycle. The TB basket is
multi-leg, so its atomicity is owned by the `BasketOrchestrator` layer above
`BrokerSession` (not forced through the single-leg `_process_event` path). The
generic contracts (StrategyAdapter / CapitalTranslationAdapter / BrokerSession /
durable store / ownership / reconciliation) are all reused; only the multi-leg
orchestration is new.

## Guarantees

- PRIMARY is shadow-only (0 orders); CONTROL opens/closes the 3-leg basket.
- Write-ahead plan+legs before the first broker call; broker calls outside DB
  transactions; deterministic leg intent ids; duplicate-plan idempotency.
- Foreign positions are never touched; partial fill is never treated as full.
