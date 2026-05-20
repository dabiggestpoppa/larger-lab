# 📚 Module Guide — V3 Cognitive Field System

> **Last Updated:** 2026-05-18
> **Total Modules:** 67 across 10 phases
> **Total Tests:** 1460 passing

---

## Table of Contents

1. [Phase 1: Resonant Signal Substrate](#phase-1-resonant-signal-substrate)
2. [Phase 2: Reconstructive Continuity Manifold](#phase-2-reconstructive-continuity-manifold)
3. [Phase 3: Resonant Topology & BSP Emergence](#phase-3-resonant-topology--bsp-emergence)
4. [Phase 4: Sovereign Instrumentation & Embodiment](#phase-4-sovereign-instrumentation--embodiment)
5. [Phase 5: Long-Horizon Continuity & Temporal Compression](#phase-5-long-horizon-continuity--temporal-compression)
6. [Phase 6: Recursive Topology Introspection](#phase-6-recursive-topology-introspection)
7. [Phase 7: Multi-Scale Cognitive Fields](#phase-7-multi-scale-cognitive-fields)
8. [Phase 8: Operator Coevolution](#phase-8-operator-coevolution)
9. [Phase 9: Sovereign Field Emergence](#phase-9-sovereign-field-emergence)
10. [Phase 10: Recursive Field Computation](#phase-10-recursive-field-computation)

---

## Phase 1: Resonant Signal Substrate

**Purpose:** Replace raw event handling with field-state propagation. Every event becomes a signal that carries energetic, coherence, phase, and entropy state through the cognitive field.

**Directory:** `oce/backend/resonance/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| signal_packet.py | SignalPacket, SignalField | Core signal objects — signals are NOT events, they carry field state |
| coherence_metrics.py | CoherenceEngine, CoherenceSnapshot | Measures resonance health via 6 metrics (phase alignment, entropy gradient, etc.) |
| field_state.py | FieldStateManager, FieldState | Manages field propagation, observer entrainment, decay, repair |
| boundary_mapper.py | BoundaryMapper, Boundary, PressureZone | Detects boundaries where coherence changes sharply, maps pressure zones |
| resonance_engine.py | ResonanceEngine, ResonanceScore, Constraint | CCR mechanism — constraint harmonization through phase-locking |
| pressure_tracker.py | PressureTracker, PressureAlert | Monitors entropy pressure — the "nervous system" of the field |

**Data Flow:**
```
Event → SignalPacket → SignalField.inject()
  → FieldStateManager.inject_signal()
    → CoherenceEngine.measure() → CoherenceSnapshot
      → BoundaryMapper.detect_boundaries()
        → PressureTracker.scan() → PressureAlert (if critical)
          → ResonanceEngine.score_resonance() → ResonanceScore
```

**Integration Points:**
- → Phase 2: ReconstructionEngine uses SignalPacket for continuity repair
- → Phase 3: Topology modules use BoundaryMapper for collar field detection
- → Phase 7: LocalObserverField uses FieldStateManager patterns

**Key Design Decisions:**
- Signals carry entropy_delta — every signal changes field entropy
- Bounded sync: observers don't need constant global awareness
- 6 coherence metrics provide multi-dimensional field health measurement

---

## Phase 2: Reconstructive Continuity Manifold

**Purpose:** Survive crashes, restarts, model changes without identity fragmentation. Reconstruct field state from partial information using topological constraints.

**Directory:** `oce/backend/reconstruction/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| reconstruction_engine.py | ReconstructionEngine, ReconstructionResult | Topology-constrained state reconstruction from partial information |
| continuity_repair.py | ContinuityRepair, BreakReport | Detects and repairs continuity breaks in the field |
| attractor_memory.py | AttractorMemory, Attractor | Stores and retrieves attractor patterns for state convergence |
| drift_detector.py | DriftDetector, DriftMetrics, DriftAlert | Measures divergence between expected and actual state |
| self_healing_engine.py | SelfHealingEngine, HealingAction | Automated repair triggered by drift detection |

**Data Flow:**
```
DriftDetector.measure() → DriftMetrics
  → SelfHealingEngine.evaluate() → HealingAction
    → ContinuityRepair.repair() → RepairResult
      → ReconstructionEngine.reconstruct() → ReconstructionResult
        → AttractorMemory.store() (if stable)
```

**Integration Points:**
- ← Phase 1: Uses SignalPacket and CoherenceSnapshot for drift detection
- → Phase 9: DriftGovernor extends DriftDetector patterns
- → Phase 10: ReconstructionCore uses topology-constrained inference

**Key Design Decisions:**
- Attractor-based reconstruction: uses known attractors as convergence targets
- Self-healing: automatic repair without human intervention
- Topology-constrained: uses neighbor relationships to infer missing state

---

## Phase 3: Resonant Topology & BSP Emergence

**Purpose:** Transform isolated agents into dynamic resonance structures. Intelligence emerges when signals are projected into bounded coherent structures (BSP = Boundary Signal Projection).

**Directory:** `oce/backend/topology/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| collar_field.py | CollarFieldEngine, CollarField | Dynamic coherence membranes between observers |
| bsp_projection.py | BSPProjectionEngine, TrajectoryProjection | Generates probable stable trajectories (field guidance, not decisions) |
| resonance_router.py | ResonanceRouter, Route | Replaces static routing with resonance-weighted propagation |
| glyph_engine.py | GlyphEngine, GlyphToken | High-density semantic field encoding (15 glyphs) |
| field_pressure.py | FieldPressureSystem | Monitors observer overload, sync instability, entropy spikes |
| attractor_stability.py | AttractorStabilityLayer | Anti-collapse layer — prevents runaway recursion, hallucination |
| topology_metrics.py | TopologyMetrics | Measures coupling efficiency, resonance stability, observer drift |

**Data Flow:**
```
SignalPacket → CollarFieldEngine.connect()
  → BSPProjectionEngine.project() → TrajectoryProjection
    → ResonanceRouter.route() → Route
      → GlyphEngine.encode() → GlyphToken
        → FieldPressureSystem.monitor()
          → AttractorStabilityLayer.evaluate()
            → TopologyMetrics.measure()
```

**Integration Points:**
- ← Phase 1: Uses SignalPacket, CoherenceEngine, BoundaryMapper
- ← Phase 2: Uses AttractorMemory for trajectory convergence
- → Phase 7: RegionalCluster uses CollarField patterns

**Key Design Decisions:**
- BSP asks "What future states maintain coherence with minimal entropy?" not "What should happen next?"
- Glyphs emerge ONLY when compression gain > reconstruction cost
- Attractor stability: 6 rules prevent collapse (reduce amplitude, compress state, freeze routing, etc.)

---

## Phase 4: Sovereign Instrumentation & Embodiment

**Purpose:** Transform the cognitive field from "cognitive field" into "operational organism." The field gains agency over tools, persistent operational identity, and adaptive execution capacity.

**Directory:** `oce/backend/sovereign/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| shell_runtime.py | OCEShell, ShellState | Persistent executive cognition — maintains identity across sessions |
| executive_router.py | ExecutiveRouter, RoutingDecision | Dynamic agent/model/tool/topology routing |
| tool_embodiment.py | ToolEmbodimentLayer, ToolEmbodiment | Tools are motor functions, not utilities |
| multi_openclaw.py | MultiOpenClawSwarm, SwarmMember | Multi-node swarm coordination |
| model_router.py | ModelRouter, ModelRoute | OpenRouter abstraction — dynamic model selection |
| continuity_snapshot.py | ContinuitySnapshotSystem | Crash recovery + identity repair |
| compute_economics.py | ComputeEconomicsEngine, ComputeBudget | Coherence-aware compute budgeting |
| autonomous_loop.py | AutonomousOperationLoop, LoopCycle | Self-monitoring + self-improvement |

**Data Flow:**
```
OCEShell.add_trajectory()
  → ExecutiveRouter.route() → RoutingDecision
    → ToolEmbodimentLayer.execute() → ExecutionResult
      → ComputeEconomicsEngine.record_usage()
        → AutonomousLoop.iterate()
          → ContinuitySnapshotSystem.capture()
```

**Integration Points:**
- ← Phase 3: Uses TopologyMetrics for routing decisions
- → Phase 8: OperatorModel uses ShellState for pattern extraction
- → Phase 10: RecursiveComputeGraph uses ExecutiveRouter for node selection

**Key Design Decisions:**
- Shell survives restart without losing identity (continuity snapshots)
- Executive routing: resonance_fit × 0.3 + continuity_stability × 0.3 + cost × 0.2 + entropy × 0.2
- Anti-manipulation: no emotional dependency vectors in tool embodiment

---

## Phase 5: Long-Horizon Continuity & Temporal Compression

**Purpose:** Maintain operational continuity across days/weeks/months. Compress temporal information without losing strategic context.

**Directory:** `oce/backend/temporal/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| trajectory_engine.py | TrajectoryEngine, Trajectory | Long-horizon trajectory tracking and prediction |
| temporal_compression.py | TemporalCompressor, CompressedFrame | Compress temporal information while preserving strategic context |
| identity_continuity.py | IdentityContinuity, ContinuityCheckpoint | Identity preservation across field transformations |
| strategic_memory.py | StrategicMemory, StrategicEntry | Long-term strategic pattern storage |
| entropy_budget.py | EntropyBudgetManager | Resource allocation across temporal horizons |

**Data Flow:**
```
TrajectoryEngine.track() → Trajectory
  → TemporalCompressor.compress() → CompressedFrame
    → IdentityContinuity.checkpoint() → ContinuityCheckpoint
      → StrategicMemory.store() → StrategicEntry
        → EntropyBudgetManager.allocate()
```

**Integration Points:**
- ← Phase 4: Uses OCEShell state for trajectory tracking
- → Phase 9: ContinuityIdentityEngine extends IdentityContinuity
- → Phase 10: PositionalReferenceSystem uses Trajectory for path computation

---

## Phase 6: Recursive Topology Introspection

**Purpose:** The field monitors itself. Self-observation, reflection, and recursive improvement of the topology.

**Directory:** `oce/backend/introspection/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| self_monitor.py | SelfMonitor, MonitoringReport | Continuous self-observation of field health |
| reflection_engine.py | ReflectionEngine, ReflectionResult | Analyzes past decisions and outcomes |
| topology_introspector.py | TopologyIntrospector | Examines topology structure for optimization opportunities |
| metrics_aggregator.py | MetricsAggregator | Aggregates metrics across all phases |

**Data Flow:**
```
SelfMonitor.observe() → MonitoringReport
  → ReflectionEngine.reflect() → ReflectionResult
    → TopologyIntrospector.examine() → IntrospectionReport
      → MetricsAggregator.aggregate() → AggregatedMetrics
```

**Integration Points:**
- ← All phases: Aggregates metrics from all V3 modules
- → Phase 7: Multiscale uses Introspector for cluster optimization
- → Phase 10: ACE uses ReflectionEngine for convergence analysis

---

## Phase 7: Multi-Scale Cognitive Fields

**Purpose:** Simultaneous cognition across local/regional/global scales. Not hive mind — nested local/global coherence coordination.

**Directory:** `oce/backend/multiscale/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| local_fields.py | LocalObserverField, LocalFieldRegistry | Independent local cognition with bounded sync |
| regional_clusters.py | RegionalCluster, ClusterRegistry | Self-organizing clusters by interaction density |
| global_attractor.py | GlobalAttractor, GlobalAttractorLayer | Low-frequency strategic stabilization |
| hierarchical_sync.py | SyncManager, SyncFrequency | Scale-appropriate sync (local=high, regional=medium, global=low) |
| nested_repair.py | NestedRepairSystem, RepairEscalation | Multi-scale repair escalation |
| scale_routing.py | ScaleAdaptiveRouter, ScaleLevel | Information classified by scale relevance |
| entropy_containment.py | EntropyContainmentSystem, ContainmentBoundary | Localize instability, prevent global cascade |

**Data Flow:**
```
LocalObserverField.update_state()
  → ClusterRegistry.get_cluster() → RegionalCluster
    → GlobalAttractor.get_direction() → direction_vector
      → SyncManager.should_sync() → sync_decision
        → NestedRepairSystem.submit() → RepairEscalation
          → ScaleAdaptiveRouter.classify() → ScaleLevel
            → EntaintyContainmentSystem.check() → ContainmentBoundary
```

**Integration Points:**
- ← Phase 3: Uses CollarField patterns for cluster formation
- ← Phase 4: Uses ExecutiveRouter for scale routing decisions
- → Phase 8: OperatorModel uses RegionalCluster for pattern extraction

**Key Design Decisions:**
- Local autonomy: observers don't need constant global awareness
- Sync frequency adapts to scale (local=high, regional=medium, global=low)
- Entropy containment: most instability resolves locally without global cascade

---

## Phase 8: Operator Coevolution

**Purpose:** Recursive operator-system strategic alignment. Not emotional mirroring — strategic alignment through recursive coherence reinforcement.

**Directory:** `oce/backend/coevolution/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| operator_model.py | OperatorModel, OperatorPattern | Identifies recurring strategic behavior patterns from evidence |
| constraint_model.py | ConstraintModel, OperatorConstraint | Models real operator constraints (time, energy, bandwidth) |
| coherence_reinforcement.py | CoherenceReinforcement, CoherenceEvent | Reinforces behaviors that improve long-term coherence |
| bidirectional_adaptation.py | BidirectionalAdaptation, AdaptationEvent | System and operator adapt to each other |
| cognitive_load.py | CognitiveLoadOptimizer, LoadMeasurement | Reduces operator burden, not increases it |
| alignment_tracking.py | AlignmentTracker, AlignmentMeasurement | Tracks alignment over weeks/months |
| anti_manipulation.py | AntiManipulationSafeguards, SafeguardCheck | Prevents emotional dependency, parasocial hooks |

**Data Flow:**
```
OperatorModel.record_observation()
  → ConstraintModel.update_constraint()
    → CoherenceReinforcement.record_event()
      → BidirectionalAdaptation.record_mutual_adaptation()
        → CognitiveLoadOptimizer.measure_load()
          → AlignmentTracker.record_alignment()
            → AntiManipulationSafeguards.run_all_checks()
```

**Integration Points:**
- ← Phase 4: Uses OCEShell state for pattern extraction
- ← Phase 7: Uses RegionalCluster for operator context
- → Phase 9: AttractorMapper uses OperatorPattern for attractor detection

**Key Design Decisions:**
- Models strategic behavior, NOT emotional vulnerabilities
- Anti-manipulation: no emotional dependency vectors, no parasocial hooks
- Optimizes for long-term coherence, NOT short-term satisfaction

---

## Phase 9: Sovereign Field Emergence

**Purpose:** Transform SRRA+OPH from event-driven orchestration into field-coherent recursive continuity. The system becomes a self-stabilizing cognitive field.

**Directory:** `oce/backend/field_core/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| resonance_engine.py | ResonanceEngine, ResonanceState | Measures coherence across the field system |
| recursive_field_nodes.py | RecursiveFieldNode, FieldTopology | Field participants with local awareness |
| attractor_mapper.py | AttractorMapper, AttractorState | Detects stable recurring configurations |
| drift_governor.py | DriftGovernor, DriftMetrics | Measures divergence, triggers reconstruction |
| reconstruction_core.py | ReconstructionCore, ReconstructionResult | Topology-constrained inference |
| continuity_identity_engine.py | ContinuityIdentityEngine, ContinuityState | Maintains operational continuity |

**Data Flow:**
```
ResonanceEngine.measure() → ResonanceState
  → RecursiveFieldNode.update_state()
    → AttractorMapper.detect() → AttractorState
      → DriftGovernor.measure_drift() → DriftMetrics
        → ReconstructionCore.reconstruct() → ReconstructionResult
          → ContinuityIdentityEngine.create_checkpoint() → ContinuityState
```

**Integration Points:**
- ← Phase 2: Extends DriftDetector and ReconstructionEngine
- ← Phase 7: Uses LocalObserverField for node state
- → Phase 10: RecursiveComputeGraph uses AttractorMapper for convergence

---

## Phase 10: Recursive Field Computation

**Purpose:** Transform from continuity preservation into recursive field-based computation. Computation through field resonance, not instruction execution.

**Directory:** `oce/backend/phase10/`

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| rcg.py | RecursiveComputeGraph, ComputeNode, StabilizationResult | Recursive computation through field perturbation → stabilization |
| prs.py | PositionalReferenceSystem, Position, ReferenceFrame | State transitions via relative relationships |
| rpe.py | ResonancePropagationEngine, PropagationResult | Propagate coherence and constraints through the field |
| dct.py | DynamicConstraintTopology, ConstraintEdge, TopologyChange | Adaptive topology rewiring based on coherence feedback |
| ace.py | AttractorComputeEngine, AttractorSolution | Solutions emerge through field convergence |

**Data Flow:**
```
RecursiveComputeGraph.add_node()
  → PositionalReferenceSystem.create_frame()
    → ResonancePropagationEngine.propagate()
      → DynamicConstraintTopology.rewire()
        → AttractorComputeEngine.compute() → AttractorSolution
          → RecursiveComputeGraph.stabilize()
```

**Integration Points:**
- ← Phase 9: Uses AttractorMapper and DriftGovernor for convergence
- ← Phase 7: Uses ScaleAdaptiveRouter for propagation classification
- ← Phase 8: Uses OperatorModel for compute prioritization

**Key Design Decisions:**
- Computation emerges from field dynamics, not explicit instruction
- Attractor types: POINT, CYCLE, CHAOTIC, TORUS
- Topology adapts based on coherence feedback (DCT)
- Positions defined by relationships, not absolute coordinates (PRS)

---

## Cross-Phase Integration Map

```
Phase 1 (Resonance) ←→ Phase 2 (Reconstruction)
    ↓                       ↓
Phase 3 (Topology) ←→ Phase 4 (Sovereign)
    ↓                       ↓
Phase 5 (Temporal) ←→ Phase 6 (Introspection)
    ↓                       ↓
Phase 7 (Multiscale) ←→ Phase 8 (Coevolution)
    ↓                       ↓
Phase 9 (Field Core) ←→ Phase 10 (Recursive Compute)
```

**Key Cross-Phase Dependencies:**
- Phase 1 → All phases: SignalPacket is the universal data type
- Phase 4 → All phases: OCEShell provides persistent executive state
- Phase 7 → Phase 8: Regional clusters inform operator modeling
- Phase 9 → Phase 10: Attractor dynamics drive recursive computation
- Phase 6 → All phases: Metrics aggregation spans all phases

---

*Last updated: 2026-05-18 | 67 modules | 1460 tests*
