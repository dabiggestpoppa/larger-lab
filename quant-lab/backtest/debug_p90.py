"""Debug P90 backtest for EURUSD"""
import sys, csv
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')
from asset_configs import ASSET_CONFIGS
from p90_engine_dmr import P90Engine, Bar

EST = timezone(timedelta(hours=-5))

config = ASSET_CONFIGS['EURUSD']
engine = P90Engine(
    pip_size=config.get('pip_value', 0.0001),
    tier_config=config.get('tiers'),
    symbol='EURUSD',
)

print('T1 ar_max:', engine.tier_config.get('T1', {}).get('ar_max'))

bars = []
with open('quant-lab/data/EURUSD_M5.csv', newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            ts = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=EST)
            bars.append(Bar(timestamp=ts, open=float(row['open']), high=float(row['high']),
                          low=float(row['low']), close=float(row['close'])))
        except: pass

print('Loaded %d bars' % len(bars))

current_date = None
init_count = 0
active_count = 0
signal_count = 0

for i, b in enumerate(bars[:5000]):
    # Session init at 3AM
    if b.timestamp.hour == 3 and b.timestamp.minute == 0:
        sdate = b.timestamp.date()
        if sdate != current_date:
            current_date = sdate
            # Collect Asian bars (19:00-03:00 EST)
            asian_bars = []
            for j in range(i - 1, -1, -1):  # Start from bar before 3AM
                bj = bars[j]
                bj_hour = bj.timestamp.hour
                if bj_hour >= 19 or bj_hour < 3:
                    bj_date = bj.timestamp.date()
                    if bj_hour >= 19:
                        bj_date = (bj.timestamp + timedelta(days=1)).date()
                    if bj_date == sdate:
                        asian_bars.append(bj)
                else:
                    break
            if asian_bars:
                ah = max(x.high for x in asian_bars)
                al = min(x.low for x in asian_bars)
                ar = (ah - al) / engine.pip_size
                engine.initialize_session(ah, al)
                init_count += 1
                if init_count <= 3:
                    print('Init %s: AR=%.1fp, active=%s, tier=%s' % (sdate, ar, engine.session_active, engine.tier_name))

    if b.timestamp.hour == 12 and b.timestamp.minute == 0:
        engine.hard_exit()

    if not engine.session_active:
        continue

    active_count += 1
    sig = engine.process_bar(b)
    if sig:
        signal_count += 1
        print('SIGNAL: %s %s at %s' % (sig.event, sig.variant, b.timestamp.strftime('%m-%d %H:%M')))
        if sig.event == 'ENTRY':
            print('  Entry=%.5f SL=%.5f TP1=%.5f' % (sig.entry_price, sig.sl_price, sig.tp_price))
            break

print('Inits: %d, Active bars: %d, Signals: %d' % (init_count, active_count, signal_count))
