# OBSERVER CORE + OCE UNIFIED — MASTER PLAN

> **Created:** 2026-05-26
> **Status:** Planning — Ready for Task Assignment
> **Source Files:**
>   - `OBSERVER CORE BUILD AFTER FRONT END.txt` (Phases O-0 → O-7)
>   - `oce front end upgrade plan.txt` (Primary Observer + UX Layer)
>   - `FRONT END AND SYSTEM CLARITY FOR BUILD.txt` (Unified Architecture)
>   - `EXTRA CONTEXT AND PLANS FOR FRONT END AND OBSERVERS.txt` (Observer ≠ LLM)

---

## EXECUTIVE SUMMARY

We are NOT rebuilding SRRA. We are **extending the validated Phase 11 substrate** with an **observer-mediated orchestration layer** and a **unified OCE frontend**.

The current SRRA/OPH runtime (Phase 11 tested, 38/38 tests passing) is the **substrate**. Now we add:
1. **Primary Observer** — persistent continuity-aware orchestration interface
2. **Observer Consensus** — distributed task routing intelligence
3. **Spawn Engine** — dynamic cognition deployment with context inheritance
4. **Field Learning** — meta-operational adaptation from traces
5. **Unified OCE** — single interface merging SRRA observatory + operational cockpit
6. **Local Embodiment** — machine-aware bounded execution
7. **Persistent Field** — continuous operational continuity

---

## ARCHITECTURAL DIRECTIVE (from source files)

### The Correct Architecture:
```
USER
 ↓
PRIMARY OBSERVER (continuity anchor, NOT an LLM)
 ↓
OBSERVER FIELD (distributed consensus)
 ↓
SPAWN ORCHESTRATION (temporary cognition workers)
 ↓
EXECUTION SUBSTRATE (bounded, traced)
 ↓
TRACE FEEDBACK → FIELD MEMORY → ADAPTATION
 ↓
CONTINUITY
```

### Critical Distinctions:
- **Observer ≠ Generic LLM** — The observer is a continuity abstraction layer
- **SRRA/OPH = backend runtime substrate** — invisible to users
- **OCE = singular operational frontend** — the only interface users see
- **Spawned agents = temporary cognition workers** — ephemeral, traced, bounded
- **The field is the intelligence** — not any single model or agent

### What We Are NOT Building:
- ❌ Chatbot wrapper
- ❌ Agent swarm
- ❌ Autonomous AI god system
- ❌ Fancy dashboard
- ❌ Two separate frontend apps

---

## CURRENT STATE ASSESSMENT

| Layer | Status | Notes |
|-------|--------|-------|
| Runtime substrate (SRRA/OPH) | ✅ Active | Phase 11 tested, 38/38 pass |
| Observers | ⚠️ Partial | Basic observer runtime exists |
| Entropy engine | ✅ Active | Tested with real data |
| Chaos testing | ✅ Active | 20/20 cycles, 3.0x amp |
| Repair systems | ✅ Active | Validated |
| Replay | ⚠️ Partial | Backend exists, frontend incomplete |
| OCE frontend | ⚠️ Beginning | Separate apps, not unified |
| Observer orchestration | ❌ Not started | This is the new work |
| Persistent primary observer | ❌ Not started | This is the new work |
| Spawn-routing system | ❌ Not started | This is the new work |
| Context inheritance | ❌ Not started | This is the new work |
| Field learning | ❌ Not started | This is the new work |
| Local embodiment | ❌ Not started | This is the new work |
| Persistent field mode | ❌ Not started | This is the new work |

---

## PHASE O-1: PRIMARY OBSERVER CORE

**Goal:** Create persistent continuity-aware interface observer

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-1

### Components to Build:
```
src/observer/
├── PrimaryObserver.ts        # Main orchestration interface
├── ObserverState.ts          # Persistent observer state
├── RuntimeAwareness.ts       # Topology/entropy/repair awareness
├── ContinuityMemory.ts       # Operational continuity memory (NOT chat memory)
├── TaskIntentAnalyzer.ts     # Task classification (domain, complexity, spawn needs)
├── ContextDistiller.ts       # Compress field state for spawned agents
├── EventAwareness.ts         # Runtime event observation
├── ObserverSession.ts        # Session continuity management
└── ObserverLifecycle.ts      # Heartbeat, recovery, restart continuity
```

### Primary Observer Responsibilities:
- Session continuity (persistent interaction memory)
- Runtime awareness (active topology awareness)
- Task analysis (determine task type)
- Context distillation (gather relevant field state)
- Event awareness (observe active runtime)
- Routing prep (prepare orchestration)
- Operational memory (preserve workflow history)
- OCE communication (feed visualization layer)

