# TB-R0 — CANONICAL TRUTH DISCOVERY — ARCHITECTURE MAP

**Program:** TB-FORWARD-ENGINE (TB-R0 … TB-R10) — execution/deployment translation of the
sealed triangular-basis (TB) research onto the CEREBUS MT5/Python bridge.

**Branch:** `tb-forward-engine` (base: `origin/master` @ `6769ad31`).
**Companion:** `TB_FORWARD_TRUTH_LOCK.json` (machine-readable truth; this file is the
human-readable explanation of the same facts).

---

## 0. Headline decision

**DECISION = UNIQUE_CANONICAL_TRUTH_IDENTIFIED.** The sealed TB research and the legacy MT5
bridge are both uniquely identifiable on `master`, and the canonical forward contract in the
program spec is confirmed by the research decisions (P6 entry → 3.0, P7 exit → −0.25, TB-B
exact-neutral weighting).

**One material discovery changes the shape of the program:** a prior agent already built a
large fraction of TB-R1 … TB-R7 on `master` (the `TB-LIVE-*` / `triangular_*` work under
`quant-lab/mt5/`, `quant-lab/engines/`, and `artifacts/triangular_basis/live/`). That work is
inventoried in §5 and must be **reused, audited, or superseded deliberately** at each later
checkpoint — the program is not greenfield from `cerebus_live_bridge.py`.

---

## A. Research truth (what the sealed model actually is)

| Fact | Value | Source |
|---|---|---|
| Canonical branch / commit | `master` @ `6769ad31` | repo tip |
| Sealed validation | TB-P5 `7868a67d` (405/405 exact frozen-signal re-sim) | `tb_p5_validate.py` |
| Entry anatomy | TB-P6 seal `31e7ad5e` + P6.5 `a7a1fddd` | `TB_P6_DECISION.json` |
| Exit/convergence | TB-P7 seal `765415e1` + repro-fix `6769ad31` | `TB_P7_DECISION.json` |
| Universe | GBPAUD, GBPNZD, AUDNZD | `strategy_freeze.json` |
| Basis | `ln(GBPAUD) − ln(GBPNZD) + ln(AUDNZD)` | `tb_p5_validate.py` |
| Normalization | rolling mean / population-std (ddof=0) over the **previous 200** bars (shifted by 1 → current bar excluded); `z=(b−μ)/σ`; NaN→0.0 | `compute_basis_z` |
| Lookback | 200 | `LOOKBACK` |
| **Primary entry** | `|z| > 3.0` (strict `>`) — TB-B@3.00 = A | `tb_p6_anatomy.py simulate`, P6 decision |
| **Primary exit** | same rolling z: SHORT exits when `z ≤ −0.25`; LONG exits when `z ≥ +0.25` | `tb_p6_anatomy.py simulate(exit_target=−0.25)`, P7 E1 = A |
| Control entry | `|z| > 2.5` | frozen |
| Control exit | `z → 0.0` (SHORT `z≤0`, LONG `z≥0`) | frozen |
| Stop / invalidation | `|z| ≥ 6.0` | frozen |
| Session | London only, 3–12 EST (fixed UTC−5), ≥120 min to exit, hard exit at 12 EST | frozen |
| Direction | `z>0` (rich) → SHORT basket; `z<0` (cheap) → LONG basket | `_open_t` |
| Re-entry | max 1 concurrent basket; no cooldown; post-close re-signal re-enters | `simulate` loop |
| Daily loss cap | −500 pips/session-day → stop | `MAX_DAILY_LOSS_PIPS` |
| Weighting | **TB-B exact-neutral**: `min ‖q−q_α‖²` s.t. `E q = 0`, `Σq=1`, `q≥0`; sizes `s=3q`; `q_α` = inverse-ATR normalized | `verify_tb_04a.project_basket(eps=0)` |
| Exposure matrix `E` | 3×3 USD-normalized currency exposure; `f_i = rate_base/(p_i·rate_quote)`; per-leg sides from direction | `exposure_matrix` |
| Costs | 10.2 pips round trip (spread 1.5+2.5+2.0, commission 1.4×3) | frozen |
| Magic number | `31082026` | `strategy_freeze.json` |
| Timeframe | M5 | frozen |
| Conversion rates | GBP 1.34852, AUD 0.70583, NZD 0.58844 | `neutrality_gate.json` |
| Contract specs | 100k contract, 0.01 min/step, 200 max lot | `neutrality_gate.json` |

