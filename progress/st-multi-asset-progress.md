# Symmetry Trap Multi-Asset Backtest Progress
Started: 2026-06-03 11:36:58

[2026-06-03 11:36:58] ============================================================
[2026-06-03 11:36:58] SYMMETRY TRAP MULTI-ASSET BACKTEST
[2026-06-03 11:36:58] ============================================================
[2026-06-03 11:36:58] Total assets in registry: 20
[2026-06-03 11:36:58] Assets: EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF, XAUUSD, XAGUSD, BTCUSD, ETHUSD, NAS100, US500, DE30, FR40, HK50
[2026-06-03 11:36:58] 
--- STEP 1: Checking existing CSV data ---
[2026-06-03 11:36:58] Found CSV data for 19 assets: EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF, XAUUSD, XAGUSD, BTCUSD, ETHUSD, US500, DE30, FR40, HK50
[2026-06-03 11:36:58] Missing data for 1 assets: NAS100
[2026-06-03 11:36:58] 
--- STEP 2: Attempting MT5 data fetch ---
[2026-06-03 11:36:58]   [MT5] NAS100: symbol not found in MT5 — skipping
[2026-06-03 11:36:58] Successfully fetched 0 assets from MT5: 
[2026-06-03 11:36:58] Still missing data for 1 assets: NAS100
[2026-06-03 11:36:58] 
--- STEP 3: Running Symmetry Trap backtests ---
[2026-06-03 11:36:58] 
>>> EURUSD: EURUSD_M5.csv
[2026-06-03 11:36:58]   Running EURUSD (EUR/USD) | pip_size=0.0001 | csv=EURUSD_M5.csv (15.2MB)
[2026-06-03 11:37:03]   EURUSD (EUR/USD): 886 trades | WR=44.0% | PnL=+155.2p | PF=1.03
[2026-06-03 11:37:03] --- Done: EURUSD ---
[2026-06-03 11:37:03] 
>>> GBPUSD: GBPUSD_M5.csv
[2026-06-03 11:37:03]   Running GBPUSD (GBP/USD) | pip_size=0.0001 | csv=GBPUSD_M5.csv (16.2MB)
[2026-06-03 11:37:09]   GBPUSD (GBP/USD): 997 trades | WR=38.8% | PnL=+240.5p | PF=1.04
[2026-06-03 11:37:09] --- Done: GBPUSD ---
[2026-06-03 11:37:09] 
>>> USDCHF: USDCHF_M5.csv
[2026-06-03 11:37:09]   Running USDCHF (USD/CHF) | pip_size=0.0001 | csv=USDCHF_M5.csv (14.9MB)
[2026-06-03 11:37:14]   USDCHF (USD/CHF): 847 trades | WR=39.9% | PnL=+71.1p | PF=1.02
[2026-06-03 11:37:14] --- Done: USDCHF ---
[2026-06-03 11:37:14] 
>>> USDJPY: USDJPY_M5.csv
[2026-06-03 11:37:14]   Running USDJPY (USD/JPY) | pip_size=0.01 | csv=USDJPY_M5.csv (14.9MB)
[2026-06-03 11:37:19]   USDJPY (USD/JPY): 486 trades | WR=32.5% | PnL=+197.7p | PF=1.06
[2026-06-03 11:37:19] --- Done: USDJPY ---
[2026-06-03 11:37:19] 
>>> AUDUSD: AUDUSD_M5.csv
[2026-06-03 11:37:19]   Running AUDUSD (AUD/USD) | pip_size=0.0001 | csv=AUDUSD_M5.csv (14.7MB)
[2026-06-03 11:37:24]   AUDUSD (AUD/USD): 620 trades | WR=37.9% | PnL=-422.0p | PF=0.88
[2026-06-03 11:37:24] --- Done: AUDUSD ---
[2026-06-03 11:37:24] 
>>> NZDUSD: NZDUSD_M5.csv
[2026-06-03 11:37:24]   Running NZDUSD (NZD/USD) | pip_size=0.0001 | csv=NZDUSD_M5.csv (14.9MB)
[2026-06-03 11:37:28]   NZDUSD (NZD/USD): 547 trades | WR=33.5% | PnL=-518.7p | PF=0.84
[2026-06-03 11:37:28] --- Done: NZDUSD ---
[2026-06-03 11:37:28] 
>>> CHFJPY: CHFJPY_M5.csv
[2026-06-03 11:37:28]   Running CHFJPY (CHF/JPY) | pip_size=0.01 | csv=CHFJPY_M5.csv (14.9MB)
[2026-06-03 11:37:33]   CHFJPY (CHF/JPY): 623 trades | WR=33.7% | PnL=+56.9p | PF=1.01
[2026-06-03 11:37:33] --- Done: CHFJPY ---
[2026-06-03 11:37:33] 
>>> GBPJPY: GBPJPY_M5.csv
[2026-06-03 11:37:33]   Running GBPJPY (GBP/JPY) | pip_size=0.01 | csv=GBPJPY_M5.csv (15.0MB)
[2026-06-03 11:37:37]   GBPJPY (GBP/JPY): 617 trades | WR=36.8% | PnL=+100.4p | PF=1.02
[2026-06-03 11:37:37] --- Done: GBPJPY ---
[2026-06-03 11:37:37] 
>>> GBPAUD: GBPAUD_M5.csv
[2026-06-03 11:37:37]   Running GBPAUD (GBP/AUD) | pip_size=0.0001 | csv=GBPAUD_M5.csv (17.2MB)
[2026-06-03 11:37:43]   GBPAUD (GBP/AUD): 551 trades | WR=35.6% | PnL=-6.1p | PF=1.00
[2026-06-03 11:37:43] --- Done: GBPAUD ---
[2026-06-03 11:37:43] 
>>> GBPNZD: GBPNZD_M5.csv
[2026-06-03 11:37:43]   Running GBPNZD (GBP/NZD) | pip_size=0.0001 | csv=GBPNZD_M5.csv (15.8MB)
