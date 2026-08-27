#!/usr/bin/env python3
"""TB-R6.6.1 - External health check. Runs every 5min via SYSTEM task.
Checks heartbeat age, PIDs alive, writes alarm + Telegram if stale."""
import json, os, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))
from tb_runtime_config import STATE_DIR, RUNTIME_DB

def pid_alive(pid):
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h: ctypes.windll.kernel32.CloseHandle(h); return True
    except: pass
    return False

def main():
    threshold = 300
    try:
        conn = sqlite3.connect(f"file:{RUNTIME_DB}?mode=ro", uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        r = conn.execute("SELECT ts FROM runtime_heartbeat ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(r["ts"])).total_seconds() if r else None
    except: age = None
    stale = age is None or age > threshold
    pids = {}
    for name, fn in [("supervisor","tb_supervisor.pid"),("worker","tb_worker.pid")]:
        try:
            pid = int(open(STATE_DIR / fn).read().strip())
            pids[name] = {"pid": pid, "alive": pid_alive(pid)}
        except: pids[name] = {"pid": None, "alive": False}
    report = {"ts": datetime.now(timezone.utc).isoformat(), "age": age, "stale": stale, "pids": pids}
    if stale:
        try:
            conn = sqlite3.connect(str(RUNTIME_DB), timeout=5.0)
            conn.execute("INSERT INTO runtime_status(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                ("runtime_alarm", json.dumps({"alarm":"CRITICAL_RUNTIME_STALE","ts":datetime.now(timezone.utc).isoformat()}), datetime.now(timezone.utc).isoformat()))
            conn.commit(); conn.close()
        except: pass
        creds = STATE_DIR / "tb_telegram.json"
        if creds.exists():
            try:
                c = json.loads(creds.read_text())
                subprocess.run(["curl","-s","-X","POST",f"https://api.telegram.org/bot{c['token']}/sendMessage","-d",f"chat_id={c['chat_id']}","-d",f"text=TB HEALTHCHECK: STALE heartbeat age={age:.0f}s"], timeout=10, capture_output=True)
            except: pass
    print(json.dumps(report, indent=2))
    return 0
if __name__ == "__main__": sys.exit(main())
