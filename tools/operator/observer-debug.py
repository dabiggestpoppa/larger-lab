#!/usr/bin/env python3
"""OCE Observer Debug CLI — inspect and manage observers via the OCE backend API."""

import argparse
import sys
import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"

# ── colour helpers ──────────────────────────────────────────────────────────

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def green(text: str)  -> str: return _c("32", text)
def yellow(text: str) -> str: return _c("33", text)
def red(text: str)    -> str: return _c("31", text)
def bold(text: str)   -> str: return _c("1", text)
def dim(text: str)    -> str: return _c("2", text)

def health_color(state: str) -> str:
    s = state.lower()
    if s in ("healthy", "active", "ok"):
        return green(state)
    if s in ("warning", "degraded", "suspended"):
        return yellow(state)
    return red(state)

# ── HTTP helper ─────────────────────────────────────────────────────────────

def api_get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"✗  API unreachable at {url}"))
        print(dim(f"   {exc}"))
        sys.exit(1)
    except json.JSONDecodeError:
        print(red(f"✗  Invalid JSON response from {url}"))
        sys.exit(1)

# ── tabulate fallback (no external dep) ─────────────────────────────────────

def render_table(headers: list[str], rows: list[list[str]]) -> str:
    """Simple table renderer — uses tabulate if available, else manual."""
    try:
        from tabulate import tabulate as _tb
        return _tb(rows, headers=headers, tablefmt="simple")
    except ImportError:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        lines: list[str] = []
        header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        lines.append(bold(header_line))
        lines.append(dim("  ".join("-" * w for w in widths)))
        for row in rows:
            lines.append("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        return "\n".join(lines)

# ── command implementations ─────────────────────────────────────────────────

def cmd_list(_args: argparse.Namespace) -> None:
    data = api_get("/api/v1/observers")
    observers = data if isinstance(data, list) else data.get("observers", data.get("data", []))
    if not observers:
        print(yellow("No observers found."))
        return
    rows = []
    for o in observers:
        state = health_color(o.get("state", o.get("status", "unknown")))
        rows.append([
            str(o.get("id", "")),
            str(o.get("type", "")),
            state,
            str(o.get("health", o.get("health_score", "-"))),
        ])
    print(render_table(["ID", "Type", "State", "Health"], rows))
    print(dim(f"\n{len(observers)} observer(s)"))

def cmd_status(args: argparse.Namespace) -> None:
    data = api_get(f"/api/v1/observers/{args.id}")
    if not data:
        print(red(f"Observer '{args.id}' not found."))
        sys.exit(1)
    print(bold(f"Observer: {args.id}"))
    print(dim("─" * 40))
    for key, val in data.items():
        if isinstance(val, dict):
            print(f"  {bold(key)}:")
            for k2, v2 in val.items():
                print(f"    {k2}: {v2}")
        elif isinstance(val, list):
            print(f"  {bold(key)}: [{len(val)} items]")
        else:
            print(f"  {bold(key)}: {val}")

def cmd_health(args: argparse.Namespace) -> None:
    data = api_get(f"/api/v1/observers/{args.id}/health")
    if not data:
        print(red(f"Observer '{args.id}' not found."))
        sys.exit(1)
    entropy  = data.get("entropy", "-")
    drift    = data.get("drift", "-")
    budget   = data.get("budget", data.get("budget_remaining", "-"))
    score    = data.get("health_score", data.get("score", "-"))

    def _metric_color(val, low, high):
        try:
            v = float(val)
            if v <= low:  return green(str(val))
            if v <= high: return yellow(str(val))
            return red(str(val))
        except (TypeError, ValueError):
            return str(val)

    rows = [
        ["Health Score", _metric_color(score, 70, 40)],
        ["Entropy",     _metric_color(entropy, 0.3, 0.6)],
        ["Drift",       _metric_color(drift, 0.2, 0.5)],
        ["Budget",      str(budget)],
    ]
    print(bold(f"Health — {args.id}"))
    print(render_table(["Metric", "Value"], rows))

def cmd_events(args: argparse.Namespace) -> None:
    limit = getattr(args, "limit", 20)
    data = api_get(f"/api/v1/observers/{args.id}/events?limit={limit}")
    events = data if isinstance(data, list) else data.get("events", data.get("data", []))
    if not events:
        print(yellow(f"No events for observer '{args.id}'."))
        return
    rows = []
    for e in events:
        ts   = str(e.get("timestamp", e.get("ts", "")))
        etype = str(e.get("type", e.get("event_type", "")))
        detail = str(e.get("detail", e.get("message", "")))[:60]
        rows.append([ts, etype, detail])
    print(render_table(["Timestamp", "Type", "Detail"], rows))
    print(dim(f"\n{len(events)} event(s)"))

def cmd_logs(args: argparse.Namespace) -> None:
    lines = getattr(args, "lines", 50)
    data = api_get(f"/api/v1/observers/{args.id}/logs?lines={lines}")
    entries = data if isinstance(data, list) else data.get("logs", data.get("data", []))
    if not entries:
        print(yellow(f"No log entries for observer '{args.id}'."))
        return
    for entry in entries:
        if isinstance(entry, dict):
            ts      = entry.get("timestamp", entry.get("ts", ""))
            level   = str(entry.get("level", "")).upper()
            message = entry.get("message", entry.get("msg", ""))
            level_colored = {
                "INFO": green(level), "WARN": yellow(level),
                "ERROR": red(level), "DEBUG": dim(level),
            }.get(level, level)
            print(f"  {dim(ts)}  {level_colored}  {message}")
        else:
            print(f"  {entry}")
    print(dim(f"\n{len(entries)} log line(s)"))

def _post_command(action: str, id_: str) -> None:
    url = f"{BASE_URL}/api/v1/observers/{id_}/{action}"
    try:
        req = urllib.request.Request(url, method="POST",
                                     data=b"{}",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            data = json.loads(body) if body else {}
    except urllib.error.URLError as exc:
        print(red(f"✗  API error: {exc}"))
        sys.exit(1)
    state = data.get("state", data.get("status", action + "d"))
    print(green(f"✓  Observer '{id_}' {state}"))
    if data:
        for k, v in data.items():
            if k not in ("state", "status"):
                print(f"   {k}: {v}")

def cmd_activate(args: argparse.Namespace) -> None:
    _post_command("activate", args.id)

def cmd_suspend(args: argparse.Namespace) -> None:
    _post_command("suspend", args.id)

# ── CLI setup ───────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="observer-debug",
        description="OCE Observer Debug CLI — inspect and manage observers",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all observers")

    p = sub.add_parser("status", help="Full observer details")
    p.add_argument("id", help="Observer ID")

    p = sub.add_parser("health", help="Health metrics")
    p.add_argument("id", help="Observer ID")

    p = sub.add_parser("events", help="Recent events")
    p.add_argument("id", help="Observer ID")
    p.add_argument("limit", nargs="?", type=int, default=20, help="Max events (default 20)")

    p = sub.add_parser("logs", help="Log entries")
    p.add_argument("id", help="Observer ID")
    p.add_argument("lines", nargs="?", type=int, default=50, help="Max lines (default 50)")

    p = sub.add_parser("activate", help="Activate a suspended observer")
    p.add_argument("id", help="Observer ID")

    p = sub.add_parser("suspend", help="Suspend an active observer")
    p.add_argument("id", help="Observer ID")

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "list":     cmd_list,
        "status":   cmd_status,
        "health":   cmd_health,
        "events":   cmd_events,
        "logs":     cmd_logs,
        "activate": cmd_activate,
        "suspend":  cmd_suspend,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
