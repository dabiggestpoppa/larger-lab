"""
OCE System Operator — Phase C
==============================
Windows-native system-level operations: processes, packages, environment,
services, scheduled tasks, network.

Uses:
- psutil (if available) for process/system info, with PowerShell fallback
- subprocess for running system commands
- sc.exe for Windows services
- schtasks.exe for scheduled tasks
- pip / npm for package management
"""

import subprocess
import json
import os
import sys
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# ─── psutil availability ─────────────────────────────────────────────────────

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _run(cmd: str, timeout: int = 30, shell: bool = True,
         capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command, return CompletedProcess. Raises on non-zero if check=True."""
    return subprocess.run(
        cmd, shell=shell, capture_output=capture,
        text=True, timeout=timeout, encoding="utf-8", errors="replace",
    )


def _ps(cmd: str, timeout: int = 30) -> str:
    """Run a PowerShell command, return stdout."""
    r = _run(f'powershell -NoProfile -Command "{cmd}"', timeout=timeout)
    return r.stdout.strip()


def _json_ps(cmd: str, timeout: int = 30) -> Any:
    """Run a PowerShell command that outputs JSON, return parsed object."""
    r = _run(f'powershell -NoProfile -Command "{cmd} | ConvertTo-Json"', timeout=timeout)
    if r.returncode == 0 and r.stdout.strip():
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return r.stdout.strip()
    return None


# ─── Process Management ─────────────────────────────────────────────────────

class ProcessManager:
    """List, kill, start, and inspect processes."""

    @staticmethod
    def list_processes(filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if HAS_PSUTIL:
            procs = []
            for p in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
                try:
                    info = p.info
                    name = info.get("name", "")
                    if filter_name and filter_name.lower() not in name.lower():
                        continue
                    mem = info.get("memory_info")
                    procs.append({
                        "pid": info["pid"],
                        "name": name,
                        "memory_mb": round(mem.rss / (1024 * 1024), 1) if mem else 0,
                        "cpu_percent": info.get("cpu_percent", 0.0),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return sorted(procs, key=lambda x: x["memory_mb"], reverse=True)
        else:
            cmd = "Get-Process | Select-Object Id, ProcessName, @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, CPU | ConvertToJson"
            if filter_name:
                cmd = (
                    f"Get-Process -Name '*{filter_name}*' -ErrorAction SilentlyContinue "
                    f"| Select-Object Id, ProcessName, @{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,1)}}}}, CPU "
                    f"| ConvertTo-Json"
                )
            result = _json_ps(cmd)
            if result is None:
                return []
            if isinstance(result, dict):
                result = [result]
            return [
                {
                    "pid": p.get("Id", 0),
                    "name": p.get("ProcessName", ""),
                    "memory_mb": p.get("MemoryMB", 0),
                    "cpu_percent": round(p.get("CPU", 0.0), 1),
                }
                for p in result
            ]

    @staticmethod
    def kill_process(pid: Optional[int] = None, name: Optional[str] = None) -> Dict[str, Any]:
        if pid:
            if HAS_PSUTIL:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    return {"ok": True, "pid": pid, "name": p.name()}
                except psutil.NoSuchProcess:
                    return {"ok": False, "error": f"No process with PID {pid}"}
                except psutil.AccessDenied:
                    return {"ok": False, "error": f"Access denied for PID {pid}"}
            else:
                r = _run(f"taskkill /PID {pid} /F")
                return {"ok": r.returncode == 0, "pid": pid,
                        "error": r.stderr if r.returncode != 0 else None}
        elif name:
            if HAS_PSUTIL:
                killed = []
                for p in psutil.process_iter(["pid", "name"]):
                    if name.lower() in (p.info["name"] or "").lower():
                        try:
                            p.terminate()
                            killed.append({"pid": p.info["pid"], "name": p.info["name"]})
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                return {"ok": len(killed) > 0, "killed": killed}
            else:
                r = _run(f'taskkill /IM "{name}" /F')
                return {"ok": r.returncode == 0, "name": name,
                        "error": r.stderr if r.returncode != 0 else None}
        else:
            return {"ok": False, "error": "Need pid or name"}

    @staticmethod
    def start_process(command: str, detached: bool = True) -> Dict[str, Any]:
        try:
            if detached:
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                p = subprocess.Popen(command, creationflags=flags,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p = subprocess.Popen(command, shell=True)
            return {"ok": True, "pid": p.pid, "command": command}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def get_process_info(pid: int) -> Dict[str, Any]:
        if HAS_PSUTIL:
            try:
                p = psutil.Process(pid)
                return {
                    "ok": True,
                    "pid": pid,
                    "name": p.name(),
                    "status": p.status(),
                    "cpu_percent": p.cpu_percent(),
                    "memory_mb": round(p.memory_info().rss / (1024 * 1024), 1),
                    "create_time": datetime.fromtimestamp(p.create_time()).isoformat(),
                    "exe": p.exe(),
                    "cmdline": p.cmdline(),
                }
            except psutil.NoSuchProcess:
                return {"ok": False, "error": f"No process with PID {pid}"}
            except psutil.AccessDenied:
                return {"ok": False, "error": f"Access denied for PID {pid}"}
        else:
            cmd = (
                f"Get-Process -Id {pid} -ErrorAction SilentlyContinue "
                f"| Select-Object Id, ProcessName, Status, "
                f"@{{N='MemoryMB';E={{[math]::Round($_.WorkingSet64/1MB,1)}}}}, "
                f"StartTime, Path, CommandLine | ConvertTo-Json"
            )
            result = _json_ps(cmd)
            if result:
                return {"ok": True, "pid": pid,
                        "name": result.get("ProcessName", ""),
                        "status": result.get("Status", ""),
                        "memory_mb": result.get("MemoryMB", 0),
                        "create_time": result.get("StartTime", ""),
                        "exe": result.get("Path", ""),
                        "cmdline": result.get("CommandLine", "")}
            return {"ok": False, "error": f"No process with PID {pid}"}

    @staticmethod
    def is_running(name: str) -> bool:
        if HAS_PSUTIL:
            for p in psutil.process_iter(["name"]):
                try:
                    if name.lower() in (p.info["name"] or "").lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        else:
            r = _run(f'powershell -NoProfile -Command "Get-Process -Name \'*{name}*\' -ErrorAction SilentlyContinue | Select-Object -First 1"')
            return bool(r.stdout.strip())


# ─── Package Management ──────────────────────────────────────────────────────

class PackageManager:
    """Install, update, uninstall, search packages via pip and npm."""

    @staticmethod
    def list_packages(manager: str = "pip") -> List[Dict[str, str]]:
        if manager == "pip":
            r = _run("pip list --format=json")
            if r.returncode == 0:
                try:
                    pkgs = json.loads(r.stdout)
                    return [{"name": p["name"], "version": p["version"]} for p in pkgs]
                except (json.JSONDecodeError, KeyError):
                    return []
            return []
        elif manager == "npm":
            r = _run("npm list -g --json", timeout=15)
            if r.returncode == 0:
                try:
                    data = json.loads(r.stdout)
                    deps = data.get("dependencies", {})
                    result = []
                    for name, info in deps.items():
                        result.append({"name": name, "version": info.get("version", "unknown")})
                    return result
                except (json.JSONDecodeError, KeyError):
                    return []
            return []
        else:
            return []

    @staticmethod
    def install_package(package: str, manager: str = "pip") -> Dict[str, Any]:
        if manager == "pip":
            r = _run(f"pip install {package}", timeout=120)
        elif manager == "npm":
            r = _run(f"npm install -g {package}", timeout=120)
        else:
            return {"ok": False, "error": f"Unknown manager: {manager}"}
        return {"ok": r.returncode == 0, "package": package, "manager": manager,
                "stdout": r.stdout[-500:] if r.stdout else "",
                "stderr": r.stderr[-500:] if r.stderr else ""}

    @staticmethod
    def uninstall_package(package: str, manager: str = "pip") -> Dict[str, Any]:
        if manager == "pip":
            r = _run(f"pip uninstall -y {package}", timeout=60)
        elif manager == "npm":
            r = _run(f"npm uninstall -g {package}", timeout=60)
        else:
            return {"ok": False, "error": f"Unknown manager: {manager}"}
        return {"ok": r.returncode == 0, "package": package, "manager": manager,
                "stderr": r.stderr[-500:] if r.stderr else ""}

    @staticmethod
    def update_package(package: str, manager: str = "pip") -> Dict[str, Any]:
        if manager == "pip":
            r = _run(f"pip install --upgrade {package}", timeout=120)
        elif manager == "npm":
            r = _run(f"npm update -g {package}", timeout=120)
        else:
            return {"ok": False, "error": f"Unknown manager: {manager}"}
        return {"ok": r.returncode == 0, "package": package, "manager": manager,
                "stdout": r.stdout[-500:] if r.stdout else ""}

    @staticmethod
    def search_package(query: str, manager: str = "pip") -> List[Dict[str, str]]:
        if manager == "pip":
            r = _run(f"pip search {query}", timeout=30)
            # pip search is often disabled; fall back to index
            if r.returncode != 0:
                return []
            results = []
            for line in r.stdout.strip().split("\n"):
                if " " in line:
                    parts = line.split(" ", 1)
                    results.append({"name": parts[0].strip(), "summary": parts[1].strip()})
            return results
        elif manager == "npm":
            r = _run(f"npm search {query} --json", timeout=30)
            if r.returncode == 0:
                try:
                    data = json.loads(r.stdout)
                    return [{"name": p.get("name", ""), "summary": p.get("description", "")}
                            for p in data[:20]]
                except json.JSONDecodeError:
                    return []
            return []
        return []


# ─── Environment Management ──────────────────────────────────────────────────

class EnvironmentManager:
    """Environment variables, system info, disk usage."""

    @staticmethod
    def get_env_vars() -> Dict[str, str]:
        return dict(os.environ)

    @staticmethod
    def set_env_var(name: str, value: str, scope: str = "user") -> Dict[str, Any]:
        try:
            if scope == "user":
                _run(f'setx {name} "{value}"')
            elif scope == "machine":
                _run(f'setx {name} "{value}" /M')
            else:
                os.environ[name] = value
            return {"ok": True, "name": name, "scope": scope}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        info = {
            "os": sys.platform,
            "python_version": sys.version,
            "hostname": os.environ.get("COMPUTERNAME", ""),
            "username": os.environ.get("USERNAME", ""),
            "cpu_count": os.cpu_count(),
        }
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            info.update({
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_total_gb": round(mem.total / (1024**3), 1),
                "memory_used_gb": round(mem.used / (1024**3), 1),
                "memory_percent": mem.percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            })
        else:
            result = _json_ps(
                "Get-CimInstance Win32_OperatingSystem "
                "| Select-Object @{{N='TotalGB';E={{[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}}}, "
                "@{{N='FreeGB';E={{[math]::Round($_.FreePhysicalMemory/1MB,1)}}}}, "
                "@{{N='UsedPercent';E={{[math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,1)}}}} "
                "| ConvertTo-Json"
            )
            if result:
                total = result.get("TotalGB", 0)
                free = result.get("FreeGB", 0)
                info.update({
                    "memory_total_gb": total,
                    "memory_used_gb": round(total - free, 1),
                    "memory_percent": result.get("UsedPercent", 0),
                })
        return info

    @staticmethod
    def get_disk_usage() -> List[Dict[str, Any]]:
        if HAS_PSUTIL:
            drives = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    drives.append({
                        "drive": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": usage.percent,
                    })
                except PermissionError:
                    continue
            return drives
        else:
            result = _json_ps(
                "Get-PSDrive -PSProvider FileSystem "
                "| Select-Object Name, @{{N='UsedGB';E={{[math]::Round($_.Used/1GB,1)}}}}, "
                "@{{N='FreeGB';E={{[math]::Round($_.Free/1GB,1)}}}}, "
                "@{{N='TotalGB';E={{[math]::Round(($_.Used+$_.Free)/1GB,1)}}}} "
                "| ConvertTo-Json"
            )
            if result is None:
                return []
            if isinstance(result, dict):
                result = [result]
            return [
                {
                    "drive": d.get("Name", ""),
                    "mountpoint": d.get("Name", "") + ":\\",
                    "total_gb": d.get("TotalGB", 0),
                    "used_gb": d.get("UsedGB", 0),
                    "free_gb": d.get("FreeGB", 0),
                    "percent": round(d.get("UsedGB", 0) / d.get("TotalGB", 1) * 100, 1),
                }
                for d in result
            ]


# ─── Service Management ──────────────────────────────────────────────────────

class ServiceManager:
    """Windows service control via sc.exe."""

    @staticmethod
    def list_services(filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
        cmd = "Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
        if filter_name:
            cmd = (
                f"Get-Service -Name '*{filter_name}*' -ErrorAction SilentlyContinue "
                f"| Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
            )
        result = _json_ps(cmd)
        if result is None:
            return []
        if isinstance(result, str):
            return []
        if isinstance(result, dict):
            result = [result]
        if not isinstance(result, list):
            return []
        return [
            {
                "name": s.get("Name", ""),
                "display_name": s.get("DisplayName", ""),
                "status": str(s.get("Status", "")),
                "start_type": str(s.get("StartType", "")),
            }
            for s in result
        ]

    @staticmethod
    def start_service(name: str) -> Dict[str, Any]:
        r = _run(f"net start {name}")
        return {"ok": r.returncode == 0, "name": name, "action": "start",
                "output": r.stdout, "error": r.stderr if r.returncode != 0 else None}

    @staticmethod
    def stop_service(name: str) -> Dict[str, Any]:
        r = _run(f"net stop {name}")
        return {"ok": r.returncode == 0, "name": name, "action": "stop",
                "output": r.stdout, "error": r.stderr if r.returncode != 0 else None}

    @staticmethod
    def get_service_status(name: str) -> Dict[str, Any]:
        cmd = (
            f"Get-Service -Name '{name}' -ErrorAction SilentlyContinue "
            f"| Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
        )
        result = _json_ps(cmd)
        if result:
            return {"ok": True, "name": result.get("Name", ""),
                    "display_name": result.get("DisplayName", ""),
                    "status": str(result.get("Status", "")),
                    "start_type": str(result.get("StartType", ""))}
        return {"ok": False, "error": f"Service not found: {name}"}


# ─── Scheduled Tasks ─────────────────────────────────────────────────────────

class TaskScheduler:
    """Windows scheduled tasks via schtasks.exe."""

    @staticmethod
    def list_scheduled_tasks() -> List[Dict[str, Any]]:
        r = _run('schtasks /query /fo LIST /v')
        if r.returncode != 0:
            return []
        tasks = []
        current = {}
        for line in r.stdout.split("\n"):
            line = line.strip()
            if not line:
                if current.get("task_name"):
                    tasks.append(current)
                current = {}
                continue
            if ": " in line:
                key, val = line.split(": ", 1)
                key = key.strip().lower().replace(" ", "_")
                current[key] = val.strip()
        if current.get("task_name"):
            tasks.append(current)
        return tasks

    @staticmethod
    def create_scheduled_task(name: str, command: str,
                              trigger: str = "DAILY") -> Dict[str, Any]:
        r = _run(f'schtasks /create /tn "{name}" /tr "{command}" /sc {trigger} /f')
        return {"ok": r.returncode == 0, "name": name, "trigger": trigger,
                "error": r.stderr if r.returncode != 0 else None}

    @staticmethod
    def delete_scheduled_task(name: str) -> Dict[str, Any]:
        r = _run(f'schtasks /delete /tn "{name}" /f')
        return {"ok": r.returncode == 0, "name": name,
                "error": r.stderr if r.returncode != 0 else None}

    @staticmethod
    def run_scheduled_task(name: str) -> Dict[str, Any]:
        r = _run(f'schtasks /run /tn "{name}"')
        return {"ok": r.returncode == 0, "name": name,
                "error": r.stderr if r.returncode != 0 else None}


# ─── Network ─────────────────────────────────────────────────────────────────

class NetworkManager:
    """Network info, ping, port checks."""

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        info = {"hostname": os.environ.get("COMPUTERNAME", ""), "interfaces": []}
        if HAS_PSUTIL:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for iface, addr_list in addrs.items():
                iface_info = {"name": iface, "addresses": []}
                if iface in stats:
                    s = stats[iface]
                    iface_info["is_up"] = s.isup
                    iface_info["speed_mbps"] = s.speed
                for addr in addr_list:
                    if addr.family.name == "AF_INET":
                        iface_info["addresses"].append({
                            "type": "ipv4",
                            "address": addr.address,
                            "netmask": addr.netmask,
                        })
                    elif addr.family.name == "AF_INET6":
                        iface_info["addresses"].append({
                            "type": "ipv6",
                            "address": addr.address,
                        })
                info["interfaces"].append(iface_info)
        else:
            result = _json_ps(
                "Get-NetIPAddress -AddressFamily IPv4 "
                "| Select-Object InterfaceAlias, IPAddress, PrefixLength "
                "| ConvertTo-Json"
            )
            if result:
                if isinstance(result, dict):
                    result = [result]
                info["interfaces"] = [
                    {"name": r.get("InterfaceAlias", ""),
                     "addresses": [{"type": "ipv4", "address": r.get("IPAddress", ""),
                                    "netmask": str(r.get("PrefixLength", ""))}]}
                    for r in result
                ]
        return info

    @staticmethod
    def ping(host: str, count: int = 4) -> Dict[str, Any]:
        r = _run(f"ping -n {count} {host}", timeout=count * 5 + 10)
        return {"ok": r.returncode == 0, "host": count, "output": r.stdout}

    @staticmethod
    def check_port(host: str, port: int) -> Dict[str, Any]:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return {"ok": result == 0, "host": host, "port": port,
                    "open": result == 0}
        except Exception as e:
            return {"ok": False, "host": host, "port": port, "error": str(e)}


# ─── System Operator (Facade) ────────────────────────────────────────────────

class SystemOperator:
    """Unified system operator — facade over all subsystems."""

    def __init__(self):
        self.processes = ProcessManager()
        self.packages = PackageManager()
        self.environment = EnvironmentManager()
        self.services = ServiceManager()
        self.scheduler = TaskScheduler()
        self.network = NetworkManager()

    def summary(self) -> Dict[str, Any]:
        """Quick system summary."""
        info = self.environment.get_system_info()
        disks = self.environment.get_disk_usage()
        return {"system": info, "disks": disks, "psutil": HAS_PSUTIL}


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="OCE System Operator")
    sub = parser.add_subparsers(dest="command")

    # ── processes ──
    p = sub.add_parser("processes", help="List processes")
    p.add_argument("--filter", help="Filter by name")

    p = sub.add_parser("kill", help="Kill a process")
    p.add_argument("--pid", type=int, help="Process ID")
    p.add_argument("--name", help="Process name")

    p = sub.add_parser("start", help="Start a process")
    p.add_argument("command_str", help="Command to run")
    p.add_argument("--no-detach", action="store_true")

    p = sub.add_parser("procinfo", help="Get process info")
    p.add_argument("pid", type=int)

    p = sub.add_parser("isrunning", help="Check if process is running")
    p.add_argument("name")

    # ── packages ──
    p = sub.add_parser("packages", help="List installed packages")
    p.add_argument("--manager", default="pip", choices=["pip", "npm"])

    p = sub.add_parser("install", help="Install a package")
    p.add_argument("package")
    p.add_argument("--manager", default="pip", choices=["pip", "npm"])

    p = sub.add_parser("uninstall", help="Uninstall a package")
    p.add_argument("package")
    p.add_argument("--manager", default="pip", choices=["pip", "npm"])

    p = sub.add_parser("update", help="Update a package")
    p.add_argument("package")
    p.add_argument("--manager", default="pip", choices=["pip", "npm"])

    p = sub.add_parser("search", help="Search for packages")
    p.add_argument("query")
    p.add_argument("--manager", default="pip", choices=["pip", "npm"])

    # ── environment ──
    p = sub.add_parser("env", help="Show environment variables")
    p.add_argument("--name", help="Show specific variable")

    p = sub.add_parser("setenv", help="Set environment variable")
    p.add_argument("name")
    p.add_argument("value")
    p.add_argument("--scope", default="user", choices=["user", "machine", "process"])

    p = sub.add_parser("info", help="System info")

    p = sub.add_parser("disk", help="Disk usage")

    # ── services ──
    p = sub.add_parser("services", help="List Windows services")
    p.add_argument("--filter", help="Filter by name")

    p = sub.add_parser("service-status", help="Get service status")
    p.add_argument("name")

    p = sub.add_parser("service-start", help="Start a service")
    p.add_argument("name")

    p = sub.add_parser("service-stop", help="Stop a service")
    p.add_argument("name")

    # ── scheduled tasks ──
    p = sub.add_parser("tasks", help="List scheduled tasks")

    p = sub.add_parser("task-create", help="Create a scheduled task")
    p.add_argument("name")
    p.add_argument("command_str")
    p.add_argument("--trigger", default="DAILY")

    p = sub.add_parser("task-delete", help="Delete a scheduled task")
    p.add_argument("name")

    p = sub.add_parser("task-run", help="Run a scheduled task")
    p.add_argument("name")

    # ── network ──
    p = sub.add_parser("network", help="Network info")

    p = sub.add_parser("ping", help="Ping a host")
    p.add_argument("host")
    p.add_argument("--count", type=int, default=4)

    p = sub.add_parser("port", help="Check if port is open")
    p.add_argument("host")
    p.add_argument("port", type=int)

    # ── summary ──
    sub.add_parser("summary", help="System summary")

    args = parser.parse_args()
    op = SystemOperator()

    if args.command == "processes":
        procs = op.processes.list_processes(args.filter)
        for p in procs[:50]:
            print(f"  {p['pid']:>7}  {p['name']:<40}  {p['memory_mb']:>8} MB  cpu={p['cpu_percent']}")
        print(f"\n  {len(procs)} processes total")

    elif args.command == "kill":
        result = op.processes.kill_process(pid=args.pid, name=args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "start":
        result = op.processes.start_process(args.command_str, detached=not args.no_detach)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "procinfo":
        result = op.processes.get_process_info(args.pid)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "isrunning":
        print(op.processes.is_running(args.name))

    elif args.command == "packages":
        pkgs = op.packages.list_packages(args.manager)
        for p in pkgs[:50]:
            print(f"  {p['name']:<40}  {p['version']}")
        print(f"\n  {len(pkgs)} packages")

    elif args.command == "install":
        result = op.packages.install_package(args.package, args.manager)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "uninstall":
        result = op.packages.uninstall_package(args.package, args.manager)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "update":
        result = op.packages.update_package(args.package, args.manager)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "search":
        results = op.packages.search_package(args.query, args.manager)
        for r in results[:20]:
            print(f"  {r['name']:<40}  {r.get('summary', '')}")

    elif args.command == "env":
        if args.name:
            val = op.environment.get_env_vars().get(args.name, "")
            print(f"{args.name}={val}")
        else:
            for k, v in sorted(op.environment.get_env_vars().items()):
                print(f"  {k}={v}")

    elif args.command == "setenv":
        result = op.environment.set_env_var(args.name, args.value, args.scope)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "info":
        info = op.environment.get_system_info()
        print(json.dumps(info, indent=2, default=str))

    elif args.command == "disk":
        disks = op.environment.get_disk_usage()
        for d in disks:
            print(f"  {d['drive']:<15}  total={d['total_gb']}GB  used={d['used_gb']}GB"
                  f"  free={d['free_gb']}GB  {d['percent']}%")

    elif args.command == "services":
        services = op.services.list_services(args.filter)
        for s in services[:50]:
            print(f"  {s['name']:<40}  {s['status']:<15}  {s['start_type']}")
        print(f"\n  {len(services)} services")

    elif args.command == "service-status":
        result = op.services.get_service_status(args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "service-start":
        result = op.services.start_service(args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "service-stop":
        result = op.services.stop_service(args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "tasks":
        tasks = op.scheduler.list_scheduled_tasks()
        for t in tasks[:30]:
            name = t.get("task_name", t.get("task_to_run", "?"))
            status = t.get("status", t.get("state", "?"))
            print(f"  {name:<50}  {status}")
        print(f"\n  {len(tasks)} tasks")

    elif args.command == "task-create":
        result = op.scheduler.create_scheduled_task(args.name, args.command_str, args.trigger)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "task-delete":
        result = op.scheduler.delete_scheduled_task(args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "task-run":
        result = op.scheduler.run_scheduled_task(args.name)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "network":
        info = op.network.get_network_info()
        print(json.dumps(info, indent=2, default=str))

    elif args.command == "ping":
        result = op.network.ping(args.host, args.count)
        print(result["output"])

    elif args.command == "port":
        result = op.network.check_port(args.host, args.port)
        state = "OPEN" if result.get("open") else "CLOSED"
        print(f"{args.host}:{args.port} — {state}")

    elif args.command == "summary":
        s = op.summary()
        print(json.dumps(s, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
