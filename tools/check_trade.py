import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check all trades
c.execute("SELECT * FROM trades ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print("=== TRADES ===")
for r in rows:
    print(r)

# Check CHFJPY P90s
c.execute("SELECT id, date, time, symbol, direction, body_pips, threshold, notes FROM p90_events WHERE symbol='CHFJPY.PRO' ORDER BY time")
rows = c.fetchall()
print(f"\n=== CHFJPY P90s ({len(rows)} total) ===")
for r in rows:
    print(f"  {r[2]} {r[4]} body={r[5]:.1f}p thresh={r[6]:.1f} {r[7]}")

# Check system log for trade placement
c.execute("SELECT timestamp, level, message FROM system_log WHERE message LIKE '%TRADE%' OR message LIKE '%trade%' OR message LIKE '%CHFJPY%' ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
print(f"\n=== TRADE LOGS ===")
for r in rows:
    print(f"  [{r[0]}] {r[1]}: {r[2][:150]}")

conn.close()
