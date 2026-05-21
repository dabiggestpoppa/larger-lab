"""
IACER Breath Sync — OWL Self-Regulation Engine
===============================================
Run after every 4 task/tool call cycles to prevent runaway execution.

Usage:
    python tools/iacer_breath_sync.py [--check] [--full]

What it does:
    1. INTENT check: Am I still aligned with MAD's last directive?
    2. ABSTRACTION check: Did I drift beyond the original scope?
    3. CONTEXT check: Is system state consistent with my actions?
    4. EXPECTATIONS check: Am I delivering what's expected?
    5. RESULTS check: Did my last 4 cycles actually improve continuity?

If any check fails → STOP and ask MAD before proceeding.

Integrated into OWL's operating pattern:
    - After every 4 tool calls or task completions, OWL runs a quick IACER check
    - If drift detected → re-anchor before next task
    - If continuity threatened → repair before proceeding
"""

import json
import os
import sys
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
STATE_FILE = os.path.join(WORKSPACE, "memory-bank", "iacer_state.json")
LOG_FILE = os.path.join(WORKSPACE, "logs", "iacer_breath.log")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "cycle_count": 0,
        "last_mad_directive": "",
        "last_heartbeat": "",
        "drift_flags": [],
        "continuity_score": 1.0,
    }


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_breach(check_name, detail):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] BREACH: {check_name} — {detail}\n")


def run_check(verbose=True):
    state = load_state()
    issues = []

    # ── INTENT ──────────────────────────────────────────────────────────
    # Check: Does last_mad_directive match current trajectory?
    if not state.get("last_mad_directive"):
        issues.append("INTENT: No MAD directive recorded. Need anchor point.")

    # ── ABSTRACTION ─────────────────────────────────────────────────────
    # Check: Cycle count vs. expected output ratio
    cycles = state.get("cycle_count", 0)
    if cycles > 20 and not state.get("last_heartbeat"):
        issues.append(
            f"ABSTRACTION: {cycles} cycles without heartbeat sync. Likely drift."
        )

    # ── CONTEXT ─────────────────────────────────────────────────────────
    # Check: Workspace bloat
    tools_md = os.path.join(WORKSPACE, "TOOLS.md")
    heartbeat_md = os.path.join(WORKSPACE, "HEARTBEAT.md")
    for path, label in [(tools_md, "TOOLS.md"), (heartbeat_md, "HEARTBEAT.md")]:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 12000:
                issues.append(
                    f"CONTEXT: {label} is {size}b (>12K bootstrap limit). Truncation risk."
                )

    # ── EXPECTATIONS ────────────────────────────────────────────────────
    # Check: Stale delegations
    prog_dir = os.path.join(WORKSPACE, "progress")
    if os.path.exists(prog_dir):
        stale = []
        for fn in os.listdir(prog_dir):
            fp = os.path.join(prog_dir, fn)
            age_h = (datetime.now().timestamp() - os.path.getmtime(fp)) / 3600
            if age_h > 72:  # 3 days stale
                stale.append(f"{fn} ({age_h:.0f}h old)")
        if stale:
            issues.append(
                f"EXPECTATIONS: Stale progress files — {', '.join(stale[:3])}"
            )

    # ── RESULTS ─────────────────────────────────────────────────────────
    # Check: Continuity score
    score = state.get("continuity_score", 1.0)
    if score < 0.5:
        issues.append(
            f"RESULTS: Continuity score {score:.2f} — below safe threshold (0.5)"
        )

    # ── Report ──────────────────────────────────────────────────────────
    if verbose:
        if issues:
            print("[STOP] IACER BREATH SYNC -- ISSUES DETECTED:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print("\n[WARN] RECOMMENDATION: Re-anchor before next task cycle.")
        else:
            print("[OK] IACER BREATH SYNC -- ALL CLEAR")
            print(f"   Cycles: {cycles} | Continuity: {score:.2f}")
            print(f"   Last directive: {state.get('last_mad_directive', 'N/A')[:60]}")

    return issues


def record_cycle(mad_directive=None):
    """Call this after every task cycle to increment counter."""
    state = load_state()
    state["cycle_count"] = state.get("cycle_count", 0) + 1
    if mad_directive:
        state["last_mad_directive"] = mad_directive
    state["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    # Auto-trigger check every 4 cycles
    if state["cycle_count"] % 4 == 0:
        print(f"\n[BREATH] IACER BREATH SYNC (cycle {state['cycle_count']})")
        return run_check()
    return []


def record_success():
    state = load_state()
    state["continuity_score"] = min(1.0, state.get("continuity_score", 1.0) + 0.05)
    save_state()


def record_failure(reason=""):
    state = load_state()
    state["continuity_score"] = max(0.0, state.get("continuity_score", 1.0) - 0.15)
    state.setdefault("drift_flags", []).append(
        {"ts": datetime.now(timezone.utc).isoformat(), "reason": reason}
    )
    save_state()
    log_breach("continuity_drop", reason)


if __name__ == "__main__":
    if "--check" in sys.argv or "--full" in sys.argv:
        issues = run_check(verbose=True)
        sys.exit(1 if issues else 0)
    elif "--record" in sys.argv:
        directive = sys.argv[sys.argv.index("--record") + 1] if "--record" in sys.argv and len(sys.argv) > sys.argv.index("--record") + 1 else None
        record_cycle(mad_directive=directive)
    else:
        # Default: run check
        run_check(verbose=True)
