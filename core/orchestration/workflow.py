"""
Phase 1.6.4 — Workflow Topology

Execution DAG system. Represents workflows as directed acyclic graphs
that are inspectable, recursive, modular, and replayable.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.workflow")


@dataclass
class WorkflowNode:
    """A node in a workflow DAG."""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    title: str = ""
    action: str = ""  # What to execute
    agent: str = ""  # Which agent handles it
    config: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, complete, failed
    output: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class WorkflowEdge:
    """A directed edge between workflow nodes."""
    from_id: str = ""
    to_id: str = ""
    condition: str = ""  # Optional condition for traversal


@dataclass
class Workflow:
    """A complete workflow DAG."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, title: str, action: str, agent: str = "", config: Optional[Dict] = None) -> WorkflowNode:
        """Add a node to the workflow."""
        node = WorkflowNode(title=title, action=action, agent=agent, config=config or {})
        self.nodes.append(node)
        return node

    def add_edge(self, from_id: str, to_id: str, condition: str = "") -> WorkflowEdge:
        """Add a directed edge between nodes."""
        edge = WorkflowEdge(from_id=from_id, to_id=to_id, condition=condition)
        self.edges.append(edge)
        return edge

    def get_ready_nodes(self) -> List[WorkflowNode]:
        """Get nodes whose dependencies are all complete."""
        completed_ids = {n.node_id for n in self.nodes if n.status == "complete"}
        ready = []
        for node in self.nodes:
            if node.status != "pending":
                continue
            # Check all incoming edges
            incoming = [e for e in self.edges if e.to_id == node.node_id]
            if all(e.from_id in completed_ids for e in incoming):
                ready.append(node)
        return ready

    @property
    def is_complete(self) -> bool:
        return all(n.status == "complete" for n in self.nodes)

    @property
    def completion_pct(self) -> float:
        if not self.nodes:
            return 0.0
        complete = sum(1 for n in self.nodes if n.status == "complete")
        return complete / len(self.nodes)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "title": self.title,
            "nodes": [{"id": n.node_id, "title": n.title, "status": n.status} for n in self.nodes],
            "edges": [{"from": e.from_id, "to": e.to_id} for e in self.edges],
            "completion_pct": self.completion_pct,
        }


class WorkflowEngine:
    """
    Manages workflow DAGs: creation, execution, persistence, replay.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self._workflows: Dict[str, Workflow] = {}
        self._storage_dir = storage_dir or Path("data/workflows")
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def create_workflow(self, title: str, description: str = "") -> Workflow:
        """Create a new workflow."""
        wf = Workflow(title=title, description=description)
        self._workflows[wf.workflow_id] = wf
        logger.info(f"Workflow created: {title} ({wf.workflow_id})")
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def save_workflow(self, workflow_id: str) -> bool:
        """Persist workflow to disk."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        path = self._storage_dir / f"{workflow_id}.json"
        path.write_text(json.dumps(wf.to_dict(), indent=2), encoding="utf-8")
        return True

    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow from disk."""
        path = self._storage_dir / f"{workflow_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        wf = Workflow(
            workflow_id=data["workflow_id"],
            title=data["title"],
        )
        for node_data in data.get("nodes", []):
            node = WorkflowNode(node_id=node_data["id"], title=node_data["title"], status=node_data.get("status", "pending"))
            wf.nodes.append(node)
        for edge_data in data.get("edges", []):
            wf.add_edge(edge_data["from"], edge_data["to"])
        self._workflows[workflow_id] = wf
        return wf

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows with their status."""
        return [
            {
                "id": wf.workflow_id,
                "title": wf.title,
                "nodes": len(wf.nodes),
                "completion_pct": wf.completion_pct,
            }
            for wf in self._workflows.values()
        ]
