"""
Investigate the gap between backtest WR (82-98%) and live WR (42-55%).
Key hypothesis: The backtest used a DIFFERENT engine configuration or data period.
Let's check what the actual backtest infrastructure produces.
"""
import sys, os, csv, json
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from engines.p90_engine import (
    P90Engine, TradeDirection, P90Variant, EngineState, Bar,
    classify_tier, MIN_P90_BODY, MIN_RR
)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Focus on EURUSD — the pair with most data and clearest signal
CSV_FILE = os.path.join(DATA_DIR, 'EURUSD_M5.csv')


def load_csv(filepath):
    """Load ALL bars"""
    bars = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            try:
                if len(row) >= 5:
                    ts_str = row[0]
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        try:
                            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            ts = datetime.strptime(ts_str, '%Y.%m.%d %H:%M')
                    o, h, l, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                    bars.append(Bar(timestamp=ts, open=o, high=h, low=l, close=c))
            except:
                continue
    return bars


def run_detailed_backtest(symbol, bars):
    """Run with detailed logging to understand WHY trades lose."""
    engine = P90Engine(
        pip_size=0.0001,
        symbol=symbol,
    )
    
    trades = []
    asian_high = None
    asian_low = None
    session_count = 0
    
    for i, bar in enumerate(bars):
        ts = bar.timestamp
        est_hour = (ts.hour - 5) % 24
        
        if est_hour >= 19 or est_hour < 3:
            if asian_high is None:
                asian_high = bar.high
                asian_low = bar.low
            else:
                asian_high = max(asian_high, bar.high)
                asian_low = min(asian_low, bar.low)
        
        if est_hour == 3 and asian_high is not None and not engine.session_active:
            engine.initialize_session(asian_high, asian_low)
            asian_high = None
            asian_low = None
            session_count += 1
        
        if not engine.session_active:
            continue
        
        if est_hour == 12:
            if engine.state == EngineState.IN_TRADE:
                entry = engine.entry_price
                direction = engine.direction
                if direction == TradeDirection.LONG:
                    pnl = (bar.close - entry) / engine.pip_size
                else:
                    pnl = (entry - bar.close) / engine.pip_size
                trades.append({
                    'outcome': '12PM',
                    'pnl_pips': pnl,
                    'variant': engine.active_variant.value,
                    'direction': 'LONG' if direction == TradeDirection.LONG else 'SHORT',
                    'session': session_count,
                })
            engine.hard_exit()
            continue
        
        sig = engine.process_bar(bar)
        
        if sig and sig.event == 'ENTRY':
            entry = sig.entry_price
            sl = sig.sl_price
            tp1 = sig.tp_price
            direction = 'LONG' if sig.direction == TradeDirection.LONG else 'SHORT'
            variant = sig.variant
            
            # Extended lookahead — 500 bars (~41 hours)
            outcome = None
            exit_price = None
            bars_held = 0
            for j in range(i + 1, min(i + 500, len(bars))):
                bars_held += 1
                fb = bars[j]
                # Check if 12PM exit would have hit
                fb_est = (fb.timestamp.hour - 5) % 24
                if fb_est == 12:
                    outcome = '12PM'
                    exit_price = fb.close
                    break
                if direction == 'LONG':
                    if fb.low <= sl:
                        outcome = 'SL'
                        exit_price = sl
                        break
                    if fb.high >= tp1:
                        outcome = 'TP'
                        exit_price = tp1
                        break
                else:
                    if fb.high >= sl:
                        outcome = 'SL'
                        exit_price = sl
                        break
                    if fb.low <= tp1:
                        outcome = 'TP'
                        exit_price = tp1
                        break
            
            if outcome is None:
                outcome = 'TIMEOUT'
                exit_price = bars[min(i + 499, len(bars) - 1)].close
            
            if direction == 'LONG':
                pnl = (exit_price - entry) / engine.pip_size
            else:
                pnl = (entry - exit_price) / engine.pip_size
            
            trades.append({
                'outcome': outcome,
                'pnl_pips': pnl,
                'variant': variant.value,
                'direction': direction,
                'session': session_count,
                'bars_held': bars_held,
                'rr': abs(tp1 - entry) / abs(sl - entry) if sl != entry else 0,
            })
    
    return trades, session_count


print("Loading EURUSD data...")
bars = load_csv(CSV_FILE)
print(f"Total bars: {len(bars)}")
print(f"Date range: {bars[0].timestamp} to {bars[-1].timestamp}")

trades, sessions = run_detailed_backtest('EURUSD', bars)

print(f"\nSessions: {sessions}")
print(f"Trades: {len(trades)}")

# Overall stats
tp_count = sum(1 for t in trades if t['outcome'] == 'TP')
sl_count = sum(1 for t in trades if t['outcome'] == 'SL')
pm_count = sum(1 for t in trades if t['outcome'] == '12PM')
to_count = sum(1 for t in trades if t['outcome'] == 'TIMEOUT')
closed = tp_count + sl_count
wr = (tp_count / closed * 100) if closed > 0 else 0

