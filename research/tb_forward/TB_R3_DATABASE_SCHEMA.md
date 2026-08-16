# TB-R3 — Database Schema

**Storage:** SQLite, WAL mode, `synchronous=FULL`, `foreign_keys=ON`,
`busy_timeout=10000`. Schema version `1` recorded in `schema_meta`.

## Tables

### `schema_meta`

| column | type | notes |
|--------|------|-------|
| key    | TEXT PRIMARY KEY | `schema_version`, `app_version` |
| value  | TEXT | `1`, `TB-R3-PERSISTENCE-RECONCILIATION-01` |

### `events` (append-only ledger — THE source of truth)

```sql
CREATE TABLE events (
    event_id      TEXT PRIMARY KEY,
    seq           INTEGER NOT NULL UNIQUE,
    event_type    TEXT NOT NULL,
    ts_utc        TEXT NOT NULL,
    basket_id     TEXT NOT NULL DEFAULT '',
    strategy_id   TEXT NOT NULL DEFAULT '',
    prior_state   TEXT NOT NULL DEFAULT '',
    new_state     TEXT NOT NULL DEFAULT '',
    dedup_key     TEXT UNIQUE,
    payload       TEXT NOT NULL DEFAULT '{}',
    payload_hash  TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT '',
    reason        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_events_basket ON events(basket_id);
CREATE INDEX idx_events_type   ON events(event_type);
CREATE INDEX idx_events_seq    ON events(seq);
```

Write path: `INSERT` only. The normal flow never UPDATEs or DELETEs rows
(the API exposes no update/delete methods). `seq` is `MAX(seq)+1` inside the
same transaction, so sequence is contiguous and monotonic.

### `basket_current` (derived materialized cache)

```sql
CREATE TABLE basket_current (
    basket_id     TEXT PRIMARY KEY,
    strategy_id   TEXT NOT NULL DEFAULT '',
    direction     TEXT NOT NULL DEFAULT '',
    state         TEXT NOT NULL,
    last_seq      INTEGER NOT NULL,
    entry_time_utc TEXT NOT NULL DEFAULT '',
    entry_basis   REAL NOT NULL DEFAULT 0.0,
    entry_z       REAL NOT NULL DEFAULT 0.0
);
```

Updated with an `INSERT ... ON CONFLICT(basket_id) DO UPDATE` **in the same
transaction** as the event that changed the basket's state. Integrity check
verifies `basket_current` matches the last event per basket; it is a
fast-startup cache, and reconstruction always replays `events`.

## State validation on write

`append_event` enforces, before commit:

1. If `dedup_key` provided and already present → idempotent no-op (existing
   event returned; nothing appended).
2. If the event type is a **required transition** event, both
   `prior_state` and `new_state` must be present AND form a valid transition
   in the frozen state-machine graph. Otherwise `ValueError` (fail closed).
3. If states are provided on any other event, they are validated the same way.
4. Payload is stored JSON + `payload_hash` (sha256 of canonical JSON).

## Startup integrity check

Returns a list of problems; ANY problem ⇒ engine fails closed
(`BLOCKED_UNKNOWN_STATE`), no signal processing:

* schema version mismatch
* missing table
* sequence gap or duplicate (non-contiguous `seq`)
* payload hash mismatch / corrupt JSON
* required-transition event with missing or invalid states
* `basket_current` stale or inconsistent with events

## Runtime files

* `tb_ledger.db` — WAL-mode database (runtime, git-ignored)
* `tb_ledger.db-wal` / `tb_ledger.db-shm` — WAL sidecar files (managed by
  SQLite)

## Migration policy

Schema changes require a migration; old rows are never silently
reinterpreted. `TB_STATE_SCHEMA_VERSION` gates this.

**Scientific changes: NONE.**
