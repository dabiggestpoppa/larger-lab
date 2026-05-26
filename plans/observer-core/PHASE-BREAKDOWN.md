# OBSERVER CORE — PHASE-BY-PHASE TASK BREAKDOWN

> **Created:** 2026-05-26
> **Status:** Planning — Ready for Task Assignment

---

## PHASE O-1: PRIMARY OBSERVER CORE

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | PrimaryObserver | `observer/PrimaryObserver.ts` → `core/observer/primary_observer.py` | Main orchestration interface. Receives user input, analyzes intent, gathers runtime state, communicates with observer field, prepares orchestration requests, maintains continuity state |
| 2 | ObserverState | `observer/ObserverState.ts` → `core/observer/observer_state.py` | Persistent observer state: active_task, session_context, runtime_state, observer_health, continuity_score, active_agents, entropy_state, repair_state |
| 3 | RuntimeAwareness | `observer/RuntimeAwareness.ts` → `core/observer/runtime_awareness.py` | Maintains awareness of topology, active observers, entropy, repair state, spawned agents, execution systems. Inputs: event_bus, topology_state, observer_registry, runtime_metrics, entropy_metrics |
| 4 | ContinuityMemory | `observer/ContinuityMemory.ts` → `core/observer/continuity_memory.py` | Operational continuity memory (NOT chat memory). Tracks: workflow evolution, prior orchestration, successful/failed routing, active operational goals, user/system continuity. Storage: JSON + lightweight vector |
| 5 | TaskIntentAnalyzer | `observer/TaskIntentAnalyzer.ts` → `core/observer/task_intent_analyzer.py` | Classifies task domain, complexity, execution requirements, orchestration needs. Output: {domain, complexity, requires_spawn, requires_repo_access, requires_runtime_context} |
| 6 | ContextDistiller | `observer/ContextDistiller.ts` → `core/observer/context_distiller.py` | Compresses relevant field state for spawned agents. Inputs: topology, active tasks, runtime state, prior workflows, entropy state, user objective. Output: structured orchestration context (NOT massive prompt dumping) |
| 7 | EventAwareness | `observer/EventAwareness.ts` → `core/observer/event_awareness.py` | Observes runtime events: TASK_STARTED, TASK_FAILED, OBSERVER_SPAWNED, ENTROPY_SPIKE, REPAIR_TRIGGERED, ROUTING_UPDATED |
| 8 | ObserverSession | `observer/ObserverSession.ts` → `core/observer/observer_session.py` | Session continuity management |
| 9 | ObserverLifecycle | `observer/ObserverLifecycle.ts` → `core/observer/observer_lifecycle.py` | Heartbeat, healthcheck, recovery, state persistence, restart continuity |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | ChatPanel | `components/chat/ChatPanel.tsx` | Enhanced Primary Observer chat interface (replaces basic chat) |
| 2 | ExecutionFeed | `components/chat/ExecutionFeed.tsx` | Live execution visibility in chat |
| 3 | ReplaySummary | `components/chat/ReplaySummary.tsx` | Replay summaries in chat |
| 4 | ArtifactViewer | `components/chat/ArtifactViewer.tsx` | Artifacts/results panel |
| 5 | ObserverConsole | `components/observer/ObserverConsole.tsx` | Primary Observer interface panel |
| 6 | ObserverStatus | `components/observer/ObserverStatus.tsx` | Observer alive state + health |
| 7 | ContinuityPanel | `components/observer/ContinuityPanel.tsx` | Continuity state display |
| 8 | RuntimeSummary | `components/observer/RuntimeSummary.tsx` | Current runtime awareness display |
| 9 | ObserverHealthPanel | `components/observer/ObserverHealthPanel.tsx` | Observer health metrics |
| 10 | observerStore | `stores/observerStore.ts` | Zustand store for observer state |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Continuity test | 24hr persistent observer session |
| 2 | Runtime awareness test | Inject topology mutation, entropy spike, observer failure |
| 3 | Task analysis test | Feed coding, research, orchestration, repair tasks |
| 4 | Context distillation test | Spawn multiple tasks, verify low-noise context |
| 5 | Restart recovery test | Crash observer, verify continuity restored |
| 6 | OCE integration test | Live panels, event sync, runtime updates |

---

