# TB-R2 — Synchronized Market-Data Protocol

**Checkpoint:** TB-R2-SYNCHRONIZED-MARKET-DATA
**Branch:** `tb-forward-engine`
**Base:** `2181c4832e760caf873ca93a0ed6d7ac1b1b5480` (TB-R1.1)
**Canonical research:** `6769ad31ac737946dae54e3660e22cb36f72e2b7`
**Execution authorization:** `NOT_AUTHORIZED`

---

## 1. Purpose

Build the missing synchronized three-leg market-data layer for the TB forward
engine. The prior stack could consume three bars, but it did not prove that
the three legs represent the **same closed signal interval**, nor that
execution quotes are fresh/synchronous enough to translate a basket intent.

This checkpoint is **market-data plumbing only** — no strategy math, no
scientific changes, no broker orders.

## 2. Core design rule

**Signal generation stays CLOSED-M5-BAR based.**

- Live ticks are used ONLY for execution pricing, quote freshness, spread
  measurement, and synchronization safety.
- Ticks NEVER enter the basis/z computation and can never turn the strategy
  into a tick-entry model (proven by test
  `strategy_gets_closed_bar_and_ticks_do_not_enter_basis`).

## 3. Two snapshots, never conflated

| Snapshot | Content | Used for |
|---|---|---|
| `TriangleSignalSnapshot` | 3 CLOSED M5 bars at the **same** signal timestamp | basis / z / entry / exit / weights |
| `TriangleExecutionSnapshot` | 3 fresh bid/ask ticks immediately before order translation | execution pricing, freshness, skew |

BAR PRICE ≠ EXECUTION BID/ASK.

## 4. Timestamp semantics (frozen, parity-preserving)

- MT5 `copy_rates*` returns bar timestamps in **server time**; the timestamp is
  the bar **OPEN time**.
- The canonical research CSVs (`GBPAUD_M5.csv`, `GBPNZD_M5.csv`,
  `AUDNZD_PRO_M5.csv`) carry exactly those raw open-time timestamps, and the
  sealed pipeline applies the session rule `est_hour = (hour - 5) % 24`
  **directly** (never +5 min).
- **The strategy key is the raw MT5 bar open time, used verbatim.**
  `bar_close_time = bar_open_time + 300s` is computed only for freshness math.
- R2 does **not** add +5min to the strategy key — doing so would shift session
  classification and break the sealed parity (proven: 265,809 bars → 194/405
  events, 0 mismatches).

## 5. Synchronization algorithm

`SynchronizedTriangleFeed.get_synchronized_closed_triangle(reference_time)`:

1. resolve broker symbols (runtime, locked);
2. fetch recent bars per leg;
3. keep only bars **closed by the reference time**
   (`bar_close_time <= reference_time`) — the forming bar is excluded by time,
   never by list position;
4. intersect timestamps across the three legs; the latest common closed bar is
   selected;
5. per-leg lag gate: the selected bar must be within `max_signal_bar_lag_bars`
   (1) of the newest closed bar available for that leg;
6. OHLC sanity + staleness gate (`max_signal_bar_age_s`);
7. dedup: one strategy evaluation per new synchronized closed bar.

## 6. Fail-closed gates

Signal snapshot invalid if: missing leg, no common closed bar, forming bar,
stale signal bar, invalid OHLC (NaN/inf/nonpositive/high<low/close outside
range), timestamp mismatch, per-leg duplicate bar.

Execution snapshot invalid if: invalid quote (bid ≤ 0, ask ≤ 0, ask < bid),
stale quote (> `max_quote_age_ms`), cross-leg skew
(> `max_cross_leg_skew_ms`), clock regression, symbol unavailable,
broker disconnected.

## 7. Configuration (centralized, provisional)

`TBMarketDataConfig` holds every threshold. These are
**PROVISIONAL_EXECUTION_SAFETY_LIMITS** — engineering defaults, NOT validated
scientifically, NOT tuned against PnL:

| Parameter | Default | Note |
|---|---|---|
| `timeframe` / `bar_seconds` | M5 / 300 | frozen |
| `max_signal_bar_lag_bars` | 1 | >1 bar behind ⇒ invalidate |
| `max_signal_bar_age_s` | 600 | 2 M5 bars, provisional |
| `max_quote_age_ms` | 2000 | provisional |
| `max_cross_leg_skew_ms` | 1000 | provisional |
| `spread_gate_mode` | `spread_monitor_only` | no invented optimal spread limits |
| `clock_regression_tolerance_ms` | 5000 | flag older-than-previous ticks |
| `canonical_timezone_semantics` | `FIXED_UTC_MINUS_5` | never DST-corrected |

## 8. Adapters

- `MT5MarketDataAdapter` — data + symbol-info ONLY (no order functions exist in
  the class by construction; test `mt5_adapter_exposes_no_order_functions`).
- `MockMarketDataAdapter` / replay adapter — deterministic; all R2 tests run
  against mocks (no MT5 terminal required for PASS).
- `MarketDataAdapter` Protocol: `get_recent_bars`, `get_tick`, `symbol_info`,
  `server_time`, `shutdown`.

## 9. Symbol resolution

`SymbolResolver` probes candidate suffixes (`""`, `.PRO`, `m`, `.raw`, `.stp`,
`.a`) at runtime, requires valid metadata + tradeable `trade_mode` +
`contract_size > 0`, then **locks** the mapping for the process lifetime.
Never assumed; never silently re-mapped. `.PRO` is the expected live suffix
but resolution is runtime-verified (test `L_symbol_suffix_resolution`).

## 10. Zero-order guarantee

Fresh valid signal + fresh valid ticks + valid weights still result in
**ZERO broker orders** during R2 (test
`fresh_signal_fresh_ticks_valid_weights_produce_zero_orders`). The executor
remains fail-closed: default mode SHADOW, `EXECUTION_AUTHORIZED = False`,
demo not authorized.

## 11. Health states

`HEALTHY`, `WAITING_FOR_BAR_SYNC`, `STALE_SIGNAL_DATA`,
`STALE_EXECUTION_QUOTES`, `BROKER_DISCONNECTED`, `SYMBOL_UNAVAILABLE`,
`INVALID_MARKET_DATA` — written to shadow logs via `TriangleSnapshotHealth`.

## 12. Code layout

```
quant-lab/tb_live/market_data.py        typed contract + validation + config
quant-lab/tb_live/snapshot.py           adapters, SymbolResolver, feed
quant-lab/tb_live/snapshot_capture.py   rolling capture CLI (audit)
quant-lab/mt5/triangular_basis_executor.py  R2 feed wired into shadow loop
quant-lab/engines/tb_r2_parity.py       historical replay parity harness
quant-lab/engines/tb_r2_tests.py        R2 test suite (26 tests)
```

Reproduce:

```bash
python quant-lab/engines/tb_r2_tests.py   # 26/26
python quant-lab/engines/tb_r2_parity.py  # 194/405 parity + leakage audit
```
