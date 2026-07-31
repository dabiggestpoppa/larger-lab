"""
OCE Desktop Control API
========================
FastAPI server exposing desktop control as HTTP endpoints for OpenClaw agents.

Run: python tools/operator/desktop_api.py
Port: 8001 (separate from OCE backend on 8000)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

import importlib
import os as _os

_op_dir = _os.path.dirname(_os.path.abspath(__file__))
_dc_spec = importlib.util.spec_from_file_location(
    "desktop_control", _os.path.join(_op_dir, "desktop-control.py")
)
_dc_mod = importlib.util.module_from_spec(_dc_spec)
_dc_spec.loader.exec_module(_dc_mod)
DesktopController = _dc_mod.DesktopController
ScreenRegion = _dc_mod.ScreenRegion

app = FastAPI(
    title="OCE Desktop Control API",
    description="Desktop control layer for OpenClaw Operator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dc = DesktopController()


# ─── Models ──────────────────────────────────────────────────────────────────

class ScreenshotRequest(BaseModel):
    region: Optional[Dict[str, int]] = None  # {x, y, width, height}

class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"
    double: bool = False

class TypeRequest(BaseModel):
    text: str
    interval: float = 0.02

class HotkeyRequest(BaseModel):
    keys: List[str]

class ScrollRequest(BaseModel):
    direction: str = "down"
    amount: int = 3

class DragRequest(BaseModel):
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    duration: float = 0.5

class FindWindowRequest(BaseModel):
    title: str

class FocusWindowRequest(BaseModel):
    title: str

class FindTemplateRequest(BaseModel):
    template_path: str
    threshold: float = 0.8


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "OCE Desktop Control API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "screen": dc.screen.get_screen_size()}


@app.post("/desktop/screenshot")
async def screenshot(req: ScreenshotRequest):
    """Take a screenshot. Optionally pass region {x, y, width, height}."""
    try:
        result = dc.screenshot(req.region)
        return {"ok": True, "path": result.path, "width": result.width, "height": result.height}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/click")
async def click(req: ClickRequest):
    """Click at screen coordinates."""
    try:
        dc.click(req.x, req.y, req.button, req.double)
        return {"ok": True, "action": "click", "x": req.x, "y": req.y}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/type")
async def type_text(req: TypeRequest):
    """Type text at current cursor position."""
    try:
        dc.type(req.text, req.interval)
        return {"ok": True, "action": "type", "length": len(req.text)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/hotkey")
async def hotkey(req: HotkeyRequest):
    """Press a keyboard shortcut (e.g., ['control', 's'])."""
    try:
        dc.hotkey(*req.keys)
        return {"ok": True, "action": "hotkey", "keys": req.keys}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/scroll")
async def scroll(req: ScrollRequest):
    """Scroll the mouse wheel."""
    try:
        dc.scroll(req.direction, req.amount)
        return {"ok": True, "action": "scroll", "direction": req.direction}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/drag")
async def drag(req: DragRequest):
    """Drag from one point to another."""
    try:
        dc.drag(req.from_x, req.from_y, req.to_x, req.to_y, req.duration)
        return {"ok": True, "action": "drag"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/desktop/windows")
async def list_windows():
    """List all visible windows."""
    try:
        windows = dc.list_windows()
        return {"ok": True, "windows": windows, "count": len(windows)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/window/find")
async def find_window(req: FindWindowRequest):
    """Find a window by title substring."""
    try:
        win = dc.find_window(req.title)
        if win:
            return {"ok": True, "window": win}
        return {"ok": False, "error": f"Window not found: {req.title}"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/window/focus")
async def focus_window(req: FocusWindowRequest):
    """Find and focus a window by title."""
    try:
        ok = dc.focus_window(req.title)
        return {"ok": ok, "focused": req.title if ok else None}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/find")
async def find_template(req: FindTemplateRequest):
    """Find a template image on screen."""
    try:
        matches = dc.find_on_screen(req.template_path, req.threshold)
        return {"ok": True, "matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/desktop/wait")
async def wait_for(req: FindTemplateRequest):
    """Wait for a template to appear on screen (polls every 0.5s, max 10s)."""
    import time
    try:
        for _ in range(20):
            matches = dc.find_on_screen(req.template_path, req.threshold)
            if matches:
                return {"ok": True, "matches": matches, "found": True}
            time.sleep(0.5)
        return {"ok": True, "matches": [], "found": False, "timeout": True}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── VS Code Bridge ───────────────────────────────────────────────────────

from vscode_bridge import VSCodeBridge

vscode = VSCodeBridge()


# ─── VS Code Models ─────────────────────────────────────────────────────────

class VSCodeOpenRequest(BaseModel):
    path: str
    line: Optional[int] = None

class VSCodeFolderRequest(BaseModel):
    path: str

class VSCodeTerminalRequest(BaseModel):
    command: str

class VSCodeExtensionRequest(BaseModel):
    extension_id: str

class VSCodeGitRequest(BaseModel):
    action: str  # status, commit, push, pull, log, diff, branch
    message: Optional[str] = None


# ─── VS Code Endpoints ──────────────────────────────────────────────────────

@app.post("/vscode/open")
async def vscode_open(req: VSCodeOpenRequest):
    """Open a file in VS Code."""
    try:
        result = vscode.open_file(req.path, req.line)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/folder")
async def vscode_folder(req: VSCodeFolderRequest):
    """Open a folder/workspace in VS Code."""
    try:
        result = vscode.open_folder(req.path)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/save")
async def vscode_save():
    """Save the current file."""
    try:
        result = vscode.save_file()
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/close")
async def vscode_close():
    """Close the current editor tab."""
    try:
        result = vscode.close_file()
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/terminal")
async def vscode_terminal(req: VSCodeTerminalRequest):
    """Open terminal and run a command."""
    try:
        result = vscode.run_in_terminal(req.command)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/extension/install")
async def vscode_install_extension(req: VSCodeExtensionRequest):
    """Install a VS Code extension."""
    try:
        result = vscode.install_extension(req.extension_id)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/vscode/git")
async def vscode_git(req: VSCodeGitRequest):
    """Git operations via VS Code terminal."""
    try:
        action = req.action.lower()
        if action == "status":
            result = vscode.git_status()
        elif action == "commit":
            if not req.message:
                raise HTTPException(400, "Commit requires a message")
            result = vscode.git_commit(req.message)
        elif action == "push":
            result = vscode.git_push()
        elif action == "pull":
            result = vscode.git_pull()
        elif action == "log":
            result = vscode.git_log()
        elif action == "diff":
            result = vscode.git_diff()
        elif action == "branch":
            result = vscode.git_branch()
        else:
            raise HTTPException(400, f"Unknown git action: {req.action}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/vscode/status")
async def vscode_status():
    """Get VS Code status (active file, workspace info)."""
    try:
        active = vscode.get_active_file()
        workspaces = vscode.get_workspace_folders()
        extensions = vscode.list_extensions()
        return {
            "ok": True,
            "active_file": active,
            "workspaces": workspaces,
            "extensions_count": extensions.get("count", 0),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── System Operator ──────────────────────────────────────────────────────

from system_operator import SystemOperator

sysop = SystemOperator()


# ─── System Models ──────────────────────────────────────────────────────────

class ProcessFilterRequest(BaseModel):
    filter: Optional[str] = None

class ProcessKillRequest(BaseModel):
    pid: Optional[int] = None
    name: Optional[str] = None

class ProcessStartRequest(BaseModel):
    command: str
    detached: bool = True

class PackageRequest(BaseModel):
    package: str
    manager: str = "pip"

class EnvSetRequest(BaseModel):
    name: str
    value: str

class ServiceControlRequest(BaseModel):
    name: str
    action: str  # start, stop

class PingRequest(BaseModel):
    host: str
    count: int = 4

class PortCheckRequest(BaseModel):
    host: str
    port: int


# ─── System Endpoints ───────────────────────────────────────────────────────

@app.get("/system/processes")
async def system_processes(filter: Optional[str] = None):
    """List running processes. Optional ?filter=name."""
    try:
        procs = sysop.processes.list_processes(filter)
        return {"ok": True, "processes": procs, "count": len(procs)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/process/kill")
async def system_kill_process(req: ProcessKillRequest):
    """Kill a process by PID or name."""
    try:
        result = sysop.processes.kill_process(pid=req.pid, name=req.name)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/process/start")
async def system_start_process(req: ProcessStartRequest):
    """Start a new process."""
    try:
        result = sysop.processes.start_process(req.command, req.detached)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/packages")
async def system_packages(manager: str = "pip"):
    """List installed packages (pip or npm)."""
    try:
        pkgs = sysop.packages.list_packages(manager)
        return {"ok": True, "packages": pkgs, "count": len(pkgs), "manager": manager}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/package/install")
async def system_install_package(req: PackageRequest):
    """Install a package via pip or npm."""
    try:
        result = sysop.packages.install_package(req.package, req.manager)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/env")
async def system_env():
    """Get environment variables."""
    try:
        env = sysop.environment.get_env_vars()
        return {"ok": True, "env": env, "count": len(env)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/env/set")
async def system_set_env(req: EnvSetRequest):
    """Set an environment variable (user scope)."""
    try:
        result = sysop.environment.set_env_var(req.name, req.value)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/info")
async def system_info():
    """Get system info (OS, CPU, memory)."""
    try:
        info = sysop.environment.get_system_info()
        return {"ok": True, "info": info}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/disk")
async def system_disk():
    """Get disk usage per drive."""
    try:
        disks = sysop.environment.get_disk_usage()
        return {"ok": True, "disks": disks}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/services")
async def system_services(filter: Optional[str] = None):
    """List Windows services. Optional ?filter=name."""
    try:
        services = sysop.services.list_services(filter)
        return {"ok": True, "services": services, "count": len(services)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/service/control")
async def system_service_control(req: ServiceControlRequest):
    """Start or stop a Windows service."""
    try:
        if req.action == "start":
            result = sysop.services.start_service(req.name)
        elif req.action == "stop":
            result = sysop.services.stop_service(req.name)
        else:
            raise HTTPException(400, f"Unknown action: {req.action}. Use 'start' or 'stop'.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/system/network")
async def system_network():
    """Get network info (IP addresses, interfaces)."""
    try:
        info = sysop.network.get_network_info()
        return {"ok": True, "network": info}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/ping")
async def system_ping(req: PingRequest):
    """Ping a host."""
    try:
        result = sysop.network.ping(req.host, req.count)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/system/port/check")
async def system_check_port(req: PortCheckRequest):
    """Check if a port is open on a host."""
    try:
        result = sysop.network.check_port(req.host, req.port)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
