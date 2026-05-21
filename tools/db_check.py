import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])

for table in ["trades", "p90_events", "system_log"]:
    try:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {c.fetchone()[0]} rows")
        c.execute(f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT 3")
        rows = c.fetchall()
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"{table}: error - {e}")

conn.close()