## PHASE O-2: OBSERVER CONSENSUS + TASK ROUTING

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | ObserverConsensus | `consensus/ObserverConsensus.py` | Coordinate distributed observer decision-making. Gather evaluations, compare routing proposals, resolve conflicts, calculate confidence, finalize orchestration blueprint |
| 2 | TaskClassifier | `consensus/TaskClassifier.py` | Determine task type: CODING, RESEARCH, ARCHITECTURE, REPAIR, DEBUGGING, ORCHESTRATION, VISUALIZATION, AUTOMATION, SYSTEM_ANALYSIS |
| 3 | RoutingConsensus | `consensus/RoutingConsensus.py` | Determine best orchestration path. Factors: prior success rate, runtime load, entropy conditions, topology proximity, specialization score |
| 4 | ComplexityScorer | `consensus/ComplexityScorer.py` | Estimate operational complexity: LOW, MEDIUM, HIGH, CRITICAL. Factors: execution depth, context size, tool usage, runtime mutation risk, orchestration breadth |
| 5 | SpawnPlanner | `consensus/SpawnPlanner.py` | Generate task orchestration blueprint before spawning. Output: {spawn_required, spawn_count, recommended_model, tool_scope, context_scope, execution_constraints} |
| 6 | ModelSelector | `consensus/ModelSelector.py` | Choose best cognition provider. Factors: latency, complexity, prior success, context size, operational cost. Initial: Qwen-Coder (coding), DeepSeek (reasoning), Local (fast classification), DSPy (structured) |
| 7 | CapabilityMatcher | `consensus/CapabilityMatcher.py` | Determine required capabilities: REPO_ACCESS, TERMINAL, WEB_SEARCH, MEMORY_ACCESS, GRAPH_ANALYSIS, VISUALIZATION, RUNTIME_INSPECTION |
| 8 | ConsensusMemory | `consensus/ConsensusMemory.py` | Store orchestration outcome history: successful routing, failed routing, entropy-producing workflows, stable patterns, observer confidence trends |
| 9 | ObserverSpecialization | `consensus/ObserverSpecialization.py` | Allow observers to gradually specialize through operational history (NOT hardcoded personalities) |
| 10 | ConsensusReplay | `consensus/ConsensusReplay.py` | Replay observer orchestration decisions: why routes chosen, why model selected, why capabilities assigned |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | ConsensusPanel | `components/consensus/ConsensusPanel.tsx` | Observer consensus flow visualization |
| 2 | RoutingMap | `components/consensus/RoutingMap.tsx` | Orchestration routing visualization |
| 3 | SpawnBlueprintView | `components/consensus/SpawnBlueprintView.tsx` | Spawn plan display |
| 4 | ObserverSpecializationMap | `components/consensus/ObserverSpecializationMap.tsx` |
| 5 | ConsensusReplayPanel | `components/consensus/ConsensusReplayPanel.tsx` |
| 6 | CapabilityInspector | `components/consensus/CapabilityInspector.tsx` |
| 7 | consensusStore | `stores/consensusStore.ts` | Zustand store for consensus state |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Task classification test | Feed coding, debugging, orchestration, visualization, repair tasks |
| 2 | Routing stability test | 100 repeated orchestration requests |
| 3 | Model selection test | Large coding, lightweight, research tasks |
| 4 | Entropy routing test | Overloaded runtime, unstable topology, failing observers |
| 5 | Consensus replay test | Replay orchestration history |
| 6 | Specialization test | Extended orchestration workloads |
| 7 | Spawn planning test | Bounded execution scopes, stable spawn plans |

---

