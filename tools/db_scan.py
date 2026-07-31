import sqlite3, os

dbs = []
workspace = r"C:\Users\wifik\Desktop\projects\larger-lab"
for root, dirs, files in os.walk(workspace):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', '.git')]
    for f in files:
        if f.endswith(".db"):
            dbs.append(os.path.join(root, f))

for db_path in sorted(dbs):
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        sizes = {}
        for t in table_names:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM `{t}`").fetchone()
                sizes[t] = count[0]
            except:
                sizes[t] = "?"
        conn.close()
        size_kb = os.path.getsize(db_path) // 1024
        rel = os.path.relpath(db_path, workspace)
        print(f"\n{'='*60}")
        print(f"DB: {rel} | {size_kb} KB")
        print(f"Tables ({len(table_names)}):")
        for t in sorted(table_names):
            print(f"  {t}: {sizes.get(t, '?')} rows")
    except Exception as e:
        print(f"\nERROR: {db_path} — {e}")
