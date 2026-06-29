# PM2 PO Field Test Results

Timestamp: 2026-06-26T14:00:00Z

```json
{
  "type": "test_results",
  "command": "po_field_test_pm2",
  "target": "primary_observer_tools",
  "assignee": "PM2",
  "executed_by": "CC (on behalf of PM2)",
  "timestamp": "2026-06-26T14:00:00Z",
  "status": "complete"
}
```

## Final Results: 26 PASS, 14 FAIL out of 40

### PASSING TESTS (26)

| # | Test | Endpoint | Status |
|---|------|----------|--------|
| 1 | memory/store WORK | POST /memory/store | ✅ 200 |
| 2 | memory/store LEARNED | POST /memory/store | ✅ 200 |
| 3 | memory/store KNOWLEDGE | POST /memory/store | ✅ 200 |
| 4 | agent/execute read_file | POST /agent/execute | ✅ 200 |
| 5 | agent/execute write_file | POST /agent/execute | ✅ 200 |
| 6 | agent/execute edit_file | POST /agent/execute | ✅ 200 |
| 7 | agent/execute run_python | POST /agent/execute | ✅ 200 |
| 8 | agent/execute git_op log | POST /agent/execute | ✅ 200 |
| 9 | agent/execute git_op diff | POST /agent/execute | ✅ 200 |
| 10 | PO git_log | POST /api/po/tools/execute | ✅ 200 |
| 11 | PO search_content | POST /api/po/tools/execute | ✅ 200 |
| 12 | PO write_file | POST /api/po/tools/execute | ✅ 200 |
| 13 | PO execute_python | POST /api/po/tools/execute | ✅ 200 |
| 14 | memory/search | GET /memory/search | ✅ 200 |
| 15 | memory/compress | POST /memory/compress | ✅ 200 |
| 16 | memory/export | GET /memory/export | ✅ 200 |
| 17 | memory/stats | GET /memory/stats | ✅ 200 |
| 22 | events/ingest | POST /events/ingest | ✅ 200 |
| 23 | events/types | GET /events/types | ✅ 200 |
| 24 | events/stats | GET /events/stats | ✅ 200 |
| 25 | events/persistence/stats | GET /events/persistence/stats | ✅ 200 |
| 27 | topology/edge (corrected) | POST /topology/edge | ✅ 200 |
| 28 | topology/stats | GET /topology/stats | ✅ 200 |
| 37 | governance/propose | POST /governance/propose | ✅ 200 |
| 38 | governance/proposals | GET /governance/proposals | ✅ 200 |
| 39 | resonance/signal | POST /resonance/signal | ✅ 200 |
| 40 | resonance/score | POST /resonance/score | ✅ 200 |

### FAILING TESTS (14)

| # | Test | Endpoint | Error | Root Cause |
|---|------|----------|-------|------------|
| 18 | PO chat | POST /api/po/chat | Timeout | LLM response slow — blocks single-threaded uvicorn |
| 19 | PO chat stream | POST /api/po/chat | Timeout | Same as above |
| 20 | rate-limit/status | GET /rate-limit/status | Timeout | Cascading from test 18 |
| 21 | rate-limit/errors | GET /rate-limit/errors | 503 | Rate limit tracker not initialized |
| 26 | events/persistence/compress | POST /events/persistence/compress | 422 | Missing required body fields |
| 29 | observers POST | POST /observers | 200 but not persisted | **BUG**: create_observer returns 200 but observer not stored |
| 30-35 | observer CRUD | various | 404 | Cascading from test 29 — observer doesn't exist |
| 36 | observer delete | DELETE | 404 | Same |

## Bugs Found

### BUG-1: Observer Persistence Failure (MEDIUM)
- **Endpoint:** POST /observers → GET /observers/{id}
- **Symptom:** POST returns 200 with observer_id, but subsequent GET returns 404 "Observer not found"
- **Root Cause:** `runtime.create_observer(config)` accepts the config but doesn't persist to internal store
- **Impact:** Observer CRUD lifecycle broken — can create but not retrieve/activate/delete

### BUG-2: PO Chat Blocks Backend (LOW)
- **Endpoint:** POST /api/po/chat
- **Symptom:** LLM response takes >15s, blocks all subsequent requests on single-threaded uvicorn
- **Root Cause:** Synchronous LLM call in async handler without background task
- **Impact:** PO chat unusable in production — needs async LLM or worker pool

### BUG-3: Rate Limit Tracker 503 (LOW)
- **Endpoint:** GET /rate-limit/errors
- **Symptom:** Returns 503 "Service Unavailable"
- **Root Cause:** Rate limit tracker not initialized at startup
- **Impact:** Rate limit monitoring unavailable

### BUG-4: Events Persistence Compress Schema (LOW)
- **Endpoint:** POST /events/persistence/compress
- **Symptom:** 422 "Field required" — body cannot be null
- **Root Cause:** Endpoint requires body but schema unclear
- **Impact:** Cannot trigger persistence compression via API

## Corrected Schemas (for future reference)

### Observer Create
```json
POST /observers
{
  "observer_id": "unique_id",
  "name": "Display Name",
  "observer_type": "custom",
  "goal": "Observer purpose",
  "initial_state": "active"
}
```

### Topology Edge
```json
POST /topology/edge
{
  "observer_a": "source_id",
  "observer_b": "target_id",
  "weight": 0.8
}
```

### Agent Execute
```json
POST /agent/execute
{
  "action": "read_file|write_file|edit_file|run_python|git_op|run_command",
  "params": { ... }
}
```

### Memory Store
```json
POST /memory/store
{
  "layer": "WORK|LEARNED|KNOWLEDGE",
  "content": { ... }
}
```
