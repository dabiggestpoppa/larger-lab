# CEREBUS Symmetry Trap — Master Report Index
> **Generated:** 2026-05-31 01:45 EDT
> **Engine:** CEREBUS Symmetry Trap v4.0 (Model B, 4-state FSM)
> **Scope:** 19 assets, ~17,700+ individual trades, 12,488 pooled multi-asset trades

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Assets Tested | 19/20 (NAS100 skipped — no MT5 data) |
| Total Individual Trades | ~17,700+ |
| Pooled Multi-Asset Trades | 12,488 |
| Blended Win Rate | 81.2% |
| Combined Profit Factor | 26.58 |
| Combined Sharpe | 4.72 |
| MC Ruin Probability | 0.62% |
| Best Asset (WR) | ETHUSD — 96.9% |
| Best Asset (PF) | ETHUSD — 50.34 |
| Best Asset (Sharpe) | ETHUSD — 24.04 |
| Worst Asset | XAGUSD — 2 trades, 50% WR (config issue) |

---

## Reports Directory

### 1. Per-Asset Reports (`per-asset/`)
Full individual backtest + Monte Carlo for each asset.

| Asset | Trades | WR | PF | Sharpe | MaxDD | MC Ruin | Report |
|-------|--------|----|----|--------|-------|---------|--------|
| ETHUSD | 547 | 96.9% | 50.34 | 24.04 | 31.7p | 0.00% | [EURUSD](per-asset/ETHUSD_full_report.md) |
| HK50 | 385 | 94.0% | 40.30 | 20.42 | 149.7p | 0.00% | [HK50](per-asset/HK50_full_report.md) |
| NZDUSD | 727 | 93.3% | 19.02 | 18.31 | 54.3p | 0.00% | [NZDUSD](per-asset/NZDUSD_full_report.md) |
| BTCUSD | 801 | 92.6% | 26.52 | 13.00 | 785p | 0.00% | [BTCUSD](per-asset/BTCUSD_full_report.md) |
| US500 | 372 | 91.7% | 13.95 | 12.02 | 116.8p | 0.00% | [US500](per-asset/US500_full_report.md) |
| GBPCHF | 803 | 91.2% | 24.51 | 17.74 | 22.7p | 0.00% | [GBPCHF](per-asset/GBPCHF_full_report.md) |
| AUDUSD | 828 | 89.3% | 18.47 | 16.73 | 23.3p | 0.00% | [AUDUSD](per-asset/AUDUSD_full_report.md) |
| GBPAUD | 715 | 88.4% | 14.97 | 14.77 | 60.1p | 0.00% | [GBPAUD](per-asset/GBPAUD_full_report.md) |
| GBPNZD | 664 | 88.4% | 20.87 | 15.83 | 46.2p | 0.00% | [GBPNZD](per-asset/GBPNZD_full_report.md) |
| USDJPY | 729 | 87.8% | 16.73 | 13.76 | 42.3p | 0.00% | [USDJPY](per-asset/USDJPY_full_report.md) |
| FR40 | 1,085 | 87.0% | 12.21 | 13.63 | 107.7p | 0.00% | [FR40](per-asset/FR40_full_report.md) |
| CHFJPY | 751 | 86.3% | 13.01 | 11.17 | 87.5p | 0.00% | [CHFJPY](per-asset/CHFJPY_full_report.md) |
| GBPJPY | 830 | 86.3% | 12.61 | 14.05 | 61.9p | 0.00% | [GBPJPY](per-asset/GBPJPY_full_report.md) |
| GBPUSD | 1,259 | 85.7% | 9.23 | 11.89 | 48.5p | 0.00% | [GBPUSD](per-asset/GBPUSD_full_report.md) |
| EURUSD | 1,163 | 85.0% | 8.57 | 11.54 | 39.2p | 0.00% | [EURUSD](per-asset/EURUSD_full_report.md) |
| USDCHF | 1,153 | 84.9% | 8.87 | 11.73 | 57.6p | 0.00% | [USDCHF](per-asset/USDCHF_full_report.md) |
| XAUUSD | 604 | 84.4% | 7.42 | 11.28 | 121.4p | 0.00% | [XAUUSD](per-asset/XAUUSD_full_report.md) |
| DE30 | 1,145 | 82.8% | 9.91 | 12.02 | 134.0p | 0.00% | [DE30](per-asset/DE30_full_report.md) |
| XAGUSD | 2 | 50.0% | — | — | — | — | ⚠️ FLAGGED |

---

### 2. Group Reports (`groups/`)
Combined backtest + Monte Carlo for each asset class group.

| Group | Trades | WR | PF | MC Ruin | Report |
|-------|--------|----|----|---------|--------|
| Majors (6 FX) | ~6,857 | ~86% | ~11 | 0.00% | [Majors](groups/majors_report.md) |
| Crosses (5 pairs) | 3,763 | 88.1% | 15.82 | 0.00% | [Crosses](groups/crosses_report.md) |
| Metals + Crypto | 1,954 | 91.3% | 24.21 | 0.00% | [Metals+Crypto](groups/metals_crypto_report.md) |
| Indices (4) | 2,987 | 86.9% | 15.22 | 0.00% | [Indices](groups/indices_report.md) |

---

### 3. Multi-Asset Combined (`multi_asset/`)
All 19 assets pooled into a single Monte Carlo simulation.

| Metric | Value |
|--------|-------|
| Pooled Trades | 12,488 |
| Blended WR | 81.2% |
| Combined PF | 26.58 |
| MC Median Final PnL | $6.16M (on $10K base) |
| Ruin Probability | 0.62% |
| Profitable Sims | 99.38% |

📄 [Full Multi-Asset Report](multi_asset/multi_asset_full_report.md)

---

### 4. Top Performers Deep-Dive (`top5_majors/`)
Re-run with full reports for top 5 + major 6.

**Top 5 by WR:**
1. ETHUSD — 96.9% WR, PF 50.34
2. HK50 — 94.0% WR, PF 40.30
3. NZDUSD — 93.3% WR, PF 19.02
4. BTCUSD — 92.6% WR, PF 26.52
5. US500 — 91.7% WR, PF 13.95

**Major 6 Aggregate:**
- 5,859 trades | 87.1% WR | PF 11.51 | +32,818 pips
- Combined MC: 100% profitable sims, median +$65,656

📄 [Majors 6 Group Report](top5_majors/majors6_group_report.md)

---

### 5. Sage Orchestration Meditation (`meditation-room/`)
Strategic reflection on orchestration patterns and structural reproducibility.

📄 [Sage Meditation](meditation-room/SAGE_ORCHESTRATION_MEDITATION.md)

---

## Flags & Known Issues

| Issue | Severity | Details |
|-------|----------|---------|
| XAGUSD config | 🔴 High | Only 2 trades — tier thresholds too tight for silver |
| NAS100 missing | 🟡 Medium | No MT5 data available, skipped |
| BTCUSD concentration | 🟡 Medium | 55% of multi-asset PnL from single asset |
| Crypto correlation | 🟡 Medium | BTC + ETH = 58.5% of pool, correlated risk |

---

## Data Source
- **Date Range:** 2022-01-03 to 2026-05-29 (~4.4 years M5 data)
- **Fetch Date:** 2026-05-30
- **Config Injection:** Per-asset configs from `quant-lab/configs/asset_configs.py`
- **Engine:** `quant-lab/engines/symmetry_trap.py` (4-state FSM: SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE)
- **12PM EST Hard Cutoff:** Applied to all backtests (by design)

---

*Index maintained by OWL — CEREBUS FX v4.0*
*Last updated: 2026-05-31 01:45 EDT*
