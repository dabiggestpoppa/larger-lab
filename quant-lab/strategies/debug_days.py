import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

df = load_data()

# Find a day with more action
for dk in [date(2024,1,16), date(2024,1,17), date(2024,1,18), date(2024,2,1), date(2024,3,1)]:
    db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(df, dk)
    tier = 'T1' if ar['ar_pips']<20 else 'T2' if ar['ar_pips']<30 else 'T3'
    au = {'T1':10,'T2':12,'T3':15}[tier]
    ah = ar['ah']; al = ar['al']
    day = db[(db['est_hour']>=3) & (db['est_hour']<12)]

    # Count closes above AH and below AL
    above = day[day['close']>ah]
    below = day[day['close']<al]

    # Count impulses (body >= au*0.5) that close outside band
    impulse_min = au * 0.5
    imp_outside = day[((day['close']>ah) | (day['close']<al)) & (abs(day['close']-day['open'])*10000 >= impulse_min)]

    print(f"{dk}: AR={ar['ar_pips']:.1f}p {tier} | above={len(above)} below={len(below)} impulse_outside={len(imp_outside)}")

    if len(imp_outside)>0:
        for _, b in imp_outside.head(2).iterrows():
            body = abs(b['close']-b['open'])*10000
            d = "BULL" if b['close']>b['open'] else "BEAR"
            print(f"  {b['timestamp']} EST{b['est_hour']:.0f} {d} body={body:.1f}p C={b['close']:.5f}")

print("\n--- Problem analysis ---")
print("The entry requires: close outside Asian band AND body >= au*0.5")
print("On M5, most closes outside band are small bodied noise.")
print("The Symmetry Trap may need a DIFFERENT impulse definition.")
