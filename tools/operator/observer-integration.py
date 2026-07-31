#!/usr/bin/env python3
"""
OCE-3.16 Operator <-> Observer Integration
Connects operator tools to the OCE Observer Runtime.
Every operator action emits an observer event to the OCE backend.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

OCE_BASE_URL = os.environ.get("OCE_BASE_URL", "http://localhost:8000")
EVENTS_INGEST_URL = f"{OCE_BASE_URL}/events/ingest"
WS_EVENTS_URL = f"{OCE_BASE_URL.replace('http', 'ws')}/ws/events"

def green(t): return f"\033[92m{t}\033[0m"
def red(t):   return f"\033[91m{t}\033[0m"
def yellow(t):return f"\033[93m{t}\033[0m"
def cyan(t):  return f"\033[96m{t}\033[0m"

def _build_event(event_type, observer_id, data):
    return {"type": event_type, "observer_id": observer_id,
            "timestamp": datetime.now(timezone.utc).isoformat(), "data": data}

def _emit_event(event):
    payload = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(EVENTS_INGEST_URL, data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw else {}
            eid = body.get("event_id", body.get("id", ""))
            print(green(f"  OK Event emitted: {event.get('type')} -> id={eid}"))
            return {"success": True, "event_id": eid}
    except Exception as exc:
        print(red(f"  XX Emit failed: {exc}"))
        return {"success": False, "event_id": ""}

def exec_and_emit(command, observer_id="operator"):
    """Run a command and emit operator.command.executed event."""
    print(cyan(f"[exec_and_emit] Running: {command}"))
    output, success = "", False
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = r.stdout.strip()
        if r.stderr.strip(): output += "\n" + r.stderr.strip()
        success = r.returncode == 0
        print(green("  OK Command succeeded") if success else red(f"  XX Command failed (rc={r.returncode})"))
    except subprocess.TimeoutExpired:
        output = "Command timed out after 60s"; print(red(f"  XX {output}"))
    except Exception as exc:
        output = str(exc); print(red(f"  XX {exc}"))
    ev = _build_event("operator.command.executed", observer_id,
                      {"command": command, "output": output[:2000], "returncode": 0 if success else 1})
    er = _emit_event(ev)
    return {"success": success and er["success"], "event_id": er["event_id"], "output": output}

def kill_and_emit(pid, observer_id="operator"):
    """Kill a process and emit operator.process.killed event."""
    print(cyan(f"[kill_and_emit] Killing PID: {pid}"))
    success = False
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
        success = True; print(green(f"  OK Process {pid} killed"))
    except ProcessLookupError:
        print(red(f"  XX Process {pid} not found"))
    except Exception as exc:
        print(red(f"  XX {exc}"))
    ev = _build_event("operator.process.killed", observer_id, {"pid": pid, "killed": success})
    er = _emit_event(ev)
    return {"success": success and er["success"], "event_id": er["event_id"]}

def install_and_emit(package, manager="pip", observer_id="operator"):
    """Install a package and emit operator.package.installed event."""
    print(cyan(f"[install_and_emit] Installing {package} via {manager}"))
    cmd = {"pip": f"pip install {package}", "npm": f"npm install {package}",
           "yarn": f"yarn add {package}"}.get(manager, f"{manager} install {package}")
    output, success = "", False
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        output = r.stdout.strip()
        success = r.returncode == 0
        print(green(f"  OK {package} installed") if success else red(f"  XX Install failed (rc={r.returncode})"))
    except subprocess.TimeoutExpired:
        output = "Install timed out after 120s"; print(red(f"  XX {output}"))
    except Exception as exc:
        output = str(exc); print(red(f"  XX {exc}"))
    ev = _build_event("operator.package.installed", observer_id,
                      {"package": package, "manager": manager, "output": output[:2000], "installed": success})
    er = _emit_event(ev)
    return {"success": success and er["success"], "event_id": er["event_id"]}

def vscode_open_and_emit(file_path, observer_id="operator"):
    """Open file in VS Code and emit operator.vscode.file_opened event."""
    print(cyan(f"[vscode_open_and_emit] Opening: {file_path}"))
    success = False
    try:
        r = subprocess.run(["code", file_path], capture_output=True, text=True, timeout=15)
        success = r.returncode == 0
        print(green(f"  OK Opened in VS Code") if success else red(f"  XX VS Code rc={r.returncode}"))
    except FileNotFoundError:
        print(red("  XX 'code' not found. Is VS Code in PATH?"))
    except Exception as exc:
        print(red(f"  XX {exc}"))
    ev = _build_event("operator.vscode.file_opened", observer_id, {"file_path": file_path, "opened": success})
    er = _emit_event(ev)
    return {"success": success and er["success"], "event_id": er["event_id"]}

def subscribe_to_observer_health(observer_id, callback=None):
    """Subscribe to health events for an observer (WebSocket or HTTP polling fallback)."""
    print(cyan(f"[subscribe_to_observer_health] Observer: {observer_id}"))
    sub_id = f"sub-{observer_id}-{int(time.time())}"
    try:
        import websocket
        ws = websocket.create_connection(WS_EVENTS_URL, timeout=5)
        print(green(f"  OK WebSocket connected to {WS_EVENTS_URL}"))
        count = 0
        try:
            while True:
                ev = json.loads(ws.recv())
                if ev.get("type", "").startswith("observer.") and ev.get("observer_id") == observer_id:
                    count += 1
                    (callback(ev) if callback else print(yellow(f"  [evt] #{count}: {ev.get('type')}")))
        except KeyboardInterrupt:
            print(yellow(f"\n  Ended. {count} events received."))
        finally:
            ws.close()
    except ImportError:
        print(yellow("  ⚠ websocket-client not installed. HTTP polling fallback."))
        count = 0
        try:
            while True:
                try:
                    url = f"{OCE_BASE_URL}/events?observer_id={observer_id}&type_prefix=observer."
                    with urllib.request.urlopen(url, timeout=5) as resp:
                        for ev in json.loads(resp.read().decode("utf-8")):
                            count += 1
                            (callback(ev) if callback else print(yellow(f"  [evt] #{count}: {ev.get('type')}")))
                except urllib.error.URLError:
                    print(red("  XX Backend unreachable"))
                time.sleep(5)
        except KeyboardInterrupt:
            print(yellow(f"\n  Ended. {count} events received."))
    except Exception as exc:
        print(red(f"  XX Connection failed: {exc}"))
        return {"success": False, "subscription_id": sub_id}
    return {"success": True, "subscription_id": sub_id}

def main():
    p = argparse.ArgumentParser(description="OCE-3.16 Operator <-> Observer Integration")
    sp = p.add_subparsers(dest="action")
    pe = sp.add_parser("exec"); pe.add_argument("command"); pe.add_argument("--observer-id", default="operator")
    pk = sp.add_parser("kill"); pk.add_argument("pid", type=int); pk.add_argument("--observer-id", default="operator")
    pi = sp.add_parser("install"); pi.add_argument("package"); pi.add_argument("--manager", default="pip")
    pi.add_argument("--observer-id", default="operator")
    pv = sp.add_parser("vscode"); pv.add_argument("file_path"); pv.add_argument("--observer-id", default="operator")
    ps = sp.add_parser("subscribe"); ps.add_argument("--observer-id", required=True)
    args = p.parse_args()
    if not args.action: p.print_help(); sys.exit(1)
    print(f"\n{'='*60}\n  OCE-3.16 Operator <-> Observer Integration\n  Backend: {OCE_BASE_URL}\n{'='*60}\n")
    if args.action == "exec":    r = exec_and_emit(args.command, args.observer_id)
    elif args.action == "kill":  r = kill_and_emit(args.pid, args.observer_id)
    elif args.action == "install": r = install_and_emit(args.package, args.manager, args.observer_id)
    elif args.action == "vscode": r = vscode_open_and_emit(args.file_path, args.observer_id)
    elif args.action == "subscribe": r = subscribe_to_observer_health(args.observer_id)
    else: p.print_help(); sys.exit(1)
    print(f"\n{'-'*60}\n  Result: {json.dumps(r, indent=2)}\n{'-'*60}\n")

if __name__ == "__main__":
    main()
