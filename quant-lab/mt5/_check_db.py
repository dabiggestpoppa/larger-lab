import sqlite3, json
from pathlib import Path

db = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
state_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json")

# State
if state_file.exists():
    with open(state_file) as f:
        state = json.load(f)
    print("=== LIVE STATE ===")
    for sym, data in state.get("symbols", {}).items():
        print(f"\n{sym}:")
        print(f"  trades_today: {data.get('trades_today', 0)}")
        print(f"  active_trade: {data.get('active_trade', False)}")
        print(f"  last_p90: {data.get('last_p90_time', 'none')}")
        print(f"  last_trade: {data.get('last_trade_time', 'none')}")
        print(f"  pnl: {data.get('pnl', 0.0)}")
        print(f"  p90_count: {data.get('p90_count', 0)}")

# DB
if db.exists():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print(f"\n=== DB TABLES: {tables} ===")
    
    if "trades" in tables:
        c.execute("SELECT COUNT(*) FROM trades")
        print(f"Total trades: {c.fetchone()[0]}")
        c.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 5")
        rows = c.fetchall()
        c.execute("PRAGMA table_info(trades)")
        cols = [col[1] for col in c.fetchall()]
        print(f"Columns: {cols}")
        for r in rows:
            print(r)
    
    if "p90_events" in tables:
        c.execute("SELECT COUNT(*) FROM p90_events")
        print(f"Total P90 events: {c.fetchone()[0]}")
        c.execute("SELECT date, time, symbol, direction, body_pips, trade_triggered, trade_ticket FROM p90_events ORDER BY id DESC LIMIT 10")
        for r in c.fetchall():
            print(r)
    
    if "system_log" in tables:
        c.execute("SELECT timestamp, level, category, message FROM system_log ORDER BY id DESC LIMIT 10")
        print("\n=== RECENT SYSTEM LOG ===")
        for r in c.fetchall():
            print(r)
    
    conn.close()
