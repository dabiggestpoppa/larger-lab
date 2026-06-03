"""Deep dive: Initial vs Cascade WR analysis"""
import sys, os, csv

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
                        ts = __import__('datetime').datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        try:
                            ts = __import__('datetime').datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            ts = __import__('datetime').datetime.strptime(ts_str, '%Y.%m.%d %H:%M')
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
    
    for i, bar in enumerate(bars):
        ts = bar.timestamp
        est_hour = (ts.hour - 5) % 24
        
        # Asian range
        if not hasattr(engine, '_ah'):
            engine._ah = None
            engine._al = None
        
        if est_hour >= 19 or est_hour < 3:
            if engine._ah is None:
                engine._ah = bar.high
                engine._al = bar.low
            else:
                engine._ah = max(engine._ah, bar.high)
                engine._al = min(engine._al, bar.low)
        
        # Session init at 3AM EST
        if est_hour == 3 and engine._ah is not None and not engine.session_active:
            engine.initialize_session(engine._ah, engine._al)
            engine._ah = None
            engine._al = None
        
        if not engine.session_active:
            continue
        
        # 12PM exit
        if est_hour == 12:
            if engine.state == EngineState.IN_TRADE:
                outcome = '12PM' 
                direction = engine.direction
                entry = engine.entry_price
                sl = engine.sl_price
                
                if direction == TradeDirection.LONG:
                    pnl = (bar.close - entry) / engine.pip_size
                else:
                    pnl = (entry - bar.close) / engine.pip_size
                
                trade = {'variant': engine.active_variant.value, 'outcome': outcome, 'pnl_pips': pnl}
                if engine.active_variant == P90Variant.INITIAL:
                    initial_trades.append(trade)
                else:
                    cascade_trades.append(trade)
            engine.hard_exit()
            continue
        
        sig = engine.process_bar(bar)
        
        if sig and sig.event == 'ENTRY':
            entry = sig.entry_price
            sl = sig.sl_price
            tp1 = sig.tp_price
            direction = 'LONG' if sig.direction == TradeDirection.LONG else 'SHORT'
            variant = sig.variant.value
            
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
                'variant': variant,
                'outcome': outcome,
                'pnl_pips': pnl,
                'direction': direction,
            }
            
            if sig.variant == P90Variant.INITIAL:
                initial_trades.append(trade)
            elif sig.variant == P90Variant.CASCADE:
                cascade_trades.append(trade)
    
    return initial_trades, cascade_trades


def stats(trades):
    if not trades:
        return {'count': 0, 'wr': 0, 'avg_pnl': 0}
    wins = sum(1 for t in trades if t['outcome'] in ('TP',))
    losses = sum(1 for t in trades if t['outcome'] == 'SL')
    closed = wins + losses
    wr = (wins / closed * 100) if closed > 0 else 0
    avg_pnl = sum(t['pnl_pips'] for t in trades) / len(trades)
    return {'count': len(trades), 'closed': closed, 'wins': wins, 'losses': losses, 'wr': wr, 'avg_pnl': avg_pnl}


print("=" * 70)
print("DEEP DIVE: INITIAL vs CASCADE WR ANALYSIS")
print("=" * 70)

for symbol in PAIRS:
    csv_file = CSV_FILES[symbol]
    filepath = os.path.join(DATA_DIR, csv_file)
    if not os.path.exists(filepath):
        continue
    
    bars = load_csv(filepath, max_bars=50000)
    initial, cascade = run_backtest(symbol, bars)
    
    si = stats(initial)
    sc = stats(cascade)
    st = stats(initial + cascade)
    
    print(f"\n{symbol}:")
    print(f"  INITIAL: {si['count']} trades | {si['wins']}W/{si['losses']}L | WR {si['wr']:.1f}% | Avg {si['avg_pnl']:.1f}p")
    print(f"  CASCADE: {sc['count']} trades | {sc['wins']}W/{sc['losses']}L | WR {sc['wr']:.1f}% | Avg {sc['avg_pnl']:.1f}p")
    print(f"  COMBINED: {st['count']} trades | {st['wins']}W/{st['losses']}L | WR {st['wr']:.1f}% | Avg {st['avg_pnl']:.1f}p")
    
    # Show cascade details
    if cascade:
        for ct in cascade[:5]:
            print(f"    Cascade: {ct['direction']} {ct['outcome']} {ct['pnl_pips']:.1f}pnl")

print("\n" + "=" * 70)
