# O-6: Local Execution Substrate — Implementation Plan

> **Created:** 2026-05-28
> **Status:** Foundation Complete — Ready for Testing
> **Assigned to:** PM (Backend), PM2 (Frontend)

---

## 🎯 O-6 OBJECTIVE

Build the **Local Execution Substrate** — machine-aware bounded execution layer that enables:
- Filesystem awareness and scoped access
- Terminal orchestration with safety boundaries
- Process monitoring and lifecycle management
- Application bridge for controlled interaction
- Recovery controller for runtime stabilization

---

## 📦 BACKEND COMPONENTS (11)

| # | Component | File | Priority | Dependencies |
|---|-----------|------|----------|------------|
| 1 | LocalRuntime | `oce/backend/substrate/local_runtime.py` | HIGH | O-3 Spawn Engine |
| 2 | FilesystemAwareness | `oce/backend/substrate/filesystem_awareness.py` | HIGH | LocalRuntime |
| 3 | TerminalOrchestrator | `oce/backend/substrate/terminal_orchestrator.py` | HIGH | LocalRuntime |
| 4 | ProcessObserver | `oce/backend/substrate/process_observer.py` | MEDIUM | TerminalOrchestrator |
| 5 | ApplicationBridge | `oce/backend/substrate/application_bridge.py` | MEDIUM | LocalRuntime |
| 6 | EnvironmentModel | `oce/backend/substrate/environment_model.py` | MEDIUM | FilesystemAwareness |
| 7 | RuntimeInspector | `oce/backend/substrate/runtime_inspector.py` | LOW | ProcessObserver |
| 8 | PermissionLayer | `oce/backend/substrate/permission_layer.py` | HIGH | All execution components |
| 9 | ExecutionSandbox | `oce/backend/substrate/execution_sandbox.py` | HIGH | PermissionLayer |
| 10 | MachineStateGraph | `oce/backend/substrate/machine_state_graph.py` | LOW | All substrate components |
| 11 | RecoveryController | `oce/backend/substrate/recovery_controller.py` | HIGH | All components |

---

## 🖥️ FRONTEND COMPONENTS (8)

| # | Component | File | Priority | Dependencies |
|---|-----------|------|----------|------------|
| 1 | MachineStateView | `oce/frontend/components/substrate/MachineStateView.tsx` | HIGH | substrateStore |
| 2 | ProcessGraph | `oce/frontend/components/substrate/ProcessGraph.tsx` | MEDIUM | substrateStore |
| 3 | RuntimeInspector | `oce/frontend/components/substrate/RuntimeInspector.tsx` | MEDIUM | substrateStore |
| 4 | FilesystemTopology | `oce/frontend/components/substrate/FilesystemTopology.tsx` | HIGH | substrateStore |
| 5 | SandboxMonitor | `oce/frontend/components/substrate/SandboxMonitor.tsx` | HIGH | substrateStore |
| 6 | EnvironmentModelView | `oce/frontend/components/substrate/EnvironmentModelView.tsx` | LOW | substrateStore |
| 7 | TerminalExecutionPanel | `oce/frontend/components/substrate/TerminalExecutionPanel.tsx` | HIGH | substrateStore |
| 8 | RecoveryTimeline | `oce/frontend/components/substrate/RecoveryTimeline.tsx` | MEDIUM | substrateStore |

---

## 🗄️ STORE

| Component | File | Description |
|-----------|------|-------------|
| substrateStore | `oce/frontend/stores/substrateStore.ts` | Zustand store for substrate state |

---

## 🔌 API ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/substrate/state` | GET | Current machine state |
| `/api/substrate/processes` | GET | Active processes |
| `/api/substrate/filesystem` | GET | Filesystem topology |
| `/api/substrate/execute` | POST | Execute command in sandbox |
| `/api/substrate/sandbox` | GET | Sandbox status |
| `/api/substrate/recovery` | POST | Trigger recovery action |

---

## 📋 IMPLEMENTATION ORDER

### Phase 1: Core Substrate (Days 1-2)
1. Create `substrate/` directory in backend
2. Implement `LocalRuntime` - central orchestration point
3. Implement `PermissionLayer` - security boundaries
4. Implement `ExecutionSandbox` - safe execution zones
5. Add API endpoints to `main.py`

### Phase 2: Filesystem + Terminal (Days 2-3)
1. Implement `FilesystemAwareness` - workspace awareness
2. Implement `TerminalOrchestrator` - command execution
3. Implement `EnvironmentModel` - runtime context
4. Add frontend `substrateStore.ts`

### Phase 3: Process + Recovery (Days 3-4)
1. Implement `ProcessObserver` - process monitoring
2. Implement `RecoveryController` - stabilization
3. Implement `MachineStateGraph` - topology representation
4. Add `/api/substrate/` endpoints

### Phase 4: Frontend Components (Days 4-5)
1. `MachineStateView` - live machine state
2. `FilesystemTopology` - workspace as graph
3. `TerminalExecutionPanel` - execution display
4. `SandboxMonitor` - sandbox status
5. `ProcessGraph` - process visualization
6. `RecoveryTimeline` - recovery history

---

## ✅ SUCCESS CRITERIA

- [x] All 11 backend components implemented
- [x] All 8 frontend components implemented
- [x] All 7 API endpoints registered
- [ ] Filesystem scoped access tested
- [ ] Terminal bounded execution tested
- [ ] Process monitoring operational
- [ ] Recovery controller tested
- [ ] 8/8 tests passing

---

## 📊 TEST SCENARIOS

1. **Filesystem awareness** - Track repo mutations, workflow outputs
2. **Terminal orchestration** - Bounded execution workflows
3. **Process monitor** - Hung processes, overload conditions
4. **Environment model** - Switch projects, runtimes
5. **Sandbox** - Out-of-scope execution attempts
6. **Machine topology** - Complex runtime workflows
7. **Recovery** - Observer crash, process failure
8. **Long horizon** - 72hr operational session