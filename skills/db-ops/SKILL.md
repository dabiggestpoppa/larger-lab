# Database Operations Skill

## Purpose
Manage databases for OCE persistence, SRRA-OPH state, and application data. SQLite (local), PostgreSQL (production), Redis (caching/events).

## SQLite (Local Development)

### Connection & Migration
```python
import sqlite3, json
from pathlib import Path

DB_PATH = Path("data/oce.db")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

MIGRATIONS = [
    ("001_events", """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL,
            source TEXT NOT NULL, priority INTEGER DEFAULT 1,
            payload JSON, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
    """),
    ("002_observers", """
        CREATE TABLE IF NOT EXISTS observers (
            observer_id TEXT PRIMARY KEY, observer_type TEXT NOT NULL,
            state TEXT DEFAULT 'idle', config JSON, health JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """),
    ("003_snapshots", """
        CREATE TABLE IF NOT EXISTS state_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observer_id TEXT NOT NULL, snapshot JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (observer_id) REFERENCES observers(observer_id)
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_observer ON state_snapshots(observer_id);
    """),
]

def migrate():
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS migrations (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    for name, sql in MIGRATIONS:
        if not conn.execute("SELECT 1 FROM migrations WHERE name=?",(name,)).fetchone():
            conn.executescript(sql)
            conn.execute("INSERT INTO migrations (name) VALUES (?)",(name,))
            conn.commit()
            print(f"Applied: {name}")
    conn.close()
```

### CRUD
```python
def insert_event(eid, etype, src, pri, payload):
    c = get_conn()
    c.execute("INSERT INTO events VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
              (eid, etype, src, pri, json.dumps(payload)))
    c.commit(); c.close()

def get_events(etype=None, src=None, limit=100):
    c = get_conn(); q = "SELECT * FROM events WHERE 1=1"; p = []
    if etype: q+=" AND event_type=?"; p.append(etype)
    if src: q+=" AND source=?"; p.append(src)
    q+=" ORDER BY created_at DESC LIMIT ?"; p.append(limit)
    rows = c.execute(q,p).fetchall(); c.close()
    return [dict(r) for r in rows]

def update_observer(oid, state, health=None):
    c = get_conn()
    if health:
        c.execute("UPDATE observers SET state=?,health=?,updated_at=CURRENT_TIMESTAMP WHERE observer_id=?",
                  (state, json.dumps(health), oid))
    else:
        c.execute("UPDATE observers SET state=?,updated_at=CURRENT_TIMESTAMP WHERE observer_id=?",
                  (state, oid))
    c.commit(); c.close()

def cleanup_old_events(days=30):
    c = get_conn()
    c.execute("DELETE FROM events WHERE created_at < datetime('now',?)", (f"-{days} days",))
    c.commit(); c.close()
```

## PostgreSQL (Production)
```python
import psycopg2, psycopg2.extras, os

def get_pg():
    return psycopg2.connect(
        host=os.getenv("PG_HOST","localhost"), port=int(os.getenv("PG_PORT",5432)),
        dbname=os.getenv("PG_DB","oce"), user=os.getenv("PG_USER","oce"),
        password=os.getenv("PG_PASSWORD",""),
        cursor_factory=psycopg2.extras.RealDictCursor)

# JSONB query example
def find_by_payload(conn, key, value):
    conn.execute("SELECT * FROM events WHERE payload->>%s = %s", (key, str(value)))
    return conn.fetchall()
```

## Redis (Caching + Events)
```python
import redis, json, os

def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST","localhost"),
        port=int(os.getenv("REDIS_PORT",6379)),
        decode_responses=True)

def publish(r, channel, data): r.publish(channel, json.dumps(data))
def stream_add(r, stream, data): r.xadd(stream, {"data": json.dumps(data)}, maxlen=10000)
def cache_set(r, key, value, ttl=3600): r.setex(key, ttl, json.dumps(value))
def cache_get(r, key):
    v = r.get(key); return json.loads(v) if v else None
```

## Backup
```bash
# SQLite
sqlite3 data/oce.db ".backup data/oce_backup_$(date +%Y%m%d).db"
# PostgreSQL
pg_dump -h localhost -U oce oce > backup_$(date +%Y%m%d).sql
# Restore
sqlite3 data/oce_new.db < data/oce_backup.db
psql -h localhost -U oce oce < backup.sql
```
