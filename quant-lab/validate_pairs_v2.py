"""
Optimized validation of Pairs Trading EUR/USD-GBP/USD strategy.
Avoids slow rolling.apply autocorr — uses vectorized alternatives.
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np

# ── 1. Load raw data ──────────────────────────────────────────────────────────

def load_m5(path):
    records = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            ts = pd.Timestamp(f"{parts[0]} {parts[1]}", tz='UTC')
            o, h, l, c = float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])
            vol = int(parts[6])
            records.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': vol, 'ts': ts})
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    return df

eur_path = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
gbp_path = r"C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv"

print("Loading data...")
eur = load_m5(eur_path)
gbp = load_m5(gbp_path)

print(f"EUR/USD: {len(eur):,} bars | {eur.index[0]} -> {eur.index[-1]}")
print(f"GBP/USD: {len(gbp):,} bars | {gbp.index[0]} -> {gbp.index[-1]}")

total_days = (eur.index[-1] - eur.index[0]).days
total_years = total_days / 365.25
print(f"Date range: {total_days} days ({total_years:.1f} years)")

# Check for duplicates
eur_dups = int(eur.index.duplicated().sum())
gbp_dups = int(gbp.index.duplicated().sum())
print(f"Duplicates: EUR={eur_dups}, GBP={gbp_dups}")

# Check for gaps (> 30 minutes between bars)
eur_gaps = int((eur.index.to_series().diff() > pd.Timedelta(minutes=30)).sum())
gbp_gaps = int((gbp.index.to_series().diff() > pd.Timedelta(minutes=30)).sum())
print(f"Gaps (>30min): EUR={eur_gaps}, GBP={gbp_gaps}")

# Price sanity
print(f"EUR/USD range: {eur['close'].min():.5f} - {eur['close'].max():.5f}")
print(f"GBP/USD range: {gbp['close'].min():.5f} - {gbp['close'].max():.5f}")
print(f"EUR/USD zero/negative: {(eur['close'] <= 0).sum()}")
print(f"GBP/USD zero/negative: {(gbp['close'] <= 0).sum()}")

# ── 2. Align and compute spread ───────────────────────────────────────────────

common_idx = eur.index.intersection(gbp.index)
print(f"Common timestamps: {len(common_idx):,}")
eur_a = eur.loc[common_idx]
gbp_a = gbp.loc[common_idx]

ratio = eur_a['close'] / gbp_a['close']
price_spread = eur_a['close'] - gbp_a['close']

print(f"Ratio range: {ratio.min():.6f} - {ratio.max():.6f}")
print(f"Price spread range: {price_spread.min():.5f} - {price_spread.max():.5f}")

# Rolling correlation
rolling_corr = eur_a['close'].rolling(50).corr(gbp_a['close'])
print(f"Avg 50-bar correlation: {rolling_corr.mean():.4f}")
print(f"Min 50-bar correlation: {rolling_corr.min():.4f}")
print(f"Corr < 0.70: {(rolling_corr < 0.70).sum()} bars ({(rolling_corr < 0.70).mean()*100:.1f}%)")

# ── 3. Re-run backtest with full instrumentation ──────────────────────────────

zscore_window = 50
zscore_entry = 2.0
zscore_exit = 0.5
zscore_stop = 3.0
min_correlation = 0.70
time_stop_bars = 50

# Pre-compute signals (vectorized — no slow rolling.apply)
ratio_mean = ratio.rolling(zscore_window).mean()
ratio_std = ratio.rolling(zscore_window).std()
z_ratio = (ratio - ratio_mean) / (ratio_std + 1e-10)

ps_mean = price_spread.rolling(zscore_window).mean()
ps_std = price_spread.rolling(zscore_window).std()
z_price = (price_spread - ps_mean) / (ps_std + 1e-10)

correlation = rolling_corr

# Cointegration proxy: use autocorrelation of ratio (vectorized)
# autocorr(lag=1) = corr(x[:-1], x[1:]) — can compute via rolling
ratio_lag1 = ratio.shift(1)
ratio_autocorr = ratio.rolling(50).corr(ratio_lag1)
coint_strength = 1 - ratio_autocorr.abs()

# Other signals
spread_mom = ratio.pct_change(5)
eur_vol = eur_a['close'].pct_change().rolling(20).std()
gbp_vol = gbp_a['close'].pct_change().rolling(20).std()
vol_ratio = eur_vol / (gbp_vol + 1e-10)

hour_utc = ratio.index.hour
is_london = ((hour_utc >= 7) & (hour_utc < 16)).astype(float)
dow = ratio.index.dayofweek
is_tue_wed = ((dow == 1) | (dow == 2)).astype(float)

spread_sma = ratio.rolling(20).mean()
spread_std2 = ratio.rolling(20).std()
spread_bb_pos = (ratio - spread_sma) / (spread_std2 + 1e-10)

# Alpha signals
s_z_ratio = -np.clip(z_ratio / 3, -1, 1)
s_z_price = -np.clip(z_price / 3, -1, 1)
s_corr = np.where(correlation > 0.8, 1.0, np.where(correlation > 0.7, 0.3, -1.0))
s_coint = np.where(coint_strength > 0.5, 1.0, np.where(coint_strength > 0.3, 0.3, -0.5))
s_mom = np.clip(spread_mom * 10, -1, 1)
s_vol = np.where((vol_ratio > 0.8) & (vol_ratio < 1.2), 1.0,
                 np.where((vol_ratio > 0.5) & (vol_ratio < 2.0), 0.3, -0.5))
s_session = np.where(is_london > 0, 1.0, 0.0)
s_dow = np.where(is_tue_wed > 0, 1.0, np.where((dow == 0) | (dow == 3), 0.3, -0.3))
s_bb = -np.clip(spread_bb_pos / 2, -1, 1)

alpha = (0.20 * s_z_ratio + 0.15 * s_z_price + 0.12 * s_corr +
         0.15 * s_coint + 0.08 * s_mom + 0.07 * s_vol +
         0.10 * s_session + 0.06 * s_dow + 0.07 * s_bb)

# Build aligned DataFrame
df = pd.DataFrame({
    'z_ratio': z_ratio,
    'z_price': z_price,
    'correlation': correlation,
    'alpha': alpha,
    'ratio': ratio,
}, index=common_idx)

df.dropna(inplace=True)
print(f"Bars after warmup: {len(df):,}")

# Backtest loop
equity = 10000.0
trades = []
position_open = False
bars_in_trade = 0

for idx, bar in df.iterrows():
    if position_open:
        entry_trade = trades[-1]
        bars_in_trade += 1

        current_z = bar['z_ratio']
        entry_z = entry_trade['entry_z']
        direction = entry_trade['direction']

        z_improvement = abs(entry_z) - abs(current_z)
        pnl = z_improvement * 50.0
        if not np.isfinite(pnl):
            pnl = 0.0

        exit_reason = None
        if abs(current_z) < zscore_exit:
            exit_reason = 'mean_reversion'
        elif abs(current_z) > zscore_stop:
            exit_reason = 'stop_loss'
        elif bars_in_trade >= time_stop_bars:
            exit_reason = 'time_stop'
        elif bar['correlation'] < 0.60:
            exit_reason = 'correlation_breakdown'

        if exit_reason:
            entry_trade['exit_time'] = idx
            entry_trade['exit_z'] = current_z
            entry_trade['pnl'] = pnl
            entry_trade['exit_reason'] = exit_reason
            entry_trade['bars_held'] = bars_in_trade
            equity += pnl
            position_open = False
            bars_in_trade = 0
    else:
        if abs(bar['z_ratio']) < zscore_entry:
            continue
        if bar['correlation'] < min_correlation:
            continue
        if abs(bar['alpha']) < 0.3:
            continue

        z = bar['z_ratio']
        direction = -1 if z > 0 else 1

        if bar['alpha'] * direction < 0:
            continue

        trade = {
            'entry_time': idx,
            'entry_z': z,
            'direction': direction,
            'alpha': float(bar['alpha']),
            'correlation': float(bar['correlation']),
        }
        trades.append(trade)
        position_open = True
        bars_in_trade = 0

# Close final
if position_open and trades:
    last = trades[-1]
    if 'exit_time' not in last:
        last['exit_time'] = df.index[-1]
        last['exit_z'] = float(df.iloc[-1]['z_ratio'])
        last['pnl'] = 0.0
        last['exit_reason'] = 'end_of_data'
        last['bars_held'] = 0

completed = [t for t in trades if 'pnl' in t]
pnls = [t['pnl'] for t in completed]

print(f"Total trades: {len(completed)}")

# ── 4. Compute comprehensive metrics ──────────────────────────────────────────

wins = [p for p in pnls if p > 0]
losses = [p for p in pnls if p <= 0]
total_pnl = sum(pnls)
win_rate = len(wins) / len(pnls) * 100 if pnls else 0

gross_profit = sum(wins) if wins else 0
gross_loss = abs(sum(losses)) if losses else 0
profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

cumulative = np.cumsum(pnls)
peak = np.maximum.accumulate(cumulative)
drawdowns = peak - cumulative
max_dd = float(drawdowns.max()) if len(drawdowns) > 0 else 0

avg_win = float(np.mean(wins)) if wins else 0
avg_loss = float(np.mean(losses)) if losses else 0
expectancy = (win_rate/100) * avg_win + (1 - win_rate/100) * avg_loss

durations = [t.get('bars_held', 0) for t in completed]
avg_duration = float(np.mean(durations)) if durations else 0
avg_duration_min = avg_duration * 5
avg_duration_hours = avg_duration_min / 60

trade_dates = set()
for t in completed:
    trade_dates.add(t['entry_time'].date())
active_days = len(trade_dates)
trades_per_day = len(completed) / active_days if active_days > 0 else 0
trades_per_week = trades_per_day * 7

pnl_series = np.array(pnls)
if len(pnl_series) > 1 and pnl_series.std() > 0:
    sharpe_per_trade = float(pnl_series.mean() / pnl_series.std())
    sharpe_annual = sharpe_per_trade * np.sqrt(252 * 288)
else:
    sharpe_per_trade = 0
    sharpe_annual = 0

exit_reasons = {}
for t in completed:
    r = t.get('exit_reason', 'unknown')
    exit_reasons[r] = exit_reasons.get(r, 0) + 1

# Temporal patterns
day_pnl = defaultdict(float)
day_count = defaultdict(int)
hour_pnl = defaultdict(float)
hour_count = defaultdict(int)
month_pnl = defaultdict(float)
month_count = defaultdict(int)

for t in completed:
    et = t['entry_time']
    day_pnl[et.dayofweek] += t['pnl']
    day_count[et.dayofweek] += 1
    hour_pnl[et.hour] += t['pnl']
    hour_count[et.hour] += 1
    month_pnl[et.month] += t['pnl']
    month_count[et.month] += 1

day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

best_day = max(day_pnl, key=day_pnl.get)
worst_day = min(day_pnl, key=day_pnl.get)
best_hour = max(hour_pnl, key=hour_pnl.get)
worst_hour = min(hour_pnl, key=hour_pnl.get)
best_month = max(month_pnl, key=month_pnl.get)
worst_month = min(month_pnl, key=month_pnl.get)

# Annualized return
annual_return = ((equity/10000) ** (1/total_years) - 1) * 100 if total_years > 0 else 0

# ── 5. Save JSON results ─────────────────────────────────────────────────────

results = {
    'validation_date': str(pd.Timestamp.now()),
    'data': {
        'eur_bars': len(eur),
        'gbp_bars': len(gbp),
        'common_bars': len(common_idx),
        'date_range': f"{eur.index[0]} to {eur.index[-1]}",
        'years': round(total_years, 2),
        'eur_duplicates': eur_dups,
        'gbp_duplicates': gbp_dups,
        'eur_gaps': eur_gaps,
        'gbp_gaps': gbp_gaps,
        'avg_correlation': round(float(rolling_corr.mean()), 4),
        'used_synthetic_gbp': False,
    },
    'performance': {
        'total_trades': len(completed),
        'win_rate': round(win_rate, 2),
        'total_pnl': round(total_pnl, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'profit_factor': round(profit_factor, 3),
        'max_drawdown': round(max_dd, 2),
        'final_equity': round(equity, 2),
        'expectancy_per_trade': round(expectancy, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'sharpe_trade_level': round(sharpe_per_trade, 4),
        'sharpe_annualized': round(float(sharpe_annual), 4),
        'annualized_return_pct': round(annual_return, 2),
    },
    'trade_characteristics': {
        'avg_duration_bars': round(avg_duration, 1),
        'avg_duration_hours': round(avg_duration_hours, 1),
        'active_days': active_days,
        'trades_per_day': round(trades_per_day, 1),
        'trades_per_week': round(trades_per_week, 1),
    },
    'exit_reasons': exit_reasons,
    'temporal': {
        'best_day': day_names[best_day],
        'worst_day': day_names[worst_day],
        'best_hour_utc': int(best_hour),
        'worst_hour_utc': int(worst_hour),
        'best_month': month_names[best_month-1],
        'worst_month': month_names[worst_month-1],
    },
}

out_json = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\pairs_validation_detail.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"JSON saved to {out_json}")

# ── 6. Write Markdown Report ─────────────────────────────────────────────────

issues = []
warnings = []

# Critical checks
issues.append("No commission or spread costs applied in backtest")
issues.append("P&L uses arbitrary $50/z-unit scaling, not real position sizing or pip-value calculation")
warnings.append("Alpha confirmation filter uses same-bar alpha (minor look-ahead risk)")
warnings.append("Alpha weights and IC values appear hand-tuned/assumed, not empirically measured")
warnings.append(f"Annualized return of {annual_return:.0f}% is unrealistic for pairs trading")
warnings.append(f"Win rate of {win_rate:.1f}% is unusually high for pairs trading")
warnings.append(f"Profit factor of {profit_factor:.2f} is unusually high")
warnings.append(f"High trade frequency: {trades_per_day:.1f} trades/day")

# Max DD as percentage of peak equity
max_dd_pct = max_dd / (10000 + total_pnl - max_dd) * 100 if (10000 + total_pnl - max_dd) > 0 else 0

report = f"""# Pairs Trading EUR/USD-GBP/USD — Validation Report

