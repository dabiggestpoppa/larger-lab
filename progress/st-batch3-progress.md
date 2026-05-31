# Batch 3 -- Crosses B + Metals + Crypto Backtest Summary
**Date:** 2026-05-31 00:47:08

| Asset | Trades | WR | PF | Sharpe | MaxDD (pips) | MaxDD (%) | PnL (pips) | Status |
|-------|--------|-----|-----|--------|-------------|-----------|------------|--------|
| GBPAUD | 715 | 88.4% | 14.97 | 14.77 | 60.1 | 0.06% | +7911.5 | OK |
| GBPNZD | 664 | 88.4% | 20.87 | 15.83 | 46.2 | 0.05% | +8598.3 | OK |
| GBPCHF | 803 | 91.2% | 24.51 | 17.74 | 22.7 | 0.02% | +6409.4 | OK |
| XAUUSD | 604 | 84.4% | 7.42 | 11.28 | 121.4 | 0.12% | +7187.7 | OK |
| XAGUSD | 2 | 50.0% | 26.0 | 10.39 | 0.1 | 0.0% | 2.5 | FLAGGED |
| BTCUSD | 801 | 92.6% | 26.52 | 13.0 | 785.0 | 0.78% | +152304.3 | OK |
| ETHUSD | 547 | 96.9% | 50.34 | 24.04 | 31.7 | 0.03% | +9562.5 | OK |

## Issues / Flags

- **XAGUSD:** XAGUSD generated only 2 trades -- config likely issues (tier thresholds too tight, pip_value=0.01 with small AR)

## Reports Generated

- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPAUD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPAUD_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPNZD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPNZD_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPCHF_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/GBPCHF_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/XAUUSD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/XAUUSD_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/XAGUSD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/XAGUSD_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/BTCUSD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/BTCUSD_mc_results.json`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/ETHUSD_full_report.md`
- `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/ETHUSD_mc_results.json`

## Monte Carlo Comparison

| Asset | Median PnL | 90% CI | Median MaxDD | Ruin Prob | Median PF |
|-------|-----------|--------|-------------|-----------|-----------|
| GBPAUD | +7911.499999999998p | [+7911.5, +7911.5] | 60.100000000000364p | 0.0% | 10.0 |
| GBPNZD | +8598.300000000001p | [+8598.3, +8598.3] | 46.200000000000045p | 0.0% | 10.0 |
| GBPCHF | +6409.399999999999p | [+6409.4, +6409.4] | 16.600000000000136p | 0.0% | 10.0 |
| XAUUSD | +7187.7p | [+7187.7, +7187.7] | 122.80000000000018p | 0.0% | 7.417016337826978 |
| XAGUSD | +2.5p | [+2.5, +2.5] | 0.1p | 0.0% | 10.0 |
| BTCUSD | +152304.29999999993p | [+152304.3, +152304.3] | 785.0p | 0.0% | 10.0 |
| ETHUSD | +9562.5p | [+9562.5, +9562.5] | 31.699999999999818p | 0.0% | 10.0 |

## Asset Configuration Reference

### GBPAUD
- pip_value: 0.0001
- k_factor: 0.48
- sl_method: OCC_PLUS_8P
- T1: AR<=42.0p, AU=21.0p, trigger=25.0p
- T2: AR<=64.0p, AU=32.0p, trigger=38.0p
- T3: AR<=105.0p, AU=52.0p, trigger=63.0p

### GBPNZD
- pip_value: 0.0001
- k_factor: 0.48
- sl_method: OCC_PLUS_8P
- T1: AR<=48.0p, AU=24.0p, trigger=29.0p
- T2: AR<=72.0p, AU=36.0p, trigger=43.0p
- T3: AR<=118.0p, AU=59.0p, trigger=71.0p

### GBPCHF
- pip_value: 0.0001
- k_factor: 0.48
- sl_method: OCC_PLUS_6P
- T1: AR<=35.0p, AU=18.0p, trigger=21.0p
- T2: AR<=54.0p, AU=27.0p, trigger=32.0p
- T3: AR<=88.0p, AU=44.0p, trigger=53.0p

### XAUUSD
- pip_value: 0.1
- k_factor: 0.5
- sl_method: FIXED_BUFFER
- T1: AR<=32.0p, AU=16.0p, trigger=19.0p
- T2: AR<=58.0p, AU=29.0p, trigger=35.0p
- T3: AR<=95.0p, AU=48.0p, trigger=58.0p

### XAGUSD
- pip_value: 0.01
- k_factor: 0.5
- sl_method: FIXED_BUFFER
- T1: AR<=1.8p, AU=0.9p, trigger=1.1p
- T2: AR<=3.2p, AU=1.6p, trigger=1.9p
- T3: AR<=5.2p, AU=2.6p, trigger=3.1p

### BTCUSD
- pip_value: 1.0
- k_factor: 0.52
- sl_method: FIXED_BUFFER
- T1: AR<=750.0p, AU=205.0p, trigger=246.0p
- T2: AR<=1700.0p, AU=545.0p, trigger=654.0p
- T3: AR<=3000.0p, AU=1160.0p, trigger=1392.0p

### ETHUSD
- pip_value: 1.0
- k_factor: 0.52
- sl_method: FIXED_BUFFER
- T1: AR<=70.0p, AU=35.0p, trigger=42.0p
- T2: AR<=105.0p, AU=42.0p, trigger=52.0p
- T3: AR<=160.0p, AU=52.0p, trigger=65.0p
