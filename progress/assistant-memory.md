# 🟡 Assistant Manager — Working Memory

> **Auto-synced** from `progress/assistant-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

---

## Current Context (2026-08-06 23:10 UTC — Symmetry Trap Live Multi-Asset Engine Deployed)

### Status
🟢 SYMMETRY TRAP LIVE MULTI-ASSET ENGINE RUNNING — Ready for tomorrow's session

### Deployment Summary
- **Engine**: `quant-lab/mt5/symmetry_trap_executor_multi.py` — Realistic wick/touch-based stop logic
- **Assets**: ETHUSD, HK50, NZDUSD, BTCUSD, US500, EURUSD, USDCHF, AUDUSD (8 assets)
- **MT5 Connection**: Verified (Account 1114712, Balance $282.98, OxSecurities-Demo)
- **Configuration**: Lot 0.03, Magic 20260531, Entry 2AM-11AM EST, Hard Exit 5PM EST
- **Stop Logic**: Realistic wick/touch-based (triggers on price touch/wick, not bar close)
- **Engine**: Symmetry Trap (Engine B ONLY — no P90 cross)

### Backtest Verification (All 8 Assets)
| Asset | Trades | WR | Net PnL | PF |
|-------|--------|-----|---------|-----|
| ETHUSD | 792 | 89.9% | +9,545.2p | 17.98 |
| BTCUSD | 1,179 | 82.6% | +74,294.7p | 10.80 |
| NZDUSD | 1,557 | 78.9% | +6,730.3p | 9.11 |
| US500 | 1,154 | 80.2% | +7,428.4p | 9.00 |
| EURUSD | 999 | 73.4% | +4,280.7p | 6.20 |
| USDCHF | 984 | 72.0% | +4,301.1p | 7.24 |
| AUDUSD | 641 | 75.8% | +2,417.5p | 6.88 |
| HK50 | 0 | 0.0% | 0.0p | 0.00 |

### Deployment Status
- ✅ Engine syntax fixed (GLOBAL_PARAMS, SYMBOLS_TO_TRADE)
- ✅ MT5 connection verified (Account 1114712, Balance $282.98, OxSecurities-Demo)
- ✅ Engine started successfully at 23:08:49
- ✅ Correctly detected outside trading hours (22:00 EST ≥ 17:00 EST hard exit)
- ✅ Graceful shutdown — will auto-resume at 2AM EST tomorrow
- ✅ Logs in `quant-lab/mt5/live_logs_multi/`

### Next Steps
Engine is running in background. Will auto-resume scanning at 2AM EST tomorrow.
Command: `python mt5/symmetry_trap_executor_multi.py --loop --interval 30`

---

## Current Context (2026-06-13 09:00 UTC)

### Phase 1.6 — Orchestration (2026-06-13)
- core/orchestration/ — Controller, planner, workflow, scheduler, governance, agents, memory, reflection
- 25/25 unit tests passing
- Central execution authority with task routing, recursion limits, safety governance

### Phase 1.7 — Self-Evolution (2026-06-13)
- core/evolution/ — Self-evaluation, research generator, learning loop, architecture evolution, strategy mutation, capability generation, model benchmarking, long-term adaptation
- 26/26 unit tests passing
- OCE can now detect its own weaknesses, generate research objectives, and evolve its architecture

### PDF Generation
- core/research/synthesis/pdf_generator.py — reportlab-based PDF generation
- Reports saved to data/reports/ and desktop
- Generated 2 PDF research reports (63-95 KB)
- **Fixed 3 phantom imports** in po_vault.py
- **Fixed persistent_field_api.py** — HTTP 503 + logging (was silent 200 OK errors)
- **Fixed vault_api.py** — logging + proper HTTP 503
- **Fixed srrs_adapter.py** — try/except wrappers on module-level imports
- **Tests:** 492/492 passing
- **Health score:** 94/100
- **Audit file:** `oce/backend/PO_FIELD_CHECK.md`

### Key Issues to Track
1. Dual macro implementation (old flat file vs new `macro/` package) — needs consolidation
2. Retrain path wrong (`data/combined/` vs `data/`) — will fail as-is
3. Missing micro features in old feature matrices — 6 of 8 micro features absent
4. PM2 never built pattern recognition — PM did it instead
5. `test_macro_features.py` missing `import pytest`

### Next AS Actions
- ✅ MLR window fixed (07:00-15:00 UTC)
- ✅ BTC/ETH Friday Asian anchor added
- ✅ Asian session boundaries fixed
- ✅ 9 new tests added (8 passing)
- Remaining: Write `test_pattern_recognition.py` (PM2's missing tests)
- Remaining: Prepare Wave 3 test suite (Guardian + RAG)
- Remaining: Fix PM's `detect_all_patterns` bug (requires bias column from MLR)

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

## Current Context (2026-05-27 17:00 UTC)

### Status
🟢 Active — O-5 Readiness Review Complete

### Active Phase
Observer Core + OCE Unified — O-1 through O-4 complete. O-5 in progress (CC leading). O-7 planned (AS).

### Key Patterns for OCE Frontend

#### Zustand Store Architecture (OCE)
- **Pattern:** `create<T>((set, get) => ({ ... }))` — standard Zustand with TypeScript
- **Existing stores (6):** taskStore, agentStore, timelineStore, topologyStore, uiStore, sessionStore
- **New stores added (3):** observerStore, consensusStore, spawnStore, learningStore
- **Store merging for O-5:** SRRA-OPH stores (topologyStore, entropyStore, repairStore, continuityStore, timelineStore) need to merge into OCE equivalents
- **Key interface pattern:** Each store has `setX`, `getX`, `addX`, `updateX`, `clearX` actions

#### Dark Theme CSS Variables (SRRA-OPH → OCE migration)
- **Current OCE theme:** Light operational (`--bg-primary: #ffffff`, `--text-primary: #1a1a2e`)
- **Target OCE theme:** Dark observatory (needs CSS variable override)
- **SRRA-OPH pattern:** Dark scientific theme with `--bg-primary: #0a0a0f` style variables
- **Migration approach:** Override CSS variables in globals.css, keep component classes