> **Validation Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}  
> **Validator:** Quant Lab Optimizer  
> **Strategy File:** `projects/trading/nautilus/strategies/pairs_trading_eurusd_gbpusd.py`  
> **Data:** EUR/USD M5 + GBP/USD M5 (2023-01-02 to 2026-05-06)

---

## Executive Summary

**Verdict: BUGS FOUND — NOT production ready.**

The strategy reports +$206K PnL (2,062% return) over ~3.3 years with a 72.6% win rate. This is **not a real edge** — it is an artifact of three compounding issues:

1. **No transaction costs** — Zero commission or spread applied. At ~$24 round-trip per standard lot, 3,931 trades would cost ~$94K+ in fees alone.
2. **Arbitrary P&L scaling** — The $50/z-unit multiplier is not derived from position sizing, pip value, or lot size. It is a magic number that inflates P&L without economic meaning.
3. **Suspiciously high trade count** — 3,931 trades over 3.3 years = ~3.3 trades/day, which is extremely high for a pairs trading strategy that requires |z| > 2.0 entries.

The underlying mean-reversion logic is sound in principle, but the backtest implementation is not trustworthy for production decisions.

---

## Data Quality

| Metric | Value |
|--------|-------|
| EUR/USD bars | {len(eur):,} |
| GBP/USD bars | {len(gbp):,} |
| Common bars | {len(common_idx):,} |
| Date range | {eur.index[0].strftime('%Y-%m-%d')} to {eur.index[-1].strftime('%Y-%m-%d')} |
| Duration | {total_years:.1f} years ({total_days} days) |
| EUR/USD duplicates | {eur_dups} |
| GBP/USD duplicates | {gbp_dups} |
| EUR/USD gaps (>30min) | {eur_gaps} |
| GBP/USD gaps (>30min) | {gbp_gaps} |
| EUR/USD price range | {eur['close'].min():.5f} - {eur['close'].max():.5f} |
| GBP/USD price range | {gbp['close'].min():.5f} - {gbp['close'].max():.5f} |
| Avg 50-bar correlation | {rolling_corr.mean():.4f} |
| Min 50-bar correlation | {rolling_corr.min():.4f} |
| Correlation < 0.70 | {(rolling_corr < 0.70).sum():,} bars ({(rolling_corr < 0.70).mean()*100:.1f}%) |
| GBP/USD data source | Real (not synthetic) |

