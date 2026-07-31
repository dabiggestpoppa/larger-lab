# Backtest Campaign Status — 2026-05-31 20:51 EDT

## Problem Diagnosed

The backtest campaign (`run_full_backtest_campaign.py`) returns 0 trades for ALL assets because:

1. **ST Engine**: `SymmetryTrapEngine.__init__()` doesn't accept `kwarg 'pip_value'` — campaign is passing wrong constructor args
2. **P90 Engine**: 
   - Campaign calls `run_p90_backtest()` from `p90_backtest` module — BUT the module function is actually `run_backtest()`
   - Also passes `pip_value` kwarg to `P90Engine.__init__()` which doesn't accept it

### Fix Required:
- Campaign script needs to be corrected to use actual engine APIs
- ST: Instantiate `SymmetryTrapEngine` with correct args, call `process_bar()` per bar
- P90: Import `run_backtest` from `p90_backtest` (not `run_p90_backtest`)
- Both engines have their own constructors — campaign wrapper must match

## Available Data (24 CSV files)
EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, XAUUSD, XAGUSD, BTCUSD, ETHUSD, US500, HK50, GBPJPY, GBPCHF, GBPAUD, GBPNZD, CHFJPY, FR40, DE30

## Previous Results (ST multi-asset, different runner):
- 19 assets, 14,563 trades, 82.8% avg WR
- Top: ETHUSD 96.9% | HK50 94.0% | NZDUSD 93.3% | BTCUSD 92.6%
- Output: `quant-lab/reports/st_multi_asset_results.json`

## Nautilus Backtest Reports (quant-lab/reports/):
Multiple small JSON files (258-441 bytes) suggesting failed/incomplete Nautilus runs
- NAUTILUS_SYMMETRY_TRAP_EURUSD.PRO_*.json (6 files)
- NAUTILUS_P90_EURUSD.PRO_*.json (2 files)
- NAUTILUS_P90_USDCHF.PRO_*.json (10 files)

## NT8 Track A Files (need import + compilation):
All in `tradovate/`:
1. CEREBUS_ST_NT8.cs (22.5KB)
2. CEREBUS_P90_NT8.cs (26KB)
3. CEREBUS_BacktestHarness.cs (12.7KB)
4. CEREBUS_DeployConfig.json (3.2KB)
5. CEREBUS_TradeCopier.cs (7.2KB)
6. CEREBUS_AssetPresets.cs (10.3KB)
7. CryptoAssetScanner.py (separate, in crypto/)

_Last updated: 2026-05-31 20:51 EDT_
