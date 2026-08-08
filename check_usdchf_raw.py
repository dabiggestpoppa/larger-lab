import pandas as pd
import numpy as np
import os

# Check USDCHF raw data more carefully
sym = 'USDCHF'
path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
df = pd.read_csv(path)

print(f"Columns: {list(df.columns)}")
print(f"First 5 rows:")
print(df.head())
print(f"\nLast 5 rows:")
print(df.tail())
print(f"\nTimestamp column dtype: {df['timestamp'].dtype}")
print(f"Timestamp sample values: {df['timestamp'].head(10).values}")