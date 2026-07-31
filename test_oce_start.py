"""Test OCE backend startup."""
import sys
import os
sys.path.insert(0, '.')
os.environ["PYTHONIOENCODING"] = "utf-8"

print("Step 1: Importing app...")
try:
    from oce.backend.main import app
    print("Step 1 OK: App imported")
except Exception as e:
    print(f"Step 1 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 2: Listing routes...")
for route in app.routes:
    if hasattr(route, "path"):
        methods = getattr(route, "methods", set())
        m = ",".join(methods) if methods else "MOUNT"
        print(f"  {m} {route.path}")

print("Step 3: All OK")
