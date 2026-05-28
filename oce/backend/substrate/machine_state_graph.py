"""
O-6: Machine State Graph — Machine as Topology
==============================================

Represent the machine itself as topology.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("oce.substrate.machine_state_graph")


@dataclass
class MachineNode:
    """A node in the machine state graph."""
    id: str
    type: str  # "application", "runtime", "process", "repository", "workflow", "agent"
    name: str
    status: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MachineEdge:
    """An edge in the machine state graph."""
    source: str
    target: str
    relationship: str  # "active_execution", "orchestration_dependency", "resource_coupling", "workflow_continuity"


class MachineStateGraph:
    """
    Represent the machine itself as topology.
    
    Nodes:
    - Applications
    - Runtimes
    - Processes
    - Repositories
    - Workflows
    - Spawned agents
    
    Relationships:
    - Active execution
    - Orchestration dependency
    - Resource coupling
    - Workflow continuity
    """
    
    _instance: Optional["MachineStateGraph"] = None
    
    def __init__(self):
        self.nodes: Dict[str, MachineNode] = {}
        self.edges: List[MachineEdge] = []
    
    def build_graph(self) -> Dict[str, Any]:
        """Build the machine state graph."""
        # Applications
        self._add_application_nodes()
        
        # Processes
        self._add_process_nodes()
        
        # Repositories
        self._add_repository_nodes()
        
        # Workflows
        self._add_workflow_nodes()
        
        return {
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
        }
    
    def _add_application_nodes(self):
        """Add application nodes."""
        import psutil
        
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info["name"].lower()
                if any(app in name for app in ["code", "chrome", "firefox", "node", "python"]):
                    node = MachineNode(
                        id=f"app_{proc.info['pid']}",
                        type="application",
                        name=proc.info["name"],
                        status="running",
                        metadata={"pid": proc.info["pid"]},
                    )
                    self.nodes[node.id] = node
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def _add_process_nodes(self):
        """Add process nodes."""
        from .process_observer import get_process_observer
        po = get_process_observer()
        
        for proc in po.scan_processes():
            node = MachineNode(
                id=f"proc_{proc.pid}",
                type="process",
                name=proc.name,
                status=proc.status,
                metadata={"cpu": proc.cpu_percent, "memory": proc.memory_percent},
            )
            self.nodes[node.id] = node
    
    def _add_repository_nodes(self):
        """Add repository nodes."""
        from pathlib import Path
        
        workspace = Path.cwd()
        for item in workspace.parent.iterdir():
            if item.is_dir() and (item / ".git").exists():
                node = MachineNode(
                    id=f"repo_{item.name}",
                    type="repository",
                    name=item.name,
                    status="active",
                    metadata={"path": str(item)},
                )
                self.nodes[node.id] = node
    
    def _add_workflow_nodes(self):
        """Add workflow nodes."""
        from .environment_model import get_environment_model
        em = get_environment_model()
        
        for wf in em._active_workflows:
            node = MachineNode(
                id=f"wf_{wf}",
                type="workflow",
                name=wf,
                status="active",
            )
            self.nodes[node.id] = node
    
    def add_edge(self, source: str, target: str, relationship: str):
        """Add an edge to the graph."""
        edge = MachineEdge(source=source, target=target, relationship=relationship)
        self.edges.append(edge)
    
    def get_graph(self) -> Dict[str, Any]:
        """Get current graph state."""
        return {
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }


def get_machine_state_graph() -> MachineStateGraph:
    """Get singleton MachineStateGraph instance."""
    if MachineStateGraph._instance is None:
        MachineStateGraph._instance = MachineStateGraph()
    return MachineStateGraph._instance