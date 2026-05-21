import sqlite3

db_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db"
conn = sqlite3.connect(db_file)
c = conn.cursor()

# Check current p90_events schema
c.execute("PRAGMA table_info(p90_events)")
cols = [r[1] for r in c.fetchall()]
print("Current p90_events columns:", cols)

# Add trade_ticket column if missing
if 'trade_ticket' not in cols:
    c.execute("ALTER TABLE p90_events ADD COLUMN trade_ticket INTEGER")
    print("Added trade_ticket column to p90_events")
else:
    print("trade_ticket column already exists")

# Verify
c.execute("PRAGMA table_info(p90_events)")
cols = [r[1] for r in c.fetchall()]
print("Updated p90_events columns:", cols)

conn.commit()
conn.close()
print("DB fix complete")
