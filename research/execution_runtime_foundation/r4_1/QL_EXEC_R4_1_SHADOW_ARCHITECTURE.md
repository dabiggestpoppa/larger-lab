# QL-EXEC-R4.1 — Shadow Architecture

## Topology

```
┌─────────────────────────────┐        ┌─────────────────────────────┐
│ ACTIVE TB STACK (PRIMARY)   │        │ GENERIC TB SHADOW (OBSERVER)│
│ supervisor / worker /       │        │ shadow supervisor (shadowctl)│
│ watcher / dashboard         │        │   │                          │
│   │                         │        │   ▼                          │
│   │ writes tb_runtime.db    │        │ GenericRuntime               │
│   │ writes tb_control.db    │        │   ├─ TBStrategyAdapter       │
│   │ PID/desired-state files │        │   ├─ TBTranslationAdapter    │
│   ▼                         │        │   ├─ BasketOrchestrator      │
│ MT5 terminal (EXTERNAL      │        │   └─ ReadOnlyBrokerSession   │
│ SESSION, order authority)   │        │        │                     │
└─────────────────────────────┘        │        ▼                     │
                                       │ shadow_state/<runtime_id>/   │
                                       │   runtime.sqlite (WAL)       │
                                       │   shadow.pid                 │
                                       │   shadow_desired_state      │
                                       └─────────────────────────────┘
              ▲  shared read-only market-data/decision snapshot
              └────────── exported by legacy TB (Option B) ──────────┘
```

## Key structural choices

1. **Separate process.** Generic shadow is its own process under its own
   `shadowctl`. It is never a child of the active TB supervisor.

2. **Separate durable state.** All mutable files live under
   `shadow_state/<runtime_id>/`. It never opens `quant-lab/state/tb_*` for
   write.

3. **Read-only broker boundary.** The shadow's `BrokerSession` is a
   `ReadOnlyBrokerSession` that exposes identity/account/clock/market/
   positions/orders/deals/snapshot but has NO `submit_order`,
   `close_position`, or `cancel_order` callable path.

4. **Shared data via export, not via second MT5 attach.** Because concurrent
   MT5 read safety is unresolved, G1 consumes read-only snapshots exported by
   the legacy stack (see MARKET_DATA_SHARING_OPTIONS).

5. **Hypothetical intents.** The shadow produces `ShadowExecutionPlan` /
   hypothetical intents that never flow into any submit path.

## Deployment generation

`TB-GENERIC-SHADOW-G1` binds:
- R4 commit: 750a14bf20bf0869f452d8df20138e58bbb091e5
- TB authority SHA: b48fd35255b41865026a3cba333ae2a2a0d6a004
- runtime profile hash
- account profile hash
- shadow-mode contract version

Any drift in these at startup => BLOCK (reuse R3 profile-drift gate).