### Primary Observer MUST NOT:
- ❌ Handle heavy execution
- ❌ Do deep coding tasks
- ❌ Perform autonomous recursion
- ❌ Directly spam tools
- ❌ Perform unrestricted spawning

### Success Criteria:
- ✅ Persistent operational awareness
- ✅ Session continuity preserved
- ✅ Runtime-aware interaction operational
- ✅ Task intent analysis operational
- ✅ Observer memory operational
- ✅ OCE integration operational
- ✅ State persistence operational
- ✅ Event awareness operational

### Tests:
1. Continuity test — 24hr persistent observer session
2. Runtime awareness test — inject topology mutation, entropy spike, observer failure
3. Task analysis test — feed coding, research, orchestration, repair tasks
4. Context distillation test — spawn multiple tasks, verify low-noise context
5. Restart recovery test — crash observer, verify continuity restored
6. OCE integration test — live panels, event sync, runtime updates

---

## PHASE O-2: OBSERVER CONSENSUS + TASK ROUTING

**Goal:** Distributed orchestration intelligence — observers collaboratively determine how tasks are handled

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-2

### Components to Build:
```
src/consensus/
├── ObserverConsensus.ts       # Distributed observer decision-making
├── TaskClassifier.ts         # Task type classification
├── RoutingConsensus.ts       # Best orchestration path selection
├── ComplexityScorer.ts       # Operational complexity estimation
├── SpawnPlanner.ts           # Task orchestration blueprint generation
├── ModelSelector.ts          # Best cognition provider selection
├── CapabilityMatcher.ts      # Required operational capabilities
├── ConsensusMemory.ts        # Orchestration outcome history
├── ObserverSpecialization.ts # Observer specialization through operational history
└── ConsensusReplay.ts        # Replay observer orchestration decisions
```

### Key Principle:
No single observer should dominate orchestration. Consensus emerges from topology state, observer specialization, prior outcomes, entropy conditions, and runtime awareness.

### Success Criteria:
- ✅ Observer consensus operational
- ✅ Task classification operational
- ✅ Distributed routing operational
- ✅ Model selection operational
- ✅ Spawn planning operational
- ✅ Observer specialization operational
- ✅ Routing replay operational
- ✅ Consensus visualization operational

---

## PHASE O-3: SPAWN ENGINE + CONTEXT INHERITANCE

**Goal:** Dynamic task-agent spawning with field continuity transfer

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-3

### Components to Build:
```
src/spawn/
├── AgentSpawner.ts           # Main orchestration execution layer
├── SpawnBlueprint.ts         # Formal orchestration schema before spawning
├── ContextInjector.ts        # Inject field continuity into spawned agents
├── OpenRouterGateway.ts      # Unified cognition-provider layer
├── AgentLifecycle.ts         # Init/execute/monitor/terminate/cleanup
├── ExecutionBoundary.ts      # Prevent orchestration chaos
├── MultiAgentCoordinator.ts  # Coordinate multiple spawned agents
├── TraceFeedback.ts          # Feed operational traces back to SRRA
├── SpawnReplay.ts            # Replay spawned agent behavior
└── SpawnRegistry.ts          # Global active-agent awareness
```

### Key Principle:
Agents should NEVER start stateless. Every spawned agent inherits operational continuity, topology awareness, task history, orchestration state, runtime constraints, and field awareness.

### Success Criteria:
- ✅ Dynamic spawning operational
- ✅ OpenRouter integration operational
- ✅ Context inheritance operational
- ✅ Lifecycle tracking operational
- ✅ Execution boundaries operational
- ✅ Multi-agent orchestration operational
- ✅ Trace feedback operational
- ✅ Spawn replay operational

---

## PHASE O-4: OPERATIONAL TRACE + FIELD LEARNING

**Goal:** Meta-orchestration memory — system learns how orchestration behaves

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-4

### Components to Build:
```
src/learning/
├── TraceCollector.ts          # Capture all operational orchestration traces
├── OperationalReplay.ts       # Replay full orchestration history
├── WorkflowDistiller.ts       # Extract stable orchestration patterns
├── RoutingLearning.ts         # Improve future routing from outcomes
├── FailureAnalyzer.ts         # Study why orchestration failed
├── TopologyLearning.ts        # Understand how orchestration affects topology
├── ObserverEvolution.ts       # Observers gradually specialize
├── PatternMemory.ts           # Store stable orchestration knowledge
├── WorkflowMemory.ts          # Long-horizon operational continuity
├── OperationalScoring.ts      # Quantify orchestration quality
└── AdaptationEngine.ts        # Apply controlled orchestration adaptation
```

