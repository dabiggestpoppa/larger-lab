#!/usr/bin/env python3
"""
OC2 System Safety Net
- Monitors gateway health, disk space, memory
- Auto-restarts gateway if down
- Alerts if resources are critical
- Logs all checks
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\logs")
LOG_DIR.mkdir(exist_ok=True)
SAFETY_LOG = LOG_DIR / "safety-net.log"
STATE_FILE = LOG_DIR / "safety-state.json"

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB


def log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    # Rotate log if too large
    if SAFETY_LOG.exists() and SAFETY_LOG.stat().st_size > MAX_LOG_SIZE:
        backup = LOG_DIR / "safety-net.log.old"
        if backup.exists():
            backup.unlink()
        SAFETY_LOG.rename(backup)
    with open(SAFETY_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def check_gateway():
    """Check if OC2 gateway is reachable."""
    code, out, err = run_cmd("openclaw gateway probe", timeout=15)
    if code == 0 and ("ok" in out.lower() or "connect" in out.lower()):
        return True, "Gateway healthy"
    return False, f"Gateway issue: {err or out}"


def restart_gateway():
    """Attempt to restart the gateway."""
    log("Attempting gateway restart...", "WARN")
    code, out, err = run_cmd("openclaw gateway restart", timeout=30)
    if code == 0:
        log("Gateway restart command sent successfully")
        time.sleep(10)
        ok, msg = check_gateway()
        if ok:
            log("Gateway restarted and healthy")
            return True
        else:
            log(f"Gateway restart failed: {msg}", "ERROR")
            return False
    else:
        log(f"Gateway restart command failed: {err}", "ERROR")
        return False


def check_disk():
    """Check disk space."""
    code, out, err = run_cmd(
        'powershell -Command "Get-PSDrive C | Select-Object @{N=\'FreeGB\';E={[math]::Round($_.Free/1GB,1)}},@{N=\'UsedGB\';E={[math]::Round($_.Used/1GB,1)}}"',
        timeout=10,
    )
    if code == 0 and out:
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        if len(lines) >= 2:
            # Parse the values
            parts = lines[-1].split()
            if len(parts) >= 2:
                try:
                    used_gb = float(parts[0])
                    free_gb = float(parts[1])
                    total = used_gb + free_gb
                    pct_used = (used_gb / total) * 100 if total > 0 else 0
                    return {
                        "free_gb": free_gb,
                        "used_gb": used_gb,
                        "pct_used": round(pct_used, 1),
                        "critical": free_gb < 5,
                        "warning": free_gb < 10,
                    }
                except ValueError:
                    pass
    return None


def check_memory():
    """Check system memory."""
    code, out, err = run_cmd(
        'powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{N=\'FreeMB\';E={[math]::Round($_.FreePhysicalMemory/1KB,0)}},@{N=\'TotalMB\';E={[math]::Round($_.TotalVisibleMemorySize/1KB,0)}}"',
        timeout=10,
    )
    if code == 0 and out:
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        if len(lines) >= 2:
            parts = lines[-1].split()
            if len(parts) >= 2:
                try:
                    total_mb = float(parts[0])
                    free_mb = float(parts[1])
                    pct_free = (free_mb / total_mb) * 100 if total_mb > 0 else 0
                    return {
                        "free_mb": free_mb,
                        "total_mb": total_mb,
                        "pct_free": round(pct_free, 1),
                        "critical": free_mb < 200,
                        "warning": free_mb < 500,
                    }
                except ValueError:
                    pass
    return None


def check_node_processes():
    """Check if critical Node.js processes are running."""
    code, out, err = run_cmd(
        'powershell -Command "Get-Process -Name \'node\' -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, @{N=\'MemMB\';E={[math]::Round($_.WorkingSet64/1MB,0)}} | Format-Table -AutoSize"',
        timeout=10,
    )
    if code == 0 and out:
        lines = [l.strip() for l in out.split("\n") if l.strip() and "Id" not in lines[0]]
        return len([l for l in lines if l])  # count of node processes
    return 0


def save_state(state):
    """Save safety check state."""
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    log("=== Safety Net Check Starting ===")
    state = {"checks": [], "actions": []}

    # 1. Check gateway
    gw_ok, gw_msg = check_gateway()
    state["checks"].append({"gateway": gw_ok, "message": gw_msg})
    if gw_ok:
        log(f"Gateway: OK")
    else:
        log(f"Gateway: DOWN — {gw_msg}", "WARN")
        restarted = restart_gateway()
        state["actions"].append({"gateway_restart": restarted})

    # 2. Check disk
    disk = check_disk()
    if disk:
        state["checks"].append({"disk": disk})
        if disk["critical"]:
            log(f"Disk: CRITICAL — {disk['free_gb']}GB free", "ERROR")
            state["actions"].append({"disk_alert": "critical"})
        elif disk["warning"]:
            log(f"Disk: WARNING — {disk['free_gb']}GB free", "WARN")
        else:
            log(f"Disk: OK — {disk['free_gb']}GB free ({disk['pct_used']}% used)")

    # 3. Check memory
    mem = check_memory()
    if mem:
        state["checks"].append({"memory": mem})
        if mem["critical"]:
            log(f"Memory: CRITICAL — {mem['free_mb']}MB free", "ERROR")
            state["actions"].append({"memory_alert": "critical"})
        elif mem["warning"]:
            log(f"Memory: WARNING — {mem['free_mb']}MB free", "WARN")
        else:
            log(f"Memory: OK — {mem['free_mb']}MB free ({mem['pct_free']}%)")

    # 4. Check node processes
    node_count = check_node_processes()
    state["checks"].append({"node_processes": node_count})
    log(f"Node processes: {node_count}")

    # 5. Check twin bridge
    try:
        import json as _json

        hb_file = Path(
            r"C:\Users\wifik\Desktop\projects\larger-lab\shared-twin\heartbeat.json"
        )
        if hb_file.exists():
            with open(hb_file) as f:
                hb = _json.load(f)
            oc2_ts = hb.get("oc2", {}).get("timestamp")
            oc3_ts = hb.get("oc3", {}).get("timestamp")
            state["checks"].append(
                {"twin_heartbeat": {"oc2": oc2_ts, "oc3": oc3_ts}}
            )
            log(f"Twin heartbeat: OC2={oc2_ts}, OC3={oc3_ts}")
    except Exception as e:
        log(f"Twin heartbeat check failed: {e}", "WARN")

    save_state(state)

    # Summary
    issues = [c for c in state["checks"] if not c.get("gateway", True)]
    if issues:
        log(f"=== Check complete: {len(issues)} issue(s) found ===", "WARN")
    else:
        log("=== Check complete: All systems nominal ===")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