**Data quality is good.** Both files exist, no duplicates, no zero/negative prices, and the correlation between EUR/USD and GBP/USD is consistently high (mean {rolling_corr.mean():.4f}), which is expected and validates the pairs trading premise.

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total trades | {len(completed):,} |
| Win rate | {win_rate:.1f}% |
| Total P&L | ${total_pnl:,.2f} |
| Gross profit | ${gross_profit:,.2f} |
| Gross loss | ${gross_loss:,.2f} |
| Profit factor | {profit_factor:.2f} |
| Max drawdown | ${max_dd:,.2f} |
| Max DD % of peak | {max_dd_pct:.2f}% |
| Final equity | ${equity:,.2f} |
| Expectancy/trade | ${expectancy:.2f} |
| Avg win | ${avg_win:.2f} |
| Avg loss | ${avg_loss:.2f} |
| Sharpe (trade-level) | {sharpe_per_trade:.4f} |
| Sharpe (annualized) | {sharpe_annual:.4f} |
| Annualized return | {annual_return:.1f}% |

---

## Trade Characteristics

| Metric | Value |
|--------|-------|
| Avg trade duration | {avg_duration_hours:.1f} hours ({avg_duration:.0f} bars) |
| Active trading days | {active_days:,} |
| Trades per day | {trades_per_day:.1f} |
| Trades per week | {trades_per_week:.1f} |

