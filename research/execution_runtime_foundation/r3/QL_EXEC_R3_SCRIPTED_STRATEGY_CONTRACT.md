# QL-EXEC-R3 — ScriptedStrategyAdapter Contract

Deterministic TEST/SIM strategy (runtime/adapters.py). No alpha, no performance
metrics, no market math.

- `produce_events()` replays the predeclared script (idempotent at the adapter
  level). The runtime's journal + deterministic intent ids are the dedup
  authority.
- `serialize_state()` / `restore_state()` round-trip the script + warm flag;
  restore failure is injectable (`set_restore_failure`).
- `warm()` failure is injectable (`set_warm_failure`).
- `health()` reports warm state + script size.

Event kinds: `ENTRY` (open risk), `EXIT` (close owned risk), `NOOP` (ignored).
Payload carries `side`, `quantity`, `broker_symbol`, `instrument`.

The adapter is the ONLY alpha boundary; the generic runtime never imports any
strategy package.