print(f"\n=== OUTCOME DISTRIBUTION ===")
print(f"TP:   {tp_count:>4} ({tp_count/len(trades)*100:.1f}%)")
print(f"SL:   {sl_count:>4} ({sl_count/len(trades)*100:.1f}%)")
print(f"12PM: {pm_count:>4} ({pm_count/len(trades)*100:.1f}%)")
print(f"T/O:  {to_count:>4} ({to_count/len(trades)*100:.1f}%)")
print(f"WR (TP/closed): {wr:.1f}%")

# PnL analysis
tp_pnl = [t['pnl_pips'] for t in trades if t['outcome'] == 'TP']
sl_pnl = [t['pnl_pips'] for t in trades if t['outcome'] == 'SL']
pm_pnl = [t['pnl_pips'] for t in trades if t['outcome'] == '12PM']

print(f"\n=== PNL ANALYSIS ===")
print(f"TP avg:   {sum(tp_pnl)/len(tp_pnl):.1f}p (n={len(tp_pnl)})" if tp_pnl else "TP: none")
print(f"SL avg:   {sum(sl_pnl)/len(sl_pnl):.1f}p (n={len(sl_pnl)})" if sl_pnl else "SL: none")
print(f"12PM avg: {sum(pm_pnl)/len(pm_pnl):.1f}p (n={len(pm_pnl)})" if pm_pnl else "12PM: none")
print(f"Total gross: {sum(t['pnl_pips'] for t in trades):.1f}p")

# Initial vs Cascade
init_trades = [t for t in trades if t['variant'] == 'INITIAL']
cas_trades = [t for t in trades if t['variant'] == 'CASCADE']

def variant_stats(name, vt):
    if not vt:
        print(f"\n{name}: 0 trades")
        return
    tp = sum(1 for t in vt if t['outcome'] == 'TP')
    sl = sum(1 for t in vt if t['outcome'] == 'SL')
    pm = sum(1 for t in vt if t['outcome'] == '12PM')
    closed = tp + sl
    wr = (tp / closed * 100) if closed > 0 else 0
    pnl = sum(t['pnl_pips'] for t in vt)
    print(f"\n{name}: {len(vt)} trades | {tp}W/{sl}L/{pm}12PM | WR {wr:.1f}% | Total {pnl:.1f}p")
    print(f"  TP avg: {sum(t['pnl_pips'] for t in vt if t['outcome']=='TP')/max(tp,1):.1f}p")
    print(f"  SL avg: {sum(t['pnl_pips'] for t in vt if t['outcome']=='SL')/max(sl,1):.1f}p")
    print(f"  12PM avg: {sum(t['pnl_pips'] for t in vt if t['outcome']=='12PM')/max(pm,1):.1f}p")

variant_stats("INITIAL", init_trades)
variant_stats("CASCADE", cas_trades)

# Analyze 12PM exits — are they winners or losers?
print(f"\n=== 12PM EXIT ANALYSIS ===")
pm_winners = sum(1 for t in trades if t['outcome'] == '12PM' and t['pnl_pips'] > 0)
pm_losers = sum(1 for t in trades if t['outcome'] == '12PM' and t['pnl_pips'] < 0)
pm_zero = sum(1 for t in trades if t['outcome'] == '12PM' and t['pnl_pips'] == 0)
print(f"12PM winners: {pm_winners}")
print(f"12PM losers: {pm_losers}")
print(f"12PM breakeven: {pm_zero}")
if pm_count > 0:
    print(f"12PM as % of all trades: {pm_count/len(trades)*100:.1f}%")
    print(f"12PM that are losers: {pm_losers/pm_count*100:.1f}%")

# What if we removed 12PM exits (let trades run)?
print(f"\n=== COUNTERFACTUAL: NO 12PM EXIT ===")
hypo_tp = tp_count + sum(1 for t in trades if t['outcome'] == '12PM' and t['pnl_pips'] > 0)
hypo_sl = sl_count + sum(1 for t in trades if t['outcome'] == '12PM' and t['pnl_pips'] < 0)
hypo_closed = hypo_tp + hypo_sl
hypo_wr = (hypo_tp / hypo_closed * 100) if hypo_closed > 0 else 0
print(f"Hypothetical WR (counting 12PM winners as TP): {hypo_wr:.1f}%")
print(f"Hypothetical total pnl: {sum(t['pnl_pips'] for t in trades if t['outcome'] in ('TP','SL') or (t['outcome']=='12PM' and t['pnl_pips']>0)):.1f}p")

# Analyze by session number (early vs late in dataset)
print(f"\n=== WR BY SESSION QUARTILE ===")
sessions_list = sorted(set(t['session'] for t in trades))
q1 = len(sessions_list) // 4
q2 = q1 * 2
q3 = q1 * 3

for label, start, end in [("Q1 (early)", 0, q1), ("Q2", q1, q2), ("Q3", q2, q3), ("Q4 (late)", q3, len(sessions_list))]:
    st = [t for t in trades if start <= t['session'] < end]
    if st:
        tp = sum(1 for t in st if t['outcome'] == 'TP')
        sl = sum(1 for t in st if t['outcome'] == 'SL')
        closed = tp + sl
        wr = (tp / closed * 100) if closed > 0 else 0
        pnl = sum(t['pnl_pips'] for t in st)
        print(f"  {label}: {len(st)} trades | {tp}W/{sl}L | WR {wr:.1f}% | PnL {pnl:.1f}p")
