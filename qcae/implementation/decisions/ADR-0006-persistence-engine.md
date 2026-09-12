# ADR-0006 — Persistence Engine for the Evidence + Registry Spine

**Status:** Accepted (P1)
**Phase:** P1 — Evidence + Registry Spine
**Canon refs:** Book V 13.3 (storage layers — "Exact technology is implementation policy"),
15.9 (persistence ports; engines under infrastructure), Book IV 9.1–9.7, master prompt §4

## Context

P1 requires durable structured metadata (evidence, receipts, registries,
knowledge, lineage) plus a content-addressed raw-artifact store. Book V 13.3
permits "SQLite/DuckDB or equivalent"; 15.9 requires engines live behind
repository ports under `infrastructure/`. The engine choice is not frozen by
canon, so it is decided here.

## Constraints

- `qcae/core` stays stdlib-only (ADR-0001); the engine is imported only by
  `qcae/infrastructure/persistence/`.
- Unit-of-work semantics with real rollback (P1 §15) are mandatory.
- Local-first: single-process local application today (Book V 15.1 Early
  Simplicity), possible multi-process read access later.
- Migration ledger + schema version tracking must be implementable simply.
- Backup/restore must be deterministic and testable.
- Anti-framework rule: adoption burden must be justified by capability.

## Alternatives

1. **SQLite (Python stdlib `sqlite3`).** Full ACID transactions with true
   rollback; WAL mode gives concurrent readers with a single writer;
   `user_version` + a migration-ledger table make version tracking trivial;
   file-copy / backup API restore is deterministic; zero dependency burden
   (stdlib); universally understood operational model.
   Weakness: analytics slower than column stores.
2. **DuckDB (already a repository dependency).** Excellent analytical scans,
   but single-writer-process file semantics make multi-process write unsafe,
   its OLTP transaction behavior is not its design center (P1 workloads are
   small, indexed, record-oriented writes — not scans), no migration tooling,
   and ~40MB engine burden for metadata work.
   Weakness as primary store; strength stays available for analytics.
3. **SQLAlchemy over either engine.** Present in `uv.lock` only transitively
   (via zipline/nautilus). Adds an ORM abstraction layer over a local store we
   fully control — framework burden without system-level capability gain
   (anti-framework rule). Repository ports already provide the abstraction
   the domain needs.
4. **Pure-JSON/flat-file store.** No transactions, no rollback, manual
   indexing; fails §15 without reinventing SQLite badly.

## Decision

- **SQLite (stdlib `sqlite3`) is the transactional metadata engine**, accessed
  exclusively through persistence ports (`qcae/core/ports/`) with the concrete
  adapter in `qcae/infrastructure/persistence/sqlite/`.
- WAL journal mode; `BEGIN IMMEDIATE` unit-of-work boundaries; foreign keys on.
- **Raw evidence artifacts** live in the content-addressed filesystem store
  (P1-C02), not in the database; the database holds digests + metadata.
- **Analytical/export snapshots (Parquet via DuckDB/pyarrow)** are explicitly
  deferred — built only when a phase justifies them (13.3 permits, does not
  require). DuckDB remains installed for quant-lab; QCAE core does not touch it.
- Schema version lives in SQLite `PRAGMA user_version` plus a migration-ledger
  table recording applied migrations with timestamps and digests.

## Reason

P1 workloads are record-oriented, transaction-bound, and integrity-critical:
exactly SQLite's design center. Every criterion in the comparison list
(transactions, migration, portability, operational simplicity, local-first,
concurrency, backup) favors it; only future analytics favor DuckDB, and the
port design keeps that door open for a later analytics adapter without
touching domain semantics (15.9 invariant 1).

## Burden

- One new stdlib-module adapter; SQL DDL maintained by hand (migration ledger
  compensates); SQL-injection discipline enforced by parameterized statements.
- Analytics queries will be slower than DuckDB — acceptable until a Parquet
  export path is justified.

## Reversibility

High. All domain code sees only persistence ports; swapping the engine means
writing one new adapter plus a migration. The append/supersede data model is
engine-agnostic by construction.

## Canon Compatibility

Direct implementation of Book V 13.3 (which names SQLite first) and 15.9;
no contradiction with any Book I–VI chapter or A-001.
