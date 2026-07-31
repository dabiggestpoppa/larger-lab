#!/usr/bin/env python3
"""
OCE-8.16 Governance Debug CLI
================================
Inspect and debug the OCE Governance Engine from the terminal.

Commands:
  status          — Governance engine status (boundaries, proposal counts)
  proposals       — List governance proposals (filter by status)
  proposal <id>   — Full proposal detail
  approve <id>    — Approve a proposal
  reject <id>     — Reject a proposal
  apply           — Apply all approved proposals
  override <id>   — MAD override a decision
  sovereignty     — Show sovereignty boundaries
  log             — Governance audit log
  peers           — Peer agent coevolution status
  health          — Quick governance health check
  all             — Run all checks
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

def proposal_status_color(s):
    s = str(s).lower()
    if s == "approved": return green(s)
    if s == "applied": return green(s)
    if s == "rejected": return red(s)
    if s == "overridden": return red(s)
    if s == "voting": return yellow(s)
    if s == "proposed": return cyan(s)
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

# ─── Direct engine access (fallback when API not yet registered) ────────────

def direct_engine_call(method: str, **kwargs):
    """Call governance engine directly via Python import (fallback)."""
    try:
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "oce" / "backend"))
        from governance_engine import get_governance_engine
        engine = get_governance_engine()
        func = getattr(engine, method, None)
        if func is None:
            print(red(f"  Method '{method}' not found on GovernanceEngine"))
            return None
        return func(**kwargs)
    except ImportError as exc:
        print(red(f"  Cannot import governance engine: {exc}"))
        return None
    except Exception as exc:
        print(red(f"  Engine error: {exc}"))
        return None

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

def cmd_status(args):
    """Show governance engine status."""
    print(bold("\n  Governance Engine Status\n"))

    # Try API first, fall back to direct engine
    data = api_get("/governance/status")
    if not data:
        data = direct_engine_call("get_sovereignty_report") or {}

    if not data:
        print(dim("  (governance engine not available — API endpoints may not be registered yet)"))
        return data

    # Proposal counts by status
    for status_name in ["proposed", "voting", "approved", "rejected", "applied", "overridden"]:
        proposals = api_get(f"/governance/proposals?status={status_name}&limit=1000")
        if isinstance(proposals, list):
            count = len(proposals)
            if count > 0:
                print(f"  {proposal_status_color(status_name)}: {count}")

    boundaries = data.get("boundaries", {})
    if boundaries:
        print(f"\n  Sovereignty boundaries: {len(boundaries)} configured")
        immutable = data.get("immutable_boundaries", [])
        if immutable:
            print(f"  {red('Immutable')}: {', '.join(immutable)}")

    return data

def cmd_proposals(args):
    """List governance proposals."""
    print(bold("\n  Governance Proposals\n"))
    params = []
    if args.status: params.append(f"status={args.status}")
    params.append(f"limit={args.limit}")
    data = api_get(f"/governance/proposals?{'&'.join(params)}")

    if not data:
        # Fallback to direct engine
        status_filter = args.status if args.status else None
        data = direct_engine_call("list_proposals", status=status_filter, limit=args.limit)
        if data is None:
            print(dim("  (no proposals or engine unavailable)"))
            return

    proposals = data if isinstance(data, list) else data.get("proposals", [])
    if not proposals:
        print(dim("  (no proposals found)"))
        return proposals

    rows = []
    for p in proposals:
        rows.append([
            p.get("proposal_id", "")[:12],
            p.get("proposal_type", ""),
            p.get("title", "")[:30],
            proposal_status_color(p.get("status", "")),
            f"{p.get('current_approvals', 0)}/{p.get('required_approvals', 1)}",
            (p.get("created_at", "") or "")[:19],
        ])
    print(render_table(["ID", "Type", "Title", "Status", "Votes", "Created"], rows))
    print(f"\n  {len(proposals)} proposal(s)")
    return proposals

def cmd_proposal(args):
    """Show full proposal detail."""
    print(bold(f"\n  Proposal: {args.proposal_id}\n"))
    data = api_get(f"/governance/proposals/{args.proposal_id}")
    if not data:
        data = direct_engine_call("get_proposal_status", proposal_id=args.proposal_id)
    if not data:
        print(dim("  (proposal not found)"))
        return data

    print(f"  ID:           {data.get('proposal_id', '')}")
    print(f"  Type:         {data.get('proposal_type', '')}")
    print(f"  Title:        {data.get('title', '')}")
    print(f"  Status:       {proposal_status_color(data.get('status', 'unknown'))}")
    print(f"  Proposer:     {data.get('proposer', '')}")
    print(f"  Votes:        {data.get('current_approvals', 0)}/{data.get('required_approvals', 1)}")
    print(f"  Created:      {data.get('created_at', '')}")
    print(f"  Updated:      {data.get('updated_at', '')}")
    if data.get('applied_at'):
        print(f"  Applied:      {data['applied_at']}")
    if data.get('overridden_at'):
        print(f"  {red('Overridden:')}  {data['overridden_at']}")
        print(f"  Override reason: {data.get('override_reason', '')}")

    changes = data.get('changes_json', '')
    if changes:
        print(f"\n  Changes: {changes}")
    desc = data.get('description', '')
    if desc:
        print(f"\n  Description: {desc}")
    reason = data.get('reason', '')
    if reason:
        print(f"  Reason: {reason}")
    return data

def cmd_approve(args):
    """Approve a proposal."""
    print(bold(f"\n  Approve: {args.proposal_id}\n"))
    data = api_post(f"/governance/approve/{args.proposal_id}", {"approver": args.approver or "operator"})
    if not data or not data.get("success"):
        # Fallback to direct engine
        result = direct_engine_call("approve_proposal", proposal_id=args.proposal_id, approver=args.approver or "operator")
        if result is not None:
            if result:
                print(green(f"  Proposal {args.proposal_id} fully approved"))
            else:
                print(yellow(f"  Proposal {args.proposal_id} approved (more votes needed)"))
        else:
            print(red(f"  Approval failed"))
    else:
        print(green(f"  Proposal approved: {data}"))
    return data

def cmd_reject(args):
    """Reject a proposal."""
    print(bold(f"\n  Reject: {args.proposal_id}\n"))
    data = api_post(f"/governance/reject/{args.proposal_id}", {"rejecter": args.rejecter or "operator", "reason": args.reason or ""})
    if not data or not data.get("success"):
        result = direct_engine_call("reject_proposal", proposal_id=args.proposal_id, rejecter=args.rejecter or "operator", reason=args.reason or "")
        if result is not None:
            print(green(f"  Proposal {args.proposal_id} rejected"))
        else:
            print(red(f"  Rejection failed"))
    else:
        print(green(f"  Proposal rejected: {data}"))
    return data

def cmd_apply(args):
    """Apply all approved proposals."""
    print(bold("\n  Apply Approved Proposals\n"))
    data = api_post("/governance/apply", {})
    if not data:
        result = direct_engine_call("apply_approved_proposals")
        if result is not None:
            if result:
                print(green(f"  Applied {len(result)} proposal(s): {', '.join(r[:8] for r in result)}"))
            else:
                print(dim("  No approved proposals to apply"))
        else:
            print(red(f"  Apply failed"))
    else:
        print(green(f"  Applied: {data}"))
    return data

def cmd_override(args):
    """MAD override a decision."""
    print(bold(f"\n  MAD Override: {args.proposal_id}\n"))
    reason = args.reason or input("  Override reason: ").strip()
    if not reason:
        print(red("  Override requires a reason"))
        return {}
    data = api_post("/governance/override", {"decision_id": args.proposal_id, "reason": reason, "mad_id": args.mad_id or "mad"})
    if not data or not data.get("success"):
        result = direct_engine_call("override_autonomous_decision", decision_id=args.proposal_id, reason=reason, mad_id=args.mad_id or "mad")
        if result is not None:
            print(red(f"  OVERRIDDEN: {args.proposal_id} — {reason}"))
        else:
            print(red(f"  Override failed"))
    else:
        print(red(f"  OVERRIDDEN: {data}"))
    return data

def cmd_sovereignty(args):
    """Show sovereignty boundaries."""
    print(bold("\n  Sovereignty Boundaries\n"))
    data = api_get("/governance/sovereignty")
    if not data:
        data = direct_engine_call("get_sovereignty_report")
    if not data:
        print(dim("  (unavailable)"))
        return data

    boundaries = data.get("boundaries", {})
    rows = []
    for key, boundary in boundaries.items():
        immutable = red("IMMUTABLE") if boundary.get("immutable", False) else dim("configurable")
        range_str = ""
        if "min" in boundary and "max" in boundary:
            range_str = f"{boundary['min']} - {boundary['max']}"
        elif "type" in boundary:
            range_str = boundary["type"]
        rows.append([key, immutable, range_str, boundary.get("description", "")[:50]])
    print(render_table(["Boundary", "Access", "Range", "Description"], rows))
    print(f"\n  {len(boundaries)} boundaries, {len(data.get('immutable_boundaries', []))} immutable")
    return data

def cmd_log(args):
    """Show governance audit log."""
    print(bold("\n  Governance Audit Log\n"))
    data = api_get(f"/governance/log?limit={args.limit}")
    if not data:
        data = direct_engine_call("get_governance_log", limit=args.limit)
    if not data:
        print(dim("  (no log available)"))
        return data

    entries = data if isinstance(data, list) else data.get("log", data.get("entries", []))
    if not entries:
        print(dim("  (log is empty)"))
        return entries

    rows = []
    for e in entries[:args.limit]:
        rows.append([
            (e.get("timestamp", "") or "")[:19],
            e.get("action", ""),
            e.get("actor", ""),
            str(e.get("details_json", ""))[:60],
        ])
    print(render_table(["Timestamp", "Action", "Actor", "Details"], rows))
    print(f"\n  {len(entries)} entries")
    return entries

def cmd_peers(args):
    """Show peer agent coevolution status."""
    print(bold("\n  Coevolution Peers\n"))
    data = api_get("/coevolution/peers")
    if not data:
        print(dim("  (coevolution protocol not yet available — RL building OCE-8.3)"))
        return data

    peers = data if isinstance(data, list) else data.get("peers", [])
    if not peers:
        print(dim("  (no peers registered)"))
        return peers

    rows = []
    for p in peers:
        rows.append([
            p.get("agent_id", ""),
            p.get("trust_level", ""),
            str(p.get("capabilities", [])),
            p.get("status", ""),
            (p.get("last_seen", "") or "")[:19],
        ])
    print(render_table(["Agent ID", "Trust", "Capabilities", "Status", "Last Seen"], rows))
    return peers

def cmd_health(args):
    """Quick governance health check."""
    print(bold("\n  Governance Health Check\n"))
    issues = []

    # Check sovereignty
    sov = api_get("/governance/sovereignty")
    if not sov:
        sov = direct_engine_call("get_sovereignty_report")
    if sov:
        boundaries = sov.get("boundaries", {})
        immutable = sov.get("immutable_boundaries", [])
        print(f"  Boundaries: {len(boundaries)} configured, {len(immutable)} immutable")
        if "mad_override_enabled" in immutable:
            print(green("  MAD override: enabled (immutable)"))
        else:
            issues.append("MAD override boundary not marked immutable")
    else:
        issues.append("Sovereignty report unavailable")

    # Check pending proposals
    for status in ["proposed", "voting"]:
        props = api_get(f"/governance/proposals?status={status}&limit=100")
        if isinstance(props, list) and props:
            print(f"  {proposal_status_color(status)}: {len(props)} pending")

    # Check approved but not applied
    approved = api_get("/governance/proposals?status=approved&limit=100")
    if isinstance(approved, list) and approved:
        print(yellow(f"  Approved (not applied): {len(approved)} — run 'apply' to execute"))

    print()
    if issues:
        for issue in issues:
            print(red(f"  {issue}"))
    else:
        print(green("  Governance engine healthy"))

    return {"sovereignty": sov, "issues": issues}

def cmd_all(args):
    """Run all checks."""
    print(bold("\n" + "=" * 60))
    print(bold("  OCE Governance Engine — Full Diagnostic"))
    print(bold("=" * 60))
    cmd_health(args)
    print()
    cmd_status(args)
    print()
    cmd_proposals(args)
    print()
    cmd_sovereignty(args)
    print()
    cmd_log(args)
    print(bold("\n" + "=" * 60))
    print(bold("  Diagnostic complete"))
    print(bold("=" * 60 + "\n"))

# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="OCE-8.16 Governance Debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python governance-debug.py health
  python governance-debug.py status
  python governance-debug.py proposals --status proposed
  python governance-debug.py proposal <id>
  python governance-debug.py approve <id> --approver mad
  python governance-debug.py reject <id> --reason "not needed"
  python governance-debug.py apply
  python governance-debug.py override <id> --reason "MAD override"
  python governance-debug.py sovereignty
  python governance-debug.py log --limit 20
  python governance-debug.py peers
  python governance-debug.py all
        """,
    )
    sp = p.add_subparsers(dest="command")

    sp.add_parser("status", help="Governance engine status")
    sp.add_parser("health", help="Quick health check")

    pp = sp.add_parser("proposals", help="List proposals")
    pp.add_argument("--status", choices=["proposed","voting","approved","rejected","applied","overridden"])
    pp.add_argument("--limit", type=int, default=50)

    pt = sp.add_parser("proposal", help="Proposal detail")
    pt.add_argument("proposal_id")

    pa = sp.add_parser("approve", help="Approve proposal")
    pa.add_argument("proposal_id")
    pa.add_argument("--approver", default="operator")

    pr = sp.add_parser("reject", help="Reject proposal")
    pr.add_argument("proposal_id")
    pr.add_argument("--rejecter", default="operator")
    pr.add_argument("--reason", default="")

    sp.add_parser("apply", help="Apply approved proposals")

    po = sp.add_parser("override", help="MAD override")
    po.add_argument("proposal_id")
    po.add_argument("--reason", default="")
    po.add_argument("--mad-id", default="mad")

    sp.add_parser("sovereignty", help="Show sovereignty boundaries")

    pl = sp.add_parser("log", help="Governance audit log")
    pl.add_argument("--limit", type=int, default=50)

    sp.add_parser("peers", help="Peer agent status")
    sp.add_parser("all", help="Run all checks")

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)

    handlers = {
        "status": cmd_status, "proposals": cmd_proposals, "proposal": cmd_proposal,
        "approve": cmd_approve, "reject": cmd_reject, "apply": cmd_apply,
        "override": cmd_override, "sovereignty": cmd_sovereignty, "log": cmd_log,
        "peers": cmd_peers, "health": cmd_health, "all": cmd_all,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        p.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
