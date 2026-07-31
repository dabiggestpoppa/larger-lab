"""
O-6: Permission Layer — Operational Boundaries
==============================================

Enforces strict operational boundaries for all substrate operations.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("oce.substrate.permission_layer")


@dataclass
class PermissionRule:
    """A single permission rule."""
    scope: str  # "filesystem", "terminal", "network", "application", "process"
    action: str  # "read", "write", "execute", "access"
    resource: str  # Path pattern, command pattern, etc.
    allowed: bool = True


class PermissionLayer:
    """
    Enforce strict operational boundaries.
    
    Rules:
    - Filesystem scoped to workspace
    - Terminal bounded to safe commands
    - Network controlled access
    - Applications whitelisted
    - Processes monitored
    """
    
    _instance: Optional["PermissionLayer"] = None
    
    def __init__(self):
        self.rules: List[PermissionRule] = []
        self._workspace_root = Path.cwd()
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Set up default permission rules."""
        # Filesystem rules - scoped to workspace
        self.rules.append(PermissionRule(
            scope="filesystem",
            action="read",
            resource=str(self._workspace_root),
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="filesystem",
            action="write",
            resource=str(self._workspace_root),
            allowed=True
        ))
        
        # Terminal rules - bounded commands
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="git:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="python:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="npm:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="echo:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="ls:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="cat:*",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="terminal",
            action="execute",
            resource="pwd",
            allowed=True
        ))
        
        # Network rules - controlled
        self.rules.append(PermissionRule(
            scope="network",
            action="access",
            resource="localhost:*",
            allowed=True
        ))
        
        # Application rules - whitelisted
        self.rules.append(PermissionRule(
            scope="application",
            action="access",
            resource="vscode",
            allowed=True
        ))
        self.rules.append(PermissionRule(
            scope="application",
            action="access",
            resource="browser",
            allowed=True
        ))
        
        logger.info(f"Permission layer initialized with {len(self.rules)} rules")
    
    def check_permission(
        self,
        scope: str,
        action: str,
        resource: str,
    ) -> bool:
        """
        Check if an action is permitted.
        
        Args:
            scope: Operation scope
            action: Action type
            resource: Resource identifier
            
        Returns:
            True if permitted, False otherwise
        """
        for rule in self.rules:
            if rule.scope == scope and rule.action == action:
                # Simple pattern matching
                if self._matches_pattern(resource, rule.resource):
                    return rule.allowed
        
        # Default deny
        logger.warning(f"Permission denied: {scope}/{action} on {resource}")
        return False
    
    def _matches_pattern(self, resource: str, pattern: str) -> bool:
        """Check if resource matches rule pattern.
        
        Supports wildcard * at end of pattern.
        Pattern 'echo:*' matches 'echo hello' (colon acts as space separator).
        Pattern 'git:*' matches 'git status', 'git log', etc.
        """
        if pattern.endswith("*"):
            prefix = pattern[:-1]  # e.g. "echo:" or "git:"
            # Match exact prefix (with colon) OR prefix-with-space
            # e.g. "echo:" prefix matches "echo hello" and "echo:hello"
            if resource.startswith(prefix):
                return True
            # Also match if prefix without colon + space matches
            if ":" in prefix:
                space_prefix = prefix.rstrip(":")
                if resource == space_prefix or resource.startswith(space_prefix + " "):
                    return True
            return False
        return resource == pattern
    
    def add_rule(self, rule: PermissionRule):
        """Add a permission rule."""
        self.rules.append(rule)
        logger.info(f"Added permission rule: {rule.scope}/{rule.action} on {rule.resource}")
    
    def validate_filesystem_path(self, path: str) -> bool:
        """Validate filesystem path is within workspace scope."""
        try:
            resolved = Path(path).resolve()
            return str(resolved).startswith(str(self._workspace_root))
        except Exception:
            return False
    
    def validate_command(self, command: str) -> bool:
        """Validate terminal command is safe."""
        # Block dangerous commands
        blocked = ["rm -rf", "sudo", "chmod 777", "> /dev/", "mkfs"]
        return not any(b in command for b in blocked)
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all permission rules."""
        return [
            {"scope": r.scope, "action": r.action, "resource": r.resource, "allowed": r.allowed}
            for r in self.rules
        ]


def get_permission_layer() -> PermissionLayer:
    """Get singleton PermissionLayer instance."""
    if PermissionLayer._instance is None:
        PermissionLayer._instance = PermissionLayer()
    return PermissionLayer._instance