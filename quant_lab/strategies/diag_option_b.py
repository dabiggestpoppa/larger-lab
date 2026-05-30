import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from shared import load_data, compute_asian_range
from symmetry_trap_option_b import run_symmetry_trap_option_b

df = load_data()
dates = sorted(df['est_date'].unique())

loop_data = {i: {'wins': [], 'losses': []} for i in range(1, 9)}

for dk in dates:
    db = df[df['est_date']==dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(db, dk)
    if ar is None or ar.get('tier') == 'NO_GO': continue
    ar['date_key'] = dk
    trades = run_symmetry_trap_option_b(db, ar)
    for t in trades:
        loop = t['loop']
        sl_dist = abs(t['entry'] - t['sl']) / 0.0001
        tp_dist = abs(t['tp'] - t['entry']) / 0.0001
        rr_theoretical = tp_dist / sl_dist if sl_dist > 0 else 0
        rec = {
            'sl_dist': round(sl_dist, 1),
            'tp_dist': round(tp_dist, 1),
            'rr_theoretical': round(rr_theoretical, 2),
            'pnl': t['pnl_pips'],
            'exit_type': t['type']
        }
        if t['pnl_pips'] > 0:
            loop_data[loop]['wins'].append(rec)
        else:
            loop_data[loop]['losses'].append(rec)

print("=== LOOP ANALYSIS ===")
for loop in range(1, 9):
    w = loop_data[loop]['wins']
    l = loop_data[loop]['losses']
    total = len(w) + len(l)
    if total == 0: continue
    wr = len(w) / total * 100
    avg_sl_w = pd.DataFrame(w)['sl_dist'].mean() if w else 0
    avg_tp_w = pd.DataFrame(w)['tp_dist'].mean() if w else 0
    avg_rr_w = pd.DataFrame(w)['rr_theoretical'].mean() if w else 0
    avg_sl_l = pd.DataFrame(l)['sl_dist'].mean() if l else 0
    avg_tp_l = pd.DataFrame(l)['tp_dist'].mean() if l else 0
    avg_rr_l = pd.DataFrame(l)['rr_theoretical'].mean() if l else 0
    sl_pct_w = pd.DataFrame(w)['exit_type'].eq('SL').mean() * 100 if w else 0
    tp_pct_l = pd.DataFrame(l)['exit_type'].eq('TP').mean() * 100 if l else 0
    print(f"\nLoop {loop}: {total} tr, WR={wr:.1f}%")
    print(f"  Wins: {len(w)} | avg SL={avg_sl_w:.1f}p avg TP={avg_tp_w:.1f}p avg RR={avg_rr_w:.2f}")
    print(f"  Losses: {len(l)} | avg SL={avg_sl_l:.1f}p avg TP={avg_tp_l:.1f}p avg RR={avg_rr_l:.2f}")
    time_exits_l = sum(1 for x in l if 'TIME' in x['exit_type'])
    sl_exits_l = sum(1 for x in l if x['exit_type'] == 'SL')
    print(f"  Loss exits: SL={sl_exits_l} TIME={time_exits_l}")