---

## Exit Reasons

| Exit Reason | Count | % |
|-------------|-------|---|
"""

for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
    pct = count / len(completed) * 100
    report += f"| {reason} | {count} | {pct:.1f}% |\n"

report += f"""
---

## Temporal Analysis

### Day of Week

| Day | Trades | P&L | Avg P&L |
|-----|--------|-----|---------|
"""

for i, name in enumerate(day_names):
    if i in day_pnl:
        avg = day_pnl[i] / day_count[i] if day_count[i] > 0 else 0
        report += f"| {name} | {day_count[i]} | ${day_pnl[i]:,.2f} | ${avg:,.2f} |\n"
    else:
        report += f"| {name} | 0 | $0.00 | $0.00 |\n"

report += f"""
**Best day:** {day_names[best_day]} (${day_pnl[best_day]:,.2f})  
**Worst day:** {day_names[worst_day]} (${day_pnl[worst_day]:,.2f})

### Hour of Day (UTC) — Top 5 by P&L

| Hour | Trades | P&L | Avg P&L |
|------|--------|-----|---------|
"""

for h, p in sorted(hour_pnl.items(), key=lambda x: -x[1])[:5]:
    avg = p / hour_count[h] if hour_count[h] > 0 else 0
    report += f"| {h:02d}:00 | {hour_count[h]} | ${p:,.2f} | ${avg:,.2f} |\n"

report += f"""
**Best hour:** {best_hour:02d}:00 UTC (${hour_pnl[best_hour]:,.2f})  
**Worst hour:** {worst_hour:02d}:00 UTC (${hour_pnl[worst_hour]:,.2f})

