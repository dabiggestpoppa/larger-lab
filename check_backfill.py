import pandas as pd
import numpy as np
import os
import hashlib
from datetime import datetime, timezone
from src.capital_routing.ingestion.normalize import OHLCNormalizer, NormalizationConfig

# Check if we can backfill EURUSD and USDCHF from 2022
# First, let's see what raw data we have for them
symbols = ['EURUSD', 'USDCHF']

for sym in symbols:
    raw_path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    if os.path.exists(raw_path):
        df = pd.read_csv(raw_path)
        print(f"\n{sym} raw M5:")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Rows: {len(df)}")
        
        # Parse timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        elif 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'], utc=True)
        
        df = df.sort_values('timestamp')
        print(f"  First: {df['timestamp'].min()}")
        print(f"  Last: {df['timestamp'].max()}")
        
        # Check if we have 2022 data
        data_2022 = df[df['timestamp'].dt.year == 2022]
        print(f"  2022 rows: {len(data_2022)}")
    else:
        print(f"\n{sym}: FILE NOT FOUND")