import sqlite3
from pathlib import Path

DB_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Count before
c.execute("SELECT COUNT(*) FROM p90_events")
before = c.fetchone()[0]
print(f"Before cleanup: {before} P90 rows")

# Delete duplicates — keep only the first row for each (symbol, time) pair
c.execute('''
    DELETE FROM p90_events
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM p90_events
        GROUP BY symbol, time
    )
''')
conn.commit()

# Count after
c.execute("SELECT COUNT(*) FROM p90_events")
after = c.fetchone()[0]
print(f"After cleanup: {after} P90 rows")
print(f"Removed: {before - after} duplicates")

# Show remaining
c.execute("SELECT date, time, symbol, body_pips, direction FROM p90_events ORDER BY time")
rows = c.fetchall()
print(f"\nRemaining P90s ({len(rows)}):")
for r in rows:
    print(f"  {r[1]} | {r[2]} | {r[4]} | body={r[3]:.1f}p")

conn.close()