### Key Principle:
The system learns **how orchestration behaves**, NOT how reality works. This is orchestration intelligence, NOT foundation model training.

### Success Criteria:
- ✅ Trace collection operational
- ✅ Operational replay operational
- ✅ Routing adaptation operational
- ✅ Failure pattern learning operational
- ✅ Observer specialization evolution operational
- ✅ Topology learning operational
- ✅ Workflow memory operational
- ✅ Adaptive orchestration operational

---

## PHASE O-5: OCE UNIFIED OPERATIONAL OBSERVATORY

**Goal:** Single unified OCE interface merging SRRA observatory + operational cockpit

**Source:** `FRONT END AND SYSTEM CLARITY FOR BUILD.txt` + `oce front end upgrade plan.txt`

### Critical Architecture Correction:
**Current state:** Two separate apps — OCE (:3000) and SRRA-OPH (:3001)
**Target state:** ONE unified OCE frontend with SRRA observatory as integrated panels

### OCE Layer Structure:
```
OCE FRONTEND (singular interface)
│
├── Layer 1 — Simple User Layer (DOMINATES VISUALLY)
│   ├── Chat Panel (Primary Observer interface)
│   ├── Task Workspace
│   ├── Execution Feed
│   ├── Artifacts/Results
│   ├── Live Progress
│   └── Replay Summaries
│
├── Layer 2 — Observational Layer (HIDDEN BY DEFAULT)
│   ├── Topology Observatory (SRRA-OPH integrated)
│   ├── Entropy Field View
│   ├── Repair Cascade Viewer
│   ├── Attractor Basin View
│   ├── Temporal Playback System
│   └── Experiment Session Viewer
│
└── Layer 3 — Orchestration Layer (NEW — Phase O-5 additions)
    ├── Observer Status Panel
    ├── Consensus View
    ├── Spawn Monitor
    ├── Agent Lifecycle Panel
    ├── Context Injection View
    ├── Execution Boundary View
    ├── Multi-Agent Flow Graph
    ├── Operational Replay
    ├── Routing Learning Map
    ├── Failure Analysis Panel
    ├── Observer Evolution Map
    └── Adaptation Monitor
```

### New OCE Components to Build:
```
oce/frontend/components/
├── observer/
│   ├── ObserverConsole.tsx       # Primary Observer chat interface
│   ├── ObserverStatus.tsx        # Observer alive state + health
│   ├── ContinuityPanel.tsx       # Continuity state display
│   ├── RuntimeSummary.tsx        # Current runtime awareness
│   ├── TaskFeed.tsx              # Active tasks from observer
│   └── ObserverHealthPanel.tsx   # Observer health metrics
├── consensus/
│   ├── ConsensusPanel.tsx        # Observer consensus flow
│   ├── RoutingMap.tsx            # Orchestration routing visualization
│   ├── SpawnBlueprintView.tsx    # Spawn plan display
│   ├── ObserverSpecializationMap.tsx
│   ├── ConsensusReplayPanel.tsx
│   └── CapabilityInspector.tsx
├── spawn/
│   ├── SpawnMonitor.tsx          # Active spawned agents
│   ├── AgentLifecyclePanel.tsx   # Agent lifecycle states
│   ├── ContextInjectionView.tsx  # What context was injected
│   ├── ExecutionBoundaryView.tsx # Execution boundaries
│   ├── MultiAgentFlowGraph.tsx   # Multi-agent coordination
│   ├── SpawnReplayPanel.tsx      # Spawn decision replay
│   └── RuntimeLoadPanel.tsx      # Runtime load from spawning
├── learning/
│   ├── OperationalReplay.tsx     # Orchestration history replay
│   ├── WorkflowEvolution.tsx     # Workflow pattern evolution
│   ├── RoutingLearningMap.tsx    # Routing improvement over time
│   ├── FailureAnalysisPanel.tsx  # Failure analysis display
│   ├── TopologyEvolutionView.tsx # Topology learning visualization
│   ├── ObserverEvolutionMap.tsx  # Observer specialization evolution
│   ├── PatternMemoryView.tsx     # Stable orchestration patterns
│   └── AdaptationMonitor.tsx     # Adaptation tracking
└── persistence/
    ├── PersistentFieldView.tsx   # Persistent field state
    ├── RuntimeHeartbeatPanel.tsx # Field continuity pulse
    ├── DormantStateMonitor.tsx   # Dormant/active state transitions
    ├── ObserverPersistenceView.tsx
    ├── DriftAnalysisPanel.tsx    # Operational drift detection
    ├── LongHorizonTimeline.tsx   # Long-horizon continuity
    ├── AutonomousRepairView.tsx  # Bounded self-stabilization
    └── RecoveryContinuityPanel.tsx
```

