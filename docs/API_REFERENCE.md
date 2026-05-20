# 📡 API Reference — OCE Backend & V3 Modules

> **Version:** 1.0.0 | **Last Updated:** 2026-05-18
> **Base URL:** `http://localhost:8000` (FastAPI backend)

---

## Table of Contents

1. [OCE Backend API (FastAPI)](#oce-backend-api)
2. [SRRA-OPH API](#srra-oph-api)
3. [V3 Module API (Phases 1-10)](#v3-module-api)

---

## OCE Backend API

### Chat & Continuity

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Continuity chat — preserves goals, trajectories, observer state |
| GET | `/health` | Health check — returns `{"status": "healthy"}` |

**POST /chat**
```json
{
  "message": "string",
  "session_id": "optional-session-id",
  "context": {}
}
```
Response:
```json
{
  "response": "string",
  "session_id": "string",
  "continuity_preserved": true
}
```

### Observers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/observers` | List all observers with live status |

Response: `List<ObserverStatus>`
```json
[{
  "observer_id": "string",
  "state": "active|idle|monitoring",
  "entropy": 0.5,
  "task": "string"
}]
```

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events` | Query event history (filter by type, source, priority) |
| POST | `/events/ingest` | Ingest a new event into the Event Fabric |
| GET | `/events/types` | List all registered event types |
| GET | `/events/stats` | Event throughput statistics |
| GET | `/events/persistence/stats` | Persistence layer statistics |
| POST | `/events/persistence/compress` | Compress old events |

**Query Parameters for GET /events:**
- `limit` (int, default 50, max 1000)
- `event_type` (string, optional)
- `source` (string, optional)
- `min_priority` (int, 0-3, optional)

**POST /events/ingest**
```json
{
  "event_type": "string",
  "source": "string",
  "payload": {},
  "priority": 0
}
```

### Attractor

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/attractor` | Get current attractor state |

Response:
```json
{
  "goal": "string",
  "confidence": 0.85,
  "entropy_pressure": 0.2,
  "convergence": 0.9
}
```

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memory/store` | Store a memory entry |
| POST | `/memory/search` | Search memory by query, layer, tags |
| POST | `/memory/compress` | Compress memory layer |

**POST /memory/store**
```json
{
  "layer": "WORK|LEARNED|KNOWLEDGE",
  "content": {},
  "tags": ["tag1", "tag2"],
  "ttl_seconds": 3600,
  "source": "string"
}
```

### Topology

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/topology/stats` | Observer topology statistics |

### Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/execution/submit` | Submit an execution task |
| GET | `/execution/status/{task_id}` | Get task status |
| POST | `/execution/cancel/{task_id}` | Cancel a task |
| GET | `/execution/history` | Task history |

### Governance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/governance/propose` | Submit a proposal |
| POST | `/governance/approve/{id}` | Approve a proposal |
| POST | `/governance/reject/{id}` | Reject a proposal |
| GET | `/governance/proposals` | List proposals |
| GET | `/governance/status` | Governance status |
| GET | `/governance/log` | Audit log |

### Coevolution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/coevolution/status` | Coevolution status |
| GET | `/coevolution/peers` | List peer agents |
| POST | `/coevolution/peers` | Register a peer |
| POST | `/coevolution/topology/negotiate` | Negotiate topology change |
| POST | `/coevolution/goals/align` | Align goals with peer |

### Resonance (V3 Phase 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resonance/signal` | Inject a signal into the cognitive field |
| GET | `/resonance/signals` | Query signals (by type/source) |
| DELETE | `/resonance/signals` | Clear all signals |
| GET | `/resonance/field` | Get field state + coherence |
| POST | `/resonance/field/decay` | Apply decay step |
| POST | `/resonance/field/repair` | Trigger field repair |
| GET | `/resonance/coherence` | Coherence snapshot |
| GET | `/resonance/coherence/trend` | Coherence trend history |
| POST | `/resonance/observer` | Register an observer |
| DELETE | `/resonance/observer/{id}` | Remove an observer |
| POST | `/resonance/score` | Score observer-signal resonance |
| POST | `/resonance/constraint` | Add a constraint |
| GET | `/resonance/constraints` | List constraints |
| GET | `/resonance/action-path` | Get constraint-derived action path |
| POST | `/resonance/scan` | Pressure anomaly scan |
| GET | `/resonance/alerts` | List pressure alerts |
| POST | `/resonance/alerts/{id}/resolve` | Resolve an alert |
| GET | `/resonance/stats` | Full subsystem stats |

### Reconstruction (V3 Phase 2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reconstruction/reconstruct` | Reconstruct field state |
| GET | `/reconstruction/attractors` | List attractors |
| POST | `/reconstruction/drift/check` | Check for drift |
| GET | `/reconstruction/continuity` | Continuity status |

### Topology (V3 Phase 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/topology/collar/connect` | Create/strengthen collar connection |
| DELETE | `/topology/collar/disconnect` | Weaken collar connection |
| GET | `/topology/collars` | List all collars |
| GET | `/topology/resonance-matrix` | Full resonance matrix |
| GET | `/topology/boundaries` | List boundaries |
| POST | `/topology/boundaries/detect` | Run boundary detection |
| GET | `/topology/pressure-zones` | List pressure zones |
| POST | `/topology/project` | Generate BSP trajectory projection |
| POST | `/topology/route` | Route signal by resonance |
| POST | `/topology/glyph/encode` | Encode text to glyphs |
| POST | `/topology/glyph/decode` | Decode glyphs to text |
| GET | `/topology/stats` | Topology health stats |

### Sovereign (V3 Phase 4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sovereign/route` | Get executive routing decision |
| POST | `/sovereign/tool/execute` | Execute a tool via embodiment layer |
| GET | `/sovereign/swarm` | Swarm node status |
| POST | `/sovereign/snapshot` | Create continuity snapshot |
| POST | `/sovereign/restore` | Restore from snapshot |
| GET | `/sovereign/economics` | Compute economics stats |

### Multiscale (V3 Phase 7)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/multiscale/fields` | List all local fields |
| POST | `/multiscale/fields/{id}/sync` | Force sync a field |
| GET | `/multiscale/clusters` | List regional clusters |
| GET | `/multiscale/attractor` | Global attractor state |

### Field Core (V3 Phase 9)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/field/resonance/measure` | Measure resonance between elements |
| GET | `/field/nodes` | List field nodes and topology |
| GET | `/field/attractors` | List detected attractors |
| GET | `/field/drift` | Current drift metrics |
| POST | `/field/reconstruct` | Trigger state reconstruction |
| GET | `/field/continuity` | Continuity checkpoint status |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/events` | Real-time event stream |

---

## SRRA-OPH API

### Core Classes

#### `CollarState`
Shared state contract between agents.
```python
@dataclass
class CollarState:
    agent_id: str
    status: str          # "active", "idle", "repairing"
    entropy: float       # 0-1, current entropy level
    coherence: float     # 0-1, coherence with field
    active_tasks: list[str]
    last_updated: float
```

#### `PlannerPatch`
Planning interface for agent coordination.
```python
class PlannerPatch:
    def create_plan(self, goal: str, constraints: dict) -> Plan
    def validate_plan(self, plan: Plan) -> bool
    def execute_plan(self, plan: Plan) -> ExecutionResult
```

#### `ExecutionPatch`
Execution interface for task management.
```python
class ExecutionPatch:
    def submit(self, task: Task) -> str  # returns task_id
    def status(self, task_id: str) -> ExecutionStatus
    def cancel(self, task_id: str) -> bool
    def history(self, limit: int = 50) -> list[ExecutionResult]
```

#### `MemoryPatch`
Memory interface for state persistence.
```python
class MemoryPatch:
    def store(self, key: str, value: Any, ttl: int = None) -> bool
    def retrieve(self, key: str, default: Any = None) -> Any
    def search(self, query: str, limit: int = 20) -> list[MemoryEntry]
    def compress(self, layer: str = "WORK") -> int  # returns compressed count
```

#### `RepairPatch`
Repair interface for drift correction.
```python
class RepairPatch:
    def detect_drift(self, expected: dict, actual: dict) -> DriftReport
    def repair(self, target: str, strategy: str = "auto") -> RepairResult
    def validate(self, target: str) -> bool
```

#### `CollarTopologyEngine`
Topology management for agent collars.
```python
class CollarTopologyEngine:
    def connect(self, agent_a: str, agent_b: str, weight: float = 1.0) -> None
    def disconnect(self, agent_a: str, agent_b: str) -> None
    def get_topology(self) -> dict
    def get_neighbors(self, agent_id: str) -> list[str]
    def get_stats(self) -> TopologyStats
```

#### `DriftDetector`
Drift detection for field coherence.
```python
class DriftDetector:
    def measure(self, element_id: str, expected: dict, actual: dict) -> DriftMetrics
    def get_threshold(self, element_id: str) -> float
    def set_threshold(self, element_id: str, threshold: float) -> None
    def get_alerts(self) -> list[DriftAlert]
```

#### `EntropyBudgetManager`
Resource allocation and entropy budgeting.
```python
class EntropyBudgetManager:
    def allocate(self, agent_id: str, budget: float) -> bool
    def consume(self, agent_id: str, amount: float) -> bool
    def get_remaining(self, agent_id: str) -> float
    def get_stats(self) -> BudgetStats
```

---

## V3 Module API

### Phase 1 — Resonant Signal Substrate

#### `SignalPacket`
Core signal object for the resonance substrate.
```python
@dataclass
class SignalPacket:
    source: str
    amplitude: float          # 0-1, signal strength
    coherence: float          # 0-1, coherence with field
    phase: float              # 0-2π, phase angle
    entropy_delta: float      # Entropy change caused by signal
    boundary_tags: list[str]
    resonance_targets: list[str]
    signal_id: str            # Auto-generated UUID
    timestamp: float

    @property
    def is_resonant(self) -> bool    # coherence > 0.5 and amplitude > 0.3
    @property
    def is_entropic(self) -> bool    # entropy_delta > 0.5
    @property
    def signal_pressure() -> float   # amplitude × (1 - coherence) × entropy_delta
```

#### `CoherenceEngine`
Measures resonance health of the cognitive field.
```python
class CoherenceEngine:
    def update_observer(self, observer_id: str, phase: float, coherence: float) -> None
    def remove_observer(self, observer_id: str) -> None
    def measure(self, field: SignalField) -> CoherenceSnapshot
    def get_trend(self, points: int = 10) -> list[CoherenceSnapshot]
    def get_drift_alerts(self) -> list[DriftAlert]
```

#### `FieldStateManager`
Manages the propagation of field-state through the cognitive substrate.
```python
class FieldStateManager:
    @property
    def state(self) -> FieldState
    @property
    def current_state(self) -> FieldState
    def inject_signal(self, signal: SignalPacket) -> None
    def entrain_observer(self, observer_id: str) -> None
    def remove_observer(self, observer_id: str) -> None
    def decay_step(self) -> None
    def repair(self) -> None
    def measure_coherence(self) -> CoherenceSnapshot
    def get_pressure_map(self) -> dict
    def get_drift_alerts(self) -> list[DriftAlert]
    def stats(self) -> dict
```

#### `ResonanceEngine`
Core resonance alignment and scoring mechanism.
```python
class ResonanceEngine:
    def add_constraint(self, constraint: Constraint) -> None
    def remove_constraint(self, constraint_id: str) -> None
    def score_resonance(self, observer_id: str, observer_phase: float,
                        observer_coherence: float, signal: SignalPacket) -> ResonanceScore
    def find_best_observer(self, signal: SignalPacket,
                           observers: dict) -> Optional[str]
    def harmonize_constraints(self) -> float
    def get_action_path(self) -> list[str]
    def inject_and_score(self, signal: SignalPacket, observers: dict) -> list[ResonanceScore]
    def decay_step(self) -> None
    def repair(self) -> None
    def stats(self) -> dict
```

### Phase 2 — Reconstructive Continuity

#### `ReconstructionEngine`
Reconstructs field state from partial information.
```python
class ReconstructionEngine:
    def reconstruct(self, target: str, known_state: dict, full_schema: dict) -> ReconstructionResult
    def set_topology(self, element_id: str, neighbors: list[str]) -> None
    def get_history(self, limit: int = 10) -> list[ReconstructionResult]
```

#### `ContinuityRepair`
Repairs continuity breaks in the field.
```python
class ContinuityRepair:
    def detect_break(self, element_id: str) -> Optional[BreakReport]
    def repair(self, element_id: str, strategy: str = "auto") -> RepairResult
    def validate_continuity(self, element_id: str) -> bool
```

#### `AttractorMemory`
Stores and retrieves attractor patterns.
```python
class AttractorMemory:
    def store(self, attractor: Attractor) -> str
    def find_nearest(self, state: dict, k: int = 3) -> list[Attractor]
    def get_attractor(self, attractor_id: str) -> Optional[Attractor]
    def decay(self, factor: float = 0.95) -> None
    def stats(self) -> dict
```

### Phase 7 — Multi-Scale Cognitive Fields

#### `LocalObserverField`
Independent local cognition field for a single observer.
```python
@dataclass
class LocalObserverField:
    observer_id: str
    field_state: dict
    coherence_level: float
    last_sync: Optional[datetime]
    sync_bound: int          # Max sync operations before forced sync
    local_operations: int

    def update_state(self, key: str, value: Any) -> None
    def get_state(self, key: str, default: Any = None) -> Any
    def needs_sync(self) -> bool
    def reset_sync_counter(self) -> None
    def calculate_coherence(self) -> float
```

#### `RegionalCluster`
Self-organizing cluster of observers.
```python
class RegionalCluster:
    def add_member(self, observer_id: str) -> None
    def remove_member(self, observer_id: str) -> None
    def get_members(self) -> list[str]
    def calculate_coherence(self) -> float
    def get_stats(self) -> dict
```

#### `GlobalAttractor`
Low-frequency strategic stabilization layer.
```python
class GlobalAttractor:
    def set_direction(self, direction: dict) -> None
    def get_direction(self) -> dict
    def calculate_influence(self, state: dict) -> float
    def update(self, field_state: dict) -> None
```

### Phase 8 — Operator Coevolution

#### `OperatorModel`
Models operator strategic behavior patterns from operational evidence.
```python
class OperatorModel:
    def record_observation(self, observation: dict) -> None
    def get_reliable_patterns(self) -> list[OperatorPattern]
    def get_model_summary(self) -> dict
    @property
    def stats(self) -> dict
```

#### `BidirectionalAdaptation`
System and operator adapt to each other.
```python
class BidirectionalAdaptation:
    def record_system_adaptation(self, adaptation: dict) -> None
    def record_operator_adaptation(self, adaptation: dict) -> None
    def record_mutual_adaptation(self, system_delta: dict, operator_delta: dict) -> None
    def get_adaptation_balance(self) -> dict
    @property
    def stats(self) -> dict
```

#### `AlignmentTracker`
Tracks alignment between system and operator over time.
```python
class AlignmentTracker:
    def record_alignment(self, measurement: AlignmentMeasurement) -> None
    def get_current_alignment(self) -> float
    def get_alignment_trend(self, window: int = 30) -> list[float]
    def is_aligned(self) -> bool
    def is_drifting(self) -> bool
    def get_misalignment_events(self) -> list[dict]
    @property
    def stats(self) -> dict
```

### Phase 9 — Sovereign Field Emergence

#### `AttractorMapper`
Detects stable recurring field configurations.
```python
class AttractorMapper:
    def detect(self, field_state: dict) -> list[AttractorState]
    def get_attractor(self, attractor_id: str) -> Optional[AttractorState]
    def get_stable_attractors(self) -> list[AttractorState]
    def record_visit(self, attractor_id: str) -> None
    def get_stats(self) -> dict
```

#### `DriftGovernor`
Measures divergence and triggers reconstruction.
```python
class DriftGovernor:
    def set_threshold(self, element_id: str, threshold: float) -> None
    def measure_drift(self, element_id: str, expected_state: dict,
                      actual_state: dict) -> DriftMetrics
    def get_metrics(self, element_id: str) -> list[DriftMetrics]
    def get_alerts(self) -> list[dict]
    def trigger_reconstruction(self, element_id: str) -> bool
```

#### `ContinuityIdentityEngine`
Maintains operational continuity across field transformations.
```python
class ContinuityIdentityEngine:
    def create_checkpoint(self, element_id: str, state: dict) -> ContinuityState
    def get_checkpoint(self, state_id: str) -> Optional[ContinuityState]
    def get_latest(self, element_id: str) -> Optional[ContinuityState]
    def is_continuous(self, element_id: str) -> bool
    def get_identity_map(self) -> dict
```

### Phase 10 — Recursive Field Computation

#### `RecursiveComputeGraph`
Computation through field resonance, not instruction execution.
```python
class RecursiveComputeGraph:
    def add_node(self, node: ComputeNode) -> None
    def connect_nodes(self, node_a: str, node_b: str) -> None
    def compute_coherence(self) -> float
    def stabilize_node(self, node_id: str) -> StabilizationResult
    def compute_cycle(self) -> list[StabilizationResult]
    def get_graph_state(self) -> dict
```

#### `PositionalReferenceSystem`
State transitions via relative relationships.
```python
class PositionalReferenceSystem:
    def create_frame(self, frame_id: str) -> ReferenceFrame
    def add_position(self, frame_id: str, position: Position) -> None
    def transition(self, frame_id: str, from_pos: str, to_pos: str) -> TransitionResult
    def compute_transition_path(self, frame_id: str, from_pos: str,
                                to_pos: str) -> list[Position]
    def get_frame(self, frame_id: str) -> Optional[ReferenceFrame]
```

#### `AttractorComputeEngine`
Solutions emerge through field convergence.
```python
class AttractorComputeEngine:
    def set_field_state(self, state: dict) -> None
    def compute_energy(self) -> float
    def compute(self, max_iterations: int = 100) -> AttractorSolution
    def get_attractors(self) -> list[AttractorSolution]
    def get_convergence_history(self) -> list[dict]
```

---

*Auto-generated from source code. Last updated: 2026-05-18*
