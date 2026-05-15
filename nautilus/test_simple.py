#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '..')
from pathlib import Path

try:
    from nautilus.data_loader import _parse_csv
    print("Import successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

filepath = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
print(f"File exists: {filepath.exists()}")
df = _parse_csv(filepath)
print(f"Loaded {len(df)} rows")
print(df.head())