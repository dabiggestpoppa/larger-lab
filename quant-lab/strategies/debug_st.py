import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies')
from symmetry_trap_v4 import *

bars = load_bars_mt5('USDCHF.PRO', 50000)
if not bars:
    print('No data'); sys.exit()

sessions = group_sessions(bars)
dates = sorted(sessions.keys())

engine = SymmetryTrapEngine('USDCHF.PRO')
found = 0
for d in dates[10:30]:
    day_bars = sessions[d]
    trades = engine.run_on_bars(day_bars)
    if trades:
        found += 1
        asian = [b for b in day_bars if b['est_h'] >= 19 or b['est_h'] < 3]
        asian_h = max(b['high'] for b in asian)
        asian_l = min(b['low'] for b in asian)
        ar = price_to_pips(asian_h - asian_l, 10000)
        print(f'{d}: AR={ar:.1f}p trades={len(trades)}')
        for t in trades:
            print(f'  {t["direction"]} entry={t["entry"]:.5f} tp={t["tp"]:.5f} sl={t["sl"]:.5f} pnl={t["pnl_pips"]:+.1f}p reason={t["exit_reason"]} loop={t["loop"]}')
        if found >= 5:
            break
