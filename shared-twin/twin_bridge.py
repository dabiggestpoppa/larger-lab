#!/usr/bin/env python3
"""
Twin Pillar Heartbeat & Sync Bridge
OC2 <-> OC3 file-based synchronization
Phase A: Simple heartbeat exchange + state comparison
"""

import json
import os
import sys
from datetime import datetime, timezone

SHARED_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\shared-twin"
HEARTBEAT_FILE = os.path.join(SHARED_DIR, "heartbeat.json")
STATE_FILE = os.path.join(SHARED_DIR, "state.md")
DRIFT_LOG = os.path.join(SHARED_DIR, "drift-log.json")


def ensure_dir():
    os.makedirs(SHARED_DIR, exist_ok=True)


def write_heartbeat(pillar_id, port, model, status="active", tasks=None):
    ensure_dir()
    heartbeat = {}
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE, "r") as f:
                heartbeat = json.load(f)
        except (json.JSONDecodeError, IOError):
            heartbeat = {}

    now = datetime.now(timezone.utc).isoformat()
    heartbeat[pillar_id] = {
        "timestamp": now,
        "port": port,
        "model": model,
        "status": status,
        "tasks": tasks or [],
    }
    heartbeat["last_sync"] = now

    with open(HEARTBEAT_FILE, "w") as f:
        json.dump(heartbeat, f, indent=2)
    return heartbeat


def read_heartbeat():
    if not os.path.exists(HEARTBEAT_FILE):
        return {}
    try:
        with open(HEARTBEAT_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def check_twin_status():
    hb = read_heartbeat()
    now = datetime.now(timezone.utc)
    results = {}
    for pillar in ["oc2", "oc3"]:
        if pillar in hb:
            ts = datetime.fromisoformat(hb[pillar]["timestamp"])
            age_seconds = (now - ts).total_seconds()
            results[pillar] = {
                "alive": age_seconds < 300,
                "age_seconds": round(age_seconds, 1),
                "status": hb[pillar]["status"],
            }
        else:
            results[pillar] = {"alive": False, "age_seconds": None, "status": "unknown"}
    return results


def detect_drift():
    hb = read_heartbeat()
    drift = []
    oc2_data = hb.get("oc2", {})
    oc3_data = hb.get("oc3", {})
    if not oc2_data or not oc3_data:
        return drift
    if oc2_data.get("status") == "critical" or oc3_data.get("status") == "critical":
        drift.append({
            "type": "critical_status",
            "message": "One pillar reports critical status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    if drift:
        log_drift(drift)
    return drift


def log_drift(drift_events):
    existing = []
    if os.path.exists(DRIFT_LOG):
        try:
            with open(DRIFT_LOG, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []
    existing.extend(drift_events)
    existing = existing[-100:]
    with open(DRIFT_LOG, "w") as f:
        json.dump(existing, f, indent=2)


def update_state_md():
    hb = read_heartbeat()
    twin = check_twin_status()
    now_str = datetime.now(timezone.utc).isoformat()

    lines = [
        "# TWIN PILLAR - SHARED STATE",
        "# OC2 <-> OC3 Synchronization Layer",
        f"# Last Updated: {now_str}",
        "",
        "## Pillar Status",
        "| Pillar | Port | Status | Last Heartbeat | Alive |",
        "|--------|------|--------|----------------|-------|",
    ]

    for pillar_key, pillar_name, port in [("oc2", "OC2", 18790), ("oc3", "OC3", 18791)]:
        data = hb.get(pillar_key, {})
        status = data.get("status", "unknown")
        ts = data.get("timestamp", "N/A")
        alive = twin.get(pillar_key, {}).get("alive", False)
        alive_str = "YES" if alive else "NO"
        lines.append(f"| {pillar_name} | {port} | {status} | {ts} | {alive_str} |")

    lines.append("")
    lines.append("## Active Tasks")
    for pillar_key, pillar_name in [("oc2", "OC2"), ("oc3", "OC3")]:
        tasks = hb.get(pillar_key, {}).get("tasks", [])
        lines.append(f"### {pillar_name}")
        if tasks:
            for t in tasks:
                lines.append(f"- [{t.get('status', 'unknown')}] {t.get('name', 'unnamed')}")
        else:
            lines.append("- No active tasks")
        lines.append("")

    lines.append("## Sync Log")
    lines.append(f"- {now_str}: Heartbeat sync updated")

    if os.path.exists(DRIFT_LOG):
        try:
            with open(DRIFT_LOG, "r") as f:
                drift_events = json.load(f)
            if drift_events:
                lines.append(f"- WARNING: {len(drift_events)} drift events logged")
        except:
            pass

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "heartbeat":
        pillar = sys.argv[2] if len(sys.argv) > 2 else "oc2"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else (18790 if pillar == "oc2" else 18791)
        model = sys.argv[4] if len(sys.argv) > 4 else "unknown"
        hb = write_heartbeat(pillar, port, model)
        update_state_md()
        print(json.dumps(hb, indent=2))

    elif action == "status":
        twin = check_twin_status()
        print(json.dumps(twin, indent=2))

    elif action == "drift":
        drift = detect_drift()
        if drift:
            print("DRIFT DETECTED:")
            print(json.dumps(drift, indent=2))
        else:
            print("No drift detected. Pillars aligned.")

    elif action == "full":
        pillar = sys.argv[2] if len(sys.argv) > 2 else "oc2"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else (18790 if pillar == "oc2" else 18791)
        model = sys.argv[4] if len(sys.argv) > 4 else "unknown"
        hb = write_heartbeat(pillar, port, model)
        twin = check_twin_status()
        drift = detect_drift()
        update_state_md()
        print(f"[{pillar.upper()}] Heartbeat written")
        print(f"Twin status: {json.dumps(twin, indent=2)}")
        if drift:
            print(f"DRIFT: {json.dumps(drift, indent=2)}")
        else:
            print("No drift")

    else:
        print(f"Unknown action: {action}")
        print("Usage: python twin_bridge.py [heartbeat|status|drift|full] [pillar] [port] [model]")
