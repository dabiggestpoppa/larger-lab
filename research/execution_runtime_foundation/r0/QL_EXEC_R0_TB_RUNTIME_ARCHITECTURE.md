# QL_EXEC_R0_TB_RUNTIME_ARCHITECTURE

Audited at frozen SHA `df5f349e02ac932491cb067df7aff25cb71c50ac` (`TB-R6.2-NATURAL-CANARY-EVIDENCE-PLAN`). All paths are read from that tree.

---

## 1. Component map

```
quant-lab/
  runtime/                     <- process/supervision/durable-status layer
    tb_runtime_config.py       config + paths + identity-gate constants
    tb_supervisor.py           worker process lifecycle owner
    tb_worker.py               strategy/data/execution/persistence process
    tb_runtime_db.py           SQLite/WAL runtime status + heartbeat + NAV
    tb_proc.py                 PID singleton + detached spawn helpers
    tb_dashboard.py            read-only localhost HTTP dashboard
    tbctl.py                   status/start/stop/restart CLI
    tb_r6_1_tests.py           runtime DB/worker/desired-state tests
    DEPLOYMENT_PROFILES.md     local_windows / windows_vps
  tb_live/                     <- durable domain layer (MT5-free except one lazy adapter import)
    market_data.py             typed fail-closed market-data contract + config
    snapshot.py                data-only adapter Protocol + MT5/Mock adapters + synchronized feed
    state_machine.py           frozen basket lifecycle transition graph
    persistence.py             append-only event ledger (BasketLedger)
    reconciliation.py          broker/local reconciler + ownership rule
    full_engine.py             deterministic full-engine harness + translate_intent
  engines/                     <- TB strategy science + demo canary harness
    tb_forward_config.py       frozen StrategyModelConfig (PRIMARY/CONTROL)
    triangular_basis_engine.py basis/z math (sealed)
    triangular_basis_live.py   live strategy engine (BasketDecision/BasketIntent)
    triangular_execution_contract.py  execution intent types + notional/lot translation
    tb_r6_demo_canary.py       DemoEnvironment (identity gate) + quote/truth/order-send accounting
  mt5/                         <- broker/execution adapters (direct MT5)
    triangular_execution_layer.py  atomic 3-leg basket execution (order_check/order_send)
    execution_layer.py         legacy symmetry-trap executor (NOT the TB runtime path)
    ... many legacy executors  (symmetry_trap/p90/dmr/etc.)
```

---

## 2. Process topology (validated, local_windows)

- **Supervisor** (`tb_supervisor.py`) owns the WORKER process lifecycle only. It never touches strategy logic.
  - Singleton PID lock (`tb_supervisor.pid`); second supervisor fails closed (split-brain protection).
  - Spawns `tb_worker.py` with a UTC `GEN-%Y%m%dT%H%M%S` generation when desired-state == RUNNING.
  - Bounded exponential backoff `(5, 15, 30, 60)s`; backoff counter resets after the worker survives 120 s.
  - Kills + restarts a worker whose heartbeat is stale (> 300 s) while the process is still alive.
  - Never restarts after an intentional `tbctl stop` (durable desired state).

- **Worker** (`tb_worker.py`) is the strategy/data/execution/persistence process. Startup order (frozen, fail-closed):
  1. MT5 connect (via `DemoEnvironment`).
  2. Identity gate (`Ox Securities` / `OxSecurities-Demo` / trade_mode 0 DEMO / USD).
  3. Ledger integrity check → BLOCKED_LEDGER on corruption.
  4. Reconstruct ledger state.
  5. Broker read (`broker_truth`) filtered by magic.
  6. Reconcile owned-vs-ledger: owned positions without ledger intent → BLOCKED_RECONCILIATION.
  7. Warm the rolling window from real terminal history.
  8. Monitor loop. PRIMARY (`TB-FWD-V1`) runs SHADOW-ONLY (decisions logged, never executes); CONTROL (`TB-FROZEN-CONTROL`) is the executable demo model.

- **Dashboard** (`tb_dashboard.py`) reads `RuntimeDB` only; no log scraping, no MT5, no controls.

- **tbctl** is the operator control surface. `stop` is an INTENTIONAL STOP (persists STOPPED_BY_USER).

---

## 3. Durable state

Two distinct stores:

1. `RuntimeDB` (`quant-lab/state/tb_runtime.db`, SQLite WAL):
   - `runtime_status` key/value flags (desired_state, deployment_generation/start, NAV baselines).
   - `runtime_heartbeat` (pid, generation, state, mt5_connected, account_gate, market_open, last_closed_bar, open_basket_id, today/deploy PnL, account_equity, disk_free_gb, last_error).
   - `runtime_errors` (bounded 200-row trail).
   - `daily_nav`, `deployment_nav` (frozen equity baselines).

2. `BasketLedger` (`quant-lab/state/tb_control.db`, SQLite WAL, append-only):
   - `events` table: `event_id` PK, monotonic `seq` UNIQUE, `dedup_key` UNIQUE (idempotency), `payload` + `payload_hash`, `prior_state`/`new_state` validated against the frozen transition graph before commit.
   - `basket_current`: derived materialized last-known state (cache, never source of truth).
   - Integrity check on startup (schema version, tables, monotonic seq, idempotency keys, payload hashes, transition validity).