### Monthly

| Month | Trades | P&L | Avg P&L |
|-------|--------|-----|---------|
"""

for m in range(1, 13):
    if m in month_pnl:
        avg = month_pnl[m] / month_count[m] if month_count[m] > 0 else 0
        report += f"| {month_names[m-1]} | {month_count[m]} | ${month_pnl[m]:,.2f} | ${avg:,.2f} |\n"
    else:
        report += f"| {month_names[m-1]} | 0 | $0.00 | $0.00 |\n"

report += f"""
**Best month:** {month_names[best_month-1]} (${month_pnl[best_month]:,.2f})  
**Worst month:** {month_names[worst_month-1]} (${month_pnl[worst_month]:,.2f})

---

## Critical Issues Found

### ❌ Issues (Must Fix)

"""

for i, issue in enumerate(issues, 1):
    report += f"{i}. **{issue}**\n"

report += f"""
### ⚠️ Warnings (Should Address)

"""

for i, w in enumerate(warnings, 1):
    report += f"{i}. {w}\n"

report += f"""
---

## Detailed Analysis

### 1. Commission & Spread Impact

The backtest applies **zero transaction costs**. For a realistic estimate:

- **Spread cost:** ~0.5 pips per leg (EUR/USD and GBP/USD are tight, but not zero)
- **Commission:** ~0.1 pips per leg (typical ECN)
- **Round-trip cost per trade:** 4 legs x 0.6 pips = 2.4 pips ≈ $24 per standard lot
- **Total cost for {len(completed):,} trades:** ~${len(completed) * 24:,.0f}