#### Component Structure Pattern
- **Layout:** TopNav + MainContent + RightPanel + StatusBar (4-region)
- **Pages:** Next.js app router (`app/[page]/page.tsx`)
- **Components:** `components/[feature]/Component.tsx`
- **Stores:** `stores/storeName.ts` with Zustand
- **Hooks:** `hooks/use[Feature].ts` for data fetching

### Migration Patterns (SRRA-OPH → OCE)

#### Store Interface Mapping
| SRRA-OPH Store | OCE Store | Migration Action | Status |
|----------------|-----------|-----------------|--------|
| topologyStore.ts | topologyStore.ts | Migrated with ObserverNode/Edge/ClusterState | ✅ Done |
| entropyStore.ts | entropyStore.ts | Created with EntropyEngine class | ✅ Done |
| repairStore.ts | repairStore.ts | Migrated with RepairEvent interface | ✅ Done |
| continuityStore.ts | continuityStore.ts | Migrated with Checkpoint interface | ✅ Done |
| timelineStore.ts | timelineStore.ts | Migrated with RuntimeFrame types | ✅ Done |

#### Component Migration List
- ObservatoryCanvas → OCE topology page ✅
- EntropyField → OCE entropy page ✅
- RepairCascade → OCE repair page ✅
- AttractorMap → OCE attractors page (pending)
- ClusterOverlay → OCE topology overlay (pending)
- RepairWaveAnimation → OCE repair visualization (pending)

### Testing Requirements for Unified Frontend
1. **Store integration tests** — Verify merged stores work together ✅
2. **Component render tests** — Each migrated component renders in OCE layout ✅
3. **WebSocket unification test** — Single LiveDataProvider serves all panels ✅
4. **Performance tests** — 60fps idle, 30fps under load (pending)
5. **Theme consistency** — All panels use dark observatory theme ✅
6. **Navigation tests** — In-app panel switching works (pending)

### O-7 Persistent Field — Expected Structure
- **Backend (12 components):** PersistentRuntime, ObserverPersistence, PassiveAwareness, EnvironmentalMonitor, ContinuityPreserver, DormantStateManager, AutonomousRepair, RuntimeHeartbeat, PersistentScheduler, RecoveryPersistence, LongHorizonMemory, OperationalDriftDetector
- **Frontend (9 components):** PersistentFieldView, RuntimeHeartbeatPanel, DormantStateMonitor, ObserverPersistenceView, DriftAnalysisPanel, LongHorizonTimeline, AutonomousRepairView, RecoveryContinuityPanel, persistenceStore
- **Dependencies:** O-7 depends on O-6 → O-5 → O-4
- **Key pattern:** Long-horizon continuity (7-day operation), autonomous repair, drift detection

---

## Sync Metadata
- **Last Sync:** 2026-05-27 17:00 UTC
- **Progress File:** `progress/assistant-progress.md`
- **Working Memory:** `progress/assistant-memory.md`
- **Sync Threshold:** 7 updates

## Shared Notes (read-only references)
- Build Notes: `progress/BUILD-NOTES.md`
- Team Notes: `progress/TEAM-NOTES.md`
- Phase 11 Status: `progress/phase-11-status.md`
- Observer Core Tasks: `plans/observer-core/TEAM-TASKS.md`
- build_notes: `progress/BUILD-NOTES.md` (updated 2026-06-02 15:00 UTC)
