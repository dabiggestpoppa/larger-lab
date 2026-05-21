import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check the latest P90 events after the most recent restart
c.execute("SELECT timestamp, message FROM system_log ORDER BY rowid DESC LIMIT 5")
rows = conn.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 8").fetchall()
for r in rows:
    print(f"[{r[0][11:19]}] {r[1]}: {r[2][:120]}")

# Check if there are P90s with the NEW thresholds
c.execute("SELECT symbol, body_pips, threshold FROM p90_events WHERE threshold IN (5.2, 7.2, 8.6, 9.2, 2.0, 3.8, 3.6, 4.6) ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print(f"\nP90s with NEW thresholds: {len(rows)}")
for r in rows:
    print(f"  {r[0]} body={r[1]}p thresh={r[2]}p")

# Check all unique thresholds used today
c.execute("SELECT DISTINCT threshold, symbol FROM p90_events WHERE date='2026-05-21' ORDER BY symbol, threshold")
rows = c.fetchall()
print(f"\nUnique thresholds used today:")
for r in rows:
    print(f"  thresh={r[0]}p ({r[1]})")

conn.close()
