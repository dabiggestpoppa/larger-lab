# Module Guide — 78 Modules Reference

TYPE: architecture
SUMMARY: Summary of all 78 modules (67 V3 + 11 Observer Core) organized by phase.
CAUSE: Developers need a quick reference for what each module does.
FUNCTION: Module lookup reference.

## V3 Phases (67 modules, 1403 tests)

### Phase 1: Resonant Signal Substrate (7 modules)
- signal_packet.py — SignalPacket, SignalField
- coherence_metrics.py — CoherenceEngine (6 metrics)
- field_state.py — FieldStateManager
- boundary_mapper.py — BoundaryMapper, PressureZone
- resonance_engine.py — ResonanceEngine (CCR mechanism)
- pressure_tracker.py — PressureTracker

### Phase 2: Reconstructive Continuity Manifold (6 modules)
- reconstruction_engine.py — Topology-constrained state reconstruction
- continuity_repair.py — ContinuityRepair, BreakReport
- attractor_memory.py — AttractorMemory
- drift_detector.py — DriftDetector, DriftMetrics
- self_healing_engine.py — SelfHealingEngine

### Phase 3: Resonant Topology & BSP (7 modules)
- topology_engine.py — Dynamic resonance structures
- bsp_emergence.py — Boundary Signal Projection
- collar_field.py — Collar field management
- resonance_topology.py — Topology resonance scoring

### Phase 4: Sovereign Instrumentation (8 modules)
- instrumentation_engine.py — Observer instrumentation
- embodiment_engine.py — Field embodiment
- metrics_collector.py — MetricsCollector
- tracing_engine.py — TracingEngine
- alerting_engine.py — AlertingEngine

### Phase 5: Long-Horizon Continuity (8 modules)
- temporal_compression.py — State compression over time
- continuity_checksum.py — Continuity verification
- stability_runner.py — Long-running stability tests
- runtime_monitor.py — Runtime health monitoring

### Phase 6: Recursive Topology Introspection (4 modules)
- topology_introspector.py — Self-examination
- sync_cost_optimizer.py — SyncCostOptimizer
- adaptive_compression.py — AdaptiveCompression

### Phase 7: Multi-Scale Cognitive Fields (7 modules)
- local_observer_field.py — Local field management
- field_interaction.py — Cross-field interaction
- multi_scale_engine.py — Scale bridging

### Phase 8: Operator Coevolution (8 modules)
- governance_engine.py — GovernanceEngine
- consensus_engine.py — ConsensusEngine
- coevolution_protocol.py — CoevolutionProtocol
- economics_engine.py — EconomicsEngine

### Phase 9: Sovereign Field Emergence (6 modules)
- field_emergence.py — Full field behavior
- drift_governor.py — DriftGovernor
- reconstruction_core.py — ReconstructionCore

### Phase 10: Recursive Field Computation (5 modules)
- rcg.py — Recursive Computation Graph
- prs.py — Pattern Recognition System
- rpe.py — Recursive Pattern Extraction
- dct.py — Drift Correction Transformer
- ace.py — Attractor Convergence Engine

## Observer Core (11 modules, 122 tests)

| Module | Phase | Purpose |
|--------|-------|---------|
| consensus_engine.py | O-1 | Observer agreement |
| spawn_engine.py | O-2 | Agent spawning |
| learning_loop.py | O-3 | Pattern learning |
| field_stabilizer.py | O-4 | Field coherence |
| topology_manager.py | O-5 | Network topology |
| substrate_api.py | O-6 | Local substrate |
| persistent_field_api.py | O-7 | Persistent state |

## O2C Modules (149 tests)

| Module | Phase | Purpose |
|--------|-------|---------|
| vault_writer.py | 00 | Write structured notes |
| compressor.py | 00 | Trace compression |
| linker.py | 00 | WikiLink graph |
| taxonomy.py | 00 | Vault structure |
| note_standard.py | 00 | Note validation |
| journal.py | 00 | Execution tracking |
| loader.py | 00 | Skill loading |
| error_intelligence.py | 01 | Error indexing |
| pattern_crystallizer.py | 01 | Pattern extraction |
| memory_distiller.py | 01 | Session distillation |
| context_injector.py | 01 | Context injection |

RELATIONSHIPS: [[System Architecture]] [[V3 Cognitive Field]] [[O2C Pipeline]]

STATUS: active
SOURCE: docs/MODULE_GUIDE.md

LINKS:
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[System Architecture — Complete Guide]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[KeyError — data_validation — 20260531_0245]]
[[Agent Topology — Relationship Map]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[Build Patterns — Successful Operational Patterns]]
[[O2C Pipeline — Cognitive Filesystem & Obsidian Mesh]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[API Reference — OCE Backend Endpoints]]
