import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_usdchf_trades.json') as f:
    trades = json.load(f)

print("=== SAMPLE TRADES ===")
for t in trades[:15]:
    risk = abs(t['entry'] - t['sl']) * 10000
    reward = abs(t['tp'] - t['entry']) * 10000
    rr = reward / risk if risk > 0 else 0
    print(f"{t['date']} {t['dir']:5} entry={t['entry']:.5f} tp={t['tp']:.5f} sl={t['sl']:.5f} risk={risk:.1f}p reward={reward:.1f}p rr=1:{rr:.2f} result={t['result']} pnl={t['pnl']}p")

tp = [t for t in trades if t['result'] == 'TP']
sl = [t for t in trades if t['result'] == 'SL']
he = [t for t in trades if t['result'] == 'HARD_EXIT']
eo = [t for t in trades if t['result'] == 'EOD']

print(f"\n=== RESULTS ===")
print(f"TP: {len(tp)}  SL: {len(sl)}  HARD_EXIT: {len(he)}  EOD: {len(eo)}")

tp_pnls = [t['pnl'] for t in tp]
sl_pnls = [t['pnl'] for t in sl]

if tp_pnls:
    print(f"TP avg win: {sum(tp_pnls)/len(tp_pnls):.1f}p  min={min(tp_pnls)}p  max={max(tp_pnls)}p")
if sl_pnls:
    print(f"SL avg loss: {sum(sl_pnls)/len(sl_pnls):.1f}p  min={min(sl_pnls)}p  max={max(sl_pnls)}p")

print(f"\n=== R:R ON TP HITS ===")
tp_rrs = []
for t in tp:
    r = abs(t['entry'] - t['sl']) * 10000
    rw = abs(t['tp'] - t['entry']) * 10000
    if r > 0:
        tp_rrs.append((rw/r, r, rw, t['pnl']))
print(f"Avg R:R 1:{sum(x[0] for x in tp_rrs)/len(tp_rrs):.2f}")
print(f"Min R:R 1:{min(x[0] for x in tp_rrs):.2f}  Max R:R 1:{max(x[0] for x in tp_rrs):.2f}")

print(f"\n=== CHECK: IS DEEP MULT BEING IGNORED? ===")
print("Expected: DeepMult=2.0, KillMult=2.2")
print("For 4p body: reward should be ~8p, sl should be ~8.8p")
print()
for t in tp[:15]:
    body_pips = t['body']
    ds_dist = abs(t['entry'] - t['tp']) * 10000  # entry to TP = deep mult distance
    ks_dist = abs(t['entry'] - t['sl']) * 10000  # entry to SL = kill mult distance
    body_from_act = abs(t['tp'] - (t['entry'] - ds_dist * (1 if t['dir']=='LONG' and t['entry']>t['tp'] else -1)/10000 if t['dir']=='SHORT' else t['entry'] + ds_dist/10000)) * 10000
    print(f"{t['date']} body={body_pips}p entry->TP={ds_dist:.1f}p entry->SL={ks_dist:.1f}p ratio={ks_dist/ds_dist:.2f}")