## PHASE O-3: SPAWN ENGINE + CONTEXT INHERITANCE

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | AgentSpawner | `spawn/agent_spawner.py` | Main orchestration execution layer. spawn_agent(), terminate_agent(), pause_agent(), resume_agent(), monitor_agent() |
| 2 | SpawnBlueprint | `spawn/spawn_blueprint.py` | Formal orchestration schema before spawning. Deterministic structure, bounded scope, capability restrictions, continuity inheritance flags |
| 3 | ContextInjector | `spawn/context_injector.py` | **THE CORE BREAKTHROUGH LAYER.** Injects field continuity intelligence into spawned agents. Injected: topology state, active runtime state, user continuity, prior orchestration history, entropy state, repair state, observer notes. NOT massive prompt dumping. |
| 4 | OpenRouterGateway | `spawn/openrouter_gateway.py` | Unified cognition-provider layer. Route to models, manage provider configs, manage retries, normalize responses, track performance, manage token usage |
| 5 | AgentLifecycle | `spawn/agent_lifecycle.py` | Manage initialization, execution, monitoring, termination, cleanup, replay registration. States: INITIALIZING, ACTIVE, WAITING, FAILED, RECOVERING, TERMINATED |
| 6 | ExecutionBoundary | `spawn/execution_boundary.py` | Prevent orchestration chaos. Limits: filesystem scope, terminal scope, runtime duration, API access, memory access, process permissions |
| 7 | MultiAgentCoordinator | `spawn/multi_agent_coordinator.py` | Coordinate multiple spawned agents. Initial: sequential tasks, cooperative execution, delegated subtasks. NOT massive autonomous swarms yet. |
| 8 | TraceFeedback | `spawn/trace_feedback.py` | Feed operational traces back into SRRA field memory. Track: execution success, failure causes, routing quality, orchestration efficiency, topology effects, repair outcomes |
| 9 | SpawnReplay | `spawn/spawn_replay.py` | Replay spawned agent behavior, orchestration decisions, execution flow, runtime mutations |
| 10 | SpawnRegistry | `spawn/spawn_registry.py` | Maintain global active-agent awareness. Track: active agents, model assignments, runtime load, execution scopes, lifecycle states, orchestration relationships |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | SpawnMonitor | `components/spawn/SpawnMonitor.tsx` | Active spawned agents display |
| 2 | AgentLifecyclePanel | `components/spawn/AgentLifecyclePanel.tsx` | Agent lifecycle states |
| 3 | ContextInjectionView | `components/spawn/ContextInjectionView.tsx` | What context was injected |
| 4 | ExecutionBoundaryView | `components/spawn/ExecutionBoundaryView.tsx` | Execution boundaries display |
| 5 | MultiAgentFlowGraph | `components/spawn/MultiAgentFlowGraph.tsx` | Multi-agent coordination graph |
| 6 | SpawnReplayPanel | `components/spawn/SpawnReplayPanel.tsx` | Spawn decision replay |
| 7 | RuntimeLoadPanel | `components/spawn/RuntimeLoadPanel.tsx` | Runtime load from spawning |
| 8 | spawnStore | `stores/spawnStore.ts` | Zustand store for spawn state |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Basic spawn test | Spawn coding, research, orchestration agents |
| 2 | Context inheritance test | Verify topology awareness, prior workflow awareness, runtime awareness |
| 3 | Execution boundary test | Attempt out-of-scope file access, restricted terminal execution |
| 4 | Multi-agent coordination test | 3-agent cooperative workflow |
| 5 | Lifecycle stability test | 24hr spawn lifecycle test |
| 6 | Trace feedback test | Routing metrics update, orchestration memory updates |
| 7 | Failover test | Model timeout, provider failure, execution crash |
| 8 | Spawn storm test | High-frequency task bursts |

---

