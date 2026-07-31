"""USOIL Asian Range -25% and -50% Hit Rate Analysis for 2026"""
import pandas as pd, numpy as np, json, os, sys

DATA_PATH = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\OILUSDPRO_H1.csv'
print("Loading...")
df = pd.read_csv(DATA_PATH, sep=',')
df['time'] = pd.to_datetime(df['time'])
df['date'] = df['time'].dt.date
df['hour'] = df['time'].dt.hour
print(f"Loaded {len(df)} rows")

df = df[df['time'] >= '2026-01-01'].copy()
print(f"2026: {len(df)} rows")

asian = df[(df['hour'] >= 0) & (df['hour'] < 8)].copy()
lny = df[(df['hour'] >= 3) & (df['hour'] < 17)].copy()

results = []
for date, grp in asian.groupby('date'):
    if len(grp) < 2: continue
    ah, al = grp['high'].max(), grp['low'].min()
    ao, ac = grp.iloc[0]['open'], grp.iloc[-1]['close']
    rg = ah - al
    if rg <= 0: continue
    bias = 'BULLISH' if ac > ao else 'BEARISH'
    lny_d = lny[lny['date'] == date]
    if len(lny_d) == 0: continue
    dh, dl = lny_d['high'].max(), lny_d['low'].min()
    h25 = (dh >= ah + rg*0.25) or (dl <= al - rg*0.25)
    h50 = (dh >= ah + rg*0.50) or (dl <= al - rg*0.50)
    rk = (dh >= ah + rg*1.32) or (dl <= al - rg*1.32)
    results.append({'date': str(date), 'weekday': pd.Timestamp(date).strftime('%A'), 'bias': bias, 'ao': round(ao,2), 'ac': round(ac,2), 'ah': round(ah,2), 'al': round(al,2), 'rg': round(rg,2), 'dh': round(dh,2), 'dl': round(dl,2), 'h25': h25, 'h50': h50, 'rk': rk})

R = pd.DataFrame(results)
N = len(R)
print(f"\n=== 2026 OVERALL ({N} days) ===")
print(f"-25%: {R['h25'].sum()}/{N} = {R['h25'].sum()/N*100:.1f}%")
print(f"-50%: {R['h50'].sum()}/{N} = {R['h50'].sum()/N*100:.1f}%")
print(f"Rekey: {R['rk'].sum()}/{N} = {R['rk'].sum()/N*100:.1f}%")

R['dt'] = pd.to_datetime(R['date'])
R['mo'] = R['dt'].dt.to_period('M')
M = R.groupby('mo').agg(d=('date','count'),h25=('h25','sum'),h50=('h50','sum'),rk=('rk','sum'),avgr=('rg','mean')).reset_index()
print(f"\n=== MONTHLY ===")
for _,r in M.iterrows():
    print(f"{r['mo']}: {r['d']}d | -25%: {r['h25']/r['d']*100:.1f}% | -50%: {r['h50']/r['d']*100:.1f}% | Rekey: {r['rk']/r['d']*100:.1f}% | AvgRg: {r['avgr']:.2f}")

Mar = R[R['dt'].dt.month==3]
print(f"\n=== MARCH 2026 (War Drop) ===")
print(f"Days: {len(Mar)} | -25%: {Mar['h25'].sum()}/{len(Mar)}={Mar['h25'].sum()/len(Mar)*100:.1f}% | -50%: {Mar['h50'].sum()}/{len(Mar)}={Mar['h50'].sum()/len(Mar)*100:.1f}% | Rekey: {Mar['rk'].sum()}/{len(Mar)}={Mar['rk'].sum()/len(Mar)*100:.1f}%")

MarW = Mar.copy()
MarW['wk'] = MarW['dt'].dt.isocalendar().week
MW = MarW.groupby('wk').agg(d=('date','count'),h25=('h25','sum'),h50=('h50','sum'),rk=('rk','sum')).reset_index()
print("March weekly:")
for _,r in MW.iterrows():
    print(f"  W{int(r['wk'])}: {r['d']}d | -25%: {r['h25']/r['d']*100:.1f}% | -50%: {r['h50']/r['d']*100:.1f}% | Rekey: {r['rk']}")

Apr = R[R['dt'] >= '2026-04-01']
print(f"\n=== RECOVERY (Apr-Jun) ===")
print(f"Days: {len(Apr)} | -25%: {Apr['h25'].sum()}/{len(Apr)}={Apr['h25'].sum()/len(Apr)*100:.1f}% | -50%: {Apr['h50'].sum()}/{len(Apr)}={Apr['h50'].sum()/len(Apr)*100:.1f}%")

L45 = R.tail(45)
print(f"\n=== LAST 45 DAYS ({L45['date'].iloc[0]} to {L45['date'].iloc[-1]}) ===")
print(f"Days: {len(L45)} | -25%: {L45['h25'].sum()}/{len(L45)}={L45['h25'].sum()/len(L45)*100:.1f}% | -50%: {L45['h50'].sum()}/{len(L45)}={L45['h50'].sum()/len(L45)*100:.1f}% | Rekey: {L45['rk'].sum()}/{len(L45)}={L45['rk'].sum()/len(L45)*100:.1f}%")

RK = R[R['rk']==True]
print(f"\n=== REKEY DAYS ({len(RK)}) ===")
for _,r in RK.iterrows():
    print(f"  {r['date']} ({r['weekday']}) Rg: {r['rg']:.2f}")

print("\nDone!")
