# OCE Phase 4 Quality Review — Structural Memory

**Date:** 2026-05-16
**Reviewer:** Sub-AS
**Scope:** `oce/backend/structural_memory.py` + `oce/backend/tests/test_structural_memory.py`

---

## 1. Summary

The Structural Memory engine is a clean, well-structured implementation of a three-layer memory system (WORK / LEARNED / KNOWLEDGE) backed by SQLite with FTS5 full-text search. The code is readable, properly typed with Pydantic models, and follows solid engineering practices. The test suite covers all public methods with 30 tests across 7 test classes. The main areas for improvement are: missing database indexes for common query patterns, no input validation/sanitization on the search path, no TTL-based expiration logic, and the FTS5 tag post-filter is an in-memory operation that could bottleneck at scale. Overall, this is a strong foundation that works correctly for the current scope but needs hardening before production use.

---

## 2. What's Good

- **Clean architecture**: Separation of models (`MemoryEntry`, `MemoryLayer`, `MemoryStats`) from engine logic (`StructuralMemory`) is well done. Pydantic models provide validation and serialization for free.
- **FTS5 integration**: Using SQLite FTS5 with triggers for automatic index sync is the right approach — no external search dependency, zero-config, and performant for the expected data volume.
- **WAL mode + foreign keys**: `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` show awareness of SQLite concurrency and integrity best practices.
- **`INSERT OR REPLACE` in store()**: Gracefully handles upserts without requiring a separate code path for updates.
- **Comprehensive test suite**: 30 tests covering all public methods, edge cases (empty DB, no results, overwrites), and cross-layer isolation. Tests use `tmp_path` for isolation — no test pollution.
- **Layer isolation in compress()**: Correctly scopes compression to a single layer, verified by `test_compress_only_affects_target_layer`.
- **Wiki export**: Clean markdown generation with proper filtering to KNOWLEDGE layer only. File output tested.
- **API integration**: The `main.py` endpoints wrap the engine cleanly with proper error handling (ValueError → 400, Exception → 503).
- **Singleton pattern**: `get_structural_memory()` in `main.py` ensures a single DB connection pool per process.
- **Logging**: Appropriate use of `logger.info` for store and compress operations — aids debugging without being noisy.

---

## 3. Issues Found

### 🔴 HIGH — No Input Validation on Search Query

**File:** `structural_memory.py`, `search()` method
**Detail:** The `query` parameter is passed directly to `memory_fts MATCH ?` with no sanitization. FTS5 query syntax supports operators (`AND`, `OR`, `NOT`, `*`, `^`, `"`) and malformed queries (e.g., unmatched parentheses, trailing operators) will raise `sqlite3.OperationalError` that propagates unhandled. The API layer catches generic `Exception` → 503, but this should be a 400 with a clear message.
**Impact:** Malformed FTS5 queries crash the search endpoint. An attacker could probe for error responses.

### 🔴 HIGH — No TTL Expiration Logic

**File:** `structural_memory.py`
**Detail:** The `ttl_seconds` field is stored in the DB but never enforced. There is no `expire()` method, no background cleanup, and no TTL filtering in `search()` or `get_timeline()`. Entries with `ttl_seconds` set will live forever. This is a data integrity gap — the API accepts `ttl_seconds` in the request model (`StoreMemoryRequest`) creating the impression that TTLs work.
**Impact:** WORK-layer entries (designed to be ephemeral) accumulate indefinitely, defeating the purpose of the three-layer architecture.

### 🟡 MEDIUM — Missing Database Indexes

**File:** `structural_memory.py`, `_init_db()`
**Detail:** No indexes on `layer`, `source`, or `created_at` columns. The `search()` method filters by `layer` and orders by `created_at`. The `get_timeline()` method filters by `source` and `created_at`. The `compress()` method filters by `layer` and orders by `created_at`. All of these will do full table scans without indexes.
**Impact:** Performance degrades linearly with data volume. At 10K+ entries (expected for WORK layer over time), search and compress operations will be noticeably slow.

### 🟡 MEDIUM — FTS5 Tag Post-Filter Is In-Memory

**File:** `structural_memory.py`, `search()` method
**Detail:** When `tags` are provided alongside a full-text query, the FTS5 search runs first (returning `limit` rows), then tags are filtered in Python. This means: (1) the FTS5 query may return 20 results, all of which get filtered out by tags, returning 0 results to the caller; (2) the `limit` applies before tag filtering, so the caller may get fewer results than requested with no way to know why.
**Impact:** Unpredictable result counts. Callers requesting `limit=20` with a tag filter may get 0-20 results.

