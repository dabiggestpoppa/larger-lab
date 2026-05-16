"""
Hermes Watchdog — OWL Safety Monitor
======================================
Monitors OWL's gateway, sessions, and overall health.
Posts alerts to team-chat if anything is degraded.

Run: python tools/hermes-watchdog.py
Or as background: pythonw tools/hermes-watchdog.py
"""

import subprocess
import json
import time
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ─────────────────────────────────────────────────────────────────

OWL_GATEWAY_PORT = 18790
OWL_GATEWAY_URL = f"http://127.0.0.1:{OWL_GATEWAY_PORT}"
TEAM_CHAT_PATH = Path(__file__).parent.parent / "shared-conversations" / "team-chat.md"
LOG_PATH = Path(__file__).parent.parent / "logs" / "hermes-watchdog.log"
CHECK_INTERVAL_SECONDS = 300  # 5 minutes
STALL_THRESHOLD_SECONDS = 1800  # 30 minutes

# ─── Helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def post_to_team_chat(message: str):
    """Append a message to team-chat.md"""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"\n\n### 🔴 [HERMES WATCHDOG] {timestamp} — Alert\n\n{message}\n\n---\n"
        with open(TEAM_CHAT_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        log(f"Posted to team-chat: {message[:80]}...")
    except Exception as e:
        log(f"Failed to post to team-chat: {e}")

def check_gateway() -> dict:
    """Check if OWL gateway is responding"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", f"{OWL_GATEWAY_URL}/health"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                return {"ok": True, "status": data.get("status", "unknown"), "data": data}
            except json.JSONDecodeError:
                return {"ok": True, "status": "responding", "data": result.stdout[:200]}
        return {"ok": False, "error": f"HTTP {result.returncode}: {result.stderr[:200]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Gateway timeout (15s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_workspace_health() -> dict:
    """Quick workspace health checks"""
    issues = []
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("C:\\")
        free_gb = free / (1024**3)
        if free_gb < 5:
            issues.append(f"Low disk space: {free_gb:.1f}GB free")
    except:
        pass
    
    # Check if key directories exist
    key_dirs = ["oce", "srrs_opc", "tools", "skills", "progress"]
    for d in key_dirs:
        if not Path(d).exists():
            issues.append(f"Missing directory: {d}")
    
    # Check if SRRA-OPH tests still pass (quick import check)
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import srrs_opc; print('OK')"],
            capture_output=True, text=True, timeout=30,
            cwd=str(Path(__file__).parent.parent)
        )
        if result.returncode != 0:
            issues.append(f"SRRA-OPH import failed: {result.stderr[:100]}")
    except:
        pass
    
    return {"ok": len(issues) == 0, "issues": issues}

def restart_gateway():
    """Attempt to restart OWL gateway"""
    log("Attempting gateway restart...")
    try:
        # Kill existing gateway process
        subprocess.run(
            ["taskkill", "/F", "/IM", "node.exe", "/FI", "WINDOWTITLE eq openclaw*"],
            capture_output=True, timeout=10
        )
        time.sleep(2)
        # Start gateway
        gateway_cmd = "openclaw gateway run --port 18789 --allow-unconfigured"
        subprocess.Popen(
            gateway_cmd.split(),
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        time.sleep(5)
        log("Gateway restart attempted")
        return True
    except Exception as e:
        log(f"Gateway restart failed: {e}")
        return False

# ─── Main Loop ──────────────────────────────────────────────────────────────

def run_check():
    """Run a single health check cycle"""
    log("=" * 60)
    log("Starting health check cycle...")
    
    # 1. Check gateway
    gw = check_gateway()
    if gw["ok"]:
        log(f"[OK] Gateway OK: {gw['status']}")
    else:
        log(f"[DOWN] Gateway DOWN: {gw['error']}")
        post_to_team_chat(
            f"[ALERT] OWL Gateway is DOWN!\n"
            f"Error: {gw['error']}\n"
            f"Attempting restart..."
        )
        if restart_gateway():
            time.sleep(10)
            gw2 = check_gateway()
            if gw2["ok"]:
                post_to_team_chat("[OK] Gateway restarted successfully")
            else:
                post_to_team_chat(
                    f"[CRITICAL] Gateway restart FAILED - Manual intervention required!\n"
                    f"Error: {gw2['error']}"
                )
    
    # 2. Check workspace
    ws = check_workspace_health()
    if ws["ok"]:
        log("[OK] Workspace healthy")
    else:
        for issue in ws["issues"]:
            log(f"[WARN] Workspace issue: {issue}")
        post_to_team_chat(
            f"[WARNING] Workspace Issues Detected:\n" +
            "\n".join(f"- {i}" for i in ws["issues"])
        )
    
    # 3. Check context usage (via session status)
    try:
        result = subprocess.run(
            ["openclaw", "status", "--json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            log(f"Status check OK")
    except:
        pass
    
    log("Health check cycle complete")

def main():
    log("=" * 60)
    log("HERMES WATCHDOG STARTING")
    log(f"Monitoring OWL gateway on port {OWL_GATEWAY_PORT}")
    log(f"Check interval: {CHECK_INTERVAL_SECONDS}s")
    log(f"Team chat: {TEAM_CHAT_PATH}")
    log("=" * 60)
    
    # Run once immediately
    run_check()
    
    # Then loop
    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        run_check()

if __name__ == "__main__":
    if "--once" in sys.argv:
        run_check()
    else:
        main()
