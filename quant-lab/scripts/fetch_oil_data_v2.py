"""Fetch oil data from 2023 onwards using copy_rates_range."""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import os

mt5.initialize()
os.makedirs("quant-lab/data", exist_ok=True)

for sym in ["LCOUSD.PRO", "OILUSD.PRO"]:
    # Try copy_rates_range for 2023-01-01 to now
    from_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
    to_dt = datetime(2026, 6, 2, tzinfo=timezone.utc)
    bars = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, from_dt, to_dt)
    if bars is not None and len(bars) > 0:
        df = pd.DataFrame(bars)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        print(f"{sym}: {len(df)} bars | {df.time.iloc[0]} -> {df.time.iloc[-1]}")
        # Also pull H1 for regime analysis
        bars_h1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1, from_dt, to_dt)
        if bars_h1 is not None and len(bars_h1) > 0:
            df_h1 = pd.DataFrame(bars_h1)
            df_h1["time"] = pd.to_datetime(df_h1["time"], unit="s")
            print(f"  H1: {len(df_h1)} bars | {df_h1.time.iloc[0]} -> {df_h1.time.iloc[-1]}")
            df_h1.to_csv(f"quant-lab/data/{sym.replace('.', '')}_H1.csv", index=False)
        # Also pull D1 for macro regime
        bars_d1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_D1, datetime(2020, 1, 1, tzinfo=timezone.utc), to_dt)
        if bars_d1 is not None and len(bars_d1) > 0:
            df_d1 = pd.DataFrame(bars_d1)
            df_d1["time"] = pd.to_datetime(df_d1["time"], unit="s")
            print(f"  D1: {len(df_d1)} bars | {df_d1.time.iloc[0]} -> {df_d1.time.iloc[-1]}")
            df_d1.to_csv(f"quant-lab/data/{sym.replace('.', '')}_D1.csv", index=False)
        df.to_csv(f"quant-lab/data/{sym.replace('.', '')}_M5.csv", index=False)
    else:
        print(f"{sym}: No data for 2023+")

mt5.shutdown()
