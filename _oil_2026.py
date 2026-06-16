import pandas as pd
from datetime import datetime, timezone

df_june = pd.read_csv('quant-lab/data/OILUSD_PRO_M5_JUNE.csv')
df_june['time'] = pd.to_datetime(df_june['time'], utc=True)

df_hist = pd.read_csv('quant-lab/data/OILUSDPRO_H1.csv', sep=',')
df_hist['time'] = pd.to_datetime(df_hist['time'], utc=True)

df = pd.concat([df_hist, df_june], ignore_index=True)
df = df[df['time'].dt.year == 2026].copy()
df = df.sort_values('time').reset_index(drop=True)
df['date'] = df['time'].dt.date

print('2026 USOIL: {} bars, {} trading days'.format(len(df), df['date'].nunique()))
print('Range: {} to {}'.format(df['time'].min(), df['time'].max()))
print()

asian = df[(df['time'].dt.hour >= 0) & (df['time'].dt.hour < 8)].copy()

results = []
for date, group in asian.groupby('date'):
    ar = group['high'].max() - group['low'].min()
    direction = 1 if group.iloc[-1]['close'] > group.iloc[0]['open'] else -1
    day_bars = df[df['time'].dt.date == date]
    activation = day_bars[(day_bars['time'].dt.hour >= 8) & (day_bars['time'].dt.hour < 17)]
    if len(activation) == 0:
        continue
    entry = activation.iloc[0]['close']
    if direction == 1:
        t25 = entry + ar * 0.25
        t50 = entry + ar * 0.50
    else:
        t25 = entry - ar * 0.25
        t50 = entry - ar * 0.50
    h25 = h50 = rekey = False
    for _, bar in activation.iterrows():
        if direction == 1:
            if bar['high'] >= t25: h25 = True
            if bar['high'] >= t50: h50 = True
            if bar['low'] <= entry - ar * 1.32: rekey = True
        else:
            if bar['low'] <= t25: h25 = True
            if bar['low'] <= t50: h50 = True
            if bar['high'] >= entry + ar * 1.32: rekey = True
    results.append({'date': date, 'ar': ar, 'dir': direction, 'h25': h25, 'h50': h50, 'rekey': rekey})

r = pd.DataFrame(results)

print('=== 2026 OVERALL ({} days) ==='.format(len(r)))
print('-25%: {}/{} = {:.1f}%'.format(r['h25'].sum(), len(r), r['h25'].sum()/len(r)*100))
print('-50%: {}/{} = {:.1f}%'.format(r['h50'].sum(), len(r), r['h50'].sum()/len(r)*100))
print('Rekey: {}/{} = {:.1f}%'.format(r['rekey'].sum(), len(r), r['rekey'].sum()/len(r)*100))
print('Avg Asian Range: {:.2f}'.format(r['ar'].mean()))
print()

print('=== MONTHLY BREAKDOWN ===')
r['month'] = r['date'].apply(lambda x: x.strftime('%Y-%m'))
monthly = r.groupby('month').agg(days=('date','count'), h25=('h25','sum'), h50=('h50','sum'), rekey=('rekey','sum'), avg_ar=('ar','mean')).reset_index()
for _, row in monthly.iterrows():
    d = int(row['days'])
    print('{}: {}d | -25%: {}/{}={:.1f}% | -50%: {}/{}={:.1f}% | Rekey: {}/{}={:.1f}% | AvgRg: {:.2f}'.format(
        row['month'], d, int(row['h25']), d, row['h25']/d*100,
        int(row['h50']), d, row['h50']/d*100,
        int(row['rekey']), d, row['rekey']/d*100, row['avg_ar']))
print()

mar = r[r['month'] == '2026-03']
print('=== MARCH 2026 (War Drop) ===')
print('Days: {} | -25%: {}/{}={:.1f}% | -50%: {}/{}={:.1f}% | Rekey: {}/{}={:.1f}%'.format(
    len(mar), mar['h25'].sum(), len(mar), mar['h25'].mean()*100,
    mar['h50'].sum(), len(mar), mar['h50'].mean()*100,
    mar['rekey'].sum(), len(mar), mar['rekey'].mean()*100))
print()

rec = r[r['month'].isin(['2026-04','2026-05','2026-06'])]
print('=== RECOVERY (Apr-Jun) ===')
print('Days: {} | -25%: {}/{}={:.1f}% | -50%: {}/{}={:.1f}%'.format(
    len(rec), rec['h25'].sum(), len(rec), rec['h25'].mean()*100,
    rec['h50'].sum(), len(rec), rec['h50'].mean()*100))
print()

last45 = r.tail(45)
print('=== LAST 45 DAYS ({} to {}) ==='.format(last45['date'].iloc[0], last45['date'].iloc[-1]))
print('Days: {} | -25%: {}/{}={:.1f}% | -50%: {}/{}={:.1f}% | Rekey: {}/{}={:.1f}%'.format(
    len(last45), last45['h25'].sum(), len(last45), last45['h25'].mean()*100,
    last45['h50'].sum(), len(last45), last45['h50'].mean()*100,
    last45['rekey'].sum(), len(last45), last45['rekey'].mean()*100))
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
