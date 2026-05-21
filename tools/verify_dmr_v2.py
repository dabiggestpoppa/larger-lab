import json, sqlite3

# Check state
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json") as f:
    state = json.load(f)

print("=== DMR State ===")
for sym, data in state.get('symbols', {}).items():
    kp = data.get('known_p90s', [])
    print(f"  {sym}: P90s={data.get('p90_count',0)} | times={kp[-5:] if kp else 'none'}")

# Check DB
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

c.execute("SELECT symbol, time, body_pips, threshold FROM p90_events WHERE date='2026-05-21' ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
print("\n=== Today's P90 Events ===")
for r in rows:
    print(f"  {r[0]:12} {r[1][11:16]} body={r[2]:.1f}p thresh={r[3]:.1f}")

# Check latest logs
c.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print("\n=== Latest Logs ===")
for r in rows:
    print(f"  [{r[0][11:19]}] {r[1]}: {r[2][:120]}")

conn.close()
