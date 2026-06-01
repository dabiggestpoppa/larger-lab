# 🟠 PM2 — SRRA-OPH Frontend Plan
## Temporal Playback + Entropy Field Dynamics (Phases 3-4)

**Agent:** PM2
**Frontend:** SRRA-OPH (:3001)
**Depends on:** CC2 completing Phase 1 (layout, theme, state stores, Cytoscape)

---

## PHASE 3 — TEMPORAL PLAYBACK ENGINE

### 3.1 Timeline Core
**Files:**
- `lib/timeline/TimelineEngine.ts` — Master temporal controller
- `lib/timeline/FrameManager.ts` — Frame indexing and state
- `lib/timeline/TemporalClock.ts` — Playback clock
- `stores/timelineStore.ts` — Zustand timeline state

**Frame schema:**
```ts
type RuntimeFrame = {
  frameId: string;
  timestamp: number;
  topologySnapshot: { nodes: NodeState[]; edges: EdgeState[] };
  entropySnapshot: { local: number; cluster: number; global: number };
  repairSnapshot: { active: RepairEvent[]; completed: RepairEvent[] };
  events: TimelineEvent[];
  observerStates: Record<string, ObserverState>;
}
```

### 3.2 Playback Controls
**Files:**
- `components/timeline/PlaybackControls.tsx` — Play/pause/stop/reverse/step
- `components/timeline/SpeedControl.tsx` — 0.25x to 10x speed

### 3.3 Frame State Engine
**Files:**
- `lib/timeline/FrameInterpolator.ts` — Smooth interpolation between frames
- `lib/timeline/FrameCompressor.ts` — Delta compression for storage

### 3.4 Multi-View Sync
**Files:**
- `lib/timeline/TemporalSyncEngine.ts` — Sync topology + entropy + repair + metrics
- `hooks/useTemporalSync.ts` — React hook for frame-locked updates

### 3.5 Event Sequencing
**Files:**
- `lib/events/EventSequencer.ts` — Event ordering and causality
- `lib/events/CausalityTracker.ts` — Cause/effect chain tracking
- `components/timeline/EventMarkers.tsx` — Event type markers on timeline

**Event types:** PERTURBATION, REPAIR_TRIGGER, REPAIR_PROPAGATION, SYNC_COLLAPSE, SYNC_RESTORE, ENTROPY_SPIKE, ROUTING_SHIFT, OBSERVER_FAILURE, ATTRACTOR_FORMATION

### 3.6 Long Horizon Storage
**Files:**
- `lib/storage/FrameCompression.ts` — Compress redundant states
- `lib/storage/TemporalChunking.ts` — Group frames into replay windows
- `lib/storage/ReplayCache.ts` — LRU cache for active replay

### 3.7 Temporal Scrubber
**Files:**
- `components/timeline/TemporalScrubber.tsx` — Draggable scrubber with markers
- `components/timeline/EventDensity.tsx` — Event density visualization

### 3.8 Experiment Replay
**Files:**
- `components/experiments/ExperimentLoader.tsx` — Load experiment sessions
- `components/experiments/SessionComparison.tsx` — Side-by-side comparison
- `components/experiments/ReplayMetadata.tsx` — Experiment metadata display

---

## PHASE 4 — ENTROPY + PERTURBATION FIELD

### 4.1 Entropy Core
**Files:**
- `lib/entropy/EntropyEngine.ts` — Entropy computation
- `lib/entropy/EntropyMetrics.ts` — Observer/cluster/global metrics
- `lib/entropy/FieldStress.ts` — Continuity stress calculation
- `lib/entropy/StabilityIndex.ts` — Stability scoring

### 4.2 Perturbation Engine
**Files:**
- `lib/perturbation/PerturbationInjector.ts` — Controlled chaos injection
- `lib/perturbation/ChaosProfiles.ts` — Predefined chaos profiles
- `lib/perturbation/InjectionScheduler.ts` — Timed injection scheduling

**Perturbation types:** NODE_FAILURE, SYNC_BREAK, ROUTING_CORRUPTION, MEMORY_LOSS, SIGNAL_DELAY, REPAIR_BLOCK, FIELD_DISTORTION, CASCADE_STRESS

### 4.3 Propagation Dynamics
**Files:**
- `lib/perturbation/PropagationSimulator.ts` — Entropy spread simulation
- `components/visualization/Shockwave.tsx` — Perturbation shockwave rendering
- `components/visualization/StressGradient.tsx` — Pressure intensity overlay

### 4.4 Stability Gradients
**Files:**
- `components/visualization/StabilityGradient.tsx` — Stability field overlay
- `lib/stability/CoherenceMap.ts` — Coherence region mapping
- `lib/stability/ResilienceZones.ts` — Fragile/stable zone detection
- `lib/stability/DriftTracker.ts` — Observer drift tracking

### 4.5 Pressure Field Renderer
**Files:**
- `components/visualization/PressureField.tsx` — Pressure field overlay
- `lib/rendering/PressureModes.ts` — THERMAL, VECTOR, GRADIENT, PRESSURE_WAVES

### 4.6 Collapse Detection
**Files:**
- `lib/collapse/CollapseDetector.ts` — Predictive collapse detection
- `lib/collapse/ResonanceTracker.ts` — Synchronization breakdown tracking
- `lib/collapse/CriticalityEngine.ts` — Criticality scoring
- `components/visualization/CollapseIndicator.tsx` — Pre-collapse warning

### 4.7 Repair ↔ Entropy Interaction
**Files:**
- `components/visualization/RepairEntropyInteraction.tsx` — Counterforce visualization
- `lib/repair/RepairEntropyDynamics.ts` — Repair vs entropy interaction logic

### 4.8 Multi-Scale Field
**Files:**
- `components/visualization/MultiScaleField.tsx` — Zoom-aware field rendering
- `hooks/useFieldScale.ts` — Scale-aware data adaptation

### 4.9 Entropy Timeline
**Files:**
- `components/timeline/EntropyTimeline.tsx` — Entropy evolution over time
- `components/timeline/CollapseMarkers.tsx` — Collapse event markers

---

## SUCCESS CONDITIONS

### Phase 3:
✅ Full timeline playback (forward + reverse)
✅ Multi-view synchronization stable
✅ 24hr replay functional
✅ Experiment replay + comparison working
✅ Frame interpolation smooth

### Phase 4:
✅ Entropy fields render with heat/pressure overlays
✅ Perturbation injection creates visible propagation
✅ Collapse prediction visible before failure
✅ Repair waves suppress entropy visibly
✅ Multi-scale zoom works (observer → global)
✅ 72hr entropy replay stable
