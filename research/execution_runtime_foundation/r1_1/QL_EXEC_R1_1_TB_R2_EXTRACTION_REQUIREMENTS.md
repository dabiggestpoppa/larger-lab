# QL-EXEC-R1.1 TB R2 EXTRACTION REQUIREMENTS

Precise handoff for R2 `MT5BrokerSession` extraction. READ-ONLY inventory;
no MT5 adapter is implemented in R1.1.

TB engineering authority: `d12005988ce61170d9bc5478089baa5ce54cc2a9`
(R6.1B worker state-latch fix; strategy math unchanged).

Canonical TB runtime MT5 surfaces (validated path):
- `quant-lab/runtime/tb_worker.py`
- `quant-lab/engines/tb_r6_demo_canary.py`
- `quant-lab/mt5/triangular_execution_layer.py`
- `quant-lab/mt5/execution_layer.py`
- `quant-lab/tb_live/snapshot.py`
- `quant-lab/tb_live/full_engine.py`

## MT5 function -> generic BrokerSession mapping

| MT5 function | Source (canonical path) | Generic method | Normalized output | Side effects | Failure semantics | R2 tested | Broker execution |
|---|---|---|---|---|---|---|---|
| initialize | tb_worker.py, tb_r6_demo_canary.py | connect | bool | terminal attach | fail closed / retcode | yes | no (connect only) |
| shutdown | tb_worker.py, tb_r6_demo_canary.py | disconnect | None | terminal detach | best-effort | yes | no |
| terminal_info | tb_r6_demo_canary.py | identity (partial) | BrokerIdentity (company/server/path) | none | fail closed | yes | no |
| account_info | tb_worker.py, tb_r6_demo_canary.py | account_state | AccountState | none | fail closed | yes | no |
| symbol_info | tb_r6_demo_canary.py, snapshot.py | symbol_info | SymbolInfo | none | fail closed | yes | no |
| symbol_select | tb_r6_demo_canary.py | ensure_symbol | bool | makes symbol available | no-op success where unsupported | yes | no |
| symbol_info_tick | tb_r6_demo_canary.py, snapshot.py | tick | Tick | none | fail closed | yes | no |
| copy_rates_from_pos | tb_r6_demo_canary.py, snapshot.py | bars | list[Bar] | none | fail closed / empty | yes | no |
| positions_get | tb_worker.py, triangular_execution_layer.py | positions | list[Position] | none | fail closed | yes | no |
| orders_get | tb_worker.py | orders | list[Order] | none | fail closed | yes | no |
| history_deals_get | tb_worker.py, triangular_execution_layer.py | deals | list[Deal] | none | fail closed | yes | no |
| order_check | triangular_execution_layer.py, execution_layer.py | order_check | CheckResult | none | fail closed | yes | no |
| order_send | triangular_execution_layer.py, execution_layer.py | submit_order | SubmitResult | order submit | retcode normalization | yes | YES (isolated/demo only) |
| last_error | (throughout) | health / result reasons | normalized error text | none | fail closed | yes | no |

Additional MT5 calls to preserve for parity (bounded):
- `login` (terminal session attach; external-session model)
- `copy_rates_range`, `copy_ticks_range`, `copy_rates_from` (data parity)
- `symbols_get` (symbol universe)
- `history_orders_get` (order history)

## Critical preservation requirements (R2)
1. Raw source bar timestamp semantics: MT5 bar time == BAR OPEN time.
2. Server-clock calibration (offset) for closure/freshness.
3. Real MT5 numpy record handling (normalize to broker-neutral value objects).
4. `order_check` before `order_send`.
5. Broker fill-mode behavior (request vs position fills).
6. Retcode normalization to generic failure semantics.
7. Ownership metadata (magic/comment) mapping from `OwnershipNamespace`.
8. Broker-truth verification after submission.

## R2 contract discovery
| Contract | Status |
|---|---|
| OrderIntent | R2_BOUNDED_EXTENSION_REQUIRED (price/fill-mode/slippage fields) |
| SymbolInfo | NO_CHANGE_REQUIRED |
| Tick | NO_CHANGE_REQUIRED (source timestamp preserved) |
| Bar | NO_CHANGE_REQUIRED (source timestamp preserved) |
| BrokerIdentity | NO_CHANGE_REQUIRED |
| BrokerCapabilities | NO_CHANGE_REQUIRED (symbol activation added in R1.1) |
| BrokerSession | NO_CHANGE_REQUIRED (ensure_symbol/clock_state added in R1.1) |

## R2 non-negotiables
- Injected / fake MT5 module + replay fixtures + isolated tests FIRST.
- Any real terminal smoke test requires separate explicit authorization.
- No active-deployment switch; no automatic migration of the live TB runtime.
- Include the d120 market-recovery regression (ONLINE_MARKET_CLOSED ->
  recovery -> FLAT/OPEN state recomputation) in R2/R4 parity.