## PHASE O-4: OPERATIONAL TRACE + FIELD LEARNING

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | TraceCollector | `learning/trace_collector.py` | Capture all operational orchestration traces. Types: TASK_TRACE, ROUTING_TRACE, FAILURE_TRACE, ENTROPY_TRACE, SPAWN_TRACE, TOPOLOGY_TRACE, REPAIR_TRACE, CONSENSUS_TRACE |
| 2 | OperationalReplay | `learning/operational_replay.py` | Replay full orchestration history: task evolution, observer decisions, routing chains, spawned agents, topology changes, entropy spikes, repair events |
| 3 | WorkflowDistiller | `learning/workflow_distiller.py` | Extract stable orchestration patterns from traces. Detect: successful routing chains, stable agent combinations, efficient model selection, recurring repair paths, topology bottlenecks |
| 4 | RoutingLearning | `learning/routing_learning.py` | Improve future orchestration routing through operational outcomes. Learns: which models succeed, which routes fail, which observers perform best, which workflows destabilize topology. Adapts slowly and conservatively. |
| 5 | FailureAnalyzer | `learning/failure_analyzer.py` | Study why orchestration failed. Types: routing failure, entropy collapse, topology instability, repair saturation, context fragmentation |
| 6 | TopologyLearning | `learning/topology_learning.py` | Understand how orchestration affects field topology. Track: observer interaction density, routing clusters, entropy zones, bottleneck nodes, stable orchestration paths |
| 7 | ObserverEvolution | `learning/observer_evolution.py` | Allow observers to gradually specialize through operational weighting (NOT free-form self-rewriting) |
| 8 | PatternMemory | `learning/pattern_memory.py` | Store stable orchestration knowledge. Types: successful workflows, stable routing paths, repair strategies, topology stabilization patterns, entropy mitigation patterns |
| 9 | WorkflowMemory | `learning/workflow_memory.py` | Track long-horizon operational continuity. Stores: user workflows, project evolution, orchestration chains, repair history, topology evolution |
| 10 | OperationalScoring | `learning/operational_scoring.py` | Quantify orchestration quality. Scores: routing score, entropy score, repair score, continuity score, topology score |
| 11 | AdaptationEngine | `learning/adaptation_engine.py` | Apply controlled orchestration adaptation. Allowed: routing weighting, model preferences, observer confidence, topology heuristics. Forbidden: autonomous code rewriting, unrestricted observer mutation, recursive topology rewriting |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | OperationalReplay | `components/learning/OperationalReplay.tsx` | Orchestration history replay |
| 2 | WorkflowEvolution | `components/learning/WorkflowEvolution.tsx` | Workflow pattern evolution |
| 3 | RoutingLearningMap | `components/learning/RoutingLearningMap.tsx` | Routing improvement over time |
| 4 | FailureAnalysisPanel | `components/learning/FailureAnalysisPanel.tsx` | Failure analysis display |
| 5 | TopologyEvolutionView | `components/learning/TopologyEvolutionView.tsx` | Topology learning visualization |
| 6 | ObserverEvolutionMap | `components/learning/ObserverEvolutionMap.tsx` | Observer specialization evolution |
| 7 | PatternMemoryView | `components/learning/PatternMemoryView.tsx` | Stable orchestration patterns |
| 8 | AdaptationMonitor | `components/learning/AdaptationMonitor.tsx` | Adaptation tracking |
| 9 | learningStore | `stores/learningStore.ts` | Zustand store for learning state |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Trace integrity test | 100 orchestration workflows, all traces captured |
| 2 | Replay reconstruction test | Replay task chains, failures, routing evolution |
| 3 | Routing learning test | Repeated task families, routing quality improves |
| 4 | Failure analysis test | Inject broken models, entropy overload, routing collapse |
| 5 | Topology learning test | Extended orchestration workloads, stable patterns emerge |
| 6 | Observer evolution test | Long-horizon sessions, specialization improves performance |
| 7 | Adaptation stability test | Gradual routing adaptation, no orchestration destabilization |
| 8 | Long-horizon memory test | Restart system repeatedly, continuity preserved |

---

## PHASE O-5: OCE UNIFIED OPERATIONAL OBSERVATORY

**This is primarily a frontend integration phase.**

### Tasks

| # | Task | Description |
|---|------|-------------|
| 1 | Merge state stores | Move topologyStore, timelineStore, entropyStore, repairStore, continuityStore from SRRA-OPH to OCE |
| 2 | Move visualization components | Move all topology/, entropy/, repair/, timeline/ components from SRRA-OPH to OCE |
| 3 | Create Layer System | Build LayerSwitcher, modify layout.tsx for three layers, implement panel expand/collapse |
| 4 | Update navigation | Replace separate app navigation with in-app layer/panel navigation |
| 5 | Unify WebSocket | Merge LiveDataProvider with SRRA-OPH's WebSocket connections |
| 6 | Theme unification | Switch OCE from light to dark observatory theme, consistent color language |
| 7 | Build new observer components | ObserverConsole, ObserverStatus, ContinuityPanel, RuntimeSummary, ObserverHealthPanel |
| 8 | Build new consensus components | ConsensusPanel, RoutingMap, SpawnBlueprintView, ConsensusReplayPanel |
| 9 | Build new spawn components | SpawnMonitor, AgentLifecyclePanel, ContextInjectionView, MultiAgentFlowGraph |
| 10 | Build new learning components | OperationalReplay, WorkflowEvolution, RoutingLearningMap, FailureAnalysisPanel |
| 11 | Build new persistence components | PersistentFieldView, RuntimeHeartbeatPanel, DormantStateMonitor, DriftAnalysisPanel |
| 12 | Performance validation | 60fps idle, 30fps under load, no memory leaks |

