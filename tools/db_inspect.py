import sqlite3

conn = sqlite3.connect(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", c.fetchall())

c.execute("PRAGMA table_info(system_log)")
print("system_log columns:", c.fetchall())

c.execute("SELECT * FROM system_log ORDER BY id DESC LIMIT 10")
rows = c.fetchall()
print("\nLatest log entries:")
for r in rows:
    print(f"  {r}")

# Check trades table too
c.execute("PRAGMA table_info(trades)")
print("\ntrades columns:", c.fetchall())

c.execute("SELECT COUNT(*) FROM trades")
print("Trade count:", c.fetchone()[0])

# Check if any orders were placed
c.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 5")
for r in c.fetchall():
    print(f"  Trade: {r}")

conn.close()
