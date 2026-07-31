import sqlite3
conn = sqlite3.connect("data/research/agents.db")
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", rows)
conn.close()
