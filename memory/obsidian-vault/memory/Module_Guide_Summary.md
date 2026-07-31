# Module Guide Summary

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

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
[[Taxonomy]]
[[Linker]]
[[Compressor]]
[[Vault]]
[[Metrics]]
[[Loader]]
[[Journal]]
[[Memory]]
[[Writing Guide]]
[[System]]
[[Standard]]
[[Skill]]
[[Server]]
[[Patterns]]
[[Ohmsha Guide]]
[[Modules]]
[[Methods Guide]]
[[Interaction]]
[[Cohere]]
[[Cal]]
[[Benchmark Guide]]
[[Action]]
[[Welcome]]
[[Vault Distillation 20260531 0245]]
[[Tradovate Api Discovery 20260531]]
[[Track A Ninjascript Build 20260531]]
[[Track A Build Status]]
[[Track A Build Complete 20260531]]
[[Test Pattern]]
[[Test Note]]
[[Team Roster]]
[[Team Phase01 Status]]
[[Task Flow]]
[[Srra Oph]]
[[Session Testagent 20260531 0245 Full]]
[[Session Testagent 20260531 0245]]
[[Session 20260531 2200]]
[[Self Heal Report]]
[[Sage Audit Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit 20260531 Environment Utilization]]
[[Quantlab Bible]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Progress]]
[[Pm2 Test Note]]
[[Option A Confirmed 20260531]]
[[Operational State 20260531]]
[[Ontology Core Summary]]
[[Oc2 Vault Access Guide]]
[[Oc2 Identity]]
[[Oc2 Gateway Failures]]
[[Obsidian Vault Connection Info]]
[[Observer Core O1 O7]]
[[Master Plan Assessment 20260531]]
[[Live Deployment Status]]
[[Keyerror Data Validation 20260531 0245]]
[[Journal 20260602T005953Z Task Update]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Graph]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Activation Note]]
[[Foundational Principles]]
[[Failure Index Oc2]]
[[Executor Crash 20260531]]
[[Errors And Solutions]]
[[Doctor Prescription]]
[[Dashboard Build Complete]]
[[Daily Runtime 20260531]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Build Progress 20260531]]
[[Build Patterns]]
[[Backtest Phase Status]]
[[Backtest Campaign V3 Results]]
[[Backtest Campaign Status 20260531]]
[[Api Test Note]]
[[Api Reference Summary]]
[[Api Execution Architecture 20260531]]
[[Agent Topology]]
[[Active Strategies Performance]]
[[2026 06 01]]
[[2026 05 31]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 30 Evening]]
[[2026 05 30]]
[[2026 05 21]]
[[2026 05 20]]
[[2026 05 18]]
[[2026 05 17]]
[[Operator Rules]]
[[Module Guide]]
[[Api Reference]]
[[Architecture]]
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
