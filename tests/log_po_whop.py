import urllib.request, json

BASE = "http://127.0.0.1:8000"

# Log the Whop store task assignment
body = json.dumps({
    "event_type": "task_received",
    "source": "primary_observer",
    "data": {
        "request_id": "req_whop_build_20260626",
        "domain": "coding",
        "complexity": "high",
        "description": "MAD LABS Whop Store Build — create landing page, verify configs, update progress"
    }
}).encode()

req = urllib.request.Request(
    BASE + "/api/po/monitor/event",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"}
)
r = urllib.request.urlopen(req, timeout=5)
print("Log:", r.status, r.read().decode())
