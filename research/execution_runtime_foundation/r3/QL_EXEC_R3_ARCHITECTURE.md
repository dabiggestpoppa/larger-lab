# QL-EXEC-R3 — Architecture

## Module layout (new under `quant-lab/execution_runtime/`)

```
runtime/
  state.py          RuntimeState enum + frozen transition graph
  intent.py         IntentState / PositionState / ExecutionIntent + deterministic id
  store.py          RuntimeStore (SQLite + WAL) + append-only journal
  reconciliation.py ReconciliationState + Reconciler
  singleton.py      SingletonLock (file lock keyed by runtime_id)
  heartbeat.py      Heartbeat + TelemetrySnapshot (read-only)
  adapters.py       ScriptedStrategyAdapter / PassThroughCapitalPolicyAdapter /
                    TestCapitalTranslationAdapter (TEST/SIM)
  engine.py         GenericRuntime (lifecycle + step + crash injection)
brokers/
  sim_broker.py     SimBrokerSession (BrokerSession, in-memory, fault injection)
```

## Dependency direction

```
RuntimeProfile / AccountProfile
        |
GenericRuntime (engine.py)
   ├── StrategyAdapter            (injected)
   ├── CapitalPolicyAdapter       (injected)
   ├── CapitalTranslationAdapter  (injected)
   ├── BrokerSession              (injected; SimBrokerSession in tests)
   ├── RuntimeStore               (injected; SQLite/WAL)
   ├── SingletonLock              (injected or derived from store path)
   └── clock (callable, injected) — wall time only for heartbeat diagnostics
```

## Key invariants

1. Write-ahead: `ExecutionIntent` is committed BEFORE `broker.submit_order`.
2. No broker call inside a SQLite write transaction (TX1 intent -> commit,
   broker call, TX2 result -> commit).
3. Broker truth wins for physical exposure; the local journal is authoritative
   for logical ownership/history. Reconciliation combines them.
4. Foreign positions are reported, never modified, never claimed.
5. Provider/strategy-specific values never live in the generic engine.
