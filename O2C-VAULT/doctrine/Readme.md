# Readme

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# System Architecture — Mermaid Diagrams

> **Purpose:** All system-level Mermaid diagrams in one place.
> **For:** Pipeline alignment review, architecture verification.
> **Updated:** 2026-05-18 | Phase 10 Complete | 1460 tests passing

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
- [x] **Phase 10:** Recursive field computation → `oce/backend/phase10/`
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

### V3 Phase 10 Alignment Checklist

- [x] **RecursiveComputeGraph:** Recursive compute graph + stabilization → `oce/backend/phase10/rcg.py`
- [x] **PositionalReferenceSystem:** Positional reference system → `oce/backend/phase10/prs.py`
- [x] **ResonancePropagationEngine:** Resonance propagation → `oce/backend/phase10/rpe.py`
- [x] **DynamicConstraintTopology:** Dynamic constraint topology → `oce/backend/phase10/dct.py`
- [x] **AttractorComputeEngine:** Attractor compute engine → `oce/backend/phase10/ace.py`
- [x] **Total:** 23 tests passing

LINKS:
[[Architecture]]
[[Codemap]]
[[System Architecture]]
[[V3 Cognitive Field]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Claude]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Progress]]
[[Team Roster]]
[[Action]]
[[Api Endpoints]]
[[Cal]]
[[Cohere]]
[[Description]]
[[Interaction]]
[[Modules]]
[[Optimization]]
[[Patterns]]
[[Rest Api]]
[[Server]]
[[Skill]]
[[Sources]]
[[System]]
[[Workflow]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Metrics]]
[[Observer Consensus]]
[[Observer Lifecycle]]
[[Primary Observer]]
