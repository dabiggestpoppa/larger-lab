import sqlite3
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

c.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 8")
rows = c.fetchall()
for r in rows:
    print("[" + r[0][11:19] + "] " + r[1] + ": " + r[2][:120])

c.execute("SELECT symbol, body_pips, threshold FROM p90_events ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
print("\nLatest P90s:")
for r in rows:
    print("  " + r[0] + " body=" + str(round(r[1],1)) + "p thresh=" + str(r[2]) + "p")

c.execute("SELECT DISTINCT threshold, symbol FROM p90_events WHERE date='2026-05-21' ORDER BY symbol, threshold")
rows = c.fetchall()
print("\nUnique thresholds today:")
for r in rows:
    print("  thresh=" + str(r[0]) + "p (" + r[1] + ")")

conn.close()
