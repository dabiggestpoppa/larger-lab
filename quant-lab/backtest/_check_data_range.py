import csv
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")

pairs = {
    "EURUSD": "quant-lab/data/EURUSDPRO_M5_2023_2026.csv",
    "USDCHF": "quant-lab/data/USDCHFPRO_M5.csv",
    "GBPUSD": "quant-lab/data/GBPUSD_M5.csv",
    "AUDUSD": "quant-lab/data/AUDUSD_M5.csv",
    "BTCUSD": "quant-lab/data/BTCUSD_M5.csv",
    "XAUUSD": "quant-lab/data/XAUUSD_M5.csv",
}

for name, rel in pairs.items():
    path = WORKSPACE / rel
    if not path.exists():
        print(f"{name}: FILE NOT FOUND")
        continue
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    first = rows[0].get("timestamp", "?")
    last = rows[-1].get("timestamp", "?")
    print(f"{name:10s}: {len(rows):>8,} bars | First: {first} | Last: {last}")
