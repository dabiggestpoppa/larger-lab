import urllib.request, json

BASE = "http://127.0.0.1:8000"

# Test monitor endpoint
try:
    r = urllib.request.urlopen(BASE + "/api/po/monitor/", timeout=5)
    data = json.loads(r.read().decode())
    print("=== PO MONITOR ===")
    print("Status:", data["status"])
    print("Total events:", data["summary"]["total_events"])
    print("Last 24h:", data["summary"]["last_24h_events"])
    print("State changes:", data["summary"]["total_state_changes"])
    print("Chat messages:", data["summary"]["total_chat_messages"])
    print("Event types:", len(data["event_types"]))
    for t in data["event_types"][:5]:
        print(f"  {t['event_type']}: {t['count']}")
    print("Recent events:", len(data["recent_events"]))
    if data["recent_events"]:
        latest = data["recent_events"][0]
        print("Latest:", latest["event_type"], "from", latest["source"], "at", latest["timestamp"])
except Exception as e:
    print("Monitor error:", e)

# Test learning log
try:
    r = urllib.request.urlopen(BASE + "/api/po/monitor/learning-log", timeout=5)
    data = json.loads(r.read().decode())
    print("\n=== LEARNING LOG ===")
    print("Recent tasks:", len(data["recent_tasks"]))
    print("State changes:", len(data["recent_state_changes"]))
    print("Learning prompts:", len(data["learning_prompts"]))
except Exception as e:
    print("Learning log error:", e)

# Test log event
try:
    body = json.dumps({"event_type": "test", "source": "cc", "data": {"msg": "monitor test"}}).encode()
    req = urllib.request.Request(
        BASE + "/api/po/monitor/event",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req, timeout=5)
    print("\nLog event:", r.status, r.read().decode()[:100])
except Exception as e:
    print("Log event error:", e)
