#!/usr/bin/env python3
"""Check actual spread column values in PRO CSV files."""
import csv
from pathlib import Path

DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")

PRO_FILES = [
    "EURJPY_PRO_M5.csv", "AUDJPY_PRO_M5.csv", "NZDJPY_PRO_M5.csv", "CADJPY_PRO_M5.csv",
    "EURGBP_PRO_M5.csv", "EURCHF_PRO_M5.csv", "EURCAD_PRO_M5.csv", "EURNZD_PRO_M5.csv",
    "EURAUD_PRO_M5.csv", "AUDCAD_PRO_M5.csv", "AUDCHF_PRO_M5.csv", "AUDNZD_PRO_M5.csv",
    "CADCHF_PRO_M5.csv", "NZDCAD_PRO_M5.csv", "NZDCHF_PRO_M5.csv", "GBPCAD_PRO_M5.csv",
    "USDCAD_PRO_M5.csv",
]

for fname in PRO_FILES:
    path = DATA_DIR / fname
    if not path.exists():
        continue
    
    spreads = []
    nonzero = 0
    total = 0
    
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader, None)
        spread_col = None
        if header:
            for i, h in enumerate(header):
                if h.lower().strip() == 'spread':
                    spread_col = i
                    break
        
        if spread_col is None:
            print(f"{fname}: NO SPREAD COLUMN")
            continue
        
        for row in reader:
            total += 1
            if len(row) > spread_col:
                try:
                    s = float(row[spread_col])
                    spreads.append(s)
                    if s > 0:
                        nonzero += 1
                except:
                    pass
    
    if spreads:
        avg_all = sum(spreads) / len(spreads)
        nonzero_vals = [s for s in spreads if s > 0]
        avg_nonzero = sum(nonzero_vals) / len(nonzero_vals) if nonzero_vals else 0
        max_spread = max(spreads)
        
        pair = fname.replace('_PRO_M5.csv', '').replace('_M5.csv', '')
        print(f"{pair:12s}: total={total:>8d}  nonzero={nonzero:>8d}  avg_all={avg_all:>10.4f}  avg_nonzero={avg_nonzero:>10.4f}  max={max_spread:>10.4f}")
    else:
        print(f"{fname}: NO DATA")
