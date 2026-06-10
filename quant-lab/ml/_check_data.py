"""Check data availability for training"""
import pandas as pd
from pathlib import Path

# Check features
df = pd.read_parquet("quant-lab/ml/data/full_features_v2/EURUSD_full.parquet")
print("EURUSD full features:")
print(f"  Shape: {df.shape}")
print(f"  Columns ({len(df.columns)}):")
for c in sorted(df.columns):
    print(f"    {c}")

# Check labels
labels_path = Path("quant-lab/ml/data/labels")
label_files = list(labels_path.glob("*_labeled.parquet"))
print(f"\nLabel files: {len(label_files)}")
lf = pd.read_parquet("quant-lab/ml/data/labels/EURUSD_labeled.parquet")
print(f"EURUSD labels shape: {lf.shape}")
label_cols = [c for c in lf.columns if "label" in c or "rekey" in c or "regime" in c]
print(f"Label columns: {label_cols}")

# Check all assets
print("\n=== ALL ASSETS ===")
full_dir = Path("quant-lab/ml/data/full_features_v2")
for f in sorted(full_dir.glob("*_full.parquet")):
    name = f.stem.replace("_full", "")
    try:
        d = pd.read_parquet(f)
        print(f"  {name}: {d.shape}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

# Check macro features
print("\n=== MACRO FEATURES ===")
macro_dir = Path("quant-lab/ml/data/macro_features")
if macro_dir.exists():
    for f in sorted(macro_dir.glob("*_macro.parquet"))[:3]:
        name = f.stem.replace("_macro", "")
        d = pd.read_parquet(f)
        macro_cols = [c for c in d.columns if c not in ["open", "high", "low", "close", "volume", "timestamp"]]
        print(f"  {name}: {d.shape} | macro cols: {len(macro_cols)}")
        for c in sorted(macro_cols):
            print(f"    {c}")
