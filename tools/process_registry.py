"""
Process Registry — Single source of truth for all running services.

ALL agents MUST check this before starting any service.
Prevents duplicate processes, stale PIDs, and conflicting instances.

Usage:
    from tools.process_registry import ProcessRegistry
    reg = ProcessRegistry()
    
    # Before starting a service:
    if reg.is_running('po_telegram'):
        print("PO bot already running, skipping")
    else:
        reg.start_service('po_telegram', 'scripts/telegram_gateway.py')
    
    # Check status:
    status = reg.get_status()
    # {'po_telegram': {'pid': 12345, 'status': 'running', 'started': '...'}, ...}
    
    # Stop a service:
    reg.stop_service('po_telegram')
    
    # Stop all duplicates:
    reg.kill_duplicates('po_telegram')
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

REGISTRY_FILE = Path(__file__).resolve().parents[1] / "data" / "process_registry.json"
REPO_ROOT = Path(__file__).resolve().parents[1]

# ─── Service Definitions ────────────────────────────────────────────────────
# Each service has a unique name, script path, and port (if applicable).
# Agents MUST use these definitions — never hardcode paths.

SERVICES = {
    "po_telegram": {
        "script": "scripts/telegram_gateway.py",
        "port": None,
        "python": ".venv",
        "description": "PO Telegram Bot",
    },
    "srrs_api": {
        "script": "srrs_opc/frontend/api_server.py",
        "port": 8001,
        "python": ".venv",
        "description": "SRRA-OPH API Server",
    },
    "oce_backend": {
        "script": None,  # uvicorn, not a script
        "port": 8000,
        "python": "system",
        "description": "OCE FastAPI Backend",
        "command": ["uvicorn", "oce.backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
    },
    "oce_frontend": {
        "script": None,  # Next.js dev server
        "port": 3000,
        "python": None,
        "description": "OCE Frontend (Next.js)",
    },
    "srrs_frontend": {
        "script": None,  # Next.js dev server
        "port": 3001,
        "python": None,
        "description": "SRRA-OPH Frontend (Next.js)",
    },
    "oc2_gateway": {
        "script": None,  # OpenClaw gateway
        "port": 18790,
        "python": None,
        "description": "OC2 Gateway (OpenClaw)",
    },
}


class ProcessRegistry:
    """Central registry for all workspace services."""

    def __init__(self):
        self._lock = threading.Lock()
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if REGISTRY_FILE.exists():
            try:
                return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return {"services": {}, "last_updated": None}

    def _save(self):
        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            REGISTRY_FILE.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")
        except IOError:
            pass

    def _is_pid_alive(self, pid: int) -> bool:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def _find_processes(self, script_name: str) -> List[int]:
        """Find all PIDs running a specific script across all Python interpreters."""
        pids = []
        try:
            result = subprocess.run(
                ["wmic", "process", "where", f"commandline like '%{script_name}%'", "get", "processid"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.isdigit():
                    pids.append(int(line))
        except Exception:
            pass
        return pids

    def _find_port_processes(self, port: int) -> List[int]:
        """Find all PIDs listening on a specific port."""
        pids = []
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts:
                        try:
                            pids.append(int(parts[-1]))
                        except ValueError:
                            pass
        except Exception:
            pass
        return pids

    def is_running(self, service_name: str) -> bool:
        """Check if a service is actually running (not just in registry)."""
        if service_name not in SERVICES:
            return False

        svc = SERVICES[service_name]

        # Check by port if available
        if svc.get("port"):
            port_pids = self._find_port_processes(svc["port"])
            if port_pids:
                return True

        # Check by script name
        if svc.get("script"):
            script_pids = self._find_processes(svc["script"])
            if script_pids:
                return True

        # Check registry + PID alive
        with self._lock:
            entry = self._data["services"].get(service_name)
            if entry and entry.get("pid"):
                if self._is_pid_alive(entry["pid"]):
                    return True
                # Stale entry — clean it up
                del self._data["services"][service_name]
                self._save()

        return False

    def get_status(self) -> dict:
        """Get status of all services."""
        status = {}
        for name, svc in SERVICES.items():
            running = self.is_running(name)
            with self._lock:
                entry = self._data["services"].get(name, {})
            status[name] = {
                "name": name,
                "description": svc["description"],
                "running": running,
                "pid": entry.get("pid"),
                "started": entry.get("started"),
                "port": svc.get("port"),
            }
        return status

    def start_service(self, service_name: str, extra_args: list = None) -> bool:
        """Start a service if not already running. Returns True if started."""
        if self.is_running(service_name):
            return False

        if service_name not in SERVICES:
            return False

        svc = SERVICES[service_name]
        script = svc.get("script")

        if script:
            script_path = REPO_ROOT / script
            if not script_path.exists():
                return False

            # Determine Python interpreter
            if svc.get("python") == ".venv":
                python_exe = str(REPO_ROOT / ".venv" / "Scripts" / "python.exe")
            else:
                python_exe = sys.executable

            cmd = [python_exe, str(script_path)]
            if extra_args:
                cmd.extend(extra_args)

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                with self._lock:
                    self._data["services"][service_name] = {
                        "pid": proc.pid,
                        "started": datetime.now(timezone.utc).isoformat(),
                    }
                    self._save()
                return True
            except Exception:
                return False

        return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a service by PID."""
        with self._lock:
            entry = self._data["services"].get(service_name)
            if entry and entry.get("pid"):
                pid = entry["pid"]
                if self._is_pid_alive(pid):
                    try:
                        if sys.platform == "win32":
                            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
                        else:
                            os.kill(pid, signal.SIGTERM)
                    except Exception:
                        pass
                del self._data["services"][service_name]
                self._save()
                return True
        return False

    def kill_duplicates(self, service_name: str) -> int:
        """Kill all duplicate processes for a service. Returns count killed."""
        if service_name not in SERVICES:
            return 0

        svc = SERVICES[service_name]
        killed = 0

        # Find all processes running this script
        if svc.get("script"):
            pids = self._find_processes(svc["script"])
            for pid in pids:
                try:
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
                    else:
                        os.kill(pid, signal.SIGTERM)
                    killed += 1
                except Exception:
                    pass

        # Clean registry
        with self._lock:
            if service_name in self._data["services"]:
                del self._data["services"][service_name]
                self._save()

        return killed

    def cleanup_stale(self):
        """Remove stale entries from registry."""
        with self._lock:
            stale = []
            for name, entry in self._data["services"].items():
                if entry.get("pid") and not self._is_pid_alive(entry["pid"]):
                    stale.append(name)
            for name in stale:
                del self._data["services"][name]
            if stale:
                self._save()
            return stale


# ─── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process Registry")
    parser.add_argument("action", choices=["status", "start", "stop", "kill-dupes", "cleanup"])
    parser.add_argument("--service", "-s", help="Service name")
    args = parser.parse_args()

    reg = ProcessRegistry()

    if args.action == "status":
        status = reg.get_status()
        print(json.dumps(status, indent=2, default=str))

    elif args.action == "start":
        if not args.service:
            print("Error: --service required")
            sys.exit(1)
        if reg.is_running(args.service):
            print(f"{args.service} is already running")
        elif reg.start_service(args.service):
            print(f"Started {args.service}")
        else:
            print(f"Failed to start {args.service}")

    elif args.action == "stop":
        if not args.service:
            print("Error: --service required")
            sys.exit(1)
        if reg.stop_service(args.service):
            print(f"Stopped {args.service}")
        else:
            print(f"{args.service} not running")

    elif args.action == "kill-dupes":
        if not args.service:
            print("Error: --service required")
            sys.exit(1)
        count = reg.kill_duplicates(args.service)
        print(f"Killed {count} duplicate(s) for {args.service}")

    elif args.action == "cleanup":
        stale = reg.cleanup_stale()
        print(f"Cleaned {len(stale)} stale entries: {stale}")