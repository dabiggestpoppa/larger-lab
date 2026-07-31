#!/usr/bin/env python3
"""
OCE-6.16 Execution Debug CLI
==============================
Inspect and debug the OCE Execution Engine from the terminal.

Commands:
  queue           — Show task queue (pending/queued/running)
  workers         — Show worker pool status with utilization
  task <id>       — Full task detail (payload, status, result, history)
  list            — List tasks with filters
  replay <id>     — Replay a completed/failed task
  cancel <id>     — Cancel a pending/running task
  history         — Execution history
  stats           — Engine statistics
  analytics       — Per-task-type throughput, success rate, latency
  bottlenecks     — Identify slow tasks, queue buildup, worker starvation
  policies        — List execution policies
  policy-add      — Create/update a policy
  health          — Quick health check of execution engine
  all             — Run all checks and print summary

Color coding:
  Green  = completed / healthy
  Yellow = running / warning
  Red    = failed / critical
  Cyan   = pending / queued
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

OCE_BASE_URL = "http://localhost:8000"

# ─── Colour helpers ─────────────────────────────────────────────────────────

def _c(code, text):
    return f"\033[{code}m{text}\033[0m"

def green(text):   return _c("32", text)
def yellow(text):  return _c("33", text)
def red(text):     return _c("31", text)
def cyan(text):    return _c("36", text)
def bold(text):    return _c("1", text)
def dim(text):     return _c("2", text)

def status_color(s):
    s = str(s).lower()
    if s in ("completed", "success"): return green(s)
    if s in ("failed", "error", "cancelled", "timed_out"): return red(s)
    if s in ("running", "retrying"): return yellow(s)
    if s in ("pending", "queued"): return cyan(s)
    return s

def severity_color(s):
    s = str(s).lower()
    if s == "critical": return red(s.upper())
    if s == "warning": return yellow(s.upper())
    return green(s.upper())

# ─── HTTP helpers ───────────────────────────────────────────────────────────

def api_get(path: str):
    url = f"{OCE_BASE_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"  API unreachable at {url}"))
        print(dim(f"    {exc}"))
        sys.exit(1)
    except json.JSONDecodeError:
        print(red(f"  Invalid JSON from {url}"))
        sys.exit(1)

def api_post(path: str, data: dict):
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
        print(red(f"  API unreachable: {exc}"))
        sys.exit(1)

# ─── Table renderer ─────────────────────────────────────────────────────────

def render_table(headers, rows):
    if not rows:
        return dim("  (no data)")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  ".join("-" * w for w in widths)
    lines = []
    lines.append("  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("  " + sep)
    for row in rows:
        lines.append("  " + "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)

# ─── Command handlers ──────────────────────────────────────────────────────

def cmd_queue(args):
    """Show task queue grouped by status."""
    print(bold("\n  Task Queue\n"))

    for status_name, status_val in [("Running", "running"), ("Queued", "queued"), ("Pending", "pending")]:
        data = api_get(f"/execution/tasks?status={status_val}&limit=50")
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        if tasks:
            print(cyan(f"  {status_name} ({len(tasks)}):"))
            rows = []
            for t in tasks:
                rows.append([
                    t.get("task_id", "")[:12],
                    t.get("task_type", ""),
                    t.get("source", ""),
                    str(t.get("attempts", 0)),
                    t.get("created_at", "")[:19],
                ])
            print(render_table(["Task ID", "Type", "Source", "Attempts", "Created"], rows))
            print()
        else:
            print(green(f"  {status_name}: (empty)"))

    # Also show recent failures
    data = api_get("/execution/tasks?status=failed&limit=5")
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    if tasks:
        print(red(f"  Recent Failures ({len(tasks)}):"))
        rows = []
        for t in tasks:
            rows.append([
                t.get("task_id", "")[:12],
                t.get("task_type", ""),
                (t.get("error", "") or "")[:50],
                t.get("completed_at", "")[:19],
            ])
        print(render_table(["Task ID", "Type", "Error", "Failed At"], rows))
        print()

def cmd_workers(args):
    """Show worker pool status."""
    print(bold("\n  Worker Pool\n"))
    data = api_get("/execution/workers")
    workers = data.get("workers", [])
    if not workers:
        print(dim("  (no workers registered)"))
        return data

    rows = []
    busy_count = 0
    for w in workers:
        is_busy = w.get("is_busy", False)
        if is_busy:
            busy_count += 1
        rows.append([
            w.get("worker_id", ""),
            green("IDLE") if not is_busy else yellow("BUSY"),
            str(w.get("tasks_processed", 0)),
            str(w.get("tasks_failed", 0)),
            (w.get("current_task_id", "") or "-")[:12],
        ])
    print(render_table(["Worker", "State", "Processed", "Failed", "Current Task"], rows))
    print(f"\n  Total: {len(workers)} workers, {yellow(str(busy_count) + ' busy')}, {green(str(len(workers) - busy_count) + ' idle')}")
    print(f"  Queue size: {data.get('queue_size', 'N/A')}, Active: {data.get('active_count', 'N/A')}")
    return data

def cmd_task(args):
    """Show full task detail."""
    print(bold(f"\n  Task Detail: {args.task_id}\n"))
    data = api_get(f"/execution/tasks/{args.task_id}")
    if not data:
        print(dim("  (task not found)"))
        return data

    print(f"  Task ID:     {data.get('task_id', '')}")
    print(f"  Type:        {data.get('task_type', '')}")
    print(f"  Status:      {status_color(data.get('status', 'unknown'))}")
    print(f"  Priority:    {data.get('priority', '')}")
    print(f"  Source:      {data.get('source', '')}")
    print(f"  Attempts:    {data.get('attempts', 0)}/{data.get('max_retries', 3)}")
    print(f"  Timeout:     {data.get('timeout_sec', 0)}s")
    print(f"  Created:     {data.get('created_at', '')}")
    print(f"  Started:     {data.get('started_at', '') or '-'}")
    print(f"  Completed:   {data.get('completed_at', '') or '-'}")
    print(f"  Trace ID:    {data.get('trace_id', '') or '-'}")
    print(f"  Tags:        {', '.join(data.get('tags', []))}")

    payload = data.get("payload", {})
    if payload:
        print(f"\n  Payload:")
        print(f"    {json.dumps(payload, indent=4, default=str)[:500]}")

    result = data.get("result")
    if result:
        print(f"\n  Result:")
        print(f"    {json.dumps(result, indent=4, default=str)[:500]}")

    error = data.get("error")
    if error:
        print(f"\n  {red('Error:')}")
        print(f"    {error}")

    return data

def cmd_list(args):
    """List tasks with filters."""
    print(bold("\n  Task List\n"))
    params = []
    if args.status: params.append(f"status={args.status}")
    if args.task_type: params.append(f"task_type={args.task_type}")
    params.append(f"limit={args.limit}")
    data = api_get(f"/execution/tasks?{'&'.join(params)}")
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    if not tasks:
        print(dim("  (no tasks found)"))
        return data

    rows = []
    for t in tasks:
        rows.append([
            t.get("task_id", "")[:12],
            t.get("task_type", ""),
            status_color(t.get("status", "")),
            t.get("source", ""),
            str(t.get("attempts", 0)),
            (t.get("created_at", "") or "")[:19],
        ])
    print(render_table(["Task ID", "Type", "Status", "Source", "Attempts", "Created"], rows))
    print(f"\n  {len(tasks)} task(s)")
    return data

def cmd_replay(args):
    """Replay a task."""
    print(bold(f"\n  Replay: {args.task_id}\n"))
    data = api_post(f"/execution/{args.task_id}/replay", {"policy_id": args.policy})
    if data.get("new_task_id"):
        print(green(f"  Replayed as: {data['new_task_id']}"))
    else:
        print(red(f"  Replay failed"))
    return data

def cmd_cancel(args):
    """Cancel a task."""
    print(bold(f"\n  Cancel: {args.task_id}\n"))
    data = api_post(f"/execution/{args.task_id}/cancel", {})
    if data.get("status") == "cancelled":
        print(green(f"  Cancelled: {args.task_id}"))
    else:
        print(red(f"  Cancel failed: {data}"))
    return data

def cmd_history(args):
    """Show execution history."""
    print(bold("\n  Execution History\n"))
    params = [f"limit={args.limit}"]
    if args.status: params.append(f"status={args.status}")
    data = api_get(f"/execution/history?{'&'.join(params)}")
    records = data if isinstance(data, list) else data.get("records", data.get("history", []))
    if not records:
        print(dim("  (no history)"))
        return data

    rows = []
    for r in records[:args.limit]:
        rows.append([
            r.get("task_id", "")[:12],
            r.get("task_type", ""),
            status_color(r.get("status", "")),
            f"{r.get('latency_ms', 0):.0f}ms",
            (r.get("completed_at", "") or r.get("created_at", ""))[:19],
        ])
    print(render_table(["Task ID", "Type", "Status", "Latency", "Time"], rows))
    print(f"\n  {len(records)} record(s)")
    return data

def cmd_stats(args):
    """Show engine statistics."""
    print(bold("\n  Engine Statistics\n"))
    data = api_get("/execution/stats")
    if not data:
        print(dim("  (no stats available)"))
        return data

    for k, v in data.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for k2, v2 in v.items():
                print(f"    {k2}: {v2}")
        else:
            print(f"  {k}: {v}")
    return data

def cmd_analytics(args):
    """Show execution analytics."""
    print(bold("\n  Execution Analytics\n"))
    data = api_get("/execution/analytics")
    if not data:
        print(dim("  (no analytics available)"))
        return data

    by_type = data.get("by_type", {})
    if by_type:
        rows = []
        for task_type, stats in by_type.items():
            rows.append([
                task_type,
                str(stats.get("total", 0)),
                f"{stats.get('success_rate', 0):.1%}",
                f"{stats.get('avg_latency_ms', 0):.1f}ms",
                str(stats.get("completed", 0)),
                str(stats.get("failed", 0)),
            ])
        print(render_table(["Task Type", "Total", "Success Rate", "Avg Latency", "Completed", "Failed"], rows))

    summary = data.get("summary", {})
    if summary:
        print(f"\n  Summary:")
        for k, v in summary.items():
            print(f"    {k}: {v}")

    engine_stats = data.get("engine_stats", {})
    if engine_stats:
        print(f"\n  Engine:")
        for k, v in engine_stats.items():
            if not isinstance(v, dict):
                print(f"    {k}: {v}")
    return data

def cmd_bottlenecks(args):
    """Show execution bottlenecks."""
    print(bold("\n  Execution Bottlenecks\n"))
    data = api_get("/execution/bottlenecks")
    bottlenecks = data.get("bottlenecks", [])
    if not bottlenecks:
        print(green("  No bottlenecks detected"))
        return data

    for b in bottlenecks:
        sev = b.get("severity", "info")
        print(f"  {severity_color(sev)}: {b.get('message', '')}")
        if b.get("detail"):
            print(f"    {dim(b['detail'])}")
    return data

def cmd_policies(args):
    """List execution policies."""
    print(bold("\n  Execution Policies\n"))
    data = api_get("/execution/policies")
    policies = data if isinstance(data, list) else data.get("policies", [])
    if not policies:
        print(dim("  (no policies configured)"))
        return data

    rows = []
    for p in policies:
        rows.append([
            p.get("policy_id", ""),
            p.get("name", ""),
            str(p.get("max_concurrent", 0)),
            str(p.get("rate_limit_per_minute", 0)),
            "yes" if p.get("sandboxed") else "no",
        ])
    print(render_table(["Policy ID", "Name", "Max Concurrent", "Rate Limit/m", "Sandboxed"], rows))
    return data

def cmd_policy_add(args):
    """Create/update an execution policy."""
    print(bold(f"\n  Add Policy: {args.policy_id}\n"))
    data = api_post("/execution/policies", {
        "policy_id": args.policy_id,
        "name": args.name,
        "max_concurrent": args.max_concurrent,
        "rate_limit_per_minute": args.rate_limit,
        "sandboxed": args.sandboxed,
        "description": args.description,
    })
    if data.get("status") == "registered":
        print(green(f"  Policy registered: {data.get('policy_id')}"))
    else:
        print(red(f"  Failed: {data}"))
    return data

def cmd_health(args):
    """Quick health check of execution engine."""
    print(bold("\n  Execution Engine Health\n"))
    stats = api_get("/execution/stats")
    workers = api_get("/execution/workers")
    bottlenecks = api_get("/execution/bottlenecks")

    issues = []

    # Workers
    w_list = workers.get("workers", [])
    busy = sum(1 for w in w_list if w.get("is_busy"))
    queue_size = workers.get("queue_size", 0)
    print(f"  Workers: {len(w_list)} total, {yellow(str(busy) + ' busy')}, {green(str(len(w_list) - busy) + ' idle')}")
    print(f"  Queue:   {queue_size} pending")

    if queue_size > 20:
        issues.append(f"Queue buildup: {queue_size} pending tasks")
    if w_list and busy == len(w_list) and queue_size > 5:
        issues.append("All workers busy with pending queue")

    # Stats
    total = stats.get("total_tasks", 0)
    completed = stats.get("completed_tasks", 0)
    failed = stats.get("failed_tasks", 0)
    print(f"  Tasks:   {total} total, {green(str(completed) + ' completed')}, {red(str(failed) + ' failed')}")

    if total > 0 and failed / total > 0.2:
        issues.append(f"High failure rate: {failed}/{total} ({failed/total:.0%})")

    # Bottlenecks
    bn = bottlenecks.get("bottlenecks", [])
    critical = [b for b in bn if b.get("severity") == "critical"]
    if critical:
        issues.extend([b.get("message", "") for b in critical])

    print()
    if issues:
        for issue in issues:
            print(red(f"  {issue}"))
    else:
        print(green("  All systems nominal"))

    return {"stats": stats, "workers": workers, "bottlenecks": bottlenecks}

def cmd_all(args):
    """Run all checks."""
    print(bold("\n" + "=" * 60))
    print(bold("  OCE Execution Engine — Full Diagnostic"))
    print(bold("=" * 60))
    cmd_health(args)
    print()
    cmd_queue(args)
    print()
    cmd_workers(args)
    print()
    cmd_analytics(args)
    print()
    cmd_bottlenecks(args)
    print(bold("\n" + "=" * 60))
    print(bold("  Diagnostic complete"))
    print(bold("=" * 60 + "\n"))

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="OCE-6.16 Execution Debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python execution-debug.py health
  python execution-debug.py queue
  python execution-debug.py workers
  python execution-debug.py task <task_id>
  python execution-debug.py list --status running
  python execution-debug.py cancel <task_id>
  python execution-debug.py replay <task_id>
  python execution-debug.py history --limit 20
  python execution-debug.py stats
  python execution-debug.py analytics
  python execution-debug.py bottlenecks
  python execution-debug.py policies
  python execution-debug.py policy-add default "Default Policy" --max-concurrent 5
  python execution-debug.py all
        """,
    )
    sp = p.add_subparsers(dest="command")

    sp.add_parser("queue", help="Show task queue by status")
    sp.add_parser("workers", help="Show worker pool status")

    pt = sp.add_parser("task", help="Show task detail")
    pt.add_argument("task_id")

    pl = sp.add_parser("list", help="List tasks")
    pl.add_argument("--status", choices=["pending","queued","running","completed","failed","cancelled","timed_out","retrying"])
    pl.add_argument("--task-type")
    pl.add_argument("--limit", type=int, default=50)

    pr = sp.add_parser("replay", help="Replay a task")
    pr.add_argument("task_id")
    pr.add_argument("--policy", default="default")

    pc = sp.add_parser("cancel", help="Cancel a task")
    pc.add_argument("task_id")

    ph = sp.add_parser("history", help="Execution history")
    ph.add_argument("--limit", type=int, default=50)
    ph.add_argument("--status")

    sp.add_parser("stats", help="Engine statistics")
    sp.add_parser("analytics", help="Execution analytics")
    sp.add_parser("bottlenecks", help="Bottleneck detection")
    sp.add_parser("policies", help="List policies")

    pa = sp.add_parser("policy-add", help="Create/update policy")
    pa.add_argument("policy_id")
    pa.add_argument("name")
    pa.add_argument("--max-concurrent", type=int, default=5)
    pa.add_argument("--rate-limit", type=int, default=60)
    pa.add_argument("--sandboxed", action="store_true")
    pa.add_argument("--description", default="")

    sp.add_parser("health", help="Quick health check")
    sp.add_parser("all", help="Run all checks")

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)

    handlers = {
        "queue": cmd_queue, "workers": cmd_workers, "task": cmd_task,
        "list": cmd_list, "replay": cmd_replay, "cancel": cmd_cancel,
        "history": cmd_history, "stats": cmd_stats, "analytics": cmd_analytics,
        "bottlenecks": cmd_bottlenecks, "policies": cmd_policies,
        "policy-add": cmd_policy_add, "health": cmd_health, "all": cmd_all,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        p.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
