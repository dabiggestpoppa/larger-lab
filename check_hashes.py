import pandas as pd
import os
import hashlib
import json
from datetime import datetime, timedelta

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF']

# Check raw files
for sym in symbols:
    raw_path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    if os.path.exists(raw_path):
        sha256 = hashlib.sha256()
        with open(raw_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        print(f'{sym}: raw_path={raw_path}, raw_sha256={sha256.hexdigest()}')
    else:
        print(f'{sym}: RAW FILE NOT FOUND at {raw_path}')

print("\n--- Normalized files ---")
for sym in symbols:
    norm_path = f'data/normalized/h1/{sym}_H1.parquet'
    if os.path.exists(norm_path):
        sha256 = hashlib.sha256()
        with open(norm_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        print(f'{sym}: norm_path={norm_path}, norm_sha256={sha256.hexdigest()}')
    else:
        print(f'{sym}: NORMALIZED FILE NOT FOUND at {norm_path}')