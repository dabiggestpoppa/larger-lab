# System Architecture — Mermaid Diagrams

> **Purpose:** All system-level Mermaid diagrams in one place.
> **For:** Pipeline alignment review, architecture verification.
> **Updated:** 2026-05-16

## Files

| File | Content | Phases |
|------|---------|--------|
| `CODEMAP.md` | **Unified system architecture** — all 5 levels + workflows + storage | All |
| `01-system-overview.md` | Full system at all 5 levels | All |
| `02-agent-workflow.md` | Agent communication, workflow state machine, event flow | All |
| `03-srra-topology.md` | SRRA-OPH technical architecture per phase | 1-9 |
| `04-data-and-storage.md` | Data pipeline, storage layers, backup, memory sync | All |

## Architecture Levels

1. **Level 1:** Human Interface + Agent Network (6 agents, OC2 gateway)
2. **Level 2:** SRRA-OPH Substrate (9 phases, observer patches, repair loops)
3. **Level 3:** OCE — Operator Continuity Engine (Event Fabric, Observer Runtime)
4. **Level 4:** Data + Trading Pipeline (CSV → Parquet → Nautilus → Reports)
5. **Level 5:** Infrastructure + External Services (Cloud, APIs, Monitoring)

## Key Pipelines

### OCE Event Pipeline
```
SRRA-OPH → Event Fabric → Observer Runtime → WebSocket → Frontend
                ↓                ↓
           Persist to      State Updates
           Trajectory      → Telegram
```

### Agent Coordination Pipeline
```
Human → CC → OC → HR/OC2 → Results → Progress Files → Sync → Memory
```

### Memory Sync Pipeline
```
progress files → progress-sync.py → working memory + persistent memory + repo memory
team-chat.md → chat_sync.py → working memory + repo memory
errors → errors-and-solutions.md → repo memory (every 7 entries)
```

## Alignment Checklist

Use this to verify the actual pipeline matches the original architecture:

- [x] **Phase 1:** CollarLayer + 4 patches + AgentBridge → `srrs_opc/`
- [x] **Phase 2:** Recovery anchors, drift detector, reconstruction → `srrs_opc/`
- [x] **Phase 3:** Dynamic coupling, topological router, active collars → `srrs_opc/`
- [x] **Phase 4:** Capability fields, workspace integration → `srrs_opc/`
- [x] **Phase 5:** Trajectory fields, continuity collars → `srrs_opc/`
- [x] **Phase 6:** Topology observer, recursive routing → `srrs_opc/`
- [x] **Phase 7:** Overlap cognition, prediction contracts → `srrs_opc/`
- [x] **Phase 8:** Operator patterns, strategic preferences → `srrs_opc/`
- [x] **Phase 9:** Entropy economics, sustainability governance → `srrs_opc/`
- [x] **OCE Event Fabric:** Ingest → Route → Persist → Stream → `oce/backend/event_fabric.py`
- [x] **OCE Observer Runtime:** Lifecycle → Health → State → `oce/backend/observer_runtime.py`
- [x] **OC2 Gateway:** Telegram + Watchdog + Context Monitor → `.openclaw-2/`
- [x] **Memory Sync:** 7-update threshold, 20-entry summarize → `tools/progress-sync.py`

### V3 Phase 1 Alignment Checklist

- [x] **SignalPacket:** Signal ontology with resonance scoring → `oce/backend/resonance/signal_packet.py`
- [x] **CoherenceMetrics:** 6 metrics tracking → `oce/backend/resonance/coherence_metrics.py`
- [x] **FieldStateManager:** Field state management → `oce/backend/resonance/field_state.py`
- [x] **BoundaryMapper:** Boundary detection → `oce/backend/resonance/boundary_mapper.py`
- [x] **ResonanceEngine:** Resonance alignment → `oce/backend/resonance/resonance_engine.py`
- [x] **PressureTracker:** Entropy pressure monitoring → `oce/backend/resonance/pressure_tracker.py`
- [x] **RL Integration:** RL ↔ CC bridge → `oce/backend/resonance/rlp_integration.py`
- [x] **Debug CLI:** `tools/operator/resonance-debug.py`

### V3 Phase 2 Alignment Checklist

- [x] **CausalGeometry:** Causal relationship mapping → `oce/backend/reconstruction/causal_geometry.py`
- [x] **AttractorMemory:** Memory attractor patterns → `oce/backend/reconstruction/attractor_memory.py`
- [x] **ReconstructionEngine:** State reconstruction → `oce/backend/reconstruction/reconstruction_engine.py`
- [x] **OverlapManifold:** Overlap computation → `oce/backend/reconstruction/overlap_manifold.py`
- [x] **ContinuityRepair:** Repair continuity gaps → `oce/backend/reconstruction/continuity_repair.py`