### 🟡 MEDIUM — No Pagination Support

**File:** `structural_memory.py`, `search()` and `get_timeline()` methods
**Detail:** Only `limit` is supported — no `offset` parameter. The API endpoints also lack pagination. For timeline queries that could return thousands of entries, this will cause large payloads and slow responses.
**Impact:** API consumers cannot paginate results. Large timelines will be slow or truncated.

### 🟡 MEDIUM — `get_timeline()` Missing `limit` Parameter

**File:** `structural_memory.py`, `get_timeline()` method
**Detail:** Unlike `search()`, `get_timeline()` has no `limit` parameter. A timeline query for an active observer could return the entire database. The API endpoint also doesn't enforce one.
**Impact:** Unbounded query results — potential memory and response size issues.

### 🟢 LOW — `compress()` Return Value Not Verified Against Actual Deletion

**File:** `structural_memory.py`, `compress()` method
**Detail:** The method calculates `to_remove` from a `SELECT COUNT(*)` then runs a `DELETE ... LIMIT ?`. The return value is the *calculated* number to remove, not the *actual* number of rows deleted. In concurrent scenarios (WAL mode allows concurrent readers), the actual deletions could differ.
**Impact:** Minor — the FTS triggers handle cleanup, and the count is used for logging/API response, not for critical logic.

### 🟢 LOW — `export_wiki()` Uses `entry.content.get("title", ...)` Without Schema Enforcement

**File:** `structural_memory.py`, `export_wiki()` method
**Detail:** The `content` field is `Dict[str, Any]` — there's no guarantee it has a `"title"` or `"body"` key. The fallback to `entry.entry_id[:8]` works but produces ugly wiki entries. The `body` fallback dumps the entire content dict as JSON, which may not be readable markdown.
**Impact:** Wiki quality varies depending on how entries are structured. Not a bug, but a UX concern.

### 🟢 LOW — No `rowid` Alias in Table Schema

**File:** `structural_memory.py`, `_init_db()`
**Detail:** The FTS5 triggers reference `rowid` (e.g., `content_rowid='rowid'`), which works because SQLite tables implicitly have a `rowid`. However, if the table is ever recreated with `INTEGER PRIMARY KEY` (which aliases to `rowid`), the FTS triggers would break. Currently `entry_id` is `TEXT PRIMARY KEY`, so the implicit `rowid` is used — this is correct but fragile and undocumented.
**Impact:** Low — works now, but a future schema change could silently break FTS sync.

---

## 4. Recommendations

### Immediate (Before Phase 5)

1. **Add input validation for FTS5 queries** — Wrap the FTS5 MATCH in a try/except that catches `sqlite3.OperationalError` and returns an empty list or raises a clear validation error. Consider validating the query string for balanced parentheses and valid operators before passing to SQLite.

