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

    def _determine_next_action(self, request: OrchestrationRequest) -> str:
        if request.requires_spawn:
            return "spawn_agent"
        if request.task_domain == "orchestration":
            return "coordinate"
        if request.task_domain == "repair":
            return "repair"
        return "direct_response"