### OCE Design Rules (from source files):
1. **Dark environment** — Deep matte black/charcoal, low-glow, minimal neon accents
2. **NO corporate UI** — No rounded cards, bubbly UI, oversized spacing, SaaS aesthetic
3. **Information density** — Maximize relational visibility, temporal understanding, topology comprehension
4. **Spatial continuity** — Everything feels spatially connected, graphs feel alive
5. **Time is first-class** — All visual systems support replay, temporal scrub, continuity drift analysis
6. **Chat is central** — The chat interface is the primary continuity surface, NOT an add-on
7. **Two layers** — Simple user layer dominates; observational layer is hidden/optional
8. **Calm, coherent, persistent** — The observer should feel stable, not hyperactive

### Success Criteria:
- ✅ Unified OCE operational (single app, not two)
- ✅ Live topology rendering operational
- ✅ Observer visualization operational
- ✅ Runtime orchestration visualization operational
- ✅ Operational replay operational
- ✅ Entropy visualization operational
- ✅ Spawn monitoring operational
- ✅ Workflow continuity visualization operational
- ✅ Real-time event synchronization operational

---

## PHASE O-6: LOCAL EXECUTION SUBSTRATE

**Goal:** Machine-aware bounded execution — filesystem, terminal, process, app awareness

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-6

### Components to Build:
```
src/substrate/
├── LocalRuntime.ts            # Central local execution substrate
├── FilesystemAwareness.ts     # Structured machine memory awareness
├── TerminalOrchestrator.ts    # All terminal execution management
├── ProcessObserver.ts         # Real-time process awareness
├── ApplicationBridge.ts       # Controlled application interaction
├── EnvironmentModel.ts        # Live machine-state awareness
├── RuntimeInspector.ts        # Live operational conditions inspection
├── PermissionLayer.ts         # Strict operational boundaries
├── ExecutionSandbox.ts        # Safe operational execution zones
├── MachineStateGraph.ts       # Machine itself as topology
└── RecoveryController.ts      # Runtime recovery and stabilization
```

### Key Principle:
The system must become **machine-aware**, NOT **machine-unrestricted**. Bounded embodiment is mandatory.

### Success Criteria:
- ✅ Local runtime operational
- ✅ Filesystem awareness operational
- ✅ Terminal orchestration operational
- ✅ Process awareness operational
- ✅ Application interaction operational
- ✅ Runtime environment modeling operational
- ✅ Bounded execution enforcement operational
- ✅ Local continuity operational
- ✅ Observer-machine synchronization operational

---

## PHASE O-7: PERSISTENT FIELD MODE

**Goal:** Continuous operational continuity — system remains aware even without active tasks

**Source:** `OBSERVER CORE BUILD AFTER FRONT END.txt` — Phase O-7

### Components to Build:
```
src/persistence/
├── PersistentRuntime.ts       # Always-on orchestration substrate
├── ObserverPersistence.ts     # Core observers never lose continuity
├── PassiveAwareness.ts        # Background environmental awareness
├── EnvironmentalMonitor.ts    # Machine + workflow ecosystem observation
├── ContinuityPreserver.ts     # Long-horizon operational continuity
├── DormantStateManager.ts     # Active vs dormant orchestration states
├── AutonomousRepair.ts        # Bounded self-stabilization
├── RuntimeHeartbeat.ts        # Field continuity pulse
├── PersistentScheduler.ts     # Background operational tasks
├── RecoveryPersistence.ts     # Runtime continuity during failure
├── LongHorizonMemory.ts       # Persistent operational identity
└── OperationalDriftDetector.ts # Slow degradation pattern detection
```

### Key Principle:
The system should be **continuously aware**, NOT **continuously acting**. Most time should be spent in low-energy observational state. Acts only when required, when triggered, when bounded.

### Success Criteria:
- ✅ Persistent runtime operational
- ✅ Observer persistence operational
- ✅ Passive environmental awareness operational
- ✅ Autonomous repair stabilization operational
- ✅ Long-horizon continuity operational
- ✅ Persistent topology operational
- ✅ Dormant-active orchestration operational
- ✅ Recovery continuity operational
- ✅ Continuous field state operational

---

## BUILD ORDER (MANDATORY SEQUENCE)

From the source files — **ALWAYS build in this order:**

