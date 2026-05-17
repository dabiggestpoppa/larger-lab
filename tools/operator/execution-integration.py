#!/usr/bin/env python3
"""
OCE-6.15 Operator <-> Execution Engine Integration
====================================================
Connects operator tools to the OCE Execution Engine.

Every operator action can be submitted as an execution task:
  - exec     → submits a "tool_invoke" task, monitors completion
  - kill     → cancels a running task
  - install  → submits a "tool_invoke" task for package installation
  - submit   → submits a custom task (skill_call, tool_invoke, pipeline_run, agent_delegate)
  - status   → checks task status
  - list     → lists tasks by status/type
  - replay   → replays a completed/failed task
  - cancel   → cancels a pending or running task
  - workers  → shows worker pool status
  - stats    → shows execution engine statistics
  - policies → lists execution policies
  - history  → shows execution history

Backend endpoints used:
  POST /execution/submit           — Submit a task
  POST /execution/{id}/cancel      — Cancel a task
  GET  /execution/tasks            — List tasks
  GET  /execution/tasks/{id}       — Task detail
  GET  /execution/history          — Execution history
  POST /execution/{id}/replay      — Replay a task
  GET  /execution/stats            — Engine statistics
  GET  /execution/workers          — Worker pool status
  GET  /execution/policies         — List policies
  POST /execution/policies         — Create policy
  GET  /execution/analytics        — Execution analytics
  GET  /execution/bottlenecks      — Bottleneck detection
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

def status_color(s):
    s = str(s).lower()
    if s in ("completed", "success"): return green(s)
    if s in ("failed", "error", "cancelled", "timed_out"): return red(s)
    if s in ("running", "retrying"): return yellow(s)
    if s in ("pending", "queued"): return cyan(s)
    return s

# ─── HTTP helpers ───────────────────────────────────────────────────────────

def _api_get(path: str) -> dict:
    url = f"{OCE_BASE_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"  API unreachable at {url}"))
        print(dim(f"    {exc}"))
        return {}
    except json.JSONDecodeError:
        return {}

def _api_post(path: str, data: dict) -> dict:
    url = f"{OCE_BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        print(red(f"  HTTP {exc.code}: {body}"))
        return {}
    except urllib.error.URLError as exc:
        print(red(f"  API unreachable at {url}"))
        print(dim(f"    {exc}"))
        return {}

# ─── Execution Engine operations ────────────────────────────────────────────

def submit_task(task_type: str, payload: dict, priority: int = 1,
                max_retries: int = 3, timeout_sec: int = 30,
                source: str = "operator", tags: list = None,
                policy_id: str = "default") -> dict:
    """Submit a task to the execution engine."""
    data = {
        "task_type": task_type,
        "payload": payload,
        "priority": priority,
        "max_retries": max_retries,
        "timeout_sec": timeout_sec,
        "source": source,
        "tags": tags or [],
        "policy_id": policy_id,
    }
    return _api_post("/execution/submit", data)

def cancel_task(task_id: str) -> dict:
    """Cancel a running or pending task."""
    return _api_post(f"/execution/{task_id}/cancel", {})

def get_task(task_id: str) -> dict:
    """Get task details."""
    return _api_get(f"/execution/tasks/{task_id}")

def list_tasks(status: str = None, task_type: str = None, limit: int = 50) -> dict:
    """List tasks with optional filters."""
    params = []
    if status: params.append(f"status={status}")
    if task_type: params.append(f"task_type={task_type}")
    params.append(f"limit={limit}")
    return _api_get(f"/execution/tasks?{'&'.join(params)}")

def replay_task(task_id: str, policy_id: str = "default") -> dict:
    """Replay a previously executed task."""
    return _api_post(f"/execution/{task_id}/replay", {"policy_id": policy_id})

def get_history(limit: int = 50, status: str = None) -> dict:
    """Get execution history."""
    params = [f"limit={limit}"]
    if status: params.append(f"status={status}")
    return _api_get(f"/execution/history?{'&'.join(params)}")

def get_stats() -> dict:
    """Get execution engine statistics."""
    return _api_get("/execution/stats")

def get_workers() -> dict:
    """Get worker pool status."""
    return _api_get("/execution/workers")

def list_policies() -> dict:
    """List execution policies."""
    return _api_get("/execution/policies")

def create_policy(policy_id: str, name: str, max_concurrent: int = 5,
                  rate_limit: int = 60, allowed_types: list = None,
                  blocked_types: list = None, max_timeout: int = 300,
                  sandboxed: bool = False, description: str = "") -> dict:
    """Create or update an execution policy."""
    return _api_post("/execution/policies", {
        "policy_id": policy_id,
        "name": name,
        "max_concurrent": max_concurrent,
        "rate_limit_per_minute": rate_limit,
        "allowed_types": allowed_types or ["skill_call", "tool_invoke", "pipeline_run", "agent_delegate"],
        "blocked_types": blocked_types or [],
        "max_timeout_sec": max_timeout,
        "sandboxed": sandboxed,
        "description": description,
    })

def get_analytics() -> dict:
    """Get execution analytics."""
    return _api_get("/execution/analytics")

def get_bottlenecks() -> dict:
    """Get execution bottlenecks."""
    return _api_get("/execution/bottlenecks")

# ─── Operator action wrappers ───────────────────────────────────────────────

def exec_and_submit(command: str, timeout_sec: int = 60, priority: int = 1) -> dict:
    """Submit a shell command as an execution task."""
    print(cyan(f"[exec] Submitting: {command}"))
    result = submit_task(
        task_type="tool_invoke",
        payload={"command": command, "action": "exec"},
        priority=priority,
        timeout_sec=timeout_sec,
        source="operator",
        tags=["exec", "operator"],
    )
    if result.get("task_id"):
        print(green(f"  Task submitted: {result['task_id']}"))
    else:
        print(red(f"  Submit failed: {result}"))
    return result

def install_and_submit(package: str, manager: str = "pip", timeout_sec: int = 120) -> dict:
    """Submit a package installation as an execution task."""
    print(cyan(f"[install] Submitting: {package} via {manager}"))
    result = submit_task(
        task_type="tool_invoke",
        payload={"package": package, "manager": manager, "action": "install"},
        priority=1,
        timeout_sec=timeout_sec,
        source="operator",
        tags=["install", "operator"],
    )
    if result.get("task_id"):
        print(green(f"  Task submitted: {result['task_id']}"))
    else:
        print(red(f"  Submit failed: {result}"))
    return result

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="OCE-6.15 Operator <-> Execution Engine Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python execution-integration.py exec "Get-Process python"
  python execution-integration.py install requests --manager pip
  python execution-integration.py submit --task-type skill_call --payload '{"skill":"test"}'
  python execution-integration.py status <task_id>
  python execution-integration.py list --status running
  python execution-integration.py cancel <task_id>
  python execution-integration.py replay <task_id>
  python execution-integration.py workers
  python execution-integration.py stats
  python execution-integration.py analytics
  python execution-integration.py bottlenecks
  python execution-integration.py policies
        """,
    )
    sp = p.add_subparsers(dest="action")

    # Operator action wrappers
    pe = sp.add_parser("exec", help="Submit shell command as execution task")
    pe.add_argument("command")
    pe.add_argument("--timeout", type=int, default=60)
    pe.add_argument("--priority", type=int, default=1, choices=[0,1,2,3])

    pi = sp.add_parser("install", help="Submit package install as execution task")
    pi.add_argument("package")
    pi.add_argument("--manager", default="pip")
    pi.add_argument("--timeout", type=int, default=120)

    # Task management
    ps = sp.add_parser("submit", help="Submit a custom task")
    ps.add_argument("--task-type", required=True, choices=["skill_call","tool_invoke","pipeline_run","agent_delegate"])
    ps.add_argument("--payload", default="{}", help="JSON payload string")
    ps.add_argument("--priority", type=int, default=1, choices=[0,1,2,3])
    ps.add_argument("--timeout", type=int, default=30)
    ps.add_argument("--tags", nargs="*", default=[])
    ps.add_argument("--policy", default="default")

    pst = sp.add_parser("status", help="Get task status")
    pst.add_argument("task_id")

    pl = sp.add_parser("list", help="List tasks")
    pl.add_argument("--status", choices=["pending","queued","running","completed","failed","cancelled","timed_out","retrying"])
    pl.add_argument("--task-type")
    pl.add_argument("--limit", type=int, default=50)

    pc = sp.add_parser("cancel", help="Cancel a task")
    pc.add_argument("task_id")

    pr = sp.add_parser("replay", help="Replay a task")
    pr.add_argument("task_id")
    pr.add_argument("--policy", default="default")

    ph = sp.add_parser("history", help="Show execution history")
    ph.add_argument("--limit", type=int, default=50)
    ph.add_argument("--status")

    # Engine inspection
    sp.add_parser("workers", help="Show worker pool status")
    sp.add_parser("stats", help="Show engine statistics")
    sp.add_parser("analytics", help="Show execution analytics")
    sp.add_parser("bottlenecks", help="Show execution bottlenecks")
    sp.add_parser("policies", help="List execution policies")

    pa = sp.add_parser("policy-add", help="Create/update execution policy")
    pa.add_argument("policy_id")
    pa.add_argument("name")
    pa.add_argument("--max-concurrent", type=int, default=5)
    pa.add_argument("--rate-limit", type=int, default=60)
    pa.add_argument("--sandboxed", action="store_true")

    args = p.parse_args()
    if not args.action:
        p.print_help()
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  OCE-6.15 Operator <-> Execution Engine")
    print(f"  Backend: {OCE_BASE_URL}")
    print(f"{'='*60}\n")

    if args.action == "exec":
        r = exec_and_submit(args.command, args.timeout, args.priority)
    elif args.action == "install":
        r = install_and_submit(args.package, args.manager, args.timeout)
    elif args.action == "submit":
        payload = json.loads(args.payload)
        r = submit_task(args.task_type, payload, args.priority, timeout_sec=args.timeout,
                        tags=args.tags, policy_id=args.policy)
    elif args.action == "status":
        r = get_task(args.task_id)
    elif args.action == "list":
        r = list_tasks(args.status, args.task_type, args.limit)
    elif args.action == "cancel":
        r = cancel_task(args.task_id)
    elif args.action == "replay":
        r = replay_task(args.task_id, args.policy)
    elif args.action == "history":
        r = get_history(args.limit, args.status)
    elif args.action == "workers":
        r = get_workers()
    elif args.action == "stats":
        r = get_stats()
    elif args.action == "analytics":
        r = get_analytics()
    elif args.action == "bottlenecks":
        r = get_bottlenecks()
    elif args.action == "policies":
        r = list_policies()
    elif args.action == "policy-add":
        r = create_policy(args.policy_id, args.name, args.max_concurrent,
                          args.rate_limit, sandboxed=args.sandboxed)
    else:
        p.print_help()
        sys.exit(1)

    print(f"\n{'-'*60}")
    if isinstance(r, list):
        print(f"  {len(r)} result(s):")
        for item in r[:10]:
            print(f"    {json.dumps(item, indent=2, default=str)[:200]}")
        if len(r) > 10:
            print(f"    ... and {len(r) - 10} more")
    else:
        print(f"  Result:")
        print(json.dumps(r, indent=2, default=str))
    print(f"{'-'*60}\n")

if __name__ == "__main__":
    main()
