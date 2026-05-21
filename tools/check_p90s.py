import sqlite3
from pathlib import Path
from collections import Counter

DB_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Total P90s
c.execute("SELECT COUNT(*) FROM p90_events")
total = c.fetchone()[0]
print(f"Total P90 events in DB: {total}")

# By date
c.execute("SELECT date, COUNT(*) FROM p90_events GROUP BY date ORDER BY date")
print("\nBy date:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

# By symbol
c.execute("SELECT symbol, COUNT(*) FROM p90_events GROUP BY symbol")
print("\nBy symbol:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

# By hour (EST) for today
c.execute("SELECT time, body_pips, threshold, direction, trade_triggered FROM p90_events WHERE date = '2026-05-20' ORDER BY time")
today_p90s = c.fetchall()
print(f"\nToday's P90s ({len(today_p90s)}):")
for ts, body, thresh, direction, triggered in today_p90s[:20]:
    # Parse hour from timestamp
    hour = ts[11:13]
    print(f"  {ts} | {direction} | body={body:.1f}p | thresh={thresh:.1f}p | trade={triggered}")
if len(today_p90s) > 20:
    print(f"  ... and {len(today_p90s) - 20} more")

# Check for duplicates
c.execute("SELECT time, COUNT(*) as cnt FROM p90_events WHERE date = '2026-05-20' GROUP BY time HAVING cnt > 1")
dupes = c.fetchall()
if dupes:
    print(f"\n⚠️ DUPLICATE P90 timestamps: {len(dupes)}")
    for ts, cnt in dupes[:10]:
        print(f"  {ts}: {cnt} entries")
else:
    print("\nNo duplicate timestamps")

# Body size distribution
c.execute("SELECT body_pips FROM p90_events WHERE date = '2026-05-20'")
bodies = [r[0] for r in c.fetchall()]
if bodies:
    print(f"\nBody size stats:")
    print(f"  Min: {min(bodies):.1f}p")
    print(f"  Max: {max(bodies):.1f}p")
    print(f"  Avg: {sum(bodies)/len(bodies):.1f}p")
    # How many are below threshold?
    c.execute("SELECT body_pips, threshold FROM p90_events WHERE date = '2026-05-20'")
    below = [(b, t) for b, t in c.fetchall() if b < t]
    if below:
        print(f"  ⚠️ {len(below)} P90s have body BELOW threshold!")
        for b, t in below[:5]:
            print(f"    body={b:.1f}p < thresh={t:.1f}p")

conn.close()
