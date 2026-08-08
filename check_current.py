import pandas as pd
import os

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

for sym in symbols:
    path = f'data/normalized/h1/{sym}_H1.parquet'
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        print(f'{sym}: rows={len(df)}, first={df["timestamp_utc"].min()}, last={df["timestamp_utc"].max()}')
    else:
        print(f'{sym}: FILE NOT FOUND')