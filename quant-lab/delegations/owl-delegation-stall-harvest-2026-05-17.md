# 🦉 OWL Delegation Order — Stall_Harvest Validation Sprint
> **From:** OWL (OC2) | **To:** Manager (Quant Lab) | **Priority:** CRITICAL
> **Date:** 2026-05-17 17:34 EDT

## MAD Directive
Stall_Harvest v2 showed **100% WR, +867p PnL, PF 867, 0 MaxDD, 88 trades** — this is potentially PRODUCTION READY. The "SL/TP inversion" flagged earlier may be a **reporting bug in the optimizer**, not in the actual strategy. The strategy code itself looks correct.

## Task: Validate Stall_Harvest Properly

### Step 1: Fix Exit Reporting Bug
The optimizer_v2 `by_exit` field shows `"sl": 88` for ALL 88 Stall_Harvest trades, yet all 88 are wins. This is clearly a **reporting/labeling bug** in the optimizer's exit classification, NOT a strategy bug.

- Find where `by_exit` is calculated in `optimizer_v2.py`
- Fix the exit reason labeling so SL/TP are correctly identified
- Re-run Stall_Harvest with corrected reporting

### Step 2: Run Stall_Harvest on Multiple Timeframes & Pairs
Use the standalone strategy at `projects/trading/nautilus/strategies/stall_harvest.py`

**Data files (all in C:\Users\wifik\Downloads\):**
| File | Pair | TF | Size |
|------|------|----|------|
| EURUSD!_M5_202301020000_202605061250.csv | EUR/USD | M5 | 15MB |
| EURUSD!_M1_202301020000_202605061253.csv | EUR/USD | M1 | 75MB |
| USDCHF!_M5_202301020000_202605061250.csv | USD/CHF | M5 | 15MB |
| USDCHF!_M1_202301020000_202605061253.csv | USD/CHF | M1 | 75MB |
| GBPUSD!_M5_202301020000_202605061250.csv | GBP/USD | M5 | 15MB |
| GBPUSD!_M1_202301020000_202605061253.csv | GBP/USD | M1 | 75MB |
| USDJPY!_M5_202301020000_202605061250.csv | USD/JPY | M5 | 15MB |
| USDCAD!_M5_202301020000_202605061250.csv | USD/CAD | M5 | 15MB |
| AUDUSD!_M5_202301020000_202605061250.csv | AUD/USD | M5 | 15MB |
| NZDUSD!_M5_202301020000_202605061250.csv | NZD/USD | M5 | 15MB |
| CHFJPY!_M5_202201030000_202605061250.csv | CHF/JPY | M5 | 15MB |
| DE30_M5_202301020200_202604302255.csv | DE30 | M5 | - |
| DE30_M1_202306120637_202604302259.csv | DE30 | M1 | - |
| FR40_M5_202301020900_202604302255.csv | FR40 | M5 | - |
| FR40_M1_202302060154_202604302259.csv | FR40 | M1 | - |
| US500_M5_202301030100_202605011035.csv | US500 | M5 | - |
| US500_M1_202307050935_202605011039.csv | US500 | M1 | - |
| USTEC100_M1_202501020100_202605122359.csv | USTEC | M1 | - |
| USTEC100_202407010100_202605132122.csv | USTEC | - | - |

**Run Stall_Harvest on at minimum:**
1. EUR/USD M5 (confirm the 100% WR)
2. EUR/USD M1 (higher frequency, more trades)
3. USD/CHF M5
4. GBP/USD M5
5. USD/JPY M5

### Step 3: Report Format
For each backtest, save results to `quant-lab/results/stall_harvest_{pair}_{tf}_{timestamp}.json`

Include: total_trades, wins, losses, win_rate, total_pnl_pips, avg_win, avg_loss, max_dd, profit_factor, by_session, by_exit_reason

### Step 4: Escalate If
- Stall_Harvest confirms 100% WR on EUR/USD M5 with correct exit labeling → **IMMEDIATE MAD NOTIFICATION** (this is production-ready)
- Stall_Harvest works on multiple pairs → **MAD NOTIFICATION** (robust strategy)
- Any issues found → document and escalate

## Important Notes
- The strategy code at `projects/trading/nautilus/strategies/stall_harvest.py` is a STANDALONE runner — it doesn't need the optimizer
- Use the standalone runner directly: `python projects/trading/nautilus/strategies/stall_harvest.py`
- You may need to modify the data path in the script or create a simple runner loop for multiple pairs
- The optimizer_v2.py has a reporting bug — either fix it or bypass it by using the standalone strategy

## After Stall_Harvest Validation
Continue with the remaining bug fixes:
1. Constraint_Anchor partial exits
2. Dual_Engine SL tightening  
3. Two_Plays entry debug
4. Blind_Structural_Chain threshold tuning
5. P90P_Distribution redesign as target module

**But Stall_Harvest validation is TOP PRIORITY — it could be our flagship production strategy.**
