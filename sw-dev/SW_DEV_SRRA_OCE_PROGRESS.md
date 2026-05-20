# SW Dev — SRRA-OPH Frontend + OCE Frontend Upgrade

> **Started:** 2026-05-19 18:40 EDT
> **Status:** 🔨 In Progress

## Phase 1: SRRA-OPH Frontend (PRIORITY 1)

### 1.1 SRRA-OPH API Wrapper — FastAPI
- [x] Analyze SRRA-OPH module architecture (50 modules, 9 phases)
- [ ] Create `srrs_opc/api/` — FastAPI wrapper
  - [ ] `/health` — Overall SRRA-OPH health
  - [ ] `/modules` — List all modules with status
  - [ ] `/topology` — Topology graph data
  - [ ] `/tests` — Test results summary
  - [ ] `/events` — Event stream
  - [ ] `/phases` — Phase status (1-9)

### 1.2 SRRA-OPH Frontend — Next.js
- [ ] Create `srrs_opc/frontend/` — Next.js app
  - [ ] `/` — Dashboard overview
  - [ ] `/topology` — Topology visualization
  - [ ] `/modules` — Module status cards
  - [ ] `/tests` — Test results
  - [ ] `/events` — Event stream
  - [ ] Components: ModuleCard, TopologyGraph, EventStream, TestResults, HealthIndicator
  - [ ] Dark theme, WebSocket, TypeScript

## Phase 2: OCE Frontend Upgrade (PRIORITY 2)

- [ ] Review oce/frontend/ — identify broken/incomplete parts
- [ ] Add System Map page improvements
- [ ] Add real-time agent feed
- [ ] Add better metrics display
- [ ] Add theme toggle
- [ ] Add error handling improvements
- [ ] Add SRRA tab showing SRRA module status

## Phase 3: Venv Integration

- [ ] Read agent-environment docs
- [ ] Add SRRA+OCE status to agent environment dashboard
- [ ] Unified monitoring

## Architecture Notes

### SRRA-OPH Backend
- 50 Python modules across 9 phases
- Phase 1: Base patches (Planner, Execution, Memory, Repair) + CollarLayer
- Phase 2: Recovery + Drift detection
- Phase 3: Topology (DynamicCoupling, TopologicalRouter, DistributedConsensus)
- Phase 4: Workspace integration
- Phase 5: Long-horizon continuity
- Phase 6: Recursive topology introspection
- Phase 7: Multi-scale overlap ecologies
- Phase 8: Sovereign coevolution
- Phase 9: Entropy economics
- OCE backend already has `/health/srrs` endpoint via srrs_adapter

### OCE Frontend
- Next.js 15, React 19, TypeScript
- Dark theme (#0a0a0f bg)
- Pages: /, /command-center, /execution, /observability
- Components: MetricsPanel, SystemMap, AlertPanel, TraceView, ExecutionMonitor, ExecutionAnalytics, TaskDetail
- API client at `lib/api.ts` hitting localhost:8000
- WebSocket hook at `lib/useWebSocket.ts`
