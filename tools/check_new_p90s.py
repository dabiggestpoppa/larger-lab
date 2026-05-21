import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# P90s after the latest restart (11:21:57 UTC)
c.execute("SELECT symbol, time, body_pips, threshold FROM p90_events WHERE time > '2026-05-21T11:21:00' ORDER BY time")
rows = c.fetchall()
print(f"P90s after 11:21 UTC (new process): {len(rows)}")
for r in rows:
    print(f"  {r[0]:12} {r[1][11:16]} body={r[2]:.1f}p thresh={r[3]:.1f}")

# All P90s today
c.execute("SELECT symbol, COUNT(*), AVG(threshold) FROM p90_events WHERE date='2026-05-21' GROUP BY symbol")
rows = c.fetchall()
print(f"\nAll P90s today:")
for r in rows:
    print(f"  {r[0]:12} count={r[1]} avg_thresh={r[2]:.1f}")

conn.close()
