# OCE ↔ SRRA-OPH Integration Points

> **Author:** AS (Assistant Manager)
> **Date:** 2026-05-16
> **Status:** Draft — Phase 1 OCE Continuity Shell

## Purpose

This document maps every OCE component to its SRRA-OPH substrate dependency. OCE is the **user-facing continuity shell**; SRRA-OPH is the **cognitive substrate**. This doc ensures no OCE component is built without a clear integration path.

## Architecture Overview

```
User
  ↓
OCE Shell UI (Next.js)
  ↓ HTTP / WebSocket
OCE Continuity Core (FastAPI)
  ↓ Python imports / internal calls
SRRA-OPH Substrate (srrs_opc/)
  ↓
Observer Runtime → Tools / Models / State
```

## Integration Map

### OCE Phase 1 — Continuity Shell

| OCE Component | SRRA-OPH Dependency | Integration Method | Status |
|---|---|---|---|
| `POST /chat` | Phase 5 `continuity_collars.py`, Phase 8 `operator_continuity.py` | Import + call continuity functions | 🔄 Scaffold only |
| `GET /observers` | Phase 1 `observer_mesh.py`, Phase 2 `reconstruction_synthesizer.py` | Query observer state from mesh | 🔄 Scaffold only |
| `GET /events` | Phase 2 `event_fabric.py` (pending) | Read from event store | 🔄 Scaffold only |
| `GET /attractor` | Phase 7 `attractor_reasoning.py` | Call attractor state | 🔄 Scaffold only |
| `GET /memory` | Phase 5 `trajectory_fields.py`, Phase 7 `structural_memory.py` | Query memory layer | 🔄 Scaffold only |
| `WS /ws/events` | Phase 2 event fabric | Stream events via WebSocket | 🔄 Scaffold only |

### OCE Phase 2 — Event Fabric

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Event ingestion | Phase 2 `event_fabric.py` | Direct import |
| Event routing | Phase 3 `topological_router.py` | Route events through topology |
| Event persistence | Phase 5 `trajectory_fields.py` | Store in trajectory log |

### OCE Phase 3 — Observer Runtime

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Observer lifecycle | Phase 1 `observer_mesh.py` | Create/destroy observers |
| Observer state | Phase 2 `reconstruction_synthesizer.py` | Reconstruct from patches |
| Observer repair | Phase 2 `repair_loops.py` | Trigger repair on failure |

### OCE Phase 4 — Structural Memory

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Trajectory store | Phase 5 `trajectory_fields.py` | Read/write trajectories |
| Topology graph | Phase 3 `dynamic_coupling.py` | Query topology state |
| Memory compression | Phase 9 `adaptive_compression.py` | Compress old memories |

### OCE Phase 5 — Observability

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Metrics | Phase 6 `topology_tracking.py` | Export topology metrics |
| Health checks | Phase 2 `repair_loops.py` | Check repair status |
| Cost tracking | Phase 9 `entropy_budget.py` | Track resource usage |

### OCE Phase 6 — Execution Substrate

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Tool execution | Phase 4 `capability_fields.py` | Execute via capability fields |
| Workspace ops | Phase 4 `workspace_integration.py` | File/system operations |
| Trading systems | Phase 4 `tool_adapter.py` | Trading tool integration |

### OCE Phase 7 — Attractor Engine

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Goal management | Phase 7 `attractor_reasoning.py` | Set/get goals |
| Convergence tracking | Phase 7 `multi_scale_metrics.py` | Monitor convergence |
| Entropy pressure | Phase 7 `collar_entropy_tracking.py` | Read entropy state |

### OCE Phase 8 — Reconstruction

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| State reconstruction | Phase 2 `reconstruction_synthesizer.py` | Rebuild from patches |
| Identity continuity | Phase 5 `trajectory_fields.py` | Reconstruct identity |
| Repair intelligence | Phase 2 `repair_loops.py` | Auto-repair |

### OCE Phase 9 — Adaptive Evolution

| OCE Component | SRRA-OPH Dependency | Integration Method |
|---|---|---|
| Entropy economics | Phase 9 `entropy_budget.py` | Resource optimization |
| Sustainability | Phase 9 `sustainability_governance.py` | Long-term stability |
| Self-model updates | Phase 8 `probabilistic_self_models.py` | Update self-model |

## SRRA-OPH Module Dependency Graph (for OCE)

```
srrs_opc/
├── observer_mesh.py          ← OCE Phase 1 (observers), Phase 3 (runtime)
├── reconstruction_synthesizer.py ← OCE Phase 1 (observers), Phase 3 (repair), Phase 8 (reconstruction)
├── repair_loops.py           ← OCE Phase 3 (repair), Phase 5 (health)
├── event_fabric.py           ← OCE Phase 1 (events), Phase 2 (event fabric)
├── dynamic_coupling.py       ← OCE Phase 2 (routing), Phase 4 (topology)
├── topological_router.py     ← OCE Phase 2 (routing)
├── trajectory_fields.py      ← OCE Phase 1 (memory), Phase 2 (persistence), Phase 4 (store), Phase 5 (identity)
├── continuity_collars.py     ← OCE Phase 1 (chat)
├── operator_continuity.py    ← OCE Phase 1 (chat)
├── capability_fields.py      ← OCE Phase 6 (execution)
├── workspace_integration.py  ← OCE Phase 6 (workspace)
├── attractor_reasoning.py    ← OCE Phase 1 (attractor), Phase 7 (goals)
├── multi_scale_metrics.py    ← OCE Phase 7 (convergence)
├── collar_entropy_tracking.py ← OCE Phase 7 (entropy)
├── adaptive_compression.py   ← OCE Phase 4 (compression)
├── entropy_budget.py         ← OCE Phase 5 (cost), Phase 9 (economics)
├── sustainability_governance.py ← OCE Phase 9 (sustainability)
└── probabilistic_self_models.py ← OCE Phase 9 (self-model)
```

## Integration Sequence

OCE must integrate SRRA-OPH modules in dependency order:

1. **Phase 1**: `observer_mesh`, `reconstruction_synthesizer`, `continuity_collars`, `operator_continuity`, `attractor_reasoning`, `trajectory_fields`
2. **Phase 2**: `event_fabric`, `dynamic_coupling`, `topological_router`
3. **Phase 3**: (reuse Phase 1+2 modules)
4. **Phase 4**: `adaptive_compression`
5. **Phase 5**: `repair_loops`, `entropy_budget`
6. **Phase 6**: `capability_fields`, `workspace_integration`
7. **Phase 7**: `multi_scale_metrics`, `collar_entropy_tracking`
8. **Phase 8**: (reuse Phase 2 modules)
9. **Phase 9**: `sustainability_governance`, `probabilistic_self_models`

## Open Questions for CC

1. Should OCE call SRRA-OPH via Python imports (same process) or via internal HTTP API (separate processes)?
2. Does the event fabric use Redis Streams or in-memory asyncio queues for Phase 1?
3. Should the `/chat` endpoint stream responses (SSE) or return complete responses?
4. What auth mechanism for Phase 1? (API key, JWT, none for local dev?)
