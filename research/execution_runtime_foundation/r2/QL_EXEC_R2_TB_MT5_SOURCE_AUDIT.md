# QL-EXEC-R2 TB MT5 SOURCE AUDIT

Studied (read-only) canonical TB MT5 surfaces at authority
`d12005988ce61170d9bc5478089baa5ce54cc2a9`. No TB file was modified.

## Canonical surfaces
| File | Role | MT5 functions |
|---|---|---|
| `quant-lab/runtime/tb_worker.py` | worker / demo identity / broker truth | initialize, shutdown, account_info, terminal_info, positions_get, orders_get, history_deals_get |
| `quant-lab/engines/tb_r6_demo_canary.py` | DemoEnvironment: identity gate, symbol contracts, fill-mode probe, quote health, clock | account_info, terminal_info, symbol_info, symbol_info_tick, symbol_select, order_check, order_send, copy_rates_from_pos |
| `quant-lab/mt5/triangular_execution_layer.py` | basket execution: order build, precheck, retry, close, reconcile | symbol_info, symbol_info_tick, order_check, order_send, positions_get, history_deals_get |
| `quant-lab/mt5/execution_layer.py` | legacy single-strategy execution (reference only) | symbol_info, symbol_info_tick, order_send, positions_get, orders_get, copy_rates_from_pos |
| `quant-lab/tb_live/snapshot.py` | MT5MarketDataAdapter: data + symbol info only | initialize, shutdown, terminal_info, symbol_info, symbol_select, symbol_info_tick, copy_rates_from_pos |
| `quant-lab/tb_live/full_engine.py` | durable triangular engine (orchestration) | (via adapter) |

## Key extracted mechanics
1. **Identity gate**: `account_info()` + `terminal_info()`; trade_mode int
   `{0: DEMO, 1: CONTEST, 2: REAL}`; company (case-insensitive substring),
   server, currency, trade_allowed, terminal_trade_allowed, tradeapi_disabled.
2. **Clock calibration**: `off = tick.time - now`; adopt only `|off| < 12h`;
   stale/missing tick retains prior calibration.
3. **Tick normalization**: bid>0, ask>0, ask>=bid => valid; spread = ask - bid
   (the historical `spread_points=bid-ask` negative-spread expression is NOT
   carried forward).
4. **Bar normalization**: raw MT5 bar time = BAR OPEN time (preserved
   verbatim); supports dict AND numpy structured records; volume =
   real_volume else tick_volume.
5. **Fill mode**: TB probes order_check with type_filling 1(FOK)/2(IOC)/0(RETURN)
   rather than trusting `filling_mode` bits; success retcodes 0 or 10009.
6. **Retcode success**: `int(retcode) in (0, 10009)`; None => failure.
7. **Comment bound**: comments >= 30 chars make this broker return None from
   order_check; bounded to 29 chars with deterministic 16-char reduction for
   long ids.
8. **Order request**: action DEAL, volume lots, type BUY(0)/SELL(1), price
   ask(BUY)/bid(SELL), deviation (TB used 20 points), magic, comment,
   type_filling.
9. **history_deals_get**: requires NAIVE UTC datetimes (int/aware args return
   nothing).

## What was NOT copied
- `model_weight_to_notional`, `notional_to_mt5_lots` (strategy sizing)
- `_size_legs`, `_neutrality_preflight`, basket state machine (above transport)
- `leg_sides` / triangular symbols / weights / z thresholds (strategy science)