### Forward contract (frozen by this program)

- **TB-FWD-V1 (PRIMARY):** TB-B exact-neutral; `|z|>3.0` entry; rolling-z overshoot exit at
  `−0.25` (symmetric); London 3–12 EST; stop `|z|≥6.0`; hard exit 12 EST.
- **TB-FROZEN-CONTROL (shadow only):** `|z|>2.5` entry; `z→0.0` exit.

### Documented spec ambiguities (resolved, not guessed)

1. `strategy_freeze.json` points at commit `2435d04e` and lists lookback 200 / 2.5 / 6.0, but
   `triangular_basis_engine.py` at that commit *and* on master carries lookback 100 / entry 3.0 /
   stop 5.0 (the file drifted after the freeze). **Resolution:** the sealed research pipeline
   (`tb_p5_validate.py`, 405/405 exact) is the truth source; `triangular_basis_engine.py`'s
   in-file `Config` is stale and must not define the forward engine.
2. The spec's "`|z| >= 3.0`" is a paraphrase; the canonical entry is strict `|z| > threshold`.
   The spec's "trade-relative z reaches −0.25" is a paraphrase; the canonical exit uses the
   **same rolling z** as entry (SHORT `z≤−0.25`, LONG `z≥+0.25`), not a re-normalized
   trade-relative value.
3. Spec-listed `quant-lab/mt5/mt5_data_fetcher.py` is a 0-byte stub; the real fetcher is
   `quant-lab/mt5_data_fetcher.py`.
4. Frozen conversion rates / contract specs are **broker facts from the execution seal**, not
   universal constants; R2/R4 must re-read real broker metadata and fail closed on mismatch.

---

## B. Legacy MT5 bridge — transport capability map

Primary reference: `quant-lab/mt5/cerebus_live_bridge.py` (886 lines, Symmetry-Trap live bridge).

| Capability | Function(s) | Location |
|---|---|---|
| Initialize + explicit login | `mt5_connect()` (initialize → login(login/password/server) → account_info; fallback default initialize) | cerebus_live_bridge.py |
| Account info | `mt5.account_info()` (login/server/balance/equity) | cerebus_live_bridge.py |
| Bar retrieval (M5) | `get_bars()` via `mt5.copy_rates_from_pos(..., TIMEFRAME_M5, 0, count)` | cerebus_live_bridge.py |
| Tick retrieval | `mt5.symbol_info_tick(symbol)` (bid/ask) | send_order |
| Symbol metadata | `mt5.symbol_info(symbol)` + `symbol_select`; `point`, `digits`, `trade_stops_level`, `visible` | send_order / get_pip_size |
| Open-position retrieval | `get_positions()` via `mt5.positions_get()` | cerebus_live_bridge.py |
| Order placement | `send_order()` — market BUY@ask / SELL@bid, `TRADE_ACTION_DEAL`, deviation 10, `ORDER_TIME_GTC`, IOC default | cerebus_live_bridge.py |
| Fill-mode fallback | IOC → FOK → RETURN on retcodes 10014/10016/10017/10030 | send_order |
| Close logic | `close_position(ticket)` via reverse `order_send`; SL-modify path `modify_sl(ticket, new_sl)` | cerebus_live_bridge.py |
| SL/TP modification | `modify_sl()` | cerebus_live_bridge.py |
| Auto-trading status | `check_autotrading()` via `terminal_info().trade_allowed` | cerebus_live_bridge.py |
| Logging | module `log` | cerebus_live_bridge.py |
| Account guarding | `AccountGuard` (mode/environment detection, `verify_demo_identity`) | account_guard.py |
| Process monitoring | PID file / `is_pid_alive` / `start_process` / `kill_by_pid` | cerebus_guardian.py |
| Strategy health monitor | positions/orders by magic + tick PnL | cerebus_monitor.py |
| Generic execution layer | `MT5ExecutionLayer` (normalize_price, stop-distance, existing-position/pending-order checks) | execution_layer.py |

