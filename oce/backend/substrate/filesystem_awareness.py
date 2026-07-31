"""
O-6: Filesystem Awareness — Workspace Memory
============================================

Structured machine memory awareness for workspace operations.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger("oce.substrate.filesystem_awareness")


@dataclass
class FileNode:
    """Represents a file or directory in workspace."""
    path: str
    name: str
    type: str  # "file" or "directory"
    size: int = 0
    modified: str = ""
    lineage: List[str] = None
    
    def __post_init__(self):
        if self.lineage is None:
            self.lineage = []


class FilesystemAwareness:
    """
    Structured machine memory awareness.
    
    Tracks:
    - Repositories
    - Active projects
    - Workflow directories
    - Generated outputs
    - Orchestration artifacts
    - Operational lineage
    
    Features:
    - Scoped access
    - Change tracking
    - File lineage
    - Workspace awareness
    """
    
    _instance: Optional["FilesystemAwareness"] = None
    
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or Path.cwd())
        self._file_index: Dict[str, FileNode] = {}
        self._change_log: List[Dict[str, Any]] = []
    
    async def scan_workspace(self) -> Dict[str, Any]:
        """Scan workspace for all tracked paths."""
        files = []
        for path in self.workspace_root.rglob("*"):
            if path.is_file() and not str(path).endswith((".pyc", "__pycache__")):
                stat = path.stat()
                node = FileNode(
                    path=str(path),
                    name=path.name,
                    type="file",
                    size=stat.st_size,
                )
                self._file_index[str(path)] = node
                files.append(node.__dict__)
        
        logger.info(f"Scanned workspace: {len(files)} files")
        return {"files": files, "total": len(files)}
    
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute filesystem operation."""
        operation = payload.get("operation")
        
        if operation == "list":
            return await self._list_directory(payload.get("path", str(self.workspace_root)))
        elif operation == "read":
            return await self._read_file(payload.get("path", ""))
        elif operation == "write":
            return await self._write_file(payload.get("path", ""), payload.get("content", ""))
        elif operation == "search":
            return await self._search_files(payload.get("pattern", ""))
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents."""
        from .permission_layer import get_permission_layer
        pl = get_permission_layer()
        
        if not pl.validate_filesystem_path(path):
            return {"error": "Path not in workspace scope"}
        
        p = Path(path)
        if not p.exists():
            return {"error": "Path not found"}
        
        items = []
        for item in p.iterdir():
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else 0,
            })
        
        return {"items": items, "path": path}
    
    async def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents."""
        from .permission_layer import get_permission_layer
        pl = get_permission_layer()
        
        if not pl.validate_filesystem_path(path):
            return {"error": "Path not in workspace scope"}
        
        p = Path(path)
        if not p.exists():
            return {"error": "File not found"}
        
        return {"content": p.read_text(), "path": path}
    
    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file contents."""
        from .permission_layer import get_permission_layer
        pl = get_permission_layer()
        
        if not pl.validate_filesystem_path(path):
            return {"error": "Path not in workspace scope"}
        
        p = Path(path)
        p.write_text(content)
        
        self._change_log.append({
            "path": path,
            "operation": "write",
            "timestamp": str(Path(path).stat().st_mtime),
        })
        
        return {"status": "written", "path": path}
    
    async def _search_files(self, pattern: str) -> Dict[str, Any]:
        """Search for files matching pattern."""
        matches = []
        for path in self.workspace_root.rglob(pattern):
            if path.is_file():
                matches.append(str(path))
        
        return {"matches": matches, "pattern": pattern}
    
    def get_workspace_topology(self) -> Dict[str, Any]:
        """Get workspace as topology graph."""
        nodes = []
        edges = []
        
        for path in self.workspace_root.rglob("*"):
            if path.is_file() and not str(path).endswith((".pyc", "__pycache__")):
                rel_path = path.relative_to(self.workspace_root)
                nodes.append({
                    "id": str(path),
                    "name": path.name,
                    "path": str(path),
                    "type": "file",
                })
                
                # Add parent relationship
                if len(rel_path.parts) > 1:
                    parent = str(path.parent)
                    edges.append({"source": parent, "target": str(path)})
        
        return {"nodes": nodes, "edges": edges}


def get_filesystem_awareness() -> FilesystemAwareness:
    """Get singleton FilesystemAwareness instance."""
    if FilesystemAwareness._instance is None:
        FilesystemAwareness._instance = FilesystemAwareness()
    return FilesystemAwareness._instance