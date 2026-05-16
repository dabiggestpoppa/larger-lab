#!/usr/bin/env python3
"""
Phase Gate — SRRA-OPH Phase Transition Manager
===============================================
Manages phase transitions for the SRRA-OPH build.
Each phase has success criteria that must be verified before moving to next phase.

Usage:
  python tools/phase-gate.py --status     # Show current phase status
  python tools/phase-gate.py --check      # Check if current phase criteria met
  python tools/phase-gate.py --advance    # Advance to next phase (if criteria met)
  python tools/phase-gate.py --init       # Initialize phase tracking
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
PHASE_FILE = LAB_ROOT / ".phase-state.json"

# SRRA-OPH Phase Definitions (from the doctrine document)
PHASES = {
    "PHASE_0": {
        "name": "Foundational Reality Check",
        "description": "Establish bounded adaptive cognition infrastructure. No building yet.",
        "success_criteria": [
            "Architecture principles documented",
            "Success metrics defined (stable adaptive continuity)",
            "Tech stack selected",
        ],
        "status": "complete",
    },
    "PHASE_1": {
        "name": "Minimal Observer Mesh",
        "description": "Build bounded local cognition with repairable overlap.",
        "success_criteria": [
            "4 observer patches operational (Planner, Execution, Memory, Repair)",
            "Patches survive partial failures",
            "No total collapse occurs",
            "Repair remains local",
            "Synchronization remains bounded",
            "Collar protocol enforces structured overlap",
        ],
        "status": "complete",
    },
    "PHASE_2": {
        "name": "Reconstruction + Recoverability",
        "description": "Replace static memory with adaptive reconstruction.",
        "success_criteria": [
            "Recovery anchors implemented (sparse persistence)",
            "Continuity survives sparse memory (delete 90% context, reconstruct)",
            "Reconstruction mesh operational (drift detector, consistency validator, synthesizer)",
            "Contradictions self-resolve",
            "Constraint propagation works (change one constraint, downstream shifts)",
        ],
        "status": "pending",
    },
    "PHASE_3": {
        "name": "Emergent Topology",
        "description": "Allow cognition geometry to self-organize dynamically.",
        "success_criteria": [
            "Dynamic coupling between patches (adaptive edge weights)",
            "Topological routing (lowest entropy path selection)",
            "Distributed consensus (no master orchestrator)",
            "System reroutes under stress (patch failures, overload)",
            "Continuity persists after patch kill",
        ],
        "status": "pending",
    },
    "PHASE_4": {
        "name": "Workspace Integration",
        "description": "Attach operational tooling to the cognition substrate.",
        "success_criteria": [
            "OpenClaw mapped to strategic synthesis patch",
            "Hermes mapped to execution patch",
            "Nautilus mapped to environment verification",
            "Claude mapped to symbolic reasoning interface",
            "No workspace tool is central memory/orchestration/identity",
        ],
        "status": "pending",
    },
    "PHASE_5": {
        "name": "Long Horizon Adaptation",
        "description": "Persistent adaptive identity over time.",
        "success_criteria": [
            "Long-term drift tracking operational",
            "Operator trajectory modeling",
            "Reinforcement weighting",
            "Recursive compression (memory doesn't grow linearly)",
            "System retains continuity over weeks/months",
        ],
        "status": "pending",
    },
}


def load_phase_state() -> dict:
    """Load phase tracking state."""
    if PHASE_FILE.exists():
        with open(PHASE_FILE) as f:
            return json.load(f)
    return {"current_phase": "PHASE_1", "phases": {}, "history": []}


def save_phase_state(state: dict):
    """Save phase tracking state."""
    with open(PHASE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def init_phase_tracking():
    """Initialize phase tracking from the phase definitions."""
    state = {
        "current_phase": "PHASE_1",
        "phases": {},
        "history": [],
        "initialized_at": datetime.now(timezone.utc).isoformat(),
    }

    for phase_id, phase_def in PHASES.items():
        state["phases"][phase_id] = {
            "name": phase_def["name"],
            "status": phase_def["status"],
            "criteria": {c: False for c in phase_def["success_criteria"]},
            "started_at": None,
            "completed_at": None,
        }

    # Mark Phase 0 and 1 as already started
    state["phases"]["PHASE_0"]["status"] = "complete"
    state["phases"]["PHASE_0"]["started_at"] = datetime.now(timezone.utc).isoformat()
    state["phases"]["PHASE_0"]["completed_at"] = datetime.now(timezone.utc).isoformat()
    state["phases"]["PHASE_1"]["status"] = "in_progress"
    state["phases"]["PHASE_1"]["started_at"] = datetime.now(timezone.utc).isoformat()

    save_phase_state(state)
    print("✅ Phase tracking initialized.")
    print(f"   Current phase: {state['current_phase']} — {PHASES[state['current_phase']]['name']}")


def show_status():
    """Show current phase status."""
    state = load_phase_state()
    current = state.get("current_phase", "PHASE_1")
    phase_def = PHASES.get(current, {})
    phase_state = state.get("phases", {}).get(current, {})

    print(f"\n{'='*60}")
    print(f"SRRA-OPH Phase Status")
    print(f"{'='*60}")
    print(f"\n📍 Current: {current} — {phase_def.get('name', 'Unknown')}")
    print(f"   Status: {phase_state.get('status', 'unknown')}")
    print(f"   {phase_def.get('description', '')}")

    # Show all phases
    print(f"\n📊 All Phases:")
    for pid, pdef in PHASES.items():
        ps = state.get("phases", {}).get(pid, {})
        status = ps.get("status", "unknown")
        emoji = {"complete": "✅", "in_progress": "🔄", "pending": "⏳"}.get(status, "❓")
        current_marker = " ← CURRENT" if pid == current else ""
        print(f"   {emoji} {pid}: {pdef['name']}{current_marker}")

    # Show criteria for current phase
    criteria = phase_state.get("criteria", {})
    if criteria:
        print(f"\n📋 Success Criteria for {current}:")
        for criterion, met in criteria.items():
            check = "✅" if met else "⬜"
            print(f"   {check} {criterion}")

    # Show history
    history = state.get("history", [])
    if history:
        print(f"\n📜 Recent History:")
        for entry in history[-5:]:
            print(f"   {entry['timestamp']}: {entry['action']}")

    print()


def check_criteria():
    """Check if current phase criteria are met."""
    state = load_phase_state()
    current = state.get("current_phase", "PHASE_1")
    phase_state = state.get("phases", {}).get(current, {})
    criteria = phase_state.get("criteria", {})

    if not criteria:
        print(f"⚠️ No criteria found for {current}. Run --init first.")
        return False

    met = sum(1 for v in criteria.values() if v)
    total = len(criteria)

    print(f"\n📋 {current} Criteria: {met}/{total} met")
    for criterion, is_met in criteria.items():
        check = "✅" if is_met else "⬜"
        print(f"   {check} {criterion}")

    if met == total:
        print(f"\n🎉 All criteria met! Ready to advance to next phase.")
        return True
    else:
        print(f"\n⏳ {total - met} criteria remaining.")
        return False


def advance_phase():
    """Advance to next phase if criteria are met."""
    state = load_phase_state()
    current = state.get("current_phase", "PHASE_1")
    phase_state = state.get("phases", {}).get(current, {})
    criteria = phase_state.get("criteria", {})

    # Check all criteria met
    if not all(criteria.values()):
        met = sum(1 for v in criteria.values() if v)
        total = len(criteria)
        print(f"❌ Cannot advance: only {met}/{total} criteria met.")
        print(f"   Run --check to see remaining criteria.")
        return False

    # Find next phase
    phase_order = list(PHASES.keys())
    try:
        current_idx = phase_order.index(current)
        if current_idx + 1 >= len(phase_order):
            print(f"🎉 {current} is the final phase! All phases complete.")
            return True
        next_phase = phase_order[current_idx + 1]
    except ValueError:
        print(f"❌ Unknown phase: {current}")
        return False

    # Complete current phase
    now = datetime.now(timezone.utc).isoformat()
    phase_state["status"] = "complete"
    phase_state["completed_at"] = now

    # Start next phase
    next_state = state["phases"].get(next_phase, {})
    next_state["status"] = "in_progress"
    next_state["started_at"] = now

    # Update state
    state["current_phase"] = next_phase
    state["history"].append({
        "timestamp": now,
        "action": f"Advanced from {current} to {next_phase}",
    })

    save_phase_state(state)

    print(f"🚀 Advanced from {current} to {next_phase}")
    print(f"   {next_phase}: {PHASES[next_phase]['name']}")
    print(f"   {PHASES[next_phase]['description']}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Phase Gate — SRRA-OPH Phase Manager")
    parser.add_argument("--init", action="store_true", help="Initialize phase tracking")
    parser.add_argument("--status", action="store_true", help="Show current phase status")
    parser.add_argument("--check", action="store_true", help="Check if phase criteria are met")
    parser.add_argument("--advance", action="store_true", help="Advance to next phase")
    parser.add_argument("--set-criterion", nargs=2, metavar=("CRITERION", "true/false"),
                        help="Set a criterion status")
    args = parser.parse_args()

    if args.init:
        init_phase_tracking()
    elif args.status or (not args.check and not args.advance and not args.set_criterion):
        show_status()
    elif args.check:
        check_criteria()
    elif args.advance:
        advance_phase()
    elif args.set_criterion:
        criterion, value = args.set_criterion
        state = load_phase_state()
        current = state.get("current_phase", "PHASE_1")
        criteria = state["phases"].get(current, {}).get("criteria", {})
        if criterion in criteria:
            criteria[criterion] = value.lower() in ("true", "1", "yes")
            save_phase_state(state)
            print(f"✅ Set '{criterion}' = {criteria[criterion]}")
        else:
            print(f"❌ Criterion '{criterion}' not found in {current}")
            print(f"   Available: {', '.join(criteria.keys())}")


if __name__ == "__main__":
    main()
