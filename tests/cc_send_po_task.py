"""
CC sends task to PO via OCE backend /chat endpoint.
PO (Primary Observer) will receive and execute autonomously.
"""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"

task_message = """CC HERE. TASK FOR PO (Primary Observer):

Your next assignment: MAD LABS Whop Store Build.

The store config files are already created in whop-store/ directory. Your job:

1. Read the Whop store mission brief (it's in the workspace context)
2. Verify all 9 JSON config files in whop-store/ are valid
3. Create the landing page HTML at whop-store/landing.html — premium black background, minimalist, institutional finance aesthetic. Sections: Hero, Overview, Services, Community, Research (coming soon), Software (in development), Book Consultation. Link to Calendly, Discord, Linktree.
4. Create whop-store/README.md documenting the store structure
5. Store completion memory via POST /memory/store layer=WORK content={"task": "whop_store_build", "status": "complete"}
6. Update your progress file
7. Report back to team-chat

Use the OCE backend at http://127.0.0.1:8000 for all API calls.
Use run_in_terminal for PowerShell, create_file for new files, read_file to read existing files.
Do NOT modify existing JSON config files unless they have errors.

EXECUTE NOW."""

payload = {
    "message": task_message,
    "session_id": "cc_po_task_whop_build_20260626",
    "context": {
        "sender": "CC",
        "task_type": "whop_store_build",
        "priority": "high"
    }
}

data = json.dumps(payload).encode()
req = urllib.request.Request(
    BASE + "/chat",
    data=data,
    method="POST",
    headers={"Content-Type": "application/json"}
)

print("Sending task to PO via OCE backend...")
print(f"Payload size: {len(data)} bytes")

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        status = resp.status
        body = resp.read().decode()
        print(f"\nStatus: {status}")
        print(f"Response ({len(body)} chars):")
        print(body[:2000])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"Error: {e}")
