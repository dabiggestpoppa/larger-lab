$dbFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db"
if (Test-Path $dbFile) {
    Add-Type -Path "C:\Users\wifik\AppData\Local\Programs\Python\Python311\Lib\sqlite3\__init__.py" -ErrorAction SilentlyContinue
    # Use python to query instead
    python -c "
import sqlite3, datetime
conn = sqlite3.connect(r'$dbFile')
c = conn.cursor()

# Check tables
c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = c.fetchall()
print('Tables:', [t[0] for t in tables])

# Recent trades
try:
    c.execute('SELECT * FROM trades ORDER BY created_at DESC LIMIT 5')
    rows = c.fetchall()
    print('\nRecent trades:')
    for r in rows:
        print(r)
    c.execute('SELECT COUNT(*) FROM trades')
    print('Total trades:', c.fetchone()[0])
except Exception as e:
    print('Trades error:', e)

# Recent system logs
try:
    c.execute('SELECT * FROM system_log ORDER BY created_at DESC LIMIT 10')
    rows = c.fetchall()
    print('\nRecent system logs:')
    for r in rows:
        print(r)
except Exception as e:
    print('No system_log table or error:', e)

# P90 events
try:
    c.execute('SELECT * FROM p90_events ORDER BY created_at DESC LIMIT 5')
    rows = c.fetchall()
    print('\nRecent P90 events:')
    for r in rows:
        print(r)
    c.execute('SELECT COUNT(*) FROM p90_events')
    print('Total P90s:', c.fetchone()[0])
except Exception as e:
    print('No p90_events table or error:', e)

conn.close()
"
} else {
    Write-Host "DB not found"
}
