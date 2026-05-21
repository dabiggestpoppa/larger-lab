import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check the latest system logs
c.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 15")
rows = c.fetchall()
for r in rows:
    print(f"[{r[0][11:19]}] {r[1]:5} {r[2][:150]}")

conn.close()
