# Symmetry Trap Multi-Asset Backtest Progress
Started: 2026-05-30 23:56:19

[2026-05-30 23:56:19] ============================================================
[2026-05-30 23:56:19] SYMMETRY TRAP MULTI-ASSET BACKTEST
[2026-05-30 23:56:19] ============================================================
[2026-05-30 23:56:19] Total assets in registry: 20
[2026-05-30 23:56:19] Assets: EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF, XAUUSD, XAGUSD, BTCUSD, ETHUSD, NAS100, US500, DE30, FR40, HK50
[2026-05-30 23:56:19] 
--- STEP 1: Checking existing CSV data ---
[2026-05-30 23:56:19] Found CSV data for 19 assets: EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF, XAUUSD, XAGUSD, BTCUSD, ETHUSD, US500, DE30, FR40, HK50
[2026-05-30 23:56:19] Missing data for 1 assets: NAS100
[2026-05-30 23:56:19] 
--- STEP 2: Attempting MT5 data fetch ---
[2026-05-30 23:56:19]   [MT5] NAS100: symbol not found in MT5 — skipping
[2026-05-30 23:56:19] Successfully fetched 0 assets from MT5: 
[2026-05-30 23:56:19] Still missing data for 1 assets: NAS100
[2026-05-30 23:56:19] 
--- STEP 3: Running Symmetry Trap backtests ---
[2026-05-30 23:56:19] 
>>> EURUSD: EURUSD_M5.csv
[2026-05-30 23:56:19]   Running EURUSD (EUR/USD) | pip_size=0.0001 | csv=EURUSD_M5.csv (15.2MB)
[2026-05-30 23:56:24]   EURUSD (EUR/USD): 1163 trades | WR=85.0% | PnL=+5048.1p | PF=8.57
[2026-05-30 23:56:24] --- Done: EURUSD ---
[2026-05-30 23:56:24] 
>>> GBPUSD: GBPUSD_M5.csv
[2026-05-30 23:56:24]   Running GBPUSD (GBP/USD) | pip_size=0.0001 | csv=GBPUSD_M5.csv (16.2MB)
[2026-05-30 23:56:29]   GBPUSD (GBP/USD): 1259 trades | WR=85.7% | PnL=+7444.3p | PF=9.23
[2026-05-30 23:56:29] --- Done: GBPUSD ---
[2026-05-30 23:56:29] 
>>> USDCHF: USDCHF_M5.csv
[2026-05-30 23:56:29]   Running USDCHF (USD/CHF) | pip_size=0.0001 | csv=USDCHF_M5.csv (14.9MB)
[2026-05-30 23:56:33]   USDCHF (USD/CHF): 1153 trades | WR=84.9% | PnL=+5035.5p | PF=8.87
[2026-05-30 23:56:33] --- Done: USDCHF ---
[2026-05-30 23:56:33] 
>>> USDJPY: USDJPY_M5.csv
[2026-05-30 23:56:33]   Running USDJPY (USD/JPY) | pip_size=0.01 | csv=USDJPY_M5.csv (14.9MB)
[2026-05-30 23:56:38]   USDJPY (USD/JPY): 729 trades | WR=87.8% | PnL=+7086.7p | PF=16.73
[2026-05-30 23:56:38] --- Done: USDJPY ---
[2026-05-30 23:56:38] 
>>> AUDUSD: AUDUSD_M5.csv
[2026-05-30 23:56:38]   Running AUDUSD (AUD/USD) | pip_size=0.0001 | csv=AUDUSD_M5.csv (14.7MB)
[2026-05-30 23:56:42]   AUDUSD (AUD/USD): 828 trades | WR=89.3% | PnL=+3989.7p | PF=18.47
[2026-05-30 23:56:43] --- Done: AUDUSD ---
[2026-05-30 23:56:43] 
>>> NZDUSD: NZDUSD_M5.csv
[2026-05-30 23:56:43]   Running NZDUSD (NZD/USD) | pip_size=0.0001 | csv=NZDUSD_M5.csv (14.9MB)
[2026-05-30 23:56:47]   NZDUSD (NZD/USD): 727 trades | WR=93.3% | PnL=+4213.6p | PF=19.02
[2026-05-30 23:56:47] --- Done: NZDUSD ---
[2026-05-30 23:56:47] 
>>> CHFJPY: CHFJPY_M5.csv
[2026-05-30 23:56:47]   Running CHFJPY (CHF/JPY) | pip_size=0.01 | csv=CHFJPY_M5.csv (14.9MB)
[2026-05-30 23:56:52]   CHFJPY (CHF/JPY): 751 trades | WR=86.3% | PnL=+7167.0p | PF=13.01
[2026-05-30 23:56:52] --- Done: CHFJPY ---
[2026-05-30 23:56:52] 
>>> GBPJPY: GBPJPY_M5.csv
[2026-05-30 23:56:52]   Running GBPJPY (GBP/JPY) | pip_size=0.01 | csv=GBPJPY_M5.csv (15.0MB)
[2026-05-30 23:56:57]   GBPJPY (GBP/JPY): 830 trades | WR=86.3% | PnL=+8655.6p | PF=12.61
[2026-05-30 23:56:57] --- Done: GBPJPY ---
[2026-05-30 23:56:57] 
>>> GBPAUD: GBPAUD_M5.csv
[2026-05-30 23:56:57]   Running GBPAUD (GBP/AUD) | pip_size=0.0001 | csv=GBPAUD_M5.csv (17.2MB)
[2026-05-30 23:57:01]   GBPAUD (GBP/AUD): 715 trades | WR=88.4% | PnL=+7911.5p | PF=14.97
[2026-05-30 23:57:01] --- Done: GBPAUD ---
[2026-05-30 23:57:01] 
>>> GBPNZD: GBPNZD_M5.csv
[2026-05-30 23:57:01]   Running GBPNZD (GBP/NZD) | pip_size=0.0001 | csv=GBPNZD_M5.csv (15.8MB)
[2026-05-30 23:57:06]   GBPNZD (GBP/NZD): 664 trades | WR=88.4% | PnL=+8598.3p | PF=20.87
[2026-05-30 23:57:06] --- Done: GBPNZD ---
[2026-05-30 23:57:06] 
>>> GBPCHF: GBPCHF_M5.csv
[2026-05-30 23:57:06]   Running GBPCHF (GBP/CHF) | pip_size=0.0001 | csv=GBPCHF_M5.csv (15.4MB)
[2026-05-30 23:57:11]   GBPCHF (GBP/CHF): 803 trades | WR=91.2% | PnL=+6409.4p | PF=24.51
[2026-05-30 23:57:11] --- Done: GBPCHF ---
[2026-05-30 23:57:11] 
>>> XAUUSD: XAUUSD_M5.csv
[2026-05-30 23:57:11]   Running XAUUSD (XAU/USD) | pip_size=0.1 | csv=XAUUSD_M5.csv (16.6MB)
[2026-05-30 23:57:19]   XAUUSD (XAU/USD): 604 trades | WR=84.4% | PnL=+7187.7p | PF=7.42
[2026-05-30 23:57:19] --- Done: XAUUSD ---
[2026-05-30 23:57:19] 
>>> XAGUSD: XAGUSD_M5.csv
[2026-05-30 23:57:19]   Running XAGUSD (XAG/USD) | pip_size=0.01 | csv=XAGUSD_M5.csv (15.3MB)
[2026-05-30 23:57:25]   XAGUSD (XAG/USD): 2 trades | WR=50.0% | PnL=+2.5p | PF=26.00
[2026-05-30 23:57:25] --- Done: XAGUSD ---
[2026-05-30 23:57:25] 
>>> BTCUSD: BTCUSD_M5.csv
[2026-05-30 23:57:25]   Running BTCUSD (BTC/USD) | pip_size=1.0 | csv=BTCUSD_M5.csv (25.2MB)
[2026-05-30 23:57:32]   BTCUSD (BTC/USD): 801 trades | WR=92.6% | PnL=+152304.3p | PF=26.52
[2026-05-30 23:57:32] --- Done: BTCUSD ---
[2026-05-30 23:57:32] 
>>> ETHUSD: ETHUSD_M5.csv
[2026-05-30 23:57:32]   Running ETHUSD (ETH/USD) | pip_size=1.0 | csv=ETHUSD_M5.csv (24.6MB)
[2026-05-30 23:57:44]   ETHUSD (ETH/USD): 547 trades | WR=96.9% | PnL=+9562.5p | PF=50.34
[2026-05-30 23:57:44] --- Done: ETHUSD ---
[2026-05-30 23:57:44] 
>>> US500: US500_M5.csv
[2026-05-30 23:57:44]   Running US500 (US500) | pip_size=1.0 | csv=US500_M5.csv (13.5MB)
[2026-05-30 23:57:54]   US500 (US500): 372 trades | WR=91.7% | PnL=+3414.8p | PF=13.95
[2026-05-30 23:57:54] --- Done: US500 ---
[2026-05-30 23:57:54] 
>>> DE30: DE30_M5.csv
[2026-05-30 23:57:54]   Running DE30 (DE30) | pip_size=1.0 | csv=DE30_M5.csv (14.0MB)
[2026-05-30 23:57:58]   DE30 (DE30): 1145 trades | WR=82.8% | PnL=+18466.8p | PF=9.91
[2026-05-30 23:57:58] --- Done: DE30 ---
[2026-05-30 23:57:58] 
>>> FR40: FR40_M5.csv
[2026-05-30 23:57:58]   Running FR40 (FR40) | pip_size=1.0 | csv=FR40_M5.csv (13.0MB)
[2026-05-30 23:58:03]   FR40 (FR40): 1085 trades | WR=87.0% | PnL=+9730.3p | PF=12.21
[2026-05-30 23:58:03] --- Done: FR40 ---
[2026-05-30 23:58:03] 
>>> HK50: HK50_M5.csv
[2026-05-30 23:58:03]   Running HK50 (HK50) | pip_size=1.0 | csv=HK50_M5.csv (13.4MB)
[2026-05-30 23:58:08]   HK50 (HK50): 385 trades | WR=94.0% | PnL=+21838.8p | PF=40.30
[2026-05-30 23:58:08] --- Done: HK50 ---
[2026-05-30 23:58:08] 
--- STEP 4: Generating reports ---
[2026-05-30 23:58:08] Saved JSON results to C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json
[2026-05-30 23:58:08] Saved markdown report to C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_report.md
[2026-05-30 23:58:08] 
--- Verification ---
[2026-05-30 23:58:08]   OK   EURUSD: WR=85.0% | Trades=1163
[2026-05-30 23:58:08]   OK   GBPUSD: WR=85.7% | Trades=1259
[2026-05-30 23:58:08]   OK   USDCHF: WR=84.9% | Trades=1153
[2026-05-30 23:58:08]   OK   USDJPY: WR=87.8% | Trades=729
[2026-05-30 23:58:08]   OK   AUDUSD: WR=89.2% | Trades=828
[2026-05-30 23:58:09]   OK   NZDUSD: WR=93.3% | Trades=727
[2026-05-30 23:58:09]   OK   CHFJPY: WR=86.3% | Trades=751
[2026-05-30 23:58:09]   OK   GBPJPY: WR=86.3% | Trades=830
[2026-05-30 23:58:09]   OK   GBPAUD: WR=88.4% | Trades=715
[2026-05-30 23:58:09]   OK   GBPNZD: WR=88.4% | Trades=664
[2026-05-30 23:58:09]   OK   GBPCHF: WR=91.2% | Trades=803
[2026-05-30 23:58:09]   OK   XAUUSD: WR=84.4% | Trades=604
[2026-05-30 23:58:09]   OK   XAGUSD: WR=50.0% | Trades=2
[2026-05-30 23:58:09]   OK   BTCUSD: WR=92.6% | Trades=801
[2026-05-30 23:58:09]   OK   ETHUSD: WR=96.9% | Trades=547
[2026-05-30 23:58:09]   OK   US500: WR=91.7% | Trades=372
[2026-05-30 23:58:09]   OK   DE30: WR=82.8% | Trades=1145
[2026-05-30 23:58:09]   OK   FR40: WR=87.0% | Trades=1085
[2026-05-30 23:58:09]   OK   HK50: WR=94.0% | Trades=385
[2026-05-30 23:58:09] 
=== COMPLETE: 19/20 assets backtested ===
