"""
DMR (Deep Mean Reversion) Backtest — Python/Nautilus-compatible
Uses EXACT optimizer_v2 logic that produced 94.8% WR benchmark.

This is the GOLD STANDARD backtest that Nautilus results will be compared against.

DMR Logic:
  1. Asian Range: 7PM-3AM EST, lock at 3AM (valid: 3-45 pips)
  2. P90 Detection: 2AM-11AM, body >= threshold by hour
  3. Deep State: activation + body*2.0 in P90 direction
  4. Touch: price touches DS before noon
  5. Entry: mean reversion (against P90), entry=DS, SL=KS(2.2x), TP=activation
  6. Management: 1 trade/day, hard exit 5PM

Reference: 94.8% WR, 671 trades, +7903 pips, PF 205 (EUR/USD 2022-2026)
"""
import sys, os, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pytz

EST = pytz.timezone('US/Eastern')

MT5_EXE = r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe"
REPORTS_DIR = Path(__file__).parent.parent / 'reports'
DATA_DIR = Path(__file__).parent.parent / 'data'

# ─── P90 THRESHOLDS (EUR/USD by EST hour) ───────────────────────
P90_THRESHOLDS_EURUSD = {
    2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2,
}

# ─── SYMBOL CONFIG ──────────────────────────────────────────────
SYMBOLS = {
    'EURUSD.PRO': {
        'thresholds': P90_THRESHOLDS_EURUSD,
        'pip_divisor': 10000.0,
        'name': 'EURUSD',
    },
}


def price_to_pips(price, divisor):
    return price * divisor

def pips_to_price(pips, divisor):
    return pips / divisor


def is_new_yesterday_bar(ts_est, prev_ts_est):
    """Check if we've crossed midnight EST"""
    return ts_est.date() != prev_ts_est.date()


