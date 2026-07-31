# Progress: ST Phase 2 — Metals & Crypto Group Report

**Date:** 2026-05-31
**Worker:** subagent (st-phase2-metals-crypto)
**Status:** ✅ COMPLETE

---

## Task Summary
Generated grouped backtest report + Monte Carlo simulation for the Metals + Crypto group
(XAUUSD, XAGUSD, BTCUSD, ETHUSD) using the CEREBUS Symmetry Trap Engine B.

## Actions Taken
1. Read all 4 MC results JSON files from `quant-lab/reports/per-asset/`
2. Read all 4 full report files (`*_full_report.md`)
3. Built combined 1954-trade pooled MC simulation (Python, 10K iterations, seed=42)
4. Computed aggregate stats, blended WR, combined PF, Sharpe, DD distribution, ruin probability
5. Generated markdown report: `quant-lab/reports/groups/metals_crypto_report.md`
6. Generated MC results JSON: `quant-lab/reports/groups/metals_crypto_mc_results.json`

## Key Results
| Metric | Value |
|--------|-------|
| Total Pooled Trades | 1,954 |
| Blended Win Rate | 91.25% |
| Combined Profit Factor | 24.21 |
| Combined Sharpe | 7.97 |
| Combined Gross PnL | +169,057 pips |
| Median Max DD | 1.71% |
| Worst Max DD | 13.56% |
| Ruin Probability | 0.00% |

## Per-Asset Highlights

| Asset | Trades | WR | PnL (pips) | PF | Sharpe | Max DD |
|-------|--------|-----|------------|-----|--------|--------|
| XAUUSD | 604 | 84.4% | +7,187.7 | 7.42 | 11.28 | 0.12% |
| XAGUSD ⚠️ | 2 | 50.0% | +2.5 | 26.00 | 10.39 | 0.00% |
| BTCUSD | 801 | 92.6% | +152,304.3 | 26.52 | 13.00 | 0.78% |
| ETHUSD | 547 | 96.9% | +9,562.5 | 50.34 | 24.04 | 0.03% |

## Flags
- **⚠️ XAGUSD: Only 2 trades** — statistically meaningless. Flagged prominently in report.
- **BTCUSD concentration: 90.1% of group PnL** from single asset.
- **Crypto correlation risk**: BTC+ETH correlated drawdown potential identified.

## Files Written
| File | Path |
|------|------|
| Markdown Report | `quant-lab/reports/groups/metals_crypto_report.md` |
| MC Results JSON | `quant-lab/reports/groups/metals_crypto_mc_results.json` |
| MC Python Script | `quant-lab/reports/groups/metals_crypto_mc_sim.py` |

## No Engine Code Modified
✅ Confirmed: No engine code was touched. Read-only operation on strategy files.

## Notes
- MC simulation uses full universe shuffle (1954 trades randomized across assets)
- Total PnL is invariant across sims (same trade set); DD varies by ordering
- Equity curve bands widen through mid-section (widest ~trade 1000) then narrow
- Report includes tier breakdown, per-asset analysis, recommendations, and data quality appendix
