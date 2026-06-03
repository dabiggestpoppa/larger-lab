"""Deep dive: Initial vs Cascade WR analysis — fixed"""
import sys, os, csv, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from engines.p90_engine import (
    P90Engine, TradeDirection, P90Variant, EngineState, Bar,
    classify_tier, MIN_P90_BODY, MIN_RR
)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

PAIRS = ['EURUSD', 'USDCHF', 'NZDUSD', 'GBPJPY', 'CHFJPY', 'GBPAUD',
         'GBPUSD', 'GBPNZD', 'GBPCHF', 'USDJPY']

CSV_FILES = {
    'EURUSD': 'EURUSD_M5.csv',
    'USDCHF': 'USDCHF_M5.csv',
    'NZDUSD': 'NZDUSD_M5.csv',
    'GBPJPY': 'GBPJPY_M5.csv',
    'CHFJPY': 'CHFJPY_M5.csv',
    'GBPAUD': 'GBPAUD_M5.csv',
    'GBPUSD': 'GBPUSD_M5.csv',
    'GBPNZD': 'GBPNZD_M5.csv',
    'GBPCHF': 'GBPCHF_M5.csv',
    'USDJPY': 'USDJPY_M5.csv',
}


def load_csv(filepath, max_bars=100000):
    bars = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for i, row in enumerate(reader):
            if i >= max_bars:
                break
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


def run_backtest(symbol, bars):
    engine = P90Engine(
        pip_size=0.01 if 'JPY' in symbol else 0.0001,
        symbol=symbol,
    )
    
    initial_trades = []
    cascade_trades = []
    asian_high = None
    asian_low = None
    
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
        
        if not engine.session_active:
            continue
        
        if est_hour == 12:
            if engine.state == EngineState.IN_TRADE:
                entry = engine.entry_price
                sl = engine.sl_price
                direction = engine.direction
                if direction == TradeDirection.LONG:
                    pnl = (bar.close - entry) / engine.pip_size
                else:
                    pnl = (entry - bar.close) / engine.pip_size
                trade = {'variant': engine.active_variant.value, 'outcome': '12PM', 'pnl_pips': pnl, 'direction': 'LONG' if direction == TradeDirection.LONG else 'SHORT'}
                if engine.active_variant == P90Variant.CASCADE:
                    cascade_trades.append(trade)
                else:
                    initial_trades.append(trade)
            engine.hard_exit()
            continue
        
        sig = engine.process_bar(bar)
        
        if sig and sig.event == 'ENTRY':
            entry = sig.entry_price
            sl = sig.sl_price
            tp1 = sig.tp_price
            direction = 'LONG' if sig.direction == TradeDirection.LONG else 'SHORT'
            variant = sig.variant
            
            outcome = None
            exit_price = None
            for j in range(i + 1, min(i + 200, len(bars))):
                fb = bars[j]
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
                exit_price = bars[min(i + 199, len(bars) - 1)].close
            
            if direction == 'LONG':
                pnl = (exit_price - entry) / engine.pip_size
            else:
                pnl = (entry - exit_price) / engine.pip_size
            
            trade = {
                'variant': variant.value,
                'outcome': outcome,
                'pnl_pips': pnl,
                'direction': direction,
            }
            
            if variant == P90Variant.CASCADE:
                cascade_trades.append(trade)
            else:
                initial_trades.append(trade)
    
    return initial_trades, cascade_trades


def stats(trades):
    if not trades:
        return {'count': 0, 'closed': 0, 'wins': 0, 'losses': 0, 'wr': 0, 'avg_pnl': 0, 'total_pnl': 0}
    wins = sum(1 for t in trades if t['outcome'] == 'TP')
    losses = sum(1 for t in trades if t['outcome'] == 'SL')
    closed = wins + losses
    wr = (wins / closed * 100) if closed > 0 else 0
    avg_pnl = sum(t['pnl_pips'] for t in trades) / len(trades)
    total_pnl = sum(t['pnl_pips'] for t in trades)
    return {'count': len(trades), 'closed': closed, 'wins': wins, 'losses': losses, 'wr': wr, 'avg_pnl': avg_pnl, 'total_pnl': total_pnl}


print("=" * 80)
print("DEEP DIVE: INITIAL vs CASCADE WR ANALYSIS (50K bars per asset)")
print("=" * 80)

results = {}
for symbol in PAIRS:
    csv_file = CSV_FILES[symbol]
    filepath = os.path.join(DATA_DIR, csv_file)
    if not os.path.exists(filepath):
        continue
    
    bars = load_csv(filepath, max_bars=50000)
    initial, cascade = run_backtest(symbol, bars)
    
    si = stats(initial)
    sc = stats(cascade)
    combined = initial + cascade
    st = stats(combined)
    
    results[symbol] = {'initial': si, 'cascade': sc, 'combined': st}
    
    print(f"\n{symbol}:")
    print(f"  INITIAL: {si['count']:>4} trades | {si['wins']:>3}W/{si['losses']:>3}L | WR {si['wr']:>5.1f}% | Avg {si['avg_pnl']:>+7.1f}p | Total {si['total_pnl']:>+8.1f}p")
    print(f"  CASCADE: {sc['count']:>4} trades | {sc['wins']:>3}W/{sc['losses']:>3}L | WR {sc['wr']:>5.1f}% | Avg {sc['avg_pnl']:>+7.1f}p | Total {sc['total_pnl']:>+8.1f}p")
    print(f"  COMBINED: {st['count']:>3} trades | {st['wins']:>3}W/{st['losses']:>3}L | WR {st['wr']:>5.1f}% | Avg {st['avg_pnl']:>+7.1f}p | Total {st['total_pnl']:>+8.1f}p")

# Summary table
print("\n" + "=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
print(f"{'Pair':<10} {'Init WR':>8} {'Init N':>6} {'Cas WR':>8} {'Cas N':>6} {'Comb WR':>8} {'Comb N':>6}")
print("-" * 80)
for sym in PAIRS:
    r = results.get(sym)
    if r:
        print(f"{sym:<10} {r['initial']['wr']:>7.1f}% {r['initial']['count']:>6} {r['cascade']['wr']:>7.1f}% {r['cascade']['count']:>6} {r['combined']['wr']:>7.1f}% {r['combined']['count']:>6}")

# Save
with open(os.path.join(os.path.dirname(__file__), 'reports', 'p90_wr_analysis.json'), 'w') as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved to reports/p90_wr_analysis.json")