def run_dmr_backtest(df, symbol_config):
    """Run DMR strategy on a DataFrame of M5 bars"""
    thresholds = symbol_config['thresholds']
    pip_div = symbol_config['pip_divisor']
    
    trades = []
    daily_pnl = {}
    
    # State variables
    asian_high = 0.0
    asian_low = 999.0
    ar_locked = False
    current_date = None
    
    p90_found = False
    ds_touched = False
    trade_placed = False
    
    p90_direction = 0
    activation_level = 0.0
    deep_state_level = 0.0
    kill_switch_level = 0.0
    p90_body_pips = 0.0
    today_trades = 0
    
    position = 0
    entry_price = 0.0
    sl_price = 0.0
    tp_price = 0.0
    entry_time = None
    
    position_open = False
    
    for i in range(len(df)):
        row = df.iloc[i]
        ts = row['timestamp']
        
        # Convert to EST
        if ts.tzinfo is None:
            ts = pytz.utc.localize(ts)
        ts_est = ts.astimezone(EST)
        est_hour = ts_est.hour
        bar_date = ts_est.date()
        
        o = float(row['open'])
        h = float(row['high'])
        l = float(row['low'])
        c = float(row['close'])
        
        # ─── NEW DAY RESET ──────────────────────────────────
        if current_date != bar_date:
            # Close any position at day change
            if position_open and entry_price > 0:
                if position == 1:
                    pnl_pips = (c - entry_price) * pip_div
                else:
                    pnl_pips = (entry_price - c) * pip_div
                trades.append({
                    'entry_time': entry_time, 'exit_time': ts_est,
                    'direction': 'LONG' if position == 1 else 'SHORT',
                    'entry': entry_price, 'exit': c,
                    'pnl_pips': round(pnl_pips, 1),
                    'result': 'WIN' if pnl_pips > 0 else 'LOSS',
                    'exit_reason': 'new_day',
                })
                key = str(current_date) if current_date else 'unknown'
                daily_pnl[key] = daily_pnl.get(key, 0) + pnl_pips
                position_open = False
                position = 0
            
            current_date = bar_date
            asian_high = 0.0
            asian_low = 999.0
            ar_locked = False
            p90_found = False
            ds_touched = False
            trade_placed = False
            p90_direction = 0
            today_trades = 0
            p90_body_pips = 0.0
        
        # ─── ASIAN RANGE (7PM-3AM EST) ──────────────────────
        if est_hour >= 19 or est_hour < 3:
            if h > asian_high:
                asian_high = h
            if l < asian_low:
                asian_low = l
        
        # ─── LOCK AR AT 3AM ─────────────────────────────────
        if est_hour == 3 and not ar_locked:
            ar_locked = True
            ar_pips = price_to_pips(asian_high - asian_low, pip_div)
        
        # ─── CHECK TP/SL FOR OPEN POSITION ──────────────────
        if position_open:
            if position == 1:  # LONG
                if l <= sl_price:
                    pnl_pips = (sl_price - entry_price) * pip_div
                    trades.append({
                        'entry_time': entry_time, 'exit_time': ts_est,
                        'direction': 'LONG', 'entry': entry_price, 'exit': sl_price,
                        'pnl_pips': round(-abs(pnl_pips), 1),
                        'result': 'LOSS', 'exit_reason': 'SL',
                    })
                    daily_pnl[str(bar_date)] = daily_pnl.get(str(bar_date), 0) - abs(pnl_pips)
                    position_open = False
                    position = 0
                    trade_placed = True
                    continue
                if h >= tp_price:
                    pnl_pips = (tp_price - entry_price) * pip_div
                    trades.append({
                        'entry_time': entry_time, 'exit_time': ts_est,
                        'direction': 'LONG', 'entry': entry_price, 'exit': tp_price,
                        'pnl_pips': round(pnl_pips, 1),
                        'result': 'WIN', 'exit_reason': 'TP',
                    })
                    daily_pnl[str(bar_date)] = daily_pnl.get(str(bar_date), 0) + pnl_pips
                    position_open = False
                    position = 0
                    trade_placed = True
                    continue
            else:  # SHORT
                if h >= sl_price:
                    pnl_pips = (entry_price - sl_price) * pip_div
                    trades.append({
                        'entry_time': entry_time, 'exit_time': ts_est,
                        'direction': 'SHORT', 'entry': entry_price, 'exit': sl_price,
                        'pnl_pips': round(-abs(pnl_pips), 1),
                        'result': 'LOSS', 'exit_reason': 'SL',
                    })
                    daily_pnl[str(bar_date)] = daily_pnl.get(str(bar_date), 0) - abs(pnl_pips)
                    position_open = False
                    position = 0
                    trade_placed = True
                    continue
                if l <= tp_price:
                    pnl_pips = (entry_price - tp_price) * pip_div
                    trades.append({
                        'entry_time': entry_time, 'exit_time': ts_est,
                        'direction': 'SHORT', 'entry': entry_price, 'exit': tp_price,
                        'pnl_pips': round(pnl_pips, 1),
                        'result': 'WIN', 'exit_reason': 'TP',
                    })
                    daily_pnl[str(bar_date)] = daily_pnl.get(str(bar_date), 0) + pnl_pips
                    position_open = False
                    position = 0
                    trade_placed = True
                    continue
            
            # Hard exit at 5PM
            if est_hour >= 17:
                if position == 1:
                    pnl_pips = (c - entry_price) * pip_div
                else:
                    pnl_pips = (entry_price - c) * pip_div
                trades.append({
                    'entry_time': entry_time, 'exit_time': ts_est,
                    'direction': 'LONG' if position == 1 else 'SHORT',
                    'entry': entry_price, 'exit': c,
                    'pnl_pips': round(pnl_pips, 1),
                    'result': 'WIN' if pnl_pips > 0 else 'LOSS',
                    'exit_reason': 'hard_exit',
                })
                daily_pnl[str(bar_date)] = daily_pnl.get(str(bar_date), 0) + pnl_pips
                position_open = False
                position = 0
                trade_placed = True
                continue
        
        # ─── NO TRADING BEFORE 2AM OR AFTER HARD EXIT ───────
        if est_hour < 2:
            continue
        
        # ─── P90 DETECTION (2AM-11AM) ────────────────────────
        if not p90_found and not trade_placed and 2 <= est_hour < 11:
            threshold = thresholds.get(est_hour, 999.0)
            body = abs(c - o)
            body_pips = price_to_pips(body, pip_div)
            
            if body_pips >= threshold:
                p90_found = True
                p90_body_pips = body_pips
                activation_level = c
                
                if c > o:  # bullish P90
                    p90_direction = 1
                    deep_state_level = activation_level + pips_to_price(body_pips * 2.0, pip_div)
                    kill_switch_level = activation_level + pips_to_price(body_pips * 2.2, pip_div)
                else:  # bearish P90
                    p90_direction = -1
                    deep_state_level = activation_level - pips_to_price(body_pips * 2.0, pip_div)
                    kill_switch_level = activation_level - pips_to_price(body_pips * 2.2, pip_div)
                continue
        
        # ─── DEEP STATE TOUCH ────────────────────────────────
        if p90_found and not ds_touched and not trade_placed and est_hour < 12:
            if p90_direction == 1 and l <= deep_state_level:
                ds_touched = True
                continue
            elif p90_direction == -1 and h >= deep_state_level:
                ds_touched = True
                continue
        
        # ─── ENTRY (Mean Reversion) ──────────────────────────
        if ds_touched and not trade_placed and today_trades < 1 and est_hour < 12:
            if p90_direction == 1:
                # P90 bullish → SELL
                position = -1
                entry_price = deep_state_level
                sl_price = kill_switch_level
                tp_price = activation_level
            else:
                # P90 bearish → BUY
                position = 1
                entry_price = deep_state_level
                sl_price = kill_switch_level
                tp_price = activation_level
            
            entry_time = ts_est
            position_open = True
            trade_placed = True
            today_trades += 1
    
    return trades, daily_pnl