---

## PHASE O-6: LOCAL EXECUTION SUBSTRATE

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | LocalRuntime | `substrate/local_runtime.py` | Central local execution substrate. execute_task(), inspect_runtime(), track_environment(), manage_execution(), sync_state() |
| 2 | FilesystemAwareness | `substrate/filesystem_awareness.py` | Structured machine memory awareness. Tracks: repositories, active projects, workflow directories, generated outputs, orchestration artifacts, operational lineage. Features: scoped access, change tracking, file lineage, workspace awareness |
| 3 | TerminalOrchestrator | `substrate/terminal_orchestrator.py` | All terminal execution management. Capabilities: run commands, monitor output, track runtime, stop hung processes, stream logs, attach execution traces. Safeguards: timeouts, permission scopes, resource limits, command allowlists |
| 4 | ProcessObserver | `substrate/process_observer.py` | Real-time process awareness. Tracks: active processes, spawned runtimes, CPU usage, memory usage, hung processes, orphaned tasks |
| 5 | ApplicationBridge | `substrate/application_bridge.py` | Controlled application interaction. Initial targets: VS Code, browser, terminal, git, Docker |
| 6 | EnvironmentModel | `substrate/environment_model.py` | Live machine-state awareness. Tracks: open projects, active workflows, running environments, operational context, active repos, orchestration zones |
| 7 | RuntimeInspector | `substrate/runtime_inspector.py` | Inspect live operational conditions. Tracks: system load, memory pressure, GPU state, disk state, runtime bottlenecks, orchestration pressure |
| 8 | PermissionLayer | `substrate/permission_layer.py` | Enforce strict operational boundaries. Rules: filesystem scoped, terminal bounded, network controlled, applications whitelisted, processes monitored |
| 9 | ExecutionSandbox | `substrate/execution_sandbox.py` | Safe operational execution zones. Types: dev sandbox, orchestration sandbox, testing sandbox, replay sandbox |
| 10 | MachineStateGraph | `substrate/machine_state_graph.py` | Represent the machine itself as topology. Nodes: applications, runtimes, processes, repositories, workflows, spawned agents. Relationships: active execution, orchestration dependency, resource coupling, workflow continuity |
| 11 | RecoveryController | `substrate/recovery_controller.py` | Handle runtime recovery and stabilization. Responsibilities: terminate hung tasks, restart observers, recover runtime continuity, restore orchestration state, reduce entropy cascades |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | MachineStateView | `components/substrate/MachineStateView.tsx` | Live machine state display |
| 2 | ProcessGraph | `components/substrate/ProcessGraph.tsx` | Process topology visualization |
| 3 | RuntimeInspector | `components/substrate/RuntimeInspector.tsx` | Runtime telemetry display |
| 4 | FilesystemTopology | `components/substrate/FilesystemTopology.tsx` | Filesystem as topology |
| 5 | SandboxMonitor | `components/substrate/SandboxMonitor.tsx` | Sandbox monitoring |
| 6 | EnvironmentModelView | `components/substrate/EnvironmentModelView.tsx` | Environment model display |
| 7 | TerminalExecutionPanel | `components/substrate/TerminalExecutionPanel.tsx` | Terminal execution display |
| 8 | RecoveryTimeline | `components/substrate/RecoveryTimeline.tsx` | Recovery operations timeline |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Filesystem awareness test | Track repo mutations, workflow outputs, runtime artifacts |
| 2 | Terminal orchestration test | Bounded execution workflows |
| 3 | Process monitor test | Hung processes, overload conditions, runtime crashes |
| 4 | Environment model test | Switch projects, runtimes, active workflows |
| 5 | Sandbox test | Attempt out-of-scope execution, restricted access |
| 6 | Machine topology test | Complex runtime workflows, machine graph updates |
| 7 | Recovery test | Observer crash, process failure, orchestration collapse |
| 8 | Long horizon embodiment test | 72hr operational session |

---

## PHASE O-7: PERSISTENT FIELD MODE

