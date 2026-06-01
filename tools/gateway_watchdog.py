"""
Gateway Watchdog — Keeps OC2 (OpenClaw) and Hermes gateways running 24/7.
Runs as a persistent loop. Intended to be launched at system startup via Task Scheduler.

Usage:
  python tools\gateway_watchdog.py          # Run foreground loop
  python tools\gateway_watchdog.py --check  # Single check + exit
  python tools\gateway_watchdog.py --install  # Register as Windows Scheduled Task at boot
"""

import subprocess
import time
import sys
import os
import json
import socket
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────

SERVICES = {
    "OC2": {
        "port": 18790,
        "cmd": [
            "node",
            r"C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs",
            "gateway", "run", "--port", "18790"
        ],
        "log": r"C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog-oc2.log",
        "stuck_check": True,   # Enable OC2-specific stuck session detection
    },
    "Hermes": {
        "port": 8642,
        "cmd": [
            r"C:\Users\wifik\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe",
            "gateway", "run"
        ],
        "log": r"C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog-hermes.log",
    },
    "OCE-Backend": {
        "port": 8000,
        "cmd": [
            "uvicorn", "oce.backend.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ],
        "log": r"C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog-oce-backend.log",
        "cwd": r"C:\Users\wifik\Desktop\projects\larger-lab",
        "env": {"PYTHONIOENCODING": "utf-8"},
    },
    "OCE-Frontend": {
        "port": 3000,
        "cmd": [
            "node",
            r"C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js",
            "run", "dev"
        ],
        "log": r"C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog-oce-frontend.log",
        "cwd": r"C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend",
    },
    "Sniper-Dashboard": {
        "port": 3001,
        "cmd": [
            "node",
            r"C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js",
            "run", "dev"
        ],
        "log": r"C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog-sniper.log",
        "cwd": r"C:\Users\wifik\Desktop\projects\larger-lab\sniper-dashboard",
    },
}

CHECK_INTERVAL = 30       # seconds between health checks
RESTART_COOLDOWN = 60     # seconds after a restart before restarting again
MAX_RESTARTS_PER_HOUR = 5 # circuit breaker
OC2_STUCK_TIMEOUT = 960    # 16 minutes — if OC2 port is up but no log activity, restart

WORKSPACE = Path(__file__).parent.parent
STATE_FILE = WORKSPACE / "tools" / ".watchdog-state.json"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg, service="WATCHDOG"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{service}] {msg}"
    print(line, flush=True)
    # Also write to a general watchdog log
    log_dir = Path(r"C:\Users\wifik\AppData\Local\Temp\openclaw")
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "watchdog.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_port_listening(port):
    """Check if a port is actively listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            result = s.connect_ex(("127.0.0.1", port))
            return result == 0
    except Exception:
        return False


def is_process_alive(pid):
    """Check if a process PID is still running."""
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        # Fallback: use tasklist
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in result.stdout


def load_state():
    """Load watchdog state (restart counts, last restart times)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"restarts": {}, "last_restart": {}}


def save_state(state):
    """Persist watchdog state."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def kill_existing_on_port(port):
    """Kill any process listening on the given port."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                log(f"Killing stale process PID {pid} on port {port}")
                subprocess.run(["taskkill", "/F", "/PID", pid],
                             capture_output=True, timeout=10)
                time.sleep(2)
    except Exception as e:
        log(f"Error killing stale process on port {port}: {e}")