def compute_stats(trades):
    """Compute backtest statistics"""
    if not trades:
        return {'trades': 0, 'wr': 0, 'pnl': 0, 'pf': 0}
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    total = len(trades)
    wr = len(wins) / total * 100
    total_pnl = sum(t['pnl_pips'] for t in trades)
    gross_win = sum(t['pnl_pips'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_pips'] for t in losses)) if losses else 1
    pf = gross_win / gross_loss if gross_loss > 0 else 0
    
    # Max consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    cw = 0
    cl = 0
    for t in trades:
        if t['result'] == 'WIN':
            cw += 1
            cl = 0
            max_consec_wins = max(max_consec_wins, cw)
        else:
            cl += 1
            cw = 0
            max_consec_losses = max(max_consec_losses, cl)
    
    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t['pnl_pips']
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)
    
    return {
        'trades': total,
        'wins': len(wins),
        'losses': len(losses),
        'wr': round(wr, 1),
        'pnl_pips': round(total_pnl, 1),
        'pf': round(pf, 1),
        'avg_win': round(gross_win / len(wins), 1) if wins else 0,
        'avg_loss': round(gross_loss / len(losses), 1) if losses else 0,
        'max_consec_wins': max_consec_wins,
        'max_consec_losses': max_consec_losses,
        'max_drawdown_pips': round(max_dd, 1),
    }


def main():
    import MetaTrader5 as mt5
    
    print("="*70)
    print("  DMR BACKTEST — Gold Standard Python Engine")
    print("="*70)
    
    # Step 1: Ensure MT5 running
    def mt5_running():
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], capture_output=True, text=True)
        return 'terminal64' in r.stdout
    
    if not mt5_running():
        print("Starting MT5...")
        subprocess.Popen([MT5_EXE])
        for _ in range(30):
            time.sleep(1)
            if mt5_running():
                time.sleep(5)
                break
        else:
            print("FAILED to start MT5")
            return
    else:
        print("MT5 running ✓")
    
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return
    
    account = mt5.account_info()
    print(f"Connected: {account.login} @ {account.server} | {account.balance} {account.currency}")
    
    # Step 2: Fetch data for all symbols
    all_trades = {}
    all_stats = {}
    
    for sym, config in SYMBOLS.items():
        name = config['name']
        print(f"\n{'─'*70}")
        print(f"  {name}")
        print(f"{'─'*70}")
        
        print(f"  Fetching M5 bars (2022-01-01 → now)...")
        rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, datetime(2022, 1, 1), datetime.now())
        
        if rates is None or len(rates) == 0:
            print(f"  FAILED: {mt5.last_error()}")
            continue
        
        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = df.drop(columns=['time'])
        df = df[df['timestamp'].dt.dayofweek < 5]
        
        print(f"  Data: {len(df):,} M5 bars ({df['timestamp'].min()} → {df['timestamp'].max()})")
        
        # Run backtest
        trades, daily_pnl = run_dmr_backtest(df, config)
        stats = compute_stats(trades)
        
        print(f"\n  Results:")
        print(f"  ├─ Trades:     {stats['trades']}")
        print(f"  ├─ Win Rate:   {stats['wr']}% ({stats['wins']}W / {stats['losses']}L)")
        print(f"  ├─ PnL:        {stats['pnl_pips']:+.1f} pips")
        print(f"  ├─ PF:         {stats['pf']}")
        print(f"  ├─ Avg Win:    {stats['avg_win']}p")
        print(f"  ├─ Avg Loss:   {stats['avg_loss']}p")
        print(f"  ├─ Max Cons W: {stats['max_consec_wins']}")
        print(f"  ├─ Max Cons L: {stats['max_consec_losses']}")
        print(f"  └─ Max DD:     {stats['max_drawdown_pips']}p")
        
        all_trades[name] = trades
        all_stats[name] = stats
    
    # Step 3: Save report
    mt5.shutdown()
    
    REPORTS_DIR.mkdir(exist_ok=True)
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save trades CSV
    for name, trades in all_trades.items():
        if trades:
            trades_df = pd.DataFrame(trades)
            trades_path = REPORTS_DIR / f"DMR_trades_{name}_{now_str}.csv"
            trades_df.to_csv(trades_path, index=False)
            print(f"\n  Trades saved: {trades_path}")
    
    # Save summary
    summary_path = REPORTS_DIR / f"DMR_summary_{now_str}.txt"
    with open(summary_path, 'w') as f:
        f.write(f"DMR BACKTEST SUMMARY — {datetime.now()}\n")
        f.write(f"Account: {account.login} @ {account.server}\n")
        f.write("="*50 + "\n")
        for name, stats in all_stats.items():
            f.write(f"\n{name}:\n")
            for k, v in stats.items():
                f.write(f"  {k}: {v}\n")
    
    print(f"  Summary: {summary_path}")
    
    print(f"\n{'='*70}")
    print(f"  COMPLETE")
    print(f"{'='*70}")
    
    # Benchmark comparison
    if 'EURUSD' in all_stats:
        s = all_stats['EURUSD']
        print(f"\n  Benchmark comparison:")
        print(f"  WR:   {s['wr']}%  (target: 94.8%)")
        print(f"  PnL:  {s['pnl_pips']:+}p  (target: +7903p)")


if __name__ == '__main__':
    main()
