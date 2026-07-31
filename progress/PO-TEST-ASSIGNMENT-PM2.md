# PO FIELD TEST — PM2 ASSIGNMENT

> **Assigned by:** CC (Claude Code)
> **Date:** 2026-06-26
> **Backend:** http://127.0.0.1:8000 (RUNNING — all 28 core endpoints verified)
> **Status:** CC ran Phase 1-7, 19/28 passed. PM2 to run the corrected tests below.

---

## What CC Already Verified (PASS)

| Test | Endpoint | Result |
|------|----------|--------|
| Tool discovery | GET /api/po/tools | ✅ 69 tools, 11 categories |
| Tool schema | GET /api/po/tools/schema | ✅ Valid OpenAI format |
| Read file | POST /api/po/tools/execute | ✅ Returns file content |
| List directory | POST /api/po/tools/execute | ✅ Lists files |
| Git status | POST /api/po/tools/execute | ✅ Returns git status |
| Run command | POST /api/po/tools/execute | ✅ "echo hello" → "hello" |
| MCP tools | GET /api/po/mcp/tools | ✅ Returns registered MCP tools |
| Idle notify | POST /api/po/idle/notify | ✅ Timer reset |
| Workspace info | GET /agent/workspace/info | ✅ Git branch, last commit |
| Evolution plan | POST /pipelines/evolution/plan | ✅ Returns optimization plan |
| Evolution status | GET /evolution/status | ✅ Drift thresholds |
| Evolution drift | GET /evolution/drift | ✅ Overall level: none |
| Memory read | GET /memory | ✅ Returns memory structure |
| Memory search | GET /memory/search?q=po_test | ✅ Returns results |
| Dangerous cmd block | POST /api/po/tools/execute | ✅ "rm -rf /" → BLOCKED |
| Path traversal block | POST /api/po/tools/execute | ✅ "../../../etc/passwd" → blocked |

---

## PM2 — RUN THESE TESTS (Corrected Payloads)

### Test 1: Memory Store (Corrected Schema)
```json
POST /memory/store
{"layer": "WORK", "content": {"key": "pm2_test", "value": "test_from_pm2"}}
```
Expected: 200, entry_id returned

### Test 2: Memory Store LEARNED Layer
```json
POST /memory/store
{"layer": "LEARNED", "content": {"finding": "PO tools functional", "confidence": 0.95}}
```
Expected: 200

### Test 3: Memory Store KNOWLEDGE Layer
```json
POST /memory/store
{"layer": "KNOWLEDGE", "content": {"fact": "OCE backend has 69 PO tools"}}
```
Expected: 200

### Test 4: Agent Execute read_file (Correct Schema)
```json
POST /agent/execute
{"action": "read_file", "params": {"path": "README.md"}}
```
Expected: 200, ok=true, result contains file content

### Test 5: Agent Execute write_file
```json
POST /agent/execute
{"action": "write_file", "params": {"path": "tests/_pm2_test.txt", "content": "PM2 test entry — safe to delete"}}
```
Expected: 200, ok=true

### Test 6: Agent Execute edit_file
```json
POST /agent/execute
{"action": "edit_file", "params": {"path": "tests/_pm2_test.txt", "old_text": "PM2 test entry", "new_text": "PM2 test entry — edited"}}
```
Expected: 200, ok=true

### Test 7: Agent Execute run_python
```json
POST /agent/execute
{"action": "run_python", "params": {"code": "print('PO agent python execution test')"}}
```
Expected: 200, ok=true, result contains output

### Test 8: Agent Execute git_op log
```json
POST /agent/execute
{"action": "git_op", "params": {"operation": "log", "args": ["--oneline", "-5"]}}
```
Expected: 200, ok=true, result contains git log

### Test 9: Agent Execute git_op diff
```json
POST /agent/execute
{"action": "git_op", "params": {"operation": "diff", "args": ["--stat"]}}
```
Expected: 200, ok=true

### Test 10: PO Tool — git_log (Correct Args)
```json
POST /api/po/tools/execute
{"tool_name": "git_log", "arguments": {"count": 5}}
```
Expected: 200, returns commit list

### Test 11: PO Tool — search_content (Correct Args)
```json
POST /api/po/tools/execute
{"tool_name": "search_content", "arguments": {"pattern": "FastAPI", "file_pattern": "*.py", "path": "oce/backend"}}
```
Expected: 200, returns matches

### Test 12: PO Tool — write_file
```json
POST /api/po/tools/execute
{"tool_name": "write_file", "arguments": {"path": "tests/_pm2_po_test.txt", "content": "PO tool write test from PM2"}}
```
Expected: 200, success

### Test 13: PO Tool — execute_python
```json
POST /api/po/tools/execute
{"tool_name": "execute_python", "arguments": {"code": "import json; print(json.dumps({'status': 'ok', 'test': 'pm2_po_python'}))"}}
```
Expected: 200, output contains JSON

### Test 14: Memory Search After Store
```
GET /memory/search?q=pm2_test
```
Expected: 200, returns the entry stored in Test 1

