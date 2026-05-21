import sqlite3, time
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check for recent errors
c.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print("Recent system logs:")
for r in rows:
    print(f"  [{r[0]}] {r[1]}: {r[2][:100]}")

# Check P90 count
c.execute("SELECT COUNT(*) FROM p90_events")
print(f"\nP90 events: {c.fetchone()[0]}")

# Check account snapshots
c.execute("SELECT COUNT(*) FROM account_snapshots")
print(f"Account snapshots: {c.fetchone()[0]}")

conn.close()
