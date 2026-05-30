import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_multi_pair_v2.json') as f:
    d = json.load(f)
pp = d.get('per_pair', {})
tot_trades = sum(v.get('total_trades',0) for v in pp.values())
tot_wins = sum(v.get('wins',0) for v in pp.values())
tot_losses = sum(v.get('losses',0) for v in pp.values())
tot_wr = (tot_wins / tot_trades * 100) if tot_trades else 0
tot_pnl = sum(v.get('total_pnl_pips',0) for v in pp.values())
print(f'v2 Totals: trades={tot_trades} wins={tot_wins} losses={tot_losses} WR={tot_wr:.1f}% PnL={tot_pnl:.1f}p')
for s,v in pp.items():
    t = v['total_trades']
    wr = v['win_rate']
    pnl = v['total_pnl_pips']
    pf = v.get('profit_factor','?')
    k = v.get('kelly_criterion','?')
    print(f'  {s}: {t}t WR={wr}% PnL={pnl}p PF={pf} K={k}')

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_usdchf.json') as f:
    c = json.load(f)
st = c.get('stats',{})
tt = st.get('total_trades','?')
wr = st.get('win_rate','?')
pnl = st.get('total_pnl_pips','?')
pf = st.get('profit_factor','?')
k = st.get('kelly','?')
eva = st.get('expectancy_pips','?')
print(f'USDCHF All-Time: {tt} trades WR={wr}% PnL={pnl}p PF={pf} K={k} E={eva}')

# dmr_multi_pair (v1)
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_multi_pair.json') as f:
    m = json.load(f)
print(f'v1 summary:')
agg = m.get('summary',{})
for sym,sv in agg.items():
    print(f'  {sym}: {sv.get(\"total\",\"?\")}t PnL={sv.get(\"total_pnl\",\"?\")}p WR={round(sv[\"wins\"]/sv[\"total\"]*100,1) if sv.get(\"total\") else \"?\"}%')

# p90 CFD expansion v5
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\p90_cfd_expansion_v5_stats.json') as f:
    v5 = json.load(f)
print(f'P90 CFD v5: {json.dumps(v5)}')

# daily p90 counts from multi_pair_v2
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\p90_thresholds.json') as f:
    th = json.load(f)
print(f'P90 thresholds today: {json.dumps(th)}')
