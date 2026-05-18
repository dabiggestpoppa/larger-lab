#!/usr/bin/env python3
"""
H3 - Hermes Support Instance for OC3
Lightweight mediation layer between OC2 and OC3
Phase A: Health monitoring + repair routing + continuity buffering
"""

import json
import os
import sys
import time
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

SHARED_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\shared-twin"
HEARTBEAT_FILE = os.path.join(SHARED_DIR, "heartbeat.json")
DRIFT_LOG = os.path.join(SHARED_DIR, "drift-log.json")
H3_LOG = os.path.join(SHARED_DIR, "h3-log.json")
H3_STATE = os.path.join(SHARED_DIR, "h3-state.json")

OC2_PORT = 18790
OC3_PORT = 18791
H3_PORT = 18795


def log_h3(event):
    """Log H3 events."""
    entries = []
    if os.path.exists(H3_LOG):
        try:
            with open(H3_LOG, "r") as f:
                entries = json.load(f)
        except:
            entries = []
    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event
    })
    entries = entries[-200:]
    with open(H3_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def check_pillar_health():
    """Check health of both pillars."""
    if not os.path.exists(HEARTBEAT_FILE):
        return {"oc2": "unknown", "oc3": "unknown"}

    try:
        with open(HEARTBEAT_FILE, "r") as f:
            hb = json.load(f)
    except:
        return {"oc2": "error", "oc3": "error"}

    now = datetime.now(timezone.utc)
    results = {}

    for pillar, key in [("oc2", "oc2"), ("oc3", "oc3")]:
        data = hb.get(key, {})
        ts_str = data.get("timestamp")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str)
                age = (now - ts).total_seconds()
                if age < 120:
                    results[pillar] = "healthy"
                elif age < 300:
                    results[pillar] = "stale"
                else:
                    results[pillar] = "down"
            except:
                results[pillar] = "error"
        else:
            results[pillar] = "no_heartbeat"

    return results


def route_repair_signal(source_pillar, issue_type, details):
    """Route a repair signal between pillars."""
    signal = {
        "type": "repair_signal",
        "source": source_pillar,
        "issue": issue_type,
        "details": details,
        "routed_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending"
    }
    log_h3(signal)
    return signal


def get_continuity_snapshot():
    """Get a continuity snapshot of the twin pillar system."""
    health = check_pillar_health()

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "h3_status": "active",
        "pillars": {
            "oc2": {
                "port": OC2_PORT,
                "health": health.get("oc2", "unknown"),
                "role": "strategic_continuity"
            },
            "oc3": {
                "port": OC3_PORT,
                "health": health.get("oc3", "unknown"),
                "role": "adaptive_execution"
            }
        },
        "twin_alignment": "aligned" if health.get("oc2") == "healthy" and health.get("oc3") == "healthy" else "degraded"
    }

    # Save state
    with open(H3_STATE, "w") as f:
        json.dump(snapshot, f, indent=2)

    return snapshot


class H3Handler(BaseHTTPRequestHandler):
    """H3 HTTP handler for status and repair routing."""

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            health = check_pillar_health()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "h3": "active",
                "pillars": health,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif self.path == "/snapshot":
            snapshot = get_continuity_snapshot()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(snapshot, indent=2).encode())

        elif self.path == "/drift":
            drift_events = []
            if os.path.exists(DRIFT_LOG):
                try:
                    with open(DRIFT_LOG, "r") as f:
                        drift_events = json.load(f)
                except:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(drift_events[-10:], indent=2).encode())

        elif self.path == "/logs":
            logs = []
            if os.path.exists(H3_LOG):
                try:
                    with open(H3_LOG, "r") as f:
                        logs = json.load(f)
                except:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(logs[-20:], indent=2).encode())

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        if self.path == "/repair":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body)
            except:
                data = {}

            source = data.get("source", "unknown")
            issue = data.get("issue", "unknown")
            details = data.get("details", "")

            signal = route_repair_signal(source, issue, details)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(signal, indent=2).encode())

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def log_message(self, format, *args):
        pass  # Suppress HTTP logging


def run_server():
    """Run H3 HTTP server."""
    server = HTTPServer(("127.0.0.1", H3_PORT), H3Handler)
    log_h3({"event": "h3_server_started", "port": H3_PORT})
    print(f"H3 Hermes support instance running on port {H3_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_h3({"event": "h3_server_stopped"})
        server.shutdown()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "snapshot":
        print(json.dumps(get_continuity_snapshot(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "health":
        print(json.dumps(check_pillar_health(), indent=2))
    else:
        run_server()
