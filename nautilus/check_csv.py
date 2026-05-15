import pandas as pd
f = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
df = pd.read_csv(f, nrows=5)
with open("nautilus/data/csv_check.txt", "w", encoding="utf-8") as out:
    out.write(f"Columns: {df.columns.tolist()}\n")
    out.write(f"Shape: {df.shape}\n")
    out.write(f"Dtypes:\n{df.dtypes}\n")
    out.write(f"\nHead:\n{df.head(3).to_string()}\n")
    out.write(f"\nTail:\n{df.tail(3).to_string()}\n")
print("Done - check nautilus/data/csv_check.txt")
