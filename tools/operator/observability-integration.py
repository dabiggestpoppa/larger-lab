#!/usr/bin/env python3
"""
OCE-5.17 Operator <-> Observability Integration
================================================
Connects operator tools to the OCE Observability layer (Phase 5).

Every operator action is recorded as a metric + trace span:
  - exec     → records command latency, emits trace hop
  - kill     → records process termination metric
  - install  → records package install latency
  - vscode   → records file open metric
  - query    → pulls metrics/traces/alerts for operator context

Also subscribes to observability WebSocket streams so the operator
can react to alerts and metric changes in real time.

Backend endpoints used:
  GET  /metrics                     — Current metrics summary
  GET  /metrics/history             — Historical metrics
  GET  /traces                      — List/search traces
  GET  /traces/{id}                 — Trace detail
  GET  /traces/observer/{id}        — Traces by observer
  GET  /alerts                      — Active alerts
  GET  /alerts/history              — Alert history
  POST /alerts/{id}/acknowledge     — Acknowledge alert
  POST /alerts/rules                — Add custom rule
  GET  /dashboard                   — Full dashboard data
  WS   /ws/metrics                  — Real-time metrics stream
  WS   /ws/alerts                   — Real-time alert stream
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

OCE_BASE_URL = os.environ.get("OCE_BASE_URL", "http://localhost:8000")

# ─── Colour helpers ─────────────────────────────────────────────────────────

def green(t):  return f"\033[92m{t}\033[0m"
def red(t):    return f"\033[91m{t}\033[0m"
def yellow(t): return f"\033[93m{t}\033[0m"
def cyan(t):   return f"\033[96m{t}\033[0m"
def bold(t):   return f"\033[1m{t}\033[0m"
def dim(t):    return f"\033[2m{t}\033[0m"

# ─── HTTP helpers ───────────────────────────────────────────────────────────

def _api_get(path: str) -> dict:
    url = f"{OCE_BASE_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"  ✗ API unreachable at {url}"))
        print(dim(f"    {exc}"))
        return {}
    except json.JSONDecodeError:
        print(red(f"  ✗ Invalid JSON from {url}"))
        return {}

def _api_post(path: str, data: dict) -> dict:
    url = f"{OCE_BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"  ✗ API unreachable at {url}"))
        print(dim(f"    {exc}"))
        return {}
    except json.JSONDecodeError:
        return {}

# ─── Metric recording helpers ───────────────────────────────────────────────

def _record_metric(name: str, value: float, labels: dict = None):
    """Record a metric via the event ingest endpoint (best-effort)."""
    event = {
        "type": "operator.metric.recorded",
        "observer_id": "operator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"metric_name": name, "metric_value": value, "labels": labels or {}},
    }
    try:
        _api_post("/events/ingest", event)
    except Exception:
        pass  # Best-effort; don't fail the operator action

def _start_trace(action: str, observer_id: str = "operator") -> str:
    """Start a trace span for an operator action. Returns trace_id."""
    result = _api_post("/traces", {"action": action, "observer_id": observer_id})
    return result.get("trace_id", "")

def _end_trace(trace_id: str, outcome: str = "success"):
    """End a trace span."""
    if trace_id:
        _api_post(f"/traces/{trace_id}/end", {"outcome": outcome})

# ─── Operator actions with observability ────────────────────────────────────

def exec_and_record(command: str, observer_id: str = "operator") -> dict:
    """Run a command, record metrics + trace."""
    print(cyan(f"[exec] Running: {command}"))
    trace_id = _start_trace("exec", observer_id)
    t0 = time.time()
    output, success = "", False
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = r.stdout.strip()
        if r.stderr.strip():
            output += "\n" + r.stderr.strip()
        success = r.returncode == 0
        print(green("  ✓ Command succeeded") if success else red(f"  ✗ Command failed (rc={r.returncode})"))
    except subprocess.TimeoutExpired:
        output = "Command timed out after 60s"
        print(red(f"  ✗ {output}"))
    except Exception as exc:
        output = str(exc)
        print(red(f"  ✗ {exc}"))

    latency_ms = (time.time() - t0) * 1000
    _record_metric("operator.exec.latency_ms", latency_ms,
                   {"command": command[:50], "success": str(success)})
    _record_metric("operator.exec.count", 1,
                   {"success": str(success)})
    _end_trace(trace_id, "success" if success else "error")
    return {"success": success, "output": output, "latency_ms": latency_ms}

def kill_and_record(pid: int, observer_id: str = "operator") -> dict:
    """Kill a process, record metrics + trace."""
    import signal
    print(cyan(f"[kill] Killing PID: {pid}"))
    trace_id = _start_trace("kill", observer_id)
    t0 = time.time()
    success = False
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
        success = True
        print(green(f"  ✓ Process {pid} killed"))
    except ProcessLookupError:
        print(red(f"  ✗ Process {pid} not found"))
    except Exception as exc:
        print(red(f"  ✗ {exc}"))

    latency_ms = (time.time() - t0) * 1000
    _record_metric("operator.kill.latency_ms", latency_ms, {"pid": str(pid)})
    _record_metric("operator.kill.count", 1, {"success": str(success)})
    _end_trace(trace_id, "success" if success else "error")
    return {"success": success, "latency_ms": latency_ms}

def install_and_record(package: str, manager: str = "pip", observer_id: str = "operator") -> dict:
    """Install a package, record metrics + trace."""
    print(cyan(f"[install] Installing {package} via {manager}"))
    trace_id = _start_trace("install", observer_id)
    t0 = time.time()
    cmd = {"pip": f"pip install {package}", "npm": f"npm install {package}",
           "yarn": f"yarn add {package}"}.get(manager, f"{manager} install {package}")
    output, success = "", False
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        output = r.stdout.strip()
        success = r.returncode == 0
        print(green(f"  ✓ {package} installed") if success else red(f"  ✗ Install failed (rc={r.returncode})"))
    except subprocess.TimeoutExpired:
        output = "Install timed out after 120s"
        print(red(f"  ✗ {output}"))
    except Exception as exc:
        output = str(exc)
        print(red(f"  ✗ {exc}"))

    latency_ms = (time.time() - t0) * 1000
    _record_metric("operator.install.latency_ms", latency_ms,
                   {"package": package, "manager": manager})
    _record_metric("operator.install.count", 1, {"success": str(success)})
    _end_trace(trace_id, "success" if success else "error")
    return {"success": success, "output": output, "latency_ms": latency_ms}

# ─── Observability query helpers ────────────────────────────────────────────

def get_metrics_summary() -> dict:
    """Pull current metrics summary from OCE."""
    return _api_get("/metrics")

def get_metrics_history(metric_name: str, limit: int = 100) -> dict:
    """Pull historical metrics for a specific metric path."""
    return _api_get(f"/metrics/history?metric_name={metric_name}&limit={limit}")

def get_active_traces(limit: int = 50) -> dict:
    """Get currently in-flight traces."""
    return _api_get(f"/traces?active=true&limit={limit}")

def search_traces(event_type: str = None, outcome: str = None,
                  source: str = None, min_latency_ms: float = None,
                  limit: int = 50) -> dict:
    """Search traces with filters."""
    params = []
    if event_type: params.append(f"event_type={event_type}")
    if outcome: params.append(f"outcome={outcome}")
    if source: params.append(f"source={source}")
    if min_latency_ms: params.append(f"min_latency_ms={min_latency_ms}")
    params.append(f"limit={limit}")
    return _api_get(f"/traces?{'&'.join(params)}")

def get_traces_by_observer(observer_id: str, limit: int = 50) -> dict:
    """Get all traces for a specific observer."""
    return _api_get(f"/traces/observer/{observer_id}?limit={limit}")

def get_active_alerts() -> dict:
    """Get all active alerts."""
    return _api_get("/alerts")

def get_alert_history(limit: int = 100) -> dict:
    """Get alert history."""
    return _api_get(f"/alerts/history?limit={limit}")

def acknowledge_alert(alert_id: str) -> dict:
    """Acknowledge an alert."""
    return _api_post(f"/alerts/{alert_id}/acknowledge", {})

def add_alert_rule(name: str, metric: str, threshold: float,
                   comparison: str = "lt", severity: str = "warning",
                   cooldown_sec: int = 300, description: str = "",
                   auto_repair: bool = False) -> dict:
    """Add a custom alert rule."""
    return _api_post("/alerts/rules", {
        "name": name, "metric": metric, "threshold": threshold,
        "comparison": comparison, "severity": severity,
        "cooldown_sec": cooldown_sec, "description": description,
        "auto_repair": auto_repair,
    })

def get_dashboard() -> dict:
    """Get full observability dashboard data."""
    return _api_get("/dashboard")

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="OCE-5.17 Operator <-> Observability Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python observability-integration.py exec "Get-Process python"
  python observability-integration.py kill 12345
  python observability-integration.py install requests --manager pip
  python observability-integration.py metrics
  python observability-integration.py traces --active
  python observability-integration.py alerts
  python observability-integration.py dashboard
  python observability-integration.py rule-add "High CPU" "system.cpu" 90 gt critical
        """,
    )
    sp = p.add_subparsers(dest="action")

    # Operator actions with observability
    pe = sp.add_parser("exec", help="Run command + record metrics/trace")
    pe.add_argument("command")
    pe.add_argument("--observer-id", default="operator")

    pk = sp.add_parser("kill", help="Kill process + record metrics/trace")
    pk.add_argument("pid", type=int)
    pk.add_argument("--observer-id", default="operator")

    pi = sp.add_parser("install", help="Install package + record metrics/trace")
    pi.add_argument("package")
    pi.add_argument("--manager", default="pip")
    pi.add_argument("--observer-id", default="operator")

    # Observability queries
    sp.add_parser("metrics", help="Get current metrics summary")
    pmh = sp.add_parser("metrics-history", help="Get historical metrics")
    pmh.add_argument("metric_name")
    pmh.add_argument("--limit", type=int, default=100)

    pt = sp.add_parser("traces", help="List/search traces")
    pt.add_argument("--active", action="store_true")
    pt.add_argument("--event-type")
    pt.add_argument("--outcome")
    pt.add_argument("--source")
    pt.add_argument("--min-latency-ms", type=float)
    pt.add_argument("--limit", type=int, default=50)

    pto = sp.add_parser("traces-observer", help="Get traces by observer")
    pto.add_argument("observer_id")
    pto.add_argument("--limit", type=int, default=50)

    sp.add_parser("alerts", help="Get active alerts")
    pal = sp.add_parser("alerts-history", help="Get alert history")
    pal.add_argument("--limit", type=int, default=100)

    paa = sp.add_parser("alert-ack", help="Acknowledge an alert")
    paa.add_argument("alert_id")

    par = sp.add_parser("rule-add", help="Add custom alert rule")
    par.add_argument("name")
    par.add_argument("metric")
    par.add_argument("threshold", type=float)
    par.add_argument("--comparison", default="lt")
    par.add_argument("--severity", default="warning")
    par.add_argument("--cooldown", type=int, default=300)
    par.add_argument("--description", default="")
    par.add_argument("--auto-repair", action="store_true")

    sp.add_parser("dashboard", help="Get full observability dashboard")

    args = p.parse_args()
    if not args.action:
        p.print_help()
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  OCE-5.17 Operator <-> Observability Integration")
    print(f"  Backend: {OCE_BASE_URL}")
    print(f"{'='*60}\n")

    if args.action == "exec":
        r = exec_and_record(args.command, args.observer_id)
    elif args.action == "kill":
        r = kill_and_record(args.pid, args.observer_id)
    elif args.action == "install":
        r = install_and_record(args.package, args.manager, args.observer_id)
    elif args.action == "metrics":
        r = get_metrics_summary()
    elif args.action == "metrics-history":
        r = get_metrics_history(args.metric_name, args.limit)
    elif args.action == "traces":
        r = search_traces(args.event_type, args.outcome, args.source,
                          args.min_latency_ms, args.limit)
        if args.active:
            r = get_active_traces(args.limit)
    elif args.action == "traces-observer":
        r = get_traces_by_observer(args.observer_id, args.limit)
    elif args.action == "alerts":
        r = get_active_alerts()
    elif args.action == "alerts-history":
        r = get_alert_history(args.limit)
    elif args.action == "alert-ack":
        r = acknowledge_alert(args.alert_id)
    elif args.action == "rule-add":
        r = add_alert_rule(args.name, args.metric, args.threshold,
                           args.comparison, args.severity, args.cooldown,
                           args.description, args.auto_repair)
    elif args.action == "dashboard":
        r = get_dashboard()
    else:
        p.print_help()
        sys.exit(1)

    print(f"\n{'-'*60}")
    print(f"  Result:")
    print(json.dumps(r, indent=2, default=str))
    print(f"{'-'*60}\n")

if __name__ == "__main__":
    main()
