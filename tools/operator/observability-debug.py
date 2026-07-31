#!/usr/bin/env python3
"""
OCE-5.18 Observability Debug CLI
=================================
Inspect and debug the OCE Observability layer from the terminal.

Commands:
  metrics       — Current metrics summary (event rates, observer health, memory, entropy)
  metrics-hist  — Historical metrics for a specific metric path
  traces        — List active or completed traces
  trace-detail  — Full detail for a single trace
  traces-by-obs — All traces through a specific observer
  alerts        — Active alerts with severity colors
  alert-hist    — Alert history
  alert-ack     cknowledge an alert
  rules         — List configured alert rules
  rule-add      — Add a custom alert rule
  rule-del      — Remove an alert rule
  dashboard     — Full observability dashboard (metrics + alerts + traces)
  topology      — Topology map with health colors
  health        — Quick health check of all OCE subsystems
  all           — Run all checks and print summary

Color coding:
  Green  = healthy / success / info
  Yellow = warning / degraded
  Red    = critical / error / failure
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

def severity_color(sev: str) -> str:
    s = sev.lower()
    if s in ("critical", "error"):
        return red(sev.upper())
    if s in ("warning", "warn", "degraded"):
        return yellow(sev.upper())
    return green(sev.upper())

def health_color(value: float) -> str:
    if value >= 0.7:
        return green(f"{value:.2f}")
    if value >= 0.4:
        return yellow(f"{value:.2f}")
    return red(f"{value:.2f}")

def outcome_color(outcome: str) -> str:
    o = outcome.lower()
    if o in ("success", "ok", "healthy"):
        return green(o)
    if o in ("error", "failed", "failure", "dropped"):
        return red(o)
    if o in ("timeout", "degraded", "warning"):
        return yellow(o)
    return o

# ─── HTTP helpers ───────────────────────────────────────────────────────────

def api_get(path: str):
    url = f"{OCE_BASE_URL}{path}"
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

def api_post(path: str, data: dict):
    url = f"{OCE_BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        print(red(f"✗  HTTP {exc.code}: {body}"))
        return {}
    except urllib.error.URLError as exc:
        print(red(f"✗  API unreachable: {exc}"))
        sys.exit(1)

# ─── Table renderer (no external deps) ─────────────────────────────────────

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

def cmd_metrics(args):
    """Display current metrics summary."""
    print(bold("\n📊  Metrics Summary\n"))
    data = api_get("/metrics")
    if not data:
        print(dim("  (no metrics available)"))
        return data

    # Event metrics
    events = data.get("events", {})
    if events:
        print(cyan("  Events:"))
        rows = []
        for k, v in events.items():
            rows.append([k, str(v)])
        print(render_table(["Metric", "Value"], rows))
        print()

    # Observer metrics
    observers = data.get("observers", {})
    if observers:
        print(cyan("  Observers:"))
        rows = []
        for k, v in observers.items():
            if isinstance(v, dict):
                rows.append([k, str(v.get("count", v)), f"avg_health={v.get('avg_health', 'N/A'):.2f}" if isinstance(v.get("avg_health"), float) else ""])
            else:
                rows.append([k, str(v)])
        print(render_table(["Metric", "Value", "Detail"], rows))
        print()

    # Memory metrics
    memory = data.get("memory", {})
    if memory:
        print(cyan("  Memory:"))
        rows = []
        for k, v in memory.items():
            rows.append([k, str(v)])
        print(render_table(["Metric", "Value"], rows))
        print()

    # Entropy metrics
    entropy = data.get("entropy", {})
    if entropy:
        print(cyan("  Entropy:"))
        rows = []
        for k, v in entropy.items():
            rows.append([k, str(v)])
        print(render_table(["Metric", "Value"], rows))
        print()

    # Operator metrics
    operator = data.get("operator", {})
    if operator:
        print(cyan("  Operator:"))
        rows = []
        for k, v in operator.items():
            rows.append([k, str(v)])
        print(render_table(["Metric", "Value"], rows))
        print()

    # Raw fallback
    if not any([events, observers, memory, entropy, operator]):
        print(json.dumps(data, indent=2, default=str))

    return data

def cmd_metrics_history(args):
    """Display historical metrics for a specific metric path."""
    print(bold(f"\n📈  Metrics History: {args.metric_name}\n"))
    data = api_get(f"/metrics/history?metric_name={args.metric_name}&limit={args.limit}")
    if isinstance(data, list):
        rows = []
        for entry in data[:args.limit]:
            ts = entry.get("timestamp", "")
            val = entry.get("value", "")
            rows.append([ts, str(val)])
        print(render_table(["Timestamp", "Value"], rows))
    else:
        print(json.dumps(data, indent=2, default=str))
    return data

def cmd_traces(args):
    """List traces (active or search)."""
    print(bold("\n🔍  Traces\n"))
    if args.active:
        data = api_get(f"/traces?active=true&limit={args.limit}")
    else:
        params = []
        if args.event_type: params.append(f"event_type={args.event_type}")
        if args.outcome: params.append(f"outcome={args.outcome}")
        if args.source: params.append(f"source={args.source}")
        if args.min_latency: params.append(f"min_latency_ms={args.min_latency}")
        params.append(f"limit={args.limit}")
        data = api_get(f"/traces?{'&'.join(params)}")

    traces = data if isinstance(data, list) else data.get("traces", data.get("data", []))
    if not traces:
        print(dim("  (no traces found)"))
        return data

    rows = []
    for t in traces:
        rows.append([
            t.get("trace_id", "")[:12],
            t.get("event_type", ""),
            t.get("source", ""),
            outcome_color(t.get("outcome", "unknown")),
            f"{t.get('total_latency_ms', 0):.1f}ms",
            str(t.get("hop_count", 0)),
        ])
    print(render_table(["Trace ID", "Event Type", "Source", "Outcome", "Latency", "Hops"], rows))
    print(f"\n  {len(traces)} trace(s)")
    return data

def cmd_trace_detail(args):
    """Show full detail for a single trace."""
    print(bold(f"\n🔎  Trace Detail: {args.trace_id}\n"))
    data = api_get(f"/traces/{args.trace_id}")
    if not data:
        print(dim("  (trace not found)"))
        return data

    print(f"  Trace ID:    {data.get('trace_id', '')}")
    print(f"  Event Type:  {data.get('event_type', '')}")
    print(f"  Source:      {data.get('source', '')}")
    print(f"  Outcome:     {outcome_color(data.get('outcome', 'unknown'))}")
    print(f"  Latency:     {data.get('total_latency_ms', 0):.1f}ms")
    print(f"  Started:     {data.get('started_at', '')}")
    print(f"  Ended:       {data.get('ended_at', '')}")

    hops = data.get("hops", [])
    if hops:
        print(f"\n  {bold('Hops:')}")
        rows = []
        for h in hops:
            rows.append([
                h.get("observer_id", ""),
                h.get("action", ""),
                f"{h.get('latency_ms', 0):.1f}ms",
                outcome_color(h.get("outcome", "unknown")),
            ])
        print(render_table(["Observer", "Action", "Latency", "Outcome"], rows))
    return data

def cmd_traces_by_observer(args):
    """Show all traces for a specific observer."""
    print(bold(f"\n👁  Traces by Observer: {args.observer_id}\n"))
    data = api_get(f"/traces/observer/{args.observer_id}?limit={args.limit}")
    traces = data if isinstance(data, list) else data.get("traces", [])
    if not traces:
        print(dim("  (no traces for this observer)"))
        return data
    rows = []
    for t in traces:
        rows.append([
            t.get("trace_id", "")[:12],
            t.get("event_type", ""),
            outcome_color(t.get("outcome", "unknown")),
            f"{t.get('total_latency_ms', 0):.1f}ms",
        ])
    print(render_table(["Trace ID", "Event Type", "Outcome", "Latency"], rows))
    print(f"\n  {len(traces)} trace(s)")
    return data

def cmd_alerts(args):
    """Display active alerts."""
    print(bold("\n🚨  Active Alerts\n"))
    data = api_get("/alerts")
    alerts = data if isinstance(data, list) else data.get("alerts", data.get("data", []))
    if not alerts:
        print(green("  ✓ No active alerts"))
        return data

    rows = []
    for a in alerts:
        rows.append([
            a.get("alert_id", "")[:12],
            a.get("name", ""),
            severity_color(a.get("severity", "info")),
            a.get("state", ""),
            a.get("fired_at", ""),
        ])
    print(render_table(["Alert ID", "Name", "Severity", "State", "Fired At"], rows))
    print(f"\n  {red(str(len(alerts) + ' active alert(s)'))}")
    return data

def cmd_alert_history(args):
    """Display alert history."""
    print(bold("\n📜  Alert History\n"))
    data = api_get(f"/alerts/history?limit={args.limit}")
    alerts = data if isinstance(data, list) else data.get("alerts", [])
    if not alerts:
        print(dim("  (no alert history)"))
        return data
    rows = []
    for a in alerts:
        rows.append([
            a.get("alert_id", "")[:12],
            a.get("name", ""),
            severity_color(a.get("severity", "info")),
            a.get("state", ""),
            a.get("fired_at", ""),
        ])
    print(render_table(["Alert ID", "Name", "Severity", "State", "Fired At"], rows))
    return data

def cmd_alert_ack(args):
    """Acknowledge an alert."""
    print(bold(f"\n✓  Acknowledging alert: {args.alert_id}\n"))
    data = api_post(f"/alerts/{args.alert_id}/acknowledge", {})
    if data.get("ok"):
        print(green(f"  ✓ Alert {args.alert_id} acknowledged"))
    else:
        print(red(f"  ✗ Failed to acknowledge alert"))
    return data

def cmd_rules(args):
    """List alert rules (from alerting engine stats)."""
    print(bold("\n📋  Alert Rules\n"))
    # Get dashboard which includes alerting stats
    data = api_get("/dashboard")
    alerting = data.get("alerts", {})
    stats = alerting.get("stats", {})
    rules = stats.get("rules", [])
    if not rules:
        print(dim("  (no rules configured — using built-in defaults)"))
        print(dim("  Built-in rules: health_critical, queue_overflow, memory_critical, entropy_low, error_rate"))
        return data
    rows = []
    for r in rules:
        rows.append([
            r.get("rule_id", "")[:12],
            r.get("name", ""),
            r.get("metric", ""),
            f"{r.get('comparison', '')} {r.get('threshold', '')}",
            severity_color(r.get("severity", "info")),
        ])
    print(render_table(["Rule ID", "Name", "Metric", "Condition", "Severity"], rows))
    return data

def cmd_rule_add(args):
    """Add a custom alert rule."""
    print(bold(f"\n➕  Adding alert rule: {args.name}\n"))
    data = api_post("/alerts/rules", {
        "name": args.name,
        "metric": args.metric,
        "threshold": args.threshold,
        "comparison": args.comparison,
        "severity": args.severity,
        "cooldown_sec": args.cooldown,
        "description": args.description,
        "auto_repair": args.auto_repair,
    })
    if data.get("ok"):
        print(green(f"  ✓ Rule added: {data.get('rule_id', '')}"))
    else:
        print(red(f"  ✗ Failed to add rule"))
    return data

def cmd_dashboard(args):
    """Display full observability dashboard."""
    print(bold("\n🖥  OCE Observability Dashboard\n"))
    print(dim(f"  {datetime.now(timezone.utc).isoformat()} UTC"))
    print()
    data = api_get("/dashboard")

    # Metrics summary
    metrics = data.get("metrics", {})
    if metrics:
        print(cyan("  ── Metrics ──"))
        for section, values in metrics.items():
            if isinstance(values, dict):
                rows = [[k, str(v)] for k, v in values.items()]
                print(f"  {section}:")
                print(render_table(["  Metric", "  Value"], rows))
            else:
                print(f"  {section}: {values}")
        print()

    # Alerts summary
    alerts = data.get("alerts", {})
    if alerts:
        print(cyan("  ── Alerts ──"))
        active = alerts.get("active", [])
        if active:
            print(red(f"  {len(active)} active alert(s)"))
            for a in active:
                print(f"    {severity_color(a.get('severity', 'info'))}: {a.get('name', '')} [{a.get('state', '')}]")
        else:
            print(green("  ✓ No active alerts"))
        print()

    # Traces summary
    traces = data.get("traces", {})
    if traces:
        print(cyan("  ── Traces ──"))
        print(f"  Active: {traces.get('active_count', 0)}")
        stats = traces.get("stats", {})
        if stats:
            for k, v in stats.items():
                print(f"  {k}: {v}")
        print()

    return data

def cmd_topology(args):
    """Display topology map with health colors."""
    print(bold("\n🗺  Topology Map\n"))
    # Get observers and their health
    observers_data = api_get("/observers")
    observers = observers_data if isinstance(observers_data, list) else observers_data.get("observers", [])

    if not observers:
        print(dim("  (no observers registered)"))
        return observers_data

    rows = []
    for obs in observers:
        oid = obs.get("observer_id", obs.get("id", ""))
        otype = obs.get("type", "unknown")
        state = obs.get("state", "unknown")
        health = obs.get("health_score", obs.get("health", 0))
        if isinstance(health, (int, float)):
            health_str = health_color(health)
        else:
            health_str = str(health)
        rows.append([oid[:20], otype, state, health_str])
    print(render_table(["Observer ID", "Type", "State", "Health"], rows))
    print(f"\n  {len(observers)} observer(s)")
    return observers_data

def cmd_health(args):
    """Quick health check of all OCE subsystems."""
    print(bold("\n🏥  OCE Health Check\n"))
    data = api_get("/dashboard")
    metrics = data.get("metrics", {})
    alerts = data.get("alerts", {})
    traces = data.get("traces", {})

    issues = []

    # Check event fabric
    events = metrics.get("events", {})
    if events:
        rate = events.get("rate_per_sec", 0)
        print(f"  Event rate:     {rate}/s")
    else:
        print(f"  Event rate:     {dim('N/A')}")

    # Check observers
    observers = metrics.get("observers", {})
    if observers:
        avg_health = observers.get("avg_health", 0)
        if isinstance(avg_health, (int, float)):
            if avg_health < 0.4:
                issues.append(f"Observer avg health low: {avg_health:.2f}")
            print(f"  Observer health: {health_color(avg_health)}")
        else:
            print(f"  Observer health: {dim('N/A')}")
        print(f"  Observer count:  {observers.get('total', dim('N/A'))}")

    # Check alerts
    active = alerts.get("active", [])
    critical = [a for a in active if a.get("severity", "").lower() == "critical"]
    if critical:
        issues.append(f"{len(critical)} critical alert(s)")
        print(f"  Alerts:          {red(str(len(active) + ' active (' + str(len(critical)) + ' critical)'))}")
    elif active:
        print(f"  Alerts:          {yellow(str(len(active) + ' active'))}")
    else:
        print(f"  Alerts:          {green('✓ None')}")

    # Check traces
    active_traces = traces.get("active_count", 0)
    print(f"  Active traces:   {active_traces}")

    # Overall verdict
    print()
    if issues:
        print(red(f"  ✗ ISSUES: {', '.join(issues)}"))
    else:
        print(green("  ✓ All systems nominal"))

    return data

def cmd_all(args):
    """Run all checks and print summary."""
    print(bold("\n" + "=" * 60))
    print(bold("  OCE Observability — Full Diagnostic"))
    print(bold("=" * 60))

    cmd_health(args)
    print()
    cmd_metrics(args)
    print()
    cmd_alerts(args)
    print()
    cmd_traces(args)
    print()
    cmd_topology(args)

    print(bold("\n" + "=" * 60))
    print(bold("  Diagnostic complete"))
    print(bold("=" * 60 + "\n"))

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="OCE-5.18 Observability Debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python observability-debug.py health
  python observability-debug.py metrics
  python observability-debug.py traces --active
  python observability-debug.py traces --outcome error --limit 20
  python observability-debug.py trace-detail <trace_id>
  python observability-debug.py traces-by-obs operator
  python observability-debug.py alerts
  python observability-debug.py alert-ack <alert_id>
  python observability-debug.py rules
  python observability-debug.py rule-add "High CPU" "system.cpu" 90 gt critical
  python observability-debug.py dashboard
  python observability-debug.py topology
  python observability-debug.py all
        """,
    )
    sp = p.add_subparsers(dest="command")

    sp.add_parser("metrics", help="Current metrics summary")
    pmh = sp.add_parser("metrics-history", help="Historical metrics")
    pmh.add_argument("metric_name")
    pmh.add_argument("--limit", type=int, default=100)

    pt = sp.add_parser("traces", help="List/search traces")
    pt.add_argument("--active", action="store_true")
    pt.add_argument("--event-type")
    pt.add_argument("--outcome")
    pt.add_argument("--source")
    pt.add_argument("--min-latency", type=float)
    pt.add_argument("--limit", type=int, default=50)

    ptd = sp.add_parser("trace-detail", help="Trace detail by ID")
    ptd.add_argument("trace_id")

    pto = sp.add_parser("traces-by-obs", help="Traces by observer")
    pto.add_argument("observer_id")
    pto.add_argument("--limit", type=int, default=50)

    sp.add_parser("alerts", help="Active alerts")
    pal = sp.add_parser("alert-history", help="Alert history")
    pal.add_argument("--limit", type=int, default=100)

    paa = sp.add_parser("alert-ack", help="Acknowledge alert")
    paa.add_argument("alert_id")

    sp.add_parser("rules", help="List alert rules")

    par = sp.add_parser("rule-add", help="Add alert rule")
    par.add_argument("name")
    par.add_argument("metric")
    par.add_argument("threshold", type=float)
    par.add_argument("--comparison", default="lt")
    par.add_argument("--severity", default="warning")
    par.add_argument("--cooldown", type=int, default=300)
    par.add_argument("--description", default="")
    par.add_argument("--auto-repair", action="store_true")

    sp.add_parser("dashboard", help="Full dashboard")
    sp.add_parser("topology", help="Topology map")
    sp.add_parser("health", help="Quick health check")
    sp.add_parser("all", help="Run all checks")

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)

    handlers = {
        "metrics": cmd_metrics,
        "metrics-history": cmd_metrics_history,
        "traces": cmd_traces,
        "trace-detail": cmd_trace_detail,
        "traces-by-obs": cmd_traces_by_observer,
        "alerts": cmd_alerts,
        "alert-history": cmd_alert_history,
        "alert-ack": cmd_alert_ack,
        "rules": cmd_rules,
        "rule-add": cmd_rule_add,
        "dashboard": cmd_dashboard,
        "topology": cmd_topology,
        "health": cmd_health,
        "all": cmd_all,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        p.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
