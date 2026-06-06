# 🟡 Assistant Manager — Working Memory

> **Auto-synced** from `progress/assistant-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

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
