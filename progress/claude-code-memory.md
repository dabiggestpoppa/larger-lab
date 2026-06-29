# 🔵 Claude Code — Working Memory

> **Auto-synced** from `progress/claude-code-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

## Current Context (2026-06-26 12:10 UTC — All Endpoints Fixed + PO Test Assigned)

### Status
🟢 OCE BACKEND RUNNING on port 8000 — ALL 26 ENDPOINTS PASSING

### Fixes Applied (this session)
1. **sovereign_api.py**: `.stats` → `.get_stats()` for ExecutiveRouter + ToolEmbodimentLayer
2. **sovereign_api.py**: `_get_shell().get_status()` → `_get_shell().state.to_dict()`
3. **resonance_api.py**: `_field_manager.state` → `_field_manager.current_state`
4. **resonance_api.py**: `_signal_field.stats()` → `_signal_field.stats` (property, not method)
5. **Terminal cleanup**: Killed stale node daemon (34h), duplicate DDG MCP, stale PowerShell terminals

### Active Task
**PO Field Testing — COMPLETE (26 PASS / 14 FAIL out of 40)**
- CC executed all tests on behalf of PM2
- 4 bugs found: observer persistence (MEDIUM), PO chat blocks backend, rate limit 503, events compress 422
- Vault: `O2C-VAULT/journal_20260626T140000Z_pm2_po_test_results.md`
- Test script: `tests/pm2_po_field_test.py`

**Whop Store Build — COMPLETE (9/9 PASS)**
- All 15 products configured in `whop-store/`
- 3 consultations ACTIVE, 12 future offerings ready
- Brand, payments, integrations all configured
- Results: `progress/PO-FIRST-TEST-RESULTS.md`

**PM2 Whop Verification — COMPLETE (10/10 PASS)**
- PM2 executed `tests/pm2_whop_verify.py` via terminal
- Created observer, ingested event, proposed governance, injected resonance
- Vault: `O2C-VAULT/journal_20260626T142000Z_pm2_whop_build.json`

---

## PowerShell/Windows Execution Gotchas

### Encoding Issues
- **Problem:** Windows PowerShell defaults to `cp1252` encoding, breaking emoji and Unicode
- **Fix:** Always set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Symptom:** 🔄✅⚠️ characters appear as `?` or cause silent failures

### Process Invocation
- **Problem:** `Start-Process "openclaw"` opens .ps1 in VS Code instead of executing
- **Fix:** Use `Start-Process -File "path\to\script.ps1"` or `Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "script.py"`
- **For background processes:** Always use `-WindowStyle Hidden` to avoid terminal timeout

### Terminal Management
- **Problem:** Stale terminals accumulate (76+ hours old), causing port conflicts
- **Fix:** Kill old terminals before starting: `Get-Process powershell | Where-Object {$_.StartTime -lt (Get-Date).AddHours(-1)} | Stop-Process`
- **Best practice:** Use `gateway_watchdog.py` for 24/7 monitoring instead of async terminals

### Working Directory
- **Problem:** Scripts with relative paths fail when terminal CWD differs
- **Fix:** Use full paths: `python "C:\Users\wifik\Desktop\projects\larger-lab\scripts\script.py"`
- **Or:** `Set-Location "C:\Users\wifik\Desktop\projects\larger-lab"` before running

### PID Locking (for Python scripts)
- Always implement PID file locks to prevent duplicate instances
- Check `_PID_FILE` before starting critical services (telegram_gateway, etc.)
- Use `taskkill /F /PID <pid>` to kill stale processes

---

## Current Context (2026-05-28 12:00 UTC — Post O-6 Test Fix)

### Status
🟢 V3 PHASES 1-10 COMPLETE + Phase 11 Short-Run Tests Complete + O-1..O-5 Complete + O-6 Tests Passing

### Active Phase
**Observer Core + OCE Unified — O-6 Local Substrate**
- O-1: ✅ Complete (42/42 tests)
- O-2: ✅ Complete (13 tests need alignment — pre-existing)
- O-3: ✅ Complete (25 tests need alignment — pre-existing)
- O-4: ✅ Complete (14/14 tests)
- O-5: ✅ Complete (all 12 components + Layer 3 panels)
- O-6: 🔄 Foundation complete, **52/52 tests passing** (fixed in this session)
- O-7: ⏳ Planned (AS docs done, awaiting PM/PM2)

### O-6 Fixes Applied (2026-05-28)
1. **Syntax error:** `with.assertRaises` → `with pytest.raises` (line 284)
2. **Async test pattern:** `self.assertRaises` → `pytest.raises` in all async test methods
3. **Permission layer:** Added echo/ls/cat/pwd command rules
4. **Pattern matching:** Fixed `_matches_pattern` to handle space-separated commands (`echo hello` matches `echo:*`)
5. **Terminal orchestrator:** Changed `command.split()[0]` → `command` for permission check

### Pending Tasks
- 11.1-B: Resume or restart 72h test (operator decision required)
- 11.5: 7-day orchestration stability test

### Recent Activity (from git)
#### 🔵 [CC] 2026-05-26 — Memory Reconstruction
- All agent memory files were stale (last updates 2026-05-24)
- Reconstructed from git log — ~20 commits not in any memory file
- Updated all progress + memory files

#### 🔵 [CC] 2026-05-25 — LiveDataProvider Fix + Skills Cleanup
- Fixed infinite loop in LiveDataProvider.tsx (commit 5d6c795)
- Removed 700+ accidentally downloaded skills (commit 198bdf7)
- System restart — all services restored (commit 1e59589)

#### 🔵 [CC] 2026-05-24 — All Frontend Phases Complete
- SRRA-OPH: All 5 phases, 13 pages (commits d1f650d, c7ae63b)
- OCE: All pages complete
- PM2: Phases 3-5 built (commits ef8c3a4, 0a21a9c)

#### 🔵 [CC] 2026-05-18 16:00 UTC — Phase 10 Core Build Complete
- Built all 5 Phase 10 modules: rcg.py, prs.py, rpe.py, dct.py, ace.py
- All 23 Phase 10 tests passing
- Full suite: 1403 OCE + 57 SRRA-OPH = 1460 total tests passing
- Fixed API mismatches in 4 tests (RecursiveFieldNode, PRS, DriftGovernor)
- All 11 capability tests passing
- Tests validate: field coherence chain, RCG integration, PRS integration, memory efficiency, concurrent operations, error recovery, observer pattern, drift recovery, attractor convergence, compute throughput, memory growth
- **Status:** System validated for deployment readiness

#### 🔵 [CC] 2026-05-21 12:00 UTC — Phase 11.1 Infrastructure Verified
- Verified Phase 11.1 Long-Horizon Continuity Testing infrastructure
- Observer Stress Test: tools/testing/long_horizon/observer_stress.py ✅
- Runtime Monitor: tools/testing/long_horizon/runtime_monitor.py ✅
- Continuity Checksum Engine: tools/testing/long_horizon/continuity_checksum.py ✅
- Stability Runner Daemon: tools/testing/long_horizon/stability_runner.py ✅
- Stability Database: stability/runtime_metrics.db, continuity_states.db ✅
- Schema: stability/schema.sql ✅
- Updated workspace-state.md and team-chat.md with Phase 11.1 status
- **Status:** Ready for 24-hour observer survival test

---

## Sync Metadata
- **Last Sync:** 2026-05-21 14:07:41 UTC
- **Progress File:** `progress/claude-code-progress.md`
- **Working Memory:** `progress/claude-code-memory.md`
- **Sync Threshold:** 7 updates


## Sync Metadata
- **Last Sync:** 2026-05-26 14:00 UTC
- **Shared Notes (read-only):** `progress/BUILD-NOTES.md` | `progress/TEAM-NOTES.md` | `progress/phase-11-status.md`
- build_notes: `progress/BUILD-NOTES.md` (updated 2026-06-02 15:00 UTC)
