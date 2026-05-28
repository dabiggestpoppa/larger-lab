"""Check full system integration."""
import requests
import json

print("=== Service Health ===")
for name, url in [
    ("OCE Backend", "http://localhost:8000/health"),
    ("SRRA-OPH API", "http://localhost:8001/api/health"),
]:
    try:
        r = requests.get(url, timeout=3)
        print(f"{name}: OK ({r.status_code})")
    except Exception as e:
        print(f"{name}: FAIL ({e})")

print("\n=== OCE Agents ===")
r = requests.get("http://localhost:8000/command-center/agents")
for k, v in r.json()["agents"].items():
    print(f"  {v['label']} ({v['status']})")

print("\n=== OCE Rooms ===")
r = requests.get("http://localhost:8000/command-center/rooms")
for k, v in r.json()["rooms"].items():
    print(f"  {v['name']} ({len(v.get('agent_ids', []))} agents)")

print("\n=== SRRA-OPH Observers ===")
r = requests.get("http://localhost:8001/api/observers")
print(f"  {len(r.json()['observers'])} observers")

print("\n=== OCE Observers ===")
r = requests.get("http://localhost:8000/observers")
print(f"  {len(r.json())} observers")

print("\n=== OCE Events ===")
r = requests.get("http://localhost:8000/events")
print(f"  {len(r.json())} events")
