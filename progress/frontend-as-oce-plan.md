# 🟢 AS — OCE Frontend Plan
## Operational Cockpit Build (Phases 1-4)

**Agent:** AS (me)
**Frontend:** OCE (:3000)
**Base:** `oce/frontend/` (Next.js 15, React 19, TypeScript)
**Dependencies:** None — can start immediately

---

## PHASE 1 — COCKPIT FOUNDATION

### 1.1 Theme + Visual Foundation
**Files:**
- `app/globals.css` — Clean operational theme (light, functional, low-fatigue)
- `tailwind.config.ts` — Operational color tokens

**Color tokens:**
```css
--bg-primary: #f8f9fa
--bg-secondary: #ffffff
--accent-primary: #2563eb
--accent-success: #16a34a
--accent-warning: #d97706
--accent-danger: #dc2626
--text-primary: #1a1a2e
--text-secondary: #6b7280
```

### 1.2 Layout System
**Files:**
- `app/layout.tsx` — Cockpit layout
- `components/layout/TopNav.tsx` — Top navigation bar
- `components/layout/MainContent.tsx` — Main content area
- `components/layout/RightPanel.tsx` — Right context panel
- `components/layout/StatusBar.tsx` — Bottom status bar

### 1.3 State Management
**Files:**
- `stores/taskStore.ts` — Task queue, active/completed/failed
- `stores/agentStore.ts` — Agent status, health, current tasks
- `stores/sessionStore.ts` — Session state, active experiments
- `stores/uiStore.ts` — UI state, filters, panel visibility

### 1.4 Routing
**Files:**
- `app/dashboard/page.tsx` — Main dashboard
- `app/tasks/page.tsx` — Task management
- `app/agents/page.tsx` — Agent status
- `app/chaos/page.tsx` — Chaos test monitoring
- `app/settings/page.tsx` — Settings

### 1.5 WebSocket Connection
**Files:**
- `lib/websocket/oce-socket.ts` — WebSocket client to OCE backend (:8000)
- `hooks/useOCEStream.ts` — React hook for live data
- `components/ConnectionStatus.tsx` — Connection indicator

---

## PHASE 2 — TASK + AGENT MANAGEMENT

### 2.1 Task Queue
**Files:**
- `components/tasks/TaskQueue.tsx` — Task list with status
- `components/tasks/TaskCard.tsx` — Individual task card
- `components/tasks/TaskCreator.tsx` — Create/delegate tasks
- `components/tasks/TaskProgress.tsx` — Live progress bars

### 2.2 Agent Status
**Files:**
- `components/agents/AgentGrid.tsx` — Agent status grid
- `components/agents/AgentCard.tsx` — Agent health, task, uptime
- `components/agents/AgentLog.tsx` — Agent communication log

### 2.3 Progress Tracking
**Files:**
- `components/dashboard/ProgressOverview.tsx` — Overall progress
- `components/dashboard/ActiveTasks.tsx` — Currently running tasks
- `components/dashboard/RecentActivity.tsx` — Activity feed

---

## PHASE 3 — CHAOS TEST MONITORING

### 3.1 Live Chaos Dashboard
**Files:**
- `components/chaos/ChaosDashboard.tsx` — Live chaos test status
- `components/chaos/AmplificationGauge.tsx` — Current amplification factor
- `components/chaos/CycleProgress.tsx` — Cycle counter and progress
- `components/chaos/ScenarioBreakdown.tsx` — Per-scenario pass/fail

### 3.2 Chaos Event Timeline
**Files:**
- `components/chaos/ChaosTimeline.tsx` — Chronological chaos events
- `components/chaos/RecoveryChart.tsx` — Recovery time over cycles

### 3.3 Historical Results
**Files:**
- `components/chaos/TestHistory.tsx` — Past chaos test results
- `components/chaos/TestComparison.tsx` — Compare test runs

---

## PHASE 4 — SEMANTIC TEST RESULTS (Phase 11.4.1+11.4.2)

### 4.1 Contradiction Test Results
**Files:**
- `components/semantic/SemanticTestDashboard.tsx` — Overview of 11.4.1 results
- `components/semantic/ContradictionTimeline.tsx` — Chronological contradiction map
- `components/semantic/TestCategoryResult.tsx` — Per-category (1A-1E) results

### 4.2 Metrics Dashboard
**Files:**
- `components/semantic/MetricsGrid.tsx` — All 8 metrics with pass/fail
- `components/semantic/MetricCard.tsx` — Individual metric display
- `components/semantic/MetricsChart.tsx` — Metrics over time

**Metrics displayed:** SDI, RIS, OCS, APS, FAR, RVA, SIS, TVT

### 4.3 Observer Consensus + Reconstruction
**Files:**
- `components/semantic/ConsensusReport.tsx` — Observer agreement visualization
- `components/semantic/ReconstructionReport.tsx` — Recovered/discarded truths

---

## SUCCESS CONDITIONS

### Phase 1:
✅ OCE cockpit launches with clean operational theme
✅ Layout stable (top nav, main, right panel, status bar)
✅ Zustand stores operational
✅ WebSocket connected to backend

### Phase 2:
✅ Task queue functional
✅ Agent status cards live-updating
✅ Progress tracking visible

### Phase 3:
✅ Chaos test dashboard shows live amplification
✅ Event timeline renders
✅ Historical results viewable

### Phase 4:
✅ Semantic test results displayed
✅ All 8 metrics with pass/fail indicators
✅ Contradiction timeline renders