### Backend Components (Python)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | PersistentRuntime | `persistence/persistent_runtime.py` | Always-on orchestration substrate. Maintains runtime continuity, coordinates persistent observers, preserves field state, manages dormant cycles, maintains topology continuity |
| 2 | ObserverPersistence | `persistence/observer_persistence.py` | Ensure core observers never lose continuity. Features: heartbeat, restart recovery, state restoration, observer synchronization |
| 3 | PassiveAwareness | `persistence/passive_awareness.py` | Background environmental awareness WITHOUT constant active orchestration. Tracks: machine state, workflow evolution, active projects, topology drift, entropy changes |
| 4 | EnvironmentalMonitor | `persistence/environmental_monitor.py` | Observe machine + workflow ecosystem. Monitors: repository changes, runtime health, resource pressure, process instability, orchestration saturation |
| 5 | ContinuityPreserver | `persistence/continuity_preserver.py` | Preserve long-horizon operational continuity. Tracks: workflows, topology evolution, observer states, orchestration memory, runtime lineage |
| 6 | DormantStateManager | `persistence/dormant_state_manager.py` | Control active vs dormant orchestration states. States: dormant (low-resource awareness), observational (passive monitoring), active (task execution), recovery (stabilization), critical (emergency containment) |
| 7 | AutonomousRepair | `persistence/autonomous_repair.py` | Bounded self-stabilization. Allowed: restart observers, terminate hung tasks, restore continuity state, rebalance topology, reduce orchestration load. Forbidden: rewrite system architecture, mutate orchestration core, uncontrolled spawning |
| 8 | RuntimeHeartbeat | `persistence/runtime_heartbeat.py` | Maintain field continuity pulse. Tracks: observer health, topology stability, entropy pressure, runtime load, orchestration activity |
| 9 | PersistentScheduler | `persistence/persistent_scheduler.py` | Manage background operational tasks. Types: health checks, topology snapshots, memory persistence, replay compression, entropy scans. Must remain predictable and bounded. |
| 10 | RecoveryPersistence | `persistence/recovery_persistence.py` | Preserve runtime continuity during failure. Handles: crashes, restarts, machine reboots, observer failures, runtime corruption |
| 11 | LongHorizonMemory | `persistence/long_horizon_memory.py` | Maintain persistent operational identity across weeks, months, project evolution. Stores: workflow evolution, orchestration evolution, topology history, adaptation trends, repair history |
| 12 | OperationalDriftDetector | `persistence/operational_drift_detect.py` | Detect slow degradation patterns. Detects: entropy creep, observer instability, topology decay, orchestration inefficiency, memory corruption |

### Frontend Components (TypeScript/React)

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | PersistentFieldView | `components/persistence/PersistentFieldView.tsx` | Persistent field state display |
| 2 | RuntimeHeartbeatPanel | `components/persistence/RuntimeHeartbeatPanel.tsx` | Field continuity pulse |
| 3 | DormantStateMonitor | `components/persistence/DormantStateMonitor.tsx` | Dormant/active state transitions |
| 4 | ObserverPersistenceView | `components/persistence/ObserverPersistenceView.tsx` | Observer persistence status |
| 5 | DriftAnalysisPanel | `components/persistence/DriftAnalysisPanel.tsx` | Operational drift detection |
| 6 | LongHorizonTimeline | `components/persistence/LongHorizonTimeline.tsx` | Long-horizon continuity timeline |
| 7 | AutonomousRepairView | `components/persistence/AutonomousRepairView.tsx` | Bounded self-stabilization display |
| 8 | RecoveryContinuityPanel | `components/persistence/RecoveryContinuityPanel.tsx` | Recovery continuity display |
| 9 | persistenceStore | `stores/persistenceStore.ts` | Zustand store for persistence state |

### Tests

| # | Test | Description |
|---|------|-------------|
| 1 | Persistent runtime test | 7-day continuous operation |
| 2 | Observer recovery test | Crash observers, runtime processes, topology nodes |
| 3 | Dormant state test | Idle runtime periods, low-resource passive state |
| 4 | Autonomous repair test | Inject hung tasks, entropy spikes, topology instability |
| 5 | Machine reboot test | Restart machine, runtime, orchestration layer |
| 6 | Drift detection test | Inject slow orchestration degradation |
| 7 | Long-horizon memory test | Multi-week operational workflows |
| 8 | Stress test | Persistent observers + multiple spawned agents + replay + topology monitoring for extended duration |
