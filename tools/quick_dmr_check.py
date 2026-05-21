import json, sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()
c.execute("SELECT symbol, time, body_pips, threshold FROM p90_events ORDER BY rowid DESC LIMIT 8")
rows = c.fetchall()
for r in rows:
    print(f"{r[0]:12} {r[1][11:16]} body={r[2]:.1f}p thresh={r[3]:.1f}")
c.execute("SELECT timestamp, message FROM system_log ORDER BY rowid DESC LIMIT 3")
rows = c.fetchall()
for r in rows:
    print(f"[{r[0][11:19]}] {r[2][:100]}")
conn.close()
