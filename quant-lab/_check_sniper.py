import sqlite3
conn = sqlite3.connect('quant-lab/sniper/sniper.db')
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables:', tables)
for t in tables:
    try:
        cols = [d[0] for d in conn.execute(f'PRAGMA table_info({t})').fetchall()]
        count = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'\n{t} ({count} rows):')
        print('  Cols:', cols)
        if count > 0:
            sample = conn.execute(f'SELECT * FROM {t} LIMIT 2').fetchall()
            for s in sample:
                print('  ', s)
    except Exception as e:
        print(f'  Error: {e}')
conn.close()