def start_service(name, config):
    """Start a gateway service."""
    log(f"Starting {name} gateway...", name)
    
    # Kill anything already on the port
    kill_existing_on_port(config["port"])
    
    # Clear old log
    log_path = Path(config["log"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Start the process
    try:
        with open(config["log"], "a", encoding="utf-8") as log_f:
            log_f.write(f"\n{'='*60}\n")
            log_f.write(f"[{datetime.now().isoformat()}] Starting {name}\n")
            log_f.write(f"Command: {' '.join(config['cmd'])}\n")
            log_f.write(f"{'='*60}\n\n")
        
        # Build environment
        env = os.environ.copy()
        if "env" in config:
            env.update(config["env"])
        
        proc = subprocess.Popen(
            config["cmd"],
            stdout=open(config["log"], "a"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            cwd=config.get("cwd"),
            env=env,
        )
        
        log(f"{name} started with PID {proc.pid}", name)
        
        # Wait for port to come up
        for attempt in range(10):
            time.sleep(2)
            if is_port_listening(config["port"]):
                log(f"{name} is listening on port {config['port']} ✓", name)
                return proc.pid
        
        log(f"{name} started but port {config['port']} not listening yet (may still be initializing)", name)
        return proc.pid
        
    except Exception as e:
        log(f"Failed to start {name}: {e}", name)
        return None


def is_oc2_responsive():
    """
    Check if OC2 is actually responding to messages, not just listening on port.
    Looks at the OC2 log for recent inbound/outbound Telegram activity.
    Returns True if responsive, False if stuck.
    """
    log_path = Path(r"C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-31.log")
    if not log_path.exists():
        return True  # Can't check, assume OK
    
    try:
        # Check last 50 lines for recent Telegram inbound activity
        result = subprocess.run(
            ["powershell", "-Command", f"Get-Content '{log_path}' -Tail 50 | Select-String 'telegram.*inbound' | Select-Object -Last 1"],
            capture_output=True, text=True, timeout=10
        )
        last_inbound = result.stdout.strip()
        
        if not last_inbound:
            return True  # No recent inbound, can't determine stuck
        
        # Check if there's been any outbound/response activity after the last inbound
        result2 = subprocess.run(
            ["powershell", "-Command", f"Get-Content '{log_path}' -Tail 100 | Select-String 'telegram.*outbound|chat.send|message.send' | Select-Object -Last 1"],
            capture_output=True, text=True, timeout=10
        )
        
        # Check for stalled session warnings
        result3 = subprocess.run(
            ["powershell", "-Command", f"Get-Content '{log_path}' -Tail 100 | Select-String 'stalled session' | Select-Object -Last 1"],
            capture_output=True, text=True, timeout=10
        )
        
        if result3.stdout.strip():
            # There's a stalled session — check how old
            stall_line = result3.stdout.strip()
            if "age=" in stall_line:
                # Extract age in seconds
                import re
                match = re.search(r'age=(\d+)s', stall_line)
                if match:
                    age = int(match.group(1))
                    if age > OC2_STUCK_TIMEOUT:
                        log(f"OC2 has stalled session older than {OC2_STUCK_TIMEOUT}s — needs restart")
                        return False
        
        return True
        
    except Exception as e:
        log(f"Error checking OC2 responsiveness: {e}")
        return True  # On error, don't restart


def check_and_restart(name, config, state):
    """Check a service and restart if needed. Returns True if healthy."""
    port = config["port"]
    
    if is_port_listening(port):
        # For OC2, also check responsiveness (not just port)
        if config.get("stuck_check") and not is_oc2_responsive():
            log(f"{name} port {port} is listening but NOT RESPONSIVE — restarting", name)
        else:
            return True
    
    log(f"Port {port} NOT LISTENING — {name} is DOWN", name)
    
    # Circuit breaker: don't restart too frequently
    now = time.time()
    last_restart = state.get("last_restart", {}).get(name, 0)
    restart_count = state.get("restarts", {}).get(name, 0)
    
    if now - last_restart < RESTART_COOLDOWN:
        log(f"Cooldown active for {name} — skipping restart", name)
        return False
    
    if restart_count >= MAX_RESTARTS_PER_HOUR:
        log(f"CIRCUIT BREAKER: {name} exceeded {MAX_RESTARTS_PER_HOUR}/hour — manual intervention needed!", name)
        return False
    
    # Restart
    pid = start_service(name, config)
    
    # Update state
    state.setdefault("last_restart", {})[name] = now
    state.setdefault("restarts", {})[name] = restart_count + 1
    save_state(state)
    
    return pid is not None


def reset_restart_counts(state):
    """Reset hourly restart counters."""
    now = datetime.now()
    if not hasattr(reset_restart_counts, "last_reset"):
        reset_restart_counts.last_reset = now
    
    if (now - reset_restart_counts.last_reset).total_seconds() >= 3600:
        state["restarts"] = {}
        save_state(state)
        reset_restart_counts.last_reset = now
        log("Reset hourly restart counters")


def install_scheduled_task():
    """Register this watchdog as a Windows Scheduled Task that runs at system startup."""
    script_path = Path(__file__).resolve()
    python_path = sys.executable
    
    task_name = "GatewayWatchdog"
    cmd = f'"{python_path}" "{script_path}"'
    
    # Create XML task definition for boot-time startup
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Keeps OC2 and Hermes gateways running 24/7</Description>
    <Author>OWL</Author>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{WORKSPACE}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
    
    xml_path = WORKSPACE / "tools" / "gateway_watchdog_task.xml"
    xml_path.write_text(xml_content, encoding="utf-16")
    
    # Register the task
    subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"], 
                   capture_output=True, timeout=10)
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", task_name, "/XML", str(xml_path)],
        capture_output=True, text=True, timeout=15
    )
    
    if result.returncode == 0:
        log(f"Scheduled task '{task_name}' registered — watchdog will start at boot")
    else:
        log(f"Failed to register scheduled task: {result.stderr}")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    if "--install" in sys.argv:
        install_scheduled_task()
        return
    
    if "--check" in sys.argv:
        state = load_state()
        all_ok = True
        for name, config in SERVICES.items():
            ok = is_port_listening(config["port"])
            status = "✓ UP" if ok else "✗ DOWN"
            print(f"{name} (port {config['port']}): {status}")
            if not ok:
                all_ok = False
        sys.exit(0 if all_ok else 1)
    
    log("=" * 60)
    log("Gateway Watchdog started — monitoring OC2 + Hermes 24/7")
    log(f"Check interval: {CHECK_INTERVAL}s | Max restarts/hour: {MAX_RESTARTS_PER_HOUR}")
    log("=" * 60)
    
    state = load_state()
    
    while True:
        try:
            reset_restart_counts(state)
            
            for name, config in SERVICES.items():
                check_and_restart(name, config, state)
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Watchdog stopped by user")
            break
        except Exception as e:
            log(f"Watchdog error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
