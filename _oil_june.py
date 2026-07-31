import pandas as pd

df = pd.read_csv('quant-lab/data/OILUSDPRO_H1.csv', sep=',')
df['time'] = pd.to_datetime(df['time'])
df = df.sort_values('time').reset_index(drop=True)

dfjune = df[(df['time'].dt.year == 2026) & (df['time'].dt.month == 6)].copy()
dfjune['date'] = dfjune['time'].dt.date

print('June 2026: {} bars, {} trading days'.format(len(dfjune), dfjune['date'].nunique()))
print('Range: {} to {}'.format(dfjune['date'].min(), dfjune['date'].max()))
print()

asian = dfjune[(dfjune['time'].dt.hour >= 0) & (dfjune['time'].dt.hour < 8)].copy()
daily = asian.groupby('date').agg(
    ar=('high', lambda x: x.max() - asian.loc[x.index, 'low'].min()),
    ac=('close', 'last'),
    ao=('open', 'first')
).reset_index()
daily['dir'] = (daily['ac'] > daily['ao']).astype(int).replace({0: -1})

results = []
for _, row in daily.iterrows():
    td = row['date']
    ar = row['ar']
    d = row['dir']
    act = dfjune[(dfjune['time'].dt.date == td) & (dfjune['time'].dt.hour >= 8)]
    if len(act) == 0:
        continue
    entry = act.iloc[0]['close']
    if d == 1:
        t25 = entry + ar * 0.25
        t50 = entry + ar * 0.50
    else:
        t25 = entry - ar * 0.25
        t50 = entry - ar * 0.50
    sess = act[act['time'].dt.hour < 17]
    h25 = h50 = rekey = False
    for _, b in sess.iterrows():
        if d == 1:
            if b['high'] >= t25: h25 = True
            if b['high'] >= t50: h50 = True
            if b['low'] <= entry - ar * 1.32: rekey = True
        else:
            if b['low'] <= t25: h25 = True
            if b['low'] <= t50: h50 = True
            if b['high'] >= entry + ar * 1.32: rekey = True
    results.append({'date': td, 'ar': ar, 'dir': d, 'h25': h25, 'h50': h50, 'rekey': rekey})

r = pd.DataFrame(results)

print('=== JUNE 2026 ({} days) ==='.format(len(r)))
h25_pct = r['h25'].sum() / len(r) * 100
h50_pct = r['h50'].sum() / len(r) * 100
rk_pct = r['rekey'].sum() / len(r) * 100
print('-25%: {}/{} = {:.1f}%'.format(r['h25'].sum(), len(r), h25_pct))
print('-50%: {}/{} = {:.1f}%'.format(r['h50'].sum(), len(r), h50_pct))
print('Rekey: {}/{} = {:.1f}%'.format(r['rekey'].sum(), len(r), rk_pct))
print('Avg Range: {:.2f}'.format(r['ar'].mean()))
print()

print('=== DAILY DETAIL ===')
for _, row in r.iterrows():
    d = 'Bull' if row['dir'] == 1 else 'Bear'
    h25 = 'Y' if row['h25'] else 'N'
    h50 = 'Y' if row['h50'] else 'N'
    rk = 'R' if row['rekey'] else ' '
    print('  {} | {} | Rg:{:.2f} | -25%:{} | -50%:{} | {}'.format(row['date'], d, row['ar'], h25, h50, rk))

print()
rk = r[r['rekey'] == True]
print('=== REKEY DAYS ({}) ==='.format(len(rk)))
for _, row in rk.iterrows():
    d = 'Bull' if row['dir'] == 1 else 'Bear'
    print('  {} | {} | Rg:{:.2f}'.format(row['date'], d, row['ar']))
