"""
O-6: Application Bridge — Controlled Application Interaction
=========================================================

Controlled application interaction for VS Code, browser, terminal, git, Docker.
"""

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("oce.substrate.application_bridge")


@dataclass
class ApplicationState:
    """State of an application."""
    name: str
    status: str  # "running", "idle", "unavailable"
    pid: Optional[int] = None
    last_interaction: str = ""


class ApplicationBridge:
    """
    Controlled application interaction.
    
    Initial targets:
    - VS Code
    - Browser
    - Terminal
    - Git
    - Docker
    """
    
    _instance: Optional["ApplicationBridge"] = None
    
    def __init__(self):
        self._applications: Dict[str, ApplicationState] = {}
    
    async def interact(
        self,
        app_name: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Interact with an application.
        
        Args:
            app_name: Application name
            action: Action to perform
            params: Action parameters
            
        Returns:
            Interaction result
        """
        from .permission_layer import get_permission_layer
        pl = get_permission_layer()
        
        if not pl.check_permission("application", "access", app_name):
            return {"error": f"Application {app_name} not permitted"}
        
        if app_name == "vscode":
            return await self._vscode_action(action, params)
        elif app_name == "browser":
            return await self._browser_action(action, params)
        elif app_name == "terminal":
            return await self._terminal_action(action, params)
        elif app_name == "git":
            return await self._git_action(action, params)
        elif app_name == "docker":
            return await self._docker_action(action, params)
        else:
            return {"error": f"Unknown application: {app_name}"}
    
    async def _vscode_action(self, action: str, params: Optional[Dict]) -> Dict[str, Any]:
        """VS Code interaction."""
        # Would integrate with VS Code extension API
        return {"app": "vscode", "action": action, "status": "simulated"}
    
    async def _browser_action(self, action: str, params: Optional[Dict]) -> Dict[str, Any]:
        """Browser interaction."""
        # Would integrate with browser automation
        return {"app": "browser", "action": action, "status": "simulated"}
    
    async def _terminal_action(self, action: str, params: Optional[Dict]) -> Dict[str, Any]:
        """Terminal interaction."""
        from .terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        
        if action == "execute":
            return await to.execute(params.get("command", ""))
        elif action == "list":
            return to.get_active_executions()
        else:
            return {"error": f"Unknown terminal action: {action}"}
    
    async def _git_action(self, action: str, params: Optional[Dict]) -> Dict[str, Any]:
        """Git interaction."""
        from .terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        
        if action == "status":
            return await to.execute("git status")
        elif action == "commit":
            return await to.execute(f"git commit -m '{params.get('message', '')}'")
        else:
            return {"error": f"Unknown git action: {action}"}
    
    async def _docker_action(self, action: str, params: Optional[Dict]) -> Dict[str, Any]:
        """Docker interaction."""
        from .terminal_orchestrator import get_terminal_orchestrator
        to = get_terminal_orchestrator()
        
        if action == "ps":
            return await to.execute("docker ps")
        elif action == "logs":
            return await to.execute(f"docker logs {params.get('container', '')}")
        else:
            return {"error": f"Unknown docker action: {action}"}
    
    def get_application_state(self, app_name: str) -> Optional[ApplicationState]:
        """Get state of a specific application."""
        return self._applications.get(app_name)
    
    def list_applications(self) -> Dict[str, Any]:
        """List all tracked applications."""
        return {
            "applications": [
                {"name": name, "status": state.status}
                for name, state in self._applications.items()
            ]
        }


def get_application_bridge() -> ApplicationBridge:
    """Get singleton ApplicationBridge instance."""
    if ApplicationBridge._instance is None:
        ApplicationBridge._instance = ApplicationBridge()
    return ApplicationBridge._instance