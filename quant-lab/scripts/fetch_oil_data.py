"""Fetch LCOUSD.PRO and OILUSD.PRO M5 data from MT5."""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import os

mt5.initialize()

os.makedirs("quant-lab/data", exist_ok=True)

for sym in ["LCOUSD.PRO", "OILUSD.PRO"]:
    from_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
    bars = mt5.copy_rates_from(sym, mt5.TIMEFRAME_M5, from_dt, 500000)
    if bars is not None and len(bars) > 0:
        df = pd.DataFrame(bars)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        print(f"{sym}: {len(df)} bars | {df.time.iloc[0]} → {df.time.iloc[-1]}")
        fname = f"quant-lab/data/{sym.replace('.', '')}_M5.csv"
        df.to_csv(fname, index=False)
        print(f"  Saved: {fname}")
    else:
        print(f"{sym}: No data returned")

mt5.shutdown()
