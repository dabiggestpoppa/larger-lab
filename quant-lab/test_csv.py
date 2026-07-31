import csv
path = r'C:\Users\wifii\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M\5.csv'
with open(path) as f:
    reader = csv.DictReader(f)
    row = next(reader)
    print(list(row.keys()))
    print(row)