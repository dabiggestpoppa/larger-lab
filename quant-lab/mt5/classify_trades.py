import openpyxl
import datetime

wb = openpyxl.load_workbook(r'C:\Users\wifik\Downloads\ReportHistory-650898.xlsx', read_only=True)
ws = wb.active

today = datetime.date(2026, 6, 2)

# Collect all rows from today
rows_today = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] is None:
        continue
    try:
        t = row[0]
        if isinstance(t, datetime.datetime):
            trade_date = t.date()
        else:
            continue
        if trade_date == today:
            rows_today.append(row)
    except:
        continue

print(f"Total rows today: {len(rows_today)}")
print()

# Print first 10 rows with column indices to understand format
for i, row in enumerate(rows_today[:10]):
    print(f"Row {i}:")
    for j, val in enumerate(row):
        if val is not None:
            print(f"  col[{j}] = {val}")
    print()

# Now print the deal history section (rows where col[2] contains "in" or "out")
print("=" * 80)
print("DEAL HISTORY ENTRIES (col[2] contains 'in' or 'out')")
print("=" * 80)
for row in rows_today:
    order_str = str(row[2]) if row[2] else ""
    if 'in' in order_str.lower() or 'out' in order_str.lower():
        # Deal History format: Time, Deal, Order(in/out), Dir, Vol, Price, SL, TP, Comment, Magic
        print(f"  {str(row[0])[:16]} | Deal={row[1]} | {order_str} | {row[3]} {row[4]} @ {row[5]} | SL={row[6]} TP={row[7]} | Comment={row[8]} | Magic={row[9]}")
