# Primary Observer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""
O-1-B1: PrimaryObserver
=======================
Main orchestration interface.

Receives user input, analyzes intent, gathers runtime state,
communicates with observer field, prepares orchestration requests,
maintains continuity state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.observer.observer_state import ObserverState, get_observer_state, HealthStatus
from core.observer.task_intent_analyzer import TaskIntentAnalyzer
from core.observer.context_distiller import ContextDistiller
from core.observer.event_awareness import EventAwareness, EventType


@dataclass
class OrchestrationRequest:
    """Structured orchestration request from user input."""
    request_id: str
    raw_input: str
    timestamp: str
    task_domain: str = ""
    complexity: str = "low"
    requires_spawn: bool = False
    requires_repo_access: bool = False
    requires_runtime_context: bool = False
    context: dict[str, Any] = field(default_factory=dict)
    routing_hints: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResponse:
    """Response from the Primary Observer."""
    request_id: str
    observer_id: str
    timestamp: str
    status: str  # "received", "analyzing", "routing", "spawning", "complete", "error"
    task_domain: str = ""
    complexity: str = ""
    message: str = ""
    context_summary: dict[str, Any] = field(default_factory=dict)
    routing_hints: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""
    error: str | None = None


class PrimaryObserver:
    """
    The Primary Observer — persistent continuity-aware orchestration interface.
    
    This is the main entry point for all user orchestration requests.
    It analyzes intent, gathers runtime state, and prepares orchestration.
    """

    def __init__(self):
        self.observer_id = "primary_observer"
        self.state = get_observer_state()
        self.intent_analyzer = TaskIntentAnalyzer()
        self.context_distiller = ContextDistiller()
        self.event_awareness = EventAwareness()
        self._request_count = 0

    @property
    def health(self) -> dict[str, Any]:
        return {
            "observer_id": self.observer_id,
            "status": self.state.get("observer_health"),
            "continuity_score": self.state.get("continuity_score"),
            "active_agents": self.state.get("active_agents", []),
            "request_count": self._request_count,
            "last_updated": self.state.get("last_updated"),
        }

    def receive_input(self, user_input: str, session_context: dict | None = None) -> OrchestrationResponse:
        """
        Main entry point: receive user input and produce orchestration response.
        
        Flow:
        1. Create orchestration request
        2. Analyze task intent
        3. Gather runtime state
        4. Distill context
        5. Emit event
        6. Return structured response
        """
        self._request_count += 1

        # Step 1: Create request
        request = OrchestrationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            raw_input=user_input,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=session_context or {},
        )

        # Step 2: Analyze intent
        intent = self.intent_analyzer.analyze(user_input)
        request.task_domain = intent["domain"]
        request.complexity = intent["complexity"]
        request.requires_spawn = intent["requires_spawn"]
        request.requires_repo_access = intent["requires_repo_access"]
        request.requires_runtime_context = intent["requires_runtime_context"]
        request.routing_hints = intent.get("routing_hints", {})

        # Step 3: Update state
        self.state.update(
            active_task=request.request_id,
            session_context={
                "last_input": user_input,
                "last_domain": request.task_domain,
                "last_complexity": request.complexity,
            },
        )

        # Step 4: Distill context
        context_summary = self.context_distiller.distill(
            task_domain=request.task_domain,
            complexity=request.complexity,
            runtime_state=self.state.get("runtime_state", {}),
            session_context=request.context,
        )

        # Step 5: Emit event
        self.event_awareness.emit(
            EventType.TASK_RECEIVED,
            source=self.observer_id,
            data={
                "request_id": request.request_id,
                "domain": request.task_domain,
                "complexity": request.complexity,
            },
        )

        # Step 6: Build response
        response = OrchestrationResponse(
            request_id=request.request_id,
            observer_id=self.observer_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status="received",
            task_domain=request.task_domain,
            complexity=request.complexity,
            message=f"Task analyzed: {request.task_domain} ({request.complexity})",
            context_summary=context_summary,
            routing_hints=request.routing_hints,
            next_action=self._determine_next_action(request),
        )

        return response

    def get_status(self) -> dict[str, Any]:
        """Get full observer status for frontend display."""
        return {
            "health": self.health,
            "runtime_state": self.state.get("runtime_state", {}),
            "entropy_state": self.state.get("entropy_state", {}),
            "repair_state": self.state.get("repair_state", {}),
            "continuity_score": self.state.get("continuity_score"),
            "active_agents": self.state.get("active_agents", []),
        }

    def update_runtime_state(self, key: str, value: Any) -> None:
        """Update a specific runtime state field."""
        runtime = self.state.get("runtime_state", {})
        runtime[key] = value
        self.state.set("runtime_state", runtime)

    def execute(self, response: OrchestrationResponse, user_input: str) -> dict[str, Any]:
        """
        Execute the next action determined by receive_input().
        
        If next_action is spawn_agent, runs the AgentSpawner pipeline
        AND executes real tasks via TaskExecutor when task is recognized.
        Returns a dict with execution results.
        """
        from core.observer.task_executor import TaskExecutor
        executor = TaskExecutor()

        # Check for known task patterns and execute directly
        task_results = self._try_execute_known_task(user_input, executor)
        if task_results is not None:
            self.event_awareness.emit(
                EventType.TASK_COMPLETED,
                source=self.observer_id,
                data={
                    "request_id": response.request_id,
                    "task_results": [r.to_dict() for r in task_results],
                },
            )
            return {
                "action": "direct_execution",
                "status": "completed",
                "task_results": [r.to_dict() for r in task_results],
            }

        # Otherwise run the spawn pipeline for general tasks
        if response.next_action == "spawn_agent":
            import asyncio
            from core.spawn.agent_spawner import AgentSpawner
            
            spawner = AgentSpawner()
            try:
                result = asyncio.get_event_loop().run_until_complete(
                    spawner.spawn(
                        user_input=user_input,
                        session_context=response.context_summary,
                    )
                )
                self.event_awareness.emit(
                    EventType.AGENT_SPAWNED,
                    source=self.observer_id,
                    data={
                        "spawn_id": result.spawn_id,
                        "status": result.status,
                        "task_type": result.consensus.get("task_type"),
                        "model": result.blueprint.get("target_model") if result.blueprint else None,
                    },
                )
                self.state.add_active_agent(result.spawn_id)
                return {
                    "action": "spawn_agent",
                    "spawn_id": result.spawn_id,
                    "status": result.status,
                    "output": result.output,
                    "consensus": result.consensus,
                    "duration_ms": result.duration_ms,
                }
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        spawner.spawn(
                            user_input=user_input,
                            session_context=response.context_summary,
                        )
                    )
                    self.event_awareness.emit(
                        EventType.AGENT_SPAWNED,
                        source=self.observer_id,
                        data={
                            "spawn_id": result.spawn_id,
                            "status": result.status,
                            "task_type": result.consensus.get("task_type"),
                        },
                    )
                    self.state.add_active_agent(result.spawn_id)
                    return {
                        "action": "spawn_agent",
                        "spawn_id": result.spawn_id,
                        "status": result.status,
                        "output": result.output,
                        "consensus": result.consensus,
                        "duration_ms": result.duration_ms,
                    }
                finally:
                    loop.close()
            except Exception as e:
                self.event_awareness.emit(
                    EventType.SPAWN_FAILED,
                    source=self.observer_id,
                    data={"error": str(e)},
                )
                return {"action": "spawn_agent", "status": "failed", "error": str(e)}
        
        return {"action": response.next_action, "status": "no_execution_needed"}

    def _try_execute_known_task(self, user_input: str, executor) -> list | None:
        """Detect known task patterns and execute them directly."""
        text = user_input.lower()

        # Phase 1 cleanup
        if any(kw in text for kw in ["phase 1", "phase1", "cleanup", "workspace cleanup"]):
            if any(kw in text for kw in [".openclaw", "quant_lab", "shared", "archive", "cleanup"]):
                return executor.execute_phase1_cleanup()

        # Move to archive
        if "move" in text and "archive" in text:
            import re
            match = re.search(r"move\s+(\S+)\s+to\s+archive", text)
            if match:
                return [executor.move_to_archive(match.group(1))]

        # Remove symlink
        if "remove" in text and "symlink" in text:
            import re
            match = re.search(r"remove\s+symlink\s+(\S+)", text)
            if match:
                return [executor.remove_symlink(match.group(1))]

        # Merge directories
        if "merge" in text:
            import re
            match = re.search(r"merge\s+(\S+)\s+into\s+(\S+)", text)
            if match:
                return [executor.merge_directories(match.group(1), match.group(2))]

        return None

    def _determine_next_action(self, request: OrchestrationRequest) -> str:
        if request.requires_spawn:
            return "spawn_agent"
        if request.task_domain == "orchestration":
            return "coordinate"
        if request.task_domain == "repair":
            return "repair"
        return "direct_response"

```

LINKS:
[[All Mermaid Graphs]]
[[Agents]]
[[Master Plan Observer Core]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[User]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Action]]
[[Blueprint]]
[[Citation Workflow]]
[[Patterns]]
[[Server]]
[[Wise]]
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
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