---

## 4. Ownership model (validated)

A broker position is "TB-owned" only through explicit identity evidence:
- `magic == TB magic` AND (`TB|<basket_id>|<canonical>|<leg_id>` comment token OR a persisted `LEG_FILL_CONFIRMED` linkage for that position ticket).

Anything else is `UNKNOWN_POSITION`: never altered, never assumed. Foreign/manual positions may consume margin/buying power but are never claimed as strategy PnL.

Current magic: CONTROL and PRIMARY both use `31082026` (acceptable only because primary remains shadow); test harness uses `31082027`. This single-shared-magic pattern is explicitly **not** acceptable as generalized multi-strategy identity (see `QL_EXEC_R0_OWNERSHIP_NAMESPACE.md`).

---

## 5. Execution translation chain (validated)

```
BasketIntent (model weights)
  -> translate_intent(intent, basket_notional_usd=5000.0 FIXED)
  -> BasketExecutionIntent (legs, magic, basket_id)
  -> _size_legs: model_weight_to_notional(weight, basket_notional_usd, total_weight)
                 notional_to_mt5_lots(notional, price, ContractSpec)
  -> rounded lots (volume_min/step/max applied)
  -> _neutrality_preflight (GATE K residual exposure)
  -> open_basket -> order_check/order_send (3 legs)
  -> broker verification -> BASKET_OPEN_VERIFIED
```

The notional is a **frozen fixed demo constant** (`BASKET_NOTIONAL_USD = 5000.0`), NOT derived from account equity. This is exactly the hard-coupling the generalized architecture must replace: account binding and account-equity-denominated sizing must occur before notional translation.

---

## 6. Execution gates (validated, frozen, never PnL-tuned)

- `MAX_QUOTE_AGE_MS = 2000`
- `MAX_CROSS_LEG_SKEW_MS = 1000`
- `SPREAD_MAX_PTS = 100`
- `GATE_K_MAX_RESIDUAL_PCT = 10.0` (triangular neutrality residual)
- `MIN_FREE_DISK_GB = 0.5` (disk guard)
- Identity gate: company / server / trade_mode / currency.

---

## 7. MT5 coupling summary (canonical runtime path)

Four modules in the canonical TB R6.1 runtime import `MetaTrader5` directly:

1. `runtime/tb_worker.py` — `terminal_info`, `history_deals_get`, `positions_get`, `account_info`.
2. `engines/tb_r6_demo_canary.py` — `account_info`, `terminal_info`, `symbol_info`, `symbol_info_tick`, `order_check`, `positions_get`, `orders_get`, `history_deals_get`, plus `order_send` monkeypatched for accounting.
3. `mt5/triangular_execution_layer.py` — `symbol_info`, `symbol_info_tick`, `order_check`, `order_send`, `positions_get`, `orders_get`.
4. `tb_live/snapshot.py` — lazy `import MetaTrader5` inside `MT5MarketDataAdapter` (data-only: `initialize`, `terminal_info`, `symbol_info`, `symbol_select`, `copy_rates_from_pos`, `symbol_info_tick`, `shutdown`).

The durable domain layer (`state_machine`, `persistence`, `reconciliation`, `market_data`) is MT5-free by construction — enforced by `tb_r3_tests.py` ("must not import MT5").

There is a large **legacy/parallel** MT5 surface in `quant-lab/mt5/*` and several `engines/*` (symmetry_trap, p90, dmr, production_runtime, etc.) that is NOT part of the validated TB R6.1 runtime path. Full inventory: `QL_EXEC_R0_DIRECT_MT5_COUPLING_AUDIT.csv`.

---

## 8. What TB Forward already proves (the reusable pattern)

- Persistent runtime with supervisor/worker separation.
- Durable runtime status DB + append-only event ledger with write-ahead intent.
- Idempotency via deterministic dedup keys.
- State-machine-enforced lifecycle with fail-closed transitions.
- Broker/local reconciliation with explicit ownership.
- Restart reconstruction (verify durable state → connect → identity gate → read account/orders/positions/deals → reconstruct → reconcile → warm → only then allow risk).
- Demo identity gate (configured vs reachable vs authenticated vs identity-matched vs execution-enabled distinction is partially implicit).
- PnL ownership from owned (magic + comment) positions/deals only.
- Heartbeat, dashboard (read-only), desired-state, PID singleton, disk guard, log rotation.
- Broker truth precedence for exposure; durable local ledger for ownership intent.

---

## 9. What TB Forward does NOT yet have (the R0 additions)

- An explicit `AccountRegistry` / account object (identity gate constants are hard-coded in two modules).
- A `PortfolioGroup` / `StrategyAccountBinding` / `RuntimeProfile` model.
- A generic `StrategyAdapter` (worker imports the triangular engine directly).
- A generic `CapitalPolicyAdapter` (notional is a fixed constant).
- A generic `BrokerSession` (data adapter exists; execution/account/identity still call MT5 directly).
- Multi-instance state isolation (`state/`, `logs/` are shared, not keyed by runtime_id).
- Atomic heat reservation (single-threaded worker avoids the race by construction; a multi-event fleet will not).
- Fleet supervision (supervisor supervises exactly one worker).
- Hedging vs netting policy, and a strong ownership namespace (single shared magic).
