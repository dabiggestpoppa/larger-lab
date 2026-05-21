import json, sqlite3

# Check state
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json") as f:
    state = json.load(f)

print("=== DMR State ===")
for sym, data in state.get('symbols', {}).items():
    print(f"  {sym}: P90s={data.get('p90_count',0)} | active={data.get('active_trade')} | last_p90={data.get('last_p90_time')}")

# Check DB for new P90s
conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()
c.execute("SELECT symbol, time, body_pips, threshold FROM p90_events ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
print("\n=== Latest P90 Events (DB) ===")
for r in rows:
    print(f"  {r[0]:12} {r[1][:16]} body={r[2]:.1f}p thresh={r[3]:.1f}")

# Check for errors
c.execute("SELECT timestamp, level, message FROM system_log WHERE level='ERROR' ORDER BY rowid DESC LIMIT 3")
rows = c.fetchall()
if rows:
    print("\n=== Recent Errors ===")
    for r in rows:
        print(f"  [{r[0]}] {r[2][:100]}")
else:
    print("\n=== No recent errors ===")

conn.close()
