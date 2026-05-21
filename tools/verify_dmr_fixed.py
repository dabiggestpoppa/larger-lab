import sqlite3, json, time

# Wait a moment for DMR to process
time.sleep(5)

conn = sqlite3.connect(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
c = conn.cursor()

# Check for errors
c.execute("SELECT timestamp, level, message FROM system_log ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print("=== Recent System Logs ===")
for r in rows:
    print(f"  [{r[0]}] {r[1]}: {r[2][:120]}")

# Check P90 events per symbol
c.execute("SELECT symbol, COUNT(*) FROM p90_events GROUP BY symbol")
rows = c.fetchall()
print("\n=== P90 Events ===")
for r in rows:
    print(f"  {r[0]}: {r[1]}")

# Check state
state_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
with open(state_file) as f:
    state = json.load(f)
print("\n=== State ===")
for sym, data in state.get('symbols', {}).items():
    print(f"  {sym}: P90s={data.get('p90_count',0)} active_trade={data.get('active_trade')}")

conn.close()
