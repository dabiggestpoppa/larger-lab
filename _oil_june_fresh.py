import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Connect and fetch
mt5.initialize()
print('MT5 connected')

# Fetch OILUSD.PRO M5 from June 1 to today
rates = mt5.copy_rates_range('OILUSD.PRO', mt5.TIMEFRAME_M5, datetime(2026, 6, 1), datetime(2026, 6, 16))
print('Fetched {} bars'.format(len(rates)))

if rates is not None and len(rates) > 0:
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df = df.rename(columns={'tick_volume': 'volume'})
    print('Range: {} to {}'.format(df['time'].min(), df['time'].max()))
    
    # Save fresh data
    df.to_csv('quant-lab/data/OILUSD_PRO_M5_JUNE.csv', index=False)
    print('Saved to quant-lab/data/OILUSD_PRO_M5_JUNE.csv')
    
    # Now run Asian Range analysis for June
    df['date'] = df['time'].dt.date
    
    # Asian session: 7PM-3AM EST = 00:00-08:00 UTC
    asian = df[(df['time'].dt.hour >= 0) & (df['time'].dt.hour < 8)].copy()
    
    results = []
    for date, group in asian.groupby('date'):
        ar = group['high'].max() - group['low'].min()
        direction = 1 if group.iloc[-1]['close'] > group.iloc[0]['open'] else -1
        
        # Get activation bars (08:00-17:00 UTC = 3AM-12PM EST)
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
        
        results.append({
            'date': date, 'ar': ar, 'dir': direction,
            'entry': entry, 'h25': h25, 'h50': h50, 'rekey': rekey
        })
    
    r = pd.DataFrame(results)
    
    print()
    print('=== JUNE 2026 USOIL (OILUSD.PRO) ===')
    print('Trading days: {}'.format(len(r)))
    print('-25%: {}/{} = {:.1f}%'.format(r['h25'].sum(), len(r), r['h25'].sum()/len(r)*100))
    print('-50%: {}/{} = {:.1f}%'.format(r['h50'].sum(), len(r), r['h50'].sum()/len(r)*100))
    print('Rekey: {}/{} = {:.1f}%'.format(r['rekey'].sum(), len(r), r['rekey'].sum()/len(r)*100))
    print('Avg Asian Range: {:.2f}'.format(r['ar'].mean()))
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

mt5.shutdown()
print('\nDone!')