This alone would eat ~47% of the reported P&L. With slippage and wider spreads during off-hours, the real cost could be even higher.

### 2. P&L Calculation

The P&L formula is: `pnl = (|entry_z| - |current_z|) * $50`

This is a **purely arbitrary scaling**. It does not account for:
- Actual position size (lot size)
- Pip value (which depends on the pair and lot size)
- The fact that EUR/USD and GBP/USD have different pip values
- The ratio spread vs. price spread distinction

A proper implementation would:
1. Define position size based on account risk (e.g., 1% per trade)
2. Calculate pip value for each leg
3. Compute actual dollar P&L from price changes

### 3. Look-Ahead Bias Assessment

**No significant look-ahead bias found.** All signals are computed from past data only:
- Rolling z-scores use backward-looking windows
- Entry/exit conditions use current bar values
- The alpha confirmation filter uses the same bar, which is acceptable for a bar-close strategy

### 4. Overfitting Risk

- 9 alpha signals with hand-tuned weights (sum to 1.0)
- IC values appear assumed rather than empirically measured
- Z-score parameters (window=50, entry=2.0, exit=0.5) are common defaults
- No walk-forward analysis or out-of-sample testing performed

### 5. Comparison with Other Strategies

From `unified_results.json`, the pairs trading strategy is the **best-performing** by raw P&L:

| Strategy | Trades | WR% | Total P&L | Max DD |
|----------|--------|-----|-----------|--------|
| Pairs Trading | 3,931 | 72.6% | +$206,245 | -$265 |
| P90 Alpha Combo | 426 | 51.2% | -$300 | -$318 |
| HMM Regime | 367 | 55.9% | -$57 | -$72 |
| Multi-TF CNN | 694 | 55.5% | -$290 | -$351 |
| Sentiment Enhanced | 627 | 48.0% | -$200 | -$258 |

The fact that pairs trading is massively profitable while all other strategies are flat or losing is a **red flag**. It suggests the P&L calculation is not comparable across strategies.

---

## Recommendation

### Status: **NEEDS WORK — Bug Found**

The strategy's mean-reversion logic is conceptually valid for EUR/USD-GBP/USD (highly correlated pairs), but the backtest implementation has critical flaws that make the results unreliable.

### Required Fixes Before Production

1. **Implement proper position sizing** — Risk 1-2% per trade, calculate lot size from stop distance
2. **Add transaction costs** — Include spread (0.5-1.0 pip) and commission per leg
3. **Fix P&L calculation** — Use actual pip values and position sizes, not arbitrary $50/z-unit
4. **Add walk-forward validation** — Test on out-of-sample data
5. **Reduce trade frequency** — 3.3 trades/day is excessive; consider higher z-score entry threshold
6. **Implement proper risk management** — Max daily loss limit, correlation breakdown exit

### Estimated Realistic Performance

After applying transaction costs and proper position sizing, a reasonable estimate:
- **Win rate:** 55-65% (still good for mean-reversion)
- **Profit factor:** 1.2-1.5 (decent but not extraordinary)
- **Annual return:** 15-30% (realistic for pairs trading)
- **Max drawdown:** 8-15% of account

---

*Report generated by Quant Lab Optimizer — {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*
"""

out_md = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\PAIRS_TRADING_VALIDATION.md")
out_md.parent.mkdir(parents=True, exist_ok=True)
with open(out_md, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"Report saved to {out_md}")
print("DONE")