1. **Stability** — Foundation must be rock solid
2. **Visibility** — Visualize before automating
3. **Replay** — Log everything, replay everything
4. **Boundaries** — Enforce limits before adding capability
5. **Persistence** — Make it survive restarts
6. **Adaptation** — Learn from traces
7. **Automation** — Only automate what's proven stable

**NEVER skip:** replay, logging, entropy tracking, boundaries, topology visibility, recovery paths.

---

## DEVELOPMENT RULES (from source files)

1. **OBSERVE BEFORE AUTOMATING** — Visualize, replay, monitor, understand. Then automate.
2. **TEST LONGER THAN YOU THINK** — Most failures appear after 24hr, 72hr, during idle, during recovery, during drift accumulation.
3. **BUILD FOR RECOVERY** — Assume observers crash, models fail, runtimes hang, memory corrupts, topology drifts.
4. **PREVENT ORCHESTRATION STORMS** — Watch for recursive spawning, repair loops, observer deadlocks, replay saturation, event floods. Always implement rate limits and execution caps.
5. **DO NOT OVER-CENTRALIZE** — The primary observer coordinates, stabilizes, relays continuity. It should NOT become a monolithic god-object.
6. **TOPOLOGY IS A REAL SIGNAL** — Topology changes reveal overload zones, orchestration bottlenecks, repair hotspots, observer isolation, entropy propagation.
7. **MEMORY SHOULD BE STRUCTURED** — Avoid massive prompt stuffing. Use vector memory, graph memory, replay chains, workflow lineage, compressed continuity packets.

---

## KEY METRICS (NOT vanity metrics)

Track these, NOT number of agents or model count:

| Metric | Meaning |
|--------|---------|
| continuity stability | system coherence |
| entropy pressure | orchestration health |
| replay completeness | explainability |
| recovery success rate | resilience |
| topology stability | structural integrity |
| observer synchronization | coordination quality |
| orchestration latency | operational efficiency |
| spawn success rate | runtime reliability |

---

## ERROR HANDLING MASTER GUIDE

| Failure | Symptoms | Response |
|---------|----------|----------|
| Observer failure | missing consensus, routing instability, continuity gaps | restart observer, restore snapshot, replay missed traces, resync topology |
| Spawn failure | failed model response, execution timeout, provider crash | retry once, fallback model, restore orchestration state, record failure trace |
| Entropy spike | event floods, CPU spikes, orchestration instability, topology fragmentation | pause spawning, reduce active observers, enter stabilization mode, increase replay logging |
| Topology drift | isolated nodes, replay inconsistencies, broken routing chains | reconstruct graph, resync runtime state, replay recent topology mutations |
| Memory fragmentation | continuity gaps, lost workflow lineage, inconsistent orchestration context | restore snapshots, compress replay chains, rebuild continuity packets |
| Repair loop cascade | repair agents spawning repeatedly, escalating orchestration, constant recovery cycles | freeze repair layer, enter manual review mode, rollback recent mutations |
| UI desync | stale topology, missing events, replay mismatch | rebuild event stream, resync websocket state, reload topology snapshot |

---

## IMPLEMENTATION PRIORITY

### DO NOW (Phases O-1 through O-5):
These are the immediate next steps, in order:
1. O-1: Primary Observer Core
2. O-2: Observer Consensus + Task Routing
3. O-3: Spawn Engine + Context Inheritance
4. O-4: Operational Trace + Field Learning
5. O-5: OCE Unified Operational Observatory

### DO LATER (Phases O-6, O-7):
These require O-1 through O-5 to be stable first:
6. O-6: Local Execution Substrate
7. O-7: Persistent Field Mode

### DELAY (Research Horizon):
- Full predictive cognition (Phase 7 from FRONT END BUILD)
- Autonomous topology mutation
- Self-modifying observers
- Recursive spawning swarms
- Multi-environment federation (Phase 8)
- Planetary-scale substrates (Phase 9)

---

## FILES REFERENCE

| File | Key Content |
|------|-------------|
| `OBSERVER CORE BUILD AFTER FRONT END.txt` | Phases O-0 → O-7, build order, development rules, error handling, metrics |
| `oce front end upgrade plan.txt` | Primary Observer UX, two-layer UI, user flow, chat-centric design |
| `FRONT END AND SYSTEM CLARITY FOR BUILD.txt` | Unified architecture (ONE system), OCE role, SRRA role, phase integration |
| `EXTRA CONTEXT AND PLANS FOR FRONT END AND OBSERVERS.txt` | Observer ≠ LLM, corrected architecture, OpenRouter as modular cognition |
