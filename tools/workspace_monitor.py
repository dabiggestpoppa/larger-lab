#!/usr/bin/env python3
"""
Workspace Monitor — Run every 2 hours via cron.
Checks all critical systems and writes status to a log file.
"""
import subprocess
import json
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
LOG_FILE = BASE / "logs" / "workspace_monitor.log"
DB_FILE = BASE / "quant-lab" / "mt5" / "dmr_live.db"
STATE_FILE = BASE / "quant-lab" / "mt5" / "dmr_live_state.json"
CONFIG_FILE = BASE / "quant-lab" / "mt5" / "dmr_config.json"

LOG_FILE.parent.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except:
        pass
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_port(port, name):
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=5)
        return True
    except:
        return False

def check_port_raw(port):
    """Check if a port is listening without HTTP."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False

def get_ram():
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = round(stat.ullTotalPhys / (1024**3), 1)
        free_gb = round(stat.ullAvailPhys / (1024**3), 1)
        used_pct = stat.dwMemoryLoad
        return total_gb, free_gb, used_pct
    except:
        return None, None, None

def main():
    log("=" * 60)
    log("WORKSPACE MONITOR CHECK")
    log("=" * 60)

    # RAM
    total, free, pct = get_ram()
    if total:
        log(f"RAM: {free}GB free / {total}GB ({pct}% used)")
        if pct > 95:
            log("⚠️ CRITICAL: RAM usage above 95%!")
        elif pct > 90:
            log("⚠️ WARNING: RAM usage above 90%")

    # Disk
    import shutil
    disk = shutil.disk_usage("C:\\")
    free_gb = round(disk.free / (1024**3), 1)
    log(f"Disk: {free_gb}GB free")
    if free_gb < 10:
        log("⚠️ WARNING: Disk space below 10GB!")

    # Ports
    ports = {
        8000: "OCE Backend",
        8001: "SRRA API",
        3000: "OCE Frontend",
        3001: "SRRA Frontend",
        8002: "DMR Dashboard",
        18790: "OpenClaw Gateway",
    }
    for port, name in ports.items():
        up = check_port_raw(port)
        status = "[OK]" if up else "[DOWN]"
        log(f"  {name} (:{port}): {status}")

    # DMR Live process
    dmr_running = False
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'dmr_live'} | Select-Object Id"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            dmr_running = True
            log(f"DMR Live: ✅ Running ({result.stdout.strip()})")
        else:
            log("DMR Live: ❌ NOT RUNNING!")
    except:
        log("DMR Live: Could not check process")

    # DMR Config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        log(f"DMR Config: enabled={cfg.get('enabled')}, symbols={cfg.get('symbols')}, lots={cfg.get('lot_size')}")

    # DMR State
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        log(f"DMR State: today={state.get('today')}, trades={state.get('total_trades', 0)}, pnl={state.get('pnl', 0)}")

    # DMR DB
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM trades")
            trades = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM p90_events")
            p90s = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM system_log")
            logs = c.fetchone()[0]
            c.execute("SELECT timestamp, level, message FROM system_log ORDER BY id DESC LIMIT 1")
            last_log = c.fetchone()
            conn.close()
            log(f"DMR DB: {trades} trades, {p90s} P90s, {logs} log entries")
            if last_log:
                log(f"Last log: [{last_log[1]}] {last_log[2]}")
        except Exception as e:
            log(f"DB Error: {e}")

    # MT5 AutoTrading check (from recent logs)
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT message, details FROM system_log WHERE category='MT5' ORDER BY id DESC LIMIT 3")
            mt5_logs = c.fetchall()
            conn.close()
            for msg, details in mt5_logs:
                if 'DISABLED' in msg or 'disabled' in str(details):
                    log(f"⚠️ MT5 AutoTrading may be DISABLED! Check MT5 toolbar.")
                    break
        except:
            pass

    log("=" * 60)

if __name__ == "__main__":
    main()
