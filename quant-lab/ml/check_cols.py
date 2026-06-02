import pandas as pd
from pathlib import Path

feat_dir = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\ml\data\features')
f = feat_dir / "EURUSD_features.parquet"
df = pd.read_parquet(f)
print("Columns:", list(df.columns))
print("\nFirst 3 rows:")
print(df.head(3).to_string())
print("\nDtypes:")
print(df.dtypes)
