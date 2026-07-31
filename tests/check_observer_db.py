import sqlite3, os
db = "data/observer/observer_actions.db"
if not os.path.exists(db):
    print("DB not found")
    exit()
conn = sqlite3.connect(db)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"  {t[0]}: {count} rows")
    schema = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
    cols = [s[1] for s in schema]
    print(f"    columns: {cols}")
    if count > 0:
        row = conn.execute(f"SELECT * FROM {t[0]} ORDER BY rowid DESC LIMIT 1").fetchone()
        print(f"    last row: {row}")
conn.close()