---

## C. Reusable / strategy-specific / unsafe / unknown classification

### REUSABLE_TRANSPORT (extract into `quant-lab/live/` at R1)
- MT5 initialize / explicit login / account_info / shutdown / terminal status / auto-trading.
- Symbol existence, visibility, `symbol_select`, digits, point, `volume_min/max/step`,
  `contract_size`, `trade_stops_level`, filling-mode enumeration.
- Tick retrieval (bid/ask), M5 bar retrieval (with tz-aware raw broker timestamps).
- `positions_get` / `orders_get` filtered by magic + comment.
- Market order placement with explicit volume/comment/magic + bounded fill-mode fallback
  (IOC→FOK→RETURN).
- Close-by-ticket with post-close existence confirmation.
- Account guard (mode detection + demo-identity verification) — reused for R9's fail-closed
  demo gate.
- Process supervision (guardian) — reused for R7/R10 operational health.

### LEGACY_STRATEGY_SPECIFIC (must NOT leak into TB)
- `SymmetryTrapEngine` import and its `Bar`/`TradeDirection` types.
- Profit-lock SL ontology ("SL = impulse bar high/low ABOVE/BELOW entry — a PROFIT LOCK").
- Bridge RR gate (`MIN_RR = 1.0` reject).
- `no_sl` touch/wick exit path (engine-monitored SL).
- Impulse-extreme SL/TP derivation.
- Asian-Range / tier / AU / FLOOR-mode configs (`demo_deploy_config.py`, `clean_bridge.py`).
- P90 trailing stop, P90 cascade tiers, symmetry-trap trailing.
- Hardcoded legacy magic numbers `20260601` (ST bridge), `20260531`/`20260532` (monitor),
  and the TOP8/TOP7 `.PRO` pair lists.
- `check_trailing_stop(active_trades, trail_pips=2.0)`.

### UNSAFE / DEPRECATED (do not reuse without replacement)
- Hardcoded account JSON paths + `live_account.json`/`demo_account.json` credentials handling —
  replace with env-var + config-file indirection (R9 safety gates).
- `cerebus_live.py` / `.v2.backup` and `archive/` copies — historical, not the forward template.
- Magic-number collisions across strategies (ST/P90/TB must be namespaced; TB uses `31082026`).

### UNKNOWN (must be resolved by inspection at the checkpoint that needs them)
- Exact broker account(s) currently configured and their trade_mode (demo vs live) — R9 must
  re-verify, never assume.
- Whether the broker supports netting or hedging for this account — `account_mode.json` says
  hedging → magic/ticket isolation; netting-with-overlap → fail closed.

---

## D. Broker symbol resolution

- Legacy ST bridge uses `.PRO` suffixes: `EURJPY.PRO … GBPAUD.PRO, GBPNZD.PRO, …`.
- TB frozen data uses unsuffixed canonical names, but the TB execution seal resolves to
  `GBPAUD.PRO`, `GBPNZD.PRO`, `AUDNZD.PRO` (contract specs in `neutrality_gate.json`).
- `demo_deploy_config.py` uses `.DEMO` for crypto demo symbols — evidence that the suffix is
  **not** universal; it must be resolved per-symbol at runtime.
- **Resolution logic to implement at R1/R2 (deterministic, not assumed):** for each canonical
  symbol, probe `mt5.symbol_info()` over an ordered candidate list `[GBPAUD, GBPAUD.PRO,
  GBPAUD.DEMO]`, require `visible` + non-null tick + valid metadata, and fail closed if no
  candidate resolves. Never silently substitute a different currency pair.

---

## E. Dependency graph (target architecture)