2. **Add database indexes** — Create the following indexes in `_init_db()`:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_memory_layer ON memory_entries(layer);
   CREATE INDEX IF NOT EXISTS idx_memory_source ON memory_entries(source);
   CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at);
   ```

3. **Implement TTL expiration** — Add an `expire()` method that deletes entries where `created_at + ttl_seconds < now()`, and call it from `search()` (or as a periodic cleanup). At minimum, filter expired entries from search results.

### Short-Term (Phase 5-6)

4. **Fix tag filtering** — Either: (a) store tags as a space-separated string in a dedicated column and use FTS5 to search tags, or (b) increase the FTS5 query limit significantly and accept the post-filter, but document the behavior. Option (a) is more correct.

5. **Add pagination** — Add `offset` parameter to `search()` and `get_timeline()`. Enforce a maximum `limit` (e.g., 100) in the API layer.

6. **Add `limit` to `get_timeline()`** — Both the engine method and the API endpoint should accept and enforce a limit.

### Long-Term

7. **Consider content schema validation** — For KNOWLEDGE layer entries, enforce a schema (e.g., `title: str, body: str`) at the Pydantic model level to ensure wiki export quality.

8. **Add `rowid` documentation** — Add a comment in `_init_db()` explaining that `entry_id` is TEXT PRIMARY KEY (not aliasing rowid), so the implicit rowid is used for FTS5. This prevents future breakage.

---

## 5. Test Coverage Analysis

| Method | Tests | Coverage Quality | Notes |
|--------|-------|-----------------|-------|
| `MemoryEntry.__init__` | 5 | ✅ Excellent | Defaults, explicit IDs, tags, source, timestamps all tested |
| `store()` | 4 | ✅ Good | Store+retrieve, all layers, overwrite behavior tested |
| `search()` | 6 | ✅ Good | FTS query, layer filter, tags, combined, limit, no results |
| `get_timeline()` | 4 | ✅ Good | Chronological order, observer filter, time range, empty result |
| `compress()` | 3 | ✅ Good | No-op, removes oldest, layer isolation |
| `export_wiki()` | 4 | ✅ Good | Markdown content, layer filtering, file write, empty knowledge |
| `get_stats()` | 4 | ✅ Good | Counts, oldest/newest, db size, empty DB |

### Missing Test Coverage

| Gap | Severity | Suggested Test |
|-----|----------|----------------|
| FTS5 query with special characters (malformed) | 🔴 HIGH | `test_search_malformed_fts_query_returns_empty_or_raises` |
| TTL expiration | 🔴 HIGH | `test_expired_entries_not_returned_in_search` (requires `expire()` method first) |
| Concurrent store operations | 🟡 MEDIUM | `test_concurrent_stores_no_data_loss` |
| `get_timeline()` with no limit on large datasets | 🟡 MEDIUM | `test_timeline_returns_all_matching_entries` (verify no silent truncation) |
| `compress()` with exactly `max_entries` entries (boundary) | 🟢 LOW | `test_compress_exact_boundary` |
| `export_wiki()` with content missing title/body keys | 🟢 LOW | `test_export_wiki_fallback_title_and_body` |
| Unicode content in store/search | 🟢 LOW | `test_unicode_content_roundtrip` |
| Very large `limit` parameter | 🟢 LOW | `test_search_large_limit` |

### Test Infrastructure Notes

- **Fixtures are well-designed**: `mem` (clean instance) and `populated_mem` (6 entries across 3 layers) provide good isolation and realistic data.
- **No mocking needed**: Tests use real SQLite via `tmp_path`, which is correct for this layer — integration tests with real DB are more valuable than mocked unit tests.
- **Test naming**: Clear and consistent (`test_<method>_<scenario>`). Easy to identify what's broken from test output.

---

## 6. Integration Assessment

**With `main.py` (API layer):**
- ✅ Clean integration via `get_structural_memory()` singleton
- ✅ All 6 engine methods exposed as REST endpoints (`/memory/store`, `/memory/search`, `/memory/timeline/{id}`, `/memory/compress`, `/memory/export`, `/memory/stats`)
- ✅ Proper HTTP status codes (400 for bad input, 503 for service errors)
- ⚠️ API `tags` parameter passed as comma-separated string (not JSON array) — works but inconsistent with the `StoreMemoryRequest` model which accepts `List[str]`
- ⚠️ No `limit` cap on `/memory/search` or `/memory/timeline/{id}` — client can request `limit=10000`

**With `srrs_adapter.py`:**
- ✅ `get_structural_memory()` in adapter returns SRRA-OPH topology data (separate concern from the SQLite engine — no conflict)
- ✅ No circular imports — adapter imports from `event_fabric`, not from `structural_memory`

**With other OCE modules:**
- ✅ No direct coupling to `event_fabric`, `observer_runtime`, or `dspy_pipelines` — structural memory is a standalone module that can be tested and deployed independently
- ⚠️ No event emission on memory operations — storing/compressing memory doesn't emit events to the Event Fabric, so the memory system is invisible to observers

---

## 7. Security Assessment

| Area | Status | Notes |
|------|--------|-------|
| SQL Injection | ✅ Safe | All queries use parameterized statements (`?` placeholders) |
| FTS5 Query Injection | ⚠️ Partial | FTS5 MATCH syntax can cause errors but not data leakage. Should validate/sanitize. |
| Input Validation | ⚠️ Weak | No validation on `content` dict structure, `tags` list contents, or `source` string. Malformed data can be stored. |
| Path Traversal (`export_wiki`) | ⚠️ Partial | `path` parameter accepts any `Path` — no restriction on directory. In API, path is not user-supplied (server-side only), so risk is low. |
| Denial of Service | ⚠️ Weak | No rate limiting, no max `limit` enforcement, no max `content` size. A client could store huge entries or request unlimited results. |

---

**Overall Grade: B+**

Solid implementation with good test coverage and clean architecture. The main gaps are operational (indexes, TTL, input validation) rather than structural. Fix the 2 HIGH issues and add indexes, and this is production-ready.
