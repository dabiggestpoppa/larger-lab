import sys, json
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

df = load_data()
dk = date(2024, 1, 15)
db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
ar = compute_asian_range(df, dk)

tier = 'T1' if ar['ar_pips']<20 else 'T2' if ar['ar_pips']<30 else 'T3'
au = {'T1':10,'T2':12,'T3':15}[tier]

print(f"Date: {dk}")
print(f"Asian: H={ar['ah']:.5f} L={ar['al']:.5f} AR={ar['ar_pips']:.1f}p Tier={tier} AU={au}")

# Closes outside Asian band (3-11AM)
day = db[(db['est_hour']>=3) & (db['est_hour']<11)]
ah = ar['ah']; al = ar['al']
outside = day[(day['close']>ah) | (day['close']<al)]
print(f"\nBars outside Asian band: {len(outside)}")

# Impulse candles (body >= au*0.5)
impulse_min = au * 0.5
print(f"Impulse threshold: {impulse_min}p")
impc = 0
for _, b in day.iterrows():
    body = abs(b['close']-b['open'])*10000
    if body >= impulse_min:
        impc += 1
        if impc <= 5:
            d = "BULL" if b['close']>b['open'] else "BEAR"
            print(f"  {b['timestamp']} {d} body={body:.1f}p C={b['close']:.5f} vs AH={ah:.5f} AL={al:.5f}")
print(f"Total impulses: {impc}")