```
research truth (sealed, frozen)
   ├─ tb_p5_validate.py / verify_tb_04a.py / tb_p6_anatomy.py / tb_p7_convergence.py
   └─ canonical_trade_log.csv + bar_parity.csv + strategy_freeze.json

strategy functions (imported, never duplicated)
   └─ basis, rolling-z, entry/exit/reset, exposure_matrix, project_basket (TB-B)

MT5 infrastructure (transport, no strategy)
   ├─ quant-lab/live/mt5_connection.py   (login/shutdown/reconnect/status)
   ├─ quant-lab/live/mt5_symbols.py      (metadata, suffix resolution)
   ├─ quant-lab/live/mt5_market_data.py  (ticks/bars, tz-aware)
   ├─ quant-lab/live/mt5_execution.py    (order_check, market orders, fill fallback)
   ├─ quant-lab/live/mt5_positions.py    (list/by-ticket/by-magic/close)
   └─ quant-lab/live/execution_logging.py

NEW TB-specific layers (quant-lab/tb_live/)
   ├─ market_data.py + snapshot.py        → TriangleSnapshot (fail-closed 3-leg quote)
   ├─ strategy.py / state.py / signals.py → BasketSignal (NO_SIGNAL/ENTRY/EXIT/RESET/INVALID_DATA)
   ├─ sizing.py + exposure.py             → TB-B weights → notional → lots (neutrality gate)
   ├─ basket.py / coordinator.py / order_plan.py → atomic 3-leg basket state machine
   ├─ persistence.py / reconciliation.py  → append-only ledger + restart reconcile
   └─ execution adapters                  → Shadow / Demo / (locked) Live

forbidden legacy logic (never imported by TB)
   └─ SymmetryTrapEngine, P90, Asian Range, AU tiers, profit-lock SL, RR gate, trailing
```

Strategy package must not import MT5. MT5 transport must not import TB strategy. The
coordinator may depend on both via interfaces.

---

## F. Prior-art TB-live inventory (reuse / audit / supersede)

A prior agent built much of the deployment stack already. At each later checkpoint these must
be deliberately reused, audited, or replaced — **not silently re-implemented**:

| Prior-art file | Maps to checkpoint | Status for TB forward |
|---|---|---|
| `engines/triangular_execution_contract.py` | R4 (sizing/exposure) | strong candidate to reuse (typed contract, model_weight→notional→lots, neutrality assess) |
| `mt5/triangular_execution_layer.py` | R5 (atomic coordinator) | strong candidate (state machine, 3-fill verification, BROKEN_HEDGE flatten) |
| `mt5/triangular_basis_executor.py` | R7 (shadow runner) | candidate (thin orchestration, shadow/trade modes) |
| `engines/triangular_basis_live.py` | R3 (strategy wrapper) | candidate (delegates to canonical engine) |
| `engines/tb_live_parity.py` | R3/R8 (parity) | reuse (already proves run_backtest vs process_snapshot parity) |
| `engines/tb_live_exec_sim.py` | R5 (test harness) | reuse (mock MT5 failure scenarios) |
| `engines/tb_live_exec_seal.py` | R9 (broker seal) | reuse/audit (real order_check preflight) |
| `engines/tb_live_shadow_04a.py` | R7 (shadow) | reuse/audit |
| `artifacts/triangular_basis/live/execution/*` | R4/R5/R6/R8/R9 evidence | frozen broker facts + test results to build on |

**R0 does not modify or certify any of this prior art** — it is recorded here so the program
can decide at each checkpoint whether to reuse (with tests), audit (fix defects), or supersede.

---

## G. R0 scaffold

- `quant-lab/tb_live/` — created (empty package marker + README; **no live logic**).
- `research/tb_forward/` — created (this map + truth lock).

---

## H. Open risks carried into R1+

1. Legacy bridge credentials are stored in JSON under `quant-lab/mt5/`; R1 must not copy that
   pattern — use env/config indirection.
2. The `.PRO` suffix is broker-specific; R2 must resolve it at runtime per symbol.
3. The drifted `triangular_basis_engine.py` (100/3.0/5.0) must not be imported by R3 as the
   strategy source — R3 imports `verify_tb_04a` + the sealed `tb_p5/tb_p6/tb_p7` functions.
4. Prior-art TB-live files have not been independently certified in this program yet; R1–R9
   must treat them as untrusted inputs until their tests pass against the frozen truth.

---

**SCIENTIFIC CHANGES: NONE.** **EXECUTION AUTHORIZATION: NOT AUTHORIZED.**
