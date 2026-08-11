# EURCHF Triangular Basis v1 — Backtest Report

Generated: 2026-08-09T11:54:07

**Universe:** EURUSD, USDCHF, EURCHF (MT5 PRO daily)
**Period:** 2015-10-11 → 2026-06-11 (2912 bars)
**Basis:** ln(EURCHF) - ln(EURUSD) - ln(USDCHF)

## Baseline Parameters (spec §6)

| Param | Value |
|-------|-------|
| z_window | 90 |
| z_min_periods | 60 |
| hl_window | 120 |
| max_half_life | 25.0 |
| corr_window | 30 |
| corr_min_periods | 20 |
| min_corr | -0.5 |
| entry_z | 2.0 |
| exit_z | 0.3 |
| stop_z | 3.5 |
| max_hold | 20 |
| cost_per_position_change | 0.0006 |
| use_vol_kill | False |
| vol_win | 20 |
| vol_pct | 0.95 |

## Daily Results

| Metric | Value |
|--------|-------|
| n_bars | 2911 |
| n_trades | 326 |
| cum_gross | 0.008031193316557567 |
| cum_net | -0.38316880668344033 |
| ann_sharpe_net | -6.07961982396961 |
| ann_sortino_net | -6.515229602150298 |
| max_dd_net | -0.38316880668344033 |
| avg_daily_net | -0.0001316278964903615 |
| avg_daily_gross | 2.758912166457426e-06 |
| cost_drag | 0.3911999999999979 |
| win_rate | 0.018404907975460124 |
| avg_trade_net | -0.0011759730699545316 |
| median_trade_net | -0.0011979983817048776 |
| avg_trade_gross | 2.4026930045468296e-05 |
| avg_hold_bars | 2.558282208588957 |
| max_hold_bars | 13.0 |
| avg_mae | 0.0001398991778876346 |
| max_mae | 0.0023288707576146735 |

## Per-Year

| Year | Net | Trades | Sharpe |
|------|-----|--------|--------|
| 2015 | 0.0000 | 0 | 0.00 |
| 2016 | -0.0420 | 35 | -8.06 |
| 2017 | -0.0147 | 12 | -4.47 |
| 2018 | -0.0368 | 31 | -8.16 |
| 2019 | -0.0572 | 50 | -10.21 |
| 2020 | -0.0423 | 36 | -7.54 |
| 2021 | -0.0458 | 38 | -6.71 |
| 2022 | -0.0294 | 28 | -3.32 |
| 2023 | -0.0283 | 24 | -6.46 |
| 2024 | -0.0425 | 35 | -8.85 |
| 2025 | -0.0390 | 32 | -4.87 |
| 2026 | -0.0051 | 4 | -4.13 |

## Robustness Sweep (spec §10)

> Each row varies ONE parameter around baseline; checks directionally-stable behavior.

### z_window

- values: `60, 90, 120`
- cum net: `-0.3942, -0.3832, -0.4055`

### entry_z

- values: `1.8, 2.0, 2.2, 2.5`
- cum net: `-0.4209, -0.3832, -0.3590, -0.3123`

### exit_z

- values: `0.0, 0.3, 0.5`
- cum net: `-0.3702, -0.3832, -0.3955`

### stop_z

- values: `3.0, 3.5, 4.0`
- cum net: `-0.3909, -0.3832, -0.3800`

### max_hold

- values: `10, 15, 20, 30`
- cum net: `-0.3844, -0.3832, -0.3832, -0.3832`

### max_half_life

- values: `15, 20, 25, 30`
- cum net: `-0.3832, -0.3832, -0.3832, -0.3832`

### min_corr

- values: `-0.4, -0.5, -0.6`
- cum net: `-0.3918, -0.3832, -0.3556`

### cost_per_position_change

- values: `0.0003, 0.0006, 0.001`
- cum net: `-0.1876, -0.3832, -0.6440`

## Interpretation

> **Anti-overfit fail-fast check (spec §9):** if gross survives but net dies at 6-10bps costs, the strategy is NOT ready. Review before forward-testing.

### VERDICT: NOT READY (fail-fast, spec §9)

**The gross edge is essentially zero — costs are not the only reason it fails.**

| Quantity | Value | Note |
|----------|-------|------|
| Cum gross (10.7y) | +0.0080 | ≈ +0.24 bps per trade gross |
| Cum net @ 6bps | **-0.383** | every year 2016-2026 negative |
| Gross win fraction (per held-bar) | 52.4% | barely above a coin flip |
| Avg \|Δbasis\| on held bars | 2.7 bps | tiny excursion to capture |
| Net edge per held bar | ~0.16 bps | no exploitable mean reversion |
| Avg hold | 2.56 bars | short (spec desired) but not profitable |
| Max DD (net) | -0.383 | monotone decline |

### Diagnosis

1. **The no-arbitrage identity is tight**: `mean|EURCHF/(EURUSD·USDCHF)-1| ≈ 0.017%`
   and `basis std ≈ 3 bps`. The triangle is internally consistent (data is good),
   but the departures are tiny.
2. **Mean reversion is real but weak at daily frequency**: per-bar win fraction
   52.4%, but average |basis move| on a held bar is only ~2.7 bps — far below the
   6bps (12bps round-trip) cost of acting on it.
3. **Cost drag (0.391) exceeds total gross (0.008) by ~49×.** This is precisely the
   §9 fail-fast condition: gross survives only trivially, net dies.
4. **Not overfit — the opposite.** No single parameter neighborhood is profitable.

### Robustness sweep (spec §10): uniformly negative

Every parameter neighborhood produced negative cum net:
- `z_window {60,90,120}` → all ≈ -0.38 to -0.41
- `entry_z {1.8,2.0,2.2,2.5}` → all -0.31 to -0.42
- `exit_z {0,0.3,0.5}`, `stop_z {3,3.5,4}`, `max_hold {10,15,20,30}`,
  `max_half_life {15,20,25,30}`, `min_corr {-0.4,-0.5,-0.6}` → all negative
- Only `cost` changes the magnitude monotonically (`-0.19 → -0.64`), confirming
  the result is **cost-driven**, not a parameter artifact.

### Spec §9 applicability

Spec: *"If gross returns look good but disappear after 6-10 bps costs, the
strategy is not ready."* Here gross never looked good even before costs. The
strategy does not produce a robust net edge on **daily** EURUSD/USDCHF/EURCHF.

### Recommendation

- **Do NOT forward-test this daily-frequency v1.** Gross lacks edge; net is
  decisively negative and cost-dominated.
- **Potential follow-ons (research-only):**
  1. **Higher frequency (4H / M5)** — mean-reversion edges typically weaken with
     bar length; if present, they are usually stronger intraday. Requires the
     shorter `EURCHF_PRO_M5` panel (full 2015+ D1 exists, M5 may be thinner).
  2. **Wider triangle set** — the lab's existing GBPAUD/GBPNZD/AUDNZD triangle
     already trades a mean-reversion basis with sessions/hard-exit; compare.
  3. **Verification gate** — do not revisit daily until a higher-frequency or
     cost-adjusted variant shows gross >> 12bps round-trip per trade.
- The engine, tests, and sweep harness are left in place for a fast 4H rerun.