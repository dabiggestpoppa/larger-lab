import pandas as pd, json, os
f = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
df = pd.read_csv(f, nrows=5)
result = {
    "columns": df.columns.tolist(),
    "shape": list(df.shape),
    "dtypes": {k: str(v) for k, v in df.dtypes.items()},
    "head": df.head(3).to_dict(),
    "tail": df.tail(3).to_dict(),
}
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\data\csv_info.json", "w") as out:
    json.dump(result, out, indent=2, default=str)
# Also check file size
size = os.path.getsize(f)
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\data\csv_info.json", "a") as out:
    out.write(f"\n\nFile size: {size / 1e6:.1f} MB")
