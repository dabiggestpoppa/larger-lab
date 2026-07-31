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
[2026-06-03 11:37:48]   GBPNZD (GBP/NZD): 514 trades | WR=32.9% | PnL=-313.0p | PF=0.94
[2026-06-03 11:37:48] --- Done: GBPNZD ---
[2026-06-03 11:37:48] 
>>> GBPCHF: GBPCHF_M5.csv
[2026-06-03 11:37:48]   Running GBPCHF (GBP/CHF) | pip_size=0.0001 | csv=GBPCHF_M5.csv (15.4MB)
[2026-06-03 11:37:53]   GBPCHF (GBP/CHF): 631 trades | WR=31.2% | PnL=-282.4p | PF=0.93
[2026-06-03 11:37:53] --- Done: GBPCHF ---
[2026-06-03 11:37:53] 
>>> XAUUSD: XAUUSD_M5.csv
[2026-06-03 11:37:53]   Running XAUUSD (XAU/USD) | pip_size=0.1 | csv=XAUUSD_M5.csv (16.6MB)
[2026-06-03 11:37:58]   XAUUSD (XAU/USD): 366 trades | WR=74.9% | PnL=+1511.3p | PF=1.18
[2026-06-03 11:37:58] --- Done: XAUUSD ---
[2026-06-03 11:37:58] 
>>> XAGUSD: XAGUSD_M5.csv
[2026-06-03 11:37:58]   Running XAGUSD (XAG/USD) | pip_size=0.01 | csv=XAGUSD_M5.csv (15.3MB)
[2026-06-03 11:38:03]   XAGUSD (XAG/USD): 469 trades | WR=54.8% | PnL=-409.4p | PF=0.95
[2026-06-03 11:38:03] --- Done: XAGUSD ---
[2026-06-03 11:38:03] 
>>> BTCUSD: BTCUSD_M5.csv
[2026-06-03 11:38:03]   Running BTCUSD (BTC/USD) | pip_size=1.0 | csv=BTCUSD_M5.csv (25.2MB)
[2026-06-03 11:38:11]   BTCUSD (BTC/USD): 582 trades | WR=22.3% | PnL=+6525.0p | PF=1.14
[2026-06-03 11:38:11] --- Done: BTCUSD ---
[2026-06-03 11:38:11] 
>>> ETHUSD: ETHUSD_M5.csv
[2026-06-03 11:38:11]   Running ETHUSD (ETH/USD) | pip_size=1.0 | csv=ETHUSD_M5.csv (24.6MB)
[2026-06-03 11:38:18]   ETHUSD (ETH/USD): 395 trades | WR=19.7% | PnL=-619.9p | PF=0.82
[2026-06-03 11:38:18] --- Done: ETHUSD ---
[2026-06-03 11:38:18] 
>>> US500: US500_M5.csv
[2026-06-03 11:38:18]   Running US500 (US500) | pip_size=1.0 | csv=US500_M5.csv (13.5MB)
[2026-06-03 11:38:22]   US500 (US500): 303 trades | WR=25.7% | PnL=-782.3p | PF=0.64
[2026-06-03 11:38:22] --- Done: US500 ---
[2026-06-03 11:38:23] 
>>> DE30: DE30_M5.csv
[2026-06-03 11:38:23]   Running DE30 (DE30) | pip_size=1.0 | csv=DE30_M5.csv (14.0MB)
[2026-06-03 11:38:27]   DE30 (DE30): 986 trades | WR=37.1% | PnL=+2062.6p | PF=1.20
[2026-06-03 11:38:27] --- Done: DE30 ---
[2026-06-03 11:38:27] 
>>> FR40: FR40_M5.csv
[2026-06-03 11:38:27]   Running FR40 (FR40) | pip_size=1.0 | csv=FR40_M5.csv (13.0MB)
[2026-06-03 11:38:30]   FR40 (FR40): 834 trades | WR=36.7% | PnL=+980.9p | PF=1.17
[2026-06-03 11:38:30] --- Done: FR40 ---
[2026-06-03 11:38:30] 
>>> HK50: HK50_M5.csv
[2026-06-03 11:38:30]   Running HK50 (HK50) | pip_size=1.0 | csv=HK50_M5.csv (13.4MB)
[2026-06-03 11:38:34]   HK50 (HK50): 183 trades | WR=13.7% | PnL=-1537.9p | PF=0.65
[2026-06-03 11:38:34] --- Done: HK50 ---
[2026-06-03 11:38:34] 
--- STEP 4: Generating reports ---
[2026-06-03 11:38:34] Saved JSON results to C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json
[2026-06-03 11:38:34] Saved markdown report to C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_report.md
[2026-06-03 11:38:34] 
--- Verification ---
[2026-06-03 11:38:34]   FLAG EURUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG GBPUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG USDCHF: LOW_WR
[2026-06-03 11:38:34]   FLAG USDJPY: LOW_WR
[2026-06-03 11:38:34]   FLAG AUDUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG NZDUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG CHFJPY: LOW_WR
[2026-06-03 11:38:34]   FLAG GBPJPY: LOW_WR
[2026-06-03 11:38:34]   FLAG GBPAUD: LOW_WR
[2026-06-03 11:38:34]   FLAG GBPNZD: LOW_WR
[2026-06-03 11:38:34]   FLAG GBPCHF: LOW_WR
[2026-06-03 11:38:34]   OK   XAUUSD: WR=74.9% | Trades=366
[2026-06-03 11:38:34]   OK   XAGUSD: WR=54.8% | Trades=469
[2026-06-03 11:38:34]   FLAG BTCUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG ETHUSD: LOW_WR
[2026-06-03 11:38:34]   FLAG US500: LOW_WR
[2026-06-03 11:38:34]   FLAG DE30: LOW_WR
[2026-06-03 11:38:34]   FLAG FR40: LOW_WR
[2026-06-03 11:38:34]   FLAG HK50: LOW_WR
[2026-06-03 11:38:34] 
=== COMPLETE: 19/20 assets backtested ===
