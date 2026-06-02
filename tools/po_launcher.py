"""
PO Launcher — Starts all PO services and keeps them running.
Run: python tools/po_launcher.py
"""
import subprocess
import sys
import time
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
CWD = str(ROOT)

SERVICES = [
    ("PO API",      [PYTHON, "tools/po_api.py"],       8765),
    ("PO SSE",      [PYTHON, "tools/po_sse.py"],       8780),
    ("PO Dashboard",[PYTHON, "tools/po_dashboard.py"], 8770),
]

def is_port_up(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def main():
    procs = []
    for name, cmd, port in SERVICES:
        if is_port_up(port):
            print(f"[OK] {name} already running on :{port}")
            continue
        print(f"[START] {name} on :{port}...")
        p = subprocess.Popen(
            cmd, cwd=CWD,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append((name, p, port))
        # Wait for port to come up
        for _ in range(15):
            time.sleep(1)
            if is_port_up(port):
                print(f"[UP] {name} on :{port} (PID {p.pid})")
                break
        else:
            print(f"[WARN] {name} started but port :{port} not yet listening")

    print()
    print("All PO services started. Dashboard: http://127.0.0.1:8770/index.html")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(60)
            # Check health
            for name, p, port in procs:
                if p.poll() is not None:
                    print(f"[DOWN] {name} exited with code {p.returncode}, restarting...")
                    idx = SERVICES.index(next(s for s in SERVICES if s[0] == name))
                    _, cmd, port = SERVICES[idx]
                    p2 = subprocess.Popen(
                        cmd, cwd=CWD,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    procs[idx] = (name, p2, port)
    except KeyboardInterrupt:
        print("\nShutting down...")
        for name, p, port in procs:
            p.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
