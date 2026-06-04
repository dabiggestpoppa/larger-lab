"""Check first few rows of EURGBP to understand the data format."""
import csv

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    print("Columns:", list(reader.fieldnames))
    print()
    for i, row in enumerate(reader):
        if i < 5 or i > 276622:
            print("Row {}: {}".format(i, {k: v for k, v in row.items()}))
        if i > 276625:
            break
