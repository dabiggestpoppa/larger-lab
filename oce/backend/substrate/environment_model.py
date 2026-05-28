"""
O-6: Environment Model — Live Machine-State Awareness
=====================================================

Live machine-state awareness for workspace operations.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("oce.substrate.environment_model")


class EnvironmentModel:
    """
    Live machine-state awareness.
    
    Tracks:
    - Open projects
    - Active workflows
    - Running environments
    - Operational context
    - Active repos
    - Orchestration zones
    """
    
    _instance: Optional["EnvironmentModel"] = None
    
    def __init__(self):
        self._active_projects: List[str] = []
        self._active_workflows: List[str] = []
        self._running_environments: List[str] = []
    
    def get_current_environment(self) -> Dict[str, Any]:
        """Get current environment state."""
        import psutil
        
        # Get active projects (workspace directories)
        workspace = Path.cwd()
        projects = []
        
        for item in workspace.parent.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "active": str(item) == str(workspace),
                })
        
        return {
            "workspace": str(workspace),
            "projects": projects,
            "active_projects": self._active_projects,
            "active_workflows": self._active_workflows,
            "running_environments": self._running_environments,
            "system": {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("/").percent,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def set_active_project(self, project_path: str):
        """Set active project."""
        if project_path not in self._active_projects:
            self._active_projects.append(project_path)
    
    def set_active_workflow(self, workflow_id: str):
        """Set active workflow."""
        if workflow_id not in self._active_workflows:
            self._active_workflows.append(workflow_id)


def get_environment_model() -> EnvironmentModel:
    """Get singleton EnvironmentModel instance."""
    if EnvironmentModel._instance is None:
        EnvironmentModel._instance = EnvironmentModel()
    return EnvironmentModel._instance