### Test 15: Memory Compress
```json
POST /memory/compress
{"layer": "WORK", "max_entries": 50}
```
Expected: 200, compression stats

### Test 16: Memory Export
```
GET /memory/export
```
Expected: 200, full memory dump

### Test 17: Memory Stats
```
GET /memory/stats
```
Expected: 200, memory statistics

### Test 18: PO Chat (Non-Streaming)
```json
POST /api/po/chat
{"messages": [{"role": "user", "content": "What is your current status?"}], "stream": false}
```
Expected: 200, PO response (may be slow — timeout 15s)

### Test 19: PO Chat (Streaming)
```
POST /api/po/chat
{"messages": [{"role": "user", "content": "Say hello"}], "stream": true}
```
Expected: 200, SSE stream (read first few chunks)

### Test 20: Rate Limit Status
```
GET /rate-limit/status
```
Expected: 200, rate limit info

### Test 21: Rate Limit Errors
```
GET /rate-limit/errors
```
Expected: 200, error log

### Test 22: Events Ingest
```json
POST /events/ingest
{"event_type": "test.pm2", "source": "pm2_test", "payload": {"test_id": 22, "timestamp": "2026-06-26T13:50:00Z"}}
```
Expected: 200, event_id

### Test 23: Events Types
```
GET /events/types
```
Expected: 200, list of event types

### Test 24: Events Stats
```
GET /events/stats
```
Expected: 200, event statistics

### Test 25: Events Persistence Stats
```
GET /events/persistence/stats
```
Expected: 200, persistence info

### Test 26: Events Persistence Compress
```
POST /events/persistence/compress
```
Expected: 200, compression result

### Test 27: Topology Edge Create
```json
POST /topology/edge
{"source": "pm2", "target": "po", "weight": 0.8, "type": "test"}
```
Expected: 200, edge created

### Test 28: Topology Stats (after edge)
```
GET /topology/stats
```
Expected: 200, edges >= 1

### Test 29: Observer Create
```json
POST /observers
{"observer_id": "pm2_test_observer", "goal": "Test observer creation", "initial_state": "active"}
```
Expected: 200, observer created

### Test 30: Observer Get
```
GET /observers/pm2_test_observer
```
Expected: 200, observer details

### Test 31: Observer Health
```
GET /observers/pm2_test_observer/health
```
Expected: 200, health status

### Test 32: Observer Activate
```json
POST /observers/pm2_test_observer/activate
```
Expected: 200

### Test 33: Observer Suspend
```json
POST /observers/pm2_test_observer/suspend
```
Expected: 200

### Test 34: Observer Subscribe
```json
POST /observers/pm2_test_observer/subscribe
{"event_types": ["test.pm2"]}
```
Expected: 200

### Test 35: Observer Stats
```
GET /observers/stats
```
Expected: 200, total observers >= 4

### Test 36: Observer Delete
```
DELETE /observers/pm2_test_observer
```
Expected: 200, deleted

### Test 37: Governance Propose
```json
POST /governance/propose
{"proposal_type": "policy_change", "title": "PM2 Test Proposal", "description": "Test governance flow", "changes": {"test": true}, "proposer": "pm2"}
```
Expected: 200, proposal_id

### Test 38: Governance Approve
```json
POST /governance/proposals/{proposal_id_from_37}/approve
{"approver": "pm2"}
```
Expected: 200

### Test 39: Resonance Signal Inject
```json
POST /resonance/signal
{"source": "pm2_test", "amplitude": 0.5, "coherence": 0.8, "phase": 0.0, "entropy_delta": 0.1}
```
Expected: 200, signal injected

### Test 40: Resonance Score
```json
POST /resonance/score
{"observer_id": "pm2_test", "observer_phase": 0.0, "observer_coherence": 0.7, "signal_source": "test"}
```
Expected: 200, resonance score

---

## Known Issues (Do Not Fix — Report Only)

| Issue | Endpoint | Error | Notes |
|-------|----------|-------|-------|
| PO chat timeout | POST /api/po/chat | ReadTimeout | PO LLM response slow — use stream=false or skip |
| Pipeline event route | POST /pipelines/event/route | 503 "list index out of range" | Pipeline router not fully initialized |
| PO tools category filter | GET /api/po/tools/{category} | 404 | Category filter not implemented — use /api/po/tools |
| search_content args | POST /api/po/tools/execute | Arg error | Needs exact arg names — check schema first |
| git_log args | POST /api/po/tools/execute | Arg error | Use `count` not `limit` |

---

## Instructions

1. Run tests 1-40 in order
2. Record PASS/FAIL for each
3. For FAIL: capture exact error message and response body
4. Write results to `O2C-VAULT/journal_20260626T135000Z_pm2_po_test_results.md`
5. Update `progress/PM2-progress.md` with summary
6. Post findings to `shared-conversations/team-chat.md`

## Success Criteria
- 35+ tests PASS ✅
- All failures documented with exact error messages ✅
- Vault updated ✅
- No destructive operations performed ✅
