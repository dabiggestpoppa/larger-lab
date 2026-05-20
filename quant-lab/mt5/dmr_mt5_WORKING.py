#!/usr/bin/env python3
"""
DMR (Deep Mean Reversion) MT5 Backtest — WORKING VERSION
==========================================================
Based on the OPTIMIZER v2 code that produced 91.8% WR on EUR/USD.
This is the EXACT logic from run_deep_mean_reversion() in optimizer_v2.py,
adapted to use MT5 data instead of CSV files.

Strategy (simple, clean):
1. Find P90 candle in 2-11 AM EST
2. Calculate 200% Deep State extension level
3. Wait for price to touch Deep State
4. Enter mean reversion (AGAINST P90 direction) at Deep State
5. SL at 220% (kill switch), TP at P90 activation level (0%)
6. Hard exit at 5 PM EST

Data: MT5 EUR/USD M5, Jan 2022 - May 2026
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import time

# ── Configuration ────────────────────────────────────────────────────────────
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
START_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2026, 5, 1, tzinfo=timezone.utc)
INITIAL_EQUITY = 10000.0
RISK_PCT = 0.0025  # 0.25% per trade

RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")
RESULTS_DIR.mkdir(exist_ok=True)

# ── P90 Thresholds (from optimizer_v2.py) ───────────────────────────────────
def p90_threshold(est_h):
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    if est_h < 11: return 6.2
    return 99.0

# ── Utility Functions ────────────────────────────────────────────────────────
def to_pips(price_diff, pair="EUR/USD"):
    if "JPY" in pair: return price_diff * 100.0
    return price_diff * 10000.0

def to_price(pips, pair="EUR/USD"):
    if "JPY" in pair: return pips / 100.0
    return pips / 10000.0

def calc_results(trades, name, pair="EUR/USD"):
    if not trades:
        return {"strategy": name, "pair": pair, "total_trades": 0, "error": "No trades"}
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    wr = len(wins) / len(pnls) * 100 if pnls else 0
    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else 0
    cum, peak, max_dd = [0], 0, 0
    for p in pnls:
        cum.append(cum[-1] + p)
    for v in cum:
        if v > peak: peak = v
        max_dd = min(max_dd, v - peak)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0
    expectancy = total / len(pnls) if pnls else 0
    by_exit = {}
    for t in trades:
        k = t.get('reason', 'unknown')
        by_exit[k] = by_exit.get(k, 0) + 1
    return {
        "strategy": name, "pair": pair,
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(wr, 1), "total_pnl": round(total, 2),
        "avg_win": round(avg_w, 2), "avg_loss": round(avg_l, 2),
        "max_dd": round(max_dd, 2), "profit_factor": round(pf, 2),
        "expectancy": round(expectancy, 3),
        "by_exit": by_exit,
    }

def manage_trade(bars_list, entry_price, direction, sl, tp, hard_exit_est=17):
    """Manage a single trade through subsequent bars. Returns trade dict."""
    if not bars_list:
        return None
    for bar in bars_list:
        h, l, c, est_h = bar['high'], bar['low'], bar['close'], bar['est_h']
        if est_h >= hard_exit_est:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit', 'exit_price': c, 'exit_time': bar['time']}
        if direction == 'LONG':
            if l <= sl:
                pnl = to_pips(sl - entry_price)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl',
                        'exit_price': sl, 'exit_time': bar['time']}
            if h >= tp:
                pnl = to_pips(tp - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp, 'exit_time': bar['time']}
        else:  # SHORT
            if h >= sl:
                pnl = to_pips(entry_price - sl)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl',
                        'exit_price': sl, 'exit_time': bar['time']}
            if l <= tp:
                pnl = to_pips(entry_price - tp)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp, 'exit_time': bar['time']}
    # End of data
    last = bars_list[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': last['time']}

# ── Main Backtest ────────────────────────────────────────────────────────────
def run_dmr_backtest():
    print("=" * 60)
    print("DMR MT5 Backtest — WORKING VERSION (optimizer_v2 logic)")
    print("=" * 60)
    
    # Connect to MT5
    if not mt5.initialize():
        print("❌ MT5 initialize failed:", mt5.last_error())
        return None
    
    try:
        # Get terminal info
        terminal = mt5.terminal_info()
        if terminal:
            print(f"✅ Connected: {terminal.company} | Build {terminal.build}")
        
        # Check symbol
        symbol_info = mt5.symbol_info(SYMBOL)
        if symbol_info is None:
            print(f"❌ Symbol {SYMBOL} not found")
            return None
        print(f"✅ Symbol: {SYMBOL} | Digits: {symbol_info.digits}")
        
        # Fetch M5 data
        print(f"\n📊 Fetching {SYMBOL} M5 data: {START_DATE} → {END_DATE}...")
        t0 = time.time()
        rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, START_DATE, END_DATE)
        
        if rates is None or len(rates) == 0:
            print(f"❌ No data returned. Error: {mt5.last_error()}")
            return None
        
        elapsed = time.time() - t0
        print(f"✅ Loaded {len(rates):,} bars in {elapsed:.1f}s")
        print(f"   Date range: {datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc)} → "
              f"{datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)}")
        
        # Convert to list of dicts with EST hours
        print("\n🔧 Preparing data...")
        bars = []
        for r in rates:
            ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
            utc_h = ts.hour
            est_h = (utc_h - 5 + 24) % 24
            date = ts.date()
            bars.append({
                'time': ts,
                'utc_h': utc_h,
                'est_h': est_h,
                'date': date,
                'open': r['open'],
                'high': r['high'],
                'low': r['low'],
                'close': r['close'],
                'volume': r['tick_volume'],
            })
        
        # Group by date
        days = {}
        for bar in bars:
            d = bar['date']
            if d not in days:
                days[d] = []
            days[d].append(bar)
        
        print(f"📅 Trading days: {len(days)}")
        
        # ── Run DMR Strategy ──────────────────────────────────────────────
        print("\n🚀 Running DMR strategy...")
        trades = []
        skipped_no_asian = 0
        skipped_ar_too_big = 0
        skipped_ar_too_small = 0
        skipped_no_p90 = 0
        skipped_no_touch = 0
        
        for date in sorted(days.keys()):
            day_bars = days[date]
            day_df = pd.DataFrame(day_bars)
            
            # Calculate Asian Range (7PM-3AM EST)
            asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
            if len(asian) < 2:
                skipped_no_asian += 1
                continue
            
            ah = asian['high'].max()
            al = asian['low'].min()
            ar = to_pips(ah - al)
            
            if ar > 45:
                skipped_ar_too_big += 1
                continue
            if ar < 3:
                skipped_ar_too_small += 1
                continue
            
            # Find P90 signal in 2-11 AM EST
            entry_window = day_df[(day_df['est_h'] >= 2) & (day_df['est_h'] < 11)]
            direction = None
            p90_bar = None
            
            for _, row in entry_window.iterrows():
                body_pips = to_pips(abs(row['close'] - row['open']))
                thresh = p90_threshold(row['est_h'])
                if body_pips >= thresh:
                    direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                    p90_bar = row
                    break
            
            if direction is None:
                skipped_no_p90 += 1
                continue
            
            activation = p90_bar['close']
            body_pips = to_pips(abs(p90_bar['close'] - p90_bar['open']))
            
            # Extension levels
            deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
            kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
            
            # Wait for price to touch Deep State after P90
            p90_time = p90_bar['time']
            post_p90 = day_df[day_df['time'] > p90_time]
            post_p90 = post_p90[post_p90['est_h'] < 12]
            
            if post_p90.empty:
                skipped_no_touch += 1
                continue
            
            touch_idx = None
            for i, (_, row) in enumerate(post_p90.iterrows()):
                if direction == 'LONG' and row['low'] <= deep_state:
                    touch_idx = i
                    break
                elif direction == 'SHORT' and row['high'] >= deep_state:
                    touch_idx = i
                    break
            
            if touch_idx is None:
                skipped_no_touch += 1
                continue
            
            # Mean reversion: trade AGAINST the P90 direction
            rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
            rev_entry = deep_state
            rev_sl = kill_switch
            rev_tp = activation  # Return to 0%
            
            # Get bars after touch for trade management
            touch_time = post_p90.iloc[touch_idx]['time']
            post_entry = day_df[day_df['time'] > touch_time]
            post_entry = post_entry[post_entry['est_h'] < 17]
            
            if post_entry.empty:
                skipped_no_touch += 1
                continue
            
            post_list = post_entry.to_dict('records')
            trade = manage_trade(post_list, rev_entry, rev_direction, rev_sl, rev_tp)
            
            if trade:
                trade['entry_time'] = touch_time
                trade['ar_pips'] = ar
                trade['direction'] = rev_direction
                trade['p90_direction'] = direction
                trade['deep_state'] = deep_state
                trade['activation'] = activation
                trades.append(trade)
        
        # ── Results ────────────────────────────────────────────────────────
        results = calc_results(trades, "Deep_Mean_Reversion", SYMBOL)
        
        print(f"\n{'=' * 60}")
        print("RESULTS")
        print(f"{'=' * 60}")
        print(f"Total Trades:    {results['total_trades']}")
        print(f"Wins/Losses:     {results['wins']}/{results['losses']}")
        print(f"Win Rate:        {results['win_rate']}%")
        print(f"Total PnL:       {results['total_pnl']} pips")
        print(f"Avg Win:         {results['avg_win']} pips")
        print(f"Avg Loss:        {results['avg_loss']} pips")
        print(f"Max Drawdown:    {results['max_dd']} pips")
        print(f"Profit Factor:   {results['profit_factor']}")
        print(f"Expectancy:      {results['expectancy']} pips")
        print(f"\nExit Reasons:    {results.get('by_exit', {})}")
        print(f"\nSkip Stats:")
        print(f"  No Asian bars:   {skipped_no_asian}")
        print(f"  AR > 45 pips:    {skipped_ar_too_big}")
        print(f"  AR < 3 pips:     {skipped_ar_too_small}")
        print(f"  No P90 signal:   {skipped_no_p90}")
        print(f"  No DS touch:     {skipped_no_touch}")
        
        # Compare with optimizer
        print(f"\n{'=' * 60}")
        print("COMPARISON: MT5 vs Python Optimizer v4b")
        print(f"{'=' * 60}")
        print(f"{'Metric':<20} {'MT5':>10} {'Optimizer':>10} {'Delta':>10}")
        print(f"{'─'*50}")
        opt_wr, opt_pnl, opt_pf, opt_dd, opt_exp = 91.8, 8745.68, 111.96, -5.02, 11.447
        mt5_wr = results['win_rate']
        mt5_pnl = results['total_pnl']
        mt5_pf = results['profit_factor']
        mt5_dd = results['max_dd']
        mt5_exp = results['expectancy']
        print(f"{'Win Rate':<20} {mt5_wr:>9.1f}% {opt_wr:>9.1f}% {mt5_wr-opt_wr:>9.1f}%")
        print(f"{'Total PnL':<20} {mt5_pnl:>10.1f} {opt_pnl:>10.1f} {mt5_pnl-opt_pnl:>10.1f}")
        print(f"{'Profit Factor':<20} {mt5_pf:>10.2f} {opt_pf:>10.2f} {mt5_pf-opt_pf:>10.2f}")
        print(f"{'Max DD':<20} {mt5_dd:>10.1f} {opt_dd:>10.1f} {mt5_dd-opt_dd:>10.1f}")
        print(f"{'Expectancy':<20} {mt5_exp:>10.3f} {opt_exp:>10.3f} {mt5_exp-opt_exp:>10.3f}")
        
        # Save results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        output = {
            "strategy": "Deep_Mean_Reversion_WORKING",
            "source": "MT5_Backtest_optimizer_v2_logic",
            "symbol": SYMBOL,
            "timeframe": "M5",
            "period": f"{START_DATE.date()} to {END_DATE.date()}",
            "total_bars": len(rates),
            "trading_days": len(days),
            **results,
            "skip_stats": {
                "no_asian_bars": skipped_no_asian,
                "ar_too_big": skipped_ar_too_big,
                "ar_too_small": skipped_ar_too_small,
                "no_p90": skipped_no_p90,
                "no_deep_state_touch": skipped_no_touch,
            }
        }
        
        json_path = RESULTS_DIR / f"dmr_mt5_working_{ts}.json"
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print(f"\n💾 Results saved: {json_path}")
        
        # Save trades CSV
        if trades:
            trades_df = pd.DataFrame(trades)
            csv_path = RESULTS_DIR / f"dmr_mt5_working_trades_{ts}.csv"
            trades_df.to_csv(csv_path, index=False)
            print(f"💾 Trades saved: {csv_path}")
        
        return results
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    results = run_dmr_backtest()
