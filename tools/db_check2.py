import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check system_log schema
c.execute("PRAGMA table_info(system_log)")
print("system_log columns:", [r[1] for r in c.fetchall()])

# Recent system logs
c.execute("SELECT * FROM system_log ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
for r in rows:
    print(r)

# Account snapshots
c.execute("SELECT COUNT(*) FROM account_snapshots")
print(f"\nAccount snapshots: {c.fetchone()[0]} rows")
c.execute("SELECT * FROM account_snapshots ORDER BY rowid DESC LIMIT 3")
rows = c.fetchall()
for r in rows:
    print(r)

conn.close()
