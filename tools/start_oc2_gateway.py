"""Start OC2 Gateway and verify connection."""
import subprocess
import time
import requests

# Start OC2 gateway
print("Starting OC2 Gateway...")
proc = subprocess.Popen(
    ["python", "-m", "oce.backend.oc2_gateway"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"C:\Users\wifik\Desktop\projects\larger-lab",
)
print(f"PID: {proc.pid}")

# Wait for it to connect
time.sleep(3)

# Verify registration
try:
    r = requests.get("http://localhost:8000/command-center/agents", timeout=5)
    agents = r.json()["agents"]
    print("\nRegistered agents:")
    for k, v in agents.items():
        if "gateway" in k.lower() or "oc2" in k.lower():
            print(f"  {k}: {v['label']} ({v['status']})")
except Exception as e:
    print(f"Error checking agents: {e}")

# Check gateway status
try:
    r = requests.get("http://localhost:8000/health", timeout=3)
    print(f"\nOCE Backend: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"OCE Backend error: {e}")

print("\nOC2 Gateway started. Press Ctrl+C to stop.")
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    print("\nOC2 Gateway stopped.")
