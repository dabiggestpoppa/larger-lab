import sys, os
f = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
size = os.path.getsize(f)
out = []
out.write(f"File: {f}\n")
out.write(f"Size: {size / 1e6:.1f} MB\n")

# Read raw bytes
with open(f, 'rb') as fh:
    raw = fh.read(500)
out.write(f"Raw bytes (first 200): {raw[:200]}\n")

# Try reading as text
with open(f, 'r', encoding='utf-8', errors='replace') as fh:
    lines = [fh.readline() for _ in range(5)]
out.write(f"\nFirst 5 lines:\n")
for i, line in enumerate(lines):
    out.write(f"  Line {i}: {repr(line[:200])}\n")

# Try pandas
import pandas as pd
for sep in [',', ';', '\t', '|', ' ']:
    try:
        df = pd.read_csv(f, sep=sep, nrows=3)
        out.write(f"\nPandas with sep='{sep}': {df.columns.tolist()}\n")
        out.write(f"Shape: {df.shape}\n")
        out.write(f"Head:\n{df.head(2).to_string()}\n")
        break
    except Exception as e:
        out.write(f"Pandas sep='{sep}': {e}\n")

result = "\n".join(out) if isinstance(out, list) else str(out)
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\data\csv_inspect.txt", "w", encoding="utf-8") as fh:
    fh.write(result)
