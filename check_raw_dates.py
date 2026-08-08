import pandas as pd
import os

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

for sym in symbols:
    path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    if os.path.exists(path):
        # Read just first and last few rows to get date range
        df_first = pd.read_csv(path, nrows=5)
        df_last = pd.read_csv(path).tail(5)
        print(f'{sym}:')
        print(f'  First rows: {df_first["timestamp"].values if "timestamp" in df_first.columns else df_first.iloc[:,0].values}')
        print(f'  Last rows: {df_last["timestamp"].values if "timestamp" in df_last.columns else df_last.iloc[:,0].values}')
        print(f'  Columns: {list(df_first.columns)}')
    else:
        print(f'{sym}: FILE NOT FOUND')