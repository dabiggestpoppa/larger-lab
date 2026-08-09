signals = [
    ('HK50','LONG',25550.15,25574.2,25642.15),
    ('NZDUSD','LONG',0.59011,0.59,0.59221),
    ('BTCUSD','LONG',65106.4,65141.3,65226.4),
    ('US500','SHORT',7702.46,7706.48,7683.46),
    ('EURUSD','SHORT',1.1534,1.15318,1.1524),
    ('USDCHF','LONG',0.80931,0.80942,0.81041),
    ('AUDUSD','SHORT',0.70337,0.70275,0.70227),
]
print('=== SL/TP SIDE VALIDATION ===')
print('For LONG:  SL must be < entry AND TP must be > entry')
print('For SHORT: SL must be > entry AND TP must be < entry')
print()
for sym,dirn,e,sl,tp in signals:
    if dirn=='LONG':
        sl_ok = sl < e
        tp_ok = tp > e
    else:
        sl_ok = sl > e
        tp_ok = tp < e
    status = 'OK' if (sl_ok and tp_ok) else 'INVALID'
    print(f'{sym:10s} {dirn:5s} entry={e:<12} sl={sl:<12} sl_side_ok={sl_ok} tp_side_ok={tp_ok} => {status}')