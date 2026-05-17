# Quant Lab — Mission & Goals

> MAD's requirements. Non-negotiable. Everything the team does serves these 6 goals.

## The 6 Goals

### GOAL 1: All Manual Strategies Backtested
**Every strategy in the CEREBUS manual must be coded and backtested against EUR/USD.**

From `docs/strategies/` (14 documents):
1. ✅ CFD_Expansion_Engine — DONE (losing, needs fix)
2. ✅ P90_Cascade_Activation — DONE (losing, needs fix)
3. ✅ Cascade_Methodology — DONE (combo variant, losing)
4. ✅ Stall_Harvest — DONE (suspicious 100% WR, needs investigation)
5. ❌ P90P_Distribution_Tracker — NOT BUILT
6. ✅ Monday_Asian_Float — DONE (WINNER)
7. ✅ Daily_Asian_Float — DONE (WINNER)
8. ✅ Full_Day_Range_Regime — DONE (losing)
9. ❌ Dual_Engine — NOT BUILT
10. ❌ Failure_Repair — NOT BUILT
11. ❌ Two_Plays — NOT BUILT
12. ❌ Triple_Engine — NOT BUILT
13. ❌ Blind_Structural_Chain — NOT BUILT
14. ❌ Fractal_Resolution — NOT BUILT (Resolution_Amplifier is a first attempt)

**Action items:**
- Read each `docs/strategies/<name>.txt` document
- Code the strategy in `projects/trading/nautilus/strategies/<name>.py`
- Backtest against EUR/USD data
- Report results in `quant-lab/results/<name>_YYYY-MM-DD.json`
- Update `quant-lab/STATUS.md` with results

### GOAL 2: 80% of Strategies Profitable
**Out of all strategies built, at least 80% must be profitable (positive expectancy).**

Currently: 2/9 profitable = 22%. Need to get to 80%.

**How to get there:**
- Fix the 5 losing strategies (CFD_Expansion, P90_Cascade, Cascade_Combo, Full_Day_Regime, Constraint_Anchor)
- Build the 8 missing strategies (some should be winners based on manual research)
- Each strategy must have: positive expectancy, profit factor > 1.0
- If a strategy can't be made profitable after 3 tuning attempts, document why and move on

### GOAL 3: Max Drawdown Under 12%
**All profitable strategies must have maximum drawdown ≤ 12%.**

**How to achieve:**
- Use position sizing (risk 1-2% per trade)
- Add trailing stops where appropriate
- If a strategy has >12% DD, tune: tighten stops, reduce position size, add filters
- Report max DD alongside every backtest result

### GOAL 4: One 80% Win Rate Strategy, ~2 Trades/Day
**Find or build ONE strategy with:**
- Win rate ≥ 80%
- Average 2 trades per day (≈ 40 trades/month, ≈ 500/year)
- Positive expectancy
- Max DD ≤ 12%

**This is the flagship strategy.** The manual hints at this being possible with:
- Blind_Structural_Chain (93.7% continuation in Goldilocks zone)
- P90P_Distribution_Tracker (90-95% accuracy)
- Dual_Engine synergy gap (84.2% aligned)

### GOAL 5: Backtest All Winning Strategies on USD/CHF 5-Min
**Every strategy that's profitable on EUR/USD must also be backtested on USD/CHF M5.**

Data available: `C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv`

**Action:**
- Take every strategy with positive expectancy on EUR/USD
- Run identical backtest on USD/CHF M5
- Report: win rate, PnL, profit factor, max DD, expectancy
- Goal: strategies that work on multiple pairs are more robust

### GOAL 6: Basket Backtest — EUR/USD + USD/CHF + CHF/JPY
**Create a portfolio/basket of the best strategies across 3 pairs and optimize until profitable.**

Pairs:
- EUR/USD (primary, most data)
- USD/CHF (M5 data available)
- CHF/JPY (M1 data available: `CHFJPY!_M1_202301020000_202605061250.csv`)

**Action:**
- Select top 3-5 strategies from Goals 1-4
- Run each on all 3 pairs
- Create a combined portfolio backtest
- Optimize: which strategies on which pairs, position sizing
- Target: combined portfolio with positive expectancy, max DD ≤ 12%

## Priority Order

1. **Fix existing losing strategies** (quick wins)
2. **Build 8 missing strategies** from manual
3. **Investigate Stall_Harvest_CFD** (suspicious 100% WR)
4. **Backtest winners on USD/CHF** (Goal 5)
5. **Build basket portfolio** (Goal 6)
6. **Find the 80% WR strategy** (Goal 4 — may emerge from new builds)

## Data Files

| File | Pair | Timeframe | Size |
|------|------|-----------|------|
| `EURUSD.PRO_202407010000_202605132122.csv` | EUR/USD | Tick/1M | ~3GB |
| `US500_202407010100_202605132122.csv` | US500 | Tick/1M | ~5GB |
| `USDCHF!_M5_202301020000_202605061250.csv` | USD/CHF | M5 | 15MB |
| `USDCHF!_M1_202301020000_202605061253.csv` | USD/CHF | M1 | 75MB |
| `CHFJPY!_M1_202301020000_202605061250.csv` | CHF/JPY | M1 | ~75MB |
| `USDJPY!_M5_202301020000_202605061250.csv` | USD/JPY | M5 | 15MB |
| `GBPUSD!_M5_202301020000_202605061250.csv` | GBP/USD | M5 | 15MB |

## Code Base

- Strategies: `projects/trading/nautilus/strategies/`
- Backtest engine: `projects/trading/nautilus/backtest_engine.py`
- Data loader: `projects/trading/nautilus/data_loader.py`
- Full pipeline: `projects/trading/nautilus/full_pipeline.py`
- Manual strategy docs: `docs/strategies/`
- Results: `quant-lab/results/`
- Status tracker: `quant-lab/STATUS.md`

## Reporting Format

Every backtest result must be saved as JSON:
```json
{
  "strategy": "name",
  "pair": "EUR/USD",
  "timeframe": "M5",
  "total_trades": 500,
  "wins": 280,
  "losses": 220,
  "win_rate": 56.0,
  "total_pnl": 1250.50,
  "avg_win": 12.5,
  "avg_loss": -8.2,
  "max_drawdown_pct": 8.5,
  "profit_factor": 1.45,
  "expectancy": 2.50,
  "by_exit": {"sl": 180, "tp": 310, "other": 10}
}
```
